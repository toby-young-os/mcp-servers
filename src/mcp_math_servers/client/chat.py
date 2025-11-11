"""Interactive CLI for chatting with the FastMCP math servers."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Callable, ClassVar, Mapping, Sequence

import asyncio

from mcp_math_servers.client.planner import (
    MCPPlanner,
    PlannerError,
    PlannerResult,
    is_planner_available,
)
from mcp_math_servers.servers import ServerBlueprint, get_blueprint

DEFAULT_SERVER = "autonomous"  # Default blueprint alias launched by the CLI.
EXIT_COMMANDS = {"exit", "quit", ":q"}  # Inputs that terminate the REPL.
HELP_COMMANDS = {"help", "?", ":help"}  # Inputs that display help instructions.
MANIFEST_COMMANDS = {"tools", "manifest"}  # Inputs that print the tool manifest.


def _build_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser that powers the chat CLI.

    :returns: Configured ``ArgumentParser`` instance.
    """

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
    planner_group = parser.add_mutually_exclusive_group()
    planner_group.add_argument(
        "--planner",
        dest="planner",
        action="store_true",
        help="Force the LLM planner to interpret natural-language queries.",
    )
    planner_group.add_argument(
        "--no-planner",
        dest="planner",
        action="store_false",
        help="Disable the LLM planner even if available.",
    )
    parser.set_defaults(planner=None)
    return parser


def _format_schema(parameters: Mapping[str, object]) -> str:
    """
    Render a tool's parameter schema as pretty-printed JSON.

    :param parameters: JSON-schema dictionary describing tool args.
    :returns: Indented JSON string suitable for console output.
    """

    return json.dumps(parameters, indent=2)


async def _call_tool(tool, arguments: Mapping[str, object]) -> Mapping[str, object] | list[object]:
    """
    Execute a FastMCP tool and normalize its output payload.

    :param tool: FastMCP tool object to execute.
    :param arguments: Arguments to pass when invoking the tool.
    :returns: Structured content if provided, otherwise the raw content list.
    """

    result = await tool.run(arguments)
    if result.structured_content is not None:
        return result.structured_content
    return result.content


def _print_manifest(tools: Mapping[str, object]) -> None:
    """
    Print each registered tool along with its schema to stdout.

    :param tools: Mapping of tool names to FastMCP tool objects.
    """

    print("Tools:")
    for name in sorted(tools):
        tool = tools[name]
        description = getattr(tool, "description", "")
        parameters = getattr(tool, "parameters", {})
        print(f"  - {name}: {description}")
        if parameters:
            print(f"    schema: {_format_schema(parameters)}")


def _readline(prompt: str) -> str:
    """
    Read a line of input from the console.

    :param prompt: Prompt string to display before reading.
    :returns: User input without the trailing newline.
    """

    return input(prompt)


@dataclass
class ChatContext:
    """
    Aggregates resources required to handle chat interactions.

    :param blueprint: Server blueprint associated with the active session.
    :param tools: Mapping of tool names to FastMCP tool objects.
    :param args: Parsed command-line arguments.
    :param planner: Optional planner for natural-language routing.
    """

    blueprint: ServerBlueprint
    tools: Mapping[str, object]
    args: argparse.Namespace
    planner: MCPPlanner | None = None


class BaseHandler:
    """Base class encapsulating shared behavior for chat handlers."""

    def __init__(self, context: ChatContext) -> None:
        """
        Store the shared chat context for subclasses.

        :param context: ChatContext containing blueprints, tools, and args.
        """

        self.context = context

    def intro(self) -> None:
        """
        Print introductory information about the connected server.
        """

        print(f"[chat] Connected to {self.context.blueprint.name}")
        instructions = getattr(self.context.blueprint.factory(), "instructions", None)
        if instructions:
            print(instructions)

    def help(self) -> None:
        """Print the generic help instructions for the handler."""

        print("Type 'exit' to quit, 'tools' to reprint the manifest, or ask a question.")

    async def handle(self, user_input: str) -> None:  # pragma: no cover - abstract
        """
        Process a single user input entry.

        :param user_input: Raw text the user entered.
        """

        raise NotImplementedError


