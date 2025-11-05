"""CLI entrypoint for agt command."""

import os
import subprocess
import sys
import warnings
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

# Alias mapping: (old_command,) -> (domain, action)
ALIASES = {
    ("start",): ("ws", "new"),
    ("commit",): ("ws", "save"),
    ("run",): ("ws", "run"),
    ("push",): ("ws", "push"),
    ("merge",): ("ws", "merge"),
    ("clean",): ("ws", "clean"),
    ("vscode", "init"): ("cfg", "vscode"),
}


def _resolve_alias(argv: list[str]) -> Tuple[str, str, list[str]]:
    """Resolve alias to domain and action, return (domain, action, remaining_args)."""
    if not argv:
        return None, None, []
    
    # Check for two-word aliases first (e.g., "vscode init")
    if len(argv) >= 2:
        key = tuple(argv[:2])
        if key in ALIASES:
            domain, action = ALIASES[key]
            warnings.warn(
                f"'{' '.join(key)}' is deprecated, use 'agt {domain} {action}' instead",
                DeprecationWarning,
                stacklevel=2,
            )
            return domain, action, argv[2:]
    
    # Check for single-word aliases
    key = (argv[0],)
    if key in ALIASES:
        domain, action = ALIASES[key]
        warnings.warn(
            f"'{argv[0]}' is deprecated, use 'agt {domain} {action}' instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return domain, action, argv[1:]
    
    # No alias, treat first arg as domain
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
    else:
        err(f"Unknown env action: {action}. Available: check, python")


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


def main() -> None:
    """Main CLI entrypoint."""
    if len(sys.argv) < 2:
        print(
            "Usage: agt <domain> <action> [args...]\n"
            "Domains: ws (workspace), cfg (config), task (preview), env (environment)\n"
            "See 'agt <domain> --help' for domain-specific help",
            file=sys.stderr,
        )
        sys.exit(1)
    
    # Resolve aliases and get domain/action
    domain, action, rest_args = _resolve_alias(sys.argv[1:])
    
    if domain is None or action is None:
        err("Invalid command. Use 'agt <domain> <action>' or legacy aliases.")
    
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
        err(f"Unknown domain: {domain}. Available: ws, cfg, task, env")


if __name__ == "__main__":
    main()
