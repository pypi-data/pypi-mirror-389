"""
MMN SDK for Python
==================

Python SDK for interacting with the MMN blockchain.

Provides three main clients:
- IndexerClient: Query blockchain data (transactions, wallets)
- ZkClient: Generate zero-knowledge proofs
- MmnClient: Send transactions and manage accounts

Example:
    >>> from mmn_sdk import IndexerClient, ZkClient, MmnClient
    >>> from mmn_sdk import IndexerClientConfig, ZkClientConfig, MmnClientConfig
    >>>
    >>> # Create clients
    >>> indexer = IndexerClient(IndexerClientConfig(
    ...     endpoint="https://indexer.example.com",
    ...     chain_id="1"
    ... ))
    >>>
    >>> zk_client = ZkClient(ZkClientConfig(
    ...     endpoint="https://zk.example.com"
    ... ))
    >>>
    >>> mmn_client = MmnClient(MmnClientConfig(
    ...     base_url="https://rpc.example.com"
    ... ))
"""

__version__ = "0.1.0"

# Import clients
from .indexer_client import IndexerClient, FilterParams
from .zk_client import ZkClient
from .mmn_client import MmnClient

# Import types and configurations
from .types import (
    # Client configs
    IndexerClientConfig,
    ZkClientConfig,
    MmnClientConfig,
    # Transaction types
    EphemeralKeyPair,
    TransferType,
    ExtraInfo,
    TxMsg,
    SignedTx,
    SendTransactionRequest,
    AddTxResponse,
    GetCurrentNonceResponse,
    GetAccountByAddressResponse,
    # Indexer types
    Transaction,
    Meta,
    WalletDetail,
    WalletDetailResponse,
    ListTransactionResponse,
    TransactionDetailResponse,
    # ZK types
    ZkClientType,
    GetZkProofRequest,
    ZkProof,
    ZkProofResponse,
    # JSON-RPC types
    JsonRpcRequest,
    JsonRpcResponse,
    JsonRpcError,
)

__all__ = [
    # Version
    "__version__",
    # Clients
    "IndexerClient",
    "ZkClient",
    "MmnClient",
    # Constants
    "FilterParams",
    # Configurations
    "IndexerClientConfig",
    "ZkClientConfig",
    "MmnClientConfig",
    # Transaction types
    "EphemeralKeyPair",
    "TransferType",
    "ExtraInfo",
    "TxMsg",
    "SignedTx",
    "SendTransactionRequest",
    "AddTxResponse",
    "GetCurrentNonceResponse",
    "GetAccountByAddressResponse",
    # Indexer types
    "Transaction",
    "Meta",
    "WalletDetail",
    "WalletDetailResponse",
    "ListTransactionResponse",
    "TransactionDetailResponse",
    # ZK types
    "ZkClientType",
    "GetZkProofRequest",
    "ZkProof",
    "ZkProofResponse",
    # JSON-RPC types
    "JsonRpcRequest",
    "JsonRpcResponse",
    "JsonRpcError",
]
