"""
Ailoos Python SDK - Audit Trail Module
Sistema de auditoría y trazabilidad blockchain
"""

from typing import Dict, List, Optional, Any
from ..core.client import AiloosClient
from ..core.exceptions import BlockchainError, ValidationError


class AuditTrail:
    """
    Sistema de auditoría y trazabilidad para Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
    """

    def __init__(self, client: AiloosClient):
        self.client = client

    def get_transaction_audit(self, tx_hash: str) -> Dict[str, Any]:
        """
        Obtener auditoría completa de una transacción

        Args:
            tx_hash (str): Hash de la transacción

        Returns:
            Dict[str, Any]: Auditoría de la transacción
        """
        try:
            return self.client._make_request('GET', f'/api/audit/transactions/{tx_hash}')
        except Exception as e:
            raise BlockchainError(f"Failed to get transaction audit: {str(e)}")

    def get_model_training_audit(self, model_name: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener auditoría de entrenamiento de modelo

        Args:
            model_name (str): Nombre del modelo
            session_id (str): ID de sesión de entrenamiento (opcional)

        Returns:
            Dict[str, Any]: Auditoría del entrenamiento
        """
        params = {}
        if session_id:
            params['session_id'] = session_id

        try:
            return self.client._make_request('GET', f'/api/audit/models/{model_name}/training', params=params)
        except Exception as e:
            raise BlockchainError(f"Failed to get model training audit: {str(e)}")

    def get_node_activity_audit(
        self,
        node_id: str,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener auditoría de actividad de nodo

        Args:
            node_id (str): ID del nodo
            from_timestamp (str): Timestamp inicial (ISO 8601)
            to_timestamp (str): Timestamp final (ISO 8601)

        Returns:
            List[Dict[str, Any]]: Lista de actividades auditadas
        """
        params = {}
        if from_timestamp:
            params['from_timestamp'] = from_timestamp
        if to_timestamp:
            params['to_timestamp'] = to_timestamp

        try:
            response = self.client._make_request('GET', f'/api/audit/nodes/{node_id}/activity', params=params)
            return response.get('activities', [])
        except Exception as e:
            raise BlockchainError(f"Failed to get node activity audit: {str(e)}")

    def get_dao_proposal_audit(self, proposal_id: str) -> Dict[str, Any]:
        """
        Obtener auditoría completa de propuesta DAO

        Args:
            proposal_id (str): ID de la propuesta

        Returns:
            Dict[str, Any]: Auditoría de la propuesta
        """
        try:
            return self.client._make_request('GET', f'/api/audit/dao/proposals/{proposal_id}')
        except Exception as e:
            raise BlockchainError(f"Failed to get DAO proposal audit: {str(e)}")

    def get_computation_verification(self, computation_id: str) -> Dict[str, Any]:
        """
        Obtener verificación de computación con ZK-proofs

        Args:
            computation_id (str): ID de la computación

        Returns:
            Dict[str, Any]: Verificación con prueba cero-conocimiento
        """
        try:
            return self.client._make_request('GET', f'/api/audit/computation/{computation_id}/verification')
        except Exception as e:
            raise BlockchainError(f"Failed to get computation verification: {str(e)}")

    def get_data_lineage_audit(self, data_hash: str) -> Dict[str, Any]:
        """
        Obtener auditoría de linaje de datos

        Args:
            data_hash (str): Hash de los datos

        Returns:
            Dict[str, Any]: Linaje completo de los datos
        """
        try:
            return self.client._make_request('GET', f'/api/audit/data/{data_hash}/lineage')
        except Exception as e:
            raise BlockchainError(f"Failed to get data lineage audit: {str(e)}")

    def get_security_incident_audit(
        self,
        incident_id: Optional[str] = None,
        severity: Optional[str] = None,
        from_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener auditoría de incidentes de seguridad

        Args:
            incident_id (str): ID específico del incidente
            severity (str): Severidad ('low', 'medium', 'high', 'critical')
            from_timestamp (str): Timestamp inicial

        Returns:
            List[Dict[str, Any]]: Lista de incidentes auditados
        """
        params = {}
        if severity:
            params['severity'] = severity
        if from_timestamp:
            params['from_timestamp'] = from_timestamp

        endpoint = '/api/audit/security/incidents'
        if incident_id:
            endpoint = f'/api/audit/security/incidents/{incident_id}'

        try:
            response = self.client._make_request('GET', endpoint, params=params)
            if incident_id:
                return [response]
            return response.get('incidents', [])
        except Exception as e:
            raise BlockchainError(f"Failed to get security incident audit: {str(e)}")

    def get_model_bias_audit(self, model_name: str, evaluation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener auditoría de sesgos de modelo

        Args:
            model_name (str): Nombre del modelo
            evaluation_id (str): ID de evaluación específica

        Returns:
            Dict[str, Any]: Auditoría de sesgos
        """
        params = {}
        if evaluation_id:
            params['evaluation_id'] = evaluation_id

        try:
            return self.client._make_request('GET', f'/api/audit/models/{model_name}/bias', params=params)
        except Exception as e:
            raise BlockchainError(f"Failed to get model bias audit: {str(e)}")

    def get_energy_consumption_audit(
        self,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        node_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtener auditoría de consumo energético

        Args:
            from_timestamp (str): Timestamp inicial
            to_timestamp (str): Timestamp final
            node_id (str): ID de nodo específico

        Returns:
            Dict[str, Any]: Auditoría de consumo energético
        """
        params = {}
        if from_timestamp:
            params['from_timestamp'] = from_timestamp
        if to_timestamp:
            params['to_timestamp'] = to_timestamp
        if node_id:
            params['node_id'] = node_id

        try:
            return self.client._make_request('GET', '/api/audit/energy/consumption', params=params)
        except Exception as e:
            raise BlockchainError(f"Failed to get energy consumption audit: {str(e)}")

    def get_audit_trail_summary(
        self,
        entity_type: str,
        entity_id: str,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtener resumen de trail de auditoría

        Args:
            entity_type (str): Tipo de entidad ('transaction', 'model', 'node', 'proposal')
            entity_id (str): ID de la entidad
            from_timestamp (str): Timestamp inicial
            to_timestamp (str): Timestamp final

        Returns:
            Dict[str, Any]: Resumen del trail de auditoría
        """
        params = {}
        if from_timestamp:
            params['from_timestamp'] = from_timestamp
        if to_timestamp:
            params['to_timestamp'] = to_timestamp

        try:
            return self.client._make_request('GET',
                                           f'/api/audit/{entity_type}/{entity_id}/summary',
                                           params=params)
        except Exception as e:
            raise BlockchainError(f"Failed to get audit trail summary: {str(e)}")

    def verify_zk_proof(self, proof_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verificar prueba cero-conocimiento

        Args:
            proof_data (Dict[str, Any]): Datos de la prueba ZK

        Returns:
            Dict[str, Any]: Resultado de verificación
        """
        try:
            return self.client._make_request('POST', '/api/audit/zk/verify', json=proof_data)
        except Exception as e:
            raise BlockchainError(f"Failed to verify ZK proof: {str(e)}")

    def get_compliance_report(
        self,
        report_type: str,
        jurisdiction: str = "global",
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtener reporte de compliance

        Args:
            report_type (str): Tipo de reporte ('gdpr', 'ccpa', 'data_privacy')
            jurisdiction (str): Jurisdicción
            from_timestamp (str): Timestamp inicial
            to_timestamp (str): Timestamp final

        Returns:
            Dict[str, Any]: Reporte de compliance
        """
        params = {
            'jurisdiction': jurisdiction
        }
        if from_timestamp:
            params['from_timestamp'] = from_timestamp
        if to_timestamp:
            params['to_timestamp'] = to_timestamp

        try:
            return self.client._make_request('GET', f'/api/audit/compliance/{report_type}', params=params)
        except Exception as e:
            raise BlockchainError(f"Failed to get compliance report: {str(e)}")

    def get_audit_logs(
        self,
        log_type: str = "all",
        severity: Optional[str] = None,
        from_timestamp: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener logs de auditoría

        Args:
            log_type (str): Tipo de log ('security', 'transaction', 'model', 'all')
            severity (str): Severidad ('info', 'warning', 'error', 'critical')
            from_timestamp (str): Timestamp inicial
            limit (int): Número máximo de logs

        Returns:
            List[Dict[str, Any]]: Lista de logs de auditoría
        """
        params = {
            'limit': limit
        }
        if severity:
            params['severity'] = severity
        if from_timestamp:
            params['from_timestamp'] = from_timestamp

        try:
            response = self.client._make_request('GET', f'/api/audit/logs/{log_type}', params=params)
            return response.get('logs', [])
        except Exception as e:
            raise BlockchainError(f"Failed to get audit logs: {str(e)}")

    def export_audit_trail(
        self,
        entity_type: str,
        entity_id: str,
        format: str = "json",
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exportar trail de auditoría

        Args:
            entity_type (str): Tipo de entidad
            entity_id (str): ID de la entidad
            format (str): Formato de exportación ('json', 'csv', 'pdf')
            from_timestamp (str): Timestamp inicial
            to_timestamp (str): Timestamp final

        Returns:
            Dict[str, Any]: URL de descarga del export
        """
        params = {
            'format': format
        }
        if from_timestamp:
            params['from_timestamp'] = from_timestamp
        if to_timestamp:
            params['to_timestamp'] = to_timestamp

        try:
            return self.client._make_request('GET',
                                           f'/api/audit/{entity_type}/{entity_id}/export',
                                           params=params)
        except Exception as e:
            raise BlockchainError(f"Failed to export audit trail: {str(e)}")

    def get_audit_statistics(
        self,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas de auditoría

        Args:
            from_timestamp (str): Timestamp inicial
            to_timestamp (str): Timestamp final

        Returns:
            Dict[str, Any]: Estadísticas de auditoría
        """
        params = {}
        if from_timestamp:
            params['from_timestamp'] = from_timestamp
        if to_timestamp:
            params['to_timestamp'] = to_timestamp

        try:
            return self.client._make_request('GET', '/api/audit/statistics', params=params)
        except Exception as e:
            raise BlockchainError(f"Failed to get audit statistics: {str(e)}")

    def validate_audit_integrity(self, audit_hash: str) -> Dict[str, Any]:
        """
        Validar integridad de auditoría

        Args:
            audit_hash (str): Hash de la auditoría

        Returns:
            Dict[str, Any]: Resultado de validación
        """
        try:
            return self.client._make_request('POST', '/api/audit/validate-integrity',
                                           json={'audit_hash': audit_hash})
        except Exception as e:
            raise BlockchainError(f"Failed to validate audit integrity: {str(e)}")