"""ZK Client for generating zero-knowledge proofs."""

import aiohttp
from typing import Literal, Optional
from .types import (
    ZkClientConfig,
    ZkProof,
    ZkProofResponse,
    ZkClientType,
)


class ZkClient:
    """
    Client for interacting with the Zero-Knowledge Proof service.

    The ZK Client generates cryptographic proofs for authenticating
    users without revealing sensitive information.
    """

    def __init__(self, config: ZkClientConfig):
        """
        Initialize the ZK client.

        Args:
            config: Configuration for the ZK client
        """
        self.endpoint = config.endpoint.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(
            total=config.timeout / 1000.0
        )  # Convert ms to seconds

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **(config.headers or {}),
        }

    async def _make_request(
        self,
        method: Literal["GET", "POST"],
        path: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """
        Make HTTP request with automatic error handling.

        Args:
            method: HTTP method (GET or POST)
            path: API endpoint path
            params: URL query parameters
            json_data: Request body for POST requests

        Returns:
            Response data as dictionary

        Raises:
            Exception: If request fails
        """
        url = f"{self.endpoint}/{path}"

        async with aiohttp.ClientSession(
            timeout=self.timeout, headers=self.headers
        ) as session:
            try:
                if method == "GET":
                    async with session.get(url, params=params) as response:
                        response.raise_for_status()
                        return await response.json()
                else:
                    async with session.post(
                        url, params=params, json=json_data
                    ) as response:
                        response.raise_for_status()
                        return await response.json()

            except aiohttp.ServerTimeoutError:
                raise TimeoutError(f"Request timeout after {self.timeout.total}s")
            except aiohttp.ClientResponseError as e:
                raise Exception(f"HTTP {e.status}: {e.message}") from e
            except aiohttp.ClientError as e:
                raise Exception(f"Request failed: {str(e)}") from e

    async def get_zk_proofs(
        self,
        user_id: str,
        ephemeral_public_key: str,
        jwt: str,
        address: str,
        client_type: ZkClientType = ZkClientType.MEZON,
    ) -> ZkProof:
        """
        Generate a zero-knowledge proof for user authentication.

        Args:
            user_id: User identifier
            ephemeral_public_key: Ephemeral public key for temporary auth
            jwt: JSON Web Token for authentication
            address: Wallet address
            client_type: Type of client (MEZON or OAUTH)

        Returns:
            ZK proof containing proof and public input

        Example:
            >>> client = ZkClient(config)
            >>> proof = await client.get_zk_proofs(
            ...     user_id="user123",
            ...     ephemeral_public_key="pub_key",
            ...     jwt="jwt_token",
            ...     address="wallet_address",
            ...     client_type=ZkClientType.MEZON
            ... )
            >>> print(proof.proof)
        """
        path = "prove"

        # Prepare request body
        request_body = {
            "user_id": user_id,
            "ephemeral_pk": ephemeral_public_key,
            "jwt": jwt,
            "address": address,
            "client_type": client_type.value,
        }

        response_data = await self._make_request("POST", path, json_data=request_body)
        response = ZkProofResponse(**response_data)
        return response.data
