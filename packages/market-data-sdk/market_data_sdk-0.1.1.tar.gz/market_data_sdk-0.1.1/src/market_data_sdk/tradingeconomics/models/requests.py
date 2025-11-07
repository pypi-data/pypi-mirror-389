"""
Request models for TradingEconomics agent clients
"""

from typing import Optional, List, Union
from pydantic import BaseModel, Field


class IndicatorsRequest(BaseModel):
    """Request model for getting economic indicators"""
    country: Union[str, List[str]] = Field(..., description="Country name(s) or 'all'")
    indicator: Optional[Union[str, List[str]]] = Field(None, description="Indicator name(s) like 'GDP', 'Inflation Rate'")
    start_date: Optional[str] = Field(None, description="Start date for historical data (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for historical data (YYYY-MM-DD)")


class CalendarRequest(BaseModel):
    """Request model for getting economic calendar events"""
    country: Optional[Union[str, List[str]]] = Field(None, description="Country name(s) or None for all")
    indicator: Optional[Union[str, List[str]]] = Field(None, description="Indicator name(s) or None for all")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    importance: Optional[int] = Field(None, description="Importance level (1-3)", ge=1, le=3)


class MarketsRequest(BaseModel):
    """Request model for getting market data"""
    market_type: str = Field(default="index", description="Type of market: 'index', 'currency', 'commodity', 'bond', or 'crypto'")
    country: Optional[Union[str, List[str]]] = Field(None, description="Country filter (optional)")


class ForecastsRequest(BaseModel):
    """Request model for getting economic forecasts"""
    country: Union[str, List[str]] = Field(..., description="Country name(s)")
    indicator: Optional[Union[str, List[str]]] = Field(None, description="Indicator name(s) (optional)")


class NewsRequest(BaseModel):
    """Request model for getting economic news"""
    country: Optional[Union[str, List[str]]] = Field(None, description="Country filter")
    indicator: Optional[Union[str, List[str]]] = Field(None, description="Indicator filter")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    limit: int = Field(default=100, description="Maximum number of articles", gt=0)


class CountryDataRequest(BaseModel):
    """Request model for getting country metadata"""
    country: Union[str, List[str]] = Field(..., description="Country name(s)")


class HistoricalDataRequest(BaseModel):
    """Request model for getting historical indicator data"""
    country: str = Field(..., description="Country name")
    indicator: str = Field(..., description="Indicator name")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")


class EarningsCalendarRequest(BaseModel):
    """Request model for getting earnings calendar"""
    country: Optional[str] = Field(None, description="Country filter")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class CreditRatingsRequest(BaseModel):
    """Request model for getting credit ratings"""
    country: Optional[Union[str, List[str]]] = Field(None, description="Country filter")


class SearchRequest(BaseModel):
    """Request model for searching countries, indicators, or markets"""
    term: str = Field(..., description="Search term")
    category: Optional[str] = Field(None, description="Category filter: 'country', 'indicator', or 'market'")
