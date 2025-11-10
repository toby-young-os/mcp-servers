"""Client utilities for exercising the example FastMCP servers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from mcp_math_servers.servers import ServerBlueprint


@dataclass(slots=True)
class ClientScenario:
    """Describes how the demo client should exercise a server."""

    name: str
    description: str
    run: Callable[[ServerBlueprint], None]


ScenarioRegistry = Mapping[str, ClientScenario]

__all__ = ["ClientScenario", "ScenarioRegistry"]
