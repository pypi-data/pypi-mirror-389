"""
Ailoos Python SDK - DAO Voting Module
Sistema de votación DAO para gobernanza de Ailoos
"""

from typing import Dict, List, Optional, Any
from ..core.client import AiloosClient
from ..core.exceptions import BlockchainError, ValidationError


class DAOVoting:
    """
    Sistema de votación DAO para Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
        wallet_address (str): Dirección de la billetera para votar
    """

    def __init__(self, client: AiloosClient, wallet_address: Optional[str] = None):
        self.client = client
        self.wallet_address = wallet_address

    def get_active_proposals(self) -> List[Dict[str, Any]]:
        """
        Obtener propuestas activas para votación

        Returns:
            List[Dict[str, Any]]: Lista de propuestas activas
        """
        try:
            response = self.client._make_request('GET', '/api/dao/proposals/active')
            return response.get('proposals', [])
        except Exception as e:
            raise BlockchainError(f"Failed to get active proposals: {str(e)}")

    def get_proposal_details(self, proposal_id: str) -> Dict[str, Any]:
        """
        Obtener detalles completos de una propuesta

        Args:
            proposal_id (str): ID de la propuesta

        Returns:
            Dict[str, Any]: Detalles de la propuesta
        """
        try:
            return self.client._make_request('GET', f'/api/dao/proposals/{proposal_id}')
        except Exception as e:
            raise BlockchainError(f"Failed to get proposal details: {str(e)}")

    def create_proposal(
        self,
        title: str,
        description: str,
        proposal_type: str,
        parameters: Dict[str, Any],
        voting_duration_days: int = 7
    ) -> Dict[str, Any]:
        """
        Crear una nueva propuesta

        Args:
            title (str): Título de la propuesta
            description (str): Descripción detallada
            proposal_type (str): Tipo de propuesta ('model_update', 'parameter_change', 'feature_add')
            parameters (Dict[str, Any]): Parámetros específicos de la propuesta
            voting_duration_days (int): Duración de la votación en días

        Returns:
            Dict[str, Any]: Propuesta creada
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required to create proposals")

        data = {
            'creator_address': self.wallet_address,
            'title': title,
            'description': description,
            'type': proposal_type,
            'parameters': parameters,
            'voting_duration_days': voting_duration_days
        }

        try:
            return self.client._make_request('POST', '/api/dao/proposals', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to create proposal: {str(e)}")

    def vote_on_proposal(
        self,
        proposal_id: str,
        vote: str,
        voting_power: int
    ) -> Dict[str, Any]:
        """
        Votar en una propuesta

        Args:
            proposal_id (str): ID de la propuesta
            vote (str): Voto ('for', 'against', 'abstain')
            voting_power (int): Poder de voto (DracmaS stakeados)

        Returns:
            Dict[str, Any]: Confirmación del voto
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required to vote")

        valid_votes = ['for', 'against', 'abstain']
        if vote not in valid_votes:
            raise ValidationError(f"Vote must be one of: {', '.join(valid_votes)}")

        if voting_power <= 0:
            raise ValidationError("Voting power must be positive")

        data = {
            'voter_address': self.wallet_address,
            'proposal_id': proposal_id,
            'vote': vote,
            'voting_power': voting_power
        }

        try:
            return self.client._make_request('POST', '/api/dao/vote', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to vote on proposal: {str(e)}")

    def get_voting_history(
        self,
        address: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtener historial de votaciones

        Args:
            address (str): Dirección de la billetera
            limit (int): Número máximo de votos a retornar

        Returns:
            List[Dict[str, Any]]: Historial de votaciones
        """
        target_address = address or self.wallet_address
        if not target_address:
            raise ValidationError("Wallet address is required")

        params = {'limit': limit}

        try:
            response = self.client._make_request('GET', f'/api/dao/votes/{target_address}', params=params)
            return response.get('votes', [])
        except Exception as e:
            raise BlockchainError(f"Failed to get voting history: {str(e)}")

    def get_voting_power(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener poder de voto actual

        Args:
            address (str): Dirección de la billetera

        Returns:
            Dict[str, Any]: Poder de voto disponible
        """
        target_address = address or self.wallet_address
        if not target_address:
            raise ValidationError("Wallet address is required")

        try:
            return self.client._make_request('GET', f'/api/dao/voting-power/{target_address}')
        except Exception as e:
            raise BlockchainError(f"Failed to get voting power: {str(e)}")

    def get_proposal_results(self, proposal_id: str) -> Dict[str, Any]:
        """
        Obtener resultados de una propuesta

        Args:
            proposal_id (str): ID de la propuesta

        Returns:
            Dict[str, Any]: Resultados de la votación
        """
        try:
            return self.client._make_request('GET', f'/api/dao/proposals/{proposal_id}/results')
        except Exception as e:
            raise BlockchainError(f"Failed to get proposal results: {str(e)}")

    def delegate_voting_power(
        self,
        delegate_address: str,
        voting_power: int,
        duration_days: int = 30
    ) -> Dict[str, Any]:
        """
        Delegar poder de voto a otra dirección

        Args:
            delegate_address (str): Dirección a la que delegar
            voting_power (int): Poder de voto a delegar
            duration_days (int): Duración de la delegación

        Returns:
            Dict[str, Any]: Confirmación de delegación
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required for delegation")

        data = {
            'delegator_address': self.wallet_address,
            'delegate_address': delegate_address,
            'voting_power': voting_power,
            'duration_days': duration_days
        }

        try:
            return self.client._make_request('POST', '/api/dao/delegate', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to delegate voting power: {str(e)}")

    def revoke_delegation(self, delegation_id: str) -> Dict[str, Any]:
        """
        Revocar delegación de poder de voto

        Args:
            delegation_id (str): ID de la delegación a revocar

        Returns:
            Dict[str, Any]: Confirmación de revocación
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required")

        data = {
            'delegator_address': self.wallet_address,
            'delegation_id': delegation_id
        }

        try:
            return self.client._make_request('POST', '/api/dao/revoke-delegation', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to revoke delegation: {str(e)}")

    def get_delegations(self, address: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtener delegaciones activas

        Args:
            address (str): Dirección de la billetera

        Returns:
            List[Dict[str, Any]]: Lista de delegaciones
        """
        target_address = address or self.wallet_address
        if not target_address:
            raise ValidationError("Wallet address is required")

        try:
            response = self.client._make_request('GET', f'/api/dao/delegations/{target_address}')
            return response.get('delegations', [])
        except Exception as e:
            raise BlockchainError(f"Failed to get delegations: {str(e)}")

    def get_dao_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas generales del DAO

        Returns:
            Dict[str, Any]: Estadísticas del DAO
        """
        try:
            return self.client._make_request('GET', '/api/dao/stats')
        except Exception as e:
            raise BlockchainError(f"Failed to get DAO stats: {str(e)}")

    def get_quorum_requirement(self, proposal_type: str) -> Dict[str, Any]:
        """
        Obtener requisitos de quorum para un tipo de propuesta

        Args:
            proposal_type (str): Tipo de propuesta

        Returns:
            Dict[str, Any]: Requisitos de quorum
        """
        try:
            return self.client._make_request('GET', f'/api/dao/quorum/{proposal_type}')
        except Exception as e:
            raise BlockchainError(f"Failed to get quorum requirements: {str(e)}")

    def get_execution_status(self, proposal_id: str) -> Dict[str, Any]:
        """
        Obtener estado de ejecución de una propuesta aprobada

        Args:
            proposal_id (str): ID de la propuesta

        Returns:
            Dict[str, Any]: Estado de ejecución
        """
        try:
            return self.client._make_request('GET', f'/api/dao/proposals/{proposal_id}/execution')
        except Exception as e:
            raise BlockchainError(f"Failed to get execution status: {str(e)}")

    def execute_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """
        Ejecutar una propuesta aprobada (solo administradores)

        Args:
            proposal_id (str): ID de la propuesta a ejecutar

        Returns:
            Dict[str, Any]: Resultado de la ejecución
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required")

        data = {
            'executor_address': self.wallet_address,
            'proposal_id': proposal_id
        }

        try:
            return self.client._make_request('POST', '/api/dao/execute', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to execute proposal: {str(e)}")

    def get_proposal_templates(self) -> List[Dict[str, Any]]:
        """
        Obtener plantillas de propuestas disponibles

        Returns:
            List[Dict[str, Any]]: Lista de plantillas
        """
        try:
            response = self.client._make_request('GET', '/api/dao/templates')
            return response.get('templates', [])
        except Exception as e:
            raise BlockchainError(f"Failed to get proposal templates: {str(e)}")

    def validate_proposal_parameters(
        self,
        proposal_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validar parámetros de una propuesta antes de crearla

        Args:
            proposal_type (str): Tipo de propuesta
            parameters (Dict[str, Any]): Parámetros a validar

        Returns:
            Dict[str, Any]: Resultado de validación
        """
        data = {
            'type': proposal_type,
            'parameters': parameters
        }

        try:
            return self.client._make_request('POST', '/api/dao/validate', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to validate proposal parameters: {str(e)}")

    def set_wallet_address(self, address: str) -> None:
        """
        Establecer dirección de billetera

        Args:
            address (str): Nueva dirección de billetera
        """
        self.wallet_address = address