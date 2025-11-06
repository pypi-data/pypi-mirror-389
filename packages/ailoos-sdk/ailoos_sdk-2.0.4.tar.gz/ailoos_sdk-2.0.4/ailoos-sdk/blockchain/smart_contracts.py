"""
Ailoos Python SDK - Smart Contracts Module
Gestión de contratos inteligentes para Ailoos
"""

from typing import Dict, List, Optional, Any
from ..core.client import AiloosClient
from ..core.exceptions import BlockchainError, ValidationError


class SmartContractManager:
    """
    Gestor de contratos inteligentes para Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
        wallet_address (str): Dirección de la billetera
    """

    def __init__(self, client: AiloosClient, wallet_address: Optional[str] = None):
        self.client = client
        self.wallet_address = wallet_address

    def deploy_contract(
        self,
        contract_name: str,
        contract_type: str,
        parameters: Dict[str, Any],
        gas_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Desplegar un contrato inteligente

        Args:
            contract_name (str): Nombre del contrato
            contract_type (str): Tipo de contrato ('dracmas', 'dao', 'staking')
            parameters (Dict[str, Any]): Parámetros de inicialización
            gas_limit (int): Límite de gas opcional

        Returns:
            Dict[str, Any]: Información del contrato desplegado
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required for contract deployment")

        data = {
            'deployer_address': self.wallet_address,
            'contract_name': contract_name,
            'contract_type': contract_type,
            'parameters': parameters
        }

        if gas_limit:
            data['gas_limit'] = gas_limit

        try:
            return self.client._make_request('POST', '/api/contracts/deploy', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to deploy contract: {str(e)}")

    def get_contract_info(self, contract_address: str) -> Dict[str, Any]:
        """
        Obtener información de un contrato inteligente

        Args:
            contract_address (str): Dirección del contrato

        Returns:
            Dict[str, Any]: Información del contrato
        """
        try:
            return self.client._make_request('GET', f'/api/contracts/{contract_address}')
        except Exception as e:
            raise BlockchainError(f"Failed to get contract info: {str(e)}")

    def call_contract_function(
        self,
        contract_address: str,
        function_name: str,
        parameters: Dict[str, Any],
        value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Llamar a una función de contrato inteligente

        Args:
            contract_address (str): Dirección del contrato
            function_name (str): Nombre de la función
            parameters (Dict[str, Any]): Parámetros de la función
            value (float): Valor en DracmaS a enviar (opcional)

        Returns:
            Dict[str, Any]: Resultado de la llamada
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required for contract calls")

        data = {
            'caller_address': self.wallet_address,
            'contract_address': contract_address,
            'function_name': function_name,
            'parameters': parameters
        }

        if value is not None:
            data['value'] = value

        try:
            return self.client._make_request('POST', '/api/contracts/call', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to call contract function: {str(e)}")

    def get_contract_events(
        self,
        contract_address: str,
        event_name: Optional[str] = None,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener eventos de un contrato inteligente

        Args:
            contract_address (str): Dirección del contrato
            event_name (str): Nombre del evento (opcional)
            from_block (int): Bloque inicial (opcional)
            to_block (int): Bloque final (opcional)

        Returns:
            List[Dict[str, Any]]: Lista de eventos
        """
        params = {}
        if event_name:
            params['event_name'] = event_name
        if from_block is not None:
            params['from_block'] = from_block
        if to_block is not None:
            params['to_block'] = to_block

        try:
            response = self.client._make_request('GET', f'/api/contracts/{contract_address}/events', params=params)
            return response.get('events', [])
        except Exception as e:
            raise BlockchainError(f"Failed to get contract events: {str(e)}")

    def get_dracmas_contract(self) -> Dict[str, Any]:
        """
        Obtener información del contrato principal de DracmaS

        Returns:
            Dict[str, Any]: Información del contrato DracmaS
        """
        try:
            return self.client._make_request('GET', '/api/contracts/dracmas')
        except Exception as e:
            raise BlockchainError(f"Failed to get DracmaS contract: {str(e)}")

    def get_dao_contract(self) -> Dict[str, Any]:
        """
        Obtener información del contrato DAO

        Returns:
            Dict[str, Any]: Información del contrato DAO
        """
        try:
            return self.client._make_request('GET', '/api/contracts/dao')
        except Exception as e:
            raise BlockchainError(f"Failed to get DAO contract: {str(e)}")

    def mint_dracmas(
        self,
        amount: float,
        recipient_address: str,
        memo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Acuñar nuevos DracmaS (solo administradores)

        Args:
            amount (float): Cantidad a acuñar
            recipient_address (str): Dirección destinataria
            memo (str): Memo opcional

        Returns:
            Dict[str, Any]: Confirmación de acuñación
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required")

        data = {
            'minter_address': self.wallet_address,
            'amount': amount,
            'recipient_address': recipient_address
        }

        if memo:
            data['memo'] = memo

        try:
            return self.client._make_request('POST', '/api/contracts/dracmas/mint', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to mint DracmaS: {str(e)}")

    def burn_dracmas(self, amount: float, memo: Optional[str] = None) -> Dict[str, Any]:
        """
        Quemar DracmaS

        Args:
            amount (float): Cantidad a quemar
            memo (str): Memo opcional

        Returns:
            Dict[str, Any]: Confirmación de quema
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required")

        data = {
            'burner_address': self.wallet_address,
            'amount': amount
        }

        if memo:
            data['memo'] = memo

        try:
            return self.client._make_request('POST', '/api/contracts/dracmas/burn', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to burn DracmaS: {str(e)}")

    def pause_contract(self, contract_address: str) -> Dict[str, Any]:
        """
        Pausar un contrato inteligente (solo administradores)

        Args:
            contract_address (str): Dirección del contrato

        Returns:
            Dict[str, Any]: Confirmación de pausa
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required")

        data = {
            'pauser_address': self.wallet_address,
            'contract_address': contract_address
        }

        try:
            return self.client._make_request('POST', '/api/contracts/pause', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to pause contract: {str(e)}")

    def unpause_contract(self, contract_address: str) -> Dict[str, Any]:
        """
        Reanudar un contrato inteligente (solo administradores)

        Args:
            contract_address (str): Dirección del contrato

        Returns:
            Dict[str, Any]: Confirmación de reanudación
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required")

        data = {
            'pauser_address': self.wallet_address,
            'contract_address': contract_address
        }

        try:
            return self.client._make_request('POST', '/api/contracts/unpause', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to unpause contract: {str(e)}")

    def upgrade_contract(
        self,
        contract_address: str,
        new_implementation: str
    ) -> Dict[str, Any]:
        """
        Actualizar implementación de contrato (solo administradores)

        Args:
            contract_address (str): Dirección del contrato
            new_implementation (str): Nueva implementación

        Returns:
            Dict[str, Any]: Confirmación de actualización
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required")

        data = {
            'upgrader_address': self.wallet_address,
            'contract_address': contract_address,
            'new_implementation': new_implementation
        }

        try:
            return self.client._make_request('POST', '/api/contracts/upgrade', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to upgrade contract: {str(e)}")

    def get_contract_source(self, contract_address: str) -> Dict[str, Any]:
        """
        Obtener código fuente de un contrato

        Args:
            contract_address (str): Dirección del contrato

        Returns:
            Dict[str, Any]: Código fuente del contrato
        """
        try:
            return self.client._make_request('GET', f'/api/contracts/{contract_address}/source')
        except Exception as e:
            raise BlockchainError(f"Failed to get contract source: {str(e)}")

    def verify_contract(
        self,
        contract_address: str,
        source_code: str,
        compiler_version: str
    ) -> Dict[str, Any]:
        """
        Verificar contrato en blockchain explorer

        Args:
            contract_address (str): Dirección del contrato
            source_code (str): Código fuente
            compiler_version (str): Versión del compilador

        Returns:
            Dict[str, Any]: Resultado de verificación
        """
        data = {
            'contract_address': contract_address,
            'source_code': source_code,
            'compiler_version': compiler_version
        }

        try:
            return self.client._make_request('POST', '/api/contracts/verify', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to verify contract: {str(e)}")

    def get_contract_balance(self, contract_address: str) -> Dict[str, Any]:
        """
        Obtener balance de un contrato

        Args:
            contract_address (str): Dirección del contrato

        Returns:
            Dict[str, Any]: Balance del contrato
        """
        try:
            return self.client._make_request('GET', f'/api/contracts/{contract_address}/balance')
        except Exception as e:
            raise BlockchainError(f"Failed to get contract balance: {str(e)}")

    def estimate_contract_call_gas(
        self,
        contract_address: str,
        function_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Estimar gas para llamada a contrato

        Args:
            contract_address (str): Dirección del contrato
            function_name (str): Nombre de la función
            parameters (Dict[str, Any]): Parámetros

        Returns:
            Dict[str, Any]: Estimación de gas
        """
        data = {
            'contract_address': contract_address,
            'function_name': function_name,
            'parameters': parameters
        }

        try:
            return self.client._make_request('POST', '/api/contracts/estimate-gas', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to estimate gas: {str(e)}")

    def get_contract_templates(self) -> List[Dict[str, Any]]:
        """
        Obtener plantillas de contratos disponibles

        Returns:
            List[Dict[str, Any]]: Lista de plantillas
        """
        try:
            response = self.client._make_request('GET', '/api/contracts/templates')
            return response.get('templates', [])
        except Exception as e:
            raise BlockchainError(f"Failed to get contract templates: {str(e)}")

    def set_wallet_address(self, address: str) -> None:
        """
        Establecer dirección de billetera

        Args:
            address (str): Nueva dirección de billetera
        """
        self.wallet_address = address