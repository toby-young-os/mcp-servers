# Data-Providing Server

**Category:** Data-Providing / Context-Enriching

Each math tool executes directly and returns structured JSON (`operation`, `inputs`, `result`). There is no reasoning prompt—just deterministic data for other components to consume.

## Quick Demo

```bash
fastmcp-math-chat --server data --no-planner --show-json
```

Commands like `add 2 3` produce:

```json
{
  "operation": "addition",
  "inputs": {"augend": 2.0, "addend": 3.0},
  "result": 5.0
}
```
