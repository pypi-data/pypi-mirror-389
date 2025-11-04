"""Hyperliquid WebSocket Manager - direct pass-through to Hyperliquid Python SDK."""

import threading
from typing import Any

# Re-export everything from official hyperliquid.websocket_manager for compatibility
from hyperliquid.websocket_manager import *  # noqa: F403, F401

# Alias WebSocketManager so we can wrap it in our own class with the same name
# This allows us to add extra methods while maintaining compatibility
from hyperliquid.websocket_manager import WebsocketManager as HyperliquidWebsocketManager


class WebsocketManager(threading.Thread):
    """
    Hyperliquid WebSocket Manager for real-time data.

    This class is a direct pass-through to the Hyperliquid WebsocketManager,
    maintaining exact compatibility with the official Hyperliquid Python SDK.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the WebsocketManager with the same parameters as Hyperliquid SDK."""
        self._hyperliquid_ws = HyperliquidWebsocketManager(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Delegate all method calls to the underlying Hyperliquid WebsocketManager."""
        return getattr(self._hyperliquid_ws, name)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Silhouette's wrapper of the Hyperliquid WebsocketManager (pass-through to {repr(self._hyperliquid_ws)})"
        )
