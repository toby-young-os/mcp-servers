"""FastMCP server examples for educational math-focused demos."""

from importlib import import_module
from typing import Any

try:  # pragma: no cover - simple side effect
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency guaranteed in runtime
    load_dotenv = None  # type: ignore[assignment]

if load_dotenv is not None:
    load_dotenv()

__all__ = ["load_module"]


def load_module(path: str) -> Any:
    """Dynamically import a module from the ``mcp_math_servers`` namespace."""
    return import_module(f"mcp_math_servers.{path}")
