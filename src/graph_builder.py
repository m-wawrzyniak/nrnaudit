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
) -> tuple[list[dict], set[str]]:
    """Build hoc-to-mechanism insert edges; return edges and referenced mechanism names."""
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()
    used_mechanisms: set[str] = set()

    for source in hoc_relpaths:
        for mech in parsed_hoc[source]["inserts"]:
            if mech not in mechanism_map:
                continue
            if (source, mech) in seen:
                continue
            seen.add((source, mech))
            used_mechanisms.add(mech)
            edges.append(
                {"source": source, "target": mech, "relation": "inserts"}
            )

    return edges, used_mechanisms


def build_nodes(
    hoc_relpaths: list[str],
    mechanism_map: dict[str, str],
    used_mechanisms: set[str],
    hoc_variables: dict[str, list[dict]],
    mod_variables: dict[str, list[dict]],
) -> list[dict]:
    """Build flat node dicts for all hoc files and inserted mechanisms."""
    nodes: list[dict] = []
    for p in hoc_relpaths:
        nodes.append(
            {
                "id": p,
                "type": "hoc",
                "label": Path(p).name,
                "source_file": p,
                "variables": hoc_variables.get(p, []),
            }
        )
    for mech in sorted(used_mechanisms):
        nodes.append(
            {
                "id": mech,
                "type": "mechanism",
                "label": mech,
                "source_file": mechanism_map[mech],
                "variables": mod_variables.get(mechanism_map[mech], []),
            }
        )
    return nodes


def build_graph(
    hoc_relpaths: list[str],
    parsed_hoc: dict[str, dict[str, list[str]]],
    mechanism_map: dict[str, str],
    hoc_variables: dict[str, list[dict]],
    mod_variables: dict[str, list[dict]],
) -> dict:
    """Assemble the internal flat graph with 'nodes' and 'edges' keys."""
    load_edges = build_load_edges(parsed_hoc, hoc_relpaths)
    insert_edges, used_mechanisms = build_insert_edges(
        parsed_hoc, hoc_relpaths, mechanism_map
    )
    nodes = build_nodes(
        hoc_relpaths, mechanism_map, used_mechanisms, hoc_variables, mod_variables
    )
    return {"nodes": nodes, "edges": load_edges + insert_edges}
