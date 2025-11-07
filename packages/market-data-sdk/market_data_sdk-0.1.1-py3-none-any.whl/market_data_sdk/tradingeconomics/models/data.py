"""
Data models for TradingEconomics SDK
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TEConfig(BaseModel):
    """Configuration for TradingEconomics client"""
    api_key: str = Field(..., description="TradingEconomics API key")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")


class IndicatorData(BaseModel):
    """Economic indicator data model"""
    country: str
    category: str
    title: str
    latest_value: float
    latest_value_date: datetime
    source: Optional[str] = None
    unit: Optional[str] = None
    frequency: Optional[str] = None
    previous_value: Optional[float] = None
    previous_value_date: Optional[datetime] = None


class CalendarEvent(BaseModel):
    """Economic calendar event model"""
    date: datetime
    country: str
    category: str
    event: str
    reference: Optional[str] = None
    source: Optional[str] = None
    actual: Optional[float] = None
    previous: Optional[float] = None
    forecast: Optional[float] = None
    importance: Optional[int] = None


class MarketData(BaseModel):
    """Market data model"""
    symbol: str
    name: str
    country: str
    date: datetime
    last: float
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percentage: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None
    market_cap: Optional[float] = None


class ForecastData(BaseModel):
    """Forecast data model"""
    country: str
    category: str
    title: str
    forecast_date: datetime
    forecast_value: float
    forecast_value_previous: Optional[float] = None
    q1: Optional[float] = None
    q2: Optional[float] = None
    q3: Optional[float] = None
    q4: Optional[float] = None
    yearly: Optional[float] = None


class NewsArticle(BaseModel):
    """News article model"""
    id: str
    title: str
    date: datetime
    description: str
    country: Optional[str] = None
    category: Optional[str] = None
    symbol: Optional[str] = None
    url: Optional[str] = None
    importance: Optional[int] = None


class CountryData(BaseModel):
    """Country information model"""
    country: str
    iso2: str
    iso3: str
    currency: str
    currency_code: str
    currency_symbol: Optional[str] = None
    capital: Optional[str] = None
    continent: Optional[str] = None
    population: Optional[int] = None
    gdp: Optional[float] = None
    gdp_per_capita: Optional[float] = None


class HistoricalData(BaseModel):
    """Historical data model"""
    country: str
    category: str
    datetime: datetime
    value: float
    frequency: Optional[str] = None
    history_date: Optional[datetime] = None
    source: Optional[str] = None
    unit: Optional[str] = None