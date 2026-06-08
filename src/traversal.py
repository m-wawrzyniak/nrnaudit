"""Phase 1: repository traversal and file discovery."""

from __future__ import annotations

from pathlib import Path

from src import utils


def discover_files(repo_root: Path) -> tuple[list[str], list[str]]:
    """Collect sorted relative paths of all HOC-family and .mod files under repo_root."""
    hoc_paths: list[str] = []
    mod_paths: list[str] = []

    for path in utils.iter_repo_files(repo_root):
        if utils.is_hoc_file(path):
            hoc_paths.append(utils.to_relative_posix(path, repo_root))
        elif path.suffix.lower() == utils.MOD_EXT:
            mod_paths.append(utils.to_relative_posix(path, repo_root))

    hoc_paths.sort()
    mod_paths.sort()
    return hoc_paths, mod_paths


def discover_orphan_files(
    repo_root: Path,
    hoc_relpaths: list[str],
    mod_relpaths: list[str],
    allowed_extensions: frozenset[str],
) -> list[str]:
    """Collect sorted orphan file paths matching allowed_extensions."""
    hoc_set = set(hoc_relpaths)
    mod_set = set(mod_relpaths)
    orphan_paths: list[str] = []

    for path in utils.iter_repo_files(repo_root):
        relpath = utils.to_relative_posix(path, repo_root)
        if relpath in hoc_set or relpath in mod_set:
            continue
        if path.suffix.lower() not in allowed_extensions:
            continue
        orphan_paths.append(relpath)

    orphan_paths.sort()
    return orphan_paths
