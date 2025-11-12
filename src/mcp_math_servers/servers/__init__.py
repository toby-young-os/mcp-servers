"""Server blueprints for each MCP category."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


class ServerFactory(Protocol):
    """Protocol for functions that construct and return a FastMCP server."""

    def __call__(self) -> object:  # pragma: no cover - placeholder until implementations land
        ...


@dataclass(slots=True)
class ServerBlueprint:
    """
    Describes an example server and the MCP category it demonstrates.

    :param name: Unique server identifier.
    :param category: Human-readable MCP category name.
    :param factory: Callable that constructs the FastMCP server.
    :param summary: Short description of the server capabilities.
    :param aliases: Additional names that reference the same blueprint.
    """

    name: str
    category: str
    factory: Callable[[], object]
    summary: str
    aliases: tuple[str, ...] = ()


__all__ = [
    "ServerBlueprint",
    "ServerFactory",
]

from .autonomous_reasoner import (
    CATEGORY as AUTONOMOUS_CATEGORY,
)
from .autonomous_reasoner import (
    SERVER_NAME as AUTONOMOUS_SERVER_NAME,
)
from .autonomous_reasoner import build_server as build_autonomous_reasoner
from .capability_discovery import CATEGORY as CAPABILITY_CATEGORY
from .capability_discovery import SERVER_NAME as CAPABILITY_SERVER_NAME
from .capability_discovery import build_server as build_capability_registry
from .data_provider import CATEGORY as DATA_CATEGORY
from .data_provider import SERVER_NAME as DATA_SERVER_NAME
from .data_provider import build_server as build_data_provider
from .prompt_helper import CATEGORY as PROMPT_CATEGORY
from .prompt_helper import SERVER_NAME as PROMPT_SERVER_NAME
from .prompt_helper import build_server as build_prompt_helper

_SERVER_BLUEPRINTS: tuple[ServerBlueprint, ...] = (
    ServerBlueprint(
        name=CAPABILITY_SERVER_NAME,
        category=CAPABILITY_CATEGORY,
        factory=build_capability_registry,
        summary="Advertises math tools without executing them, ideal for capability discovery.",
        aliases=("capability", "discovery"),
    ),
    ServerBlueprint(
        name=DATA_SERVER_NAME,
        category=DATA_CATEGORY,
        factory=build_data_provider,
        summary="Executes math operations and returns structured JSON payloads.",
        aliases=("data", "provider"),
    ),
    ServerBlueprint(
        name=PROMPT_SERVER_NAME,
        category=PROMPT_CATEGORY,
        factory=build_prompt_helper,
        summary="Pairs math data with a suggested follow-up prompt for co-reasoning.",
        aliases=("prompt", "co-reasoning"),
    ),
    ServerBlueprint(
        name=AUTONOMOUS_SERVER_NAME,
        category=AUTONOMOUS_CATEGORY,
        factory=build_autonomous_reasoner,
        summary="Delegates math problem solving to an internal OpenAI call.",
        aliases=("autonomous", "reasoner"),
    ),
)
"""Tuple containing all predefined server blueprints."""

_BLUEPRINT_INDEX = {
    blueprint.name.lower(): blueprint for blueprint in _SERVER_BLUEPRINTS
}
"""Lookup table mapping blueprint names and aliases to their definitions."""
for blueprint in _SERVER_BLUEPRINTS:
    for alias in blueprint.aliases:
        _BLUEPRINT_INDEX.setdefault(alias.lower(), blueprint)


def iter_blueprints() -> tuple[ServerBlueprint, ...]:
    """
    Return all server blueprints.

    :returns: Tuple containing every registered ``ServerBlueprint``.
    """

    return _SERVER_BLUEPRINTS


def get_blueprint(key: str) -> ServerBlueprint:
    """
    Fetch a blueprint by name or alias.

    :param key: Blueprint name or alias to look up.
    :returns: Matching ``ServerBlueprint`` instance.
    :raises KeyError: If the key does not correspond to a blueprint.
    """

    normalized = key.lower()
    if normalized not in _BLUEPRINT_INDEX:
        available = ", ".join(sorted(_BLUEPRINT_INDEX))
        raise KeyError(f"Unknown server '{key}'. Available: {available}")
    return _BLUEPRINT_INDEX[normalized]


__all__.extend(
    [
        "get_blueprint",
        "iter_blueprints",
    ]
)
