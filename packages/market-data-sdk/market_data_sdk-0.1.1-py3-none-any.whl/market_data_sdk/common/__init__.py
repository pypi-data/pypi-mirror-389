"""
Common models and utilities shared across all data providers.

This package provides unified abstractions (like EpochAsset) that work
across Polygon, TradingEconomics, and other data sources.
"""

from .models.asset import EpochAsset, AssetType

__all__ = [
    "EpochAsset",
    "AssetType",
]

__version__ = "0.1.0"
