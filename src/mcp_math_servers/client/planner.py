"""LLM-driven planner that routes natural language to MCP tools."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - dependency ensured via pyproject
    AsyncOpenAI = None  # type: ignore[assignment]


class PlannerError(RuntimeError):
    """Raised when the planner cannot produce a valid instruction."""


@dataclass(slots=True)
class PlannerDecision:
    """
    Structured instruction returned from the planner LLM.

    :param action: Planner directive such as ``respond`` or ``call_tool``.
    :param message: User-facing response text when ``action`` is ``respond``.
    :param tool_name: Name of the tool to invoke when ``action`` is ``call_tool``.
    :param arguments: JSON arguments to forward to the requested tool.
    :param raw_response: Unmodified LLM JSON string for auditing.
    """

    action: str | None
    message: str | None
    tool_name: str | None
    arguments: Mapping[str, Any] | None
    raw_response: str


@dataclass(slots=True)
class PlannerResult:
    """
    Final planner outcome combining tool decisions and user-facing text.

    :param message: Text that should be relayed to the user.
    :param tool_name: Tool invoked during planning, if any.
    :param arguments: Arguments that were supplied to the invoked tool.
    :param tool_result: Raw payload returned by the tool invocation.
    :param raw_response: Original JSON emitted by the planner LLM.
    """

    message: str = ""
    tool_name: str | None = None
    arguments: Mapping[str, Any] | None = None
    tool_result: Mapping[str, Any] | Sequence[Any] | None = None
    raw_response: str | None = None

# Instruction template conveying the allowed JSON schema to the planner LLM.
SYSTEM_PROMPT_TEMPLATE = """You are an MCP-aware planner sitting between a user and a set of tools.
You must ALWAYS respond with JSON that matches exactly this schema and nothing else:
{{
  "action": "respond" | "call_tool",
  "message": string (required when action == "respond"),
  "tool_name": string (required when action == "call_tool"),
  "arguments": object (required when action == "call_tool")
}}

Available tools:
{manifest}

