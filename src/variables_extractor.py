"""Pass 2: variable and unit extraction from .mod and .hoc files."""

from __future__ import annotations

import re
from pathlib import Path

from src import utils

VARIABLE_BLOCKS = ("PARAMETER", "ASSIGNED", "STATE", "CONSTANT")
KNOWN_UNITS: frozenset[str] = frozenset(
    {"mV", "ms", "mA/cm2", "um", "nS", "mM", "S/cm2", "pA"}
)
_NAME_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)")
_UNIT_RE = re.compile(r"\(([^)]*)\)")
_EXPLICIT_HOC_RE = re.compile(
    r"\b(?:strdef|objref|create|double)\s+([A-Za-z_][A-Za-z0-9_]*)"
)
_ASSIGNMENT_LHS_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")
_INLINE_COMMENT_RE = re.compile(r"//\s*(\S+)")


def extract_block_body(text: str, block_name: str) -> str | None:
    """Return inner text of the first `block_name { ... }` block, or None."""
    pattern = re.compile(r"\b" + re.escape(block_name) + r"\s*\{")
    m = pattern.search(text)
    if m is None:
        return None
    return utils.extract_brace_body(text, m.end())


def parse_mod_block_lines(block_body: str) -> list[dict]:
    """Extract [{name, unit}] from a single NMODL declaration block body."""
    results: list[dict] = []
    stripped_body = utils.strip_mod_comments(block_body)
    for raw_line in stripped_body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("?") or line.startswith("~"):
            continue
        name_match = _NAME_RE.match(line)
        if name_match is None:
            continue
        name = name_match.group(1)
        unit_match = _UNIT_RE.search(line)
        unit = unit_match.group(1).strip() if unit_match else "???"
        results.append({"name": name, "unit": unit})
    return results


def extract_mod_variables(repo_root: Path, mod_relpath: str) -> list[dict]:
    """Return deduplicated [{name, unit}] from all declaration blocks in a .mod file."""
    text = utils.read_text_file(repo_root / mod_relpath)
    seen_names: set[str] = set()
    variables: list[dict] = []
    for block_name in VARIABLE_BLOCKS:
        body = extract_block_body(text, block_name)
        if body is None:
            continue
        for var in parse_mod_block_lines(body):
            if var["name"] not in seen_names:
                seen_names.add(var["name"])
                variables.append(var)
    return variables


def extract_hoc_explicit_variables(text: str) -> list[dict]:
    """Return [{name, unit: 'N/A'}] for strdef/objref/create/double declarations."""
    return [
        {"name": m.group(1), "unit": "N/A"}
        for m in _EXPLICIT_HOC_RE.finditer(text)
    ]


def guess_unit_from_comment(line: str) -> str:
    """Return the unit string from a // comment if it is in KNOWN_UNITS, else '???'."""
    m = _INLINE_COMMENT_RE.search(line)
    if m is None:
        return "???"
    token = m.group(1)
    return token if token in KNOWN_UNITS else "???"


def extract_hoc_assignment_variables(text: str) -> list[dict]:
    """Return [{name, unit}] for simple assignment lines (LHS must be a bare identifier)."""
    results: list[dict] = []
    for line in text.splitlines():
        m = _ASSIGNMENT_LHS_RE.match(line.strip())
        if m is None:
            continue
        name = m.group(1)
        unit = guess_unit_from_comment(line)
        results.append({"name": name, "unit": unit})
    return results


def extract_hoc_variables(repo_root: Path, hoc_relpath: str) -> list[dict]:
    """Return deduplicated [{name, unit}] from a .hoc file (explicit decls then assignments)."""
    raw_text = utils.read_text_file(repo_root / hoc_relpath)
    block_stripped = utils.strip_hoc_block_comments(raw_text)
    explicit = extract_hoc_explicit_variables(block_stripped)
    assignments = extract_hoc_assignment_variables(block_stripped)
    seen_names: set[str] = set()
    variables: list[dict] = []
    for var in explicit + assignments:
        if var["name"] not in seen_names:
            seen_names.add(var["name"])
            variables.append(var)
    return variables


def build_hoc_variables_map(
    repo_root: Path, hoc_relpaths: list[str]
) -> dict[str, list[dict]]:
    """Map each hoc relpath to its extracted variables list."""
    return {p: extract_hoc_variables(repo_root, p) for p in hoc_relpaths}


def build_mod_variables_map(
    repo_root: Path, mod_relpaths: list[str]
) -> dict[str, list[dict]]:
    """Map each mod relpath to its extracted variables list."""
    return {p: extract_mod_variables(repo_root, p) for p in mod_relpaths}
