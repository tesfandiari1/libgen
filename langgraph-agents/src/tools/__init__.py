"""Custom tools for LangGraph agents"""
from .custom_tools import get_stock_price, search_web, calculate, AVAILABLE_TOOLS
from .web_tools import fetch_web_page, anna_search_tool

# Convenience aggregate without breaking existing imports
ALL_TOOLS = [*AVAILABLE_TOOLS, fetch_web_page, anna_search_tool]

__all__ = [
    "get_stock_price",
    "search_web",
    "calculate",
    "fetch_web_page",
    "anna_search_tool",
    "AVAILABLE_TOOLS",
    "ALL_TOOLS",
]
