"""
Agent client for TradingEconomics indicators
"""

from typing import Dict, Any
from .base import AgentClientBase
from ..models.requests import IndicatorsRequest, HistoricalDataRequest


class AgentIndicatorsClient(AgentClientBase):
    """Agent client for economic indicators and historical data"""

    def get_indicators(self, request: IndicatorsRequest) -> Dict[str, Any]:
        """
        Get economic indicators data

        Args:
            request: IndicatorsRequest model

        Returns:
            Standardized response with indicator data
        """
        return self._execute(self._te_client.get_indicators, request)

    def get_historical_data(self, request: HistoricalDataRequest) -> Dict[str, Any]:
        """
        Get historical data for specific indicator

        Args:
            request: HistoricalDataRequest model

        Returns:
            Standardized response with historical data
        """
        return self._execute(self._te_client.get_historical_data, request)
