from __future__ import annotations

import pytest
from fastmcp.exceptions import DisabledError

from mcp_math_servers.servers.capability_discovery import build_server


def test_capability_tools_are_registered(run):
    server = build_server()
    tools = run(server._tool_manager.get_tools())
    assert set(tools) == {
        "math_add",
        "math_subtract",
        "math_multiply",
        "math_divide",
    }


@pytest.mark.parametrize(
    "tool_name,kwargs",
    [
        ("math_add", {"augend": 1, "addend": 2}),
        ("math_subtract", {"minuend": 5, "subtrahend": 3}),
        ("math_multiply", {"multiplicand": 2, "multiplier": 4}),
        ("math_divide", {"dividend": 10, "divisor": 5}),
    ],
)
def test_capability_tools_raise(run, tool_name, kwargs):
    server = build_server()
    tools = run(server._tool_manager.get_tools())
    tool = tools[tool_name]
    with pytest.raises(DisabledError):
        run(tool.run(kwargs))
