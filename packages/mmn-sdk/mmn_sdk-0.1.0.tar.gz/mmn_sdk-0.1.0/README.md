# MMN SDK for Python

Python SDK for interacting with the MMN blockchain. This SDK provides three main clients for comprehensive blockchain interaction:

- **IndexerClient**: Query blockchain data (transactions, wallets)
- **ZkClient**: Generate zero-knowledge proofs for authentication
- **MmnClient**: Send transactions and manage accounts

## Features

- Async/await support with `aiohttp`
- Type-safe models using Pydantic
- Ed25519 cryptographic signing
- Zero-knowledge proof generation
- Comprehensive transaction management
- Wallet and transaction querying

## Installation

```bash
# Install from source
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Requirements

- Python 3.8+
- aiohttp >= 3.8.0
- pynacl >= 1.5.0
- base58 >= 2.1.1
- pycryptodome >= 3.18.0
- pydantic >= 2.0.0

## Quick Start

### Complete Example - Sending Tokens

This example demonstrates the complete workflow of sending tokens using all three clients:

```python
import asyncio
from mmn import (
    IndexerClient,
    IndexerClientConfig,
    MmnClient,
    ZkClient,
    MmnClientConfig,
    ZkClientConfig,
    SendTransactionRequest,
    ExtraInfo,
    TransferType,
    ZkClientType,
)

async def main():
    # Initialize clients
    mmn_client = MmnClient(MmnClientConfig(
        base_url="https://dong.mezon.ai/mmn-api/",
        timeout=30000,
    ))

    indexer_client = IndexerClient(IndexerClientConfig(
        endpoint="https://dong.mezon.ai/indexer-api/",
        chain_id="1337",
    ))

    zk_client = ZkClient(ZkClientConfig(
        endpoint="https://dong.mezon.ai/zk-api/",
        timeout=30000,
    ))

    sender_id = "1982293985808355328"
    receiver_id = "1831510214096982016"

    # Generate ephemeral key pair
    keypair = mmn_client.generate_ephemeral_key_pair()

    # Get sender address
    sender_address = mmn_client.get_address_from_user_id(sender_id)

    # Get ZK proofs
    zk_proofs = await zk_client.get_zk_proofs(
        user_id=sender_id,
        ephemeral_public_key=keypair.public_key,
        jwt="your_jwt_token",
        address=sender_address,
        client_type=ZkClientType.MEZON,
    )

    # Get current nonce
    nonce_response = await mmn_client.get_current_nonce(sender_id, "pending")

    # Prepare transaction
    extra_info = ExtraInfo(
        type=TransferType.TRANSFER_TOKEN.value,
        UserSenderId=sender_id,
        UserSenderUsername="Python SDK User",
        UserReceiverId=receiver_id,
    )

    tx_request = SendTransactionRequest(
        sender=sender_id,
        recipient=receiver_id,
        amount=mmn_client.scale_amount_to_decimals(1),  # 1 token
        nonce=nonce_response.nonce + 1,
        text_data="Sending 1 token",
        extra_info=extra_info,
        public_key=keypair.public_key,
        private_key=keypair.private_key,
        zk_proof=zk_proofs.proof,
        zk_pub=zk_proofs.public_input,
    )

    # Send transaction
    result = await mmn_client.send_transaction(tx_request)

    if result.ok:
        print(f"Transaction hash: {result.tx_hash}")

        # Query transaction by hash
        tx_detail = await indexer_client.get_transaction_by_hash(result.tx_hash)
        print(f"Transaction details: {tx_detail}")
    else:
        print(f"Transaction failed: {result.error}")

asyncio.run(main())
```

### IndexerClient

Query blockchain data like transactions and wallet information:

```python
import asyncio
from mmn import IndexerClient, IndexerClientConfig, FilterParams

async def main():
    indexer_client = IndexerClient(IndexerClientConfig(
        endpoint="https://dong.mezon.ai/indexer-api/",
        chain_id="1337",
    ))

    # Get transaction by hash
    tx = await indexer_client.get_transaction_by_hash("tx_hash_here")
    print(f"Transaction: {tx}")

    # Get wallet details
    wallet = await indexer_client.get_wallet_detail("wallet_address")
    print(f"Balance: {wallet.balance}")

    # Get transactions by wallet
    result = await indexer_client.get_transaction_by_wallet(
        wallet="wallet_address",
        page=1,
        limit=10,
        filter_type=FilterParams.ALL,
    )
    print(f"Total transactions: {result.meta.total_items}")

