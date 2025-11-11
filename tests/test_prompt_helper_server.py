from __future__ import annotations

import pytest

from mcp_math_servers.servers.prompt_helper import build_server


@pytest.fixture(scope="module")
def prompt_tools(run):
    server = build_server()
    tools = run(server._tool_manager.get_tools())
    return tools


@pytest.mark.parametrize(
    ("tool_name", "kwargs", "expected"),
    [
        ("math_add_with_prompt", {"augend": 1, "addend": 4}, 5),
        ("math_subtract_with_prompt", {"minuend": 8, "subtrahend": 2}, 6),
        ("math_multiply_with_prompt", {"multiplicand": 5, "multiplier": 2}, 10),
        ("math_divide_with_prompt", {"dividend": 12, "divisor": 3}, 4),
    ],
)
def test_prompt_tools_include_next_prompt(run, prompt_tools, tool_name, kwargs, expected):
    tool = prompt_tools[tool_name]
    result = run(tool.run(kwargs))
    payload = result.structured_content
    assert payload["result"] == expected
    assert str(expected) in payload["next_prompt"]
