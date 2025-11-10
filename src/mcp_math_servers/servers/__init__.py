"""Server factory placeholders for each MCP category."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


class ServerFactory(Protocol):
    """Protocol for functions that construct and return a FastMCP server."""

    def __call__(self) -> object:  # pragma: no cover - placeholder until implementations land
        ...


@dataclass(slots=True)
class ServerBlueprint:
    """Describes an example server and the MCP category it demonstrates."""

    name: str
    category: str
    factory: Callable[[], object]
    summary: str


__all__ = [
    "ServerBlueprint",
    "ServerFactory",
]
