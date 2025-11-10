"""Prompt-returning FastMCP server implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fastmcp import FastMCP

CATEGORY = "Prompt-Returning / Co-Reasoning"
SERVER_NAME = "math-prompt-helper"


@dataclass(slots=True)
class PromptedResult:
    operation: str
    inputs: dict[str, float]
    result: float
    next_prompt: str

    def serialize(self) -> dict[str, Any]:
        return asdict(self)


def _build_prompt(operation: str, payload: dict[str, float], answer: float) -> str:
    return (
        f"The {operation} result is {answer}. Inputs: {payload}. "
        "Incorporate this numeric value into your next reasoning step. "
        "If the user asked a follow-up, restate the interpreted question before responding."
    )


def _structure(operation: str, **inputs: float) -> dict[str, Any]:
    result = _compute(operation, inputs)
    prompt = _build_prompt(operation, inputs, result)
    return PromptedResult(operation=operation, inputs=inputs, result=result, next_prompt=prompt).serialize()


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
    """Return a FastMCP server that pairs math data with suggested prompts."""

    server = FastMCP(
        name=SERVER_NAME,
        version="0.1.0",
        instructions=(
            "Demonstrates prompt-returning MCP responses by pairing math results with "
            "a suggested follow-up prompt the model can immediately run."
        ),
    )

    @server.tool(
        name="math_add_with_prompt",
        title="Add numbers (prompt-ready)",
        description="Return addition data plus a suggested follow-up prompt.",
    )
    def math_add(augend: float, addend: float) -> dict[str, Any]:
        return _structure("addition", augend=augend, addend=addend)

    @server.tool(
        name="math_subtract_with_prompt",
        title="Subtract numbers (prompt-ready)",
        description="Return subtraction data plus a suggested follow-up prompt.",
    )
    def math_subtract(minuend: float, subtrahend: float) -> dict[str, Any]:
        return _structure("subtraction", minuend=minuend, subtrahend=subtrahend)

    @server.tool(
        name="math_multiply_with_prompt",
        title="Multiply numbers (prompt-ready)",
        description="Return multiplication data plus a suggested follow-up prompt.",
    )
    def math_multiply(multiplicand: float, multiplier: float) -> dict[str, Any]:
        return _structure("multiplication", multiplicand=multiplicand, multiplier=multiplier)

    @server.tool(
        name="math_divide_with_prompt",
        title="Divide numbers (prompt-ready)",
        description="Return division data plus a suggested follow-up prompt.",
    )
    def math_divide(dividend: float, divisor: float) -> dict[str, Any]:
        return _structure("division", dividend=dividend, divisor=divisor)

    return server


__all__ = ["build_server", "CATEGORY", "SERVER_NAME"]
