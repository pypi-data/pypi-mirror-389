"""
Re-export of official hyperliquid.utils.

This module provides the hyperliquid.utils functionality from the official SDK.
After importing silhouette, use standard hyperliquid imports:

    from hyperliquid.utils import constants, signing, types

    # Access constants
    print(constants.MAINNET_API_URL)

    # Access types
    meta: types.Meta = {...}

    # Access signing functions
    signature = signing.sign_l1_action(...)
"""

# Explicit re-exports for IDE support and type checking
from silhouette.hyperliquid.utils import constants, error, signing, types

__all__ = ["constants", "error", "signing", "types"]
