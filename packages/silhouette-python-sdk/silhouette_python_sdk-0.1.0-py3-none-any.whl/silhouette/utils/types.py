from typing import Literal, TypedDict

from hyperliquid.utils.types import (
    SIDES,
    ActiveAssetCtx,
    ActiveAssetCtxMsg,
    ActiveAssetCtxSubscription,
    ActiveAssetData,
    ActiveAssetDataMsg,
    ActiveAssetDataSubscription,
    ActiveSpotAssetCtx,
    ActiveSpotAssetCtxMsg,
    AllMidsData,
    AllMidsMsg,
    AllMidsSubscription,
    AssetInfo,
    BboData,
    BboMsg,
    BboSubscription,
    BuilderInfo,
    CandleSubscription,
    Cloid,
    CrossLeverage,
    Fill,
    IsolatedLeverage,
    L2BookData,
    L2BookMsg,
    L2BookSubscription,
    L2Level,
    Leverage,
    Meta,
    OrderUpdatesSubscription,
    OtherWsMsg,
    PerpAssetCtx,
    PerpDexSchemaInput,
    PongMsg,
    Side,
    SpotAssetCtx,
    SpotAssetInfo,
    SpotMeta,
    SpotMetaAndAssetCtxs,
    SpotTokenInfo,
    Subscription,
    Trade,
    TradesMsg,
    TradesSubscription,
    UserEventsData,
    UserEventsMsg,
    UserEventsSubscription,
    UserFillsData,
    UserFillsMsg,
    UserFillsSubscription,
    UserFundingsSubscription,
    UserNonFundingLedgerUpdatesSubscription,
    WebData2Subscription,
    WsMsg,
)
from typing_extensions import NotRequired

TransactionType = Literal["deposit", "withdrawal", "trade", "order"]
HistoryFilterType = Literal["deposit", "withdrawal", "trade", "order", "all"]


class SessionInfo(TypedDict):
    id: str
    startTime: str
    filtered: bool


class TransactionMetadata(TypedDict):
    direction: str
    rawAmount: str


class TransactionItem(TypedDict):
    id: str
    type: TransactionType
    timestamp: str
    address: str
    amount: str
    token: str
    status: str
    txHash: str
    metadata: TransactionMetadata


class GetHistoryRequest(TypedDict, total=False):
    address: str
    type: HistoryFilterType
    limit: int
    offset: int
    sessionOnly: bool


class GetHistoryResponse(TypedDict, total=False):
    transactions: list[TransactionItem]
    session: SessionInfo


class GetHealthResponse(TypedDict, total=False):
    status: str
    timestamp: str
    environment: str
    version: str


class GetFeaturesResponse(TypedDict, total=False):
    environment: str
    features: dict[str, bool]
    version: str


class GetHealthInfoResponse(TypedDict):
    environment: str
    features: dict[str, bool]
    version: str
    status: str
    uptime: int
    memory: dict[str, int]
    node: str
    pid: int
    platform: str
    arch: str
    env: dict[str, str]


class GetHealthReadyResponse(TypedDict):
    ready: bool
    services: dict[str, bool]


class DetailedSessionInfo(TypedDict):
    id: str
    startTime: str
    environment: str
    testMode: bool
    filteringEnabled: bool


class GetSessionResponse(TypedDict):
    success: bool
    session: DetailedSessionInfo


class HistoryStats(TypedDict):
    totalTransactions: int
    deposits: int
    withdrawals: int
    trades: int
    sessionStart: str


class GetStatsResponse(TypedDict):
    stats: HistoryStats


class ResetSessionInfo(TypedDict):
    id: str
    startTime: str


class ResetSessionResponse(TypedDict):
    session: ResetSessionInfo


ClearingVenue = Literal["hyperliquid", "silhouette", "hybrid"]


class CreateOrderRequest(TypedDict):
    """TypedDict for the createOrder operation payload."""

    side: Literal["buy", "sell"]
    orderType: Literal["limit", "market"]
    baseToken: str
    quoteToken: str
    amount: str
    price: NotRequired[str]  # Required for limit orders
    expiry: NotRequired[int]  # Optional Unix timestamp
    clearingVenue: NotRequired[ClearingVenue]


class CreateOrderResponse(TypedDict):
    """TypedDict for a successful createOrder response."""

    message: str
    orderId: str


class Balance(TypedDict):
    """TypedDict for a single token balance."""

    token: str
    total: str
    available: str
    availableFloat: str
    locked: str


