"""Phase 3: HOC file load and insert extraction."""

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
    """Parse one .hoc file into raw load paths and insert mechanism names."""
    text = utils.read_text_file(repo_root / hoc_relpath)
    stripped = utils.strip_hoc_comments(text)
    return {
        "loads": extract_loaded_files(stripped),
        "inserts": extract_inserted_mechanisms(stripped),
    }


def parse_all_hoc(
    repo_root: Path, hoc_relpaths: list[str]
) -> dict[str, dict[str, list[str]]]:
    """Parse every discovered .hoc file; keys are relative hoc paths."""
    parsed: dict[str, dict[str, list[str]]] = {}
    for hoc_relpath in hoc_relpaths:
        parsed[hoc_relpath] = parse_hoc_file(repo_root, hoc_relpath)
    return parsed
