"""Cytoscape.js graph JSON serialization adapter.

Converts the internal flat graph from Phase 4 into the Cytoscape.js
``elements`` schema: nodes and edges wrapped in ``{"data": ...}`` envelopes,
stable edge IDs, and a derived ``variables_flat`` display string per node.

Consumed by ``main`` for export and by ``utility_gui`` when loading saved graphs.
"""

from __future__ import annotations


def make_edge_id(source: str, relation: str, target: str) -> str:
    """Build a stable edge id from source, relation, and target."""
    return f"{source}_{relation}_{target}"


def format_variables_flat(variables: list[dict]) -> str:
    """Render a variables list as 'name (unit) | name (unit) | ...'."""
    return " | ".join(f"{v['name']} ({v['unit']})" for v in variables)


def wrap_node(node: dict) -> dict:
    """Wrap a flat node dict in a Cytoscape.js {'data': ...} envelope."""
    node_data = dict(node)
    if "variables" in node_data:
        node_data["variables_flat"] = format_variables_flat(node_data["variables"])
    return {"data": node_data}


def wrap_edge(edge: dict) -> dict:
    """Add a generated id and wrap a flat edge in a Cytoscape.js data envelope."""
    source = edge["source"]
    target = edge["target"]
    relation = edge["relation"]
    edge_data = dict(edge)
    edge_data["id"] = make_edge_id(source, relation, target)
    return {"data": edge_data}


def wrap_nodes(nodes: list[dict]) -> list[dict]:
    """Wrap each node in the graph for Cytoscape.js."""
    return [wrap_node(n) for n in nodes]


def wrap_edges(edges: list[dict]) -> list[dict]:
    """Wrap each edge in the graph for Cytoscape.js."""
    return [wrap_edge(e) for e in edges]


def to_cytoscape(graph: dict) -> dict:
    """Convert a flat ``build_graph`` dict to Cytoscape.js elements schema.

    Wraps each node and edge in a ``{"data": ...}`` envelope, assigns stable
    edge IDs via ``make_edge_id``, and adds ``variables_flat`` (a pipe-separated
    ``name (unit)`` summary) to nodes that carry a ``variables`` list.

    Args:
        graph: Internal flat graph with ``nodes`` and ``edges`` keys.

    Returns:
        ``{"elements": {"nodes": [...], "edges": [...]}}`` ready for Cytoscape.js
        or the Dash GUI. Additional top-level fields may be added by ``main``
        (e.g. ``simulation_flow``) after this call.
    """
    return {
        "elements": {
            "nodes": wrap_nodes(graph["nodes"]),
            "edges": wrap_edges(graph["edges"]),
        }
    }
