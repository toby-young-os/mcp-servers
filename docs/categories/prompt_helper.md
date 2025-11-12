# Prompt-Returning Server

**Category:** Prompt-Returning / Co-Reasoning

Each tool behaves like the data server but augments the response with a `next_prompt` that guides downstream reasoning.

## Quick Demo

```bash
fastmcp-math-chat --server prompt --no-planner --show-json
```

`add 5 11` returns the structured data plus guidance on how to use it in the next reasoning step.

## Sample Request and Response

Request:

```json
{
  "augend": 5,
  "addend": 11
}
```

Response:

```json
{
  "operation": "addition",
  "inputs": {"augend": 5.0, "addend": 11.0},
  "result": 16.0,
  "next_prompt": "The addition result is 16.0. Inputs: {'augend': 5.0, 'addend': 11.0}. Incorporate this numeric value into your next reasoning step..."
}
```
