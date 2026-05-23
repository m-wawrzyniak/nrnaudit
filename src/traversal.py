"""Phase 1: repository traversal and file discovery."""

from __future__ import annotations

from pathlib import Path

from src import utils


def discover_files(repo_root: Path) -> tuple[list[str], list[str]]:
    """Collect sorted relative paths of all .hoc and .mod files under repo_root."""
    hoc_paths: list[str] = []
    mod_paths: list[str] = []

    for path in utils.iter_repo_files(repo_root):
        if path.suffix == utils.HOC_EXT:
            hoc_paths.append(utils.to_relative_posix(path, repo_root))
        elif path.suffix == utils.MOD_EXT:
            mod_paths.append(utils.to_relative_posix(path, repo_root))

    hoc_paths.sort()
    mod_paths.sort()
    return hoc_paths, mod_paths
