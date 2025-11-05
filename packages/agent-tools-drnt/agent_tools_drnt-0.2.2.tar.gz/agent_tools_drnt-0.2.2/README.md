# agent-tools

Worktree-based agent workflow management toolkit.

## Overview

`agent-tools` provides a Python-based CLI for managing isolated Git worktrees for agent workflows. It replaces shell scripts with a maintainable, testable Python package that can be used locally, as a submodule, or in CI/CD pipelines.

## Features

- **Isolated Worktrees**: Each agent gets its own isolated Git worktree
- **Simple CLI**: `start`, `run`, `commit`, `push`, `clean` commands
- **Manual PR Creation**: Push branch and create PR manually in GitHub UI
- **Cross-platform**: Works on Windows, Linux, and macOS
- **Installable**: Can be installed via pip or used as submodule

## Quick Start

### Installation

```bash
# From source
cd agt
uv pip install -e .  # or: pip install -e .

# Or as submodule
git submodule add -b main https://github.com/tnedr/agent-ops .tools
cd .tools/agt
uv pip install -e .  # or: pip install -e .
```

**Note**: This project follows UV Cache Workflow Guidelines. If using `uv`, ensure `UV_CACHE_DIR` is set (e.g., `E:\uv-cache` on Windows).

### Usage

```bash
# Start a new agent worktree
agt start

# Run commands in the worktree
agt run python my_script.py

# Commit changes
agt commit "feat: new feature"

# Push to remote (then open PR manually)
agt push

# Optional: cleanup after PR is merged
agt clean
```

### VS Code Integration

Generate VS Code Command Runner settings with agt commands:

```bash
agt vscode init  # Creates/updates .vscode/settings.json
```

This adds the following commands to VS Code/Cursor:
- `agt start`: Start a new agent worktree
- `agt run`: Run a command in the agent worktree (with input prompt)
- `agt commit`: Commit changes (with input prompt for message)
- `agt push`: Push branch to remote
- `agt merge`: Merge agent branch back to base
- `agt clean`: Remove agent worktree

**Usage in VS Code/Cursor:**
- Press `F1` → `Command Runner: Run...`
- Select any `agt *` command
- Or use in chat: `> run command: agt start`

**Note:** The `agt vscode init` command preserves existing commands in your `.vscode/settings.json`, so you can combine it with other Command Runner configurations.

## Documentation

- [Quick Start Guide](docs/quick_start.md)
- [CLI Reference](docs/cli_reference.md)
- [Architecture](docs/architecture.md)
- [Changelog](docs/CHANGELOG.md)

## Examples

See the [examples/](examples/) directory for:
- `demo_local.sh`: Local workflow example
- `demo_action.yml`: GitHub Actions workflow example

## Development

### Setup

```bash
cd agt
uv pip install -e ".[dev]"  # or: pip install -e ".[dev]"
```

**Note**: Uses UV Cache Workflow - minimal `.venv`, global cache.

### Run Tests

```bash
uv run pytest tests/ -v  # or: pytest tests/ -v
```

### Run Linter

```bash
uv run ruff check .  # or: ruff check .
```

## Project Structure

```
agt/
├── __init__.py          # Package metadata
├── __main__.py          # Allows `python -m agt`
├── worktree.py          # Low-level Git worktree operations
├── cli.py               # CLI entrypoint and command handlers
└── pyproject.toml        # Package configuration

bin/
└── agt                  # Standalone entrypoint script

docs/                    # Documentation
tests/                   # Test suite
examples/                # Usage examples
.github/                 # CI/CD workflows and actions
```

## License

MIT

