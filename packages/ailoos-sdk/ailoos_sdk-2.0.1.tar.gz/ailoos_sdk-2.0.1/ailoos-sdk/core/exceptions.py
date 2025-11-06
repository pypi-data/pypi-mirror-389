"""
Ailoos Python SDK - Exceptions Module
Excepciones personalizadas del SDK
"""

import json
import requests
from typing import Dict, Any


class AiloosError(Exception):
    """
    Excepción base para errores de Ailoos

    Args:
        message (str): Mensaje de error
        code (str): Código de error
        details (dict): Detalles adicionales del error
    """

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self):
        if self.details:
            return f"[{self.code}] {self.message} - Details: {self.details}"
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> dict:
        """Convertir excepción a diccionario"""
        return {
            'error': {
                'code': self.code,
                'message': self.message,
                'details': self.details
            }
        }


class AuthenticationError(AiloosError):
    """
    Error de autenticación
    """

    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class ValidationError(AiloosError):
    """
    Error de validación
    """

    def __init__(self, message: str = "Validation failed", details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class NetworkError(AiloosError):
    """
    Error de red
    """

    def __init__(self, message: str = "Network error", details: dict = None):
        super().__init__(message, "NETWORK_ERROR", details)


class APIError(AiloosError):
    """
    Error de API
    """

    def __init__(self, message: str = "API error", status_code: int = None, details: dict = None):
        super().__init__(message, "API_ERROR", details)
        self.status_code = status_code

    def __str__(self):
        if self.status_code:
            return f"[{self.code}] HTTP {self.status_code}: {self.message}"
        return super().__str__()


class RateLimitError(APIError):
    """
    Error de límite de tasa
    """

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, details: dict = None):
        super().__init__(message, 429, details)
        self.retry_after = retry_after

    def __str__(self):
        if self.retry_after:
            return f"[{self.code}] Rate limit exceeded. Retry after {self.retry_after} seconds"
        return super().__str__()


class TimeoutError(AiloosError):
    """
    Error de timeout
    """

    def __init__(self, message: str = "Request timeout", timeout: float = None, details: dict = None):
        super().__init__(message, "TIMEOUT_ERROR", details)
        self.timeout = timeout

    def __str__(self):
        if self.timeout:
            return f"[{self.code}] Request timeout after {self.timeout}s: {self.message}"
        return super().__str__()


class ConfigurationError(AiloosError):
    """
    Error de configuración
    """

    def __init__(self, message: str = "Configuration error", details: dict = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ModelError(AiloosError):
    """
    Error relacionado con modelos de IA
    """

    def __init__(self, message: str = "Model error", model_name: str = None, details: dict = None):
        super().__init__(message, "MODEL_ERROR", details)
        self.model_name = model_name

    def __str__(self):
        if self.model_name:
            return f"[{self.code}] Model '{self.model_name}': {self.message}"
        return super().__str__()


class TrainingError(AiloosError):
    """
    Error durante el entrenamiento
    """

    def __init__(self, message: str = "Training error", session_id: str = None, details: dict = None):
        super().__init__(message, "TRAINING_ERROR", details)
        self.session_id = session_id

    def __str__(self):
        if self.session_id:
            return f"[{self.code}] Training session '{self.session_id}': {self.message}"
        return super().__str__()


class BlockchainError(AiloosError):
    """
    Error relacionado con blockchain
    """

    def __init__(self, message: str = "Blockchain error", tx_hash: str = None, details: dict = None):
        super().__init__(message, "BLOCKCHAIN_ERROR", details)
        self.tx_hash = tx_hash

    def __str__(self):
        if self.tx_hash:
            return f"[{self.code}] Transaction {self.tx_hash}: {self.message}"
        return super().__str__()


class P2PError(AiloosError):
    """
    Error en red P2P
    """

    def __init__(self, message: str = "P2P network error", node_id: str = None, details: dict = None):
        super().__init__(message, "P2P_ERROR", details)
        self.node_id = node_id

    def __str__(self):
        if self.node_id:
            return f"[{self.code}] Node '{self.node_id}': {self.message}"
        return super().__str__()


class ResourceError(AiloosError):
    """
    Error de recursos
    """

    def __init__(self, message: str = "Resource error", resource_type: str = None, details: dict = None):
        super().__init__(message, "RESOURCE_ERROR", details)
        self.resource_type = resource_type

    def __str__(self):
        if self.resource_type:
            return f"[{self.code}] Resource '{self.resource_type}': {self.message}"
        return super().__str__()


class SecurityError(AiloosError):
    """
    Error de seguridad
    """

    def __init__(self, message: str = "Security error", threat_level: str = None, details: dict = None):
        super().__init__(message, "SECURITY_ERROR", details)
        self.threat_level = threat_level

    def __str__(self):
        if self.threat_level:
            return f"[{self.code}] {self.threat_level.upper()} threat: {self.message}"
        return super().__str__()


# Mapeo de códigos de error HTTP a excepciones
HTTP_ERROR_MAPPING = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthenticationError,
    404: APIError,
    429: RateLimitError,
    500: APIError,
    502: NetworkError,
    503: APIError,
    504: TimeoutError,
}


def create_error_from_response(status_code: int, response_text: str) -> AiloosError:
    """
    Crear excepción desde respuesta HTTP

    Args:
        status_code (int): Código de estado HTTP
        response_text (str): Texto de respuesta

    Returns:
        AiloosError: Excepción apropiada
    """
    error_class = HTTP_ERROR_MAPPING.get(status_code, AiloosError)

    try:
        response_data = json.loads(response_text)
        if 'error' in response_data:
            error_info = response_data['error']
            return error_class(
                error_info.get('message', response_text),
                error_info.get('code', f"HTTP_{status_code}"),
                error_info.get('details', {})
            )
    except (json.JSONDecodeError, KeyError):
        pass

    return error_class(f"HTTP {status_code}: {response_text}")


# Función helper para manejo de errores
def handle_api_error(func):
    """
    Decorador para manejo automático de errores de API

    Args:
        func: Función a decorar

    Returns:
        Función decorada
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.HTTPError as e:
            raise create_error_from_response(e.response.status_code, e.response.text)
        except requests.Timeout:
            raise TimeoutError("Request timeout")
        except requests.ConnectionError:
            raise NetworkError("Connection failed")
        except Exception as e:
            raise AiloosError(f"Unexpected error: {str(e)}")

    return wrapper