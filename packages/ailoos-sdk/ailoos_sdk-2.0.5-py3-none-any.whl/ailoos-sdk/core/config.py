"""
Ailoos Python SDK - Configuration Module
Configuración y gestión de parámetros del SDK
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    Configuración del SDK de Ailoos

    Args:
        version (str): Versión del SDK
        timeout (int): Timeout para requests HTTP
        max_retries (int): Número máximo de reintentos
        retry_delay (float): Delay entre reintentos
        debug (bool): Modo debug
        cache_enabled (bool): Habilitar cache
        cache_ttl (int): TTL del cache en segundos
    """

    version: str = "2.0.0"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    debug: bool = False
    cache_enabled: bool = True
    cache_ttl: int = 300

    # Configuración de red
    network_timeout: int = 10
    websocket_timeout: int = 30
    connection_pool_size: int = 10

    # Configuración de IA
    default_model: str = "empiorio-lm-2b"
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9

    # Configuración de seguridad
    verify_ssl: bool = True
    encryption_level: str = "high"

    # Configuración de logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    def __post_init__(self):
        """Configuración post-inicialización"""
        self._load_from_env()

    def _load_from_env(self):
        """Cargar configuración desde variables de entorno"""
        env_mappings = {
            'AILOOS_TIMEOUT': ('timeout', int),
            'AILOOS_MAX_RETRIES': ('max_retries', int),
            'AILOOS_DEBUG': ('debug', lambda x: x.lower() in ('true', '1', 'yes')),
            'AILOOS_CACHE_ENABLED': ('cache_enabled', lambda x: x.lower() in ('true', '1', 'yes')),
            'AILOOS_DEFAULT_MODEL': ('default_model', str),
            'AILOOS_MAX_TOKENS': ('max_tokens', int),
            'AILOOS_TEMPERATURE': ('temperature', float),
            'AILOOS_LOG_LEVEL': ('log_level', str),
            'AILOOS_LOG_FILE': ('log_file', str),
            'AILOOS_VERIFY_SSL': ('verify_ssl', lambda x: x.lower() in ('true', '1', 'yes')),
        }

        for env_var, (attr, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    setattr(self, attr, converter(value))
                except (ValueError, TypeError):
                    if self.debug:
                        print(f"Warning: Invalid value for {env_var}: {value}")

    def to_dict(self) -> Dict[str, Any]:
        """Convertir configuración a diccionario"""
        return {
            'version': self.version,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'debug': self.debug,
            'cache_enabled': self.cache_enabled,
            'cache_ttl': self.cache_ttl,
            'network_timeout': self.network_timeout,
            'websocket_timeout': self.websocket_timeout,
            'connection_pool_size': self.connection_pool_size,
            'default_model': self.default_model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'verify_ssl': self.verify_ssl,
            'encryption_level': self.encryption_level,
            'log_level': self.log_level,
            'log_file': self.log_file,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """Crear configuración desde diccionario"""
        return cls(**config_dict)

    def save_to_file(self, filepath: str) -> None:
        """Guardar configuración en archivo JSON"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'Config':
        """Cargar configuración desde archivo JSON"""
        import json
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)

    def merge(self, other: 'Config') -> 'Config':
        """Fusionar con otra configuración"""
        current_dict = self.to_dict()
        other_dict = other.to_dict()
        merged_dict = {**current_dict, **other_dict}
        return Config.from_dict(merged_dict)

    def validate(self) -> bool:
        """Validar configuración"""
        errors = []

        if self.timeout <= 0:
            errors.append("timeout must be positive")

        if self.max_retries < 0:
            errors.append("max_retries must be non-negative")

        if not (0 <= self.temperature <= 2):
            errors.append("temperature must be between 0 and 2")

        if not (0 <= self.top_p <= 1):
            errors.append("top_p must be between 0 and 1")

        if self.max_tokens <= 0:
            errors.append("max_tokens must be positive")

        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            errors.append("log_level must be a valid logging level")

        if errors:
            if self.debug:
                print("Configuration validation errors:")
                for error in errors:
                    print(f"  - {error}")
            return False

        return True