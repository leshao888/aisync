from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .deps import require_tool, run
from .errors import GitError


@dataclass(frozen=True)
class ConflictStatus:
    state: str
    branch: str | None = None
    upstream: str | None = None
    local: str | None = None
    remote: str | None = None
    base: str | None = None
    dirty: bool = False
    details: str | None = None

    @property
    def has_conflict(self) -> bool:
        return self.state in {"behind", "diverged", "fetch-failed"}


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


def current_branch(repo: Path) -> str:
    result = git(["rev-parse", "--abbrev-ref", "HEAD"], repo)
    if result.returncode == 0 and result.stdout.strip() != "HEAD":
        return result.stdout.strip()
    symbolic = git(["symbolic-ref", "--short", "HEAD"], repo)
    if symbolic.returncode != 0:
        raise GitError("Could not determine current git branch.", why=result.stderr.strip())
    return symbolic.stdout.strip()


def upstream_ref(repo: Path) -> str | None:
    result = git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], repo)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    branch = current_branch(repo)
    candidate = f"origin/{branch}"
    verify = git(["rev-parse", "--verify", candidate], repo)
    if verify.returncode == 0:
        return candidate
    return None


def has_dirty_worktree(repo: Path) -> bool:
    result = git(["status", "--porcelain"], repo)
    if result.returncode != 0:
        raise GitError("git status failed.", why=result.stderr.strip(), next_action="Inspect the sync repository.")
    return bool(result.stdout.strip())


def inspect_conflicts(repo: Path, *, fetch_remote: bool = True) -> ConflictStatus:
    require_git_repository(repo)
    branch = current_branch(repo)
    dirty = has_dirty_worktree(repo)
    if not has_remote(repo):
        return ConflictStatus(state="no-remote", branch=branch, dirty=dirty, details="No Git remote is configured.")
    if fetch_remote:
        fetched = git(["fetch", "--prune"], repo)
        if fetched.returncode != 0:
            return ConflictStatus(
                state="fetch-failed",
                branch=branch,
                dirty=dirty,
                details=fetched.stderr.strip() or "git fetch failed.",
            )
    upstream = upstream_ref(repo)
    if not upstream:
        return ConflictStatus(
            state="no-upstream",
            branch=branch,
            dirty=dirty,
            details="No upstream branch exists yet; first push can create it.",
        )
    local = git(["rev-parse", "HEAD"], repo)
    remote = git(["rev-parse", upstream], repo)
    base = git(["merge-base", "HEAD", upstream], repo)
    if local.returncode != 0 or remote.returncode != 0 or base.returncode != 0:
        raise GitError("Could not inspect git history.", why="\n".join([local.stderr, remote.stderr, base.stderr]).strip())
    local_sha = local.stdout.strip()
    remote_sha = remote.stdout.strip()
    base_sha = base.stdout.strip()
    if local_sha == remote_sha:
        state = "synced"
    elif base_sha == remote_sha:
        state = "ahead"
    elif base_sha == local_sha:
        state = "behind"
    else:
        state = "diverged"
    if dirty and state in {"synced", "ahead"}:
        return ConflictStatus(
            state="dirty",
            branch=branch,
            upstream=upstream,
            local=local_sha,
            remote=remote_sha,
            base=base_sha,
            dirty=True,
            details="Local vault repository has uncommitted changes.",
        )
    return ConflictStatus(state=state, branch=branch, upstream=upstream, local=local_sha, remote=remote_sha, base=base_sha, dirty=dirty)


def require_no_remote_conflict(repo: Path) -> ConflictStatus:
    status = inspect_conflicts(repo, fetch_remote=True)
    if status.state in {"behind", "diverged", "fetch-failed"}:
        next_action = {
            "behind": "Run: aisync --repo <repo> pull",
            "diverged": "Resolve the Git divergence manually before running sync again.",
            "fetch-failed": "Check network access and Git credentials, then retry.",
        }.get(status.state)
        raise GitError(
            f"Vault repository conflict detected: {status.state}",
            why=status.details,
            next_action=next_action,
        )
    return status


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
        upstream = upstream_ref(repo)
        if upstream:
            push_result = git(["push"], repo)
        else:
            push_result = git(["push", "-u", "origin", current_branch(repo)], repo)
        if push_result.returncode != 0:
            raise GitError("git push failed.", why=push_result.stderr.strip(), next_action="Check network and Git credentials.")
    return commit


def pull(repo: Path) -> None:
    require_remote(repo)
    result = git(["pull", "--ff-only"], repo)
    if result.returncode != 0:
        raise GitError("git pull failed.", why=result.stderr.strip(), next_action="Resolve remote/local divergence first.")
