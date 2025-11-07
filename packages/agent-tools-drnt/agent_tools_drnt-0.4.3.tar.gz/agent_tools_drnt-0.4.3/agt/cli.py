"""CLI entrypoint for agt command."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from agt.vscode import cmd_vscode_init
from agt.worktree import (
    add_worktree,
    generate_agent_id,
    get_current_agent_id,
    get_repo_root,
    get_worktree_path,
    list_worktrees,
    remove_worktree,
)

def _parse_command(argv: list[str]) -> Tuple[Optional[str], Optional[str], list[str]]:
    """Parse domain and action from argv, return (domain, action, remaining_args)."""
    if not argv:
        return None, None, []
    
    if len(argv) < 2:
        return None, None, argv
    
    return argv[0], argv[1], argv[2:]


def safe_print(msg: str, file=sys.stdout) -> None:
    """Print message with ASCII fallback for Unicode characters."""
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe characters
        msg = msg.replace("✅", "[OK]")
        msg = msg.replace("🚀", "[PUSHED]")
        msg = msg.replace("❌", "[ERROR]")
        print(msg, file=file)


def err(msg: str) -> None:
    """Print error and exit."""
    safe_print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def _parse_agent_flag(args: list[str]) -> Tuple[Optional[str], list[str]]:
    """Parse --agent flag from args, return (agent_id, remaining_args)."""
    agent_id: Optional[str] = None
    if "--agent" in args:
        idx = args.index("--agent")
        if idx + 1 >= len(args):
            err("--agent requires an agent ID")
        agent_id = args[idx + 1]
        # Remove --agent and its value from args
        args = args[:idx] + args[idx + 2:]
    return agent_id, args


def ws_dispatch(action: str, args: list[str]) -> None:
    """Dispatch workspace (worktree) commands."""
    agent_id, args = _parse_agent_flag(args)
    
    if action == "new":
        base_branch = args[0] if args else "main"
        cmd_start(base_branch)
    
    elif action == "run":
        if not args:
            err("Missing command to run")
        cmd_run(args, agent_id=agent_id)
    
    elif action == "save":
        if not args:
            err('Usage: agt ws save [--agent <id>] "<message>"')
        message = args[0]
        cmd_commit(message, agent_id=agent_id)
    
    elif action == "push":
        remote = args[0] if args else "origin"
        cmd_push(remote, agent_id=agent_id)
    
    elif action == "merge":
        cmd_merge(agent_id=agent_id)
    
    elif action == "clean":
        cmd_clean(agent_id=agent_id)
    
    else:
        err(f"Unknown workspace action: {action}. Available: new, run, save, push, merge, clean")


def cfg_dispatch(action: str, args: list[str]) -> None:
    """Dispatch configuration commands."""
    if action == "vscode":
        if args and args[0] != "init":
            err('Usage: agt cfg vscode')
        cmd_vscode_init()
    else:
        err(f"Unknown config action: {action}. Available: vscode")


def task_dispatch(action: str, args: list[str]) -> None:
    """Dispatch task management commands (preview - not yet implemented)."""
    available_actions = ["list", "add", "pick", "done"]
    if action not in available_actions:
        err(f"Unknown task action: {action}. Available: {', '.join(available_actions)}")
    
    safe_print("🟡 Task module is a preview; functionality not yet implemented.", file=sys.stderr)
    safe_print(f"Command: agt task {action} {' '.join(args) if args else ''}", file=sys.stderr)
    sys.exit(0)


def env_dispatch(action: str, args: list[str]) -> None:
    """Dispatch environment commands."""
    if action == "check":
        # Simple environment check
        python_version = sys.version_info
        safe_print(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        safe_print(f"Platform: {sys.platform}")
    elif action == "python":
        # Run python with args
        if not args:
            err("Usage: agt env python <script> [args...]")
        subprocess.run([sys.executable] + args, check=True)
    elif action == "time":
        # Get current UTC timestamp
        import datetime
        print(datetime.datetime.now(datetime.UTC).isoformat())
    elif action == "audit":
        # Project audit: find empty files, large files, duplicates
        cmd_env_audit(args)
    else:
        err(f"Unknown env action: {action}. Available: check, python, time, audit")


def cmd_env_audit(args: list[str]) -> None:
    """Run project audit: find empty files, large files, and duplicates."""
    # Parse output path (optional)
    output_path = Path("reports/project_audit_report.json")
    exclude_dirs = {".git", "docs_refactor"}
    
    if args:
        output_path = Path(args[0])
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    safe_print("INFO: Starting project audit...")
    safe_print("INFO: Scanning files (excluding .git and docs_refactor)...")
    
    report = {
        "empty_files": [],
        "large_files": [],
        "duplicate_hashes": {},
        "summary": {"total_files": 0, "total_size_kb": 0}
    }
    
    hashes = {}
    processed = 0
    
    root_path = Path.cwd()
    
    for root, dirs, files in os.walk(root_path):
        # Skip excluded directories
        rel_root = Path(root).relative_to(root_path)
        if any(part in exclude_dirs for part in rel_root.parts):
            # Remove from dirs to prevent walking into them
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            continue
        
        # Log progress
        if processed % 1000 == 0 and processed > 0:
            safe_print(f"INFO: Processed {processed} files... (current: {rel_root})")
        
        for f in files:
            path = Path(root) / f
            try:
                size = path.stat().st_size
                report["summary"]["total_files"] += 1
                report["summary"]["total_size_kb"] += size / 1024
                processed += 1
                
                # Check for empty files
                if size == 0:
                    report["empty_files"].append(str(path.relative_to(root_path)))
                
                # Check for large files (>10MB)
                if size > 10_000_000:
                    report["large_files"].append({
                        "path": str(path.relative_to(root_path)),
                        "size_mb": round(size / 1_000_000, 2)
                    })
                
                # Calculate hash for duplicate detection (first 8KB)
                try:
                    with open(path, "rb") as fh:
                        h = hashlib.md5(fh.read(8192)).hexdigest()
                        rel_path = str(path.relative_to(root_path))
                        hashes.setdefault(h, []).append(rel_path)
                except (IOError, OSError):
                    # Skip files that can't be read
                    pass
                    
            except (OSError, PermissionError):
                # Silently skip files that can't be accessed
                pass
    
    safe_print(f"INFO: Finished scanning. Total files processed: {processed}")
    safe_print("INFO: Analyzing duplicates...")
    
    # Find duplicates (files with same hash)
    report["duplicate_hashes"] = {k: v for k, v in hashes.items() if len(v) > 1}
    
    safe_print(f"INFO: Found {len(report['empty_files'])} empty files")
    safe_print(f"INFO: Found {len(report['large_files'])} large files (>10MB)")
    safe_print(f"INFO: Found {len(report['duplicate_hashes'])} duplicate file groups")
    
    # Write report
    safe_print(f"INFO: Writing report to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(report, out, indent=2)
    
    safe_print(f"SUCCESS: Project audit report saved to {output_path}")
    safe_print(f"SUMMARY: {report['summary']['total_files']} files, {report['summary']['total_size_kb']/1024:.2f} MB total")


def cmd_start(base_branch: str = "main") -> None:
    """Start a new agent worktree."""
    root = get_repo_root(Path.cwd())
    agent_id = generate_agent_id()
    
    worktree_path, branch_name = add_worktree(root, agent_id, base_branch)
    
    safe_print(f"✅ Worktree ready: {worktree_path} (branch {branch_name})")
    print(f"AGENT_ID={agent_id}")


def cmd_run(command: list[str], agent_id: Optional[str] = None) -> None:
    """Run a command in the agent worktree."""
    root = get_repo_root(Path.cwd())
    
    if not agent_id:
        agent_id = get_current_agent_id(root, cwd=Path.cwd())
    
    if not agent_id:
        worktrees = list_worktrees(root)
        if not worktrees:
            err("No worktrees found. Run 'agt ws new' first!")
        else:
            err(
                f"Multiple worktrees found: {', '.join(worktrees)}\n"
                f"Either:\n"
                f"  - Run command from within worktree directory: cd .work/agent-xxxx\n"
                f"  - Specify agent ID: agt ws run --agent <id> <command>"
            )
    
    worktree_path = get_worktree_path(root, agent_id)
    
    if not worktree_path.exists():
        err(f"Worktree not found: {worktree_path}. Run 'agt ws new' first!")
    
    if not command:
        err("Missing command to run")
    
    cmd_str = " ".join(command)
    try:
        subprocess.run(cmd_str, check=True, cwd=worktree_path, shell=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


def cmd_commit(message: str, agent_id: Optional[str] = None) -> None:
    """Commit changes in the agent worktree."""
    root = get_repo_root(Path.cwd())
    
    if not agent_id:
        agent_id = get_current_agent_id(root, cwd=Path.cwd())
    
    if not agent_id:
        worktrees = list_worktrees(root)
        if not worktrees:
            err("No worktrees found. Run 'agt ws new' first!")
        else:
            err(
                f"Multiple worktrees found: {', '.join(worktrees)}\n"
                f"Either:\n"
                f"  - Run command from within worktree directory: cd .work/agent-xxxx\n"
                f"  - Specify agent ID: agt ws save --agent <id> <message>"
            )
    
    worktree_path = get_worktree_path(root, agent_id)
    
    if not worktree_path.exists():
        err(f"Worktree not found: {worktree_path}. Run 'agt ws new' first!")
    
    subprocess.run("git add -A", shell=True, check=True, cwd=worktree_path)
    subprocess.run(
        ["git", "commit", "-m", message],
        check=True,
        cwd=worktree_path,
    )
    
    safe_print("✅ Commit ready")


def cmd_push(remote: str = "origin", agent_id: Optional[str] = None) -> None:
    """Push the agent branch to remote."""
    root = get_repo_root(Path.cwd())
    
    if not agent_id:
        agent_id = get_current_agent_id(root, cwd=Path.cwd())
    
    if not agent_id:
        worktrees = list_worktrees(root)
        if not worktrees:
            err("No worktrees found. Run 'agt ws new' first!")
        else:
            err(
                f"Multiple worktrees found: {', '.join(worktrees)}\n"
                f"Either:\n"
                f"  - Run command from within worktree directory: cd .work/agent-xxxx\n"
                f"  - Specify agent ID: agt ws push --agent <id> [remote]"
            )
    
    worktree_path = get_worktree_path(root, agent_id)
    
    if not worktree_path.exists():
        err(f"Worktree not found: {worktree_path}. Run 'agt ws new' first!")
    
    subprocess.run(
        f"git push -u {remote} HEAD",
        shell=True,
        check=True,
        cwd=worktree_path,
    )
    
    safe_print("🚀 Pushed to remote; open a PR in the UI if needed")


def cmd_merge(agent_id: Optional[str] = None) -> None:
    """Merge agent branch into main (fast-forward only)."""
    root = get_repo_root(Path.cwd())
    
    if not agent_id:
        agent_id = get_current_agent_id(root, cwd=Path.cwd())
    
    if not agent_id:
        worktrees = list_worktrees(root)
        if not worktrees:
            err("No worktrees found. Run 'agt ws new' first!")
        else:
            err(
                f"Multiple worktrees found: {', '.join(worktrees)}\n"
                f"Either:\n"
                f"  - Run command from within worktree directory: cd .work/agent-xxxx\n"
                f"  - Specify agent ID: agt ws merge --agent <id>"
            )
    
    worktree_path = get_worktree_path(root, agent_id)
    
    if not worktree_path.exists():
        err(f"Worktree not found: {worktree_path}. Run 'agt ws new' first!")
    
    branch_name = f"feat/{agent_id}"
    
    subprocess.run("git fetch origin main", shell=True, check=True, cwd=worktree_path)
    subprocess.run("git rebase origin/main", shell=True, check=True, cwd=worktree_path)
    subprocess.run("git checkout main", shell=True, check=True, cwd=root)
    subprocess.run(
        f"git merge --ff-only {branch_name}",
        shell=True,
        check=True,
        cwd=root,
    )
    subprocess.run("git push origin main", shell=True, check=True, cwd=root)
    
    safe_print("✅ Branch fast-forwarded to main")


def cmd_clean(agent_id: Optional[str] = None) -> None:
    """Remove the agent worktree."""
    root = get_repo_root(Path.cwd())
    
    if not agent_id:
        agent_id = get_current_agent_id(root, cwd=Path.cwd())
    
    if not agent_id:
        worktrees = list_worktrees(root)
        if not worktrees:
            err("No worktrees found. Nothing to clean.")
        else:
            err(
                f"Multiple worktrees found: {', '.join(worktrees)}\n"
                f"Either:\n"
                f"  - Run command from within worktree directory: cd .work/agent-xxxx\n"
                f"  - Specify agent ID: agt ws clean --agent <id>"
            )
    
    worktree_path = get_worktree_path(root, agent_id)
    
    if not worktree_path.exists():
        err(f"Worktree not found: {worktree_path}. Run 'agt ws new' first!")
    
    remove_worktree(root, agent_id)
    safe_print(f"✅ Worktree removed ({agent_id})")


def show_help() -> None:
    """Show help information."""
    from agt import __version__
    help_text = f"""
