"""
Ailoos Python SDK - Client Module
Cliente principal para interactuar con la plataforma Ailoos
"""

import requests
import json
import websocket
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from .config import Config
from .exceptions import AiloosError, AuthenticationError, ValidationError


class AiloosClient:
    """
    Cliente principal para la plataforma Ailoos

    Args:
        api_key (str): Clave API para autenticación
        base_url (str): URL base de la API (default: http://localhost:8000)
        config (Config): Configuración personalizada
    """

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000", config: Optional[Config] = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.config = config or Config()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': f'Ailoos-Python-SDK/{self.config.version}'
        })
        self.ws_client = None
        self.ws_thread = None
        self.event_handlers = {}

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Realizar petición HTTP a la API"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 400:
                raise ValidationError(f"Validation error: {response.text}")
            else:
                raise AiloosError(f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            raise AiloosError(f"Request failed: {str(e)}")

    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema"""
        return self._make_request('GET', '/api/dashboard/status')

    def get_nodes(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Obtener lista de nodos"""
        params = {'limit': limit, 'offset': offset}
        return self._make_request('GET', '/api/dashboard/nodes', params=params)

    def get_training_status(self) -> Dict[str, Any]:
        """Obtener estado del entrenamiento"""
        return self._make_request('GET', '/api/dashboard/training/status')

    def start_training(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Iniciar sesión de entrenamiento"""
        return self._make_request('POST', '/api/dashboard/training/control',
                                json={'action': 'start', 'parameters': config})

    def stop_training(self) -> Dict[str, Any]:
        """Detener entrenamiento"""
        return self._make_request('POST', '/api/dashboard/training/control',
                                json={'action': 'stop'})

    def get_energy_metrics(self) -> Dict[str, Any]:
        """Obtener métricas energéticas"""
        return self._make_request('GET', '/api/dashboard/energy/metrics')

    def get_dao_status(self) -> Dict[str, Any]:
        """Obtener estado de gobernanza DAO"""
        return self._make_request('GET', '/api/dashboard/dao/status')

    def vote_on_proposal(self, proposal_id: str, vote: str, amount: int) -> Dict[str, Any]:
        """Votar en propuesta DAO"""
        data = {
            'proposal_id': proposal_id,
            'vote': vote,
            'dracmas_amount': amount
        }
        return self._make_request('POST', '/api/dashboard/dao/vote', json=data)

    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generar texto usando modelos de IA"""
        data = {'prompt': prompt, **kwargs}
        return self._make_request('POST', '/api/ai/generate/text', json=data)

    def analyze_image(self, image_url: str, **kwargs) -> Dict[str, Any]:
        """Analizar imagen"""
        data = {'image_url': image_url, **kwargs}
        return self._make_request('POST', '/api/ai/analyze/image', json=data)

    def process_multimodal(self, text: str, image_url: str = None, **kwargs) -> Dict[str, Any]:
        """Procesamiento multimodal"""
        data = {'text': text, 'image_url': image_url, **kwargs}
        return self._make_request('POST', '/api/ai/multimodal/process', json=data)

    def connect_websocket(self, on_message: Callable[[Dict[str, Any]], None]) -> None:
        """Conectar a WebSocket para actualizaciones en tiempo real"""
        def ws_thread():
            try:
                self.ws_client = websocket.WebSocketApp(
                    f"ws://{self.base_url.split('://')[1]}/ws/dashboard",
                    header={'Authorization': f'Bearer {self.api_key}'},
                    on_message=lambda ws, message: on_message(json.loads(message)),
                    on_error=lambda ws, error: print(f"WebSocket error: {error}"),
                    on_close=lambda ws: print("WebSocket connection closed")
                )
                self.ws_client.run_forever()
            except Exception as e:
                print(f"WebSocket connection failed: {e}")

        self.ws_thread = threading.Thread(target=ws_thread, daemon=True)
        self.ws_thread.start()

    def disconnect_websocket(self) -> None:
        """Desconectar WebSocket"""
        if self.ws_client:
            self.ws_client.close()
        if self.ws_thread:
            self.ws_thread.join(timeout=1)

    def subscribe_to_events(self, event_type: str, handler: Callable) -> None:
        """Suscribirse a eventos específicos"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def _handle_websocket_message(self, message: Dict[str, Any]) -> None:
        """Manejar mensajes WebSocket"""
        event_type = message.get('type', 'unknown')
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(message)
                except Exception as e:
                    print(f"Error in event handler: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect_websocket()