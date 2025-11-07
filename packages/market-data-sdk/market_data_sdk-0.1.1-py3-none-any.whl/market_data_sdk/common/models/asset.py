"""
Universal asset representation for Epoch ecosystem.

EpochAsset provides a provider-agnostic way to represent financial instruments.
Each data provider (Polygon, TradingEconomics) can convert from EpochAsset to
their specific format.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AssetType(str, Enum):
    """
    Universal asset type classification.

    Maps to specific provider asset classes during conversion.
    """
    STOCK = "stock"
    OPTION = "option"
    CRYPTO = "crypto"
    FOREX = "forex"
    FUTURE = "future"
    INDEX = "index"
    COMMODITY = "commodity"
    BOND = "bond"
    ETF = "etf"


class EpochAsset(BaseModel):
    """
    Universal asset representation for Epoch ecosystem.

    Provides clear, agent-friendly symbol conventions:
    - Stocks: "AAPL", "TSLA", "MSFT"
    - Crypto: "BTC-USD", "ETH-USD", "BTC" (defaults to USD)
    - Forex: "EUR-USD", "GBP-JPY"
    - Futures: "ES", "NQ", "CL"
    - Options: "AAPL250117C00150000"
    - Indices: "SPX", "NDX"

    Examples:
        >>> asset = EpochAsset(symbol="AAPL", asset_type=AssetType.STOCK)
        >>> asset.to_epoch_asset_id()
        'AAPL-Stock'

        >>> asset = EpochAsset(symbol="BTC-USD", asset_type=AssetType.CRYPTO)
        >>> asset.to_epoch_asset_id()
        '^BTCUSD-Crypto'

        >>> asset = EpochAsset(symbol="EUR-USD", asset_type=AssetType.FOREX)
        >>> asset.to_epoch_asset_id()
        '^EURUSD-Forex'
    """

    symbol: str = Field(
        description="Universal symbol (AAPL, BTC-USD, EUR-USD, ES, etc.)"
    )
    asset_type: AssetType = Field(
        description="Asset type classification"
    )

    # Optional metadata
    base_currency: Optional[str] = Field(
        default=None,
        description="Base currency for pairs (BTC in BTC-USD)"
    )
    quote_currency: Optional[str] = Field(
        default=None,
        description="Quote currency for pairs (USD in BTC-USD)"
    )
    exchange: Optional[str] = Field(
        default=None,
        description="Primary exchange (NASDAQ, NYSE, BINANCE, etc.)"
    )

    def model_post_init(self, __context) -> None:
        """
        Auto-populate currency fields for pairs.

        If symbol contains '-' and currencies not set, parse them.
        """
        if self.base_currency is None and self.quote_currency is None:
            if '-' in self.symbol:
                parts = self.symbol.split('-')
                if len(parts) == 2:
                    self.base_currency = parts[0]
                    self.quote_currency = parts[1]
            elif self.asset_type == AssetType.CRYPTO and self.base_currency is None:
                # Default crypto to USD if no pair specified
                self.base_currency = self.symbol
                self.quote_currency = "USD"

    def to_epoch_asset_id(self) -> str:
        """
        Convert to Epoch ecosystem asset ID format.

        Format conventions:
        - Stocks: "AAPL-Stock"
        - Crypto pairs: "^BTCUSD-Crypto"
        - Forex pairs: "^EURUSD-Forex"
        - Futures: "ES-Future"
        - Indices: "^SPX-Index"
        - Options: "AAPL250117C00150000-Option"

        Returns:
            Standardized asset ID for Epoch ecosystem
        """
        # Handle pairs (crypto, forex)
        if self.asset_type in [AssetType.CRYPTO, AssetType.FOREX]:
            if self.base_currency and self.quote_currency:
                pair = f"{self.base_currency}{self.quote_currency}"
                return f"^{pair}-{self.asset_type.value.capitalize()}"

        # Handle indices (prefix with ^)
        if self.asset_type == AssetType.INDEX:
            symbol = self.symbol if self.symbol.startswith('^') else f"^{self.symbol}"
            return f"{symbol}-Index"

        # Default format: SYMBOL-Type
        return f"{self.symbol}-{self.asset_type.value.capitalize()}"

    def get_pair_symbols(self) -> Optional[tuple[str, str]]:
        """
        Get base and quote currency symbols for pairs.

        Returns:
            (base, quote) tuple or None if not a pair
        """
        if self.base_currency and self.quote_currency:
            return (self.base_currency, self.quote_currency)
        return None

    @classmethod
    def from_symbol(
        cls,
        symbol: str,
        asset_type: Optional[AssetType] = None,
        **kwargs
    ) -> "EpochAsset":
        """
        Create EpochAsset from symbol with smart type inference.

        Args:
            symbol: Symbol string (AAPL, BTC-USD, EUR-USD, etc.)
            asset_type: Explicit type (if None, inferred from symbol)
            **kwargs: Additional fields

        Returns:
            EpochAsset instance

        Examples:
            >>> EpochAsset.from_symbol("AAPL", AssetType.STOCK)
            >>> EpochAsset.from_symbol("BTC-USD")  # Infers crypto
            >>> EpochAsset.from_symbol("EUR-USD")  # Infers forex
        """
        # Infer type if not provided
        if asset_type is None:
            asset_type = cls._infer_type(symbol)

        return cls(symbol=symbol, asset_type=asset_type, **kwargs)

    @staticmethod
    def _infer_type(symbol: str) -> AssetType:
        """
        Infer asset type from symbol patterns.

        Args:
            symbol: Symbol string

        Returns:
            Inferred AssetType
        """
        # Crypto patterns
        crypto_bases = ['BTC', 'ETH', 'SOL', 'USDT', 'USDC', 'BNB', 'XRP', 'ADA', 'DOGE']
        if any(symbol.startswith(base) for base in crypto_bases):
            return AssetType.CRYPTO

        # Forex patterns (3-letter currency codes)
        forex_currencies = ['EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD']
        if any(symbol.startswith(curr) for curr in forex_currencies):
            return AssetType.FOREX

        # Futures patterns (2-letter codes)
        if len(symbol) == 2 and symbol.isupper():
            return AssetType.FUTURE

        # Index patterns
        if symbol.startswith('^') or symbol in ['SPX', 'NDX', 'RUT', 'VIX']:
            return AssetType.INDEX

        # Options patterns (long alphanumeric)
        if len(symbol) > 15 and any(c.isdigit() for c in symbol):
            return AssetType.OPTION

        # Default to stock
        return AssetType.STOCK


__all__ = ["EpochAsset", "AssetType"]