asyncio.run(main())
```

### ZkClient

Generate zero-knowledge proofs for secure authentication:

```python
import asyncio
from mmn import ZkClient, ZkClientConfig, ZkClientType

async def main():
    zk_client = ZkClient(ZkClientConfig(
        endpoint="https://dong.mezon.ai/zk-api/",
        timeout=30000,
    ))

    proof = await zk_client.get_zk_proofs(
        user_id="user123",
        ephemeral_public_key="ephemeral_pub_key",
        jwt="jwt_token",
        address="wallet_address",
        client_type=ZkClientType.MEZON,
    )
    print(f"Proof: {proof.proof}")
    print(f"Public input: {proof.public_input}")

asyncio.run(main())
```

### MmnClient

Send transactions and manage blockchain accounts:

```python
import asyncio
from mmn import (
    MmnClient,
    MmnClientConfig,
    SendTransactionRequest,
    ExtraInfo,
    TransferType,
)

async def main():
    mmn_client = MmnClient(MmnClientConfig(
        base_url="https://dong.mezon.ai/mmn-api/",
        timeout=30000,
    ))

    # Generate ephemeral key pair
    keypair = mmn_client.generate_ephemeral_key_pair()

    # Get address from user ID
    address = mmn_client.get_address_from_user_id("user123")

    # Get current nonce
    nonce_resp = await mmn_client.get_current_nonce("user123", "pending")

    # Scale amount to decimals (1 token = 1000000 with 6 decimals)
    amount = mmn_client.scale_amount_to_decimals(1)

    # Send transaction
    extra_info = ExtraInfo(
        type=TransferType.TRANSFER_TOKEN.value,
        UserSenderId="sender_id",
        UserSenderUsername="sender",
        UserReceiverId="receiver_id",
    )

    tx_request = SendTransactionRequest(
        sender="sender_user_id",
        recipient="recipient_user_id",
        amount=amount,
        nonce=nonce_resp.nonce + 1,
        text_data="Payment note",
        public_key=keypair.public_key,
        private_key=keypair.private_key,
        zk_proof="zk_proof",
        zk_pub="zk_public_input",
        extra_info=extra_info,
    )

    response = await mmn_client.send_transaction(tx_request)
    if response.ok:
        print(f"Transaction hash: {response.tx_hash}")
    else:
        print(f"Error: {response.error}")

asyncio.run(main())
```

## Complete Workflow Example

The complete workflow for sending a token transaction involves:

1. **Initialize clients**: Create MmnClient, IndexerClient, and ZkClient
2. **Generate ephemeral key pair**: Temporary keys for transaction signing
3. **Convert user ID to address**: Derive blockchain address from user ID
4. **Get ZK proofs**: Generate zero-knowledge proof for authentication
5. **Get current nonce**: Retrieve the account's transaction nonce
6. **Prepare transaction**: Create transaction with all required fields
7. **Send transaction**: Submit to the blockchain
8. **Query transaction**: Verify transaction status with IndexerClient

See the complete example above or [main.py](main.py) for a full implementation.

## API Reference

### IndexerClient

#### Methods

- `get_transaction_by_hash(hash: str) -> Transaction`
  - Get transaction details by hash

- `get_transaction_by_wallet(wallet: str, page: int = 1, limit: int = 50, filter_type: int = 0, sort_by: str = "transaction_timestamp", sort_order: str = "desc") -> ListTransactionResponse`
  - Get transactions for a wallet with filtering and pagination

- `get_wallet_detail(wallet: str) -> WalletDetail`
  - Get wallet balance and nonce

#### Filter Types

- `FilterParams.ALL` (0): All transactions
- `FilterParams.SENT` (2): Sent transactions only
- `FilterParams.RECEIVED` (1): Received transactions only

### ZkClient

#### Methods

- `get_zk_proofs(user_id: str, ephemeral_public_key: str, jwt: str, address: str, client_type: ZkClientType = ZkClientType.MEZON) -> ZkProof`
  - Generate zero-knowledge proof

#### Client Types

- `ZkClientType.MEZON`: Mezon authentication
- `ZkClientType.OAUTH`: OAuth authentication

### MmnClient

#### Methods

- `generate_ephemeral_key_pair() -> EphemeralKeyPair`
  - Generate temporary Ed25519 key pair

- `get_address_from_user_id(user_id: str) -> str`
  - Convert user ID to blockchain address using SHA-256

- `send_transaction(params: SendTransactionRequest) -> AddTxResponse`
  - Send transaction using user IDs (auto-converts to addresses)

- `send_transaction_by_address(params: SendTransactionRequest) -> AddTxResponse`
  - Send transaction using addresses directly

- `get_current_nonce(user_id: str, tag: str = "latest") -> GetCurrentNonceResponse`
  - Get current nonce for an account

- `get_account_by_user_id(user_id: str) -> GetAccountByAddressResponse`
  - Get account information by user ID

- `scale_amount_to_decimals(original_amount: int, decimals: int = 6) -> str`
  - Scale amount to blockchain decimals (default 6)

- `validate_address(address: str) -> bool`
  - Validate blockchain address format

- `validate_amount(balance: str, amount: str) -> bool`
  - Check if amount doesn't exceed balance

## Examples

See [main.py](main.py) for a complete working example that demonstrates:

- Initializing all three clients (MmnClient, ZkClient, IndexerClient)
- Generating ephemeral key pairs
- Getting ZK proofs for authentication
- Sending token transactions
- Querying transactions by hash and wallet

Run the example:

```bash
python main.py
```

## Development

### Setup

```bash
# Clone repository
git clone <repository-url>
cd mmn-sdk-python

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Format code
ruff format .

