# Autonomous Reasoning Server

**Category:** Autonomous / Server-Side Reasoning

This server delegates math word problems to an internal OpenAI call (with a heuristic fallback). Instead of returning raw data or prompts, it produces the final `reasoning_steps` and `final_answer`, so clients can surface the result directly.

Tool: `solve_math_problem` accepts a natural-language `problem` (and optional `model`).

## Quick Demo

```bash
fastmcp-math-chat --server autonomous --no-planner --show-json
```

Ask a question such as `What is the result of doubling 7 and then subtracting 3?` and you’ll see the JSON reasoning trace:

```json
{
  "problem": "...",
  "reasoning_steps": ["Double 7...", "Subtract 3..."],
  "final_answer": "11",
  "model": "gpt-4.1-mini",
  "source": "openai"
}
```