class GetBalancesResponse(TypedDict):
    """TypedDict for a successful getBalances response."""

    balances: list[Balance]


class InitiateWithdrawalResponse(TypedDict):
    """TypedDict for a successful initiateWithdrawal response."""

    message: str
    withdrawalId: str


WithdrawalState = Literal["pending", "processing", "completed", "failed"]


class WithdrawalInfo(TypedDict, total=False):
    """TypedDict for withdrawal information."""

    withdrawalId: str
    token: str
    amount: str
    state: WithdrawalState
    txHash: str | None
    errorMessage: str | None
    created_at: str
    updated_at: str


class GetWithdrawalStatusResponse(TypedDict):
    """TypedDict for a successful getWithdrawalStatus response."""

    withdrawal: WithdrawalInfo


class GetUserWithdrawalsResponse(TypedDict):
    """TypedDict for a successful getUserWithdrawals response."""

    withdrawals: list[WithdrawalInfo]


OrderStatus = Literal["pending", "open", "filled", "partially_filled", "cancelled", "expired", "failed"]


class CancelOrderRequest(TypedDict):
    """TypedDict for the cancelOrder operation payload."""

    orderId: str


class CancelOrderResponse(TypedDict):
    """TypedDict for a successful cancelOrder response."""

    message: str
    orderId: str


class GetUserOrdersRequest(TypedDict, total=False):
    """TypedDict for the getUserOrders operation payload."""

    status: OrderStatus


class Order(TypedDict, total=False):
    """TypedDict representing a single order."""

    orderId: str
    side: Literal["buy", "sell"]
    orderType: Literal["limit", "market"]
    baseToken: str
    quoteToken: str
    amount: str
    amountFloat: str
    price: str
    priceFloat: str
    expiry: int
    status: OrderStatus
    createdAt: int
    updatedAt: int
    filledAmount: str
    remainingAmount: str


class GetUserOrdersResponse(TypedDict):
    """TypedDict for a successful getUserOrders response."""

    orders: list[Order]


__all__ = [
    "ActiveAssetCtx",
    "ActiveAssetCtxMsg",
    "ActiveAssetCtxSubscription",
    "ActiveAssetData",
    "ActiveAssetDataMsg",
    "ActiveAssetDataSubscription",
    "ActiveSpotAssetCtx",
    "ActiveSpotAssetCtxMsg",
    "AllMidsData",
    "AllMidsMsg",
    "AllMidsSubscription",
    "AssetInfo",
    "Balance",
    "BboData",
    "BboMsg",
    "BboSubscription",
    "BuilderInfo",
    "CandleSubscription",
    "ClearingVenue",
    "Cloid",
    "CreateOrderRequest",
    "CreateOrderResponse",
    "CrossLeverage",
    "DetailedSessionInfo",
    "Fill",
    "GetBalancesResponse",
    "GetFeaturesResponse",
    "GetHealthInfoResponse",
    "GetHealthReadyResponse",
    "GetHealthResponse",
    "GetHistoryRequest",
    "GetHistoryResponse",
    "GetSessionResponse",
    "GetStatsResponse",
    "GetUserWithdrawalsResponse",
    "GetWithdrawalStatusResponse",
    "HistoryFilterType",
    "HistoryStats",
    "InitiateWithdrawalResponse",
    "IsolatedLeverage",
    "L2BookData",
    "L2BookMsg",
    "L2BookSubscription",
    "L2Level",
    "Leverage",
    "Meta",
    "OrderUpdatesSubscription",
    "OtherWsMsg",
    "PerpAssetCtx",
    "PerpDexSchemaInput",
    "PongMsg",
    "SIDES",
    "Side",
    "ResetSessionInfo",
    "ResetSessionResponse",
    "SessionInfo",
    "SpotAssetCtx",
    "SpotAssetInfo",
    "SpotMeta",
    "SpotMetaAndAssetCtxs",
    "SpotTokenInfo",
    "Subscription",
    "Trade",
    "TradesMsg",
    "TradesSubscription",
    "TransactionItem",
    "TransactionMetadata",
    "TransactionType",
    "UserEventsData",
    "UserEventsMsg",
    "UserEventsSubscription",
    "UserFillsData",
    "UserFillsMsg",
    "UserFillsSubscription",
    "UserFundingsSubscription",
    "UserNonFundingLedgerUpdatesSubscription",
    "WebData2Subscription",
    "WithdrawalInfo",
    "WithdrawalState",
    "WsMsg",
]
