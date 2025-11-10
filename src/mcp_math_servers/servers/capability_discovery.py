"""Capability discovery FastMCP server implementation."""

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.exceptions import DisabledError

CATEGORY = "Capability Discovery / Tool Registration"
SERVER_NAME = "math-capability-registry"

_DOCS_URL = "https://gofastmcp.com/getting-started/welcome"
_EXECUTION_REDIRECT = (
    "This server only exposes tool metadata for educational purposes. "
    "Use the math-data-provider server to actually execute '{tool_name}'."
)


def _raise_capability_only(tool_name: str) -> None:
    """Always raise to remind clients this server only advertises tools."""
    raise DisabledError(_EXECUTION_REDIRECT.format(tool_name=tool_name))


def build_server() -> FastMCP:
    """Create a FastMCP server that only returns manifest data."""

    server = FastMCP(
        name=SERVER_NAME,
        version="0.1.0",
        instructions=(
            "The math capability registry demonstrates MCP's discovery pattern. "
            "Inspect the manifest to learn which arithmetic tools exist before "
            "calling into the execution-focused servers in this package."
        ),
        website_url=_DOCS_URL,
    )

    @server.tool(
        name="math_add",
        title="Add two numbers",
        description=(
            "Advertise how to sum two floats. Call the math-data-provider server "
            "with the same parameters to execute the calculation."
        ),
    )
    def math_add(augend: float, addend: float) -> float:  # pragma: no cover - raises
        _raise_capability_only("math_add")

    @server.tool(
        name="math_subtract",
        title="Subtract numbers",
        description="Return metadata for subtracting the subtrahend from the minuend.",
    )
    def math_subtract(minuend: float, subtrahend: float) -> float:  # pragma: no cover
        _raise_capability_only("math_subtract")

    @server.tool(
        name="math_multiply",
        title="Multiply numbers",
        description="Document how to multiply two factors.",
    )
    def math_multiply(multiplicand: float, multiplier: float) -> float:  # pragma: no cover
        _raise_capability_only("math_multiply")

    @server.tool(
        name="math_divide",
        title="Divide numbers",
        description="Explain how to divide a dividend by a non-zero divisor.",
    )
    def math_divide(dividend: float, divisor: float) -> float:  # pragma: no cover
        _raise_capability_only("math_divide")

    return server


__all__ = ["build_server", "CATEGORY", "SERVER_NAME"]
