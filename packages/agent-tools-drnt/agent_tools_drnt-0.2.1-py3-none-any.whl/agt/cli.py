"""CLI entrypoint for agt command."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

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


def cmd_start(base_branch: str = "main") -> None:
    """Start a new agent worktree."""
    root = get_repo_root(Path.cwd())
    agent_id = generate_agent_id()
    
    worktree_path, branch_name = add_worktree(root, agent_id, base_branch)
    
    # Note: No need to store agent ID - detection is based on working directory
    # This allows multiple concurrent agents to work independently
    
    safe_print(f"✅ Worktree ready: {worktree_path} (branch {branch_name})")
    print(f"AGENT_ID={agent_id}")


def cmd_run(command: list[str], agent_id: Optional[str] = None) -> None:
    """Run a command in the agent worktree."""
    root = get_repo_root(Path.cwd())
    
    # Get agent ID from argument, working directory, env var (legacy), or auto-detect
    if not agent_id:
        agent_id = get_current_agent_id(root, cwd=Path.cwd())
    
    if not agent_id:
        worktrees = list_worktrees(root)
        if not worktrees:
            err("No worktrees found. Run 'agt start' first!")
        else:
            err(
                f"Multiple worktrees found: {', '.join(worktrees)}\n"
                f"Either:\n"
                f"  - Run command from within worktree directory: cd .work/agent-xxxx\n"
                f"  - Specify agent ID: agt run --agent <id> <command>"
            )
    
    worktree_path = get_worktree_path(root, agent_id)
    
    if not worktree_path.exists():
        err(f"Worktree not found: {worktree_path}. Run 'agt start' first!")
    
    if not command:
        err("Missing command to run")
    
    # Execute command in worktree directory
    # Join command parts and run in shell to support pipes, redirects, etc.
    # Note: On Windows, shell=True uses cmd.exe, not PowerShell
    cmd_str = " ".join(command)
    try:
        subprocess.run(cmd_str, check=True, cwd=worktree_path, shell=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


def cmd_commit(message: str, agent_id: Optional[str] = None) -> None:
    """Commit changes in the agent worktree."""
    root = get_repo_root(Path.cwd())
    
    # Get agent ID from argument, working directory, env var (legacy), or auto-detect
    if not agent_id:
        agent_id = get_current_agent_id(root, cwd=Path.cwd())
    
    if not agent_id:
        worktrees = list_worktrees(root)
        if not worktrees:
            err("No worktrees found. Run 'agt start' first!")
        else:
            err(
                f"Multiple worktrees found: {', '.join(worktrees)}\n"
                f"Either:\n"
                f"  - Run command from within worktree directory: cd .work/agent-xxxx\n"
                f"  - Specify agent ID: agt commit --agent <id> <message>"
            )
    
    worktree_path = get_worktree_path(root, agent_id)
    
    if not worktree_path.exists():
        err(f"Worktree not found: {worktree_path}. Run 'agt start' first!")
    
    # Stage all changes
    subprocess.run("git add -A", shell=True, check=True, cwd=worktree_path)
    
    # Commit - use list form to avoid shell escaping issues
    subprocess.run(
        ["git", "commit", "-m", message],
        check=True,
        cwd=worktree_path,
    )
    
    safe_print("✅ Commit ready")


def cmd_push(remote: str = "origin", agent_id: Optional[str] = None) -> None:
    """Push the agent branch to remote."""
    root = get_repo_root(Path.cwd())
    
    # Get agent ID from argument, working directory, env var (legacy), or auto-detect
    if not agent_id:
        agent_id = get_current_agent_id(root, cwd=Path.cwd())
    
    if not agent_id:
        worktrees = list_worktrees(root)
        if not worktrees:
            err("No worktrees found. Run 'agt start' first!")
        else:
            err(
                f"Multiple worktrees found: {', '.join(worktrees)}\n"
                f"Either:\n"
                f"  - Run command from within worktree directory: cd .work/agent-xxxx\n"
                f"  - Specify agent ID: agt push --agent <id> [remote]"
            )
    
    worktree_path = get_worktree_path(root, agent_id)
    
    if not worktree_path.exists():
        err(f"Worktree not found: {worktree_path}. Run 'agt start' first!")
    
    # Push branch
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
    
    # Get agent ID from argument, working directory, env var (legacy), or auto-detect
    if not agent_id:
        agent_id = get_current_agent_id(root, cwd=Path.cwd())
    
    if not agent_id:
        worktrees = list_worktrees(root)
        if not worktrees:
            err("No worktrees found. Run 'agt start' first!")
        else:
            err(
                f"Multiple worktrees found: {', '.join(worktrees)}\n"
                f"Either:\n"
                f"  - Run command from within worktree directory: cd .work/agent-xxxx\n"
                f"  - Specify agent ID: agt merge --agent <id>"
            )
    
    worktree_path = get_worktree_path(root, agent_id)
    
    if not worktree_path.exists():
        err(f"Worktree not found: {worktree_path}. Run 'agt start' first!")
    
    branch_name = f"feat/{agent_id}"
    
    # Fetch latest main
    subprocess.run("git fetch origin main", shell=True, check=True, cwd=worktree_path)
    
    # Rebase onto main
    subprocess.run("git rebase origin/main", shell=True, check=True, cwd=worktree_path)
    
    # Switch to main branch in root repo
    subprocess.run("git checkout main", shell=True, check=True, cwd=root)
    
    # Fast-forward merge
    subprocess.run(
        f"git merge --ff-only {branch_name}",
        shell=True,
        check=True,
        cwd=root,
    )
    
    # Push to remote
    subprocess.run("git push origin main", shell=True, check=True, cwd=root)
    
    safe_print("✅ Branch fast-forwarded to main")


def cmd_clean(agent_id: Optional[str] = None) -> None:
    """Remove the agent worktree."""
    root = get_repo_root(Path.cwd())
    
    # Get agent ID from argument, working directory, env var (legacy), or auto-detect
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
                f"  - Specify agent ID: agt clean --agent <id>"
            )
    
    worktree_path = get_worktree_path(root, agent_id)
    
    if not worktree_path.exists():
        err(f"Worktree not found: {worktree_path}. Run 'agt start' first!")
    
    remove_worktree(root, agent_id)
    safe_print(f"✅ Worktree removed ({agent_id})")


def main() -> None:
    """Main CLI entrypoint."""
    if len(sys.argv) < 2:
        print("Usage: agt <start|run|commit|push|merge|clean|vscode> [args...]", file=sys.stderr)
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    # Parse --agent flag if present (must be before command-specific args)
    agent_id: Optional[str] = None
    if "--agent" in args:
        idx = args.index("--agent")
        if idx + 1 >= len(args):
            err("--agent requires an agent ID")
        agent_id = args[idx + 1]
        # Remove --agent and its value from args
        args = args[:idx] + args[idx + 2:]
    
    if cmd == "start":
        base_branch = args[0] if args else "main"
        cmd_start(base_branch)
    
    elif cmd == "run":
        if not args:
            err("Missing command to run")
        cmd_run(args, agent_id=agent_id)
    
    elif cmd == "commit":
        if not args:
            err('Usage: agt commit [--agent <id>] "<message>"')
        message = args[0]
        cmd_commit(message, agent_id=agent_id)
    
    elif cmd == "push":
        remote = args[0] if args else "origin"
        cmd_push(remote, agent_id=agent_id)
    
    elif cmd == "merge":
        cmd_merge(agent_id=agent_id)
    
    elif cmd == "clean":
        cmd_clean(agent_id=agent_id)
    
    elif cmd == "vscode":
        if not args or args[0] != "init":
            err('Usage: agt vscode init')
        cmd_vscode_init()
    
    else:
        err(f"Unknown subcommand: {cmd}")


if __name__ == "__main__":
    main()

