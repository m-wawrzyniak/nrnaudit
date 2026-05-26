"""Cytoscape.js Graph JSON serialization adapter."""

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
    """Convert a flat build_graph dict to Cytoscape.js elements schema."""
    return {
        "elements": {
            "nodes": wrap_nodes(graph["nodes"]),
            "edges": wrap_edges(graph["edges"]),
        }
    }
