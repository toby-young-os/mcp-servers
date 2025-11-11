"""CLI helpers for exercising the FastMCP math servers."""

from __future__ import annotations

import argparse
import json
from typing import Iterable

import asyncio

from mcp_math_servers.client import ClientScenario, ScenarioRegistry
from mcp_math_servers.servers import ServerBlueprint, get_blueprint


async def _prepare_server(blueprint: ServerBlueprint):
    server = blueprint.factory()
    tools = await server._tool_manager.get_tools()  # type: ignore[attr-defined]
    return server, tools


def _print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def _print_server_intro(server, blueprint: ServerBlueprint) -> None:
    print(f"{server.name} [{blueprint.category}]")
    if server.instructions:
        print(f"Instructions: {server.instructions}")


def _print_manifest(tools: dict[str, object]) -> None:
    print("Tools:")
    for name in sorted(tools):
        tool = tools[name]
        description = getattr(tool, "description", "No description provided.")
        parameters = getattr(tool, "parameters", {})
        print(f"  - {name}: {description}")
        print(f"    schema: {json.dumps(parameters, indent=2)}")


async def _run_tool(tools: dict[str, object], name: str, args: dict[str, float | str]):
    tool = tools[name]
    result = await tool.run(args)  # type: ignore[attr-defined]
    if result.structured_content is not None:
        return result.structured_content
    return result.content


async def _run_capability_demo(blueprint: ServerBlueprint) -> None:
    server, tools = await _prepare_server(blueprint)
    _print_server_intro(server, blueprint)
    _print_manifest(tools)


async def _run_data_demo(blueprint: ServerBlueprint) -> None:
    server, tools = await _prepare_server(blueprint)
    _print_server_intro(server, blueprint)
    _print_manifest(tools)
    payload = await _run_tool(tools, "math_add", {"augend": 8, "addend": 13})
    print("Sample response:", json.dumps(payload, indent=2))


async def _run_prompt_demo(blueprint: ServerBlueprint) -> None:
    server, tools = await _prepare_server(blueprint)
    _print_server_intro(server, blueprint)
    _print_manifest(tools)
    payload = await _run_tool(
        tools,
        "math_add_with_prompt",
        {"augend": 5, "addend": 11},
    )
    print("Sample response:", json.dumps(payload, indent=2))


async def _run_autonomous_demo(blueprint: ServerBlueprint) -> None:
    server, tools = await _prepare_server(blueprint)
    _print_server_intro(server, blueprint)
    _print_manifest(tools)
    payload = await _run_tool(
        tools,
        "solve_math_problem",
        {"problem": "If you triple 4 and subtract 5, what do you get?"},
    )
    print("Sample response:", json.dumps(payload, indent=2))


SCENARIOS: ScenarioRegistry = {
    "capability": ClientScenario(
        name="capability",
        description="Inspect the manifest returned by the capability registry server.",
        blueprint_key="capability",
        run=_run_capability_demo,
    ),
    "data": ClientScenario(
        name="data",
        description="Execute real math tools returning structured JSON.",
        blueprint_key="data",
        run=_run_data_demo,
    ),
    "prompt": ClientScenario(
        name="prompt",
        description="Observe data paired with a suggested follow-up prompt.",
        blueprint_key="prompt",
        run=_run_prompt_demo,
    ),
    "autonomous": ClientScenario(
        name="autonomous",
        description="Delegate a math word problem to the autonomous reasoner.",
        blueprint_key="autonomous",
        run=_run_autonomous_demo,
    ),
}


def _resolve_scenario(key: str) -> ClientScenario | None:
    normalized = key.lower()
    if normalized in SCENARIOS:
        return SCENARIOS[normalized]
    for scenario in SCENARIOS.values():
        if normalized in {
            scenario.name.lower(),
            scenario.blueprint_key.lower(),
        }:
            return scenario
    return None


async def _run_scenarios(targets: Iterable[ClientScenario]) -> None:
    for scenario in targets:
        _print_header(f"Scenario: {scenario.name}")
        blueprint = get_blueprint(scenario.blueprint_key)
        await scenario.run(blueprint)


def _list_scenarios() -> None:
    print("Available scenarios:")
    for key, scenario in SCENARIOS.items():
        print(f"  - {key}: {scenario.description}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run FastMCP math demo scenarios.")
    parser.add_argument(
        "scenario",
        nargs="?",
        default="all",
        help="Scenario or blueprint name (default: all).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit.",
    )
    args = parser.parse_args(argv)

    if args.list:
        _list_scenarios()
        return

    if args.scenario == "all":
        targets = list(SCENARIOS.values())
    else:
        scenario = _resolve_scenario(args.scenario)
        if scenario is None:
            parser.error(
                f"Unknown scenario '{args.scenario}'. Use --list to see available names."
            )
        targets = [scenario]

    asyncio.run(_run_scenarios(targets))


if __name__ == "__main__":  # pragma: no cover
    main()
