"""Data-providing FastMCP server implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fastmcp import FastMCP

CATEGORY = "Data-Providing / Context-Enriching"
SERVER_NAME = "math-data-provider"


@dataclass(slots=True)
class MathResult:
    """Structured payload returned by every math tool."""

    operation: str
    inputs: dict[str, float]
    result: float

    def serialize(self) -> dict[str, Any]:
        return asdict(self)


def _response(operation: str, **inputs: float) -> dict[str, Any]:
    """Wrap arithmetic outputs with metadata for downstream reasoning."""
    return MathResult(operation=operation, inputs=inputs, result=_compute(operation, inputs)).serialize()


def _compute(operation: str, inputs: dict[str, float]) -> float:
    if operation == "addition":
        return inputs["augend"] + inputs["addend"]
    if operation == "subtraction":
        return inputs["minuend"] - inputs["subtrahend"]
    if operation == "multiplication":
        return inputs["multiplicand"] * inputs["multiplier"]
    if operation == "division":
        divisor = inputs["divisor"]
        if divisor == 0:
            raise ValueError("Divisor must be non-zero.")
        return inputs["dividend"] / divisor
    raise ValueError(f"Unsupported operation: {operation}")


def build_server() -> FastMCP:
    """Return a FastMCP server that executes math tools and returns JSON data."""

    server = FastMCP(
        name=SERVER_NAME,
        version="0.1.0",
        instructions=(
            "Executes arithmetic operations and returns structured JSON payloads "
            "that other agents can reason over."
        ),
    )

    @server.tool(
        name="math_add",
        title="Add two numbers",
        description="Return the sum of augend and addend as structured data.",
    )
    def math_add(augend: float, addend: float) -> dict[str, Any]:
        return _response("addition", augend=augend, addend=addend)

    @server.tool(
        name="math_subtract",
        title="Subtract numbers",
        description="Return minuend - subtrahend as structured data.",
    )
    def math_subtract(minuend: float, subtrahend: float) -> dict[str, Any]:
        return _response("subtraction", minuend=minuend, subtrahend=subtrahend)

    @server.tool(
        name="math_multiply",
        title="Multiply numbers",
        description="Return multiplicand * multiplier as structured data.",
    )
    def math_multiply(multiplicand: float, multiplier: float) -> dict[str, Any]:
        return _response("multiplication", multiplicand=multiplicand, multiplier=multiplier)

    @server.tool(
        name="math_divide",
        title="Divide numbers",
        description="Return dividend / divisor as structured data.",
    )
    def math_divide(dividend: float, divisor: float) -> dict[str, Any]:
        return _response("division", dividend=dividend, divisor=divisor)

    return server


__all__ = ["build_server", "CATEGORY", "SERVER_NAME"]
