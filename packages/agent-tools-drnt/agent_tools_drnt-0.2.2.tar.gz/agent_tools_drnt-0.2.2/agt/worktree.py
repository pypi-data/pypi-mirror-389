"""Low-level Git worktree helper functions."""

import os
import subprocess
import uuid
from pathlib import Path
from typing import Optional


def get_repo_root(cwd: Optional[Path] = None) -> Path:
    """
    Get the root of the main Git repository (not worktree root).
    
    If we're in a worktree, this returns the main repository root,
    not the worktree directory itself.
    """
    if cwd is None:
        cwd = Path.cwd()
    
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
        cwd=cwd,
    )
    repo_root = Path(result.stdout.strip())
    
    # If we're in a worktree, get the main repo root
    # Check if .git is a file (worktree) or directory (main repo)
    git_path = repo_root / ".git"
    if git_path.is_file():
        # We're in a worktree, get the main repo from .git file
        git_dir_content = git_path.read_text().strip()
        if git_dir_content.startswith("gitdir: "):
            # Extract main repo path (e.g., "gitdir: ../../.git/worktrees/agent-xxxx")
            main_git_dir = Path(git_dir_content[8:].strip())
            # Resolve relative path from worktree
            if not main_git_dir.is_absolute():
                main_git_dir = (repo_root / main_git_dir).resolve()
            
            # Navigate to main repo root
            # gitdir is usually .git/worktrees/..., so go up to .git, then to repo root
            while main_git_dir.name != ".git" and main_git_dir.parent != main_git_dir:
                main_git_dir = main_git_dir.parent
            if main_git_dir.name == ".git":
                repo_root = main_git_dir.parent
    
    return repo_root


def generate_agent_id() -> str:
    """Generate a unique agent ID."""
    return f"agent-{uuid.uuid4().hex[:8]}"


def get_work_dir(root: Optional[Path] = None) -> Path:
    """Get the work directory path (.work in repo root)."""
    if root is None:
        root = get_repo_root()
    return root / ".work"


def add_worktree(root: Path, agent_id: str, base_branch: str = "main") -> tuple[Path, str]:
    """
    Add a new Git worktree for an agent.
    
    Returns:
        tuple: (worktree_path, branch_name)
    """
    work_dir = get_work_dir(root)
    work_dir.mkdir(parents=True, exist_ok=True)
    
    worktree_path = work_dir / agent_id
    branch_name = f"feat/{agent_id}"
    
    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", branch_name, base_branch],
        check=True,
        cwd=root,
    )
    
    return worktree_path, branch_name


def remove_worktree(root: Path, agent_id: str) -> None:
    """Remove a Git worktree."""
    work_dir = get_work_dir(root)
    worktree_path = work_dir / agent_id
    
    if worktree_path.exists():
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path)],
            check=True,
            cwd=root,
        )


def get_worktree_path(root: Path, agent_id: str) -> Path:
    """Get the worktree path for an agent ID."""
    work_dir = get_work_dir(root)
    return work_dir / agent_id


def list_worktrees(root: Optional[Path] = None) -> list[str]:
    """List all active agent worktree IDs."""
    if root is None:
        root = get_repo_root(Path.cwd())
    work_dir = get_work_dir(root)
    
    if not work_dir.exists():
        return []
    
    agent_ids = []
    for item in work_dir.iterdir():
        if item.is_dir() and item.name.startswith("agent-"):
            # Verify it's actually a git worktree
            if (item / ".git").exists() or (item / ".git").is_file():
                agent_ids.append(item.name)
    
    return sorted(agent_ids)


def detect_agent_id_from_cwd(cwd: Optional[Path] = None) -> Optional[str]:
    """
    Detect agent ID from current working directory.
    
    If cwd is inside a worktree (.work/agent-xxxx), return that agent ID.
    
    Returns:
        Agent ID or None if not in a worktree
    """
    if cwd is None:
        cwd = Path.cwd()
    
    cwd = cwd.resolve()
    
    # Check if we're inside .work/agent-xxxx
    # Look for .work in the path, then check if next component is agent-xxxx
    try:
        work_dir_index = cwd.parts.index(".work")
        if work_dir_index + 1 < len(cwd.parts):
            potential_agent_id = cwd.parts[work_dir_index + 1]
            if potential_agent_id.startswith("agent-"):
                # Verify it's actually a worktree by checking if .git exists
                work_dir = Path(*cwd.parts[:work_dir_index + 1])
                worktree_path = work_dir / potential_agent_id
                if worktree_path.exists() and ((worktree_path / ".git").exists() or (worktree_path / ".git").is_file()):
                    return potential_agent_id
    except ValueError:
        # .work not in path
        pass
    
    return None


def get_current_agent_id(root: Optional[Path] = None, cwd: Optional[Path] = None) -> Optional[str]:
    """
    Get the current agent ID with multiple detection strategies.
    
    Priority:
    1. Current working directory is inside a worktree (.work/agent-xxxx)
    2. Environment variable AGENT_ID (legacy support)
    3. If only one worktree exists, use that
    4. None if ambiguous
    
    This works correctly with multiple concurrent agents because:
    - Each agent runs commands from its own worktree directory
    - Detection is based on current working directory, not shared state
    
    Returns:
        Agent ID or None if ambiguous
    """
    # Strategy 1: Detect from current working directory (best for multiple agents)
    agent_id = detect_agent_id_from_cwd(cwd)
    if agent_id:
        return agent_id
    
    if root is None:
        root = get_repo_root()
    
    # Strategy 2: Environment variable (legacy support, single agent only)
    agent_id = os.environ.get("AGENT_ID")
    if agent_id:
        worktree_path = get_worktree_path(root, agent_id)
        if worktree_path.exists():
            return agent_id
    
    # Strategy 3: Auto-detect: if only one worktree exists, use it
    worktrees = list_worktrees(root)
    if len(worktrees) == 1:
        return worktrees[0]
    
    # Multiple or none - return None
    return None


def set_current_agent_id(root: Path, agent_id: str) -> None:
    """
    Set the current agent ID (legacy support, not used for detection).
    
    Note: This is kept for backward compatibility but detection is now
    based on working directory, not file state.
    """
    # No-op - we don't use file-based storage anymore to avoid conflicts
    # with multiple concurrent agents
    pass