# Check for linting issues
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

### Type Checking

```bash
mypy mmn/
```

## Release Process

This project uses [Python Semantic Release](https://python-semantic-release.readthedocs.io/) for automated versioning and releases.

### Commit Message Convention

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New feature (minor version bump, e.g., 0.1.0 → 0.2.0)
- `fix:` - Bug fix (patch version bump, e.g., 0.1.0 → 0.1.1)
- `docs:` - Documentation changes (no version bump)
- `style:` - Code style changes (no version bump)
- `refactor:` - Code refactoring (no version bump)
- `perf:` - Performance improvements (patch version bump)
- `test:` - Test changes (no version bump)
- `chore:` - Build/tooling changes (no version bump)
- `BREAKING CHANGE:` - Breaking API changes (major version bump, e.g., 0.1.0 → 1.0.0)

### Examples

```bash
# Feature (minor version bump)
git commit -m "feat: add support for batch transaction queries"

# Bug fix (patch version bump)
git commit -m "fix: correct signature validation in MmnClient"

# Breaking change (major version bump)
git commit -m "feat: redesign IndexerClient API

BREAKING CHANGE: IndexerClient methods now return Pydantic models instead of dicts"

# No version bump
git commit -m "docs: update README with new examples"
```

### Automated Releases

Releases are automatically created when commits are pushed to the `main` branch:

1. The GitHub Action analyzes commit messages since the last release
2. Determines the next version based on conventional commits
3. Updates version in `pyproject.toml` and `mmn/__init__.py`
4. Generates/updates `CHANGELOG.md`
5. Creates a git tag and GitHub release
6. Publishes package artifacts

### Manual Release

To manually trigger a release:

```bash
# Install semantic-release
pip install python-semantic-release

# Preview next version (dry run)
semantic-release version --no-commit

# Create release
semantic-release version
semantic-release publish
```

## Architecture

The SDK is organized into three main components:

```
mmn_sdk/
   __init__.py          # Public API exports
   types.py             # Pydantic models and type definitions
   indexer_client.py    # Blockchain data queries
   zk_client.py         # Zero-knowledge proof generation
   mmn_client.py        # Transaction and account management
```

### Key Features

- **Async/Await**: All I/O operations are asynchronous using `aiohttp`
- **Simple API**: No context managers required - clients create new sessions per request
- **Type Safety**: Pydantic models for validation and serialization
- **Cryptography**: Ed25519 signing with `pynacl`
- **Error Handling**: Comprehensive error messages and validation

## Security Considerations

- Private keys are handled securely and cleared from memory after use
- PKCS#8 format for Ed25519 private keys
- Zero-knowledge proofs for authentication without revealing secrets
- Secure random number generation for key pairs

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
