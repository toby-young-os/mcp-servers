"""Autonomous reasoning FastMCP server implementation."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Callable

from fastmcp import FastMCP

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency managed via pyproject
    OpenAI = None

CATEGORY = "Autonomous / Server-Side Reasoning"
SERVER_NAME = "math-autonomous-reasoner"

_DEFAULT_MODEL = "gpt-4o-mini"
_SYSTEM_PROMPT = (
    "You are an autonomous math tutor. Solve the user's problem step by step and "
    "produce JSON with keys 'reasoning_steps' (list of short steps) and 'final_answer'. "
    "Keep reasoning grounded in arithmetic and avoid prose outside the JSON."
)


@dataclass(slots=True)
class AutonomousResult:
    problem: str
    reasoning_steps: list[str]
    final_answer: str
    model: str
    source: str

    def serialize(self) -> dict[str, Any]:
        return asdict(self)


def _build_client() -> OpenAI:
    if OpenAI is None:
        raise RuntimeError("openai package is not available.")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required for this server.")
    return OpenAI(api_key=api_key)


def _chat_completion(client: OpenAI, *, model: str, problem: str) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        max_tokens=400,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Solve this math problem and respond with JSON only.\nProblem: {problem}"
                ),
            },
        ],
    )
    raw_content = response.choices[0].message.content or ""
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        parsed = {
            "reasoning_steps": [raw_content.strip()],
            "final_answer": raw_content.strip(),
        }
    reasoning_steps = parsed.get("reasoning_steps") or [parsed.get("final_answer", "Unknown")]
    final_answer = parsed.get("final_answer", reasoning_steps[-1])
    return {
        "reasoning_steps": reasoning_steps,
        "final_answer": final_answer,
        "model": model,
        "source": "openai",
    }


def _fallback_reasoner(problem: str) -> dict[str, Any]:
    numbers = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", problem)]
    lowered = problem.lower()
    operation_map: dict[str, Callable[[float, float], float]] = {
        "add": lambda a, b: a + b,
        "plus": lambda a, b: a + b,
        "sum": lambda a, b: a + b,
        "subtract": lambda a, b: a - b,
        "minus": lambda a, b: a - b,
        "difference": lambda a, b: a - b,
        "multiply": lambda a, b: a * b,
        "times": lambda a, b: a * b,
        "product": lambda a, b: a * b,
        "divide": lambda a, b: a / b if b != 0 else float("inf"),
        "quotient": lambda a, b: a / b if b != 0 else float("inf"),
    }

    result = None
    operation = "analysis"
    if len(numbers) >= 2:
        for keyword, fn in operation_map.items():
            if keyword in lowered:
                result = fn(numbers[0], numbers[1])
                operation = keyword
                break

    steps = [
        "Fallback reasoner engaged due to missing OpenAI credentials.",
        f"Identified operation '{operation}' using heuristic parsing.",
    ]
    final_answer = result if result is not None else "Unable to determine answer."
    steps.append(f"Computed result: {final_answer}")

    return {
        "reasoning_steps": steps,
        "final_answer": str(final_answer),
        "model": "heuristic-fallback",
        "source": "fallback",
    }


def _run_reasoning(problem: str, *, model: str) -> dict[str, Any]:
    try:
        client = _build_client()
    except RuntimeError:
        return _fallback_reasoner(problem)

    try:
        return _chat_completion(client, model=model, problem=problem)
    except Exception:
        return _fallback_reasoner(problem)


def build_server() -> FastMCP:
    """Return a FastMCP server that performs internal reasoning with OpenAI."""

    server = FastMCP(
        name=SERVER_NAME,
        version="0.1.0",
        instructions=(
            "Delegates math reasoning to an internal OpenAI call and returns the final answer "
            "plus reasoning steps. Falls back to a heuristic reasoner if credentials are missing."
        ),
    )

    @server.tool(
        name="solve_math_problem",
        title="Solve a math word problem autonomously",
        description=(
            "Provide a natural language problem. The server uses OpenAI to reason internally "
            "and returns the final answer with the reasoning path."
        ),
    )
    def solve_math_problem(problem: str, model: str = _DEFAULT_MODEL) -> dict[str, Any]:
        payload = _run_reasoning(problem, model=model)
        result = AutonomousResult(
            problem=problem,
            reasoning_steps=payload["reasoning_steps"],
            final_answer=str(payload["final_answer"]),
            model=payload["model"],
            source=payload["source"],
        )
        return result.serialize()

    return server


__all__ = ["build_server", "CATEGORY", "SERVER_NAME"]
