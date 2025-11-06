"""
Agent client for TradingEconomics calendar events
"""

from typing import Dict, Any
from .base import AgentClientBase
from ..models.requests import CalendarRequest, EarningsCalendarRequest


class AgentCalendarClient(AgentClientBase):
    """Agent client for economic calendar and earnings events"""

    def get_calendar_events(self, request: CalendarRequest) -> Dict[str, Any]:
        """
        Get economic calendar events

        Args:
            request: CalendarRequest model

        Returns:
            Standardized response with calendar events
        """
        return self._execute(self._te_client.get_calendar_events, request)

    def get_earnings_calendar(self, request: EarningsCalendarRequest) -> Dict[str, Any]:
        """
        Get earnings calendar

        Args:
            request: EarningsCalendarRequest model

        Returns:
            Standardized response with earnings calendar
        """
        return self._execute(self._te_client.get_earnings_calendar, request)
