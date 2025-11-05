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


CMD_BLOCK = {
    "agt ws new": "agt ws new",
    "agt ws run": "agt ws run \"${input:cmd}\"",
    "agt ws save": "agt ws save \"${input:msg}\"",
    "agt ws push": "agt ws push",
    "agt ws merge": "agt ws merge",
    "agt ws clean": "agt ws clean",
    "agt cfg vscode": "agt cfg vscode",
    "agt env check": "agt env check",
}


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
    data["command-runner.commands"].update(CMD_BLOCK)
    
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

