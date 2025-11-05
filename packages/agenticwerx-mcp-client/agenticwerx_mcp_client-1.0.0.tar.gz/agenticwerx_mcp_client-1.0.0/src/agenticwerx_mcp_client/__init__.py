"""
AgenticWerx MCP Client

A Model Context Protocol (MCP) client for AgenticWerx rule packages.
Provides universal code analysis across all IDEs and programming languages.
"""

__version__ = "1.0.0"
__author__ = "AgenticWerx"
__email__ = "support@agenticwerx.com"

from .client import AgenticWerxMCPClient
from .api import AgenticWerxAPI

__all__ = ["AgenticWerxMCPClient", "AgenticWerxAPI"]