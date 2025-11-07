"""
Tool registry for Polygon agent tools.

Provides the main interface for agents to discover and access tools.
Agents can simply call get_tools() to get all available tools.
"""

from typing import List, Optional
from langchain_core.tools import StructuredTool

from .tools import ALL_TOOLS, TOOLS_BY_NAME


def get_tools(names: Optional[List[str]] = None) -> List[StructuredTool]:
    """
    Get Polygon tools for use in LangGraph agents.

    This is the main entry point for agents to access Polygon market data tools.
    Each tool wraps a Polygon API endpoint with agent-friendly parameters.

    Args:
        names: Optional list of specific tool names to retrieve.
               If None, returns all available tools.

    Returns:
        List of StructuredTool instances ready for agent use

    Example:
        >>> from polygon import get_tools
        >>> # Get all tools
        >>> all_tools = get_tools()
        >>>
        >>> # Get specific tools
        >>> snapshot_tools = get_tools(names=["get_polygon_snapshot"])
        >>>
        >>> # Use with LangGraph agent
        >>> agent = create_react_agent(model, tools=all_tools)

    Raises:
        KeyError: If a requested tool name is not found
    """
    if names is None:
        return ALL_TOOLS.copy()

    tools = []
    for name in names:
        if name not in TOOLS_BY_NAME:
            available = ", ".join(TOOLS_BY_NAME.keys())
            raise KeyError(
                f"Tool '{name}' not found. Available tools: {available}"
            )
        tools.append(TOOLS_BY_NAME[name])

    return tools


def get_tool(name: str) -> StructuredTool:
    """
    Get a single Polygon tool by name.

    Args:
        name: Tool name (e.g., "get_polygon_aggregates")

    Returns:
        StructuredTool instance

    Example:
        >>> from polygon import get_tool
        >>> aggregates_tool = get_tool("get_polygon_aggregates")

    Raises:
        KeyError: If the tool name is not found
    """
    if name not in TOOLS_BY_NAME:
        available = ", ".join(TOOLS_BY_NAME.keys())
        raise KeyError(
            f"Tool '{name}' not found. Available tools: {available}"
        )

    return TOOLS_BY_NAME[name]


def get_tool_names() -> List[str]:
    """
    Get names of all available Polygon tools.

    Returns:
        List of tool names

    Example:
        >>> from polygon import get_tool_names
        >>> print(get_tool_names())
        ['get_polygon_aggregates', 'get_polygon_snapshot']
    """
    return list(TOOLS_BY_NAME.keys())


__all__ = [
    "get_tools",
    "get_tool",
    "get_tool_names",
]
