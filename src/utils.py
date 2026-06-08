"""Shared I/O, path normalization, and parsing helpers for the analyzer.

Used across all pipeline phases: repository walking, comment stripping,
brace-block extraction, and JSON output. Defines canonical constants such as
``HOC_EXTENSIONS``, ``OUTPUT_FILENAME``, and default orphan file extensions.

This module performs no semantic analysis; it only provides low-level utilities
consumed by traversal, parsers, graph assembly, and the GUI.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from pathlib import Path

IGNORED_DIR_NAMES = {"x86_64", "arm64", ".git"}
HOC_EXTENSIONS: frozenset[str] = frozenset({".hoc", ".tem", ".oc"})
MOD_EXT = ".mod"
OUTPUT_FILENAME = "neuron_dependencies.cyjs"
DEFAULT_ORPHAN_EXTENSIONS: frozenset[str] = frozenset(
    {".txt", ".md", ".dat", ".py", ".html"}
)


def is_hoc_file(path: Path) -> bool:
    """Return True when path has a recognized HOC-family extension."""
    return path.suffix.lower() in HOC_EXTENSIONS


def normalize_extension(token: str) -> str:
    """Normalize an extension token to lowercase dotted form (e.g. 'csv' -> '.csv')."""
    token = token.strip().lower()
    return token if token.startswith(".") else f".{token}"


def merge_orphan_extensions(extra: list[str] | None) -> frozenset[str]:
    """Return default orphan extensions merged with any CLI extras."""
    merged = set(DEFAULT_ORPHAN_EXTENSIONS)
    for token in extra or []:
        merged.add(normalize_extension(token))
    return frozenset(merged)


def read_text_file(path: Path) -> str:
    """Read a text file as UTF-8, replacing undecodable bytes."""
    with path.open(encoding="utf-8", errors="replace") as fh:
        return fh.read()


def strip_hoc_comments(text: str) -> str:
    """Remove HOC block (/* */) and line (//) comments from source text."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def strip_hoc_block_comments(text: str) -> str:
    """Remove HOC /* */ block comments only; preserves // line comments."""
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)


def strip_mod_comments(text: str) -> str:
    """Remove NMODL COMMENT/ENDCOMMENT blocks and ? / ~ line comments."""
    text = re.sub(r"COMMENT\b.*?\bENDCOMMENT\b", " ", text, flags=re.DOTALL)
    text = re.sub(r"\?[^\n]*", "", text)
    text = re.sub(r"~[^\n]*", "", text)
    return text


def to_relative_posix(absolute_path: Path, repo_root: Path) -> str:
    """Return a repo-relative path using forward slashes (POSIX style)."""
    rel = absolute_path.resolve().relative_to(repo_root.resolve())
    return rel.as_posix()


def iter_repo_files(repo_root: Path) -> Iterator[Path]:
    """Walk the repository tree, skipping compiled/binary directories."""
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIR_NAMES]
        for filename in filenames:
            yield Path(dirpath) / filename


def ensure_output_dir(output_dir: Path) -> None:
    """Create the output directory and any missing parents."""
    output_dir.mkdir(parents=True, exist_ok=True)


def write_json(data: dict, output_dir: Path) -> Path:
    """Write data as indented JSON to OUTPUT_FILENAME under output_dir."""
    ensure_output_dir(output_dir)
    target = output_dir / OUTPUT_FILENAME
    with target.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=False)
    return target


def extract_brace_body(text: str, open_pos: int) -> str | None:
    """Return inner text from open_pos to its matching closing brace, or None."""
    depth = 1
    i = open_pos
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    if depth != 0:
        return None
    return text[open_pos:i]


_ARRAY_INDEX_RE = re.compile(r"\[[^\]]*\]")


def strip_array_index(name: str) -> str:
    """Remove HOC array index brackets from a name, returning the trimmed base name."""
    return _ARRAY_INDEX_RE.sub("", name).strip()


def split_location_and_name(lhs: str) -> tuple[str, str]:
    """Split a HOC LHS into (location, name); name is the final whitespace token."""
    tokens = lhs.split()
    if not tokens:
        return "", ""
    return " ".join(tokens[:-1]), tokens[-1]


_PARAM_DEFAULT_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*([^\s(]+))?")


def parse_parameter_block_defaults(block_body: str) -> dict[str, str]:
    """Map NMODL PARAMETER names to default literals (missing default -> '0')."""
    defaults: dict[str, str] = {}
    for raw_line in strip_mod_comments(block_body).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = _PARAM_DEFAULT_RE.match(line)
        if m is None:
            continue
        defaults[m.group(1)] = m.group(2) if m.group(2) is not None else "0"
    return defaults
