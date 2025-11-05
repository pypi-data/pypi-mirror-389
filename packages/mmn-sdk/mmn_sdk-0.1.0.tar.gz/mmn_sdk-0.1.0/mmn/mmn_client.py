"""MMN Client for blockchain transactions and account management."""

import json
import time
import secrets
from typing import Literal, Optional
import aiohttp
import base58
import nacl.signing
from Crypto.Hash import SHA256

from .types import (
    MmnClientConfig,
    EphemeralKeyPair,
    TxMsg,
    SignedTx,
    SendTransactionRequest,
    AddTxResponse,
    GetCurrentNonceResponse,
    GetAccountByAddressResponse,
    ExtraInfo,
)


# Constants
TX_TYPE_TRANSFER = 0
TX_TYPE_FAUCET = 1
DECIMALS = 6
ED25519_PRIVATE_KEY_LENGTH = 32
ED25519_PUBLIC_KEY_LENGTH = 32

# ASN.1 DER encoding constants
ASN1_SEQUENCE_TAG = 0x30
ASN1_OCTET_STRING_TAG = 0x04
ASN1_INTEGER_TAG = 0x02
ASN1_LENGTH = 0x80
PKCS8_VERSION = 0
ED25519_OID_BYTES = bytes([0x06, 0x03, 0x2B, 0x65, 0x70])
PKCS8_ALGORITHM_ID_LENGTH = 0x0B
PKCS8_PRIVATE_KEY_OCTET_OUTER_LENGTH = 0x22
PKCS8_PRIVATE_KEY_OCTET_INNER_LENGTH = 0x20


