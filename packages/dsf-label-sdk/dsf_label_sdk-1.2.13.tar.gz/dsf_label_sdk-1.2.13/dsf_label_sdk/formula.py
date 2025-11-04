# dsf_label_sdk/formula.py
"""
Similarity calculations and Enterprise adjustments
Standard formula is PROTECTED in Cloud Run
"""
import numpy as np
from typing import Dict, List, Any, Optional
from collections import deque

EPSILON = 1e-10

def calculate_similarity(value: Any, reference: Any, field_cfg: Dict) -> float:
    """Calcula similitud 0-1 entre value y reference"""
    is_categorical = field_cfg.get("type") == "categorical"
    
    if value is None or reference is None:
        return float(field_cfg.get("categorical_floor", 0.0)) if is_categorical else 0.0
    
    if is_categorical:
        if isinstance(value, (int, float)) and isinstance(reference, (int, float)):
            return 1.0 if float(value) == float(reference) else float(field_cfg.get("categorical_floor", 0.0))
        return 1.0 if value == reference else float(field_cfg.get("categorical_floor", 0.0))
    
    if isinstance(value, (int, float)) and isinstance(reference, (int, float)):
        v, r = float(value), float(reference)
        if not (abs(v) < float('inf') and abs(r) < float('inf')):
            return 0.0
        d = abs(v) + abs(r)
        if d < EPSILON:
            return 1.0
        return max(0.0, min(1.0, 1.0 - abs(v - r) / (d + EPSILON)))
    
    if isinstance(value, str) and isinstance(reference, str):
        return 1.0 if value == reference else 0.3
    
    if isinstance(value, bool) and isinstance(reference, bool):
        return float(value == reference)
    
    return 0.5

def calculate_similarities_batch(
    data_batch: List[Dict[str, Any]], 
    config: Dict[str, Any]
) -> List[List[float]]:
    """
    Calcula similitudes para batch completo.
    Returns: [[sim_field1, sim_field2, ...], ...]
    """
    fields = list(config.keys())
    similarities_batch = []
    
    for data_point in data_batch:
        sims = []
        for field in fields:
            field_cfg = config[field]
            value = data_point.get(field)
            reference = field_cfg['default']
            sim = calculate_similarity(value, reference, field_cfg)
            sims.append(sim)
        similarities_batch.append(sims)
    
    return similarities_batch


class EnterpriseAdjuster:
    """
    Enterprise adjustments sobre scores base de Cloud Run.
    - Autopesos basados en magnitud
    - Threshold adaptativo
    - Tracking historial
    """
    
    def __init__(self, max_history: int = 100, adjustment_factor: float = 0.3):
        self.max_history = max_history
        self.adjustment_factor = adjustment_factor
        self.threshold = 0.65
        self.history = deque(maxlen=max_history)
        self.magnitude_stats = {}
    
    def adjust_scores(
        self,
        base_scores: List[float],
        similarities_batch: List[List[float]],
        config: Dict[str, Any],
        mode: str = 'standard'
    ) -> tuple[List[float], Dict[str, Any]]:
        """
        Aplica ajustes Enterprise sobre scores Standard.
        
        Args:
            base_scores: Scores de Cloud Run (Standard)
            similarities_batch: Similitudes calculadas localmente
            config: Configuración de campos
            mode: 'standard' o 'temporal_forgetting'
        
        Returns:
            (adjusted_scores, metadata)
        """
        # Actualizar magnitude stats
        self._update_magnitude_stats(similarities_batch, config)
        
        # Calcular pesos optimizados
        fields = list(config.keys())
        optimized_weights = []
        for field in fields:
            w = float(config[field]['weight'])
            stats = self.magnitude_stats.get(field, {})
            
            if stats.get('n', 0) > 5:
                magnitude = np.sqrt(stats['sum']) if stats.get('sum', 0) > 0 else 0.0
                prop_w = magnitude / (magnitude + 1.0) if magnitude > 0 else 0.5
                final_w = (1 - self.adjustment_factor) * w + self.adjustment_factor * prop_w
                optimized_weights.append(final_w)
            else:
                optimized_weights.append(w)
        
        # Aplicar ajuste proporcional sobre scores base
        weight_multiplier = np.mean(optimized_weights) / np.mean([config[f]['weight'] for f in fields])
        adjusted_scores = [min(1.0, s * weight_multiplier) for s in base_scores]
        
        # Actualizar threshold
        for score in adjusted_scores:
            self.history.append(score)
        
        if len(self.history) >= 10:
            if mode == 'temporal_forgetting' and len(self.history) >= 20:
                window = list(self.history)[-20:]
                avg = np.mean(window)
            else:
                avg = np.mean(list(self.history)[-10:])
            
            adjustment = (avg - 0.5) * (0.15 if mode == 'temporal_forgetting' else 0.1)
            self.threshold = np.clip(0.65 + adjustment, 0.4, 0.9)
        
        metadata = {
            'threshold': float(self.threshold),
            'history_size': len(self.history),
            'field_stats': {
                f: {
                    'n': self.magnitude_stats[f]['n'],
                    'mean': float(self.magnitude_stats[f]['mean'])
                }
                for f in fields if f in self.magnitude_stats
            }
        }
        
        return adjusted_scores, metadata
    
    def _update_magnitude_stats(self, similarities_batch: List[List[float]], config: Dict):
        """Actualiza estadísticas de magnitud por campo"""
        fields = list(config.keys())
        
        for i, field in enumerate(fields):
            if field not in self.magnitude_stats:
                self.magnitude_stats[field] = {'n': 0, 'mean': 0.0, 'M2': 0.0, 'sum': 0.0}
            
            stats = self.magnitude_stats[field]
            for sims in similarities_batch:
                if i < len(sims):
                    x = abs(float(sims[i]))
                    stats['n'] += 1
                    delta = x - stats['mean']
                    stats['mean'] += delta / stats['n']
                    stats['M2'] += delta * (x - stats['mean'])
                    stats['sum'] += x
