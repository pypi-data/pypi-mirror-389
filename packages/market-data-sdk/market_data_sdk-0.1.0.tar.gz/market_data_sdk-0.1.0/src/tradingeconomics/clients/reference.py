"""
Agent client for TradingEconomics reference data
"""

from typing import Dict, Any
from .base import AgentClientBase
from ..models.requests import CountryDataRequest, CreditRatingsRequest, SearchRequest


class AgentReferenceClient(AgentClientBase):
    """Agent client for reference data (country info, credit ratings, search)"""

    def get_country_data(self, request: CountryDataRequest) -> Dict[str, Any]:
        """
        Get country metadata

        Args:
            request: CountryDataRequest model

        Returns:
            Standardized response with country data
        """
        return self._execute(self._te_client.get_country_data, request)

    def get_credit_ratings(self, request: CreditRatingsRequest) -> Dict[str, Any]:
        """
        Get credit ratings

        Args:
            request: CreditRatingsRequest model

        Returns:
            Standardized response with credit ratings
        """
        return self._execute(self._te_client.get_credit_ratings, request)

    def search(self, request: SearchRequest) -> Dict[str, Any]:
        """
        Search for countries, indicators, or markets

        Args:
            request: SearchRequest model

        Returns:
            Standardized response with search results
        """
        return self._execute(self._te_client.search, request)
