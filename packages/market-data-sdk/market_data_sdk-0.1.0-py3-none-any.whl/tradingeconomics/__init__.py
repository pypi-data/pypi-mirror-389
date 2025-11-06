"""
TradingEconomics SDK Module
Provides a unified client interface for accessing TradingEconomics data
"""

from .client import TradingEconomicsClient
from .models import (
    TEConfig,
    IndicatorData,
    CalendarEvent,
    MarketData,
    ForecastData,
    NewsArticle,
    CountryData,
    HistoricalData,
)

__all__ = [
    "TradingEconomicsClient",
    "TEConfig",
    "IndicatorData",
    "CalendarEvent",
    "MarketData",
    "ForecastData",
    "NewsArticle",
    "CountryData",
    "HistoricalData",
]

__version__ = "0.1.0"