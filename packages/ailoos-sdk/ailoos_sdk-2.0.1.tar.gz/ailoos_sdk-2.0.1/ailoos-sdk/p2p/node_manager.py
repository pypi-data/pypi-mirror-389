"""
Ailoos Python SDK - Node Manager Module
Gestión de nodos en red P2P
"""

from typing import Dict, List, Optional, Any
from ..core.client import AiloosClient
from ..core.exceptions import P2PError, ValidationError


class NodeManager:
    """
    Gestor de nodos para red P2P de Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
        node_id (str): ID único del nodo local
    """

    def __init__(self, client: AiloosClient, node_id: Optional[str] = None):
        self.client = client
        self.node_id = node_id
        self.connected_nodes = []

    def register_node(
        self,
        node_info: Dict[str, Any],
        capabilities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Registrar nodo en la red P2P

        Args:
            node_info (Dict[str, Any]): Información del nodo
            capabilities (List[str]): Capacidades del nodo

        Returns:
            Dict[str, Any]: Confirmación de registro
        """
        data = {
            'node_info': node_info,
            'capabilities': capabilities or []
        }

        try:
            return self.client._make_request('POST', '/api/p2p/nodes/register', json=data)
        except Exception as e:
            raise P2PError(f"Failed to register node: {str(e)}")

    def get_connected_nodes(
        self,
        limit: int = 100,
        capabilities: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener lista de nodos conectados

        Args:
            limit (int): Número máximo de nodos
            capabilities (List[str]): Filtrar por capacidades

        Returns:
            List[Dict[str, Any]]: Lista de nodos conectados
        """
        params = {'limit': limit}
        if capabilities:
            params['capabilities'] = ','.join(capabilities)

        try:
            response = self.client._make_request('GET', '/api/p2p/nodes/connected', params=params)
            nodes = response.get('nodes', [])
            self.connected_nodes = nodes
            return nodes
        except Exception as e:
            raise P2PError(f"Failed to get connected nodes: {str(e)}")

    def connect_to_node(self, node_id: str, connection_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conectar a un nodo específico

        Args:
            node_id (str): ID del nodo a conectar
            connection_info (Dict[str, Any]): Información de conexión

        Returns:
            Dict[str, Any]: Confirmación de conexión
        """
        data = {
            'node_id': node_id,
            'connection_info': connection_info
        }

        try:
            return self.client._make_request('POST', '/api/p2p/nodes/connect', json=data)
        except Exception as e:
            raise P2PError(f"Failed to connect to node: {str(e)}")

    def disconnect_from_node(self, node_id: str) -> Dict[str, Any]:
        """
        Desconectar de un nodo

        Args:
            node_id (str): ID del nodo a desconectar

        Returns:
            Dict[str, Any]: Confirmación de desconexión
        """
        try:
            return self.client._make_request('DELETE', f'/api/p2p/nodes/{node_id}/disconnect')
        except Exception as e:
            raise P2PError(f"Failed to disconnect from node: {str(e)}")

    def get_node_info(self, node_id: str) -> Dict[str, Any]:
        """
        Obtener información detallada de un nodo

        Args:
            node_id (str): ID del nodo

        Returns:
            Dict[str, Any]: Información del nodo
        """
        try:
            return self.client._make_request('GET', f'/api/p2p/nodes/{node_id}')
        except Exception as e:
            raise P2PError(f"Failed to get node info: {str(e)}")

    def update_node_status(
        self,
        status: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Actualizar estado del nodo local

        Args:
            status (str): Nuevo estado ('online', 'busy', 'offline')
            additional_info (Dict[str, Any]): Información adicional

        Returns:
            Dict[str, Any]: Confirmación de actualización
        """
        if not self.node_id:
            raise ValidationError("Node ID is required to update status")

        data = {
            'node_id': self.node_id,
            'status': status,
            'additional_info': additional_info or {}
        }

        try:
            return self.client._make_request('PUT', '/api/p2p/nodes/status', json=data)
        except Exception as e:
            raise P2PError(f"Failed to update node status: {str(e)}")

    def get_network_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de la red P2P

        Returns:
            Dict[str, Any]: Estadísticas de la red
        """
        try:
            return self.client._make_request('GET', '/api/p2p/network/stats')
        except Exception as e:
            raise P2PError(f"Failed to get network stats: {str(e)}")

    def broadcast_message(
        self,
        message: Dict[str, Any],
        target_nodes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Transmitir mensaje a nodos de la red

        Args:
            message (Dict[str, Any]): Mensaje a transmitir
            target_nodes (List[str]): Nodos destino (None = broadcast)

        Returns:
            Dict[str, Any]: Confirmación de transmisión
        """
        data = {
            'message': message,
            'target_nodes': target_nodes
        }

        try:
            return self.client._make_request('POST', '/api/p2p/broadcast', json=data)
        except Exception as e:
            raise P2PError(f"Failed to broadcast message: {str(e)}")

    def send_direct_message(
        self,
        target_node: str,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enviar mensaje directo a un nodo

        Args:
            target_node (str): ID del nodo destino
            message (Dict[str, Any]): Mensaje a enviar

        Returns:
            Dict[str, Any]: Confirmación de envío
        """
        data = {
            'target_node': target_node,
            'message': message
        }

        try:
            return self.client._make_request('POST', '/api/p2p/message', json=data)
        except Exception as e:
            raise P2PError(f"Failed to send direct message: {str(e)}")

    def get_node_reputation(self, node_id: str) -> Dict[str, Any]:
        """
        Obtener reputación de un nodo

        Args:
            node_id (str): ID del nodo

        Returns:
            Dict[str, Any]: Información de reputación
        """
        try:
            return self.client._make_request('GET', f'/api/p2p/nodes/{node_id}/reputation')
        except Exception as e:
            raise P2PError(f"Failed to get node reputation: {str(e)}")

    def report_node_behavior(
        self,
        node_id: str,
        behavior_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Reportar comportamiento de un nodo

        Args:
            node_id (str): ID del nodo reportado
            behavior_type (str): Tipo de comportamiento ('malicious', 'unresponsive', 'good')
            details (Dict[str, Any]): Detalles adicionales

        Returns:
            Dict[str, Any]: Confirmación del reporte
        """
        data = {
            'reported_node': node_id,
            'behavior_type': behavior_type,
            'details': details or {}
        }

        try:
            return self.client._make_request('POST', '/api/p2p/report', json=data)
        except Exception as e:
            raise P2PError(f"Failed to report node behavior: {str(e)}")

    def get_node_resources(self, node_id: str) -> Dict[str, Any]:
        """
        Obtener recursos disponibles de un nodo

        Args:
            node_id (str): ID del nodo

        Returns:
            Dict[str, Any]: Recursos del nodo
        """
        try:
            return self.client._make_request('GET', f'/api/p2p/nodes/{node_id}/resources')
        except Exception as e:
            raise P2PError(f"Failed to get node resources: {str(e)}")

    def request_computation(
        self,
        computation_type: str,
        parameters: Dict[str, Any],
        target_nodes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Solicitar computación a nodos de la red

        Args:
            computation_type (str): Tipo de computación
            parameters (Dict[str, Any]): Parámetros de la computación
            target_nodes (List[str]): Nodos específicos (None = cualquier nodo disponible)

        Returns:
            Dict[str, Any]: Resultado de la solicitud
        """
        data = {
            'computation_type': computation_type,
            'parameters': parameters,
            'target_nodes': target_nodes
        }

        try:
            return self.client._make_request('POST', '/api/p2p/computation/request', json=data)
        except Exception as e:
            raise P2PError(f"Failed to request computation: {str(e)}")

    def get_computation_status(self, computation_id: str) -> Dict[str, Any]:
        """
        Obtener estado de una computación

        Args:
            computation_id (str): ID de la computación

        Returns:
            Dict[str, Any]: Estado de la computación
        """
        try:
            return self.client._make_request('GET', f'/api/p2p/computation/{computation_id}/status')
        except Exception as e:
            raise P2PError(f"Failed to get computation status: {str(e)}")

    def cancel_computation(self, computation_id: str) -> Dict[str, Any]:
        """
        Cancelar una computación

        Args:
            computation_id (str): ID de la computación

        Returns:
            Dict[str, Any]: Confirmación de cancelación
        """
        try:
            return self.client._make_request('DELETE', f'/api/p2p/computation/{computation_id}')
        except Exception as e:
            raise P2PError(f"Failed to cancel computation: {str(e)}")

    def get_network_topology(self) -> Dict[str, Any]:
        """
        Obtener topología de la red P2P

        Returns:
            Dict[str, Any]: Topología de la red
        """
        try:
            return self.client._make_request('GET', '/api/p2p/network/topology')
        except Exception as e:
            raise P2PError(f"Failed to get network topology: {str(e)}")

    def optimize_network_connections(self) -> Dict[str, Any]:
        """
        Optimizar conexiones de red

        Returns:
            Dict[str, Any]: Resultado de optimización
        """
        try:
            return self.client._make_request('POST', '/api/p2p/network/optimize')
        except Exception as e:
            raise P2PError(f"Failed to optimize network connections: {str(e)}")

    def get_node_health(self, node_id: str) -> Dict[str, Any]:
        """
        Obtener estado de salud de un nodo

        Args:
            node_id (str): ID del nodo

        Returns:
            Dict[str, Any]: Estado de salud
        """
        try:
            return self.client._make_request('GET', f'/api/p2p/nodes/{node_id}/health')
        except Exception as e:
            raise P2PError(f"Failed to get node health: {str(e)}")

    def set_node_id(self, node_id: str) -> None:
        """
        Establecer ID del nodo local

        Args:
            node_id (str): Nuevo ID del nodo
        """
        self.node_id = node_id

    def get_connected_node_count(self) -> int:
        """
        Obtener número de nodos conectados

        Returns:
            int: Número de nodos conectados
        """
        return len(self.connected_nodes)

    def refresh_node_list(self) -> None:
        """
        Actualizar lista de nodos conectados
        """
        try:
            self.get_connected_nodes()
        except Exception:
            pass  # Silently fail and keep old list