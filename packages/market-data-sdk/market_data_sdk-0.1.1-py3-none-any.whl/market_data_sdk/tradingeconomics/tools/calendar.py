"""
LangGraph tool for TradingEconomics calendar endpoint
"""

from typing import Dict, Any, Optional, Union, List
from pydantic import Field
from langchain_core.tools import tool

from ..client import TradingEconomicsClient


@tool
def get_te_calendar(
    country: Optional[str] = Field(default=None, description="Country name (e.g., 'United States') or None for all"),
    indicator: Optional[str] = Field(default=None, description="Specific indicator name (e.g., 'GDP', 'CPI') or None for all"),
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)"),
    importance: Optional[int] = Field(default=None, description="Importance level filter (1-3, where 3 is highest)"),
) -> Dict[str, Any]:
    """
    Get economic calendar events from TradingEconomics.

    Returns upcoming and past economic events, releases, and announcements.
    Useful for tracking important economic events that may impact markets.
    """
    try:
        client = TradingEconomicsClient()
        df = client.get_calendar_events(
            country=country,
            indicator=indicator,
            start_date=start_date,
            end_date=end_date,
            importance=importance
        )

        result = {
            "success": True,
            "country": country,
            "indicator": indicator,
            "count": len(df),
            "data": df.to_dict('records') if not df.empty else [],
            "metadata": {
                "endpoint": "calendar",
                "date_range": f"{start_date} to {end_date}" if start_date and end_date else "default_range",
                "importance_filter": importance,
                "data_type": "economic_calendar"
            }
        }

        return result

    except Exception as e:
        return {
            "success": False,
            "country": country,
            "indicator": indicator,
            "error": str(e),
            "data": []
        }