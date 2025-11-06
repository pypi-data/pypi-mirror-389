"""
Polygon.io SDK Module
Provides a unified client interface for accessing Polygon.io market data

For LangGraph agents, use the registry functions:
    >>> from polygon import get_tools
    >>> tools = get_tools()
    >>> agent = create_react_agent(model, tools=tools)
"""

# Original Polygon SDK exports (for backward compatibility)
from .client import PolygonClient
from .models import (
    PolygonConfig,
    StockData,
    OptionsData,
    ForexData,
    CryptoData,
    AggregateBar,
    Trade,
    Quote,
)

# Agent tool registry - main interface for LangGraph agents
from .registry import (
    get_tools,
    get_tool,
    get_tool_names,
)

# Agent models - for constructing requests
from .models.asset import AssetClass, PolygonAsset
from .models.filters import DateFilter
from .models.requests import (
    AggregatesRequest,
    SnapshotRequest,
    DetailsRequest,
    TradesRequest,
    QuotesRequest,
    SearchRequest,
    GetPreviousCloseRequest,
    GetSnapshotDirectionRequest,
    GetLastTradeRequest,
    GetLastQuoteRequest,
)

# Agent clients - for advanced use cases
from .clients import (
    AgentClientBase,
    AgentAggsClient,
    AgentSnapshotClient,
    AgentTradesClient,
    AgentQuotesClient,
    get_client_instance,
)

__all__ = [
    # Tool registry (main interface for agents)
    "get_tools",
    "get_tool",
    "get_tool_names",

    # Agent models
    "AssetClass",
    "PolygonAsset",
    "DateFilter",
    "AggregatesRequest",
    "SnapshotRequest",
    "DetailsRequest",
    "TradesRequest",
    "QuotesRequest",
    "SearchRequest",
    "GetPreviousCloseRequest",
    "GetSnapshotDirectionRequest",
    "GetLastTradeRequest",
    "GetLastQuoteRequest",

    # Agent clients
    "AgentClientBase",
    "AgentAggsClient",
    "AgentSnapshotClient",
    "AgentTradesClient",
    "AgentQuotesClient",
    "get_client_instance",

    # Original SDK (backward compatibility)
    "PolygonClient",
    "PolygonConfig",
    "StockData",
    "OptionsData",
    "ForexData",
    "CryptoData",
    "AggregateBar",
    "Trade",
    "Quote",
]

__version__ = "0.1.0"