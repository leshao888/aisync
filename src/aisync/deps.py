from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from .errors import DependencyError


@dataclass(frozen=True)
class Dependency:
    name: str
    required: bool
    install_hint: str


DEPENDENCIES = [
    Dependency("git", True, "Install Git from https://git-scm.com or your package manager."),
    Dependency("age", True, "macOS: brew install age | Linux: install age from your package manager."),
    Dependency("gitleaks", True, "macOS: brew install gitleaks | Other systems: https://github.com/gitleaks/gitleaks/releases"),
]


def which(name: str) -> str | None:
    return shutil.which(name)


def require_tool(name: str, hint: str) -> str:
    path = which(name)
    if not path:
        raise DependencyError(f"Missing dependency: {name}", next_action=hint)
    return path


def check_required() -> list[tuple[Dependency, str | None]]:
    return [(dep, which(dep.name)) for dep in DEPENDENCIES]


def run(cmd: list[str], *, cwd=None, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

