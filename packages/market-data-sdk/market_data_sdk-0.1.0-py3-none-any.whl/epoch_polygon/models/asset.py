"""
Polygon Asset models for agent-optimized tools.

Provides PolygonAsset class for standardized asset representation across all asset classes.
PolygonAsset is a Polygon-specific adapter that converts from EpochAsset.
"""

from typing import Optional, Literal, TYPE_CHECKING
from pydantic import BaseModel, Field
from enum import Enum

if TYPE_CHECKING:
    from common.models.asset import EpochAsset, AssetType


class AssetClass(str, Enum):
    """Standardized asset classes for Polygon API."""
    STOCKS = "stocks"
    CRYPTO = "crypto"
    FOREX = "forex"
    OPTIONS = "options"
    INDICES = "indices"
    FUTURES = "futures"


class PolygonAsset(BaseModel):
    """
    Universal Asset representation for Polygon API.

    This class standardizes how tickers are represented and converted
    for different asset classes in the Polygon API.
    """
    ticker: str = Field(description="Base ticker symbol (e.g., AAPL, BTC, EUR)")
    asset_class: AssetClass = Field(description="Asset class for the ticker")

    # Optional fields for specific asset types
    base_currency: Optional[str] = Field(None, description="Base currency for forex/crypto (e.g., EUR in EURUSD)")
    quote_currency: Optional[str] = Field(None, description="Quote currency for forex/crypto (e.g., USD in EURUSD)")
    underlying: Optional[str] = Field(None, description="Underlying asset for options")
    expiry: Optional[str] = Field(None, description="Expiry date for futures/options")
    strike: Optional[float] = Field(None, description="Strike price for options")
    contract_type: Optional[Literal["call", "put"]] = Field(None, description="Option contract type")

    def get_polygon_ticker(self) -> str:
        """
        Convert asset to Polygon-compatible ticker format.

        Returns:
            Properly formatted ticker string for Polygon API

        Examples:
            - Stocks: "AAPL"
            - Crypto: "X:BTCUSD" or "BTC" + "USD" for separated endpoints
            - Forex: "C:EURUSD" or "EUR" + "USD" for separated endpoints
            - Options: "O:SPY250321C00400000"
            - Indices: "I:SPX"
            - Futures: "GC" or with contract month
        """
        if self.asset_class == AssetClass.STOCKS:
            return self.ticker

        elif self.asset_class == AssetClass.CRYPTO:
            if self.base_currency and self.quote_currency:
                # For endpoints that need separated currencies
                return f"{self.base_currency}{self.quote_currency}"
            # For snapshot endpoints
            return f"X:{self.ticker}" if not self.ticker.startswith("X:") else self.ticker

        elif self.asset_class == AssetClass.FOREX:
            if self.base_currency and self.quote_currency:
                # For endpoints that need separated currencies
                return f"{self.base_currency}{self.quote_currency}"
            # For snapshot endpoints
            return f"C:{self.ticker}" if not self.ticker.startswith("C:") else self.ticker

        elif self.asset_class == AssetClass.OPTIONS:
            # Options have complex formatting
            if self.underlying and self.expiry and self.strike and self.contract_type:
                # Format: O:SPY250321C00400000
                strike_str = f"{int(self.strike * 1000):08d}"
                contract_letter = "C" if self.contract_type == "call" else "P"
                return f"O:{self.underlying}{self.expiry}{contract_letter}{strike_str}"
            return f"O:{self.ticker}" if not self.ticker.startswith("O:") else self.ticker

        elif self.asset_class == AssetClass.INDICES:
            return f"I:{self.ticker}" if not self.ticker.startswith("I:") else self.ticker

        elif self.asset_class == AssetClass.FUTURES:
            # Futures can have various formats
            return self.ticker

        return self.ticker

    def get_base_and_quote(self) -> tuple[str, str]:
        """
        Get base and quote currencies for forex/crypto pairs.

        Returns:
            Tuple of (base_currency, quote_currency)
        """
        if self.base_currency and self.quote_currency:
            return (self.base_currency, self.quote_currency)

        # Try to parse from ticker
        ticker = self.ticker.replace("X:", "").replace("C:", "")

        # Handle hyphenated format first (e.g., "BTC-USD", "EUR-USD")
        if '-' in ticker:
            parts = ticker.split('-')
            if len(parts) == 2:
                return (parts[0], parts[1])

        # Common patterns for non-hyphenated tickers
        if self.asset_class == AssetClass.CRYPTO:
            # Handle common crypto pairs
            if "USD" in ticker:
                base = ticker.replace("USD", "")
                return (base, "USD")
            elif "USDT" in ticker:
                base = ticker.replace("USDT", "")
                return (base, "USDT")
            elif "BTC" in ticker and ticker != "BTC":
                base = ticker.replace("BTC", "")
                return (base, "BTC")

        elif self.asset_class == AssetClass.FOREX:
            # Handle standard forex pairs (6 characters)
            if len(ticker) == 6:
                return (ticker[:3], ticker[3:])

        # Default fallback
        return (ticker, "USD")

    @classmethod
    def from_string(cls, ticker_str: str, asset_class: Optional[AssetClass] = None) -> "PolygonAsset":
        """
        Create PolygonAsset from a ticker string.

        Args:
            ticker_str: Ticker string (may include prefix like X:, C:, I:, O:)
            asset_class: Optional asset class override

        Returns:
            PolygonAsset instance
        """
        # Detect asset class from prefix if not provided
        if not asset_class:
            if ticker_str.startswith("X:"):
                asset_class = AssetClass.CRYPTO
                ticker_str = ticker_str[2:]
            elif ticker_str.startswith("C:"):
                asset_class = AssetClass.FOREX
                ticker_str = ticker_str[2:]
            elif ticker_str.startswith("I:"):
                asset_class = AssetClass.INDICES
                ticker_str = ticker_str[2:]
            elif ticker_str.startswith("O:"):
                asset_class = AssetClass.OPTIONS
                ticker_str = ticker_str[2:]
            else:
                asset_class = AssetClass.STOCKS

        return cls(ticker=ticker_str, asset_class=asset_class)

    @classmethod
    def from_epoch_asset(cls, epoch_asset: "EpochAsset") -> "PolygonAsset":
        """
        Convert from universal EpochAsset to Polygon-specific PolygonAsset.

        This adapter method maps EpochAsset's provider-agnostic representation
        to Polygon's specific requirements.

        Args:
            epoch_asset: Universal EpochAsset instance

        Returns:
            PolygonAsset configured for Polygon API

        Examples:
            >>> from common.models.asset import EpochAsset, AssetType
            >>> epoch = EpochAsset(symbol="AAPL", asset_type=AssetType.STOCK)
            >>> polygon = PolygonAsset.from_epoch_asset(epoch)
            >>> polygon.get_polygon_ticker()
            'AAPL'

            >>> epoch = EpochAsset(symbol="BTC-USD", asset_type=AssetType.CRYPTO)
            >>> polygon = PolygonAsset.from_epoch_asset(epoch)
            >>> polygon.get_polygon_ticker()
            'X:BTC-USD'
        """
        from common.models.asset import AssetType

        # Map EpochAsset.AssetType to PolygonAsset.AssetClass
        type_mapping = {
            AssetType.STOCK: AssetClass.STOCKS,
            AssetType.CRYPTO: AssetClass.CRYPTO,
            AssetType.FOREX: AssetClass.FOREX,
            AssetType.OPTION: AssetClass.OPTIONS,
            AssetType.INDEX: AssetClass.INDICES,
            AssetType.FUTURE: AssetClass.FUTURES,
            AssetType.ETF: AssetClass.STOCKS,  # ETFs treated as stocks
            AssetType.COMMODITY: AssetClass.FUTURES,  # Commodities as futures
            AssetType.BOND: AssetClass.STOCKS,  # Bonds as stocks for now
        }

        asset_class = type_mapping.get(epoch_asset.asset_type, AssetClass.STOCKS)

        # Clean symbol (remove ^ prefix if present for indices)
        ticker = epoch_asset.symbol.lstrip('^')

        # Build PolygonAsset with appropriate fields
        kwargs = {
            "ticker": ticker,
            "asset_class": asset_class,
        }

        # NOTE: We don't set base_currency/quote_currency here
        # PolygonAsset.get_polygon_ticker() and get_base_and_quote() will
        # infer them from the ticker when needed. This allows the ticker
        # format to be preserved (e.g., "BTC-USD" stays as "BTC-USD" and
        # gets the X: or C: prefix applied correctly)

        return cls(**kwargs)


__all__ = ["AssetClass", "PolygonAsset"]