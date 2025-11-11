from __future__ import annotations

import os

import pytest

from mcp_math_servers.servers.autonomous_reasoner import build_server


@pytest.fixture(scope="module")
def autonomous_tool(run):
    server = build_server()
    tools = run(server._tool_manager.get_tools())
    return tools["solve_math_problem"]


def test_autonomous_reasoner_returns_reasoning(run, autonomous_tool):
    result = run(
        autonomous_tool.run(
            {
                "problem": "If you double 3 and add 1, what do you get?",
            }
        )
    )
    payload = result.structured_content
    assert payload["problem"].startswith("If you double 3")
    assert "final_answer" in payload
    assert "reasoning_steps" in payload
    assert payload["source"] in {"fallback", "openai"}


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY to hit OpenAI backend.",
)
def test_autonomous_reasoner_uses_openai_when_key_present(run, autonomous_tool):
    result = run(
        autonomous_tool.run(
            {
                "problem": "What is 10 plus 5 minus 3?",
            }
        )
    )
    payload = result.structured_content
    assert payload["source"] == "openai"
