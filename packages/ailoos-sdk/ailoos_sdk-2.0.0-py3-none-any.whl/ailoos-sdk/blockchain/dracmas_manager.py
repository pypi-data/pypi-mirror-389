"""
Ailoos Python SDK - DracmaS Manager Module
Gestión del token DracmaS y billetera
"""

from typing import Dict, List, Optional, Any
from ..core.client import AiloosClient
from ..core.exceptions import BlockchainError, ValidationError


class DracmaSManager:
    """
    Gestor del token DracmaS para Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
        wallet_address (str): Dirección de la billetera (opcional)
    """

    def __init__(self, client: AiloosClient, wallet_address: Optional[str] = None):
        self.client = client
        self.wallet_address = wallet_address

    def get_balance(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener balance de DracmaS

        Args:
            address (str): Dirección de la billetera (usa la configurada si no se especifica)

        Returns:
            Dict[str, Any]: Balance y metadatos
        """
        target_address = address or self.wallet_address
        if not target_address:
            raise ValidationError("Wallet address is required")

        try:
            return self.client._make_request('GET', f'/api/blockchain/balance/{target_address}')
        except Exception as e:
            raise BlockchainError(f"Failed to get balance: {str(e)}")

    def get_token_info(self) -> Dict[str, Any]:
        """
        Obtener información del token DracmaS

        Returns:
            Dict[str, Any]: Información completa del token
        """
        try:
            return self.client._make_request('GET', '/api/blockchain/token/info')
        except Exception as e:
            raise BlockchainError(f"Failed to get token info: {str(e)}")

    def transfer_tokens(
        self,
        to_address: str,
        amount: float,
        memo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transferir DracmaS a otra dirección

        Args:
            to_address (str): Dirección destinataria
            amount (float): Cantidad a transferir
            memo (str): Memo opcional para la transacción

        Returns:
            Dict[str, Any]: Confirmación de la transacción
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required for transfers")

        if amount <= 0:
            raise ValidationError("Amount must be positive")

        data = {
            'from_address': self.wallet_address,
            'to_address': to_address,
            'amount': amount
        }

        if memo:
            data['memo'] = memo

        try:
            return self.client._make_request('POST', '/api/blockchain/transfer', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to transfer tokens: {str(e)}")

    def get_transaction_history(
        self,
        address: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Obtener historial de transacciones

        Args:
            address (str): Dirección de la billetera
            limit (int): Número máximo de transacciones
            offset (int): Offset para paginación

        Returns:
            Dict[str, Any]: Historial de transacciones
        """
        target_address = address or self.wallet_address
        if not target_address:
            raise ValidationError("Wallet address is required")

        params = {'limit': limit, 'offset': offset}

        try:
            return self.client._make_request('GET', f'/api/blockchain/transactions/{target_address}', params=params)
        except Exception as e:
            raise BlockchainError(f"Failed to get transaction history: {str(e)}")

    def stake_tokens(self, amount: float, duration_days: int = 30) -> Dict[str, Any]:
        """
        Hacer stake de DracmaS para gobernanza

        Args:
            amount (float): Cantidad a stakear
            duration_days (int): Duración del stake en días

        Returns:
            Dict[str, Any]: Confirmación del stake
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required for staking")

        if amount <= 0:
            raise ValidationError("Amount must be positive")

        data = {
            'address': self.wallet_address,
            'amount': amount,
            'duration_days': duration_days
        }

        try:
            return self.client._make_request('POST', '/api/blockchain/stake', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to stake tokens: {str(e)}")

    def unstake_tokens(self, stake_id: str) -> Dict[str, Any]:
        """
        Retirar stake de DracmaS

        Args:
            stake_id (str): ID del stake a retirar

        Returns:
            Dict[str, Any]: Confirmación del unstake
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required for unstaking")

        data = {
            'address': self.wallet_address,
            'stake_id': stake_id
        }

        try:
            return self.client._make_request('POST', '/api/blockchain/unstake', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to unstake tokens: {str(e)}")

    def get_staking_info(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener información de staking

        Args:
            address (str): Dirección de la billetera

        Returns:
            Dict[str, Any]: Información de staking
        """
        target_address = address or self.wallet_address
        if not target_address:
            raise ValidationError("Wallet address is required")

        try:
            return self.client._make_request('GET', f'/api/blockchain/staking/{target_address}')
        except Exception as e:
            raise BlockchainError(f"Failed to get staking info: {str(e)}")

    def get_rewards_info(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener información de recompensas

        Args:
            address (str): Dirección de la billetera

        Returns:
            Dict[str, Any]: Información de recompensas
        """
        target_address = address or self.wallet_address
        if not target_address:
            raise ValidationError("Wallet address is required")

        try:
            return self.client._make_request('GET', f'/api/blockchain/rewards/{target_address}')
        except Exception as e:
            raise BlockchainError(f"Failed to get rewards info: {str(e)}")

    def claim_rewards(self) -> Dict[str, Any]:
        """
        Reclamar recompensas acumuladas

        Returns:
            Dict[str, Any]: Confirmación de reclamación
        """
        if not self.wallet_address:
            raise ValidationError("Wallet address is required for claiming rewards")

        data = {'address': self.wallet_address}

        try:
            return self.client._make_request('POST', '/api/blockchain/claim-rewards', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to claim rewards: {str(e)}")

    def get_market_data(self) -> Dict[str, Any]:
        """
        Obtener datos de mercado de DracmaS

        Returns:
            Dict[str, Any]: Datos de mercado
        """
        try:
            return self.client._make_request('GET', '/api/blockchain/market')
        except Exception as e:
            raise BlockchainError(f"Failed to get market data: {str(e)}")

    def estimate_transaction_fee(self, amount: float, to_address: str) -> Dict[str, Any]:
        """
        Estimar tarifa de transacción

        Args:
            amount (float): Cantidad a transferir
            to_address (str): Dirección destinataria

        Returns:
            Dict[str, Any]: Estimación de tarifa
        """
        data = {
            'amount': amount,
            'to_address': to_address
        }

        try:
            return self.client._make_request('POST', '/api/blockchain/estimate-fee', json=data)
        except Exception as e:
            raise BlockchainError(f"Failed to estimate transaction fee: {str(e)}")

    def get_network_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de la red blockchain

        Returns:
            Dict[str, Any]: Estadísticas de la red
        """
        try:
            return self.client._make_request('GET', '/api/blockchain/network/stats')
        except Exception as e:
            raise BlockchainError(f"Failed to get network stats: {str(e)}")

    def validate_address(self, address: str) -> bool:
        """
        Validar formato de dirección

        Args:
            address (str): Dirección a validar

        Returns:
            bool: True si la dirección es válida
        """
        try:
            response = self.client._make_request('POST', '/api/blockchain/validate-address',
                                               json={'address': address})
            return response.get('valid', False)
        except Exception:
            return False

    def get_gas_price(self) -> Dict[str, Any]:
        """
        Obtener precio actual del gas

        Returns:
            Dict[str, Any]: Información del precio del gas
        """
        try:
            return self.client._make_request('GET', '/api/blockchain/gas-price')
        except Exception as e:
            raise BlockchainError(f"Failed to get gas price: {str(e)}")

    def set_wallet_address(self, address: str) -> None:
        """
        Establecer dirección de billetera

        Args:
            address (str): Nueva dirección de billetera
        """
        if not self.validate_address(address):
            raise ValidationError("Invalid wallet address format")
        self.wallet_address = address