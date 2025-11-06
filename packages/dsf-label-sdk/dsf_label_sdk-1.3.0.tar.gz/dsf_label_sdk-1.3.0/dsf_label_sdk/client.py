# dsf_label_sdk/client.py
import os
import requests
import time
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union
from . import __version__
from .exceptions import ValidationError, APIError, JobTimeoutError
from .models import Config, EvaluationResult, Job

logger = logging.getLogger(__name__)

TIER_LIMITS = {
    'community': {'batch': 100},
    'professional': {'batch': 1000},
    'enterprise': {'batch': 10000}
}

class LabelSDK:
    BASE_URL = 'https://label-2c0hlo65m-api-dsfuptech.vercel.app/api'
    
    def __init__(self, license_key: Optional[str] = None, tier: str = 'community', timeout: int = 60):
        if tier not in TIER_LIMITS:
            raise ValidationError(f"Invalid tier: {tier}")
        
        self.license_key = license_key
        self.tier = tier
        self.timeout = timeout
        self.base_url = self.BASE_URL
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'DSF-Label-SDK/{__version__}'
        })
    
    def _prepare_payload(self, data_points: List[Dict[str, Any]], config: Dict) -> Dict[str, Any]:
        """Prepara el JSON body para la API"""
        fields = list(config.keys())
        sample = data_points[0] if data_points else {}
        
        has_embedding_keys = any(f"embedding_{f}" in sample for f in fields)
        is_vector = any(isinstance(sample.get(f), (list, np.ndarray)) for f in fields if f in sample)
        
        if has_embedding_keys:
            embeddings_batch = [{f: dp[f"embedding_{f}"] for f in fields} for dp in data_points]
            prototypes_batch = [{f: dp[f"prototype_{f}"] for f in fields} for dp in data_points]
            logger.info("Format: embedding_X/prototype_X")
        elif is_vector:
            embeddings_batch = [{f: dp[f] for f in fields if f in dp} for dp in data_points]
            # Extraer prototipos de la config
            prototypes_batch = [{f: config[f].get('prototype', []) for f in fields} for _ in data_points]
            logger.info("Format: vectors")
        else:
            raise ValidationError("Unknown format. Expected embeddings with 'embedding_X' keys or vector fields")
        
        return {
            "embeddings_batch": embeddings_batch,
            "prototypes_batch": prototypes_batch,
            "config": config,
            "license_key": self.license_key,
            "tier": self.tier
        }

    def batch_evaluate(
        self, 
        data_points: List[Dict[str, Any]], 
        config: Optional[Union[Dict, Config]] = None,
        mode: str = 'sync'
    ) -> Union[List[EvaluationResult], Job]:
        """
        Envía un lote para evaluación.
        mode='sync': Espera y devuelve resultados (rápido, pero con timeouts).
        mode='async': Devuelve un Job ID (lento, para lotes grandes, evita timeouts).
        """
        
        if isinstance(config, Config):
            config = config.to_dict()
        
        batch_limit = TIER_LIMITS[self.tier]['batch']
        if len(data_points) > batch_limit and mode == 'sync':
            raise ValidationError(f"Batch ({len(data_points)}) exceeds {self.tier} limit for sync mode ({batch_limit}). Use mode='async'.")
        
        t0 = time.time()
        payload = self._prepare_payload(data_points, config)
        
        try:
            if mode == 'async':
                if self.tier == 'community':
                    raise ValidationError("mode='async' is not available for 'community' tier.")
                
                # --- Flujo Asíncrono ---
                endpoint = f"{self.base_url}/enqueue"
                resp = self.session.post(endpoint, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                job_data = resp.json()
                logger.info(f"Async job {job_data.get('job_id')} enqueued in {time.time()-t0:.2f}s")
                return Job(job_id=job_data['job_id'], sdk=self, status=job_data.get('status', 'queued'))

            else:
                # --- Flujo Síncrono ---
                endpoint = f"{self.base_url}/evaluate"
                resp = self.session.post(endpoint, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                scores = resp.json()['scores']
                logger.info(f"Sync evaluation completed in {time.time()-t0:.2f}s")
                return [EvaluationResult(score=float(s), tier=self.tier) for s in scores]

        except requests.exceptions.HTTPError as e:
            try: data = e.response.json()
            except: data = {'error': e.response.text}
            raise APIError(f"API Error {e.response.status_code}: {data.get('error')}")
        except Exception as e:
            raise APIError(f"Evaluation failed: {e}")
    
    def get_job_status(self, job_id: str) -> Dict:
        """Consulta el estado de un job asíncrono"""
        try:
            endpoint = f"{self.base_url}/status/{job_id}"
            resp = self.session.get(endpoint, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            try: data = e.response.json()
            except: data = {'error': e.response.text}
            raise APIError(f"API Error {e.response.status_code}: {data.get('error')}")
        except Exception as e:
            raise APIError(f"Status check failed: {e}")

    def create_config(self) -> Config:
        return Config()
    
    def close(self):
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
