"""
Hyperliquid API clients - enhanced wrappers around the official SDK.

This is a drop-in replacement for the official Hyperliquid Python SDK.
After installing silhouette-python-sdk, users must import silhouette first,
then use standard hyperliquid imports:

Usage:
    import silhouette  # Required: triggers sys.modules injection

    from hyperliquid.info import Info
    from hyperliquid.exchange import Exchange
    from hyperliquid.websocket_manager import WebsocketManager
    from hyperliquid.utils.constants import MAINNET_API_URL
    from hyperliquid.utils.types import Meta

    # Market data - includes enhanced methods
    info = Info()
    balance = info.get_balance(wallet_address, "USDC")

    # Trading - includes enhanced methods
    exchange = Exchange(wallet)
    exchange.deposit_to_silhouette(contract_address, "USDC", "100.0", converter)

    # Real-time data
    ws_manager = WebsocketManager()

    # Access utilities
    print(MAINNET_API_URL)
"""
