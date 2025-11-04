# dsf_label_sdk/client.py
"""Main SDK Client - Sends similarities to Cloud Run for Standard evaluation"""

import os
import requests
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin
import time
from functools import wraps
import logging
from pathlib import Path
import json
from .formula import EnterpriseAdjuster, calculate_similarities_batch
from .calibration import CalibrationProfile

from . import __version__
from .exceptions import ValidationError, LicenseError, APIError, RateLimitError
from .models import Field, Config, EvaluationResult
from .formula import EnterpriseAdjuster, calculate_similarities_batch

MAX_BATCH_EVAL = 10000
logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    if attempt < max_retries - 1:
                        time.sleep(e.retry_after)
                        logger.warning(f"Rate limited. Retrying after {e.retry_after}s...")
                    last_exception = e
                except (requests.RequestException, APIError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            raise last_exception
        return wrapper
    return decorator

class LabelSDK:
    BASE_URL = 'https://label-2c0hlo65m-api-dsfuptech.vercel.app/api'
    WORKER_URL = os.environ.get('CLOUD_RUN_WORKER_URL', '')
    TIERS = {'community', 'professional', 'enterprise'}
    
    def __init__(
        self,
        license_key: Optional[str] = None,
        tier: str = 'community',
        base_url: Optional[str] = None,
        worker_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True
    ):
        if tier not in self.TIERS:
            raise ValidationError(f"Invalid tier. Must be one of: {self.TIERS}")
        
        self.license_key = license_key
        self.tier = tier
        self.base_url = base_url or self.BASE_URL
        self.worker_url = self.base_url  # Vercel es el proxy
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'DSF-Label-SDK-Python/{__version__}'
        })
        
        # Enterprise Adjuster y CalibrationProfile (FIX 2)
        self.enterprise_adjuster = None
        self.calibration_profile = None 
        
        if tier == 'enterprise':
            self.enterprise_adjuster = EnterpriseAdjuster()
            # 2. FIX: Inicializar CalibrationProfile solo para Enterprise
            try:
                # La importación se maneja arriba con fallback
                self.calibration_profile = CalibrationProfile(mode='auto')
                logger.info("✅ CalibrationProfile (Enterprise) inicializado correctamente.")
            except Exception:
                self.calibration_profile = None
                logger.warning("⚠️ CalibrationProfile no disponible. Continuando sin calibración avanzada.")

        # Buffer de historial local
        self.history_buffer = []
        self.buffer_path = Path.home() / '.dsf_label' / 'history_buffer.json'
        self.buffer_path.parent.mkdir(exist_ok=True)
        self._load_buffer()
        
        # Validar licencia si aplica
        if tier != 'community' and license_key:
            self._validate_license()
    
    def _load_buffer(self):
        if self.buffer_path.exists():
            try:
                with open(self.buffer_path, 'r') as f:
                    self.history_buffer = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load buffer: {e}")
    
    def _save_buffer(self):
        try:
            with open(self.buffer_path, 'w') as f:
                json.dump(self.history_buffer, f)
        except Exception as e:
            logger.warning(f"Failed to save buffer: {e}")
    
    def _validate_license(self):
        try:
            resp = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
    
    @retry_on_failure(max_retries=3, delay=1.5)
    def _make_request(self, endpoint: str, data: dict, method: str = "POST") -> dict:
        base = self.base_url.rstrip("/")
        url = f"{base}/{endpoint.strip('/')}" if endpoint else base

        try:
            if method == "GET":
                resp = self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
            else:
                resp = self.session.post(url, json=data, timeout=self.timeout, verify=self.verify_ssl)
        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

        if resp.status_code == 429:
            err = resp.json() if resp.content else {}
            retry_after = int(err.get("retry_after", 60))
            raise RateLimitError(err.get("error", "Rate limited"), retry_after=retry_after)

        j = resp.json() if resp.content else {}

        if resp.status_code >= 400:
            msg = j.get("error", f"HTTP {resp.status_code}")
            if resp.status_code == 403:
                raise LicenseError(msg)
            raise APIError(msg, status_code=resp.status_code)

        return j
    
    def batch_evaluate_async(
            self,
            data_points: List[Dict[str, Any]],
            config: Optional[Union[Dict, Config]] = None,
            poll_interval: int = 5,
            timeout: int = 300,
            mode: str = 'standard'
        ) -> List[EvaluationResult]:
        """
        Evaluación con Standard protegida en Cloud Run.
        1. Detecta si los data_points son similitudes pre-calculadas o embeddings.
        2. Calcula (o no) las similitudes locales.
        3. Envía a Cloud Run para la fórmula Standard.
        4. Aplica ajustes Enterprise (pesos, calibración, etc.) si aplica.
        """

        if isinstance(config, Config):
            config = config.to_dict()

        if len(data_points) > MAX_BATCH_EVAL:
            raise ValidationError(f"Batch too large (max {MAX_BATCH_EVAL})")

        # 1️⃣ Detección robusta de similitudes pre-calculadas
        t0 = time.time()
        fields = list(config.keys())
        sample = data_points[:min(10, len(data_points))]

        is_pre_calculated = (
            len(sample) > 0 and
            all(f in dp for dp in sample for f in fields) and
            all(isinstance(dp[f], (int, float)) and 0 <= dp[f] <= 1
                for dp in sample for f in fields)
        )

        if is_pre_calculated:
            # Los datapoints SON similitudes [0–1]; se usan directamente
            similarities_batch = [[float(dp[f]) for f in fields] for dp in data_points]
            logger.info(f"✅ Similitudes detectadas y extraídas en {time.time()-t0:.2f}s")

        else:
            # Los datapoints son valores raw/embeddings; aplicar calibración si corresponde
            logger.info("⚙️ Calculando similitudes desde datos raw...")

            if self.tier == "enterprise" and self.calibration_profile is not None:
                logger.info("Aplicando CalibrationProfile (Enterprise)...")
                calibrated_data = []
                for dp in data_points:
                    calibrated_dp = {
                        f: self.calibration_profile.calibrate(dp[f], f) if f in dp else dp.get(f, 0.5)
                        for f in fields
                    }
                    calibrated_data.append(calibrated_dp)
                similarities_batch = calculate_similarities_batch(calibrated_data, config)
            else:
                similarities_batch = calculate_similarities_batch(data_points, config)

            logger.info(f"Similitudes calculadas desde raw data en {time.time()-t0:.2f}s")

        # 2️⃣ Enviar a Cloud Run (Fórmula Standard protegida)
        t1 = time.time()
        if not self.worker_url:
            raise APIError("Cloud Run worker URL not configured")

        try:
            resp = requests.post(
                f"{self.worker_url}/evaluate",
                json={
                    "similarities_batch": similarities_batch,
                    "config": config
                },
                timeout=60
            )
            resp.raise_for_status()
            result = resp.json()
            base_scores = result['scores']
        except Exception as e:
            raise APIError(f"Cloud Run evaluation failed: {e}")

        logger.info(f"☁️ Cloud Run evaluation completed in {time.time()-t1:.2f}s")

        # 3️⃣ Ajustes Enterprise locales (ponderación, threshold dinámico, etc.)
        if self.tier == 'enterprise' and self.enterprise_adjuster:
            t2 = time.time()
            final_scores, metadata = self.enterprise_adjuster.adjust_scores(
                base_scores,
                similarities_batch,
                config,
                mode
            )
            logger.info(f"🎛️ Enterprise adjustments in {time.time()-t2:.2f}s")

            # Persistir historial de métricas
            self._persist_history_async(metadata)
        else:
            final_scores = base_scores
            metadata = {'threshold': 0.65}

        # 4️⃣ Empaquetar resultados finales
        results = [
            EvaluationResult(
                score=float(s),
                tier=self.tier,
                confidence_level=metadata.get('threshold', 0.65),
                metrics=metadata
            )
            for s in final_scores
        ]

        logger.info(f"🏁 Total evaluation completed in {time.time()-t0:.2f}s")
        return results

    
    def _persist_history_async(self, metadata: Dict[str, Any]):
        """Persiste historial a Vercel (best-effort)"""
        payload = {
            'license_key': self.license_key,
            'tier': self.tier,
            'aggregated_data': {
                'threshold': metadata.get('threshold'),
                'history_size': metadata.get('history_size', 0),
                'field_stats': metadata.get('field_stats', {}),
                'timestamp': time.time()
            }
        }
        
        self.history_buffer.append(payload)
        self._flush_history_buffer()
    
    def _flush_history_buffer(self):
        """Envía historial buffereado"""
        if not self.history_buffer:
            return
        
        url = f"{self.base_url}/save-history"
        remaining = []
        
        for payload in self.history_buffer:
            try:
                resp = self.session.post(url, json=payload, timeout=5)
                if resp.status_code == 200:
                    logger.debug("History saved")
                elif resp.status_code == 429:
                    remaining.append(payload)
                else:
                    logger.warning(f"History save failed: {resp.status_code}")
            except Exception as e:
                logger.warning(f"History save error: {e}")
                remaining.append(payload)
        
        self.history_buffer = remaining
        self._save_buffer()
    
    def create_config(self) -> Config:
        return Config()
    
    def close(self):
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __repr__(self):
        return f"LabelSDK(tier='{self.tier}', url='{self.base_url}')"
