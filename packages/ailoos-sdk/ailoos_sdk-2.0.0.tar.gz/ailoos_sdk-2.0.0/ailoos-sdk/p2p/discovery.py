"""
Ailoos Python SDK - Node Discovery Module
Descubrimiento y gestión de nodos en la red P2P
"""

from typing import Dict, List, Optional, Any
from ..core.client import AiloosClient
from ..core.exceptions import P2PError, ValidationError


class NodeDiscovery:
    """
    Sistema de descubrimiento de nodos para Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
    """

    def __init__(self, client: AiloosClient):
        self.client = client

    def discover_nodes(
        self,
        criteria: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Descubrir nodos en la red P2P

        Args:
            criteria (Dict[str, Any]): Criterios de búsqueda
            limit (int): Número máximo de nodos a retornar

        Returns:
            List[Dict[str, Any]]: Lista de nodos descubiertos
        """
        params = {'limit': limit}
        if criteria:
            params.update(criteria)

        try:
            response = self.client._make_request('GET', '/api/discovery/nodes', params=params)
            return response.get('nodes', [])
        except Exception as e:
            raise P2PError(f"Failed to discover nodes: {str(e)}")

    def discover_by_capabilities(
        self,
        capabilities: List[str],
        min_reputation: float = 0.0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Descubrir nodos por capacidades específicas

        Args:
            capabilities (List[str]): Capacidades requeridas
            min_reputation (float): Reputación mínima requerida
            limit (int): Número máximo de nodos

        Returns:
            List[Dict[str, Any]]: Nodos que cumplen los criterios
        """
        criteria = {
            'capabilities': capabilities,
            'min_reputation': min_reputation
        }
        return self.discover_nodes(criteria, limit)

    def discover_by_location(
        self,
        country: Optional[str] = None,
        region: Optional[str] = None,
        max_distance_km: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Descubrir nodos por ubicación geográfica

        Args:
            country (str): País específico
            region (str): Región específica
            max_distance_km (float): Distancia máxima en km
            limit (int): Número máximo de nodos

        Returns:
            List[Dict[str, Any]]: Nodos en la ubicación especificada
        """
        criteria = {}
        if country:
            criteria['country'] = country
        if region:
            criteria['region'] = region
        if max_distance_km:
            criteria['max_distance'] = max_distance_km

        return self.discover_nodes(criteria, limit)

    def discover_by_resources(
        self,
        min_cpu_cores: Optional[int] = None,
        min_memory_gb: Optional[float] = None,
        has_gpu: Optional[bool] = None,
        gpu_memory_gb: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Descubrir nodos por recursos disponibles

        Args:
            min_cpu_cores (int): Número mínimo de núcleos CPU
            min_memory_gb (float): Memoria RAM mínima en GB
            has_gpu (bool): Requiere GPU
            gpu_memory_gb (float): Memoria GPU mínima en GB
            limit (int): Número máximo de nodos

        Returns:
            List[Dict[str, Any]]: Nodos con recursos suficientes
        """
        criteria = {}
        if min_cpu_cores:
            criteria['min_cpu_cores'] = min_cpu_cores
        if min_memory_gb:
            criteria['min_memory_gb'] = min_memory_gb
        if has_gpu is not None:
            criteria['has_gpu'] = has_gpu
        if gpu_memory_gb:
            criteria['gpu_memory_gb'] = gpu_memory_gb

        return self.discover_nodes(criteria, limit)

    def discover_training_nodes(
        self,
        model_type: str = "any",
        min_batch_size: int = 1,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Descubrir nodos especializados en entrenamiento

        Args:
            model_type (str): Tipo de modelo ('text', 'vision', 'multimodal', 'any')
            min_batch_size (int): Tamaño mínimo de batch
            limit (int): Número máximo de nodos

        Returns:
            List[Dict[str, Any]]: Nodos de entrenamiento disponibles
        """
        criteria = {
            'capability': 'training',
            'model_type': model_type,
            'min_batch_size': min_batch_size
        }
        return self.discover_nodes(criteria, limit)

    def discover_storage_nodes(
        self,
        min_storage_gb: float = 10.0,
        storage_type: str = "any",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Descubrir nodos especializados en almacenamiento

        Args:
            min_storage_gb (float): Almacenamiento mínimo en GB
            storage_type (str): Tipo de almacenamiento ('hdd', 'ssd', 'nvme', 'any')
            limit (int): Número máximo de nodos

        Returns:
            List[Dict[str, Any]]: Nodos de almacenamiento disponibles
        """
        criteria = {
            'capability': 'storage',
            'min_storage_gb': min_storage_gb,
            'storage_type': storage_type
        }
        return self.discover_nodes(criteria, limit)

    def discover_inference_nodes(
        self,
        model_name: Optional[str] = None,
        max_latency_ms: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Descubrir nodos especializados en inferencia

        Args:
            model_name (str): Nombre específico del modelo
            max_latency_ms (float): Latencia máxima en ms
            limit (int): Número máximo de nodos

        Returns:
            List[Dict[str, Any]]: Nodos de inferencia disponibles
        """
        criteria = {
            'capability': 'inference'
        }
        if model_name:
            criteria['model_name'] = model_name
        if max_latency_ms:
            criteria['max_latency_ms'] = max_latency_ms

        return self.discover_nodes(criteria, limit)

    def get_node_recommendations(
        self,
        task_type: str,
        requirements: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtener recomendaciones de nodos para una tarea específica

        Args:
            task_type (str): Tipo de tarea
            requirements (Dict[str, Any]): Requisitos específicos
            limit (int): Número máximo de recomendaciones

        Returns:
            List[Dict[str, Any]]: Nodos recomendados
        """
        data = {
            'task_type': task_type,
            'requirements': requirements,
            'limit': limit
        }

        try:
            response = self.client._make_request('POST', '/api/discovery/recommendations', json=data)
            return response.get('recommendations', [])
        except Exception as e:
            raise P2PError(f"Failed to get node recommendations: {str(e)}")

    def get_network_topology(self) -> Dict[str, Any]:
        """
        Obtener topología actual de la red

        Returns:
            Dict[str, Any]: Información de la topología
        """
        try:
            return self.client._make_request('GET', '/api/discovery/topology')
        except Exception as e:
            raise P2PError(f"Failed to get network topology: {str(e)}")

    def get_discovery_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de descubrimiento

        Returns:
            Dict[str, Any]: Estadísticas del sistema de descubrimiento
        """
        try:
            return self.client._make_request('GET', '/api/discovery/stats')
        except Exception as e:
            raise P2PError(f"Failed to get discovery stats: {str(e)}")

    def register_service(
        self,
        service_type: str,
        service_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Registrar un servicio en el sistema de descubrimiento

        Args:
            service_type (str): Tipo de servicio
            service_info (Dict[str, Any]): Información del servicio

        Returns:
            Dict[str, Any]: Confirmación de registro
        """
        data = {
            'service_type': service_type,
            'service_info': service_info
        }

        try:
            return self.client._make_request('POST', '/api/discovery/services', json=data)
        except Exception as e:
            raise P2PError(f"Failed to register service: {str(e)}")

    def discover_services(
        self,
        service_type: str,
        criteria: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Descubrir servicios disponibles

        Args:
            service_type (str): Tipo de servicio
            criteria (Dict[str, Any]): Criterios adicionales
            limit (int): Número máximo de servicios

        Returns:
            List[Dict[str, Any]]: Servicios disponibles
        """
        params = {
            'service_type': service_type,
            'limit': limit
        }
        if criteria:
            params.update(criteria)

        try:
            response = self.client._make_request('GET', '/api/discovery/services', params=params)
            return response.get('services', [])
        except Exception as e:
            raise P2PError(f"Failed to discover services: {str(e)}")

    def get_node_performance_metrics(
        self,
        node_id: str,
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Obtener métricas de rendimiento de un nodo

        Args:
            node_id (str): ID del nodo
            metric_types (List[str]): Tipos de métricas ('cpu', 'memory', 'network', 'storage')

        Returns:
            Dict[str, Any]: Métricas de rendimiento
        """
        params = {}
        if metric_types:
            params['metrics'] = ','.join(metric_types)

        try:
            return self.client._make_request('GET', f'/api/discovery/nodes/{node_id}/metrics', params=params)
        except Exception as e:
            raise P2PError(f"Failed to get node performance metrics: {str(e)}")

    def find_optimal_nodes(
        self,
        task_requirements: Dict[str, Any],
        optimization_criteria: List[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Encontrar nodos óptimos para una tarea específica

        Args:
            task_requirements (Dict[str, Any]): Requisitos de la tarea
            optimization_criteria (List[str]): Criterios de optimización
            limit (int): Número máximo de nodos

        Returns:
            List[Dict[str, Any]]: Nodos óptimos ordenados por puntuación
        """
        if optimization_criteria is None:
            optimization_criteria = ['latency', 'cost', 'reliability']

        data = {
            'task_requirements': task_requirements,
            'optimization_criteria': optimization_criteria,
            'limit': limit
        }

        try:
            response = self.client._make_request('POST', '/api/discovery/optimize', json=data)
            return response.get('optimal_nodes', [])
        except Exception as e:
            raise P2PError(f"Failed to find optimal nodes: {str(e)}")

    def get_geographic_distribution(self) -> Dict[str, Any]:
        """
        Obtener distribución geográfica de nodos

        Returns:
            Dict[str, Any]: Distribución por países y regiones
        """
        try:
            return self.client._make_request('GET', '/api/discovery/geographic')
        except Exception as e:
            raise P2PError(f"Failed to get geographic distribution: {str(e)}")

    def get_capability_distribution(self) -> Dict[str, Any]:
        """
        Obtener distribución de capacidades en la red

        Returns:
            Dict[str, Any]: Distribución por capacidades
        """
        try:
            return self.client._make_request('GET', '/api/discovery/capabilities')
        except Exception as e:
            raise P2PError(f"Failed to get capability distribution: {str(e)}")

    def discover_backup_nodes(
        self,
        primary_node_id: str,
        redundancy_level: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Descubrir nodos de respaldo para redundancia

        Args:
            primary_node_id (str): ID del nodo primario
            redundancy_level (int): Nivel de redundancia requerido

        Returns:
            List[Dict[str, Any]]: Nodos de respaldo
        """
        data = {
            'primary_node_id': primary_node_id,
            'redundancy_level': redundancy_level
        }

        try:
            response = self.client._make_request('POST', '/api/discovery/backup', json=data)
            return response.get('backup_nodes', [])
        except Exception as e:
            raise P2PError(f"Failed to discover backup nodes: {str(e)}")

    def get_network_health_score(self) -> Dict[str, Any]:
        """
        Obtener puntuación de salud de la red

        Returns:
            Dict[str, Any]: Puntuación y métricas de salud
        """
        try:
            return self.client._make_request('GET', '/api/discovery/health')
        except Exception as e:
            raise P2PError(f"Failed to get network health score: {str(e)}")

    def discover_by_energy_efficiency(
        self,
        min_efficiency_score: float = 0.7,
        energy_source: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Descubrir nodos por eficiencia energética

        Args:
            min_efficiency_score (float): Puntuación mínima de eficiencia
            energy_source (str): Fuente de energía preferida
            limit (int): Número máximo de nodos

        Returns:
            List[Dict[str, Any]]: Nodos energéticamente eficientes
        """
        criteria = {
            'min_efficiency_score': min_efficiency_score
        }
        if energy_source:
            criteria['energy_source'] = energy_source

        return self.discover_nodes(criteria, limit)

    def get_discovery_trends(self, timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Obtener tendencias de descubrimiento

        Args:
            timeframe_days (int): Período en días

        Returns:
            Dict[str, Any]: Tendencias de nodos y capacidades
        """
        params = {'timeframe_days': timeframe_days}

        try:
            return self.client._make_request('GET', '/api/discovery/trends', params=params)
        except Exception as e:
            raise P2PError(f"Failed to get discovery trends: {str(e)}")

    def validate_node_claims(self, node_id: str) -> Dict[str, Any]:
        """
        Validar claims de capacidades de un nodo

        Args:
            node_id (str): ID del nodo

        Returns:
            Dict[str, Any]: Resultado de validación
        """
        try:
            return self.client._make_request('POST', f'/api/discovery/validate/{node_id}')
        except Exception as e:
            raise P2PError(f"Failed to validate node claims: {str(e)}")