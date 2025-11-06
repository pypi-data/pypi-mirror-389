"""
Polygon.io Client Implementation
"""

import os
import sys
import importlib
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
import asyncio
import pandas as pd
from dotenv import load_dotenv

from .models import PolygonConfig, AggregateBar, Trade, Quote

# Lazy import of external polygon-api-client to avoid circular import
_RESTClient = None
_WebSocketClient = None

def _get_external_polygon_classes():
    """Lazy import of external polygon package."""
    global _RESTClient, _WebSocketClient
    if _RESTClient is None:
        # Import from installed package
        import importlib
        polygon_pkg = importlib.import_module('polygon')
        _RESTClient = polygon_pkg.RESTClient
        _WebSocketClient = polygon_pkg.WebSocketClient
    return _RESTClient, _WebSocketClient


class PolygonClient:
    """
    Unified client for accessing Polygon.io market data
    """

    def __init__(self, config: Optional[PolygonConfig] = None):
        """
        Initialize Polygon client

        Args:
            config: Optional PolygonConfig object. If not provided, will load from environment
        """
        load_dotenv()

        if config:
            self.config = config
        else:
            self.config = PolygonConfig(
                api_key=os.getenv("POLYGON_API_KEY", ""),
                use_async=False,
                timeout=30
            )

        if not self.config.api_key:
            raise ValueError("POLYGON_API_KEY is required. Set it in .env or pass via config")

        RESTClient, _ = _get_external_polygon_classes()
        self.client = RESTClient(api_key=self.config.api_key)
        self._ws_client = None

    def get_aggregates(
        self,
        ticker: str,
        multiplier: int,
        timespan: str,
        from_date: Union[str, date, datetime],
        to_date: Union[str, date, datetime],
        adjusted: bool = True,
        sort: str = "asc",
        limit: int = 5000
    ) -> pd.DataFrame:
        """
        Get aggregate bars for a ticker

        Args:
            ticker: Stock ticker symbol
            multiplier: Size of the timespan multiplier
            timespan: Unit of time (minute, hour, day, week, month, quarter, year)
            from_date: Start date
            to_date: End date
            adjusted: Whether to adjust for splits
            sort: Sort order (asc or desc)
            limit: Maximum number of results

        Returns:
            DataFrame with aggregate bar data
        """
        try:
            aggs = self.client.get_aggs(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_=from_date,
                to=to_date,
                adjusted=adjusted,
                sort=sort,
                limit=limit
            )

            data = []
            for agg in aggs:
                data.append({
                    'timestamp': agg.timestamp,
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume,
                    'vwap': getattr(agg, 'vwap', None),
                    'transactions': getattr(agg, 'transactions', None)
                })

            df = pd.DataFrame(data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            raise Exception(f"Error fetching aggregates: {str(e)}")

    def get_ticker_details(self, ticker: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a ticker

        Args:
            ticker: Stock ticker symbol
            date: Optional date for historical details

        Returns:
            Dictionary with ticker details
        """
        try:
            details = self.client.get_ticker_details(ticker, date=date)
            return {
                'ticker': details.ticker,
                'name': details.name,
                'market': details.market,
                'locale': details.locale,
                'primary_exchange': details.primary_exchange,
                'type': details.type,
                'active': details.active,
                'currency_name': details.currency_name,
                'cik': getattr(details, 'cik', None),
                'composite_figi': getattr(details, 'composite_figi', None),
                'share_class_figi': getattr(details, 'share_class_figi', None),
                'market_cap': getattr(details, 'market_cap', None),
                'description': getattr(details, 'description', None),
                'sic_code': getattr(details, 'sic_code', None),
                'sic_description': getattr(details, 'sic_description', None),
                'total_employees': getattr(details, 'total_employees', None),
                'list_date': getattr(details, 'list_date', None),
                'homepage_url': getattr(details, 'homepage_url', None),
                'branding': getattr(details, 'branding', None)
            }
        except Exception as e:
            raise Exception(f"Error fetching ticker details: {str(e)}")

    def get_snapshot(self, ticker: str, market_type: str = "stocks") -> Dict[str, Any]:
        """
        Get snapshot of a ticker's current market data

        Args:
            ticker: Ticker symbol
            market_type: Market type - "stocks", "crypto", "forex", "options" (default: "stocks")

        Returns:
            Dictionary with snapshot data
        """
        try:
            snapshot = self.client.get_snapshot_ticker(market_type, ticker)
            return {
                'ticker': snapshot.ticker.ticker,
                'day': {
                    'open': snapshot.ticker.day.open,
                    'high': snapshot.ticker.day.high,
                    'low': snapshot.ticker.day.low,
                    'close': snapshot.ticker.day.close,
                    'volume': snapshot.ticker.day.volume,
                    'vwap': snapshot.ticker.day.vwap
                } if snapshot.ticker.day else None,
                'last_quote': {
                    'bid': snapshot.ticker.last_quote.bid_price,
                    'ask': snapshot.ticker.last_quote.ask_price,
                    'bid_size': snapshot.ticker.last_quote.bid_size,
                    'ask_size': snapshot.ticker.last_quote.ask_size,
                    'timestamp': snapshot.ticker.last_quote.timeframe_timestamp
                } if snapshot.ticker.last_quote else None,
                'last_trade': {
                    'price': snapshot.ticker.last_trade.price,
                    'size': snapshot.ticker.last_trade.size,
                    'timestamp': snapshot.ticker.last_trade.participant_timestamp
                } if snapshot.ticker.last_trade else None,
                'prev_day': {
                    'open': snapshot.ticker.prev_day.open,
                    'high': snapshot.ticker.prev_day.high,
                    'low': snapshot.ticker.prev_day.low,
                    'close': snapshot.ticker.prev_day.close,
                    'volume': snapshot.ticker.prev_day.volume,
                    'vwap': snapshot.ticker.prev_day.vwap
                } if snapshot.ticker.prev_day else None
            }
        except Exception as e:
            raise Exception(f"Error fetching snapshot: {str(e)}")

    def get_trades(
        self,
        ticker: str,
        timestamp: Optional[str] = None,
        timestamp_gte: Optional[str] = None,
        timestamp_lte: Optional[str] = None,
        order: str = "asc",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get trades for a ticker

        Args:
            ticker: Stock ticker symbol
            timestamp: Exact timestamp to query
            timestamp_gte: Greater than or equal to timestamp
            timestamp_lte: Less than or equal to timestamp
            order: Sort order
            limit: Maximum number of results

        Returns:
            DataFrame with trade data
        """
        try:
            trades = self.client.list_trades(
                ticker=ticker,
                timestamp=timestamp,
                timestamp_gte=timestamp_gte,
                timestamp_lte=timestamp_lte,
                order=order,
                limit=limit
            )

            data = []
            for trade in trades:
                data.append({
                    'timestamp': trade.participant_timestamp,
                    'price': trade.price,
                    'size': trade.size,
                    'conditions': trade.conditions,
                    'exchange': trade.exchange
                })

            df = pd.DataFrame(data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ns')
                df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            raise Exception(f"Error fetching trades: {str(e)}")

    def get_quotes(
        self,
        ticker: str,
        timestamp: Optional[str] = None,
        timestamp_gte: Optional[str] = None,
        timestamp_lte: Optional[str] = None,
        order: str = "asc",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get quotes for a ticker

        Args:
            ticker: Stock ticker symbol
            timestamp: Exact timestamp to query
            timestamp_gte: Greater than or equal to timestamp
            timestamp_lte: Less than or equal to timestamp
            order: Sort order
            limit: Maximum number of results

        Returns:
            DataFrame with quote data
        """
        try:
            quotes = self.client.list_quotes(
                ticker=ticker,
                timestamp=timestamp,
                timestamp_gte=timestamp_gte,
                timestamp_lte=timestamp_lte,
                order=order,
                limit=limit
            )

            data = []
            for quote in quotes:
                data.append({
                    'timestamp': quote.participant_timestamp,
                    'bid_price': quote.bid_price,
                    'bid_size': quote.bid_size,
                    'ask_price': quote.ask_price,
                    'ask_size': quote.ask_size,
                    'bid_exchange': quote.bid_exchange,
                    'ask_exchange': quote.ask_exchange
                })

            df = pd.DataFrame(data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ns')
                df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            raise Exception(f"Error fetching quotes: {str(e)}")

    def search_tickers(
        self,
        search: str,
        active: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for tickers

        Args:
            search: Search query
            active: Whether to return only active tickers
            limit: Maximum number of results

        Returns:
            List of ticker information dictionaries
        """
        try:
            tickers = self.client.list_tickers(
                search=search,
                active=active,
                limit=limit
            )

            results = []
            for ticker in tickers:
                results.append({
                    'ticker': ticker.ticker,
                    'name': ticker.name,
                    'market': ticker.market,
                    'locale': ticker.locale,
                    'primary_exchange': ticker.primary_exchange,
                    'type': ticker.type,
                    'active': ticker.active,
                    'currency_name': ticker.currency_name,
                    'cik': getattr(ticker, 'cik', None),
                    'composite_figi': getattr(ticker, 'composite_figi', None),
                    'share_class_figi': getattr(ticker, 'share_class_figi', None),
                    'last_updated': getattr(ticker, 'last_updated_utc', None)
                })

            return results

        except Exception as e:
            raise Exception(f"Error searching tickers: {str(e)}")

    async def stream_trades(self, symbols: List[str], callback):
        """
        Stream real-time trades via WebSocket

        Args:
            symbols: List of symbols to stream
            callback: Callback function to handle messages
        """
        if not self._ws_client:
            _, WebSocketClient = _get_external_polygon_classes()
            self._ws_client = WebSocketClient(
                api_key=self.config.api_key,
                feed="delayed"  # Use 'realtime' for real-time data
            )

        try:
            await self._ws_client.connect()
            await self._ws_client.subscribe("T.*", *symbols)

            async for message in self._ws_client:
                await callback(message)

        except Exception as e:
            raise Exception(f"Error in WebSocket stream: {str(e)}")
        finally:
            if self._ws_client:
                await self._ws_client.close()

    def close(self):
        """
        Close all connections
        """
        if self._ws_client:
            asyncio.create_task(self._ws_client.close())
            self._ws_client = None