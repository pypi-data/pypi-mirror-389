# silhouette-python-sdk

<div align="center">

[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/silhouette-exchange/silhouette-python-sdk/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/format.json)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/silhouette-exchange/silhouette-python-sdk/blob/main/.pre-commit-config.yaml)
[![Semantic Versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/silhouette-exchange/silhouette-python-sdk/releases)
[![License](https://img.shields.io/pypi/l/silhouette-python-sdk)](https://github.com/silhouette-exchange/silhouette-python-sdk/blob/main/LICENSE.md)

Python SDK for trading on Silhouette - the shielded exchange on Hyperliquid.

</div>

## Overview

This package provides:
- **Drop-in replacement** for the official Hyperliquid Python SDK with enhanced convenience methods
- **Silhouette API integration** for trading on the shielded exchange
- **Type-safe** interfaces with comprehensive TypedDict definitions
- **Enhanced functionality** including balance checking, deposit automation, and withdrawal polling

**IMPORTANT**: This package replaces `hyperliquid-python-sdk`. Do not install both packages together. The official Hyperliquid SDK is included as a dependency.

## Installation

```bash
pip install silhouette-python-sdk
```

## Quick Start

### Using Enhanced Hyperliquid SDK

```python
# IMPORTANT: Always import silhouette FIRST
import silhouette

# Then use standard hyperliquid imports to get enhanced versions
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils.constants import TESTNET_API_URL

# Enhanced Info client with get_balance() and await_withdrawal_completion()
info = Info(base_url=TESTNET_API_URL, skip_ws=True)

# Check spot balances
spot_state = info.spot_user_state("0x1615330FAee0776a643CC0075AD2008418e067Db")
print(spot_state)

# Get specific token balance (convenience method)
usdc_balance = info.get_balance("0x1615330FAee0776a643CC0075AD2008418e067Db", "USDC")
print(f"USDC Balance: {usdc_balance}")
```

### Using Silhouette API

```python
from silhouette import SilhouetteApiClient

# Initialize client with auto-authentication
client = SilhouetteApiClient(
    base_url="https://api-alpha.silhouette.exchange:8081",
    private_key="your_private_key_here",
    auto_auth=True,
)

# Check balances
balances = client.user.get_balances()
print(balances)

# Place an order
order = client.order.create_order(
    side="buy",
    orderType="limit",
    baseToken="HYPE",
    quoteToken="USDC",
    amount="1.0",
    price="0.001",
)
print(f"Order placed: {order['orderId']}")
```

## Enhanced Features

### Hyperliquid SDK Enhancements

The enhanced Hyperliquid SDK includes these convenience methods:

**Info class:**
- `get_balance(wallet_address: str, token_symbol: str) -> float` - Get user's balance for a specific token
- `await_withdrawal_completion(wallet_address: str, pre_withdrawal_balance: float, token_symbol: str, timeout: int) -> bool` - Poll balance until withdrawal completes

**Exchange class:**
- `deposit_to_silhouette(contract_address: str, token_symbol: str, amount: str, converter: TokenConverter) -> dict` - Deposit tokens from Hyperliquid to Silhouette contract

All other Hyperliquid SDK methods work exactly as documented in the [official Hyperliquid SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk).

### Silhouette API Client

The `SilhouetteApiClient` provides access to the Silhouette shielded exchange:

- User operations: balances, withdrawal initiation
- Order management: create, cancel, query orders
- Trade execution with privacy guarantees
- Automatic authentication and session management

## Configuration

Create `examples/config.json` from the example template:

```bash
cp examples/config.json.example examples/config.json
```

Then configure:
- `account_address`: Your wallet's public address
- `secret_key`: Your wallet's private key (or use `keystore_path` for a keystore file)
- `use_testnet`: Set to `true` for testnet, `false` for mainnet

### [Optional] Using an API Wallet

Generate and authorise a new API private key on <https://app.hyperliquid.xyz/API>, and set the API wallet's private key as the `secret_key` in `examples/config.json`. Note that you must still set the public key of the main wallet (not the API wallet) as the `account_address`.

## Usage Examples

See [examples/](examples/) for complete examples:

- **[silhouette_full_workflow.py](examples/silhouette_full_workflow.py)** - Complete workflow: deposit, trade, withdraw
- **[basic_order.py](examples/basic_order.py)** - Place and manage orders on Hyperliquid
- **[basic_spot_order.py](examples/basic_spot_order.py)** - Spot trading examples
- **[basic_adding.py](examples/basic_adding.py)** - Deposit funds to Hyperliquid

Run any example after configuring your credentials:

```bash
python examples/silhouette_full_workflow.py
```

## Development

### Prerequisites

- Python 3.10 or higher
- [Poetry](https://python-poetry.org/) for dependency management

### Setup

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
make install
```

### Development Workflow

#### Code Quality and Linting

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting, with pre-commit hooks for automated checks.

**Normal development workflow:**
1. Make your changes
2. Run `git add .` to stage changes
3. Run `git commit` - pre-commit hooks will run automatically

**If pre-commit hooks fail:**
1. `make check` - See all linting issues
2. `make fix` - Auto-fix safe issues
3. `make format` - Format code
4. `make test` - Run tests
5. Stage changes and commit again

#### Available Make Commands

```bash
make build                 # Builds as a tarball and a wheel
make check                 # Run ruff check without fixes
make check-safety          # Run safety checks on dependencies
make cleanup               # Cleanup project
make fix                   # Run ruff check with fixes
make fix-unsafe            # Run ruff check with unsafe fixes
make format                # Run ruff format
make install               # Install dependencies from poetry.lock
make install-types         # Find and install additional types for mypy
make lockfile-update       # Update poetry.lock
make lockfile-update-full  # Fully regenerate poetry.lock
make poetry-download       # Download and install poetry
make pre-commit            # Run all pre-commit hooks
make publish               # Publish the package to PyPI
make test                  # Run tests with pytest
make update-dev-deps       # Update development dependencies to latest versions
```

Run `make` without arguments to see this list of commands.

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
poetry run pytest tests/hyperliquid/info_test.py -v

# Run with coverage report
poetry run pytest --cov=silhouette --cov-report=html
```

## Project Structure

```
silhouette-python-sdk/
├── silhouette/
│   ├── api/              # Silhouette API client
│   │   ├── client.py     # Main API client
│   │   └── auth.py       # Authentication
│   ├── hyperliquid/      # Enhanced Hyperliquid SDK wrappers
│   │   ├── info.py       # Enhanced Info class
│   │   ├── exchange.py   # Enhanced Exchange class
│   │   └── utils/        # Re-exported utilities
│   └── utils/
│       ├── conversions.py # Token conversion utilities
│       └── types.py       # Type definitions
├── tests/                # Test suite
│   ├── api/              # API client tests
│   ├── hyperliquid/      # Hyperliquid wrapper tests
│   └── utils/            # Utility tests
└── examples/             # Usage examples
```

## Releases

See [GitHub Releases](https://github.com/silhouette-exchange/silhouette-python-sdk/releases) for available versions.

We follow [Semantic Versioning](https://semver.org/) and use [Release Drafter](https://github.com/marketplace/actions/release-drafter) for automated release notes.

### Building and Releasing

1. Bump version: `poetry version <major|minor|patch>`
2. Commit changes: `git commit -am "Bump version to X.Y.Z"`
3. Create GitHub release
4. Publish: `make publish`

## Licence

This project is licensed under the terms of the MIT licence. See [LICENSE](LICENSE.md) for more details.

```bibtex
@misc{silhouette-python-sdk,
  author = {Silhouette},
  title = {Python SDK for trading on Silhouette - the shielded exchange on Hyperliquid},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/silhouette-exchange/silhouette-python-sdk}}
}
```

## Credits

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template).
