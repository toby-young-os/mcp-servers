"""Client utilities for exercising the example FastMCP servers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Mapping

from mcp_math_servers.servers import ServerBlueprint


@dataclass(slots=True)
class ClientScenario:
    """
    Describe how the demo client should exercise a server blueprint.

    :param name: Short identifier for the scenario.
    :param description: Human-readable explanation of what the scenario does.
    :param blueprint_key: Blueprint name or alias to load for the scenario.
    :param run: Awaitable callable that executes the scenario logic.
    """

    name: str
    description: str
    blueprint_key: str
    run: Callable[[ServerBlueprint], Awaitable[None]]


ScenarioRegistry = Mapping[str, ClientScenario]
"""Mapping from scenario key to ``ClientScenario`` definitions."""

__all__ = ["ClientScenario", "ScenarioRegistry"]
