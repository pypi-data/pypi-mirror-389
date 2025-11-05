"""VS Code integration for agent-tools."""

import json
import sys
from pathlib import Path


def safe_print(msg: str, file=sys.stdout) -> None:
    """Print message with ASCII fallback for Unicode characters."""
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe characters
        msg = msg.replace("✅", "[OK]")
        msg = msg.replace("⚠️", "[WARN]")
        print(msg, file=file)


# Command definitions with descriptions for VS Code Command Runner
CMD_DEFINITIONS = {
    "agt ws new": {
        "command": "agt ws new",
        "description": "Create a new isolated agent worktree (equivalent to 'agt start')"
    },
    "agt ws run": {
        "command": "agt ws run \"${input:cmd}\"",
        "description": "Run a command in the agent worktree (equivalent to 'agt run')"
    },
    "agt ws save": {
        "command": "agt ws save \"${input:msg}\"",
        "description": "Commit all changes in the agent worktree (equivalent to 'agt commit')"
    },
    "agt ws push": {
        "command": "agt ws push",
        "description": "Push the agent branch to remote repository (equivalent to 'agt push')"
    },
    "agt ws merge": {
        "command": "agt ws merge",
        "description": "Merge agent branch back to main (fast-forward only, equivalent to 'agt merge')"
    },
    "agt ws clean": {
        "command": "agt ws clean",
        "description": "Remove the agent worktree after PR is merged (equivalent to 'agt clean')"
    },
    "agt cfg vscode": {
        "command": "agt cfg vscode",
        "description": "Generate VS Code Command Runner settings with agt commands"
    },
    "agt env check": {
        "command": "agt env check",
        "description": "Show environment information (Python version, platform)"
    },
    "time.now": {
        "command": "python ${workspaceFolder}/.tools/scripts/current_time.py",
        "description": "Get current UTC timestamp"
    },
}

# For backward compatibility, also create simple command mapping
CMD_BLOCK = {name: defn["command"] for name, defn in CMD_DEFINITIONS.items()}


def cmd_vscode_init() -> None:
    """Generate .vscode/settings.json with agt commands."""
    root = Path.cwd()
    vscode_dir = root / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    
    settings = vscode_dir / "settings.json"
    
    # Load existing settings or create new
    data = {}
    if settings.exists():
        try:
            content = settings.read_text()
            if content.strip():
                data = json.loads(content)
        except json.JSONDecodeError:
            safe_print(
                f"⚠️  Warning: {settings} contains invalid JSON. "
                "Creating new file.",
                file=sys.stderr
            )
            data = {}
    
    # Initialize command-runner.commands if missing
    if "command-runner.commands" not in data:
        data["command-runner.commands"] = {}
    
    # Update with agt commands (preserve existing commands)
    # Convert definitions to Command Runner format (supports description field)
    for cmd_name, cmd_def in CMD_DEFINITIONS.items():
        # Command Runner supports both string (simple) and object (with description) formats
        # We'll use object format if description is available
        if isinstance(data["command-runner.commands"].get(cmd_name), str):
            # Update existing string command to object format
            data["command-runner.commands"][cmd_name] = {
                "command": cmd_def["command"],
                "description": cmd_def["description"]
            }
        else:
            # Add new command with description
            data["command-runner.commands"][cmd_name] = {
                "command": cmd_def["command"],
                "description": cmd_def["description"]
            }
    
    # Add input definitions if missing
    if "command-runner.inputs" not in data:
        data["command-runner.inputs"] = {}
    
    # Add input for agt ws run command
    if "cmd" not in data["command-runner.inputs"]:
        data["command-runner.inputs"]["cmd"] = {
            "type": "promptString",
            "description": "Command to run in agent worktree"
        }
    
    # Add input for agt ws save command
    if "msg" not in data["command-runner.inputs"]:
        data["command-runner.inputs"]["msg"] = {
            "type": "promptString",
            "description": "Commit message"
        }
    
    # Write updated settings
    settings.write_text(json.dumps(data, indent=2) + "\n")
    safe_print(f"✅ {settings} updated with agt commands")

