"""Utilities for converting between Silhouette and Hyperliquid token representations."""

from decimal import ROUND_DOWN, Decimal
from typing import Any


class TokenConverter:
    """
    Handles conversion between Silhouette's integer representation and
    Hyperliquid's float representation for token amounts.
    """

    def __init__(self, asset_info: dict[str, Any]):
        """
        Initialize the converter with asset metadata.

        Args:
            asset_info: Dictionary mapping token symbols to their metadata,
                       including weiDecimals for proper conversion.
        """
        self.asset_info = asset_info

    def get_decimals(self, token_symbol: str) -> int:
        """
        Get the decimal places (weiDecimals) for a given token.

        Args:
            token_symbol: The symbol of the token (e.g., "USDC").

        Returns:
            The number of decimal places for the token.

        Raises:
            ValueError: If the token symbol is not found in asset info.
        """
        asset = self.asset_info.get(token_symbol)
        if not asset:
            raise ValueError(f"Unsupported token symbol: {token_symbol}")
        return int(asset["weiDecimals"])

    def to_int(self, token_symbol: str, amount: float) -> int:
        """
        Convert a float amount (Hyperliquid representation) to an integer
        (Silhouette representation).

        Uses Decimal arithmetic to avoid floating-point precision errors.

        Args:
            token_symbol: The symbol of the token (e.g., "USDC").
            amount: The amount as a float.

        Returns:
            The amount as an integer in the token's smallest unit.
        """
        decimals = self.get_decimals(token_symbol)
        # Convert to Decimal via string to avoid float precision issues
        factor = Decimal(10) ** decimals
        amount_decimal = Decimal(str(amount))
        # Multiply and quantize to ensure no fractional smallest units
        result = (amount_decimal * factor).quantize(Decimal(1), rounding=ROUND_DOWN)
        return int(result)

    def to_float(self, token_symbol: str, amount: int) -> float:
        """
        Convert an integer amount (Silhouette representation) to a float
        (Hyperliquid representation).

        Uses Decimal arithmetic to avoid floating-point precision errors.

        Args:
            token_symbol: The symbol of the token (e.g., "USDC").
            amount: The amount as an integer in the token's smallest unit.

        Returns:
            The amount as a float.
        """
        decimals = self.get_decimals(token_symbol)
        # Use Decimal arithmetic for precision
        factor = Decimal(10) ** decimals
        amount_decimal = Decimal(amount)
        result_decimal = amount_decimal / factor
        return float(result_decimal)


def load_asset_info_from_hyperliquid(info_client: Any) -> dict[str, Any]:
    """
    Load asset metadata from Hyperliquid for use with TokenConverter.

    Args:
        info_client: A Hyperliquid Info client instance.

    Returns:
        Dictionary mapping token names to their metadata.
    """
    spot_meta = info_client.spot_meta()
    return {token["name"]: token for token in spot_meta.get("tokens", [])}
