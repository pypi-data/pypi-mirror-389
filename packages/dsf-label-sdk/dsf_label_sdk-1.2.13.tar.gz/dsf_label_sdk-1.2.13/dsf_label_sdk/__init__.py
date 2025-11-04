# dsf_label_sdk/__init__.py

__version__ = '1.2.13'
__author__ = 'Jaime Alexander Jimenez'
__email__ = 'contacto@softwarefinanzas.com.co'

from .client import LabelSDK
from .exceptions import (
    LabelSDKError,
    ValidationError, 
    LicenseError,
    APIError,
    RateLimitError 
)
from .models import Field, Config, EvaluationResult
from .formula import EnterpriseAdjuster, calculate_similarities_batch


__all__ = [
    'LabelSDK',
    'Field',
    'Config',
    'EvaluationResult',
    'LabelSDKError',
    'ValidationError',
    'LicenseError',
    'APIError',
    'RateLimitError',
    'EnterpriseAdjuster',
    'calculate_similarities_batch'
]