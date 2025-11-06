"""
Ailoos Python SDK - Core Module
Núcleo del SDK de Ailoos para Python
"""

__version__ = "2.0.0"
__author__ = "Ailoos Team"
__description__ = "Python SDK for Ailoos distributed AI platform"

from .client import AiloosClient
from .config import Config
from .exceptions import AiloosError, AuthenticationError, ValidationError

__all__ = [
    'AiloosClient',
    'Config',
    'AiloosError',
    'AuthenticationError',
    'ValidationError'
]