# Prompt-Returning Server

**Category:** Prompt-Returning / Co-Reasoning

This server executes the same math operations as the data provider but augments the response with a `next_prompt` that guides downstream reasoning. Agents can immediately feed that prompt back into an LLM to continue the workflow.

Tools: `math_add_with_prompt`, `math_subtract_with_prompt`, `math_multiply_with_prompt`, `math_divide_with_prompt`.

## Quick Demo

```bash
fastmcp-math-chat --server prompt --no-planner --show-json
```

Then run `add 5 11` to see both the structured result and the suggested prompt:

```json
{
  "operation": "addition",
  "inputs": {"augend": 5.0, "addend": 11.0},
  "result": 16.0,
  "next_prompt": "The addition result is 16.0..."
}
```
