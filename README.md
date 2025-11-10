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

### OpenAI Credentials

Some scenarios (e.g., autonomous reasoning) call OpenAI. Create a `.env` file next to `pyproject.toml` with:

```bash
OPENAI_API_KEY=sk-...
```

Keys loaded via `python-dotenv`, so the demo client and servers will automatically pick them up if present. Without a key, the autonomous server falls back to a heuristic reasoner.
