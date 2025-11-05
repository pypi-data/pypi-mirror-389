"""Type definitions for MMN SDK using Pydantic for validation."""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


# --- JSON-RPC Types ---


class JsonRpcRequest(BaseModel):
    """JSON-RPC request model."""

    jsonrpc: str = "2.0"
    method: str
    params: Optional[Any] = None
    id: int


class JsonRpcError(BaseModel):
    """JSON-RPC error model."""

    code: int
    message: str
    data: Optional[Any] = None


class JsonRpcResponse(BaseModel):
    """JSON-RPC response model."""

    jsonrpc: str
    id: int
    result: Optional[Any] = None
    error: Optional[JsonRpcError] = None


# --- Transaction Types ---


class EphemeralKeyPair(BaseModel):
    """Ephemeral key pair for temporary authentication."""

    private_key: str
    public_key: str


class TransferType(str, Enum):
    """Types of transfers supported."""

    GIVE_COFFEE = "give_coffee"
    TRANSFER_TOKEN = "transfer_token"
    UNLOCK_ITEM = "unlock_item"


class ExtraInfo(BaseModel):
    """Extra information for transactions."""

    model_config = ConfigDict(extra="allow")

    type: str
    ItemId: Optional[str] = None
    ItemType: Optional[str] = None
    ClanId: Optional[str] = None
    UserSenderId: str = ""
    UserSenderUsername: str = ""
    UserReceiverId: Optional[str] = None
    ChannelId: Optional[str] = None
    MessageRefId: Optional[str] = None
    ExtraAttribute: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary, excluding None values."""
        return {k: str(v) for k, v in self.model_dump().items() if v is not None}


class TxMsg(BaseModel):
    """Transaction message."""

    type: int
    sender: str
    recipient: str
    amount: str
    timestamp: int
    text_data: str
    nonce: int
    extra_info: str
    zk_proof: str
    zk_pub: str


class SignedTx(BaseModel):
    """Signed transaction."""

    tx_msg: TxMsg
    signature: str


class SendTransactionRequest(BaseModel):
    """Request to send a transaction."""

    sender: str
    recipient: str
    amount: str
    nonce: int
    public_key: str
    private_key: str
    zk_proof: str
    zk_pub: str
    timestamp: Optional[int] = None
    text_data: Optional[str] = ""
    extra_info: Optional[ExtraInfo] = None


class AddTxResponse(BaseModel):
    """Response from adding a transaction."""

    ok: bool
    tx_hash: str
    error: str = ""


class GetCurrentNonceResponse(BaseModel):
    """Response for getting current nonce."""

    address: str
    nonce: int
    tag: str
    error: str = ""


class GetAccountByAddressResponse(BaseModel):
    """Response for getting account by address."""

    address: str
    balance: str
    nonce: int
    decimals: int


# --- Client Configuration ---


class MmnClientConfig(BaseModel):
    """Configuration for MMN client."""

    base_url: str
    timeout: int = 30000
    headers: Optional[Dict[str, str]] = None


# --- Indexer Types ---


class Transaction(BaseModel):
    """Blockchain transaction details."""

    chain_id: str
    hash: str
    nonce: int
    block_hash: str
    block_number: int
    from_address: str
    to_address: str
    value: str
    transaction_type: int
    transaction_timestamp: int
    text_data: str
    extra_info: str
    block_timestamp: Optional[int] = None
    transaction_index: Optional[int] = None
    gas: Optional[int] = None
    gas_price: Optional[str] = None
    data: Optional[str] = None
    function_selector: Optional[str] = None
    max_fee_per_gas: Optional[str] = None
    max_priority_fee_per_gas: Optional[str] = None
    r: Optional[str] = None
    s: Optional[str] = None
    v: Optional[str] = None
    max_fee_per_blob_gas: Optional[str] = None
    blob_versioned_hashes: Optional[List[str]] = None
    access_list_json: Optional[str] = None
    authorization_list_json: Optional[str] = None
    contract_address: Optional[str] = None
    gas_used: Optional[int] = None
    cumulative_gas_used: Optional[int] = None
    effective_gas_price: Optional[str] = None
    blob_gas_used: Optional[int] = None
    blob_gas_price: Optional[str] = None
    logs_bloom: Optional[str] = None
    status: Optional[int] = None


class Meta(BaseModel):
    """Metadata for paginated responses."""

    chain_id: int
    page: int
    address: Optional[str] = None
    signature: Optional[str] = None
    limit: Optional[int] = None
    total_items: Optional[int] = None
    total_pages: Optional[int] = None


class WalletDetail(BaseModel):
    """Wallet details."""

    address: str
    balance: str
    account_nonce: int
    last_balance_update: int


class WalletDetailResponse(BaseModel):
    """Response containing wallet details."""

    data: WalletDetail


class ListTransactionResponse(BaseModel):
    """Response containing list of transactions."""

    meta: Meta
    data: Optional[List[Transaction]] = None


class TransactionDetailResponse(BaseModel):
    """Response containing transaction details."""

    data: Dict[str, Transaction]


class IndexerClientConfig(BaseModel):
    """Configuration for Indexer client."""

    endpoint: str
    chain_id: str
    timeout: int = 30000
    headers: Optional[Dict[str, str]] = None


# --- ZK Client Types ---


class ZkClientConfig(BaseModel):
    """Configuration for ZK client."""

    endpoint: str
    timeout: int = 30000
    headers: Optional[Dict[str, str]] = None


class ZkClientType(str, Enum):
    """Types of ZK clients."""

    MEZON = "mezon"
    OAUTH = "oauth"


class GetZkProofRequest(BaseModel):
    """Request to get ZK proof."""

    user_id: str
    ephemeral_public_key: str
    jwt: str
    address: str
    client_type: ZkClientType = ZkClientType.MEZON


class ZkProof(BaseModel):
    """ZK proof response."""

    proof: str
    public_input: str


class ZkProofResponse(BaseModel):
    """Response containing ZK proof."""

    data: ZkProof
