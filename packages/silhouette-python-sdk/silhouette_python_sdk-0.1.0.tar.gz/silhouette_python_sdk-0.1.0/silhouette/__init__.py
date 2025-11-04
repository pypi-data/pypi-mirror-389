"""
Silhouette Python SDK - Python SDK for trading on Silhouette, the shielded exchange on Hyperliquid.

This package is a drop-in REPLACEMENT for the Hyperliquid Python SDK with additional
convenience methods, plus integration with the Silhouette enclave API.

IMPORTANT: Install only silhouette-python-sdk; it depends on hyperliquid-python-sdk,
do not install hyperliquid-python-sdk separately. The official Hyperliquid SDK is
included as a dependency, and silhouette-python-sdk provides enhanced versions of
all Hyperliquid classes.

Usage:
    # IMPORTANT: Always import silhouette FIRST, before any hyperliquid imports
    import silhouette

    # Then use standard hyperliquid imports to get enhanced versions
    from hyperliquid.info import Info
    from hyperliquid.exchange import Exchange
    from hyperliquid.websocket_manager import WebsocketManager

    info = Info()  # Enhanced with get_balance(), await_withdrawal_completion()
    exchange = Exchange(wallet)  # Enhanced with deposit_to_silhouette()
    ws_manager = WebsocketManager()

    # Silhouette enclave API integration
    from silhouette.api import SilhouetteApiClient

    api_client = SilhouetteApiClient()
"""

import sys
import warnings
from importlib.metadata import PackageNotFoundError, version

# Check if hyperliquid modules were already imported before silhouette
# This helps users avoid confusion from mixed official/enhanced classes
_HYPERLIQUID_MODULES = [
    "hyperliquid.info",
    "hyperliquid.exchange",
    "hyperliquid.websocket_manager",
    "hyperliquid.api",
    "hyperliquid.utils",
]
_already_imported = [mod for mod in _HYPERLIQUID_MODULES if mod in sys.modules]
if _already_imported:
    warnings.warn(
        f"Hyperliquid modules {_already_imported} were imported before silhouette. "
        "For best results, import silhouette FIRST before any hyperliquid imports. "
        "This ensures you get the enhanced versions with all convenience methods.",
        UserWarning,
        stacklevel=2,
    )

# Now import our enhanced wrapper modules
# ruff: noqa: E402 - Imports must come after the warning check above
import silhouette.hyperliquid.api
import silhouette.hyperliquid.exchange
import silhouette.hyperliquid.info
import silhouette.hyperliquid.utils
import silhouette.hyperliquid.utils.constants
import silhouette.hyperliquid.utils.error
import silhouette.hyperliquid.utils.signing
import silhouette.hyperliquid.utils.types
import silhouette.hyperliquid.websocket_manager
from silhouette.api import SilhouetteApiClient, SilhouetteApiError

# Inject our enhanced versions into sys.modules as 'hyperliquid.*'
# This makes `from hyperliquid.info import Info` work with our enhanced versions
sys.modules["hyperliquid.info"] = silhouette.hyperliquid.info
sys.modules["hyperliquid.exchange"] = silhouette.hyperliquid.exchange
sys.modules["hyperliquid.websocket_manager"] = silhouette.hyperliquid.websocket_manager
sys.modules["hyperliquid.api"] = silhouette.hyperliquid.api
sys.modules["hyperliquid.utils"] = silhouette.hyperliquid.utils
sys.modules["hyperliquid.utils.signing"] = silhouette.hyperliquid.utils.signing
sys.modules["hyperliquid.utils.constants"] = silhouette.hyperliquid.utils.constants
sys.modules["hyperliquid.utils.error"] = silhouette.hyperliquid.utils.error
sys.modules["hyperliquid.utils.types"] = silhouette.hyperliquid.utils.types

try:
    # Prefer the distribution name from pyproject
    __version__ = version("silhouette-python-sdk")
except PackageNotFoundError:
    try:
        __version__ = version("silhouette")
    except PackageNotFoundError:
        __version__ = "0.0.0"

__all__ = ["SilhouetteApiClient", "SilhouetteApiError"]
