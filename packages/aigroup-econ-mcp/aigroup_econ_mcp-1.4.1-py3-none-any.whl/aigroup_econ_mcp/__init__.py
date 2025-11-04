"""
AIGroup  MCP 
MCP - 


- 
- OLS
- 
- 
- 
"""

__version__ = "1.4.1"
__author__ = "AIGroup jackdark425@gmail.com"
__description__ = "MCP - "

from .server import create_mcp_server

__all__ = ["create_mcp_server", "__version__", "__author__", "__description__"]