"""
Ailoos Python SDK - IPFS Storage Module
Almacenamiento distribuido con IPFS
"""

from typing import Dict, List, Optional, Any
from ..core.client import AiloosClient
from ..core.exceptions import P2PError, ValidationError


class IPFSStorage:
    """
    Cliente de almacenamiento IPFS para Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
    """

    def __init__(self, client: AiloosClient):
        self.client = client

    def upload_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Subir archivo a IPFS

        Args:
            file_path (str): Ruta del archivo local
            metadata (Dict[str, Any]): Metadatos adicionales

        Returns:
            Dict[str, Any]: Información de la subida (hash, URL, etc.)
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("File path must be a non-empty string")

        import os
        if not os.path.exists(file_path):
            raise ValidationError(f"File does not exist: {file_path}")

        data = {
            'file_path': file_path,
            'metadata': metadata or {}
        }

        try:
            return self.client._make_request('POST', '/api/ipfs/upload', json=data)
        except Exception as e:
            raise P2PError(f"Failed to upload file to IPFS: {str(e)}")

    def download_file(self, ipfs_hash: str, output_path: str) -> Dict[str, Any]:
        """
        Descargar archivo desde IPFS

        Args:
            ipfs_hash (str): Hash IPFS del archivo
            output_path (str): Ruta de salida local

        Returns:
            Dict[str, Any]: Información de la descarga
        """
        if not ipfs_hash or not isinstance(ipfs_hash, str):
            raise ValidationError("IPFS hash must be a non-empty string")

        if not output_path or not isinstance(output_path, str):
            raise ValidationError("Output path must be a non-empty string")

        data = {
            'ipfs_hash': ipfs_hash,
            'output_path': output_path
        }

        try:
            return self.client._make_request('POST', '/api/ipfs/download', json=data)
        except Exception as e:
            raise P2PError(f"Failed to download file from IPFS: {str(e)}")

    def upload_data(
        self,
        data: Any,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Subir datos serializados a IPFS

        Args:
            data (Any): Datos a subir
            filename (str): Nombre del archivo
            metadata (Dict[str, Any]): Metadatos adicionales

        Returns:
            Dict[str, Any]: Información de la subida
        """
        import tempfile
        import pickle
        import os

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=f"_{filename}") as f:
            pickle.dump(data, f)
            temp_path = f.name

        try:
            result = self.upload_file(temp_path, metadata)
            return result
        finally:
            os.unlink(temp_path)

    def download_data(self, ipfs_hash: str) -> Any:
        """
        Descargar y deserializar datos desde IPFS

        Args:
            ipfs_hash (str): Hash IPFS de los datos

        Returns:
            Any: Datos deserializados
        """
        import tempfile
        import pickle
        import os

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            self.download_file(ipfs_hash, temp_path)
            with open(temp_path, 'rb') as f:
                data = pickle.load(f)
            return data
        finally:
            os.unlink(temp_path)

    def get_file_info(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Obtener información de un archivo en IPFS

        Args:
            ipfs_hash (str): Hash IPFS del archivo

        Returns:
            Dict[str, Any]: Información del archivo
        """
        try:
            return self.client._make_request('GET', f'/api/ipfs/files/{ipfs_hash}')
        except Exception as e:
            raise P2PError(f"Failed to get file info: {str(e)}")

    def pin_file(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Fijar archivo en IPFS para asegurar disponibilidad

        Args:
            ipfs_hash (str): Hash IPFS del archivo

        Returns:
            Dict[str, Any]: Confirmación de fijado
        """
        data = {'ipfs_hash': ipfs_hash}

        try:
            return self.client._make_request('POST', '/api/ipfs/pin', json=data)
        except Exception as e:
            raise P2PError(f"Failed to pin file: {str(e)}")

    def unpin_file(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Desfijar archivo en IPFS

        Args:
            ipfs_hash (str): Hash IPFS del archivo

        Returns:
            Dict[str, Any]: Confirmación de desfijado
        """
        try:
            return self.client._make_request('DELETE', f'/api/ipfs/pin/{ipfs_hash}')
        except Exception as e:
            raise P2PError(f"Failed to unpin file: {str(e)}")

    def get_pinned_files(self) -> List[Dict[str, Any]]:
        """
        Obtener lista de archivos fijados

        Returns:
            List[Dict[str, Any]]: Lista de archivos fijados
        """
        try:
            response = self.client._make_request('GET', '/api/ipfs/pinned')
            return response.get('files', [])
        except Exception as e:
            raise P2PError(f"Failed to get pinned files: {str(e)}")

    def create_directory(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crear directorio en IPFS con múltiples archivos

        Args:
            files (List[Dict[str, Any]]): Lista de archivos con 'path' y 'content'

        Returns:
            Dict[str, Any]: Hash del directorio creado
        """
        data = {'files': files}

        try:
            return self.client._make_request('POST', '/api/ipfs/directory', json=data)
        except Exception as e:
            raise P2PError(f"Failed to create directory: {str(e)}")

    def get_directory_contents(self, ipfs_hash: str) -> List[Dict[str, Any]]:
        """
        Obtener contenido de un directorio en IPFS

        Args:
            ipfs_hash (str): Hash IPFS del directorio

        Returns:
            List[Dict[str, Any]]: Contenido del directorio
        """
        try:
            response = self.client._make_request('GET', f'/api/ipfs/directory/{ipfs_hash}')
            return response.get('contents', [])
        except Exception as e:
            raise P2PError(f"Failed to get directory contents: {str(e)}")

    def upload_model_checkpoint(
        self,
        model_name: str,
        checkpoint_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Subir checkpoint de modelo a IPFS

        Args:
            model_name (str): Nombre del modelo
            checkpoint_path (str): Ruta del checkpoint
            metadata (Dict[str, Any]): Metadatos del checkpoint

        Returns:
            Dict[str, Any]: Información de la subida
        """
        checkpoint_metadata = {
            'type': 'model_checkpoint',
            'model_name': model_name,
            'timestamp': None,  # Se establece en el servidor
            **(metadata or {})
        }

        return self.upload_file(checkpoint_path, checkpoint_metadata)

    def download_model_checkpoint(
        self,
        ipfs_hash: str,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Descargar checkpoint de modelo desde IPFS

        Args:
            ipfs_hash (str): Hash IPFS del checkpoint
            output_path (str): Ruta de salida

        Returns:
            Dict[str, Any]: Información de la descarga
        """
        return self.download_file(ipfs_hash, output_path)

    def upload_dataset_shard(
        self,
        dataset_name: str,
        shard_path: str,
        shard_index: int,
        total_shards: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Subir shard de dataset a IPFS

        Args:
            dataset_name (str): Nombre del dataset
            shard_path (str): Ruta del shard
            shard_index (int): Índice del shard
            total_shards (int): Total de shards
            metadata (Dict[str, Any]): Metadatos adicionales

        Returns:
            Dict[str, Any]: Información de la subida
        """
        shard_metadata = {
            'type': 'dataset_shard',
            'dataset_name': dataset_name,
            'shard_index': shard_index,
            'total_shards': total_shards,
            **(metadata or {})
        }

        return self.upload_file(shard_path, shard_metadata)

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de almacenamiento IPFS

        Returns:
            Dict[str, Any]: Estadísticas de almacenamiento
        """
        try:
            return self.client._make_request('GET', '/api/ipfs/stats')
        except Exception as e:
            raise P2PError(f"Failed to get storage stats: {str(e)}")

    def search_files(
        self,
        query: str,
        file_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Buscar archivos en IPFS

        Args:
            query (str): Término de búsqueda
            file_type (str): Tipo de archivo ('model', 'dataset', 'other')
            limit (int): Número máximo de resultados

        Returns:
            List[Dict[str, Any]]: Resultados de búsqueda
        """
        params = {
            'query': query,
            'limit': limit
        }
        if file_type:
            params['type'] = file_type

        try:
            response = self.client._make_request('GET', '/api/ipfs/search', params=params)
            return response.get('results', [])
        except Exception as e:
            raise P2PError(f"Failed to search files: {str(e)}")

    def replicate_file(
        self,
        ipfs_hash: str,
        target_nodes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Replicar archivo en múltiples nodos

        Args:
            ipfs_hash (str): Hash IPFS del archivo
            target_nodes (List[str]): Nodos destino (None = auto)

        Returns:
            Dict[str, Any]: Estado de replicación
        """
        data = {
            'ipfs_hash': ipfs_hash,
            'target_nodes': target_nodes
        }

        try:
            return self.client._make_request('POST', '/api/ipfs/replicate', json=data)
        except Exception as e:
            raise P2PError(f"Failed to replicate file: {str(e)}")

    def get_file_providers(self, ipfs_hash: str) -> List[Dict[str, Any]]:
        """
        Obtener nodos que proveen un archivo

        Args:
            ipfs_hash (str): Hash IPFS del archivo

        Returns:
            List[Dict[str, Any]]: Lista de proveedores
        """
        try:
            response = self.client._make_request('GET', f'/api/ipfs/providers/{ipfs_hash}')
            return response.get('providers', [])
        except Exception as e:
            raise P2PError(f"Failed to get file providers: {str(e)}")

    def validate_file_integrity(self, ipfs_hash: str, expected_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Validar integridad de archivo en IPFS

        Args:
            ipfs_hash (str): Hash IPFS del archivo
            expected_size (int): Tamaño esperado en bytes

        Returns:
            Dict[str, Any]: Resultado de validación
        """
        params = {}
        if expected_size:
            params['expected_size'] = expected_size

        try:
            return self.client._make_request('GET', f'/api/ipfs/validate/{ipfs_hash}', params=params)
        except Exception as e:
            raise P2PError(f"Failed to validate file integrity: {str(e)}")

    def get_network_info(self) -> Dict[str, Any]:
        """
        Obtener información de la red IPFS

        Returns:
            Dict[str, Any]: Información de la red
        """
        try:
            return self.client._make_request('GET', '/api/ipfs/network')
        except Exception as e:
            raise P2PError(f"Failed to get network info: {str(e)}")

    def garbage_collect(self) -> Dict[str, Any]:
        """
        Ejecutar recolección de basura en IPFS

        Returns:
            Dict[str, Any]: Resultado de la recolección
        """
        try:
            return self.client._make_request('POST', '/api/ipfs/gc')
        except Exception as e:
            raise P2PError(f"Failed to run garbage collection: {str(e)}")