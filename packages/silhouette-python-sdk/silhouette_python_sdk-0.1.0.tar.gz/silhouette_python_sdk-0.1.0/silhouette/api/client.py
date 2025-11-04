"""Silhouette API client for integrating with the enclave API."""

import json
from typing import Any, cast

import requests
from typing_extensions import Unpack

from silhouette.api.auth import AuthConfig, AuthManager
from silhouette.utils.types import (
    CancelOrderRequest,
    CancelOrderResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    GetBalancesResponse,
    GetFeaturesResponse,
    GetHealthInfoResponse,
    GetHealthReadyResponse,
    GetHealthResponse,
    GetHistoryRequest,
    GetHistoryResponse,
    GetSessionResponse,
    GetStatsResponse,
    GetUserOrdersRequest,
    GetUserOrdersResponse,
    GetUserWithdrawalsResponse,
    GetWithdrawalStatusResponse,
    InitiateWithdrawalResponse,
    ResetSessionResponse,
)


class SilhouetteApiError(Exception):
    """Custom exception for Silhouette API errors."""

    def __init__(self, code: str, message: str, status: int | None):
        super().__init__(f"API Error [{code}]: {message} (HTTP {status})")
        self.code = code
        self.message = message
        self.status = status


class HealthOperations:
    """Health endpoint operations for the enclave API."""

    def __init__(self, client: "SilhouetteApiClient"):
        self._client = client

    def get_health(self) -> GetHealthResponse:
        """Get basic health check information."""
        return cast(GetHealthResponse, self._client._request_operation("getHealth"))

    def get_features(self) -> GetFeaturesResponse:
        """Get health features discovery information."""
        return cast(GetFeaturesResponse, self._client._request_operation("getHealthFeatures"))

    def get_info(self) -> GetHealthInfoResponse:
        """Get detailed system info (debug mode only)."""
        return cast(GetHealthInfoResponse, self._client._request_operation("getHealthInfo"))

    def get_ready(self) -> GetHealthReadyResponse:
        """Get health readiness check."""
        return cast(GetHealthReadyResponse, self._client._request_operation("getHealthReady"))


class HistoryOperations:
    """History endpoint operations for the enclave API."""

    def __init__(self, client: "SilhouetteApiClient"):
        self._client = client

    def get_history(self, **params: Unpack[GetHistoryRequest]) -> GetHistoryResponse:
        """Get transaction history with optional filtering parameters."""
        return cast(GetHistoryResponse, self._client._request_operation("getHistory", dict(params)))

    def get_session(self) -> GetSessionResponse:
        """Get current session information."""
        return cast(GetSessionResponse, self._client._request_operation("getSession"))

    def get_stats(self) -> GetStatsResponse:
        """Get history statistics for current session."""
        return cast(GetStatsResponse, self._client._request_operation("getStats"))

    def reset_session(self) -> ResetSessionResponse:
        """Reset session (feature flag protected)."""
        return cast(ResetSessionResponse, self._client._request_operation("resetSession"))


class TestOperations:
    """Test endpoint operations for the enclave API."""

    __test__ = False

    def __init__(self, client: "SilhouetteApiClient"):
        self._client = client

    def get_test_balance(self, address: str) -> dict[str, Any]:
        """Get test balances for a given address."""
        return self._client._request_operation("getTestBalance", {"address": address})

    def spoof_deposit(self, user_address: str, token_symbol: str, amount: str) -> dict[str, Any]:
        """Spoof a deposit for a user."""
        params = {
            "userAddress": user_address,
            "tokenSymbol": token_symbol,
            "amount": amount,
        }
        return self._client._request_operation("spoofDeposit", params)

    def spoof_withdrawal(self, user_address: str, token_symbol: str, amount: str) -> dict[str, Any]:
        """Simulates a withdrawal for a user."""
        params = {
            "userAddress": user_address,
            "tokenSymbol": token_symbol,
            "amount": amount,
        }
        return self._client._request_operation("spoofWithdrawal", params)


