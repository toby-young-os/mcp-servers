# Prompt-Returning Server

**Category:** Prompt-Returning / Co-Reasoning

Each tool behaves like the data server but augments the response with a `next_prompt` that guides downstream reasoning.

## Quick Demo

```bash
fastmcp-math-chat --server prompt --no-planner --show-json
```

`add 5 11` returns the structured data plus guidance on how to use it in the next reasoning step.
