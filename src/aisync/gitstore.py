from __future__ import annotations

from pathlib import Path

from .deps import require_tool, run
from .errors import GitError


def git(cmd: list[str], repo: Path):
    git_bin = require_tool("git", "Install Git first.")
    return run([git_bin, *cmd], cwd=repo)


def require_git_repository(repo: Path) -> None:
    if not (repo / ".git").exists():
        raise GitError(
            "Sync repository is not a Git repository.",
            why="AIsync stores encrypted packages in Git, so the sync repo must be initialized first.",
            next_action="Run: aisync --repo <repo> init",
        )


def init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    if not (repo / ".git").exists():
        result = git(["init"], repo)
        if result.returncode != 0:
            raise GitError("git init failed.", why=result.stderr.strip(), next_action="Check repository permissions.")


def has_remote(repo: Path) -> bool:
    result = git(["remote"], repo)
    return result.returncode == 0 and bool(result.stdout.strip())


def require_remote(repo: Path) -> None:
    require_git_repository(repo)
    if not has_remote(repo):
        raise GitError(
            "No git remote configured.",
            why="AIsync v0.1 expects a private Git remote for encrypted package storage.",
            next_action="Add a private remote, for example: git remote add origin git@github.com:USER/aisync-repo.git",
        )


def commit_and_push(repo: Path, message: str, *, push: bool = True) -> str | None:
    require_git_repository(repo)
    for args in (["add", "vault", "manifests", "profiles", "recipients.txt", ".gitignore"],):
        result = git(args, repo)
        if result.returncode != 0:
            raise GitError("git add failed.", why=result.stderr.strip(), next_action="Check the sync repository.")

    diff = git(["diff", "--cached", "--quiet"], repo)
    if diff.returncode == 0:
        return None

    result = git(["commit", "-m", message], repo)
    if result.returncode != 0:
        raise GitError("git commit failed.", why=result.stderr.strip(), next_action="Check git user.name and user.email.")

    rev = git(["rev-parse", "--short", "HEAD"], repo)
    commit = rev.stdout.strip() if rev.returncode == 0 else None

    if push:
        require_remote(repo)
        push_result = git(["push"], repo)
        if push_result.returncode != 0:
            raise GitError("git push failed.", why=push_result.stderr.strip(), next_action="Check network and Git credentials.")
    return commit


def pull(repo: Path) -> None:
    require_remote(repo)
    result = git(["pull", "--ff-only"], repo)
    if result.returncode != 0:
        raise GitError("git pull failed.", why=result.stderr.strip(), next_action="Resolve remote/local divergence first.")
