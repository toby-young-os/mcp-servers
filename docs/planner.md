# Planner Usage Guide

The chat client includes an optional planner mode (`--planner`) that routes natural-language questions through an LLM before invoking a tool. Use this when

- you want to type free-form requests (e.g., "add seven to 4") and let the planner pick the right tool from the registry.
- you are working with the data or prompt-returning servers and want natural-language convenience.

## How It Works

1. The chat client fetches tool metadata from the selected server (names, descriptions, JSON schemas).
2. If `--planner` is enabled, the client sends your question plus that metadata to the LLM planner.
3. The planner returns **one** action per turn (`respond` or `call_tool`). The chat client prints this decision in magenta and executes the tool if requested.
4. Tool results or planner responses are printed afterward for you to review.

```bash
fastmcp-math-chat --server data --planner --show-json
```

## Limitations

- The current planner prompt asks for a **single tool invocation per turn**. If you ask for multi-step instructions ("add then divide"), you'll need to provide each step across separate turns unless you use the autonomous server.
- The planner adds latency (two LLM calls: planner + tool), so if you already provide structured commands (`add 2 3`) you can disable it with `--no-planner`.
- The autonomous server already handles multi-step reasoning internally, so combining it with the planner offers little benefit.

## Autonomous Server Note

The autonomous tool (`solve_math_problem`) delegates to OpenAI internally, chaining sub-steps on its own. Using the planner on top of the autonomous server adds extra round-trips without improving results. Prefer planner mode for the capability/data/prompt servers, and run the autonomous server directly when you need internal reasoning.
