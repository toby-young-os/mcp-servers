"""Interactive CLI for chatting with the FastMCP math servers."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Mapping, Sequence

import anyio

from mcp_math_servers.servers import ServerBlueprint, get_blueprint

DEFAULT_SERVER = "autonomous"
EXIT_COMMANDS = {"exit", "quit", ":q"}
HELP_COMMANDS = {"help", "?", ":help"}
MANIFEST_COMMANDS = {"tools", "manifest"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interactive REPL for FastMCP math servers."
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help=(
            "Server blueprint name or alias to use "
            "(default: %(default)s, see fastmcp-math-demo --list)."
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override for the autonomous reasoner.",
    )
    parser.add_argument(
        "--show-json",
        action="store_true",
        help="Print the raw JSON payload returned by the tool.",
    )
    return parser


def _format_schema(parameters: Mapping[str, object]) -> str:
    return json.dumps(parameters, indent=2)


async def _call_tool(tool, arguments: Mapping[str, object]) -> Mapping[str, object] | list[object]:
    result = await tool.run(arguments)
    if result.structured_content is not None:
        return result.structured_content
    return result.content


def _print_manifest(tools: Mapping[str, object]) -> None:
    print("Tools:")
    for name in sorted(tools):
        tool = tools[name]
        description = getattr(tool, "description", "")
        parameters = getattr(tool, "parameters", {})
        print(f"  - {name}: {description}")
        if parameters:
            print(f"    schema: {_format_schema(parameters)}")


def _readline(prompt: str) -> str:
    return input(prompt)


@dataclass
class ChatContext:
    blueprint: ServerBlueprint
    tools: Mapping[str, object]
    args: argparse.Namespace


class BaseHandler:
    def __init__(self, context: ChatContext) -> None:
        self.context = context

    def intro(self) -> None:
        print(f"[chat] Connected to {self.context.blueprint.name}")
        instructions = getattr(self.context.blueprint.factory(), "instructions", None)
        if instructions:
            print(instructions)

    def help(self) -> None:
        print("Type 'exit' to quit, 'tools' to reprint the manifest, or ask a question.")

    async def handle(self, user_input: str) -> None:  # pragma: no cover - abstract
        raise NotImplementedError


class CapabilityHandler(BaseHandler):
    def help(self) -> None:
        print(
            "This server only advertises tools. "
            "Use 'fastmcp-math-demo data' to execute math operations."
        )

    async def handle(self, user_input: str) -> None:
        print(
            "Capability registry is read-only. "
            "Run the data provider or prompt helper servers to execute math."
        )


class _BinaryOpMixin:
    OPERATIONS = {}

    def _parse(self, user_input: str):
        parts = user_input.split()
        if len(parts) != 3:
            print("Format: <operation> <number> <number> (e.g., add 2 3)")
            return None
        op, left, right = parts
        op = op.lower()
        if op not in self.OPERATIONS:
            print(f"Unknown operation '{op}'. Known: {', '.join(self.OPERATIONS)}")
            return None
        try:
            a = float(left)
            b = float(right)
        except ValueError:
            print("Numbers must be valid floats.")
            return None
        return op, a, b

    async def _run_operation(self, tool_name: str, payload: Mapping[str, float]) -> Mapping[str, object]:
        tool = self.context.tools[tool_name]
        return await _call_tool(tool, payload)


class DataHandler(_BinaryOpMixin, BaseHandler):
    OPERATIONS = {
        "add": ("math_add", lambda a, b: {"augend": a, "addend": b}),
        "subtract": ("math_subtract", lambda a, b: {"minuend": a, "subtrahend": b}),
        "multiply": ("math_multiply", lambda a, b: {"multiplicand": a, "multiplier": b}),
        "divide": ("math_divide", lambda a, b: {"dividend": a, "divisor": b}),
    }

    async def handle(self, user_input: str) -> None:
        parsed = self._parse(user_input)
        if not parsed:
            return
        op, left, right = parsed
        tool_name, arg_builder = self.OPERATIONS[op]
        payload = await self._run_operation(tool_name, arg_builder(left, right))
        if self.context.args.show_json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"{op.title()} result: {payload['result']} (inputs={payload['inputs']})")


class PromptHandler(_BinaryOpMixin, BaseHandler):
    OPERATIONS = {
        "add": ("math_add_with_prompt", lambda a, b: {"augend": a, "addend": b}),
        "subtract": ("math_subtract_with_prompt", lambda a, b: {"minuend": a, "subtrahend": b}),
        "multiply": ("math_multiply_with_prompt", lambda a, b: {"multiplicand": a, "multiplier": b}),
        "divide": ("math_divide_with_prompt", lambda a, b: {"dividend": a, "divisor": b}),
    }

    async def handle(self, user_input: str) -> None:
        parsed = self._parse(user_input)
        if not parsed:
            return
        op, left, right = parsed
        tool_name, arg_builder = self.OPERATIONS[op]
        payload = await self._run_operation(tool_name, arg_builder(left, right))
        if self.context.args.show_json:
            print(json.dumps(payload, indent=2))
            return
        print(f"{op.title()} result: {payload['result']}")
        print(f"Suggested prompt: {payload['next_prompt']}")


class AutonomousHandler(BaseHandler):
    async def handle(self, user_input: str) -> None:
        tool = self.context.tools["solve_math_problem"]
        arguments = {"problem": user_input}
        if self.context.args.model:
            arguments["model"] = self.context.args.model
        payload = await _call_tool(tool, arguments)
        if self.context.args.show_json:
            print(json.dumps(payload, indent=2))
            return
        steps = payload.get("reasoning_steps", [])
        if steps:
            print("Reasoning:")
            for idx, step in enumerate(steps, start=1):
                print(f"  {idx}. {step}")
        print(f"Final answer: {payload.get('final_answer')}")


def _make_handler(blueprint: ServerBlueprint, context: ChatContext) -> BaseHandler:
    if blueprint.name == "math-capability-registry":
        return CapabilityHandler(context)
    if blueprint.name == "math-data-provider":
        return DataHandler(context)
    if blueprint.name == "math-prompt-helper":
        return PromptHandler(context)
    return AutonomousHandler(context)


async def _async_main(args: argparse.Namespace) -> None:
    blueprint = get_blueprint(args.server)
    server = blueprint.factory()
    tools = await server._tool_manager.get_tools()  # type: ignore[attr-defined]
    context = ChatContext(blueprint=blueprint, tools=tools, args=args)
    handler = _make_handler(blueprint, context)

    print(f"[chat] Selected server '{blueprint.name}' ({blueprint.category})")
    instructions = getattr(server, "instructions", None)
    if instructions:
        print(instructions)
    print("Type 'help' for commands, 'exit' to quit.")
    _print_manifest(tools)

    while True:
        try:
            user_input = await anyio.to_thread.run_sync(_readline, "> ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat.")
            break
        user_input = user_input.strip()
        if not user_input:
            continue
        lowered = user_input.lower()
        if lowered in EXIT_COMMANDS:
            print("Goodbye!")
            break
        if lowered in HELP_COMMANDS:
            handler.help()
            continue
        if lowered in MANIFEST_COMMANDS:
            _print_manifest(tools)
            continue
        await handler.handle(user_input)


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    anyio.run(_async_main, args)


if __name__ == "__main__":  # pragma: no cover
    main()
