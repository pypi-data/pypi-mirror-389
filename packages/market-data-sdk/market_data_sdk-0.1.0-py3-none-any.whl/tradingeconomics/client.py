"""
TradingEconomics Client Implementation
"""

import os
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
import pandas as pd
import requests
from dotenv import load_dotenv
import tradingeconomics as te

from .models import (
    TEConfig,
    IndicatorData,
    CalendarEvent,
    MarketData,
    ForecastData,
    NewsArticle,
    CountryData,
    HistoricalData
)


class TradingEconomicsClient:
    """
    Unified client for accessing TradingEconomics data
    """

    def __init__(self, config: Optional[TEConfig] = None):
        """
        Initialize TradingEconomics client

        Args:
            config: Optional TEConfig object. If not provided, will load from environment
        """
        load_dotenv()

        if config:
            self.config = config
        else:
            self.config = TEConfig(
                api_key=os.getenv("TRADINGECONOMICS_API_KEY", ""),
                timeout=30
            )

        if not self.config.api_key:
            raise ValueError("TRADINGECONOMICS_API_KEY is required. Set it in .env or pass via config")

        # Set the API key for the TradingEconomics library
        te.login(self.config.api_key)
        self.base_url = "https://api.tradingeconomics.com"

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make HTTP request to TradingEconomics API

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response data
        """
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {}
        params['c'] = self.config.api_key

        try:
            response = requests.get(url, params=params, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")

    def get_indicators(
        self,
        country: Union[str, List[str]],
        indicator: Optional[Union[str, List[str]]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get economic indicators data

        Args:
            country: Country name(s) or 'all'
            indicator: Indicator name(s) (e.g., 'GDP', 'Inflation Rate')
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            DataFrame with indicator data
        """
        try:
            if indicator:
                data = te.getIndicatorData(country=country, indicators=indicator, output_type='df')
            else:
                data = te.getIndicatorData(country=country, output_type='df')

            if start_date and end_date:
                data = te.getHistoricalData(
                    country=country,
                    indicator=indicator,
                    initDate=start_date,
                    endDate=end_date,
                    output_type='df'
                )

            return data

        except Exception as e:
            raise Exception(f"Error fetching indicators: {str(e)}")

    def get_calendar_events(
        self,
        country: Optional[Union[str, List[str]]] = None,
        indicator: Optional[Union[str, List[str]]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        importance: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get economic calendar events

        Args:
            country: Country name(s) or None for all
            indicator: Indicator name(s) or None for all
            start_date: Start date
            end_date: End date
            importance: Importance level (1-3)

        Returns:
            DataFrame with calendar events
        """
        try:
            params = {}
            if country:
                data = te.getCalendarData(country=country, output_type='df')
            elif indicator:
                data = te.getCalendarData(indicator=indicator, output_type='df')
            elif start_date and end_date:
                data = te.getCalendarData(
                    initDate=start_date,
                    endDate=end_date,
                    output_type='df'
                )
            else:
                data = te.getCalendarData(output_type='df')

            if importance and 'Importance' in data.columns:
                data = data[data['Importance'] >= importance]

            return data

        except Exception as e:
            raise Exception(f"Error fetching calendar events: {str(e)}")

    def get_markets(
        self,
        market_type: str = "index",
        country: Optional[Union[str, List[str]]] = None
    ) -> pd.DataFrame:
        """
        Get market data (indices, currencies, commodities, bonds, crypto)

        Args:
            market_type: Type of market ('index', 'currency', 'commodity', 'bond', 'crypto')
            country: Country filter (optional)

        Returns:
            DataFrame with market data
        """
        try:
            if market_type == "index":
                data = te.getMarketsData(marketsField='index', output_type='df')
            elif market_type == "currency":
                data = te.getMarketsData(marketsField='currency', output_type='df')
            elif market_type == "commodity":
                data = te.getMarketsData(marketsField='commodity', output_type='df')
            elif market_type == "bond":
                data = te.getMarketsData(marketsField='bond', output_type='df')
            elif market_type == "crypto":
                data = te.getMarketsData(marketsField='crypto', output_type='df')
            else:
                raise ValueError(f"Invalid market_type: {market_type}")

            if country and 'Country' in data.columns:
                if isinstance(country, list):
                    data = data[data['Country'].isin(country)]
                else:
                    data = data[data['Country'] == country]

            return data

        except Exception as e:
            raise Exception(f"Error fetching market data: {str(e)}")

    def get_forecasts(
        self,
        country: Union[str, List[str]],
        indicator: Optional[Union[str, List[str]]] = None
    ) -> pd.DataFrame:
        """
        Get economic forecasts

        Args:
            country: Country name(s)
            indicator: Indicator name(s) (optional)

        Returns:
            DataFrame with forecast data
        """
        try:
            if indicator:
                data = te.getForecastData(
                    country=country,
                    indicator=indicator,
                    output_type='df'
                )
            else:
                data = te.getForecastData(country=country, output_type='df')

            return data

        except Exception as e:
            raise Exception(f"Error fetching forecasts: {str(e)}")

    def get_news(
        self,
        country: Optional[Union[str, List[str]]] = None,
        indicator: Optional[Union[str, List[str]]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get economic news

        Args:
            country: Country filter
            indicator: Indicator filter
            start_date: Start date
            end_date: End date
            limit: Maximum number of articles

        Returns:
            DataFrame with news articles
        """
        try:
            if country:
                data = te.getNews(country=country, output_type='df')
            elif indicator:
                data = te.getNews(indicator=indicator, output_type='df')
            elif start_date and end_date:
                data = te.getNews(
                    start_date=start_date,
                    end_date=end_date,
                    output_type='df'
                )
            else:
                data = te.getNews(output_type='df')

            if limit and len(data) > limit:
                data = data.head(limit)

            return data

        except Exception as e:
            raise Exception(f"Error fetching news: {str(e)}")

    def get_country_data(
        self,
        country: Union[str, List[str]]
    ) -> pd.DataFrame:
        """
        Get country metadata and basic information

        Args:
            country: Country name(s)

        Returns:
            DataFrame with country information
        """
        try:
            endpoint = f"/country/{country}"
            data = self._make_request(endpoint)
            return pd.DataFrame(data)

        except Exception as e:
            raise Exception(f"Error fetching country data: {str(e)}")

    def get_historical_data(
        self,
        country: str,
        indicator: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Get historical data for specific indicator

        Args:
            country: Country name
            indicator: Indicator name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with historical data
        """
        try:
            data = te.getHistoricalData(
                country=country,
                indicator=indicator,
                initDate=start_date,
                endDate=end_date,
                output_type='df'
            )
            return data

        except Exception as e:
            raise Exception(f"Error fetching historical data: {str(e)}")

    def get_earnings_calendar(
        self,
        country: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get earnings calendar

        Args:
            country: Country filter
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with earnings calendar
        """
        try:
            data = te.getEarnings(output_type='df')

            if country and 'Country' in data.columns:
                data = data[data['Country'] == country]

            if start_date and 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
                data = data[data['Date'] >= start_date]

            if end_date and 'Date' in data.columns:
                data = data[data['Date'] <= end_date]

            return data

        except Exception as e:
            raise Exception(f"Error fetching earnings calendar: {str(e)}")

    def get_credit_ratings(
        self,
        country: Optional[Union[str, List[str]]] = None
    ) -> pd.DataFrame:
        """
        Get credit ratings

        Args:
            country: Country filter

        Returns:
            DataFrame with credit ratings
        """
        try:
            data = te.getRatings(output_type='df')

            if country:
                if isinstance(country, list):
                    data = data[data['Country'].isin(country)]
                else:
                    data = data[data['Country'] == country]

            return data

        except Exception as e:
            raise Exception(f"Error fetching credit ratings: {str(e)}")

    def search(
        self,
        term: str,
        category: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Search for countries, indicators, or markets

        Args:
            term: Search term
            category: Category filter ('country', 'indicator', 'market')

        Returns:
            DataFrame with search results
        """
        try:
            results = te.getSearch(term=term, output_type='df')

            if category and 'Category' in results.columns:
                results = results[results['Category'] == category]

            return results

        except Exception as e:
            raise Exception(f"Error in search: {str(e)}")