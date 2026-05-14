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
