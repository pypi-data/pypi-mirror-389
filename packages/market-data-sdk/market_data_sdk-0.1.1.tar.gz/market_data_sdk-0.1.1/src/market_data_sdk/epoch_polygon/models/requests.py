"""
Request models for Polygon agent clients.

Each request model corresponds to a single endpoint and contains all parameters
as a single BaseModel for agent-friendly interaction.
"""

from typing import Optional
from pydantic import BaseModel, Field
from .asset import PolygonAsset
from .filters import DateFilter


class AggregatesRequest(BaseModel):
    """Request model for get_aggregates endpoint"""
    asset: PolygonAsset = Field(description="Asset to query (ticker + asset_class)")
    date_filter: DateFilter = Field(description="Date range for aggregates")
    timespan: str = Field(
        default="day",
        description="Timespan unit: 'minute', 'hour', 'day', 'week', 'month', 'quarter', 'year'"
    )
    multiplier: int = Field(default=1, description="Size of timespan multiplier")
    adjusted: bool = Field(default=True, description="Adjust for splits")
    sort: str = Field(default="asc", description="Sort order: 'asc' or 'desc'")
    limit: int = Field(default=5000, ge=1, le=50000, description="Maximum results")


class SnapshotRequest(BaseModel):
    """Request model for get_snapshot endpoint"""
    asset: PolygonAsset = Field(description="Asset to query (ticker + asset_class)")


class DetailsRequest(BaseModel):
    """Request model for get_ticker_details endpoint"""
    ticker: str = Field(description="Stock ticker symbol (e.g., 'AAPL')")
    date: Optional[str] = Field(default=None, description="Date for historical details (YYYY-MM-DD)")


class TradesRequest(BaseModel):
    """Request model for get_trades endpoint"""
    asset: PolygonAsset = Field(description="Asset to query (ticker + asset_class)")
    date_filter: DateFilter = Field(description="Date/time filter for trades")
    order: str = Field(default="asc", description="Sort order: 'asc' or 'desc'")
    limit: int = Field(default=100, ge=1, le=5000, description="Maximum results")


class QuotesRequest(BaseModel):
    """Request model for get_quotes endpoint"""
    asset: PolygonAsset = Field(description="Asset to query (ticker + asset_class)")
    date_filter: DateFilter = Field(description="Date/time filter for quotes")
    order: str = Field(default="asc", description="Sort order: 'asc' or 'desc'")
    limit: int = Field(default=100, ge=1, le=5000, description="Maximum results")


class SearchRequest(BaseModel):
    """Request model for search_tickers endpoint"""
    search: str = Field(description="Search query for ticker symbols or company names")
    active: bool = Field(default=True, description="Whether to return only active tickers")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")


# New request models for refactored agent clients

class GetPreviousCloseRequest(BaseModel):
    """Request model for get_previous_close_agg endpoint"""
    asset: PolygonAsset = Field(description="Asset to query (ticker + asset_class)")
    adjusted: bool = Field(default=True, description="Adjust for splits")


class GetSnapshotDirectionRequest(BaseModel):
    """Request model for get_snapshot_direction endpoint (top gainers/losers)"""
    direction: str = Field(
        description="Direction to query: 'gainers' for top gainers, 'losers' for top losers"
    )
    include_otc: bool = Field(
        default=False,
        description="Include OTC securities in results"
    )


class GetLastTradeRequest(BaseModel):
    """Request model for get_last_trade endpoint"""
    asset: PolygonAsset = Field(description="Asset to query (ticker + asset_class)")


class GetLastQuoteRequest(BaseModel):
    """Request model for get_last_quote endpoint"""
    asset: PolygonAsset = Field(description="Asset to query (ticker + asset_class)")


__all__ = [
    "AggregatesRequest",
    "SnapshotRequest",
    "DetailsRequest",
    "TradesRequest",
    "QuotesRequest",
    "SearchRequest",
    "GetPreviousCloseRequest",
    "GetSnapshotDirectionRequest",
    "GetLastTradeRequest",
    "GetLastQuoteRequest",
]