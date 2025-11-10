"""Simple hooks for running the example servers locally."""

from __future__ import annotations

from mcp_math_servers.client import ClientScenario


def default_scenario() -> ClientScenario:
    """Return a placeholder scenario until the demo client is wired up."""

    def _runner(_blueprint):
        raise NotImplementedError("Demo client will be implemented after servers exist.")

    return ClientScenario(
        name="default",
        description="Connects to a server and logs its manifest.",
        run=_runner,
    )
