"""
Agent client for TradingEconomics markets data
"""

from typing import Dict, Any
from .base import AgentClientBase
from ..models.requests import MarketsRequest


class AgentMarketsClient(AgentClientBase):
    """Agent client for market data (indices, currencies, commodities, bonds, crypto)"""

    def get_markets(self, request: MarketsRequest) -> Dict[str, Any]:
        """
        Get market data

        Args:
            request: MarketsRequest model

        Returns:
            Standardized response with market data
        """
        return self._execute(self._te_client.get_markets, request)
