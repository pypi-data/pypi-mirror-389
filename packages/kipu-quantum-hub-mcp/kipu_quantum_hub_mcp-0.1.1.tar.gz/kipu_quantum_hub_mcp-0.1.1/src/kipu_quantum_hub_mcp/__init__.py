"""
Kipu Quantum Hub MCP Server

A Model Context Protocol server for interacting with the Kipu Quantum Hub platform.
"""

__version__ = "0.1.0"

from .server import mcp

__all__ = ["mcp"]