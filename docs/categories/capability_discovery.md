# Capability Discovery Server

**Category:** Capability Discovery / Tool Registration

This server only advertises tool schemas; it never executes the operations. A planner can inspect the manifest to learn which math tools exist before calling execution-oriented servers.

## Quick Demo

```bash
fastmcp-math-chat --server capability --no-planner
```

Typing commands like `add 2 3` results in a reminder that the registry is read-only, illustrating Category 1 behavior.
