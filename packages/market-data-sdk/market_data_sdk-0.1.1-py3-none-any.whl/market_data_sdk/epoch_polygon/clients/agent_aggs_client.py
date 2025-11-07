"""
Agent-optimized Aggregates client for Polygon.

Handles OHLCV aggregate bars and historical price data.
"""

from typing import Dict, Any
from .base import AgentClientBase
from ..models.requests import AggregatesRequest, GetPreviousCloseRequest


class AgentAggsClient(AgentClientBase):
    """
    Agent-optimized client for Polygon aggregates endpoints.

    Wraps Polygon's AggsClient methods with single BaseModel parameters
    and standardized response format.
    """

    def get_aggs(self, request: AggregatesRequest) -> Dict[str, Any]:
        """
        Get aggregate OHLCV bars for an asset.

        Returns historical price data for charting, technical analysis, and backtesting.
        Supports multiple timeframes (minute, hour, day, week, month).

        Args:
            request: AggregatesRequest with asset, date_filter, timespan, etc.

        Returns:
            Dict with success, data (list of OHLCV records), and count

        Example:
            >>> from polygon import AgentAggsClient, AggregatesRequest, PolygonAsset, AssetClass, DateFilter
            >>> client = AgentAggsClient()
            >>> request = AggregatesRequest(
            ...     asset=PolygonAsset(ticker="AAPL", asset_class=AssetClass.STOCKS),
            ...     date_filter=DateFilter.last_n_days(30),
            ...     timespan="day"
            ... )
            >>> result = client.get_aggs(request)
            >>> print(result['success'], result['count'])
        """
        return self._execute(
            self._polygon_client.get_aggregates,
            request
        )

    def get_previous_close_agg(self, request: GetPreviousCloseRequest) -> Dict[str, Any]:
        """
        Get the previous day's OHLC for an asset.

        Useful for calculating daily returns, percentage changes, and
        comparing current price to previous close.

        Args:
            request: GetPreviousCloseRequest with asset and adjusted flag

        Returns:
            Dict with success and previous close data

        Example:
            >>> from polygon import AgentAggsClient, GetPreviousCloseRequest, PolygonAsset, AssetClass
            >>> client = AgentAggsClient()
            >>> request = GetPreviousCloseRequest(
            ...     asset=PolygonAsset(ticker="AAPL", asset_class=AssetClass.STOCKS),
            ...     adjusted=True
            ... )
            >>> result = client.get_previous_close_agg(request)
            >>> print(result['data'])
        """
        return self._execute(
            self._polygon_client.get_previous_close_agg,
            request
        )


__all__ = ["AgentAggsClient"]