class CapabilityHandler(BaseHandler):
    """Handler for the capability registry server which is read-only."""

    def help(self) -> None:
        """Explain that this handler cannot execute math operations."""

        print(
            "This server only advertises tools. "
            "Use 'fastmcp-math-demo data' to execute math operations."
        )

    async def handle(self, user_input: str) -> None:
        """
        Inform the user that the capability registry cannot execute commands.

        :param user_input: Ignored text supplied by the user.
        """

        print(
            "Capability registry is read-only. "
            "Run the data provider or prompt helper servers to execute math."
        )


class _BinaryOpMixin:
    """Mixin that parses simple binary math commands."""

    OperationBuilder = Callable[[float, float], dict[str, float]]
    OPERATIONS: ClassVar[dict[str, tuple[str, OperationBuilder]]] = {}

    def _parse(self, user_input: str):
        """
        Parse a binary math instruction of the form ``op left right``.

        :param user_input: Raw user input string.
        :returns: Tuple of (operation, left, right) or ``None`` if invalid.
        """

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
        """
        Execute the requested tool with the provided payload.

        :param tool_name: Name of the FastMCP tool to invoke.
        :param payload: Numeric arguments for the tool.
        :returns: Structured tool result.
        """

        tool = self.context.tools[tool_name]
        return await _call_tool(tool, payload)


class DataHandler(_BinaryOpMixin, BaseHandler):
    """Handler for the data-providing server which returns raw JSON results."""

    OPERATIONS = {
        "add": ("math_add", lambda a, b: {"augend": a, "addend": b}),
        "subtract": ("math_subtract", lambda a, b: {"minuend": a, "subtrahend": b}),
        "multiply": ("math_multiply", lambda a, b: {"multiplicand": a, "multiplier": b}),
        "divide": ("math_divide", lambda a, b: {"dividend": a, "divisor": b}),
    }

    async def handle(self, user_input: str) -> None:
        """
        Execute a data-only math operation and print the result.

        :param user_input: Command in the form ``add 2 3`` etc.
        """

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
    """Handler for the prompt-returning server that supplies suggested prompts."""

    OPERATIONS = {
        "add": ("math_add_with_prompt", lambda a, b: {"augend": a, "addend": b}),
        "subtract": ("math_subtract_with_prompt", lambda a, b: {"minuend": a, "subtrahend": b}),
        "multiply": ("math_multiply_with_prompt", lambda a, b: {"multiplicand": a, "multiplier": b}),
        "divide": ("math_divide_with_prompt", lambda a, b: {"dividend": a, "divisor": b}),
    }

    async def handle(self, user_input: str) -> None:
        """
        Execute a math operation and display its guiding prompt.

        :param user_input: Command in the form ``add 2 3`` etc.
        """

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
    """Handler for the autonomous reasoning server that delegates to OpenAI."""

    async def handle(self, user_input: str) -> None:
        """
        Invoke the autonomous server's `solve_math_problem` tool.

        :param user_input: Natural-language question describing a math task.
        """

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


