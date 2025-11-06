"""
Ailoos Python SDK - Model Manager Module
Gestión de modelos de IA en Ailoos
"""

from typing import Dict, List, Optional, Any
from ..core.client import AiloosClient
from ..core.exceptions import ModelError, ValidationError


class ModelManager:
    """
    Gestor de modelos para Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
    """

    def __init__(self, client: AiloosClient):
        self.client = client

    def list_models(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listar modelos disponibles

        Args:
            category (str): Categoría de modelos ('text', 'vision', 'multimodal', 'audio')

        Returns:
            List[Dict[str, Any]]: Lista de modelos
        """
        try:
            params = {}
            if category:
                params['category'] = category

            response = self.client._make_request('GET', '/api/models', params=params)
            return response.get('models', [])
        except Exception as e:
            raise ModelError(f"Failed to list models: {str(e)}")

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Obtener información detallada de un modelo

        Args:
            model_name (str): Nombre del modelo

        Returns:
            Dict[str, Any]: Información del modelo
        """
        try:
            return self.client._make_request('GET', f'/api/models/{model_name}')
        except Exception as e:
            raise ModelError(f"Failed to get model info: {str(e)}")

    def deploy_model(self, model_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Desplegar un modelo

        Args:
            model_name (str): Nombre del modelo
            config (Dict[str, Any]): Configuración de despliegue

        Returns:
            Dict[str, Any]: Información del despliegue
        """
        try:
            data = {
                'model_name': model_name,
                'config': config
            }
            return self.client._make_request('POST', '/api/models/deploy', json=data)
        except Exception as e:
            raise ModelError(f"Failed to deploy model: {str(e)}")

    def undeploy_model(self, deployment_id: str) -> Dict[str, Any]:
        """
        Desplegar un modelo

        Args:
            deployment_id (str): ID del despliegue

        Returns:
            Dict[str, Any]: Confirmación de undeploy
        """
        try:
            return self.client._make_request('DELETE', f'/api/models/deployments/{deployment_id}')
        except Exception as e:
            raise ModelError(f"Failed to undeploy model: {str(e)}")

    def update_model(self, model_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar configuración de modelo

        Args:
            model_name (str): Nombre del modelo
            updates (Dict[str, Any]): Actualizaciones a aplicar

        Returns:
            Dict[str, Any]: Modelo actualizado
        """
        try:
            return self.client._make_request('PUT', f'/api/models/{model_name}', json=updates)
        except Exception as e:
            raise ModelError(f"Failed to update model: {str(e)}")

    def get_model_metrics(self, model_name: str, period: str = "24h") -> Dict[str, Any]:
        """
        Obtener métricas de rendimiento de un modelo

        Args:
            model_name (str): Nombre del modelo
            period (str): Período de métricas ('1h', '24h', '7d', '30d')

        Returns:
            Dict[str, Any]: Métricas del modelo
        """
        try:
            params = {'period': period}
            return self.client._make_request('GET', f'/api/models/{model_name}/metrics', params=params)
        except Exception as e:
            raise ModelError(f"Failed to get model metrics: {str(e)}")

    def fine_tune_model(
        self,
        base_model: str,
        dataset: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fine-tunear un modelo

        Args:
            base_model (str): Modelo base
            dataset (str): Dataset para fine-tuning
            config (Dict[str, Any]): Configuración de fine-tuning

        Returns:
            Dict[str, Any]: Trabajo de fine-tuning iniciado
        """
        try:
            data = {
                'base_model': base_model,
                'dataset': dataset,
                'config': config
            }
            return self.client._make_request('POST', '/api/models/fine-tune', json=data)
        except Exception as e:
            raise ModelError(f"Failed to start fine-tuning: {str(e)}")

    def create_custom_model(
        self,
        name: str,
        architecture: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crear un modelo personalizado

        Args:
            name (str): Nombre del modelo
            architecture (str): Arquitectura base
            config (Dict[str, Any]): Configuración del modelo

        Returns:
            Dict[str, Any]: Modelo creado
        """
        try:
            data = {
                'name': name,
                'architecture': architecture,
                'config': config
            }
            return self.client._make_request('POST', '/api/models/custom', json=data)
        except Exception as e:
            raise ModelError(f"Failed to create custom model: {str(e)}")

    def clone_model(self, source_model: str, new_name: str) -> Dict[str, Any]:
        """
        Clonar un modelo existente

        Args:
            source_model (str): Modelo a clonar
            new_name (str): Nombre del nuevo modelo

        Returns:
            Dict[str, Any]: Modelo clonado
        """
        try:
            data = {'new_name': new_name}
            return self.client._make_request('POST', f'/api/models/{source_model}/clone', json=data)
        except Exception as e:
            raise ModelError(f"Failed to clone model: {str(e)}")

    def export_model(self, model_name: str, format: str = "pytorch") -> Dict[str, Any]:
        """
        Exportar modelo en diferentes formatos

        Args:
            model_name (str): Nombre del modelo
            format (str): Formato de exportación ('pytorch', 'onnx', 'tensorflow')

        Returns:
            Dict[str, Any]: URL de descarga del modelo exportado
        """
        try:
            params = {'format': format}
            return self.client._make_request('GET', f'/api/models/{model_name}/export', params=params)
        except Exception as e:
            raise ModelError(f"Failed to export model: {str(e)}")

    def import_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Importar modelo desde datos externos

        Args:
            model_data (Dict[str, Any]): Datos del modelo a importar

        Returns:
            Dict[str, Any]: Modelo importado
        """
        try:
            return self.client._make_request('POST', '/api/models/import', json=model_data)
        except Exception as e:
            raise ModelError(f"Failed to import model: {str(e)}")

    def get_model_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Obtener versiones disponibles de un modelo

        Args:
            model_name (str): Nombre del modelo

        Returns:
            List[Dict[str, Any]]: Lista de versiones
        """
        try:
            response = self.client._make_request('GET', f'/api/models/{model_name}/versions')
            return response.get('versions', [])
        except Exception as e:
            raise ModelError(f"Failed to get model versions: {str(e)}")

    def rollback_model(self, model_name: str, version: str) -> Dict[str, Any]:
        """
        Hacer rollback a una versión anterior del modelo

        Args:
            model_name (str): Nombre del modelo
            version (str): Versión a la que hacer rollback

        Returns:
            Dict[str, Any]: Modelo revertido
        """
        try:
            data = {'version': version}
            return self.client._make_request('POST', f'/api/models/{model_name}/rollback', json=data)
        except Exception as e:
            raise ModelError(f"Failed to rollback model: {str(e)}")

    def monitor_model_health(self, model_name: str) -> Dict[str, Any]:
        """
        Monitorear salud de un modelo

        Args:
            model_name (str): Nombre del modelo

        Returns:
            Dict[str, Any]: Estado de salud del modelo
        """
        try:
            return self.client._make_request('GET', f'/api/models/{model_name}/health')
        except Exception as e:
            raise ModelError(f"Failed to get model health: {str(e)}")

    def optimize_model(self, model_name: str, target: str = "latency") -> Dict[str, Any]:
        """
        Optimizar modelo para un objetivo específico

        Args:
            model_name (str): Nombre del modelo
            target (str): Objetivo de optimización ('latency', 'throughput', 'memory')

        Returns:
            Dict[str, Any]: Modelo optimizado
        """
        try:
            data = {'target': target}
            return self.client._make_request('POST', f'/api/models/{model_name}/optimize', json=data)
        except Exception as e:
            raise ModelError(f"Failed to optimize model: {str(e)}")

    def get_model_logs(self, model_name: str, lines: int = 100) -> List[str]:
        """
        Obtener logs de un modelo

        Args:
            model_name (str): Nombre del modelo
            lines (int): Número de líneas de log

        Returns:
            List[str]: Logs del modelo
        """
        try:
            params = {'lines': lines}
            response = self.client._make_request('GET', f'/api/models/{model_name}/logs', params=params)
            return response.get('logs', [])
        except Exception as e:
            raise ModelError(f"Failed to get model logs: {str(e)}")

    def delete_model(self, model_name: str, force: bool = False) -> Dict[str, Any]:
        """
        Eliminar un modelo

        Args:
            model_name (str): Nombre del modelo
            force (bool): Forzar eliminación sin confirmación

        Returns:
            Dict[str, Any]: Confirmación de eliminación
        """
        try:
            params = {'force': force}
            return self.client._make_request('DELETE', f'/api/models/{model_name}', params=params)
        except Exception as e:
            raise ModelError(f"Failed to delete model: {str(e)}")