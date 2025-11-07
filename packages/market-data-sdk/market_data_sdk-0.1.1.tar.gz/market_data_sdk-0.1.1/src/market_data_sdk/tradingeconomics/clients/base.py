"""
Base agent client with singleton pattern and execution wrapper.
"""

from typing import Dict, Any
from pydantic import BaseModel
from ..client import TradingEconomicsClient

# Singleton registry for client instances
_client_instances = {}


class AgentClientBase:
    """
    Base class for all agent-optimized TradingEconomics clients.

    Wraps the original TradingEconomicsClient and provides standardized execution
    with automatic parameter extraction from Pydantic models.
    """

    def __init__(self):
        """Initialize with wrapped TradingEconomicsClient"""
        self._te_client = TradingEconomicsClient()

    def _execute(self, func, request: BaseModel) -> Dict[str, Any]:
        """
        Standardized execution wrapper.

        Extracts parameters from Pydantic model, calls underlying function,
        and returns standardized response.

        Args:
            func: Function to execute from TradingEconomicsClient
            request: Pydantic request model

        Returns:
            Standardized dict response with success, data, count
        """
        try:
            # Build params dict by iterating through BaseModel fields
            params = {}

            # Iterate through all fields in the request model
            for field_name in request.model_fields:
                field_value = getattr(request, field_name, None)

                # Skip None values
                if field_value is None:
                    continue

                # All fields pass through unchanged
                params[field_name] = field_value

            # Call underlying function
            result = func(**params)

            # Format response - TradingEconomics returns DataFrames
            if hasattr(result, 'to_dict'):
                # Pandas DataFrame - convert to list of dicts
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
                    "method": getattr(func, '__name__', 'unknown')
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
                    "method": getattr(func, '__name__', 'unknown')
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
