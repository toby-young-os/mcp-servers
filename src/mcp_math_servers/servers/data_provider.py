"""Data-providing FastMCP server implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fastmcp import FastMCP

CATEGORY = "Data-Providing / Context-Enriching"
"""Human-readable label used in documentation and manifests."""

SERVER_NAME = "math-data-provider"
"""Server identifier exposed to clients."""


@dataclass(slots=True)
class MathResult:
    """
    Structured payload returned by every math tool.

    :param operation: Name of the arithmetic operation that was executed.
    :param inputs: Dictionary describing the numeric inputs used.
    :param result: Computed numeric result.
    """

    operation: str
    inputs: dict[str, float]
    result: float

    def serialize(self) -> dict[str, Any]:
        """
        Convert the dataclass into a serializable dictionary.

        :returns: Dictionary representation of the result.
        """

        return asdict(self)


def _response(operation: str, **inputs: float) -> dict[str, Any]:
    """
    Wrap arithmetic outputs with metadata for downstream reasoning.

    :param operation: Operation slug such as ``addition``.
    :param inputs: Numeric inputs keyed by argument name.
    :returns: Serialized ``MathResult`` dictionary.
    """

    return MathResult(operation=operation, inputs=inputs, result=_compute(operation, inputs)).serialize()


def _compute(operation: str, inputs: dict[str, float]) -> float:
    """
    Compute a math operation using the provided inputs.

    :param operation: Operation slug such as ``addition``.
    :param inputs: Numeric inputs keyed by argument name.
    :returns: Result of the computation.
    :raises ValueError: If the operation is unsupported or invalid input is provided.
    """

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
    """
    Return a FastMCP server that executes math tools and returns JSON data.

    :returns: Configured ``FastMCP`` instance for the data provider.
    """

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
        """
        Add two numbers and return structured result metadata.

        :param augend: First operand.
        :param addend: Second operand.
        :returns: Structured JSON containing inputs and the sum.
        """

        return _response("addition", augend=augend, addend=addend)

    @server.tool(
        name="math_subtract",
        title="Subtract numbers",
        description="Return minuend - subtrahend as structured data.",
    )
    def math_subtract(minuend: float, subtrahend: float) -> dict[str, Any]:
        """
        Subtract two numbers and return structured result metadata.

        :param minuend: Value from which the subtrahend is removed.
        :param subtrahend: Value to subtract.
        :returns: Structured JSON containing inputs and the difference.
        """

        return _response("subtraction", minuend=minuend, subtrahend=subtrahend)

    @server.tool(
        name="math_multiply",
        title="Multiply numbers",
        description="Return multiplicand * multiplier as structured data.",
    )
    def math_multiply(multiplicand: float, multiplier: float) -> dict[str, Any]:
        """
        Multiply two numbers and return structured result metadata.

        :param multiplicand: First factor.
        :param multiplier: Second factor.
        :returns: Structured JSON containing inputs and the product.
        """

        return _response("multiplication", multiplicand=multiplicand, multiplier=multiplier)

    @server.tool(
        name="math_divide",
        title="Divide numbers",
        description="Return dividend / divisor as structured data.",
    )
    def math_divide(dividend: float, divisor: float) -> dict[str, Any]:
        """
        Divide two numbers and return structured result metadata.

        :param dividend: Numerator value.
        :param divisor: Denominator value (must be non-zero).
        :returns: Structured JSON containing inputs and the quotient.
        """

        return _response("division", dividend=dividend, divisor=divisor)

    return server


__all__ = ["build_server", "CATEGORY", "SERVER_NAME"]
