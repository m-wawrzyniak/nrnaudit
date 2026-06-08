"""Phase 2: NMODL (``.mod``) mechanism name extraction.

Strips NMODL comments, locates the ``NEURON { ... }`` block, and reads the
declared mechanism name from ``SUFFIX``, ``POINT_PROCESS``, or ``ARTIFICIAL_CELL``.

Produces ``{mechanism_name: mod_relpath}`` where the first declaration wins on
name collision. Files without a parseable NEURON block are omitted from the map
and later appear as ``mod_file`` nodes in Phase 4.
"""

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
    return utils.extract_brace_body(stripped_text, m.end())


def extract_mechanism_name(neuron_block_body: str) -> str | None:
    """Parse SUFFIX, POINT_PROCESS, or ARTIFICIAL_CELL name from a NEURON block body."""
    m = MECH_DECL_RE.search(neuron_block_body)
    if m is None:
        return None
    return m.group(1)


def parse_mod_file(repo_root: Path, mod_relpath: str) -> str | None:
    """Return the mechanism name declared in a single ``.mod`` file.

    Strips NMODL comments, extracts the ``NEURON { ... }`` block body, and
    reads the first ``SUFFIX``, ``POINT_PROCESS``, or ``ARTIFICIAL_CELL`` name.

    Args:
        repo_root: Absolute path to the NEURON project root.
        mod_relpath: Repository-relative path to the ``.mod`` file.

    Returns:
        Declared mechanism name, or ``None`` when no NEURON block or keyword
        declaration is found.
    """
    text = utils.read_text_file(repo_root / mod_relpath)
    stripped = utils.strip_mod_comments(text)
    body = extract_neuron_block_body(stripped)
    if body is None:
        return None
    return extract_mechanism_name(body)


def build_mechanism_map(repo_root: Path, mod_relpaths: list[str]) -> dict[str, str]:
    """Map mechanism names to relative ``.mod`` paths.

    Parses each discovered ``.mod`` file and records the mechanism name from
    ``SUFFIX``, ``POINT_PROCESS``, or ``ARTIFICIAL_CELL``. When two files
    declare the same name, the first path in ``mod_relpaths`` order wins.

    Args:
        repo_root: Absolute path to the NEURON project root.
        mod_relpaths: Sorted repository-relative ``.mod`` paths from Phase 1.

    Returns:
        ``{mechanism_name: mod_relpath}`` for all successfully parsed files.
    """
    mechanism_map: dict[str, str] = {}
    for mod_relpath in mod_relpaths:
        name = parse_mod_file(repo_root, mod_relpath)
        if name is not None and name not in mechanism_map:
            mechanism_map[name] = mod_relpath
    return mechanism_map
