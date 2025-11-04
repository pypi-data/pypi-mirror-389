"""Hyperliquid Info client - direct pass-through to Hyperliquid Python SDK."""

import time
from typing import Any

from hyperliquid.api import API

# Re-export everything from official hyperliquid.info for compatibility
from hyperliquid.info import *  # noqa: F403, F401

# Alias Info so we can wrap it in our own class with the same name
# This allows us to add extra methods while maintaining compatibility
from hyperliquid.info import Info as HyperliquidInfo
from hyperliquid.utils.types import Meta, SpotMeta


class Info(API):
    """
    Silhouette's wrapper of the Hyperliquid Info client for accessing market and user data.

    This class is a direct pass-through to the Hyperliquid Info client,
    maintaining exact compatibility with the official Hyperliquid Python SDK
    with enhancements provided by Silhouette.
    """

    def __init__(
        self,
        base_url: str | None = None,
        skip_ws: bool = False,
        meta: Meta | None = None,
        spot_meta: SpotMeta | None = None,
        perp_dexs: list[str] | None = None,
        timeout: float | None = None,
    ):
        """Initialize the Info client with the same parameters as Hyperliquid SDK."""
        self._hyperliquid_info = HyperliquidInfo(
            base_url=base_url,
            skip_ws=skip_ws,
            meta=meta,
            spot_meta=spot_meta,
            perp_dexs=perp_dexs,
            timeout=timeout,
        )

    def __getattr__(self, name: str) -> Any:
        """Delegate all method calls to the underlying Hyperliquid Info client."""
        return getattr(self._hyperliquid_info, name)

    def __repr__(self) -> str:
        """String representation."""
        return f"Silhouette's wrapper of the Hyperliquid Info client (pass-through to {repr(self._hyperliquid_info)})"

    ### Silhouette-enhanced methods below ###

    def get_balance(self, wallet_address: str, token_symbol: str) -> float:
        """
        Get the user's balance on Hyperliquid for a specific token.

        Args:
            wallet_address: User's wallet address
            token_symbol: The symbol of the token (e.g., "USDC")

        Returns:
            The total balance as a float. Returns 0.0 if the token is not found.
        """
        spot_user_state = self.spot_user_state(wallet_address)
        for balance in spot_user_state.get("balances", []):
            if balance.get("coin") == token_symbol:
                total_str = balance.get("total", "0")
                return float(total_str)
        return 0.0

    def await_withdrawal_completion(
        self,
        wallet_address: str,
        pre_withdrawal_balance: float,
        token_symbol: str,
        timeout: int = 60,
    ) -> bool:
        """
        Poll the Hyperliquid balance until it increases, confirming withdrawal completion.

        Args:
            wallet_address: User's wallet address
            pre_withdrawal_balance: The user's Hyperliquid balance before the withdrawal
            token_symbol: The token to monitor
            timeout: The maximum time to wait in seconds

        Returns:
            True if the withdrawal is confirmed.

        Raises:
            ValueError: If timeout is not positive
            TimeoutError: If the balance does not update within the timeout period
        """
        if timeout <= 0:
            raise ValueError("Timeout must be positive")

        start_time = time.time()
        while time.time() - start_time < timeout:
            current_balance = self.get_balance(wallet_address, token_symbol)
            if current_balance > pre_withdrawal_balance:
                print(
                    f"Withdrawal confirmed on Hyperliquid. Balance changed from "
                    f"{pre_withdrawal_balance} to {current_balance}."
                )
                return True
            time.sleep(5)

        raise TimeoutError(f"Withdrawal did not reflect on Hyperliquid balance within {timeout}s.")
