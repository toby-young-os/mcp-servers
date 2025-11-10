"""FastMCP server examples for educational math-focused demos."""

from importlib import import_module
from typing import Any

__all__ = ["load_module"]


def load_module(path: str) -> Any:
    """Dynamically import a module from the ``mcp_math_servers`` namespace."""
    return import_module(f"mcp_math_servers.{path}")
