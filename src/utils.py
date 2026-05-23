"""Shared helpers for the NEURON static dependency analyzer."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from pathlib import Path

IGNORED_DIR_NAMES = {"x86_64", "arm64", ".git"}
HOC_EXT = ".hoc"
MOD_EXT = ".mod"
OUTPUT_FILENAME = "neuron_dependencies.cyjs"


def read_text_file(path: Path) -> str:
    """Read a text file as UTF-8, replacing undecodable bytes."""
    with path.open(encoding="utf-8", errors="replace") as fh:
        return fh.read()


def strip_hoc_comments(text: str) -> str:
    """Remove HOC block (/* */) and line (//) comments from source text."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return text


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
