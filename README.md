# Project proposal: NeuronAudit

## 1. Introduction
In computational neuroscience, the normative methodology for developing a model of a specific neuronal circuit is to 
first explore existing models that attempt to capture similar qualitative phenomena (e.g., oscillogenesis). 

A systematic exploration of these models involves querying [ModelDB](https://modeldb.science/) for a specific structure,
cell, or phenomenon and auditing the resulting code repositories. However, this process is time-consuming.
ModelDB does not impose a standardized schema for parameters or results, and models are written in a variety of 
programming languages (NEURON, GENESIS, Python, etc.). It is a mess of unstructured data.

### Validation 
Once a model is selected for exploration, it is standard procedure to validate whether the circuit encompasses
biologically plausible parameters. Modellers must verify if the parametrization (e.g. cell capacitance) corresponds 
to the empirical data. [NeuroElectro](https://neuroelectro.org/) acts as a curated repository of *in-vivo* 
electrophysiological properties and 
provides an API, making it the primary database for biological soundness. Currently, bridging the gap between ModelDB 
code and NeuroElectro data is an entirely manual process.

---

## 2. Example problem
Consider an exploration of gamma-band oscillogenesis in the olfactory bulb based on an existing model from 
**Li & Cleland (2017)** ([ModelDB 232097](https://modeldb.science/232097)).

* **Execution:** The model is primarily written in NEURON. To explore its functionality, one typically executes `mosinit.hoc` to reproduce the data shared in the original article.
* **The Problem:** Validating the parametrization of components (cells or synapses) is difficult. Parameters are scattered across numerous files with limited descriptions. A modeller must manually go through files, verify units, and then compare them with NeuroElectro.

> **Example Workflow:** 
>  To check the capacitance of a template Mitral cell, one must navigate to:
> `Tab: Model Files` > `OBGAMMA/MC_def.hoc`.
> Only on **line 137** is the parameter provided:
> `cm = 1.2 // uF/cm^2; Shen et al. JNP, 1999`

Checking a synapse conductance requires navigating a completely different file.
This lack of centralization makes it highly inefficient to compare multiple models to choose the best candidate.

---

## 3. Proposed solution

### Minimum viable product
A **data scraper** for NEURON projects from ModelDB that parses code files to:
* **Map project structure** - present the importing/loading order of files to clarify the model structure.
* **Extract the parameters** - automatically identify all assigned parameters and record their source files.

### Optional features
* **Unit deduction** - automatically identify the units for each parameter (e.g. mV, nS, µF/cm²).
* **Parameter interpretation** - provide descriptions or explanations for what a parameter represents.
* **Biological mapping** - identify parameterized components by name e.g. mapping `MC_def.hoc` > **Olfactory bulb Mitral cell**.
* **Interpretability classification** - distinguish between parameters with direct physical interpretation and those with abstract interpretation, e.g. variables in Izhikevich models.
* **NeuroElectro integration** - fetch experimental data for the identified components via the NeuroElectro API.
* **Comparison reporting** - generate an automated report comparing model parameters against the experimental biological distributions.

---

## 4. Running the dependency analyzer

From the repository root, run the static analyzer on a NEURON project directory. Output is written as Cytoscape.js-compatible JSON (`neuron_dependencies.cyjs`) under the output directory.

```bash
python -m src.main --input ground_truth_cases/232097/OBGAMMA/ --output tmp
```

Required arguments:

* `--input` / `-i` — root directory of the NEURON codebase to analyze
* `--output` / `-o` — directory where `neuron_dependencies.cyjs` is created (created if missing)

HOC discovery includes `.hoc`, `.tem`, and `.oc` files. All successfully parsed mechanisms from `.mod` files appear as graph nodes; HOC `insert` statements add `inserts` edges only to the subset that is actually used. `.mod` files without an extractable mechanism name appear as `mod_file` nodes. Orphan file nodes (gray in the GUI) are created for non-HOC, non-mod files with these extensions by default: `.txt`, `.md`, `.dat`, `.py`, `.html`. Orphan files are not parsed for variables.

Optional argument:

* `--orphan-extensions` — additional extensions to include as orphan nodes (merged with defaults), e.g.:

```bash
python -m src.main -i ./model -o out --orphan-extensions csv h
```

---

## 5. Running the visualization GUI

Install GUI dependencies (from the repository root):

```bash
pip install -r requirements.txt
```

Generate the graph file first (if you do not already have a `.cyjs`):

```bash
python -m src.main -i /path/to/NEURON/project -o /path/to/output
```

Launch the local web GUI from the repository root:

```bash
python -m src.gui_app \
  -i /path/to/NEURON/project \
  -d /path/to/output/neuron_dependencies.cyjs
```

Or use the launcher script (macOS/Linux):

```bash
chmod +x run_gui.sh
./run_gui.sh /path/to/NEURON/project /path/to/output/neuron_dependencies.cyjs
```

Open the URL printed in the terminal (default: `http://127.0.0.1:8050`).

Required arguments:

* `--input` / `-i` — NEURON project root; must match the directory used when generating the `.cyjs` file (resolves source code paths in the inspector)
* `--data` / `-d` — path to the parsed `neuron_dependencies.cyjs` (or equivalent JSON)

Optional arguments:

* `--host` — bind address (default: `127.0.0.1`)
* `--port` — port number (default: `8050`)
* `--open-browser` — open the GUI in your default browser on startup
* `--debug` — enable development mode (auto-reload and in-browser debugger)

The toolbar includes **Hide unconnected orphan files** (on by default). When checked, only HOC/mechanism nodes and orphan files connected to them via edges are shown. Uncheck to display all orphan file nodes. Export always includes the full graph regardless of the toggle.

Enable **Draw edge** to add user-defined links with two clicks: tap the source node, then the target. New edges use `relation: "annotated"` (green dotted lines) and are included in exported `.cyjs` files.

Example with browser auto-open:

```bash
python -m src.gui_app \
  -i ground_truth_cases/232097/OBGAMMA/ \
  -d out/neuron_dependencies.cyjs \
  --open-browser
```

---