class MmnClient:
    """
    Client for interacting with the MMN blockchain.

    Provides functionality for:
    - Creating and sending transactions
    - Managing accounts and nonces
    - Generating ephemeral key pairs
    - Signing transactions with Ed25519
    """

    def __init__(self, config: MmnClientConfig):
        """
        Initialize the MMN client.

        Args:
            config: Configuration for the MMN client
        """
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(
            total=config.timeout / 1000.0
        )  # Convert ms to seconds
        self.request_id = 0

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if config.headers:
            self.headers.update(config.headers)

    async def _make_request(self, method: str, params: Optional[dict] = None) -> dict:
        """
        Make JSON-RPC request.

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            Response result

        Raises:
            Exception: If request fails or returns error
        """
        self.request_id += 1

        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.request_id,
        }

        async with aiohttp.ClientSession(
            timeout=self.timeout, headers=self.headers
        ) as session:
            try:
                async with session.post(self.base_url, json=request_data) as response:
                    response.raise_for_status()
                    result = await response.json()

                    if "error" in result and result["error"]:
                        error = result["error"]
                        raise Exception(
                            f"JSON-RPC Error {error['code']}: {error['message']}"
                        )

                    return result.get("result", {})

            except aiohttp.ServerTimeoutError:
                raise TimeoutError(f"Request timeout after {self.timeout.total}s")
            except aiohttp.ClientResponseError as e:
                raise Exception(f"HTTP {e.status}: {e.message}") from e
            except aiohttp.ClientError as e:
                raise Exception(f"Request failed: {str(e)}") from e

    def _encode_length(self, length: int) -> bytes:
        """
        Encode length in ASN.1 DER format.

        Args:
            length: The length value to encode

        Returns:
            ASN.1 DER encoded length bytes
        """
        if length < ASN1_LENGTH:
            return bytes([length])

        length_bytes = []
        temp_length = length
        while temp_length > 0:
            length_bytes.insert(0, temp_length & 0xFF)
            temp_length >>= 8

        return bytes([ASN1_LENGTH | len(length_bytes)] + length_bytes)

    def _raw_ed25519_to_pkcs8_hex(self, raw_key: bytes) -> str:
        """
        Convert raw Ed25519 private key to PKCS#8 format.

        Args:
            raw_key: Raw 32-byte Ed25519 private key

        Returns:
            PKCS#8 formatted private key in hex

        Raises:
            ValueError: If input validation fails
        """
        if len(raw_key) != ED25519_PRIVATE_KEY_LENGTH:
            raise ValueError(
                f"Ed25519 private key must be exactly {ED25519_PRIVATE_KEY_LENGTH} bytes"
            )

        version_bytes = bytes([ASN1_INTEGER_TAG, 0x01, PKCS8_VERSION])

        algorithm_id = (
            bytes([ASN1_SEQUENCE_TAG, PKCS8_ALGORITHM_ID_LENGTH]) + ED25519_OID_BYTES
        )

        private_key_octet_string = (
            bytes([ASN1_OCTET_STRING_TAG, PKCS8_PRIVATE_KEY_OCTET_OUTER_LENGTH])
            + bytes([ASN1_OCTET_STRING_TAG, PKCS8_PRIVATE_KEY_OCTET_INNER_LENGTH])
            + raw_key
        )

        pkcs8_body = version_bytes + algorithm_id + private_key_octet_string

        pkcs8 = (
            bytes([ASN1_SEQUENCE_TAG])
            + self._encode_length(len(pkcs8_body))
            + pkcs8_body
        )

        return pkcs8.hex()

    def generate_ephemeral_key_pair(self) -> EphemeralKeyPair:
        """
        Generate secure ephemeral key pair using Ed25519.

        Returns:
            Ephemeral key pair with private and public keys

        Example:
            >>> client = MmnClient(config)
            >>> keypair = client.generate_ephemeral_key_pair()
            >>> print(keypair.public_key)
        """
        seed = secrets.token_bytes(ED25519_PRIVATE_KEY_LENGTH)

        signing_key = nacl.signing.SigningKey(seed)
        verify_key = signing_key.verify_key

        private_key_hex = self._raw_ed25519_to_pkcs8_hex(seed)

        public_key_base58 = base58.b58encode(bytes(verify_key)).decode("ascii")

        return EphemeralKeyPair(
            private_key=private_key_hex,
            public_key=public_key_base58,
        )

    def get_address_from_user_id(self, user_id: str) -> str:
        """
        Generate address from user ID using SHA-256.

        Args:
            user_id: User identifier

        Returns:
            Base58 encoded address

        Example:
            >>> client = MmnClient(config)
            >>> address = client.get_address_from_user_id("user123")
        """
        hash_obj = SHA256.new(user_id.encode("utf-8"))
        hash_bytes = hash_obj.digest()
        return base58.b58encode(hash_bytes).decode("ascii")

    def _serialize_transaction(self, tx: TxMsg) -> bytes:
        """
        Serialize transaction for signing.

        Args:
            tx: Transaction message

        Returns:
            Serialized transaction bytes
        """
        data = (
            f"{tx.type}|{tx.sender}|{tx.recipient}|{tx.amount}|"
            f"{tx.text_data}|{tx.nonce}|{tx.extra_info}"
        )
        return data.encode("utf-8")

    def _sign_transaction(self, tx: TxMsg, private_key_hex: str) -> str:
        """
        Sign a transaction with Ed25519.

        Args:
            tx: Transaction message to sign
            private_key_hex: Private key in PKCS#8 hex format

        Returns:
            Base58 encoded signature

        Raises:
            ValueError: If signing fails
        """
        serialized_data = self._serialize_transaction(tx)

        private_key_bytes = bytes.fromhex(private_key_hex)
        seed = private_key_bytes[-ED25519_PRIVATE_KEY_LENGTH:]

        signing_key = nacl.signing.SigningKey(seed)

        signed = signing_key.sign(serialized_data)
        signature = signed.signature

        if tx.type == TX_TYPE_FAUCET:
            return base58.b58encode(signature).decode("ascii")

        verify_key = signing_key.verify_key
        import base64

        user_sig = {
            "PubKey": base64.b64encode(bytes(verify_key)).decode("ascii"),
            "Sig": base64.b64encode(signature).decode("ascii"),
        }

        user_sig_json = json.dumps(user_sig)
        return base58.b58encode(user_sig_json.encode("utf-8")).decode("ascii")

    def _create_and_sign_tx(
        self,
        tx_type: int,
        sender: str,
        recipient: str,
        amount: str,
        nonce: int,
        public_key: str,
        private_key: str,
        zk_proof: str,
        zk_pub: str,
        timestamp: Optional[int] = None,
        text_data: Optional[str] = None,
        extra_info: Optional[ExtraInfo] = None,
    ) -> SignedTx:
        """
        Create and sign a transaction.

        Args:
            tx_type: Transaction type (TRANSFER or FAUCET)
            sender: Sender address
            recipient: Recipient address
            amount: Amount to transfer (as string)
            nonce: Transaction nonce
            public_key: Public key
            private_key: Private key in PKCS#8 hex format
            zk_proof: Zero-knowledge proof
            zk_pub: ZK public input
            timestamp: Transaction timestamp (default: current time)
            text_data: Additional text data
            extra_info: Extra transaction information

        Returns:
            Signed transaction

        Raises:
            ValueError: If validation fails
        """
        if not self.validate_address(sender):
            raise ValueError("Invalid sender address")
        if not self.validate_address(recipient):
            raise ValueError("Invalid recipient address")
        if sender == recipient:
            raise ValueError("Sender and recipient addresses cannot be the same")

        tx_msg = TxMsg(
            type=tx_type,
            sender=sender,
            recipient=recipient,
            amount=amount,
            timestamp=timestamp or int(time.time() * 1000),
            text_data=text_data or "",
            nonce=nonce,
            extra_info=json.dumps(extra_info.to_dict()) if extra_info else "",
            zk_proof=zk_proof,
            zk_pub=zk_pub,
        )

        signature = self._sign_transaction(tx_msg, private_key)

        return SignedTx(tx_msg=tx_msg, signature=signature)

    async def _add_tx(self, signed_tx: SignedTx) -> AddTxResponse:
        """
        Add a signed transaction to the blockchain.

        Args:
            signed_tx: Signed transaction

        Returns:
            Transaction response
        """
        params = {
            "tx_msg": signed_tx.tx_msg.model_dump(),
            "signature": signed_tx.signature,
        }

        result = await self._make_request("tx.addtx", params)
        return AddTxResponse(**result)

    async def send_transaction(self, params: SendTransactionRequest) -> AddTxResponse:
        """
        Send a transaction by user IDs.

        Converts user IDs to addresses and sends the transaction.

        Args:
            params: Transaction parameters

        Returns:
            Transaction response

        Example:
            >>> client = MmnClient(config)
            >>> response = await client.send_transaction(
            ...     SendTransactionRequest(
            ...         sender="user_id_1",
            ...         recipient="user_id_2",
            ...         amount="1000000",
            ...         nonce=0,
            ...         public_key="...",
            ...         private_key="...",
            ...         zk_proof="...",
            ...         zk_pub="...",
            ...     )
            ... )
            >>> print(response.tx_hash)
        """
        from_address = self.get_address_from_user_id(params.sender)
        to_address = self.get_address_from_user_id(params.recipient)

        signed_tx = self._create_and_sign_tx(
            tx_type=TX_TYPE_TRANSFER,
            sender=from_address,
            recipient=to_address,
            amount=params.amount,
            nonce=params.nonce,
            public_key=params.public_key,
            private_key=params.private_key,
            zk_proof=params.zk_proof,
            zk_pub=params.zk_pub,
            timestamp=params.timestamp,
            text_data=params.text_data,
            extra_info=params.extra_info,
        )

        return await self._add_tx(signed_tx)

    async def send_transaction_by_address(
        self, params: SendTransactionRequest
    ) -> AddTxResponse:
        """
        Send a transaction by wallet addresses.

        Args:
            params: Transaction parameters with sender/recipient as addresses

        Returns:
            Transaction response

        Example:
            >>> client = MmnClient(config)
            >>> response = await client.send_transaction_by_address(params)
        """
        signed_tx = self._create_and_sign_tx(
            tx_type=TX_TYPE_TRANSFER,
            sender=params.sender,
            recipient=params.recipient,
            amount=params.amount,
            nonce=params.nonce,
            public_key=params.public_key,
            private_key=params.private_key,
            zk_proof=params.zk_proof,
            zk_pub=params.zk_pub,
            timestamp=params.timestamp,
            text_data=params.text_data,
            extra_info=params.extra_info,
        )

        return await self._add_tx(signed_tx)

    async def get_current_nonce(
        self, user_id: str, tag: Literal["latest", "pending"] = "latest"
    ) -> GetCurrentNonceResponse:
        """
        Get current nonce for an account by user ID.

        Args:
            user_id: User identifier
            tag: Nonce tag (latest or pending)

        Returns:
            Current nonce response

        Example:
            >>> client = MmnClient(config)
            >>> nonce_resp = await client.get_current_nonce("user123")
            >>> print(nonce_resp.nonce)
        """
        address = self.get_address_from_user_id(user_id)
        result = await self._make_request(
            "account.getcurrentnonce", {"address": address, "tag": tag}
        )
        return GetCurrentNonceResponse(**result)

    async def get_account_by_user_id(self, user_id: str) -> GetAccountByAddressResponse:
        """
        Get account information by user ID.

        Args:
            user_id: User identifier

        Returns:
            Account information

        Example:
            >>> client = MmnClient(config)
            >>> account = await client.get_account_by_user_id("user123")
            >>> print(f"Balance: {account.balance}")
        """
        address = self.get_address_from_user_id(user_id)
        result = await self._make_request("account.getaccount", {"address": address})
        return GetAccountByAddressResponse(**result)

    def scale_amount_to_decimals(
        self, original_amount: int, decimals: int = DECIMALS
    ) -> str:
        """
        Scale amount to blockchain decimals.

        Args:
            original_amount: Original amount (in smallest unit)
            decimals: Number of decimal places

        Returns:
            Scaled amount as string

        Example:
            >>> client = MmnClient(config)
            >>> scaled = client.scale_amount_to_decimals(1)  # 1 token
            >>> print(scaled)  # "1000000" (with 6 decimals)
        """
        scaled_amount = original_amount * (10**decimals)
        return str(scaled_amount)

    def validate_address(self, address: str) -> bool:
        """
        Validate a blockchain address.

        Args:
            address: Address to validate

        Returns:
            True if valid, False otherwise

        Example:
            >>> client = MmnClient(config)
            >>> is_valid = client.validate_address("some_address")
        """
        try:
            decoded = base58.b58decode(address)
            return len(decoded) == ED25519_PUBLIC_KEY_LENGTH
        except Exception:
            return False

    def validate_amount(self, balance: str, amount: str) -> bool:
        """
        Validate that amount does not exceed balance.

        Args:
            balance: Available balance (as string)
            amount: Amount to send (as string)

        Returns:
            True if amount is valid, False otherwise

        Example:
            >>> client = MmnClient(config)
            >>> is_valid = client.validate_amount("1000000", "500000")
        """
        try:
            big_balance = int(balance)
            big_amount = int(amount)
            return big_amount <= big_balance
        except ValueError:
            return False
