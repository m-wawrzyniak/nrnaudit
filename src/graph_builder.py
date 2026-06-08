"""Phase 4: edge resolution and JSON graph assembly."""

from __future__ import annotations

import os
from pathlib import Path


def build_basename_index(hoc_relpaths: list[str]) -> dict[str, list[str]]:
    """Index hoc relative paths by filename (basename) for load resolution."""
    index: dict[str, list[str]] = {}
    for p in hoc_relpaths:
        index.setdefault(Path(p).name, []).append(p)
    return index


def resolve_load_target(
    captured: str,
    source_hoc_relpath: str,
    hoc_relpaths_set: set[str],
    basename_index: dict[str, list[str]],
) -> str | None:
    """Resolve a captured load string to a repo hoc path, or None if unresolved."""
    if captured in hoc_relpaths_set:
        return captured

    candidates = basename_index.get(Path(captured).name, [])
    if len(candidates) == 1:
        return candidates[0]

    loader_dir = Path(source_hoc_relpath).parent
    joined = (loader_dir / captured).as_posix()
    normalized = os.path.normpath(joined).replace("\\", "/")
    if normalized in hoc_relpaths_set:
        return normalized

    return None


def build_load_edges(
    parsed_hoc: dict[str, dict[str, list[str]]], hoc_relpaths: list[str]
) -> list[dict]:
    """Build deduplicated hoc-to-hoc load edges with relation 'loads'."""
    hoc_set = set(hoc_relpaths)
    basename_index = build_basename_index(hoc_relpaths)
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for source in hoc_relpaths:
        for captured in parsed_hoc[source]["loads"]:
            target = resolve_load_target(
                captured, source, hoc_set, basename_index
            )
            if target is None or (source, target) in seen:
                continue
            seen.add((source, target))
            edges.append(
                {"source": source, "target": target, "relation": "loads"}
            )

    return edges


def build_insert_edges(
    parsed_hoc: dict[str, dict[str, list[str]]],
    hoc_relpaths: list[str],
    mechanism_map: dict[str, str],
) -> list[dict]:
    """Build hoc-to-mechanism insert edges for HOC-declared inserts."""
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for source in hoc_relpaths:
        for mech in parsed_hoc[source]["inserts"]:
            if mech not in mechanism_map:
                continue
            if (source, mech) in seen:
                continue
            seen.add((source, mech))
            edges.append(
                {"source": source, "target": mech, "relation": "inserts"}
            )

    return edges


def unparsed_mod_relpaths(
    mod_relpaths: list[str], mechanism_map: dict[str, str]
) -> list[str]:
    """Return .mod paths with no successfully extracted mechanism name."""
    parsed_paths = set(mechanism_map.values())
    return [p for p in mod_relpaths if p not in parsed_paths]


def build_nodes(
    hoc_relpaths: list[str],
    hoc_variables: dict[str, list[dict]],
) -> list[dict]:
    """Build flat node dicts for all hoc files."""
    return [
        {
            "id": p,
            "type": "hoc",
            "label": Path(p).name,
            "source_file": p,
            "variables": hoc_variables.get(p, []),
        }
        for p in hoc_relpaths
    ]


def build_mechanism_nodes(
    mechanism_map: dict[str, str],
    mod_variables: dict[str, list[dict]],
) -> list[dict]:
    """Build flat node dicts for all successfully parsed mechanisms."""
    return [
        {
            "id": mech,
            "type": "mechanism",
            "label": mech,
            "source_file": mechanism_map[mech],
            "variables": mod_variables.get(mechanism_map[mech], []),
        }
        for mech in sorted(mechanism_map)
    ]


def build_mod_file_nodes(
    mod_relpaths: list[str],
    mod_variables: dict[str, list[dict]],
) -> list[dict]:
    """Build flat node dicts for .mod files without an extractable mechanism name."""
    return [
        {
            "id": relpath,
            "type": "mod_file",
            "label": Path(relpath).name,
            "source_file": relpath,
            "variables": mod_variables.get(relpath, []),
        }
        for relpath in mod_relpaths
    ]


def build_orphan_nodes(orphan_relpaths: list[str]) -> list[dict]:
    """Build flat node dicts for orphan files (no variable parsing)."""
    return [
        {
            "id": relpath,
            "type": "orphan",
            "label": Path(relpath).name,
            "source_file": relpath,
            "variables": [],
        }
        for relpath in orphan_relpaths
    ]


def build_graph(
    hoc_relpaths: list[str],
    mod_relpaths: list[str],
    parsed_hoc: dict[str, dict[str, list[str]]],
    mechanism_map: dict[str, str],
    hoc_variables: dict[str, list[dict]],
    mod_variables: dict[str, list[dict]],
    orphan_relpaths: list[str] | None = None,
) -> dict:
    """Assemble the internal flat graph with 'nodes' and 'edges' keys."""
    load_edges = build_load_edges(parsed_hoc, hoc_relpaths)
    insert_edges = build_insert_edges(parsed_hoc, hoc_relpaths, mechanism_map)
    nodes = (
        build_nodes(hoc_relpaths, hoc_variables)
        + build_mechanism_nodes(mechanism_map, mod_variables)
        + build_mod_file_nodes(
            unparsed_mod_relpaths(mod_relpaths, mechanism_map), mod_variables
        )
        + build_orphan_nodes(orphan_relpaths or [])
    )
    return {"nodes": nodes, "edges": load_edges + insert_edges}
