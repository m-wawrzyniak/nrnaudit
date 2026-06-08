"""Phase 1: repository traversal and file discovery.

Walks the NEURON project tree from a given root, skipping compiled/binary
directories, and collects relative paths for HOC-family files (``.hoc``,
``.tem``, ``.oc``), ``.mod`` files, and optional orphan files by extension.

Outputs sorted relative POSIX paths used as node IDs throughout later phases.
Static analysis only; no files are executed or imported at runtime.
"""

from __future__ import annotations

from pathlib import Path

from src import utils


def discover_files(repo_root: Path) -> tuple[list[str], list[str]]:
    """Collect sorted relative paths of HOC-family and ``.mod`` files.

    Walks ``repo_root`` via ``utils.iter_repo_files``, classifying paths by
    extension. HOC-family includes ``.hoc``, ``.tem``, and ``.oc``.

    Args:
        repo_root: Absolute path to the NEURON project root.

    Returns:
        Tuple of ``(hoc_relpaths, mod_relpaths)``, each a sorted list of
        repository-relative POSIX path strings used as node IDs later.
    """
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
    """Collect sorted orphan file paths matching allowed extensions.

    Orphan files are repository files that are neither HOC-family nor ``.mod``
    but whose suffix appears in ``allowed_extensions``. They are not parsed
    for variables; Phase 4 emits ``orphan`` nodes for graph context only.

    Args:
        repo_root: Absolute path to the NEURON project root.
        hoc_relpaths: HOC-family paths already discovered (excluded).
        mod_relpaths: ``.mod`` paths already discovered (excluded).
        allowed_extensions: Lowercase dotted suffixes (e.g. ``{".txt", ".py"}``).

    Returns:
        Sorted list of repository-relative POSIX paths for orphan files.
    """
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
