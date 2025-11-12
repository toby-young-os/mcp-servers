# Setup Guide

## Python Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

Editable install with dev extras (pytest, ruff, etc.):

```bash
pip install -e '.[dev]'
```

For runtime only, you can use `pip install -e .`.

## Environment Variables

Create a `.env` file (or export variables) next to `pyproject.toml`:

```bash
OPENAI_API_KEY=sk-...
```

`OPENAI_API_KEY` is required for planner mode and the autonomous reasoning server. `python-dotenv` loads `.env` automatically when you run the clients.

## Running Tests

```bash
pytest tests
```

## Linting (optional)

```bash
ruff check .
```

## CLI Examples

Chat client:

```bash
fastmcp-math-chat --server data --no-planner --show-json
fastmcp-math-chat --server prompt --planner --show-json
fastmcp-math-chat --server autonomous --no-planner --show-json
```

Demo scenarios:

```bash
fastmcp-math-demo --list
fastmcp-math-demo data
```

Planner-specific guidance lives in [docs/planner.md](planner.md).