agent-tools-drnt v{__version__} - Worktree-based agent workflow management

USAGE:
    agt <domain> <action> [args...]

DOMAINS:
    ws          Workspace (Git worktree) operations
    cfg         Configuration commands
    task        Task management (preview - not yet implemented)
    env         Environment diagnostics

WORKSPACE (ws) COMMANDS:
    agt ws new [base-branch]
        Create a new isolated agent worktree.
        Example: agt ws new develop

    agt ws run <command> [--agent <id>]
        Run a command in the agent worktree.
        Example: agt ws run "pytest -q"

    agt ws save "<message>" [--agent <id>]
        Commit all changes in the agent worktree.
        Example: agt ws save "feat: add new feature"

    agt ws push [remote] [--agent <id>]
        Push the agent branch to remote repository.
        Example: agt ws push origin

    agt ws merge [--agent <id>]
        Merge agent branch back to main (fast-forward only).

    agt ws clean [--agent <id>]
        Remove the agent worktree after PR is merged.

CONFIG (cfg) COMMANDS:
    agt cfg vscode
        Generate VS Code Command Runner settings with agt commands.

ENVIRONMENT (env) COMMANDS:
    agt env check
        Show environment information (Python version, platform).

    agt env python <script> [args...]
        Run a Python script with the system Python.

    agt env time
        Get current UTC timestamp (ISO format).

    agt env audit [output-path]
        Run project audit: find empty files, large files (>10MB), and duplicates.
        Outputs JSON report (default: reports/project_audit_report.json).

