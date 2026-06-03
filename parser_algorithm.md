# NEURON project directory parsing algorithm
This document contains a brief description of the algorithm used for 
parsing NEURON files. Within each step there are examples and 
**Implementation** comments.

---

## Phase 1: Repository Traversal & Normalization
**Goal:** Inventory all relevant files and establish a universal addressing system.

### Algorithm
1. Perform a recursive directory traversal starting from the provided `--input` root.
2. Ignore common compiled/binary directories (e.g., `x86_64`, `arm64`, `.git`).
3. Collect absolute paths for all files ending in `.mod` and `.hoc`.
4. **Implementation:** Convert all absolute paths to relative paths stemming from the repository root. All node IDs in the final graph must use these relative paths to ensure consistency when matching `load_file` strings later.

---

## Phase 2: Mod File (NMODL) Parsing
**Goal:** Map `.mod` files to their declared mechanism names.

### Algorithm
1. **Comment Stripping (Critical Step):**
   * Remove block comments encapsulated by `COMMENT` and `ENDCOMMENT`.
   * Remove inline comments starting with `?` or `~` to the end of the line.
2. **Block Targeting:**
   * Scan for the `NEURON` block declaration: `NEURON\s*\{`
3. **Mechanism Extraction:**
   * Inside the `NEURON` block, scan for one of three declaration keywords: `SUFFIX`, `POINT_PROCESS`, or `ARTIFICIAL_CELL`.
   * **Implementation:** Capture the immediate alphanumeric string following the keyword.
   * *Example:* `SUFFIX hh` -> capture `hh`.
4. **Data Structure:**
   * Store in a Python dictionary: `{ "mechanism_name": "relative/path/to/file.mod" }`.

---

## Phase 3: Hoc File Parsing
**Goal:** Determine outgoing edges from `.hoc` files (other `.hoc` files loaded, and mechanisms inserted).

### Algorithm
1. **Comment Stripping (Critical Step):**
   * Remove inline comments: `//` to end-of-line.
   * Remove block comments: `/*` through `*/`.
   * *Warning:* ModelDB repositories contain heavy amounts of commented-out legacy code. Parsing without stripping will yield false-positive dependencies.
2. **File Loading Extraction (Hoc-to-Hoc Edges):**
   * Target keywords: `load_file`, `xopen`, `ropen`.
   * **Implementation:** Match these keywords followed by parentheses or whitespace, capturing the string literal inside the quotes. 
   * *Regex Concept:* `(?:load_file|xopen|ropen)\s*\(\s*"([^"]+)"\s*\)` (Note: occasionally they are called without parentheses, e.g., `xopen("file")` or `xopen "file"`. The planner must account for both).
3. **Mechanism Insertion Extraction (Hoc-to-Mod Edges):**
   * Target keyword: `insert`.
   * **Implementation:** Capture the word immediately following the `insert` keyword. 
   * *Example:* `soma insert pas` -> capture `pas`.
   * Validate the captured string against the dictionary generated in Phase 2. If it exists in the map, register the dependency.

---

## Phase 4: Graph Resolution & Output Schema
**Goal:** Resolve collected references and serialize into a strictly formatted JSON graph in the `--output` directory.

### Edge Resolution Rules
* **Hoc Loads:** A `.hoc` file might load `"nrngui.hoc"`. The analyzer must resolve this filename against the normalized relative paths gathered in Phase 1. 
* **Mod Inserts:** A `.hoc` file inserts a mechanism (e.g., `hh`). The target node ID is the mechanism name itself, not the `.mod` file path, as this is how it is conceptually represented in NEURON.
