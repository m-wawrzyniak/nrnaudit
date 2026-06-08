"""NeuronAudit: static analysis of NEURON project dependencies and parameters.

This package parses HOC-family and NMODL source files to build a dependency graph,
extract variables with inferred units, and record object-oriented simulation flow.

Entry points:
    - ``python -m src.main`` — run the analyzer CLI and write ``neuron_dependencies.cyjs``.
    - ``python -m src.gui_app`` — launch the Dash Cytoscape GUI for interactive inspection.
"""
