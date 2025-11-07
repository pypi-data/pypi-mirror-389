"""
Agent client for TradingEconomics news
"""

from typing import Dict, Any
from .base import AgentClientBase
from ..models.requests import NewsRequest


class AgentNewsClient(AgentClientBase):
    """Agent client for economic news"""

    def get_news(self, request: NewsRequest) -> Dict[str, Any]:
        """
        Get economic news

        Args:
            request: NewsRequest model

        Returns:
            Standardized response with news articles
        """
        return self._execute(self._te_client.get_news, request)
