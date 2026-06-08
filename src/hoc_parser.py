"""Phase 3: HOC-family file load and insert extraction.

Parses HOC-family files (``.hoc``, ``.tem``, ``.oc``) after comment stripping to
collect raw ``load_file``/``xopen``/``ropen`` path strings and ``insert``
mechanism names. Load targets are not resolved here; Phase 4 matches captured
strings against discovered file paths.

Outputs ``{hoc_relpath: {"loads": [str], "inserts": [str]}}`` per file.
"""

from __future__ import annotations

import re
from pathlib import Path

from src import utils

LOAD_RE = re.compile(
    r"\b(?:load_file|xopen|ropen)\b\s*\(?\s*\"([^\"]+)\"\s*\)?"
)
INSERT_RE = re.compile(r"\binsert\s+([A-Za-z_][A-Za-z0-9_]*)")


def extract_loaded_files(stripped_text: str) -> list[str]:
    """Find quoted paths from load_file, xopen, and ropen calls."""
    return [m.group(1) for m in LOAD_RE.finditer(stripped_text)]


def extract_inserted_mechanisms(stripped_text: str) -> list[str]:
    """Find mechanism names from insert statements."""
    return [m.group(1) for m in INSERT_RE.finditer(stripped_text)]


def parse_hoc_file(repo_root: Path, hoc_relpath: str) -> dict[str, list[str]]:
    """Parse one HOC-family file into raw load paths and insert names.

    Applies full HOC comment stripping (``//`` and ``/* */``), then extracts
    quoted paths from ``load_file``/``xopen``/``ropen`` and mechanism names
    from ``insert`` statements. Load strings are returned unresolved.

    Args:
        repo_root: Absolute path to the NEURON project root.
        hoc_relpath: Repository-relative path (``.hoc``, ``.tem``, or ``.oc``).

    Returns:
        ``{"loads": [str], "inserts": [str]}`` with captured literal strings.
    """
    text = utils.read_text_file(repo_root / hoc_relpath)
    stripped = utils.strip_hoc_comments(text)
    return {
        "loads": extract_loaded_files(stripped),
        "inserts": extract_inserted_mechanisms(stripped),
    }


def parse_all_hoc(
    repo_root: Path, hoc_relpaths: list[str]
) -> dict[str, dict[str, list[str]]]:
    """Parse every discovered HOC-family file.

    Args:
        repo_root: Absolute path to the NEURON project root.
        hoc_relpaths: Sorted HOC-family relative paths from Phase 1.

    Returns:
        ``{hoc_relpath: {"loads": [str], "inserts": [str]}}`` for each file.
    """
    parsed: dict[str, dict[str, list[str]]] = {}
    for hoc_relpath in hoc_relpaths:
        parsed[hoc_relpath] = parse_hoc_file(repo_root, hoc_relpath)
    return parsed