class UserOperations:
    """Authenticated user endpoint operations for the enclave API."""

    __test__ = False

    def __init__(self, client: "SilhouetteApiClient"):
        self._client = client

    def get_balances(self) -> GetBalancesResponse:
        """Get user balances."""
        return cast(GetBalancesResponse, self._client._request_operation("getBalances"))

    def get_balance(self, token_symbol: str) -> int:
        """
        Get the available balance for a specific token from the Silhouette enclave.

        This safely handles cases where the user or token is not found, returning 0
        instead of raising an error.

        Args:
            token_symbol: The symbol of the token (e.g., "USDC")

        Returns:
            The available balance as an integer in Silhouette's fixed-point format.

        Raises:
            SilhouetteApiError: For unexpected API errors (not USER_NOT_FOUND)
        """
        try:
            balances_data = self.get_balances()
            balance_info = next(
                (b for b in balances_data.get("balances", []) if b["token"] == token_symbol),
                None,
            )
            if balance_info:
                return int(balance_info["available"])
        except SilhouetteApiError as e:
            if e.code == "USER_NOT_FOUND":
                return 0  # User doesn't exist yet, so balance is 0
            raise  # Re-raise other unexpected API errors
        else:
            return 0

    def get_balance_float(self, token_symbol: str) -> float:
        """
        Get the available balance for a specific token as a float.

        This uses the `availableFloat` field from the API, returning 0.0 if the
        user or token is not found.

        Args:
            token_symbol: The symbol of the token (e.g., "USDC")

        Returns:
            The available balance as a float.

        Raises:
            SilhouetteApiError: For unexpected API errors (not USER_NOT_FOUND)
        """
        try:
            balances_data = self.get_balances()
            balance_info = next(
                (b for b in balances_data.get("balances", []) if b["token"] == token_symbol),
                None,
            )
            if balance_info and "availableFloat" in balance_info:
                return float(balance_info["availableFloat"])
            return 0.0
        except SilhouetteApiError as e:
            if e.code == "USER_NOT_FOUND":
                return 0.0  # User doesn't exist yet, so balance is 0
            raise  # Re-raise other unexpected API errors

    def initiate_withdrawal(self, token_symbol: str, amount: str) -> InitiateWithdrawalResponse:
        """Initiate a withdrawal for the authenticated user."""
        params = {"tokenSymbol": token_symbol, "amount": amount}
        return cast(InitiateWithdrawalResponse, self._client._request_operation("initiateWithdrawal", params))

    def get_withdrawal_status(self, withdrawal_id: str) -> GetWithdrawalStatusResponse:
        """Get the status of a specific withdrawal by ID."""
        params = {"withdrawalId": withdrawal_id}
        return cast(GetWithdrawalStatusResponse, self._client._request_operation("getWithdrawalStatus", params))

    def get_user_withdrawals(self) -> GetUserWithdrawalsResponse:
        """Get all withdrawals for the authenticated user."""
        return cast(GetUserWithdrawalsResponse, self._client._request_operation("getUserWithdrawals"))


class OrderOperations:
    """Authenticated order endpoint operations for the enclave API."""

    def __init__(self, client: "SilhouetteApiClient"):
        self._client = client

    def create_order(self, **params: Unpack[CreateOrderRequest]) -> CreateOrderResponse:
        """Create a new order."""
        return cast(CreateOrderResponse, self._client._request_operation("createOrder", dict(params)))

    def cancel_order(self, **params: Unpack[CancelOrderRequest]) -> CancelOrderResponse:
        """Cancel an existing order."""
        return cast(CancelOrderResponse, self._client._request_operation("cancelOrder", dict(params)))

    def get_user_orders(self, **params: Unpack[GetUserOrdersRequest]) -> GetUserOrdersResponse:
        """Get all orders for the authenticated user."""
        return cast(GetUserOrdersResponse, self._client._request_operation("getUserOrders", dict(params)))


