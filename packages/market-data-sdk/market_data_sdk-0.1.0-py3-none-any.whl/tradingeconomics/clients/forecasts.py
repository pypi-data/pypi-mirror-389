"""
Agent client for TradingEconomics forecasts
"""

from typing import Dict, Any
from .base import AgentClientBase
from ..models.requests import ForecastsRequest


class AgentForecastsClient(AgentClientBase):
    """Agent client for economic forecasts"""

    def get_forecasts(self, request: ForecastsRequest) -> Dict[str, Any]:
        """
        Get economic forecasts

        Args:
            request: ForecastsRequest model

        Returns:
            Standardized response with forecast data
        """
        return self._execute(self._te_client.get_forecasts, request)
