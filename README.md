# FastMCP Math Servers

Example servers built with FastMCP to illustrate the four core MCP categories: capability discovery, data-providing, prompt-returning, and autonomous reasoning. The package also includes a simple client for experimentation.

## Demo Client

Install the project (or work inside the repo with the `src` layout) and run:

```bash
fastmcp-math-demo --list        # see available scenarios
fastmcp-math-demo               # run every scenario sequentially
fastmcp-math-demo capability    # run a single scenario
```

Each scenario instantiates the relevant FastMCP server, prints its manifest, and executes a representative tool (when applicable) so you can observe the different MCP interaction patterns.

## Interactive Chat

To converse with a server in a REPL-style loop:

```bash
fastmcp-math-chat --server autonomous        # default, asks OpenAI-powered server
fastmcp-math-chat --server prompt            # simple math ops that return prompts
fastmcp-math-chat --server data --show-json  # inspect raw JSON responses
fastmcp-math-chat --server autonomous --model gpt-4.1-mini
fastmcp-math-chat --server data --planner    # let the LLM planner call tools for you
fastmcp-math-chat --server data --no-planner # fall back to manual commands
```

Use `exit` to quit, `help` for guidance, and `tools` to reprint the manifest. When a planner is available (OpenAI key loaded), the chat client automatically routes non-autonomous servers through the LLM planner so you can type natural-language requests. Disable that behavior with `--no-planner`. Without the planner, the data/prompt servers expect commands like `add 2 3` or `divide 10 5`.

> **Planner behavior:** With `--planner` enabled the client asks the LLM planner to choose a single tool call per turn, prints the planner’s decision (magenta), and then executes that tool. Multi-step instructions still require additional turns unless you use the autonomous server, which chains sub-steps inside its own tool implementation.

## OpenAI Credentials

Some scenarios (e.g., autonomous reasoning) call OpenAI. Create a `.env` file next to `pyproject.toml` with:

```bash
OPENAI_API_KEY=sk-...
```

Keys loaded via `python-dotenv`, so the demo client and servers will automatically pick them up if present. Without a key, the autonomous server falls back to a heuristic reasoner.

## Category Walkthrough

## How It All Fits Together

1. **Server blueprints** live in `src/mcp_math_servers/servers/__init__.py`. Each `ServerBlueprint` describes a FastMCP server (name/aliases, category, summary, factory function).
2. **Clients** (chat or demo) call `get_blueprint(...)`, instantiate the server via `blueprint.factory()`, and retrieve the tool metadata from FastMCP (`server._tool_manager.get_tools()`).
3. **Handlers** (capability, data, prompt, autonomous) use those tool definitions to execute commands, returning structured JSON (and optional prompts) for the user or planner.
4. **Planner mode** (optional `--planner`) asks an LLM to pick a single tool call per turn based on the tool metadata; the planner’s decision is printed in magenta before executing the tool.
5. **Autonomous server** is a special case: its tool delegates to OpenAI internally, so multi-stage reasoning happens inside that tool (requires `OPENAI_API_KEY`).

See [docs/mcp_server_use_categories.md](docs/mcp_server_use_categories.md) for a full breakdown of each category and links to the detailed guides.

- **Capability Server (Category 1)** – Lists tool schemas but never executes. Demo with `fastmcp-math-chat --server capability --no-planner`; attempted commands return the “read-only” reminder.
- **Data Server (Category 2)** – Executes math tools and returns clean JSON (`operation`, `inputs`, `result`). Try `fastmcp-math-chat --server data --no-planner --show-json` and run `add 2 3`.
- **Prompt-Returning Server (Category 3)** – Returns both the structured data and a `next_prompt` to guide downstream reasoning. Example: `fastmcp-math-chat --server prompt --no-planner --show-json` followed by `add 5 11`.
- **Autonomous Server (Category 4)** – Runs reasoning internally with OpenAI, chaining any required sub-operations in a single tool call (requires `OPENAI_API_KEY`). Example: `fastmcp-math-chat --server autonomous --no-planner --show-json` and ask “What is the result of doubling 7 and then subtracting 3?”
