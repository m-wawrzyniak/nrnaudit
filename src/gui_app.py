"""Dash Cytoscape web UI entry point for the NEURON dependency graph."""

from __future__ import annotations

import argparse
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
    return parser.parse_args()


def build_left_pane(elements: list[dict], stylesheet: list[dict]) -> html.Div:
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
            elements=elements,
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


def build_layout(elements: list[dict], stylesheet: list[dict]) -> html.Div:
    """Build the full split-screen application layout."""
    return html.Div(
        [
            build_left_pane(elements, stylesheet),
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
        Output("cytoscape-graph", "elements"),
        Output("variables-datatable", "data", allow_duplicate=True),
        Input("variables-datatable", "data_timestamp"),
        State("variables-datatable", "data"),
        State("variables-datatable", "data_previous"),
        State("cytoscape-graph", "tapNodeData"),
        State("cytoscape-graph", "elements"),
        prevent_initial_call=True,
    )
    def _sync_manual_edits(
        _timestamp, table_data, table_data_previous, node_data, elements
    ):
        if table_data_previous is None or node_data is None:
            raise PreventUpdate

        updated_table = utility_gui.apply_manual_overrides(
            table_data, table_data_previous
        )
        updated_elements = utility_gui.sync_variables_to_elements(
            elements, node_data["id"], updated_table
        )
        return updated_elements, updated_table

    @app.callback(
        Output("download-cyjs", "data"),
        Input("btn-export-cyjs", "n_clicks"),
        State("cytoscape-graph", "elements"),
        prevent_initial_call=True,
    )
    def _export_cyjs(n_clicks, elements):
        if n_clicks is None:
            raise PreventUpdate
        export_json = utility_gui.serialize_export(elements, extra_export_fields)
        return dcc.send_string(export_json, filename=utility_gui.EXPORT_FILENAME)


def create_app(graph_data: dict, repo_root: Path) -> Dash:
    """Create and configure the Dash application."""
    elements = utility_gui.extract_elements(graph_data)
    stylesheet = utility_gui.build_stylesheet()
    app = Dash(__name__)
    app.layout = build_layout(elements, stylesheet)
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
    graph_data = utility_gui.load_graph_data(args.data)
    app = create_app(graph_data, repo_root)
    app.run(debug=True)


if __name__ == "__main__":
    main()