TASK (task) COMMANDS (Preview):
    agt task list [--status STATUS]
        List tasks (not yet implemented).

    agt task add <id> <description>
        Add a new task (not yet implemented).

    agt task pick <id> [--agent AGENT_ID]
        Pick a task to work on (not yet implemented).

    agt task done <id>
        Mark a task as done (not yet implemented).

OPTIONS:
    --version, -v    Show version information
    --help, -h       Show this help message

EXAMPLES:
    # Complete workflow
    agt ws new                    # Create worktree
    agt ws run "pytest -q"        # Run tests
    agt ws save "feat: tests"     # Commit changes
    agt ws push                   # Push to remote
    agt cfg vscode                # Setup VS Code integration
    agt ws clean                  # Cleanup after merge

For more information, see: https://github.com/tnedr/agent-ops
"""
    safe_print(help_text.strip())


def main() -> None:
    """Main CLI entrypoint."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    # Check for version flag
    if sys.argv[1] in ["--version", "-v"]:
        from agt import __version__
        print(f"agent-tools-drnt {__version__}")
        sys.exit(0)
    
    # Check for help flag
    if sys.argv[1] in ["--help", "-h", "help"]:
        show_help()
        sys.exit(0)
    
    # Parse domain and action
    domain, action, rest_args = _parse_command(sys.argv[1:])
    
    if domain is None or action is None:
        err("Invalid command. Use 'agt <domain> <action>'.\nUse 'agt --help' for help.")
    
    # Dispatch to domain handlers
    if domain == "ws":
        ws_dispatch(action, rest_args)
    elif domain == "cfg":
        cfg_dispatch(action, rest_args)
    elif domain == "task":
        task_dispatch(action, rest_args)
    elif domain == "env":
        env_dispatch(action, rest_args)
    else:
        err(f"Unknown domain: {domain}. Available: ws, cfg, task, env\nUse 'agt --help' for help.")


if __name__ == "__main__":
    main()
