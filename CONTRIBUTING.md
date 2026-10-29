# Contributing

Thanks for helping. Small pull requests are easiest to review.

## Development setup

```bash
git clone https://github.com/nicoleyangcoding/todo-age
cd todo-age
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
```

Tests build throwaway git repositories with fixed commit dates, so they run offline.

## Guidelines

- No runtime dependencies beyond Python and git.
- Call git with argument lists, never through a shell.
- Keep the default output short enough to read at a glance.
