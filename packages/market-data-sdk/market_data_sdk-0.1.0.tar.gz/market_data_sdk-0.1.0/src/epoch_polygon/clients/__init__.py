"""
Agent-optimized Polygon clients.

Each client wraps a specific domain of Polygon API endpoints with
agent-friendly single BaseModel parameters and standardized responses.
All clients are singletons accessed via get_client_instance().
"""

from .base import AgentClientBase, get_client_instance
from .agent_aggs_client import AgentAggsClient
from .agent_snapshot_client import AgentSnapshotClient
from .agent_trades_client import AgentTradesClient
from .agent_quotes_client import AgentQuotesClient

__all__ = [
    "AgentClientBase",
    "get_client_instance",
    "AgentAggsClient",
    "AgentSnapshotClient",
    "AgentTradesClient",
    "AgentQuotesClient",
]