"""
LangGraph tool for TradingEconomics indicators endpoint
"""

from typing import Dict, Any, Optional, Union, List
from pydantic import Field
from langchain_core.tools import tool

from ..client import TradingEconomicsClient


@tool
def get_te_indicators(
    country: str = Field(description="Country name (e.g., 'United States', 'Germany') or 'all' for all countries"),
    indicator: Optional[str] = Field(default=None, description="Specific indicator name (e.g., 'GDP', 'Inflation Rate')"),
    start_date: Optional[str] = Field(default=None, description="Start date for historical data (YYYY-MM-DD)"),
    end_date: Optional[str] = Field(default=None, description="End date for historical data (YYYY-MM-DD)"),
) -> Dict[str, Any]:
    """
    Get economic indicators data from TradingEconomics.

    Returns economic indicators like GDP, Inflation Rate, Unemployment Rate, etc.
    for specified countries. Useful for macroeconomic analysis and research.
    """
    try:
        client = TradingEconomicsClient()
        df = client.get_indicators(
            country=country,
            indicator=indicator,
            start_date=start_date,
            end_date=end_date
        )

        result = {
            "success": True,
            "country": country,
            "indicator": indicator,
            "count": len(df),
            "data": df.to_dict('records') if not df.empty else [],
            "metadata": {
                "endpoint": "indicators",
                "date_range": f"{start_date} to {end_date}" if start_date and end_date else "latest",
                "data_type": "economic_indicators"
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