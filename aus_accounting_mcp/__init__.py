"""
aus-accounting-mcp: Unified Australian Accounting & Tax MCP Server
"""

__version__ = "0.1.0"
__author__ = "Ryan Duguid"

from .server import mcp, run_stdio

__all__ = ["mcp", "run_stdio"]