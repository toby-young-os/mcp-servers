from __future__ import annotations

import pytest

from mcp_math_servers.servers.data_provider import build_server


@pytest.fixture(scope="module")
def data_tools(run):
    server = build_server()
    tools = run(server._tool_manager.get_tools())
    return tools


@pytest.mark.parametrize(
    ("tool_name", "kwargs", "expected"),
    [
        ("math_add", {"augend": 2, "addend": 3}, 5),
        ("math_subtract", {"minuend": 7, "subtrahend": 4}, 3),
        ("math_multiply", {"multiplicand": 6, "multiplier": 3}, 18),
        ("math_divide", {"dividend": 9, "divisor": 3}, 3),
    ],
)
def test_data_tools_return_structured_results(run, data_tools, tool_name, kwargs, expected):
    tool = data_tools[tool_name]
    result = run(tool.run(kwargs))
    payload = result.structured_content
    assert payload["operation"]
    assert payload["inputs"]
    assert payload["result"] == expected
