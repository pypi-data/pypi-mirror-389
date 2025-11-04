"""Authentication configuration and utilities for Silhouette API client."""

import getpass
import json
import random
import secrets
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, cast

import eth_account
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount
from siwe import SiweMessage

if TYPE_CHECKING:
    from silhouette.api.client import SilhouetteApiClient


@dataclass
class AuthConfig:
    """Configuration for automatic authentication."""

    auto_auth: bool = True
    """Enable automatic authentication when API calls require it."""

    max_login_retries: int = 3
    """Maximum number of login attempts before giving up."""

    login_retry_base_delay: float = 1.0
    """Base delay in seconds between login retries (doubled each attempt)."""

    login_retry_max_delay: float = 10.0
    """Maximum delay in seconds between login retries (caps exponential backoff)."""

    chain_id: int = 1
    """Chain ID for SIWE message signing (1 for mainnet, 421614 for Arbitrum Sepolia testnet)."""


class AuthManager:
    """Manages authentication state and automatic login for the API client."""

    # Token TTL - assume 1 hour until server provides expiresAt
    TOKEN_TTL_SECONDS = 3600

    def __init__(
        self,
        client: "SilhouetteApiClient",
        config: AuthConfig,
        private_key: str | None = None,
        keystore_path: str | None = None,
    ):
        """
        Initialize the authentication manager.

        Args:
            client: The SilhouetteApiClient instance
            config: Authentication configuration
            private_key: Private key for auto-authentication (hex string with or without 0x prefix)
            keystore_path: Path to encrypted keystore file (alternative to private_key)

        Raises:
            ValueError: If both private_key and keystore_path are provided
        """
        self.client = client
        self.config = config
        self._jwt_token: str | None = None
        self._token_expires_at: float | None = None
        self._wallet: LocalAccount | None = None
        self._login_lock = threading.Lock()

        # Load wallet if auto_auth is enabled
        if self.config.auto_auth:
            if private_key and keystore_path:
                raise ValueError("Specify either private_key or keystore_path, not both")
            if private_key:
                self._wallet = eth_account.Account.from_key(private_key)
            elif keystore_path:
                self._wallet = self._load_keystore(keystore_path)

    def _load_keystore(self, keystore_path: str) -> LocalAccount:
        """
        Load wallet from encrypted keystore file.

        Args:
            keystore_path: Path to keystore JSON file

        Returns:
            Decrypted LocalAccount

        Raises:
            FileNotFoundError: If keystore file doesn't exist
            ValueError: If keystore path is not a file
        """
        path = Path(keystore_path).expanduser()
        if not path.is_absolute():
            # Make relative paths relative to the caller's directory
            path = Path.cwd() / path

        if not path.exists():
            raise FileNotFoundError(f"Keystore file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Keystore path is not a file: {path}")

        with path.open() as f:
            keystore = json.load(f)

        password = getpass.getpass("Enter keystore password: ")
        secret_key = eth_account.Account.decrypt(keystore, password)
        return cast(LocalAccount, eth_account.Account.from_key(secret_key))

    @property
    def wallet(self) -> LocalAccount | None:
        """Get the wallet used for authentication."""
        return self._wallet

    def get_token(self) -> str | None:
        """Get the current JWT token."""
        return self._jwt_token

    def set_token(self, token: str, expires_at: float | None = None) -> None:
        """
        Set the JWT token and expiry time.

        Args:
            token: JWT token string
            expires_at: Unix timestamp when token expires (defaults to now + TOKEN_TTL_SECONDS)
        """
        self._jwt_token = token
        if expires_at is None:
            expires_at = time.time() + self.TOKEN_TTL_SECONDS
        self._token_expires_at = expires_at

    def ensure_authenticated(self) -> None:
        """
        Ensure the client is authenticated, performing auto-login if necessary.

        Raises:
            ValueError: If auto_auth is disabled and no token is present
            RuntimeError: If login fails after max retries
        """

        # Currently the only thing that unsets the token is handle_auth_error after a 401
        # We can improve this later to proactively refresh before expiry if needed
        if self._jwt_token is not None:
            return  # Already authenticated

        if not self.config.auto_auth:
            raise ValueError("Not authenticated and auto_auth is disabled. Call login() explicitly.")

        if self._wallet is None:
            raise ValueError("Cannot auto-authenticate without private_key or keystore_path")

        # Use lock to prevent concurrent login attempts
        with self._login_lock:
            # Double-checked locking: another thread may have logged in while we waited for the lock
            # This prevents redundant login attempts in multi-threaded scenarios
            if self._jwt_token is not None:
                return  # type: ignore[unreachable]  # Reachable when multiple threads call this concurrently

            self._perform_login_with_retry()

    def _perform_login_with_retry(self) -> None:
        """
        Perform login with exponential backoff and jitter.

        Raises:
            RuntimeError: If all retry attempts fail
        """
        last_error = None

        for attempt in range(self.config.max_login_retries):
            try:
                self._perform_login()
                return  # Success
            except Exception as e:
                last_error = e
                if attempt < self.config.max_login_retries - 1:
                    # Calculate delay with exponential backoff and jitter
                    delay = min(
                        self.config.login_retry_base_delay * (2**attempt),
                        self.config.login_retry_max_delay,
                    )
                    # 10% jitter
                    jitter = random.uniform(0, delay * 0.1)  # noqa: S311

                    time.sleep(delay + jitter)

        raise RuntimeError(f"Login failed after {self.config.max_login_retries} attempts: {last_error}") from last_error

    def _extract_domain_from_url(self, url: str) -> str:
        """
        Extract domain (host:port) from a URL for SIWE message.

        Args:
            url: Full URL like "https://api.example.com:8081/path"

        Returns:
            Domain string like "api.example.com:8081" or "localhost:8081"
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        # netloc includes host and port (e.g., "localhost:8081" or "api.example.com")
        domain = parsed.netloc
        if not domain:
            # Fallback if URL parsing fails
            domain = "localhost"
        return domain

    def _perform_login(self) -> None:
        """
        Perform the SIWE login flow.

        Raises:
            Various exceptions from SIWE message creation/signing or API calls
        """
        if self._wallet is None:
            raise ValueError("No wallet configured for login")

        # Extract domain from base_url for SIWE message
        domain = self._extract_domain_from_url(self.client.base_url)

        # Generate SIWE message
        message = SiweMessage(
            domain=domain,
            address=self._wallet.address,
            statement="Sign in with Ethereum to the app.",
            uri=f"{self.client.base_url}/login",
            version="1",
            chain_id=self.config.chain_id,
            nonce=secrets.token_hex(12),
            issued_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        prepared_message_str = message.prepare_message()

        # Sign the message
        message_to_sign = encode_defunct(text=prepared_message_str)
        signed_message = self._wallet.sign_message(message_to_sign)

        # Verify signature client-side
        message.verify(signed_message.signature)

        # Call login API
        signature_hex = "0x" + signed_message.signature.hex()
        token = self.client._raw_login(prepared_message_str, signature_hex)
        self.set_token(token)

    def handle_auth_error(self, response_status: int) -> bool:
        """
        Handle authentication errors by attempting to re-login.

        Args:
            response_status: HTTP status code from failed request

        Returns:
            True if login was attempted and should retry the request, False otherwise
        """
        if response_status != 401:
            return False

        if not self.config.auto_auth:
            return False

        if self._wallet is None:
            return False

        # Clear expired token and re-login
        with self._login_lock:
            # Clear the expired token
            self._jwt_token = None
            self._token_expires_at = None

            # Attempt login
            try:
                self._perform_login_with_retry()
                return True  # Retry the original request
            except Exception:
                return False  # Login failed, don't retry
