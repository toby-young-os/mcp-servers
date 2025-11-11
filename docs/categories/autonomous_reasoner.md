# Autonomous Reasoning Server

**Category:** Autonomous / Server-Side Reasoning

This server delegates math word problems to OpenAI (with a heuristic fallback), returning both `reasoning_steps` and the final answer so clients can surface the result directly.

## Quick Demo

```bash
fastmcp-math-chat --server autonomous --no-planner --show-json
```

Ask “What is the result of doubling 7 and then subtracting 3?” to see the OpenAI-produced reasoning trace.
