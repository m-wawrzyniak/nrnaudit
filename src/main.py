"""CLI entry point for the NEURON static dependency analyzer.

Orchestrates Phases 1–4, Pass 2 (variables), Pass 3 (simulation flow), and
Cytoscape export into a single ``neuron_dependencies.cyjs`` JSON file under
the user-specified output directory.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from src import (
    cytoscape_export,
    graph_builder,
    hoc_parser,
    mod_parser,
    simulation_flow,
    traversal,
    utils,
    variables_extractor,
)


def parse_args() -> argparse.Namespace:
    """Parse required --input and --output CLI arguments."""
    parser = argparse.ArgumentParser(
        description="NEURON static dependency analyzer."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        type=Path,
        help="Path to the NEURON repository root.",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        type=Path,
        help=f"Directory where {utils.OUTPUT_FILENAME} will be written.",
    )
    parser.add_argument(
        "--orphan-extensions",
        nargs="+",
        default=None,
        metavar="EXT",
        help="Additional orphan file extensions to include (e.g. csv h). "
        "Merged with defaults: .txt .md .dat .py .html",
    )
    return parser.parse_args()


def validate_input_dir(input_dir: Path) -> None:
    """Ensure the input path exists, is a directory, and is readable."""
    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise SystemExit(f"Input path is not a directory: {input_dir}")
    if not os.access(input_dir, os.R_OK):
        raise SystemExit(f"Input directory is not readable: {input_dir}")


def main() -> None:
    """Run the full static analysis pipeline and write Cytoscape JSON.

    Pipeline order:
        1. Phase 1 — discover HOC-family, ``.mod``, and orphan files.
        2. Phase 2 — build mechanism map from ``.mod`` files.
        3. Phase 3 — parse HOC loads and inserts.
        4. Pass 2 — extract variables/units from ``.mod`` and HOC files.
        5. Phase 4 — assemble flat graph with variables on nodes.
        6. Cytoscape export — wrap graph in ``elements`` schema.
        7. Pass 3 — attach ``simulation_flow`` to the export payload.
        8. Write ``neuron_dependencies.cyjs`` under ``--output``.

    Reads CLI args via ``parse_args`` and validates the input directory.
    """
    args = parse_args()
    validate_input_dir(args.input)
    repo_root = args.input.resolve()

    orphan_exts = utils.merge_orphan_extensions(args.orphan_extensions)
    hoc_relpaths, mod_relpaths = traversal.discover_files(repo_root)
    orphan_relpaths = traversal.discover_orphan_files(
        repo_root, hoc_relpaths, mod_relpaths, orphan_exts
    )
    mechanism_map = mod_parser.build_mechanism_map(repo_root, mod_relpaths)
    parsed_hoc = hoc_parser.parse_all_hoc(repo_root, hoc_relpaths)
    global_mod_registry, global_mod_registry_files = (
        variables_extractor.build_global_mod_registry(repo_root, mod_relpaths)
    )
    hoc_variables = variables_extractor.build_hoc_variables_map(
        repo_root, hoc_relpaths, global_mod_registry, global_mod_registry_files
    )
    mod_variables = variables_extractor.build_mod_variables_map(
        repo_root, mod_relpaths
    )
    graph = graph_builder.build_graph(
        hoc_relpaths,
        mod_relpaths,
        parsed_hoc,
        mechanism_map,
        hoc_variables,
        mod_variables,
        orphan_relpaths,
    )
    cytoscape_graph = cytoscape_export.to_cytoscape(graph)
    flow = simulation_flow.build_simulation_flow(
        repo_root, hoc_relpaths, mod_relpaths
    )
    cytoscape_graph["simulation_flow"] = flow
    target = utils.write_json(cytoscape_graph, args.output)
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
