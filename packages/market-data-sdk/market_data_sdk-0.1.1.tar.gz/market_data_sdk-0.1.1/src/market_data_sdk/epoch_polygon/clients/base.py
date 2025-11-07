"""
Base agent client with singleton pattern and execution wrapper.
"""

from typing import Dict, Any
from pydantic import BaseModel
from ..client import PolygonClient

# Singleton registry for client instances
_client_instances = {}


class AgentClientBase:
    """
    Base class for all agent-optimized Polygon clients.

    Wraps the original PolygonClient and provides standardized execution
    with automatic parameter extraction from Pydantic models.
    """

    def __init__(self):
        """Initialize with wrapped PolygonClient"""
        self._polygon_client = PolygonClient()

    def _execute(self, func, request: BaseModel) -> Dict[str, Any]:
        """
        Standardized execution wrapper.

        Extracts parameters from Pydantic model, handles PolygonAsset and
        DateFilter conversion, calls underlying function, and returns
        standardized response.

        Args:
            func: Function to execute from PolygonClient
            request: Pydantic request model

        Returns:
            Standardized dict response with success, data, count
        """
        try:
            from ..models.asset import PolygonAsset
            from ..models.filters import DateFilter

            func_name = func.__name__ if hasattr(func, '__name__') else str(func)

            # Build params dict by iterating through BaseModel fields
            params = {}

            # Iterate through all fields in the request model
            for field_name in request.model_fields:
                field_value = getattr(request, field_name, None)

                # Skip None values
                if field_value is None:
                    continue

                # Handle PolygonAsset fields
                if isinstance(field_value, PolygonAsset):
                    ticker = field_value.get_polygon_ticker()

                    # Add market_type for snapshot methods
                    if 'snapshot' in func_name or 'direction' in func_name:
                        params['market_type'] = field_value.asset_class.value

                    # Handle forex/crypto pairs: split ticker into from_/to_
                    if ('forex' in func_name or 'crypto' in func_name or 'currency' in func_name) and '-' in ticker:
                        # Remove any prefixes (X:, C:) first
                        clean_ticker = ticker.split(':')[-1]
                        if '-' in clean_ticker:
                            parts = clean_ticker.split('-')
                            params['from_'] = parts[0]
                            params['to_'] = parts[1]
                        else:
                            params['ticker'] = ticker
                    else:
                        params['ticker'] = ticker

                # Handle DateFilter fields
                elif isinstance(field_value, DateFilter):
                    # Determine base field name (strip '_filter' suffix if present)
                    if field_name.endswith('_filter'):
                        base_field_name = field_name[:-7]
                    else:
                        base_field_name = field_name

                    # For timestamp-based endpoints (trades, quotes, indicators)
                    if 'timestamp' in func_name or 'trade' in func_name or 'quote' in func_name or 'indicator' in func_name:
                        # Use base_field_name if not generic, otherwise default to 'timestamp'
                        param_name = base_field_name if base_field_name not in ['date', 'date_filter'] else 'timestamp'
                        date_params = field_value.to_polygon_params(param_name)
                        params.update(date_params)
                    else:
                        # For date-based endpoints (aggregates, splits, dividends, etc.)
                        if base_field_name in ['date', 'date_filter']:
                            # Generic date_filter maps to from_date/to_date for aggregates
                            if field_value.start:
                                params['from_date'] = str(field_value.start)
                            if field_value.end:
                                params['to_date'] = str(field_value.end)
                        else:
                            # Named date filters map to {base_field_name}_gte/_lte
                            if field_value.start:
                                params[f'{base_field_name}_gte'] = str(field_value.start)
                            if field_value.end:
                                params[f'{base_field_name}_lte'] = str(field_value.end)

                # All other fields pass through unchanged
                else:
                    params[field_name] = field_value

            # Call underlying function
            result = func(**params)

            # Format response
            if hasattr(result, 'to_dict'):
                # Pandas DataFrame
                data = result.to_dict('records')
                count = len(result)
            elif hasattr(result, '__len__') and not isinstance(result, str):
                # List or similar
                data = result
                count = len(result)
            elif isinstance(result, dict):
                # Dict response
                data = result
                count = None
            else:
                # Other types
                data = result
                count = None

            return {
                "success": True,
                "data": data,
                "count": count,
                "metadata": {
                    "client": self.__class__.__name__,
                    "method": func.__name__
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "count": None,
                "metadata": {
                    "client": self.__class__.__name__,
                    "method": func.__name__ if func else "unknown"
                }
            }


def get_client_instance(client_class):
    """
    Get or create singleton client instance.

    Args:
        client_class: Agent client class to instantiate

    Returns:
        Singleton instance of the client class
    """
    class_name = client_class.__name__
    if class_name not in _client_instances:
        _client_instances[class_name] = client_class()
    return _client_instances[class_name]


__all__ = ["AgentClientBase", "get_client_instance"]