"""
Dynamic tool generation for TradingEconomics agent clients.

Loads tool specifications from tool_specs.json and creates LangGraph tools
using StructuredTool.from_function() for programmatic tool creation.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.tools import StructuredTool

from ..clients.base import get_client_instance


# Load tool specs from JSON file
SPEC_FILE = Path(__file__).parent.parent / "tool_specs.json"
with open(SPEC_FILE) as f:
    TOOL_SPECS = json.load(f)


def _import_class(module_path: str, class_name: str):
    """
    Dynamically import a class from a module path.

    Args:
        module_path: Module path (e.g., "tradingeconomics.clients")
        class_name: Class name to import

    Returns:
        The imported class
    """
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def create_tool_from_spec(spec: Dict[str, Any]) -> StructuredTool:
    """
    Dynamically create StructuredTool from a tool specification.

    Args:
        spec: Tool specification dict with keys:
            - name: Tool function name
            - description: Tool description for LLM
            - client_class: Name of agent client class
            - client_method: Method name on client class
            - request_model: Name of Pydantic request model

    Returns:
        StructuredTool instance ready for LangGraph agent use
    """
    tool_name = spec["name"]
    description = spec["description"]
    client_class_name = spec["client_class"]
    client_method_name = spec["client_method"]
    request_model_name = spec["request_model"]

    # Import client class from tradingeconomics.clients
    client_class = _import_class(
        "tradingeconomics.clients",
        client_class_name
    )

    # Import request model from tradingeconomics.models.requests
    request_model = _import_class(
        "tradingeconomics.models.requests",
        request_model_name
    )

    # Create wrapper function that calls the client method
    def tool_function(**kwargs) -> Dict[str, Any]:
        """
        Dynamically generated tool function.

        Accepts kwargs matching the request model fields,
        creates request model instance, calls client method,
        and returns standardized response.
        """
        # Get singleton client instance
        client = get_client_instance(client_class)

        # Create request model from kwargs
        request = request_model(**kwargs)

        # Call client method
        method = getattr(client, client_method_name)
        result = method(request)

        return result

    # Set function metadata for better LLM understanding
    tool_function.__name__ = tool_name
    tool_function.__doc__ = description

    # Create StructuredTool from function and request model schema
    tool = StructuredTool.from_function(
        func=tool_function,
        name=tool_name,
        description=description,
        args_schema=request_model,
    )

    return tool


# Generate all tools from specs
ALL_TOOLS: List[StructuredTool] = [
    create_tool_from_spec(spec)
    for spec in TOOL_SPECS
]

# Create name-to-tool mapping for quick lookup
TOOLS_BY_NAME: Dict[str, StructuredTool] = {
    tool.name: tool
    for tool in ALL_TOOLS
}


__all__ = [
    "ALL_TOOLS",
    "TOOLS_BY_NAME",
    "create_tool_from_spec",
]
