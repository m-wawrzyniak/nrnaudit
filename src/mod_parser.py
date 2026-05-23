"""Phase 2: NMODL (.mod) mechanism name extraction."""

from __future__ import annotations

import re
from pathlib import Path

from src import utils

MECH_KEYWORDS = ("SUFFIX", "POINT_PROCESS", "ARTIFICIAL_CELL")
NEURON_BLOCK_OPEN_RE = re.compile(r"\bNEURON\s*\{")
MECH_DECL_RE = re.compile(
    r"\b(?:SUFFIX|POINT_PROCESS|ARTIFICIAL_CELL)\s+([A-Za-z_][A-Za-z0-9_]*)"
)


def extract_neuron_block_body(stripped_text: str) -> str | None:
    """Return the inner text of the first NEURON { ... } block, or None."""
    m = NEURON_BLOCK_OPEN_RE.search(stripped_text)
    if m is None:
        return None

    i = m.end()
    depth = 1
    while i < len(stripped_text) and depth > 0:
        if stripped_text[i] == "{":
            depth += 1
        elif stripped_text[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1

    if depth != 0:
        return None

    return stripped_text[m.end() : i]


def extract_mechanism_name(neuron_block_body: str) -> str | None:
    """Parse SUFFIX, POINT_PROCESS, or ARTIFICIAL_CELL name from a NEURON block body."""
    m = MECH_DECL_RE.search(neuron_block_body)
    if m is None:
        return None
    return m.group(1)


def parse_mod_file(repo_root: Path, mod_relpath: str) -> str | None:
    """Return the mechanism name declared in a single .mod file, or None."""
    text = utils.read_text_file(repo_root / mod_relpath)
    stripped = utils.strip_mod_comments(text)
    body = extract_neuron_block_body(stripped)
    if body is None:
        return None
    return extract_mechanism_name(body)


def build_mechanism_map(repo_root: Path, mod_relpaths: list[str]) -> dict[str, str]:
    """Map mechanism names to relative .mod paths (first declaration wins on collision)."""
    mechanism_map: dict[str, str] = {}
    for mod_relpath in mod_relpaths:
        name = parse_mod_file(repo_root, mod_relpath)
        if name is not None and name not in mechanism_map:
            mechanism_map[name] = mod_relpath
    return mechanism_map
