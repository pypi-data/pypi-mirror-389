"""Hyperliquid API client - direct pass-through to Hyperliquid Python SDK."""

from typing import Any

# Re-export everything from official hyperliquid.api for compatibility
from hyperliquid.api import *  # noqa: F403, F401

# Alias API so we can wrap it in our own class with the same name
# This allows us to add extra methods while maintaining compatibility
from hyperliquid.api import API as HyperliquidAPI


class API:
    """
    Hyperliquid API client base class.

    This class is a direct pass-through to the Hyperliquid API client,
    maintaining exact compatibility with the official Hyperliquid Python SDK.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the API client with the same parameters as Hyperliquid SDK."""
        self._hyperliquid_api = HyperliquidAPI(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Delegate all method calls to the underlying Hyperliquid API client."""
        return getattr(self._hyperliquid_api, name)

    def __repr__(self) -> str:
        """String representation."""
        return f"Hyperliquid API client (pass-through to {repr(self._hyperliquid_api)})"