class PlannerHandler(BaseHandler):
    """Handler that routes natural-language requests through the LLM planner."""
    def __init__(self, context: ChatContext, planner: MCPPlanner) -> None:
        super().__init__(context)
        self._planner = planner

    def help(self) -> None:
        print("Ask any natural-language question. Type 'exit' to quit.")

    async def handle(self, user_input: str) -> None:
        print("[planner] Interpreting request via LLM...")
        try:
            result = await self._planner.run(user_input)
        except PlannerError as exc:
            print(f"[planner] {exc}")
            if self.context.args.show_json:
                print("[planner] Falling back to manual mode for this turn.")
            return
        action = "respond" if not result.tool_name else f"call {result.tool_name}"
        print(f"[planner] Completed plan: {action}")
        self._print_result(result)

    def _print_result(self, result: PlannerResult) -> None:
        """
        Print the planner response and any associated tool payload.

        :param result: PlannerResult describing the final action and message.
        """

        if self.context.args.show_json:
            print(
                json.dumps(
                    {
                        "message": result.message,
                        "tool": result.tool_name,
                        "arguments": result.arguments,
                        "result": result.tool_result,
                        "raw_planner_response": result.raw_response,
                    },
                    indent=2,
                )
            )
        message = (result.message or "").strip()
        if message:
            print(message)
        else:
            print("[planner] Received an empty response from the LLM.")
            if not self.context.args.show_json:
                print(
                    "Re-run with --show-json or --no-planner if the issue persists."
                )


def _make_handler(blueprint: ServerBlueprint, context: ChatContext) -> BaseHandler:
    """
    Instantiate the appropriate handler for the selected server.

    :param blueprint: Server blueprint that the user selected.
    :param context: ChatContext shared across handlers.
    :returns: Concrete handler instance for the server type.
    """

    if context.planner is not None:
        return PlannerHandler(context, context.planner)
    if blueprint.name == "math-capability-registry":
        return CapabilityHandler(context)
    if blueprint.name == "math-data-provider":
        return DataHandler(context)
    if blueprint.name == "math-prompt-helper":
        return PromptHandler(context)
    return AutonomousHandler(context)


async def _async_main(args: argparse.Namespace) -> None:
    """
    Async entry point orchestrating the REPL session.

    :param args: Parsed command-line arguments.
    """

    blueprint = get_blueprint(args.server)
    server = blueprint.factory()
    tools = await server._tool_manager.get_tools()  # type: ignore[attr-defined]
    planner = None
    use_planner = _should_use_planner(args, blueprint)
    # Planner is optional; only instantiate when OpenAI credentials are present.
    if use_planner:
        if not is_planner_available():
            print("[chat] Planner requested but OpenAI is unavailable; falling back to manual mode.")
        else:
            try:
                planner = MCPPlanner(
                    tools=tools,
                    model=args.model or "gpt-4.1-mini",
                )
            except PlannerError as exc:
                print(f"[chat] Failed to initialize planner: {exc}")
                planner = None

    context = ChatContext(blueprint=blueprint, tools=tools, args=args, planner=planner)
    handler = _make_handler(blueprint, context)

    from mcp_math_servers import __version__

    print(
        f"[chat] fastmcp-math-servers v{__version__} | "
        f"Selected server '{blueprint.name}' ({blueprint.category})"
    )
    if context.planner:
        print(
            f"[chat] Planner enabled using model {args.model or 'gpt-4.1-mini'}."
        )
    else:
        print("[chat] Planner disabled; manual commands required.")
    instructions = getattr(server, "instructions", None)
    if instructions:
        print(instructions)
    print("Type 'help' for commands, 'exit' to quit.")
    _print_manifest(tools)

    while True:
        try:
            user_input = await asyncio.to_thread(_readline, "> ")
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

        # Dispatch to the handler (planner-aware or manual) for execution.
        await handler.handle(user_input)


def _should_use_planner(args: argparse.Namespace, blueprint: ServerBlueprint) -> bool:
    """
    Determine whether the planner should be engaged for the session.

    :param args: Parsed command-line arguments.
    :param blueprint: Selected server blueprint.
    :returns: ``True`` when planner usage is desired.
    """

    if args.planner is not None:
        return args.planner
    return blueprint.name != "math-autonomous-reasoner"


def main(argv: Sequence[str] | None = None) -> None:
    """
    CLI entry point for the chat application.

    :param argv: Optional list of command-line arguments.
    """

    parser = _build_parser()
    args = parser.parse_args(argv)
    asyncio.run(_async_main(args))


if __name__ == "__main__":  # pragma: no cover
    main()
