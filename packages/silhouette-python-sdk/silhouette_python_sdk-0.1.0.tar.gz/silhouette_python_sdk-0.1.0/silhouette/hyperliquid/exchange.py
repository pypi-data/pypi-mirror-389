"""Hyperliquid Exchange client - direct pass-through to Hyperliquid Python SDK."""

from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING, Any

from eth_account.signers.local import LocalAccount
from hyperliquid.api import API

# Re-export everything from official hyperliquid.exchange for compatibility
from hyperliquid.exchange import *  # noqa: F403, F401

# Alias Exchange so we can wrap it in our own class with the same name
# This allows us to add extra methods while maintaining compatibility
from hyperliquid.exchange import Exchange as HyperliquidExchange
from hyperliquid.utils.types import Meta, SpotMeta

if TYPE_CHECKING:
    from silhouette.utils.conversions import TokenConverter


class HyperliquidDepositError(RuntimeError):
    """Raised when a Hyperliquid spot transfer used for deposits fails."""


class Exchange(API):
    """
    Silhouette's wrapper of the Hyperliquid Exchange client for trading operations.

    This class is a direct pass-through to the Hyperliquid Exchange client,
    maintaining exact compatibility with the official Hyperliquid Python SDK
    with enhancements provided by Silhouette.
    """

    def __init__(
        self,
        wallet: LocalAccount,
        base_url: str | None = None,
        meta: Meta | None = None,
        vault_address: str | None = None,
        account_address: str | None = None,
        spot_meta: SpotMeta | None = None,
        perp_dexs: list[str] | None = None,
        timeout: float | None = None,
    ):
        """Initialize the Exchange client with the same parameters as Hyperliquid SDK."""
        self._hyperliquid_exchange = HyperliquidExchange(
            wallet=wallet,
            base_url=base_url,
            meta=meta,
            vault_address=vault_address,
            account_address=account_address,
            spot_meta=spot_meta,
            perp_dexs=perp_dexs,
            timeout=timeout,
        )

    def __getattr__(self, name: str) -> Any:
        """Delegate all method calls to the underlying Hyperliquid Exchange client."""
        return getattr(self._hyperliquid_exchange, name)

    def __repr__(self) -> str:
        """String representation."""
        return f"Silhouette's wrapper of the Hyperliquid Exchange client (pass-through to {repr(self._hyperliquid_exchange)})"

    ### Silhouette-enhanced methods below ###

    def deposit_to_silhouette(
        self,
        contract_address: str,
        token_symbol: str,
        amount: float,
        converter: "TokenConverter",
    ) -> dict[str, Any]:
        """
        Deposit tokens from Hyperliquid to Silhouette contract via spot transfer.

        Args:
            contract_address: Silhouette contract address to deposit to
            token_symbol: The symbol of the token to deposit (e.g., "USDC", "HYPE")
            amount: The amount to deposit (automatically quantized to token precision)
            converter: TokenConverter instance for looking up token metadata

        Returns:
            The response from the spot_transfer call

        Raises:
            ValueError: If the token symbol is not supported or amount is invalid
            HyperliquidDepositError: If the Hyperliquid deposit fails
        """
        # Only allow supported tokens
        supported_tokens = {"USDC", "HYPE"}
        if token_symbol not in supported_tokens:
            raise ValueError(
                f"Token '{token_symbol}' is not supported. "
                f"Silhouette currently only supports: {', '.join(sorted(supported_tokens))}"
            )

        # Get asset info from converter
        asset = converter.asset_info.get(token_symbol)
        if not asset:
            raise ValueError(f"Unsupported token symbol: {token_symbol}")

        # Quantize amount to token precision to avoid floating-point errors
        try:
            decimals = int(asset.get("weiDecimals", 0))
            quant = Decimal(1) / (Decimal(10) ** decimals)
            amount_dec = Decimal(str(amount)).quantize(quant, rounding=ROUND_DOWN)
        except Exception as e:
            raise ValueError(f"Invalid amount {amount} for {token_symbol}") from e

        if amount_dec <= 0:
            raise ValueError("Amount must be positive")

        # Prefer including tokenId when available to disambiguate tokens
        token_to_transfer = token_symbol
        if token_symbol != "USDC":  # noqa: S105
            token_id = asset.get("tokenId")
            if token_id:
                token_to_transfer = f"{token_symbol}:{token_id}"

        response: dict[str, Any] = self.spot_transfer(
            destination=contract_address,
            token=token_to_transfer,
            amount=float(amount_dec),
        )
        status = response.get("status")
        if status != "ok":
            raise HyperliquidDepositError(f"Hyperliquid deposit failed: {response}")

        return response
