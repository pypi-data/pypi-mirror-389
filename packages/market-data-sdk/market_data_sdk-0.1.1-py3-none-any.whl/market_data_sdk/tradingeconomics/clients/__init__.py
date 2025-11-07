"""
TradingEconomics agent clients
"""

from .base import AgentClientBase, get_client_instance
from .indicators import AgentIndicatorsClient
from .calendar import AgentCalendarClient
from .markets import AgentMarketsClient
from .forecasts import AgentForecastsClient
from .news import AgentNewsClient
from .reference import AgentReferenceClient

__all__ = [
    "AgentClientBase",
    "get_client_instance",
    "AgentIndicatorsClient",
    "AgentCalendarClient",
    "AgentMarketsClient",
    "AgentForecastsClient",
    "AgentNewsClient",
    "AgentReferenceClient",
]
