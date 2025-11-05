"""Indexer Client for querying MMN blockchain data."""

import aiohttp
from typing import Literal, Optional
from .types import (
    IndexerClientConfig,
    Transaction,
    TransactionDetailResponse,
    ListTransactionResponse,
    WalletDetail,
    WalletDetailResponse,
)


class FilterParams:
    """Filter parameters for transaction queries."""

    ALL = 0
    SENT = 2
    RECEIVED = 1


class IndexerClient:
    """
    Client for interacting with the MMN Indexer API.

    The Indexer provides read-only access to blockchain data including
    transactions, wallet details, and transaction history.
    """

    def __init__(self, config: IndexerClientConfig):
        """
        Initialize the Indexer client.

        Args:
            config: Configuration for the indexer client
        """
        self.endpoint = config.endpoint.rstrip("/")
        self.chain_id = config.chain_id
        self.timeout = aiohttp.ClientTimeout(
            total=config.timeout / 1000.0
        )  # Convert ms to seconds

        self.headers = {"Accept": "application/json", **(config.headers or {})}

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

    async def get_transaction_by_hash(self, hash: str) -> Transaction:
        """
        Get transaction details by transaction hash.

        Args:
            hash: Transaction hash

        Returns:
            Transaction details

        Example:
            >>> client = IndexerClient(config)
            >>> tx = await client.get_transaction_by_hash("0x123...")
            >>> print(tx.from_address)
        """
        path = f"{self.chain_id}/tx/{hash}/detail"
        response_data = await self._make_request("GET", path)
        response = TransactionDetailResponse(**response_data)
        return response.data["transaction"]

    async def get_transaction_by_wallet(
        self,
        wallet: str,
        page: int = 1,
        limit: int = 50,
        filter_type: int = FilterParams.ALL,
        sort_by: str = "transaction_timestamp",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> ListTransactionResponse:
        """
        Get transactions for a specific wallet address.

        Args:
            wallet: Wallet address
            page: Page number (1-indexed)
            limit: Number of transactions per page (max 1000)
            filter_type: Filter transactions (ALL=0, SENT=2, RECEIVED=1)
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)

        Returns:
            List of transactions with metadata

        Raises:
            ValueError: If wallet address is empty

        Example:
            >>> client = IndexerClient(config)
            >>> result = await client.get_transaction_by_wallet(
            ...     "wallet_address",
            ...     page=1,
            ...     limit=10,
            ...     filter_type=FilterParams.SENT
            ... )
            >>> print(f"Total: {result.meta.total_items}")
            >>> for tx in result.data:
            ...     print(tx.hash)
        """
        if not wallet:
            raise ValueError("wallet address cannot be empty")

        if page < 1:
            page = 1
        if limit <= 0:
            limit = 50
        if limit > 1000:
            limit = 1000

        params = {
            "page": page - 1,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        if filter_type == FilterParams.ALL:
            params["wallet_address"] = wallet
        elif filter_type == FilterParams.SENT:
            params["filter_from_address"] = wallet
        elif filter_type == FilterParams.RECEIVED:
            params["filter_to_address"] = wallet

        path = f"{self.chain_id}/transactions"
        response_data = await self._make_request("GET", path, params=params)
        return ListTransactionResponse(**response_data)

    async def get_wallet_detail(self, wallet: str) -> WalletDetail:
        """
        Get wallet details including balance and nonce.

        Args:
            wallet: Wallet address

        Returns:
            Wallet details

        Raises:
            ValueError: If wallet address is empty

        Example:
            >>> client = IndexerClient(config)
            >>> wallet = await client.get_wallet_detail("wallet_address")
            >>> print(f"Balance: {wallet.balance}")
            >>> print(f"Nonce: {wallet.account_nonce}")
        """
        if not wallet:
            raise ValueError("wallet address cannot be empty")

        path = f"{self.chain_id}/wallets/{wallet}/detail"
        response_data = await self._make_request("GET", path)
        response = WalletDetailResponse(**response_data)
        return response.data
