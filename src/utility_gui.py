"""Pure helper utilities for the Dash Cytoscape GUI."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

from dash import dash_table, html

HIDDEN_STYLE = {"display": "none"}
GRAPH_VISIBLE_STYLE = {"display": "block", "flexGrow": "1"}
CODE_VISIBLE_STYLE = {
    "display": "block",
    "flexGrow": "1",
    "overflowY": "scroll",
    "backgroundColor": "#f4f4f4",
    "padding": "15px",
}

DEFAULT_LAYOUT = "dagre"
LAYOUT_OPTIONS = [
    {"label": "Hierarchical (Dagre)", "value": "dagre"},
    {"label": "Force-Directed (Cose)", "value": "cose"},
    {"label": "Circular", "value": "circle"},
]

VARIABLES_TABLE_COLUMNS = [
    {"name": "Variable", "id": "name", "editable": False},
    {"name": "Value/Unit", "id": "unit", "editable": True},
    {"name": "Method", "id": "resolution_method", "editable": False},
]
EXPORT_FILENAME = "annotated_neuron_dependencies.cyjs"
CORE_NODE_TYPES: frozenset[str] = frozenset({"hoc", "mechanism"})


def load_graph_data(data_path: Path) -> dict:
    """Load the parsed Cytoscape JSON file into memory."""
    with data_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def extract_elements(graph_data: dict) -> list[dict]:
    """Return a flat list of Cytoscape nodes and edges."""
    elements = graph_data["elements"]
    return elements["nodes"] + elements["edges"]


def build_stylesheet() -> list[dict]:
    """Return the Cytoscape stylesheet rules from the GUI spec."""
    return [
        {
            "selector": "node",
            "style": {
                "content": "data(label)",
                "text-valign": "center",
                "text-halign": "center",
                "color": "white",
                "text-outline-width": 2,
                "text-outline-color": "#333",
            },
        },
        {
            "selector": '[type = "hoc"]',
            "style": {
                "shape": "rectangle",
                "background-color": "#0074D9",
                "width": "label",
                "padding": "10px",
            },
        },
        {
            "selector": '[type = "mechanism"]',
            "style": {
                "shape": "ellipse",
                "background-color": "#FF851B",
            },
        },
        {
            "selector": '[type = "orphan"]',
            "style": {
                "shape": "round-rectangle",
                "background-color": "#AAAAAA",
                "width": "label",
                "padding": "8px",
                "color": "#333",
                "text-outline-width": 0,
            },
        },
        {
            "selector": "edge",
            "style": {
                "curve-style": "bezier",
                "target-arrow-shape": "none",
                "source-arrow-shape": "triangle",
                "label": "data(relation)",
                "text-rotation": "autorotate",
                "text-background-opacity": 1,
                "text-background-color": "#ffffff",
            },
        },
        {
            "selector": '[relation = "loads"]',
            "style": {
                "line-color": "#AAAAAA",
                "source-arrow-color": "#AAAAAA",
            },
        },
        {
            "selector": '[relation = "inserts"]',
            "style": {
                "line-color": "#FF4136",
                "source-arrow-color": "#FF4136",
                "line-style": "dashed",
            },
        },
    ]


def build_cytoscape_layout(layout_name: str) -> dict:
    """Return a Cytoscape layout dict with animated transitions."""
    if layout_name == "cose":
        return {
            "name": "cose",
            "animate": True,
            "nodeRepulsion": 12000,
            "idealEdgeLength": 150,
            "gravity": 0.08,
            "padding": 80,
            "nodeOverlap": 20,
        }
    return {"name": layout_name, "animate": True}


def filter_visible_elements(
    elements: list[dict], hide_unconnected_orphans: bool
) -> list[dict]:
    """Return elements visible in the graph; optionally hide unconnected orphans."""
    if not hide_unconnected_orphans:
        return elements

    nodes = [element for element in elements if "source" not in element["data"]]
    edges = [element for element in elements if "source" in element["data"]]

    visible_ids = {
        node["data"]["id"]
        for node in nodes
        if node["data"].get("type") in CORE_NODE_TYPES
    }

    changed = True
    while changed:
        changed = False
        for edge in edges:
            source = edge["data"]["source"]
            target = edge["data"]["target"]
            if source in visible_ids or target in visible_ids:
                if source not in visible_ids:
                    visible_ids.add(source)
                    changed = True
                if target not in visible_ids:
                    visible_ids.add(target)
                    changed = True

    filtered_nodes = [
        node for node in nodes if node["data"]["id"] in visible_ids
    ]
    filtered_edges = [
        edge
        for edge in edges
        if edge["data"]["source"] in visible_ids
        and edge["data"]["target"] in visible_ids
    ]
    return filtered_nodes + filtered_edges


def compute_view_styles(view_value: str) -> tuple[dict, dict]:
    """Return (graph_container_style, code_container_style) for the view toggle."""
    if view_value == "code":
        return HIDDEN_STYLE, CODE_VISIBLE_STYLE
    return GRAPH_VISIBLE_STYLE, HIDDEN_STYLE


def variables_to_table_data(variables: list[dict]) -> list[dict]:
    """Convert node variables to DataTable row dicts."""
    return [
        {
            "name": v.get("name", ""),
            "unit": v.get("unit", ""),
            "resolution_method": v.get("resolution_method", ""),
        }
        for v in variables
    ]


def build_variables_datatable() -> dash_table.DataTable:
    """Build the editable inspector DataTable."""
    return dash_table.DataTable(
        id="variables-datatable",
        columns=VARIABLES_TABLE_COLUMNS,
        data=[],
        row_deletable=False,
        sort_action="none",
        style_table={"overflowX": "auto"},
        style_cell={"fontSize": "13px", "textAlign": "left", "padding": "6px"},
    )


def apply_manual_overrides(
    current: list[dict], previous: list[dict]
) -> list[dict]:
    """Tag edited unit rows with resolution_method='manual'."""
    updated = [dict(row) for row in current]
    previous_by_name = {row["name"]: row for row in previous}
    for row in updated:
        old_row = previous_by_name.get(row["name"], {})
        if row.get("unit") != old_row.get("unit"):
            row["resolution_method"] = "manual"
    return updated


def sync_variables_to_elements(
    elements: list[dict], node_id: str, table_data: list[dict]
) -> list[dict]:
    """Write edited table rows back into the matching Cytoscape node."""
    updated_elements: list[dict] = []
    for element in elements:
        data = element.get("data", {})
        if data.get("id") != node_id or "source" in data:
            updated_elements.append(element)
            continue

        updated_element = copy.deepcopy(element)
        original_by_name = {
            variable["name"]: variable
            for variable in updated_element["data"].get("variables", [])
        }
        synced_variables = []
        for row in table_data:
            variable = dict(original_by_name.get(row["name"], {}))
            variable.update(
                {
                    "name": row["name"],
                    "unit": row["unit"],
                    "resolution_method": row.get("resolution_method", ""),
                }
            )
            synced_variables.append(variable)

        updated_element["data"]["variables"] = synced_variables
        if "variables_flat" in updated_element["data"]:
            updated_element["data"]["variables_flat"] = " | ".join(
                f"{variable['name']} ({variable['unit']})"
                for variable in synced_variables
            )
        updated_elements.append(updated_element)
    return updated_elements


def build_export_payload(
    elements: list[dict], extra_fields: dict | None = None
) -> dict:
    """Reconstruct the .cyjs export schema from live Cytoscape elements."""
    nodes = [element for element in elements if "source" not in element["data"]]
    edges = [element for element in elements if "source" in element["data"]]
    payload = {"elements": {"nodes": nodes, "edges": edges}}
    if extra_fields:
        payload.update(extra_fields)
    return payload


def serialize_export(
    elements: list[dict], extra_fields: dict | None = None
) -> str:
    """Serialize the export payload to indented JSON."""
    return json.dumps(
        build_export_payload(elements, extra_fields), indent=2, sort_keys=False
    )


def build_metadata_block(node_data: dict) -> html.Base:
    """Build the inspector metadata block for a selected node."""
    node_type = node_data.get("type", "")
    source_file = node_data.get("source_file", "")
    return html.Div(
        [html.P(f"Type: {node_type}"), html.P(f"Source: {source_file}")]
    )


def read_source_code(repo_root: Path, source_file: str) -> str:
    """Read the raw source file for a selected node."""
    if not source_file:
        return "No source file associated with this node."

    path = os.path.join(str(repo_root.resolve()), source_file)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return f"Error: Could not load source file at {path}."
