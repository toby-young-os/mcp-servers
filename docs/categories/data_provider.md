# Data-Providing Server

**Category:** Data-Providing / Context-Enriching

This server executes math tools and returns a structured JSON payload with `operation`, `inputs`, and `result`. There is no reasoning prompt—just deterministic data that other tools or planners can consume when reasoning about the next step.

Tools: `math_add`, `math_subtract`, `math_multiply`, `math_divide`. Each expects two floats (named arguments) and emits a deterministic result.

## Quick Demo (no planner)

```bash
fastmcp-math-chat --server data --no-planner --show-json
```

At the prompt enter commands like `add 2 3`, `subtract 5 1`, etc. The REPL prints structured JSON such as:

```json
{
  "operation": "addition",
  "inputs": {"augend": 2.0, "addend": 3.0},
  "result": 5.0
}
```
