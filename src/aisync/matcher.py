from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import PurePosixPath


def normalize_rel(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def matches_pattern(rel: str, pattern: str) -> bool:
    rel = normalize_rel(rel)
    pattern = normalize_rel(pattern)
    basename = PurePosixPath(rel).name

    if pattern.endswith("/**") or pattern.endswith("/***"):
        prefix = pattern.rsplit("/", 1)[0]
        return rel == prefix or rel.startswith(prefix + "/")
    if "/" not in pattern and fnmatchcase(basename, pattern):
        return True
    return fnmatchcase(rel, pattern)


def matches_any(rel: str, patterns: list[str]) -> bool:
    return any(matches_pattern(rel, pattern) for pattern in patterns)

