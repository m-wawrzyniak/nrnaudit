"""Phase 4: edge resolution and flat graph assembly.

Resolves HOC load strings to repository-relative targets, validates ``insert``
mechanisms against the Phase 2 map, and assembles flat node and edge lists.

Node types: ``hoc``, ``mechanism``, ``mod_file`` (unparsed ``.mod``), and
``orphan``. Edge relations: ``loads`` (hoc→hoc) and ``inserts`` (hoc→mechanism).
Each node carries a ``variables`` list populated by Pass 2.
"""

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
    """Resolve a captured load string to a repository HOC path.

    Tries, in order: (1) exact match against a discovered relative path,
    (2) unique basename match when exactly one file shares the filename,
    (3) path joined relative to the loading file's directory.

    Args:
        captured: Raw path string from a ``load_file``/``xopen``/``ropen`` call.
        source_hoc_relpath: Relative path of the file that issued the load.
        hoc_relpaths_set: Set of all discovered HOC-family relative paths.
        basename_index: ``{filename: [relpath, ...]}`` from ``build_basename_index``.

    Returns:
        Resolved repository-relative POSIX path, or ``None`` when ambiguous or
        not found (e.g. multiple files share the same basename).
    """
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
    """Build deduplicated hoc-to-hoc load edges.

    Resolves each captured load string via ``resolve_load_target`` and emits
    one edge per unique ``(source, target)`` pair. Unresolved loads are skipped.

    Args:
        parsed_hoc: Phase 3 output mapping hoc paths to raw loads/inserts.
        hoc_relpaths: All discovered HOC-family relative paths.

    Returns:
        List of edge dicts: ``{"source": str, "target": str, "relation": "loads"}``.
    """
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
    """Build hoc-to-mechanism insert edges for HOC-declared inserts.

    Only mechanisms present in ``mechanism_map`` produce edges; unknown names
    are skipped. Target node IDs are mechanism names, not ``.mod`` paths.

    Args:
        parsed_hoc: Phase 3 output mapping hoc paths to raw loads/inserts.
        hoc_relpaths: All discovered HOC-family relative paths.
        mechanism_map: ``{mechanism_name: mod_relpath}`` from Phase 2.

    Returns:
        List of edge dicts:
        ``{"source": str, "target": str, "relation": "inserts"}``.
    """
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
    """Assemble the internal flat dependency graph.

    Combines load and insert edges with four node kinds: ``hoc`` (all HOC-family
    files), ``mechanism`` (parsed ``.mod`` mechanisms), ``mod_file`` (``.mod``
    files without an extractable mechanism name), and ``orphan`` (optional
    contextual files). Each node includes a ``variables`` list from Pass 2.

    Args:
        hoc_relpaths: Discovered HOC-family relative paths.
        mod_relpaths: Discovered ``.mod`` relative paths.
        parsed_hoc: Phase 3 parsed loads and inserts per hoc file.
        mechanism_map: Phase 2 mechanism name to mod path mapping.
        hoc_variables: Pass 2 variables keyed by hoc relpath.
        mod_variables: Pass 2 variables keyed by mod relpath.
        orphan_relpaths: Optional orphan file paths for ``orphan`` nodes.

    Returns:
        ``{"nodes": [dict], "edges": [dict]}`` in the internal flat schema
        consumed by ``cytoscape_export.to_cytoscape``.
    """
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
