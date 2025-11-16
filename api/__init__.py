"""
Meton HTTP API module.

Provides FastAPI-based HTTP server for VS Code extension integration.
"""

from .server import app, start_server

__all__ = ["app", "start_server"]
