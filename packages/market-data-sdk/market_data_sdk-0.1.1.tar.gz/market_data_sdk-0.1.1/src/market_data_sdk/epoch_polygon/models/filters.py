"""
Date filtering utilities for Polygon API.

Provides DateFilter class for simplified date range handling in agent tools.
Copied from EpochAI/common/polygon_utils.py
"""

from typing import Optional, Dict, Union
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field


class DateFilter(BaseModel):
    """
    Universal date filter that converts to Polygon API parameters.

    Handles conversion to Polygon's date filtering format:
    - *_gte: greater than or equal
    - *_lte: less than or equal
    - *_gt: greater than
    - *_lt: less than
    """
    start: Optional[Union[str, date, datetime]] = Field(None, description="Start date")
    end: Optional[Union[str, date, datetime]] = Field(None, description="End date")

    # Additional specific filters
    gte: Optional[Union[str, date, datetime]] = Field(None, description="Greater than or equal")
    gt: Optional[Union[str, date, datetime]] = Field(None, description="Greater than")
    lte: Optional[Union[str, date, datetime]] = Field(None, description="Less than or equal")
    lt: Optional[Union[str, date, datetime]] = Field(None, description="Less than")

    # Exact match
    exact: Optional[Union[str, date, datetime]] = Field(None, description="Exact date match")

    def to_polygon_params(self, field_name: str = "date") -> Dict[str, str]:
        """
        Convert to Polygon API date parameters.

        Args:
            field_name: Base field name (e.g., 'date', 'published_utc', 'execution_date')

        Returns:
            Dictionary with Polygon-formatted date parameters

        Example:
            >>> filter = DateFilter(start="2024-01-01", end="2024-12-31")
            >>> filter.to_polygon_params("published_utc")
            {"published_utc_gte": "2024-01-01", "published_utc_lte": "2024-12-31"}
        """
        params = {}

        def format_date(d: Union[str, date, datetime]) -> str:
            """Format date to string."""
            if isinstance(d, str):
                return d
            elif isinstance(d, datetime):
                return d.strftime("%Y-%m-%d")
            elif isinstance(d, date):
                return d.strftime("%Y-%m-%d")
            return str(d)

        # Handle start/end (most common)
        if self.start:
            params[f"{field_name}_gte"] = format_date(self.start)
        if self.end:
            params[f"{field_name}_lte"] = format_date(self.end)

        # Handle specific filters
        if self.gte:
            params[f"{field_name}_gte"] = format_date(self.gte)
        if self.gt:
            params[f"{field_name}_gt"] = format_date(self.gt)
        if self.lte:
            params[f"{field_name}_lte"] = format_date(self.lte)
        if self.lt:
            params[f"{field_name}_lt"] = format_date(self.lt)

        # Handle exact match
        if self.exact:
            params[field_name] = format_date(self.exact)

        return params

    @classmethod
    def last_n_days(cls, days: int) -> "DateFilter":
        """Create a DateFilter for the last N days."""
        end = datetime.now().date()
        start = end - timedelta(days=days)
        return cls(start=start, end=end)

    @classmethod
    def year_to_date(cls) -> "DateFilter":
        """Create a DateFilter for year-to-date."""
        end = datetime.now().date()
        start = date(end.year, 1, 1)
        return cls(start=start, end=end)

    @classmethod
    def last_year(cls) -> "DateFilter":
        """Create a DateFilter for the previous year."""
        today = datetime.now().date()
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)
        return cls(start=start, end=end)


__all__ = ["DateFilter"]