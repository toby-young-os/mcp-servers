# Architecture Overview

This repository is structured around three collaborating pieces that mirror a
typical MCP deployment.

1. **Server blueprints** (`mcp_math_servers.servers.__init__`)
   - `ServerBlueprint` stores the category label, factory function, summary, and
     aliases for each example server.
   - `_SERVER_BLUEPRINTS` and `_BLUEPRINT_INDEX` provide an in-process registry
     so the client can look up servers by name (or alias) without any network
     discovery step.
   - `get_blueprint("data")` returns the math data provider configuration while
     `iter_blueprints()` powers the CLI manifest listings.
2. **FastMCP server implementations** (`src/mcp_math_servers/servers/*.py`)
   - Each module maps to one MCP category:
     - `capability_discovery.py` advertises tools only.
     - `data_provider.py` executes math operations and returns JSON.
     - `prompt_helper.py` pairs results with follow-up prompts.
     - `autonomous_reasoner.py` delegates to OpenAI for end-to-end reasoning.
   - The modules document their tools and link to
     `docs/categories/<name>.md` for runnable examples.
3. **CLI + planner** (`mcp_math_servers.client.chat`,
   `mcp_math_servers.client.planner`)
   - `chat.py` parses CLI arguments, retrieves the requested blueprint,
     instantiates the FastMCP server, fetches its tool manifest, and chooses the
     appropriate handler (capability, data, prompt, autonomous, or planner).
   - When `--planner` is enabled and credentials exist, `MCPPlanner` wraps the
     OpenAI async client. Each user turn goes through `PlannerHandler`, which:
     1. Invokes the LLM with a manifest of available tools.
     2. Receives a JSON instruction (`respond` or `call_tool`).
     3. Executes at most one tool per turn, printing both the planner summary
        and the tool payload (see `docs/planner.md` for details).
   - Without the planner, manual handlers parse commands directly (e.g.,
     `add 2 3`) and call the FastMCP tool via the server’s tool manager.

## Data Flow at Runtime

1. User runs `fastmcp-math-chat --server data --planner`.
2. `chat.py` → `get_blueprint("data")` → FastMCP server instance →
   tool manifest (math_add, math_subtract, …).
3. `ChatContext` stores the blueprint, tools, CLI arguments, and optional
   planner.
4. Input loop:
   - Manual mode: parse command → build payload → `_call_tool`.
   - Planner mode: send user text to OpenAI → planner JSON → optional tool
     call → final response.
5. Results are printed in color-coded sections (user/planner/tool) when
   `colorama` is available; `--show-json` dumps raw payloads.

## Extending the Architecture

To add another server:

1. Implement it in `src/mcp_math_servers/servers/<new>.py`, mirroring the
   existing docstring style and FastMCP tool definitions.
2. Document usage in `docs/categories/<new>.md`.
3. Register it in `_SERVER_BLUEPRINTS` with aliases and summary text.
4. Update `README.md` and `docs/mcp_server_use_categories.md` if needed.
5. Provide handler logic in `chat.py` if the interaction differs from the
   existing patterns.

This architecture keeps the “registry” (blueprints) and “execution” (FastMCP
servers) separate, while the client orchestrates discovery, tool invocation, and
optional LLM planning.