Rules:
- Respond with a single JSON object with no surrounding prose or Markdown fences.
- Only call tools listed above.
- When calling a tool, supply exactly the JSON arguments the tool expects.
- If no tool is needed, reply with action "respond" and a helpful natural-language message.
- Never output additional prose outside the JSON object.
"""


def _format_manifest(tools: Mapping[str, Any]) -> str:
    """
    Build a human-readable manifest description of the registered tools.

    :param tools: Mapping of tool names to tool objects.
    :returns: Human-readable string summarizing the tools and schemas.
    """

    parts: list[str] = []
    for name, tool in tools.items():
        description = getattr(tool, "description", "No description provided.")
        parameters = getattr(tool, "parameters", {})
        parts.append(
            f"- {name}: {description}\n  Parameters: {json.dumps(parameters)}"
        )
    return "\n".join(parts)


def is_planner_available() -> bool:
    """
    Return ``True`` when the async OpenAI client and API key are available.

    :returns: ``True`` if AsyncOpenAI can be instantiated, otherwise ``False``.
    """

    return AsyncOpenAI is not None and bool(os.environ.get("OPENAI_API_KEY"))


class MCPPlanner:
    """Async planner that uses OpenAI to determine MCP tool usage."""

    def __init__(
        self,
        *,
        tools: Mapping[str, Any],
        model: str = "gpt-4.1-mini",
        timeout: float = 45.0,
    ) -> None:
        """
        Initialize the planner.

        :param tools: Mapping of tool names to FastMCP tool instances.
        :param model: OpenAI chat model identifier to use.
        :param timeout: Maximum seconds to wait for each OpenAI request.
        """
        if not is_planner_available():
            raise PlannerError(
                "OpenAI client is unavailable. Ensure `openai` is installed and OPENAI_API_KEY is set."
            )
        self._tools = tools
        self._client = AsyncOpenAI()
        self._model = model
        self._manifest = _format_manifest(tools)
        self._timeout = timeout

    async def run(self, user_input: str) -> PlannerResult:
        """
        Produce a planner decision based on free-form user text.

        :param user_input: The most recent user utterance.
        :returns: PlannerResult detailing how to respond or which tool to call.
        :raises PlannerError: If the planner cannot produce a valid instruction.
        """
        decision = await self._decide(user_input)
        if decision.action == "respond":
            if not decision.message:
                raise PlannerError("Planner returned action 'respond' without a message.")
            return PlannerResult(message=decision.message, raw_response=decision.raw_response)

        if decision.action == "call_tool":
            if not decision.tool_name or decision.arguments is None:
                raise PlannerError(
                    "Planner requested a tool call but did not provide name or arguments."
                )
            tool_name = decision.tool_name
            if tool_name not in self._tools:
                raise PlannerError(f"Planner referenced unknown tool '{tool_name}'.")
            tool = self._tools[tool_name]
            tool_result = await tool.run(decision.arguments)  # type: ignore[attr-defined]
            payload: Mapping[str, Any] | Sequence[Any]
            if getattr(tool_result, "structured_content", None) is not None:
                payload = tool_result.structured_content
            else:
                payload = tool_result.content
            final_message, final_raw = await self._summarize_with_tool(
                user_input=user_input,
                tool_name=tool_name,
                arguments=decision.arguments,
                payload=payload,
            )
            return PlannerResult(
                message=final_message,
                tool_name=tool_name,
                arguments=decision.arguments,
                tool_result=payload,
                raw_response=final_raw,
            )

        raise PlannerError(f"Unknown planner action '{decision.action}'.")

    async def _decide(self, user_input: str) -> PlannerDecision:
        """
        Request a planner decision from OpenAI.

        :param user_input: Raw user text to feed into the planner prompt.
        :returns: Parsed PlannerDecision instructions from the LLM.
        """
        prompt = SYSTEM_PROMPT_TEMPLATE.format(manifest=self._manifest)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input},
        ]
        content = await self._complete(messages)
        return self._parse_decision(content)

    async def _summarize_with_tool(
        self,
        *,
        user_input: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        payload: Mapping[str, Any] | Sequence[Any],
    ) -> tuple[str, str]:
        """
        Ask the planner to summarize the outcome of a completed tool call.

        :param user_input: Original question from the user.
        :param tool_name: Name of the tool that was executed.
        :param arguments: Arguments that were passed to the tool.
        :param payload: Result returned by the tool.
        :returns: Tuple of (message, raw_response) for user delivery.
        """
        prompt = SYSTEM_PROMPT_TEMPLATE.format(manifest=self._manifest)
        tool_summary = json.dumps(
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": payload,
            }
        )
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input},
            {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "action": "call_tool",
                        "tool_name": tool_name,
                        "arguments": arguments,
                    }
                ),
            },
            {
                "role": "user",
                "content": (
                    "Tool call completed. Use the result below to respond to the user "
                    "and DO NOT call another tool.\n"
                    f"Result: {tool_summary}"
                ),
            },
        ]
        content = await self._complete(messages)
        decision = self._parse_decision(content)
        if decision.action != "respond" or not decision.message:
            raise PlannerError(
                "Planner failed to provide a final response after tool execution."
            )
        return decision.message, decision.raw_response

    async def _complete(self, messages):
        """
        Execute the OpenAI chat completion with timeout handling.

        :param messages: Conversation payload conforming to OpenAI's schema.
        :returns: Extracted text content from the first completion choice.
        """
        try:
            response = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model,
                    temperature=0,
                    messages=messages,
                ),
                timeout=self._timeout,
            )
            return self._extract_content(response)
        except TimeoutError:  # pragma: no cover
            raise PlannerError(
                "OpenAI planner request timed out. Try again or disable the planner."
            )
        except Exception as exc:  # pragma: no cover - passthrough errors
            raise PlannerError(f"OpenAI planner failed: {exc}") from exc

    def _extract_content(self, response):
        """
        Convert an OpenAI response object into a normalized text payload.

        :param response: ChatCompletions response returned by OpenAI.
        :returns: Normalized string content.
        :raises PlannerError: If the response is missing message content.
        """
        choice = response.choices[0].message
        if not choice:
            raise PlannerError("Planner response did not include a message.")
        content = self._normalize_content(choice.content)
        if not content:
            raise PlannerError("Planner returned empty content.")
        return content

    @staticmethod
    def _normalize_content(content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
                else:
                    parts.append(str(item))
            return "\n".join(parts).strip()
        return str(content).strip()

    def _parse_decision(self, content: str) -> PlannerDecision:
        """
        Deserialize planner JSON into a PlannerDecision instance.

        :param content: Raw JSON emitted by the planner.
        :returns: PlannerDecision data structure.
        :raises PlannerError: If the JSON is malformed.
        """
        try:
            sanitized = content.strip()
            if sanitized.startswith("```"):
                sanitized = sanitized.strip("`")
                if sanitized.startswith("json"):
                    sanitized = sanitized[4:]
            data = json.loads(sanitized)
        except json.JSONDecodeError as exc:
            raise PlannerError(f"Planner response was not valid JSON: {content}") from exc
        action = data.get("action")
        message = data.get("message")
        tool_name = data.get("tool_name")
        arguments = data.get("arguments")
        return PlannerDecision(
            action=action,
            message=message,
            tool_name=tool_name,
            arguments=arguments,
            raw_response=content,
        )
