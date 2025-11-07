"""
Polygon models for agent-optimized tools
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Base data models (from old models.py)
class PolygonConfig(BaseModel):
    """Configuration for Polygon client"""
    api_key: str = Field(..., description="Polygon.io API key")
    use_async: bool = Field(default=False, description="Use async client")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")


class AggregateBar(BaseModel):
    """Aggregate bar data model"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None
    transactions: Optional[int] = None


class Trade(BaseModel):
    """Trade data model"""
    timestamp: datetime
    price: float
    size: int
    conditions: Optional[List[int]] = None
    exchange: Optional[int] = None


class Quote(BaseModel):
    """Quote data model"""
    timestamp: datetime
    bid_price: float
    bid_size: int
    ask_price: float
    ask_size: int
    bid_exchange: Optional[int] = None
    ask_exchange: Optional[int] = None


class StockData(BaseModel):
    """Stock data container"""
    ticker: str
    aggregates: Optional[List[AggregateBar]] = None
    trades: Optional[List[Trade]] = None
    quotes: Optional[List[Quote]] = None
    details: Optional[Dict[str, Any]] = None
    snapshot: Optional[Dict[str, Any]] = None


class OptionsData(BaseModel):
    """Options data container"""
    underlying: str
    contract_type: str
    strike_price: float
    expiration_date: datetime
    aggregates: Optional[List[AggregateBar]] = None
    trades: Optional[List[Trade]] = None
    quotes: Optional[List[Quote]] = None
    details: Optional[Dict[str, Any]] = None


class ForexData(BaseModel):
    """Forex data container"""
    from_currency: str
    to_currency: str
    aggregates: Optional[List[AggregateBar]] = None
    quotes: Optional[List[Quote]] = None
    snapshot: Optional[Dict[str, Any]] = None


class CryptoData(BaseModel):
    """Crypto data container"""
    from_currency: str
    to_currency: str
    aggregates: Optional[List[AggregateBar]] = None
    trades: Optional[List[Trade]] = None
    snapshot: Optional[Dict[str, Any]] = None

# Agent models
from .asset import AssetClass, PolygonAsset
from .filters import DateFilter
from .requests import (
    AggregatesRequest,
    SnapshotRequest,
    DetailsRequest,
    TradesRequest,
    QuotesRequest,
    SearchRequest,
)

__all__ = [
    # Configuration and base models
    "PolygonConfig",
    "AggregateBar",
    "Trade",
    "Quote",
    "StockData",
    "OptionsData",
    "ForexData",
    "CryptoData",

    # Asset models
    "AssetClass",
    "PolygonAsset",

    # Filters
    "DateFilter",

    # Request models
    "AggregatesRequest",
    "SnapshotRequest",
    "DetailsRequest",
    "TradesRequest",
    "QuotesRequest",
    "SearchRequest",
]