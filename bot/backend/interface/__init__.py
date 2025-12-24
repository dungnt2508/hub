"""
Interface Layer

This layer handles:
- HTTP/WebSocket endpoints
- Request/Response formatting
- Personalization application
- Error handling
"""

from .api_handler import APIHandler
from .response_formatter import format_response

__all__ = ["APIHandler", "format_response"]

