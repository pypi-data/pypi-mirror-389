"""
Agent-optimized Trades client for Polygon.

Handles trade tick data and execution history.
"""

from typing import Dict, Any
from .base import AgentClientBase
from ..models.requests import TradesRequest, GetLastTradeRequest


class AgentTradesClient(AgentClientBase):
    """
    Agent-optimized client for Polygon trades endpoints.

    Wraps Polygon's TradesClient methods with single BaseModel parameters
    and standardized response format.
    """

    def list_trades(self, request: TradesRequest) -> Dict[str, Any]:
        """
        Get historical trades for an asset.

        Returns individual trade ticks with price, size, exchange, and timestamp.
        Useful for analyzing execution quality, market microstructure, and order flow.

        Args:
            request: TradesRequest with asset, date_filter, order, and limit

        Returns:
            Dict with success, data (list of trades), and count

        Example:
            >>> from polygon import AgentTradesClient, TradesRequest, PolygonAsset, AssetClass, DateFilter
            >>> client = AgentTradesClient()
            >>> request = TradesRequest(
            ...     asset=PolygonAsset(ticker="AAPL", asset_class=AssetClass.STOCKS),
            ...     date_filter=DateFilter.last_n_days(1),
            ...     limit=100
            ... )
            >>> result = client.list_trades(request)
            >>> for trade in result['data']:
            ...     print(f"Price: {trade['price']}, Size: {trade['size']}")
        """
        return self._execute(
            self._polygon_client.get_trades,
            request
        )

    def get_last_trade(self, request: GetLastTradeRequest) -> Dict[str, Any]:
        """
        Get the most recent trade for an asset.

        Returns the latest trade tick with price, size, and timestamp.
        Useful for checking current execution price and recent trade activity.

        Args:
            request: GetLastTradeRequest with asset

        Returns:
            Dict with success and last trade data

        Example:
            >>> from polygon import AgentTradesClient, GetLastTradeRequest, PolygonAsset, AssetClass
            >>> client = AgentTradesClient()
            >>> request = GetLastTradeRequest(
            ...     asset=PolygonAsset(ticker="AAPL", asset_class=AssetClass.STOCKS)
            ... )
            >>> result = client.get_last_trade(request)
            >>> print(f"Last trade: ${result['data']['price']} x {result['data']['size']}")
        """
        return self._execute(
            self._polygon_client.get_last_trade,
            request
        )


__all__ = ["AgentTradesClient"]
