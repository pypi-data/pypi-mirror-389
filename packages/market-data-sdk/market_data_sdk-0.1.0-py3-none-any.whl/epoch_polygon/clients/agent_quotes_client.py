"""
Agent-optimized Quotes client for Polygon.

Handles NBBO quote data and bid/ask spreads.
"""

from typing import Dict, Any
from .base import AgentClientBase
from ..models.requests import QuotesRequest, GetLastQuoteRequest


class AgentQuotesClient(AgentClientBase):
    """
    Agent-optimized client for Polygon quotes endpoints.

    Wraps Polygon's QuotesClient methods with single BaseModel parameters
    and standardized response format.
    """

    def list_quotes(self, request: QuotesRequest) -> Dict[str, Any]:
        """
        Get historical NBBO quotes for an asset.

        Returns bid/ask price and size data for analyzing spread, liquidity,
        and market depth. Useful for execution analysis and market making strategies.

        Args:
            request: QuotesRequest with asset, date_filter, order, and limit

        Returns:
            Dict with success, data (list of quotes), and count

        Example:
            >>> from polygon import AgentQuotesClient, QuotesRequest, PolygonAsset, AssetClass, DateFilter
            >>> client = AgentQuotesClient()
            >>> request = QuotesRequest(
            ...     asset=PolygonAsset(ticker="AAPL", asset_class=AssetClass.STOCKS),
            ...     date_filter=DateFilter.last_n_days(1),
            ...     limit=100
            ... )
            >>> result = client.list_quotes(request)
            >>> for quote in result['data']:
            ...     spread = quote['ask_price'] - quote['bid_price']
            ...     print(f"Bid: {quote['bid_price']}, Ask: {quote['ask_price']}, Spread: {spread}")
        """
        return self._execute(
            self._polygon_client.get_quotes,
            request
        )

    def get_last_quote(self, request: GetLastQuoteRequest) -> Dict[str, Any]:
        """
        Get the most recent NBBO quote for an asset.

        Returns the latest bid/ask prices and sizes. Useful for checking
        current market spread and available liquidity.

        Args:
            request: GetLastQuoteRequest with asset

        Returns:
            Dict with success and last quote data (bid, ask, sizes)

        Example:
            >>> from polygon import AgentQuotesClient, GetLastQuoteRequest, PolygonAsset, AssetClass
            >>> client = AgentQuotesClient()
            >>> request = GetLastQuoteRequest(
            ...     asset=PolygonAsset(ticker="AAPL", asset_class=AssetClass.STOCKS)
            ... )
            >>> result = client.get_last_quote(request)
            >>> quote = result['data']
            >>> print(f"Bid: ${quote['bid_price']} x {quote['bid_size']}")
            >>> print(f"Ask: ${quote['ask_price']} x {quote['ask_size']}")
        """
        return self._execute(
            self._polygon_client.get_last_quote,
            request
        )


__all__ = ["AgentQuotesClient"]
