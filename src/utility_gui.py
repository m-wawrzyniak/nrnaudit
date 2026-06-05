"""Pure helper utilities for the Dash Cytoscape GUI."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dash import html

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
    return {"name": layout_name, "animate": True}


def compute_view_styles(view_value: str) -> tuple[dict, dict]:
    """Return (graph_container_style, code_container_style) for the view toggle."""
    if view_value == "code":
        return HIDDEN_STYLE, CODE_VISIBLE_STYLE
    return GRAPH_VISIBLE_STYLE, HIDDEN_STYLE


def build_variables_table(variables: list[dict]) -> html.Base:
    """Build an inspector table for extracted variables."""
    if not variables:
        return html.P("No variables detected.")

    header = html.Tr(
        [html.Th("Name"), html.Th("Unit/Value"), html.Th("Method")]
    )
    rows = [
        html.Tr(
            [
                html.Td(v.get("name", "")),
                html.Td(v.get("unit", "")),
                html.Td(v.get("resolution_method", "")),
            ]
        )
        for v in variables
    ]
    return html.Table(
        [header, *rows],
        style={"width": "100%", "borderCollapse": "collapse", "fontSize": "13px"},
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
