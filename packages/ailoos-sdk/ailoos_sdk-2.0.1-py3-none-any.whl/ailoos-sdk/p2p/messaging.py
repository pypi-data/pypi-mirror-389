"""
Ailoos Python SDK - P2P Messaging Module
Sistema de mensajería peer-to-peer
"""

from typing import Dict, List, Optional, Any, Callable
from ..core.client import AiloosClient
from ..core.exceptions import P2PError, ValidationError


class P2PMessaging:
    """
    Sistema de mensajería P2P para Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
        node_id (str): ID del nodo local
    """

    def __init__(self, client: AiloosClient, node_id: Optional[str] = None):
        self.client = client
        self.node_id = node_id
        self.message_handlers = {}
        self.event_handlers = {}

    def send_message(
        self,
        recipient_id: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: str = "normal",
        ttl_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        Enviar mensaje a un nodo específico

        Args:
            recipient_id (str): ID del nodo destinatario
            message_type (str): Tipo de mensaje
            payload (Dict[str, Any]): Contenido del mensaje
            priority (str): Prioridad ('low', 'normal', 'high', 'urgent')
            ttl_seconds (int): Tiempo de vida en segundos

        Returns:
            Dict[str, Any]: Confirmación de envío
        """
        if not self.node_id:
            raise ValidationError("Node ID is required to send messages")

        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if priority not in valid_priorities:
            raise ValidationError(f"Priority must be one of: {', '.join(valid_priorities)}")

        data = {
            'sender_id': self.node_id,
            'recipient_id': recipient_id,
            'message_type': message_type,
            'payload': payload,
            'priority': priority,
            'ttl_seconds': ttl_seconds
        }

        try:
            return self.client._make_request('POST', '/api/messaging/send', json=data)
        except Exception as e:
            raise P2PError(f"Failed to send message: {str(e)}")

    def broadcast_message(
        self,
        message_type: str,
        payload: Dict[str, Any],
        target_criteria: Optional[Dict[str, Any]] = None,
        max_recipients: int = 100
    ) -> Dict[str, Any]:
        """
        Transmitir mensaje a múltiples nodos

        Args:
            message_type (str): Tipo de mensaje
            payload (Dict[str, Any]): Contenido del mensaje
            target_criteria (Dict[str, Any]): Criterios para seleccionar destinatarios
            max_recipients (int): Número máximo de destinatarios

        Returns:
            Dict[str, Any]: Confirmación de transmisión
        """
        if not self.node_id:
            raise ValidationError("Node ID is required to broadcast messages")

        data = {
            'sender_id': self.node_id,
            'message_type': message_type,
            'payload': payload,
            'max_recipients': max_recipients
        }

        if target_criteria:
            data['target_criteria'] = target_criteria

        try:
            return self.client._make_request('POST', '/api/messaging/broadcast', json=data)
        except Exception as e:
            raise P2PError(f"Failed to broadcast message: {str(e)}")

    def get_messages(
        self,
        message_type: Optional[str] = None,
        sender_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtener mensajes recibidos

        Args:
            message_type (str): Filtrar por tipo de mensaje
            sender_id (str): Filtrar por remitente
            limit (int): Número máximo de mensajes
            offset (int): Offset para paginación

        Returns:
            List[Dict[str, Any]]: Lista de mensajes
        """
        if not self.node_id:
            raise ValidationError("Node ID is required to get messages")

        params = {
            'recipient_id': self.node_id,
            'limit': limit,
            'offset': offset
        }

        if message_type:
            params['message_type'] = message_type
        if sender_id:
            params['sender_id'] = sender_id

        try:
            response = self.client._make_request('GET', '/api/messaging/messages', params=params)
            return response.get('messages', [])
        except Exception as e:
            raise P2PError(f"Failed to get messages: {str(e)}")

    def mark_message_read(self, message_id: str) -> Dict[str, Any]:
        """
        Marcar mensaje como leído

        Args:
            message_id (str): ID del mensaje

        Returns:
            Dict[str, Any]: Confirmación
        """
        data = {'message_id': message_id}

        try:
            return self.client._make_request('PUT', '/api/messaging/mark-read', json=data)
        except Exception as e:
            raise P2PError(f"Failed to mark message as read: {str(e)}")

    def delete_message(self, message_id: str) -> Dict[str, Any]:
        """
        Eliminar mensaje

        Args:
            message_id (str): ID del mensaje

        Returns:
            Dict[str, Any]: Confirmación de eliminación
        """
        try:
            return self.client._make_request('DELETE', f'/api/messaging/messages/{message_id}')
        except Exception as e:
            raise P2PError(f"Failed to delete message: {str(e)}")

    def get_message_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de mensajería

        Returns:
            Dict[str, Any]: Estadísticas de mensajes
        """
        if not self.node_id:
            raise ValidationError("Node ID is required")

        try:
            return self.client._make_request('GET', f'/api/messaging/stats/{self.node_id}')
        except Exception as e:
            raise P2PError(f"Failed to get message stats: {str(e)}")

    def send_training_request(
        self,
        target_nodes: List[str],
        model_config: Dict[str, Any],
        dataset_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enviar solicitud de entrenamiento a nodos

        Args:
            target_nodes (List[str]): IDs de nodos destino
            model_config (Dict[str, Any]): Configuración del modelo
            dataset_info (Dict[str, Any]): Información del dataset

        Returns:
            Dict[str, Any]: Confirmación de envío
        """
        payload = {
            'model_config': model_config,
            'dataset_info': dataset_info,
            'request_type': 'training'
        }

        return self.broadcast_message(
            message_type='training_request',
            payload=payload,
            target_criteria={'node_ids': target_nodes}
        )

    def send_gradient_update(
        self,
        coordinator_id: str,
        gradients: Dict[str, Any],
        model_version: str
    ) -> Dict[str, Any]:
        """
        Enviar actualización de gradientes al coordinador

        Args:
            coordinator_id (str): ID del coordinador
            gradients (Dict[str, Any]): Gradientes del modelo
            model_version (str): Versión del modelo

        Returns:
            Dict[str, Any]: Confirmación de envío
        """
        payload = {
            'gradients': gradients,
            'model_version': model_version,
            'node_id': self.node_id
        }

        return self.send_message(
            recipient_id=coordinator_id,
            message_type='gradient_update',
            payload=payload,
            priority='high'
        )

    def request_model_weights(
        self,
        source_node_id: str,
        model_name: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Solicitar pesos de modelo a otro nodo

        Args:
            source_node_id (str): ID del nodo fuente
            model_name (str): Nombre del modelo
            version (str): Versión específica (opcional)

        Returns:
            Dict[str, Any]: Confirmación de solicitud
        """
        payload = {
            'model_name': model_name,
            'version': version,
            'requester_id': self.node_id
        }

        return self.send_message(
            recipient_id=source_node_id,
            message_type='model_weights_request',
            payload=payload
        )

    def send_heartbeat(self) -> Dict[str, Any]:
        """
        Enviar heartbeat para mantener conexión activa

        Returns:
            Dict[str, Any]: Confirmación de heartbeat
        """
        if not self.node_id:
            raise ValidationError("Node ID is required")

        payload = {
            'timestamp': None,  # Se establece en el servidor
            'node_status': 'active'
        }

        return self.broadcast_message(
            message_type='heartbeat',
            payload=payload,
            max_recipients=10  # Solo a nodos cercanos
        )

    def subscribe_to_messages(
        self,
        message_type: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Suscribirse a un tipo de mensaje

        Args:
            message_type (str): Tipo de mensaje
            handler (Callable): Función manejadora
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)

    def unsubscribe_from_messages(
        self,
        message_type: str,
        handler: Optional[Callable] = None
    ) -> None:
        """
        Cancelar suscripción a mensajes

        Args:
            message_type (str): Tipo de mensaje
            handler (Callable): Handler específico (None = todos)
        """
        if message_type in self.message_handlers:
            if handler:
                if handler in self.message_handlers[message_type]:
                    self.message_handlers[message_type].remove(handler)
            else:
                del self.message_handlers[message_type]

    def subscribe_to_events(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Suscribirse a eventos de la red

        Args:
            event_type (str): Tipo de evento
            handler (Callable): Función manejadora
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def process_incoming_messages(self) -> None:
        """
        Procesar mensajes entrantes (llamar periódicamente)
        """
        try:
            messages = self.get_messages()
            for message in messages:
                message_type = message.get('message_type')
                if message_type in self.message_handlers:
                    for handler in self.message_handlers[message_type]:
                        try:
                            handler(message)
                        except Exception as e:
                            print(f"Error in message handler: {e}")

                # Marcar como leído automáticamente
                self.mark_message_read(message['id'])
        except Exception as e:
            print(f"Error processing messages: {e}")

    def send_computation_result(
        self,
        requester_id: str,
        computation_id: str,
        result: Any,
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Enviar resultado de computación

        Args:
            requester_id (str): ID del solicitante
            computation_id (str): ID de la computación
            result (Any): Resultado de la computación
            execution_time (float): Tiempo de ejecución

        Returns:
            Dict[str, Any]: Confirmación de envío
        """
        payload = {
            'computation_id': computation_id,
            'result': result,
            'execution_time': execution_time,
            'executor_id': self.node_id
        }

        return self.send_message(
            recipient_id=requester_id,
            message_type='computation_result',
            payload=payload
        )

    def request_data_shard(
        self,
        data_source_id: str,
        shard_index: int,
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Solicitar shard de datos

        Args:
            data_source_id (str): ID del nodo fuente de datos
            shard_index (int): Índice del shard
            dataset_name (str): Nombre del dataset

        Returns:
            Dict[str, Any]: Confirmación de solicitud
        """
        payload = {
            'shard_index': shard_index,
            'dataset_name': dataset_name,
            'requester_id': self.node_id
        }

        return self.send_message(
            recipient_id=data_source_id,
            message_type='data_shard_request',
            payload=payload
        )

    def send_data_shard(
        self,
        requester_id: str,
        shard_data: Any,
        shard_index: int,
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Enviar shard de datos

        Args:
            requester_id (str): ID del solicitante
            shard_data (Any): Datos del shard
            shard_index (int): Índice del shard
            dataset_name (str): Nombre del dataset

        Returns:
            Dict[str, Any]: Confirmación de envío
        """
        payload = {
            'shard_data': shard_data,
            'shard_index': shard_index,
            'dataset_name': dataset_name,
            'provider_id': self.node_id
        }

        return self.send_message(
            recipient_id=requester_id,
            message_type='data_shard_response',
            payload=payload,
            priority='high'
        )

    def broadcast_node_status(self, status: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Transmitir estado del nodo a la red

        Args:
            status (str): Estado del nodo
            details (Dict[str, Any]): Detalles adicionales

        Returns:
            Dict[str, Any]: Confirmación de transmisión
        """
        payload = {
            'node_id': self.node_id,
            'status': status,
            'timestamp': None,  # Se establece en el servidor
            'details': details or {}
        }

        return self.broadcast_message(
            message_type='node_status',
            payload=payload,
            max_recipients=20
        )

    def get_messaging_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas detalladas de mensajería

        Returns:
            Dict[str, Any]: Estadísticas de mensajería
        """
        if not self.node_id:
            raise ValidationError("Node ID is required")

        try:
            return self.client._make_request('GET', f'/api/messaging/detailed-stats/{self.node_id}')
        except Exception as e:
            raise P2PError(f"Failed to get messaging stats: {str(e)}")

    def set_node_id(self, node_id: str) -> None:
        """
        Establecer ID del nodo local

        Args:
            node_id (str): Nuevo ID del nodo
        """
        self.node_id = node_id

    def get_pending_messages_count(self) -> int:
        """
        Obtener número de mensajes pendientes

        Returns:
            int: Número de mensajes sin leer
        """
        try:
            stats = self.get_message_stats()
            return stats.get('pending_count', 0)
        except Exception:
            return 0