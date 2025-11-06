"""
Ailoos Python SDK
SDK oficial de Python para la plataforma Ailoos - IA distribuida a escala global
"""

from .core import AiloosClient, Config, AiloosError, AuthenticationError, ValidationError, NetworkError, APIError

# Módulos AI
from .ai import TextGenerator, ImageAnalyzer, MultimodalProcessor, ModelManager

# Módulos Blockchain
from .blockchain import DracmaSManager, DAOVoting, SmartContractManager, AuditTrail

# Módulos P2P
from .p2p import NodeManager, IPFSStorage, NodeDiscovery, P2PMessaging

__version__ = "2.0.1"
__author__ = "Ailoos Team"
__email__ = "team@ailoos.ai"
__description__ = "Python SDK for Ailoos distributed AI platform"
__url__ = "https://github.com/ailoos/ailoos-python-sdk"

__all__ = [
    # Core
    'AiloosClient',
    'Config',
    'AiloosError',
    'AuthenticationError',
    'ValidationError',
    'NetworkError',
    'APIError',

    # AI
    'TextGenerator',
    'ImageAnalyzer',
    'MultimodalProcessor',
    'ModelManager',

    # Blockchain
    'DracmaSManager',
    'DAOVoting',
    'SmartContractManager',
    'AuditTrail',

    # P2P
    'NodeManager',
    'IPFSStorage',
    'NodeDiscovery',
    'P2PMessaging'
]

def quick_start():
    """
    Función de inicio rápido para nuevos usuarios

    Returns:
        str: Guía de inicio rápido
    """
    return """
🚀 Inicio Rápido con Ailoos Python SDK

1. Instalar el SDK:
   pip install ailoos-sdk

2. Configurar credenciales:
   export AILOOS_API_KEY="tu_api_key"
   export AILOOS_BASE_URL="https://api.ailoos.ai"

3. Primer uso:
   from ailoos_sdk import AiloosClient, TextGenerator

   client = AiloosClient()
   text_gen = TextGenerator(client)

   response = text_gen.generate("Hola, ¿cómo estás?")
   print(response['text'])

📚 Para más información, visita: https://docs.ailoos.ai/python-sdk/
"""

def get_version():
    """
    Obtener versión del SDK

    Returns:
        str: Versión del SDK
    """
    return __version__

def get_capabilities():
    """
    Obtener capacidades del SDK

    Returns:
        Dict: Capacidades disponibles
    """
    return {
        'ai': {
            'text_generation': True,
            'image_analysis': True,
            'multimodal': True,
            'model_management': True
        },
        'blockchain': {
            'dracmas_management': True,
            'dao_voting': True,
            'smart_contracts': True,
            'audit_trail': True
        },
        'p2p': {
            'node_management': True,
            'ipfs_storage': True,
            'node_discovery': True,
            'messaging': True
        },
        'features': {
            'federated_learning': True,
            'quantum_acceleration': True,
            'zk_proofs': True,
            'green_computing': True,
            'dao_governance': True
        }
    }

# Información de compatibilidad
COMPATIBILITY = {
    'python_versions': ['3.8', '3.9', '3.10', '3.11', '3.12'],
    'platforms': ['Linux', 'macOS', 'Windows'],
    'architectures': ['x86_64', 'arm64']
}

# Configuración por defecto
DEFAULT_CONFIG = {
    'timeout': 30,
    'max_retries': 3,
    'debug': False,
    'cache_enabled': True,
    'quantum_enabled': False
}