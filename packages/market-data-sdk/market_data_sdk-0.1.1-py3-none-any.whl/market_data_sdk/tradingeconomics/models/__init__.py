"""
TradingEconomics data models
"""

# Import data models
from .data import (
    TEConfig,
    IndicatorData,
    CalendarEvent,
    MarketData,
    ForecastData,
    NewsArticle,
    CountryData,
    HistoricalData,
)

# Import request models
from .requests import (
    IndicatorsRequest,
    CalendarRequest,
    MarketsRequest,
    ForecastsRequest,
    NewsRequest,
    CountryDataRequest,
    HistoricalDataRequest,
    EarningsCalendarRequest,
    CreditRatingsRequest,
    SearchRequest,
)

__all__ = [
    # Original data models
    "TEConfig",
    "IndicatorData",
    "CalendarEvent",
    "MarketData",
    "ForecastData",
    "NewsArticle",
    "CountryData",
    "HistoricalData",
    # Request models
    "IndicatorsRequest",
    "CalendarRequest",
    "MarketsRequest",
    "ForecastsRequest",
    "NewsRequest",
    "CountryDataRequest",
    "HistoricalDataRequest",
    "EarningsCalendarRequest",
    "CreditRatingsRequest",
    "SearchRequest",
]