class SilhouetteApiClient:
    """
    Silhouette API client for interacting with the enclave API.

    Provides access to health and history operations through a simple,
    synchronous interface that follows Hyperliquid SDK patterns.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8081",
        timeout: float = 30.0,
        private_key: str | None = None,
        keystore_path: str | None = None,
        auto_auth: bool = True,
        max_login_retries: int = 3,
        login_retry_base_delay: float = 1.0,
        login_retry_max_delay: float = 10.0,
        verify_ssl: bool = True,
        chain_id: int = 1,
    ):
        """
        Initialize the Silhouette API client.

        Args:
            base_url: Base URL for the enclave API
            timeout: Request timeout in seconds
            private_key: Private key for auto-authentication (hex string with or without 0x prefix)
            keystore_path: Path to encrypted keystore file (alternative to private_key)
            auto_auth: Enable automatic authentication and token refresh on 401
            max_login_retries: Maximum login retry attempts on failure
            login_retry_base_delay: Base delay for exponential backoff (seconds)
            login_retry_max_delay: Maximum delay for exponential backoff (seconds)
            verify_ssl: Enable SSL certificate verification (defaults to True for production)
            chain_id: Chain ID for SIWE authentication (1 for mainnet, 421614 for Arbitrum Sepolia)
        """
        self.base_url = base_url
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Initialize auth manager
        auth_config = AuthConfig(
            auto_auth=auto_auth,
            max_login_retries=max_login_retries,
            login_retry_base_delay=login_retry_base_delay,
            login_retry_max_delay=login_retry_max_delay,
            chain_id=chain_id,
        )
        self._auth = AuthManager(
            client=self,
            config=auth_config,
            private_key=private_key,
            keystore_path=keystore_path,
        )

        # Backwards compatibility: expose _jwt_token property
        self._jwt_token: str | None = None

        # Initialize operation groups
        self.health = HealthOperations(self)
        self.history = HistoryOperations(self)
        self.test = TestOperations(self)
        self.user = UserOperations(self)
        self.order = OrderOperations(self)

    @property
    def wallet(self):
        """Get the wallet used for authentication."""
        return self._auth.wallet

    def login(self, message: str, signature: str) -> str:
        """
        Authenticate with the enclave using a SIWE message and signature.

        Args:
            message: The SIWE message.
            signature: The signature of the message.

        Returns:
            The JWT token string.
        """
        token = self._raw_login(message, signature)
        self._auth.set_token(token)
        self._jwt_token = token  # Backwards compatibility
        return token

    def _raw_login(self, message: str, signature: str) -> str:
        """
        Perform raw login API call without updating auth state.

        This is used internally by AuthManager to avoid circular dependencies.

        Args:
            message: The SIWE message.
            signature: The signature of the message.

        Returns:
            The JWT token string.

        Raises:
            SilhouetteApiError: If login fails
        """
        params = {"message": message, "signature": signature}
        # Use _raw_request to bypass auth logic
        response = self._raw_request("login", params, token=None)
        token_value = response.get("token")
        if not isinstance(token_value, str) or not token_value:
            raise SilhouetteApiError("LOGIN_FAILED", "No token in response", None)
        return token_value

    def _request_operation(
        self, operation: str, params: dict[str, Any] | None = None, token: str | None = None
    ) -> dict[str, Any]:
        """
        Make a request to the enclave API with the envelope pattern.

        This method handles automatic authentication and 401 retry logic.

        Args:
            operation: The operation name to execute
            params: Optional parameters for the operation
            token: Optional JWT token to use for this specific request

        Returns:
            Response data with responseMetadata excluded

        Raises:
            requests.Timeout: On request timeout
            requests.ConnectionError: On connection failure
            SilhouetteApiError: On API error responses (JSON with code/error)
            ValueError: On malformed or non-JSON responses
        """
        # Operations that don't require authentication
        unauthenticated_ops = {
            "login",
            "getHealth",
            "getHealthFeatures",
            "getHealthInfo",
            "getHealthReady",
        }

        requires_auth = operation not in unauthenticated_ops

        # Auto-login if needed and no explicit token provided
        if requires_auth and token is None:
            # Check for existing token (backwards compatibility)
            token = self._auth.get_token() or self._jwt_token
            if token is None:
                # No token exists, try to auto-authenticate
                self._auth.ensure_authenticated()
                token = self._auth.get_token()

        # Make the request
        try:
            return self._raw_request(operation, params, token)
        except SilhouetteApiError as e:
            # Handle 401 by attempting re-login and retry
            if e.status == 401 and requires_auth:
                if self._auth.handle_auth_error(e.status):
                    # Login succeeded, retry with new token
                    token = self._auth.get_token()
                    return self._raw_request(operation, params, token)
            # Re-raise if not 401 or if login failed
            raise

    def _raw_request(
        self, operation: str, params: dict[str, Any] | None = None, token: str | None = None
    ) -> dict[str, Any]:
        """
        Make a raw HTTP request to the enclave API without auth logic.

        Args:
            operation: The operation name to execute
            params: Optional parameters for the operation
            token: Optional JWT token to use for this request

        Returns:
            Response data with responseMetadata excluded

        Raises:
            requests.Timeout: On request timeout
            requests.ConnectionError: On connection failure
            SilhouetteApiError: On API error responses (JSON with code/error)
            ValueError: On malformed or non-JSON responses
        """
        # Build request payload with envelope pattern
        payload = {"operation": operation}
        if params:
            payload.update(params)

        url = f"{self.base_url}/v0"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Make the HTTP request
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout, verify=self.verify_ssl)

        # Parse JSON response (best-effort)
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            # If HTTP error with non-JSON body, surface concise status
            if not response.ok:
                raise ValueError(f"HTTP {response.status_code} error with non-JSON response") from e
            raise ValueError("Failed to parse response JSON") from e

        # Handle error responses
        if not response.ok:
            error_msg = response_data.get("error", f"HTTP {response.status_code}")
            error_code = response_data.get("code", "UNKNOWN_ERROR")
            raise SilhouetteApiError(error_code, error_msg, response.status_code)

        # Extract data from envelope, excluding responseMetadata
        response_data.pop("responseMetadata", None)
        return dict(response_data)
