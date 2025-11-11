# Capability Discovery Server

**Category:** Capability Discovery / Tool Registration

The capability server only advertises tool schemas and never executes the corresponding operations. Its purpose is to expose a manifest that planners or agents can inspect before deciding which execution-oriented server to call. Attempting to execute a tool results in a `DisabledError` reminding the user to use another server.

## Quick Demo

```bash
fastmcp-math-chat --server capability --no-planner
```

Typing commands such as `add 2 3` will simply remind you that the registry is read-only, which illustrates category 1 of the MCP taxonomy.
