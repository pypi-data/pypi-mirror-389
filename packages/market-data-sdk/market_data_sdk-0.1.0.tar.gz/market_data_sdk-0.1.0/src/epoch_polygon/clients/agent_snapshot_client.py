"""
Agent-optimized Snapshot client for Polygon.

Handles real-time market snapshots and current price data.
"""

from typing import Dict, Any
from .base import AgentClientBase
from ..models.requests import SnapshotRequest, GetSnapshotDirectionRequest


class AgentSnapshotClient(AgentClientBase):
    """
    Agent-optimized client for Polygon snapshot endpoints.

    Wraps Polygon's SnapshotClient methods with single BaseModel parameters
    and standardized response format.
    """

    def get_snapshot_ticker(self, request: SnapshotRequest) -> Dict[str, Any]:
        """
        Get current market snapshot for an asset.

        Returns real-time price data with last trade, last quote, and previous day data.
        Useful for real-time price monitoring, trade alerts, and current market conditions.

        Args:
            request: SnapshotRequest with asset

        Returns:
            Dict with success and snapshot data (current price, last trade, last quote)

        Example:
            >>> from polygon import AgentSnapshotClient, SnapshotRequest, PolygonAsset, AssetClass
            >>> client = AgentSnapshotClient()
            >>> request = SnapshotRequest(
            ...     asset=PolygonAsset(ticker="AAPL", asset_class=AssetClass.STOCKS)
            ... )
            >>> result = client.get_snapshot_ticker(request)
            >>> print(result['data']['day'])
        """
        return self._execute(
            self._polygon_client.get_snapshot,
            request
        )

    def get_snapshot_direction(self, request: GetSnapshotDirectionRequest) -> Dict[str, Any]:
        """
        Get top gainers or losers of the day.

        Returns the top 20 stocks with the highest or lowest percentage price change
        since the previous close. Useful for finding market momentum and trading opportunities.

        Args:
            request: GetSnapshotDirectionRequest with direction ('gainers' or 'losers')

        Returns:
            Dict with success and list of top movers with price change data

        Example:
            >>> from polygon import AgentSnapshotClient, GetSnapshotDirectionRequest
            >>> client = AgentSnapshotClient()
            >>> request = GetSnapshotDirectionRequest(direction="gainers")
            >>> result = client.get_snapshot_direction(request)
            >>> for ticker in result['data']:
            ...     print(f"{ticker['ticker']}: {ticker['todaysChangePerc']:.2f}%")
        """
        return self._execute(
            self._polygon_client.get_snapshot_direction,
            request
        )


__all__ = ["AgentSnapshotClient"]
