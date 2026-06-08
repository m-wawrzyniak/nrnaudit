"""Dash Cytoscape web UI entry point for the NEURON dependency graph."""

from __future__ import annotations

import argparse
import os
import webbrowser
from pathlib import Path

import dash_cytoscape as cyto
from dash import Dash, Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from src import utility_gui

cyto.load_extra_layouts()


def parse_args() -> argparse.Namespace:
    """Parse required --input and --data CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Dash Cytoscape GUI for the NEURON dependency graph."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        type=Path,
        help="Absolute path to the NEURON project root (resolves source_file paths).",
    )
    parser.add_argument(
        "--data",
        "-d",
        required=True,
        type=Path,
        help="Path to the parsed .cyjs/.json file.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address for the local web server (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port for the local web server (default: 8050).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable development mode (auto-reload and in-browser debugger).",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the GUI in the default web browser on startup.",
    )
    return parser.parse_args()


def validate_input_dir(input_dir: Path) -> None:
    """Ensure the NEURON project root exists, is a directory, and is readable."""
    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise SystemExit(f"Input path is not a directory: {input_dir}")
    if not os.access(input_dir, os.R_OK):
        raise SystemExit(f"Input directory is not readable: {input_dir}")


def validate_data_file(data_path: Path) -> None:
    """Ensure the graph file exists, is a file, and is readable."""
    if not data_path.exists():
        raise SystemExit(f"Data file does not exist: {data_path}")
    if not data_path.is_file():
        raise SystemExit(f"Data path is not a file: {data_path}")
    if not os.access(data_path, os.R_OK):
        raise SystemExit(f"Data file is not readable: {data_path}")


def validate_graph_data(graph_data: dict, data_path: Path) -> None:
    """Ensure the loaded JSON contains a Cytoscape elements block."""
    if "elements" not in graph_data:
        raise SystemExit(
            f"Data file is missing 'elements' key: {data_path}"
        )
    elements = graph_data["elements"]
    if not isinstance(elements, dict):
        raise SystemExit(
            f"Data file 'elements' must be an object: {data_path}"
        )
    if "nodes" not in elements or "edges" not in elements:
        raise SystemExit(
            f"Data file 'elements' must contain 'nodes' and 'edges': {data_path}"
        )


def is_hide_orphans_enabled(toggle_value: list[str] | None) -> bool:
    """Return True when unconnected orphan nodes should be hidden."""
    return toggle_value is not None and "hide" in toggle_value


def build_left_pane(
    full_elements: list[dict],
    visible_elements: list[dict],
    stylesheet: list[dict],
) -> html.Div:
    """Build the left pane with graph/code toggle and viewers."""
    toggle_bar = html.Div(
        [
            dcc.RadioItems(
                id="view-toggle",
                options=[
                    {"label": " Graph View", "value": "graph"},
                    {"label": " Source Code", "value": "code"},
                ],
                value="graph",
                inline=True,
            ),
            dcc.Dropdown(
                id="layout-selector",
                options=utility_gui.LAYOUT_OPTIONS,
                value=utility_gui.DEFAULT_LAYOUT,
                clearable=False,
                style={"width": "200px"},
            ),
            dcc.Checklist(
                id="hide-orphans-toggle",
                options=[
                    {
                        "label": " Hide unconnected orphan files",
                        "value": "hide",
                    }
                ],
                value=["hide"],
                inline=True,
            ),
            html.Button("Export .cyjs", id="btn-export-cyjs"),
        ],
        style={"display": "flex", "alignItems": "center", "gap": "16px"},
    )
    graph_wrapper = html.Div(
        id="graph-container",
        style=utility_gui.GRAPH_VISIBLE_STYLE,
        children=cyto.Cytoscape(
            id="cytoscape-graph",
            layout=utility_gui.build_cytoscape_layout(utility_gui.DEFAULT_LAYOUT),
            style={"width": "100%", "height": "100%"},
            elements=visible_elements,
            stylesheet=stylesheet,
        ),
    )
    code_wrapper = html.Div(
        id="code-container",
        style=utility_gui.HIDDEN_STYLE,
        children=html.Pre(id="code-viewer", style={"fontFamily": "monospace"}),
    )
    return html.Div(
        [toggle_bar, graph_wrapper, code_wrapper],
        style={
            "width": "75%",
            "display": "flex",
            "flexDirection": "column",
            "borderRight": "2px solid #ccc",
        },
    )


def build_right_pane() -> html.Div:
    """Build the inspector panel on the right."""
    return html.Div(
        [
            html.H3("Inspector", id="panel-title"),
            html.Div(id="panel-metadata"),
            html.Div(
                [
                    html.P("Click a node to view extracted variables and parameters."),
                    utility_gui.build_variables_datatable(),
                ],
                id="panel-variables",
            ),
        ],
        style={
            "width": "25%",
            "display": "flex",
            "flexDirection": "column",
            "padding": "20px",
            "backgroundColor": "#ffffff",
            "overflowY": "scroll",
        },
    )


def build_layout(
    full_elements: list[dict],
    visible_elements: list[dict],
    stylesheet: list[dict],
) -> html.Div:
    """Build the full split-screen application layout."""
    return html.Div(
        [
            dcc.Store(id="graph-elements-full", data=full_elements),
            build_left_pane(full_elements, visible_elements, stylesheet),
            build_right_pane(),
            dcc.Download(id="download-cyjs"),
        ],
        style={
            "display": "flex",
            "flexDirection": "row",
            "height": "100vh",
            "width": "100vw",
            "margin": "0",
        },
    )


def register_callbacks(
    app: Dash, repo_root: Path, extra_export_fields: dict | None = None
) -> None:
    """Register view-toggle, inspector, edit-sync, and export callbacks."""

    @app.callback(
        Output("graph-container", "style"),
        Output("code-container", "style"),
        Input("view-toggle", "value"),
    )
    def _toggle_view(view_value):
        return utility_gui.compute_view_styles(view_value)

    @app.callback(
        Output("cytoscape-graph", "layout"),
        Input("layout-selector", "value"),
    )
    def _switch_layout(layout_name):
        return utility_gui.build_cytoscape_layout(layout_name)

    @app.callback(
        Output("panel-title", "children"),
        Output("panel-metadata", "children"),
        Output("variables-datatable", "data"),
        Output("code-viewer", "children"),
        Input("cytoscape-graph", "tapNodeData"),
    )
    def _inspect_node(node_data):
        if node_data is None:
            return ("Inspector", "", [], "")
        title = node_data.get("id", "Inspector")
        metadata = utility_gui.build_metadata_block(node_data)
        variables = utility_gui.variables_to_table_data(
            node_data.get("variables", [])
        )
        source = utility_gui.read_source_code(
            repo_root, node_data.get("source_file", "")
        )
        return (title, metadata, variables, source)

    @app.callback(
        Output("graph-elements-full", "data"),
        Output("cytoscape-graph", "elements", allow_duplicate=True),
        Output("variables-datatable", "data", allow_duplicate=True),
        Input("variables-datatable", "data_timestamp"),
        State("variables-datatable", "data"),
        State("variables-datatable", "data_previous"),
        State("cytoscape-graph", "tapNodeData"),
        State("graph-elements-full", "data"),
        State("hide-orphans-toggle", "value"),
        prevent_initial_call=True,
    )
    def _sync_manual_edits(
        _timestamp,
        table_data,
        table_data_previous,
        node_data,
        full_elements,
        hide_toggle,
    ):
        if table_data_previous is None or node_data is None:
            raise PreventUpdate

        updated_table = utility_gui.apply_manual_overrides(
            table_data, table_data_previous
        )
        updated_elements = utility_gui.sync_variables_to_elements(
            full_elements, node_data["id"], updated_table
        )
        visible_elements = utility_gui.filter_visible_elements(
            updated_elements, is_hide_orphans_enabled(hide_toggle)
        )
        return updated_elements, visible_elements, updated_table

    @app.callback(
        Output("cytoscape-graph", "elements", allow_duplicate=True),
        Input("hide-orphans-toggle", "value"),
        State("graph-elements-full", "data"),
        prevent_initial_call=True,
    )
    def _apply_visibility_filter(hide_toggle, full_elements):
        return utility_gui.filter_visible_elements(
            full_elements, is_hide_orphans_enabled(hide_toggle)
        )

    @app.callback(
        Output("download-cyjs", "data"),
        Input("btn-export-cyjs", "n_clicks"),
        State("graph-elements-full", "data"),
        prevent_initial_call=True,
    )
    def _export_cyjs(n_clicks, full_elements):
        if n_clicks is None:
            raise PreventUpdate
        export_json = utility_gui.serialize_export(
            full_elements, extra_export_fields
        )
        return dcc.send_string(export_json, filename=utility_gui.EXPORT_FILENAME)


def create_app(graph_data: dict, repo_root: Path) -> Dash:
    """Create and configure the Dash application."""
    elements = utility_gui.extract_elements(graph_data)
    visible_elements = utility_gui.filter_visible_elements(elements, True)
    stylesheet = utility_gui.build_stylesheet()
    app = Dash(__name__)
    app.layout = build_layout(elements, visible_elements, stylesheet)
    extra_export_fields = {
        key: value
        for key, value in graph_data.items()
        if key != "elements"
    }
    register_callbacks(app, repo_root, extra_export_fields or None)
    return app


def main() -> None:
    """Load data, create the app, and start the local server."""
    args = parse_args()
    repo_root = args.input.resolve()
    data_path = args.data.resolve()

    validate_input_dir(repo_root)
    validate_data_file(data_path)

    graph_data = utility_gui.load_graph_data(data_path)
    validate_graph_data(graph_data, data_path)

    app = create_app(graph_data, repo_root)
    url = f"http://{args.host}:{args.port}"
    print(f"NeuronAudit GUI running at {url}")
    print("Press Ctrl+C to stop.")

    if args.open_browser:
        webbrowser.open(url)

    app.run(debug=args.debug, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
