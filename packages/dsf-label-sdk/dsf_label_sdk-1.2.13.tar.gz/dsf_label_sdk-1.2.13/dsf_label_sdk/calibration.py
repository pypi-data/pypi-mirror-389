import numpy as np

class CalibrationProfile:
    """Calibra similitudes según dominio (vision/text/tabular/audio)"""
    
    def __init__(self, mode='auto'):
        self.mode = mode
    
    def calibrate(self, value: float, field_name: str) -> float:
        if self.mode == 'auto':
            return self._auto(value, field_name)
        elif self.mode == 'vision':
            return self._vision(value, field_name)
        elif self.mode == 'text':
            return self._text(value, field_name)
        elif self.mode == 'tabular':
            return self._tabular(value, field_name)
        return value
    
    def _auto(self, val, field):
        # Detectar tipo por nombre
        fl = field.lower()
        if any(x in fl for x in ['eva', 'clip', 'dino', 'siglip', 'vision', 'image']):
            return self._vision(val, field)
        elif any(x in fl for x in ['bert', 'gpt', 'text', 'embed']):
            return self._text(val, field)
        return val
    
    def _vision(self, val, field):
        # Cosine [-1,1] → [0,1] normalizado
        return (val + 1.0) / 2.0
    
    def _text(self, val, field):
        # Embeddings texto suelen [0.3-0.9]
        return np.clip((val - 0.3) / 0.6, 0, 1)
    
    def _tabular(self, val, field):
        # Z-score normalización básica
        return 1 / (1 + np.exp(-val))