"""Pass 3: object-oriented simulation flow extraction from HOC and NMODL files.

Builds a blueprint registry of instantiable classes (NEURON builtins, mod
``POINT_PROCESS``/``ARTIFICIAL_CELL`` declarations, and hoc ``begintemplate``
names), then scans HOC files for ``objref``/``new`` instantiations and
dot-parameter bindings.

Exports ``{"blueprints": sorted class names, "instances": [...]}`` embedded in
the Cytoscape JSON. The ``blueprints`` field is a name list, not full parameter
dicts. Static analysis only.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path

from src import utils, variables_extractor

NEURON_BUILTIN_CLASSES = frozenset(
    {"IClamp", "VClamp", "AlphaSynapse", "NetStim", "NetCon", "Vector", "List", "String"}
)

_MOD_CLASS_RE = re.compile(
    r"\b(?:POINT_PROCESS|ARTIFICIAL_CELL)\s+([A-Za-z_][A-Za-z0-9_]*)"
)
_TEMPLATE_RE = re.compile(r"\bbegintemplate\s+([A-Za-z_][A-Za-z0-9_]*)")
_OBJREF_RE = re.compile(r"^\s*objref\s+(.*)$")
_NEW_ASSIGN_RE = re.compile(
    r"^\s*(.+?)\s*=\s*new\s+([A-Za-z_][A-Za-z0-9_]*)"
)
_DOT_ASSIGN_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?\.[A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^=].*)$"
)


def extract_mod_class_names(repo_root: Path, mod_relpath: str) -> list[str]:
    """Return POINT_PROCESS / ARTIFICIAL_CELL class names declared in one .mod file."""
    text = utils.read_text_file(repo_root / mod_relpath)
    stripped = utils.strip_mod_comments(text)
    return _MOD_CLASS_RE.findall(stripped)


def extract_template_names(repo_root: Path, hoc_relpath: str) -> list[str]:
    """Return names declared by ``begintemplate`` in one HOC-family file."""
    text = utils.read_text_file(repo_root / hoc_relpath)
    stripped = utils.strip_hoc_comments(text)
    return _TEMPLATE_RE.findall(stripped)


def extract_parameter_defaults(repo_root: Path, mod_relpath: str) -> dict[str, str]:
    """Return {param_name: default_value} from a .mod file's PARAMETER block."""
    text = utils.read_text_file(repo_root / mod_relpath)
    stripped = utils.strip_mod_comments(text)
    body = variables_extractor.extract_block_body(stripped, "PARAMETER")
    if body is None:
        return {}
    return utils.parse_parameter_block_defaults(body)


def extract_mod_blueprints(repo_root: Path, mod_relpath: str) -> dict[str, dict]:
    """Return {class_name: {'parameters': {defaults}}} for one .mod file."""
    class_names = extract_mod_class_names(repo_root, mod_relpath)
    if not class_names:
        return {}
    parameters = extract_parameter_defaults(repo_root, mod_relpath)
    return {name: {"parameters": dict(parameters)} for name in class_names}


def build_blueprint_registry(
    repo_root: Path, hoc_relpaths: list[str], mod_relpaths: list[str]
) -> dict[str, dict]:
    """Build the instantiable class blueprint registry.

    Seeds NEURON builtin classes (empty parameters), merges ``POINT_PROCESS``/
    ``ARTIFICIAL_CELL`` declarations from ``.mod`` files with PARAMETER defaults,
    and adds hoc ``begintemplate`` names (empty parameters when not overridden).

    Args:
        repo_root: Absolute path to the NEURON project root.
        hoc_relpaths: Discovered HOC-family relative paths.
        mod_relpaths: Discovered ``.mod`` relative paths.

    Returns:
        ``{class_name: {"parameters": {param: default_value}}}``.
    """
    registry: dict[str, dict] = {
        name: {"parameters": {}} for name in NEURON_BUILTIN_CLASSES
    }
    for mod_relpath in mod_relpaths:
        registry.update(extract_mod_blueprints(repo_root, mod_relpath))
    for hoc_relpath in hoc_relpaths:
        for name in extract_template_names(repo_root, hoc_relpath):
            registry.setdefault(name, {"parameters": {}})
    return registry


def parse_objref_pointers(line: str) -> list[str]:
    """Return base pointer names declared on an 'objref' line (array brackets stripped)."""
    m = _OBJREF_RE.match(line)
    if m is None:
        return []
    pointers: list[str] = []
    for token in m.group(1).split(","):
        base = utils.strip_array_index(token)
        if base:
            pointers.append(base)
    return pointers


def parse_instantiation(line: str) -> tuple[str, str, bool, str] | None:
    """Parse ``<lhs> = new <Class>`` into instantiation components.

    Args:
        line: Single HOC source line (comments should be stripped).

    Returns:
        Tuple ``(base_name, class_name, is_array, location)`` where
        ``base_name`` has array brackets removed, ``is_array`` is True when
        the LHS token contained ``[...]``, and ``location`` is any leading
        scope prefix before the final name token. Returns ``None`` when the
        line does not match the ``new`` assignment pattern.
    """
    m = _NEW_ASSIGN_RE.match(line)
    if m is None:
        return None
    location, name_token = utils.split_location_and_name(m.group(1).strip())
    class_name = m.group(2)
    is_array = "[" in name_token
    base_name = utils.strip_array_index(name_token)
    return base_name, class_name, is_array, location


def parse_parameter_binding(line: str) -> tuple[str, str, str] | None:
    """Parse a dot-parameter assignment into pointer, param, and value.

    Matches ``pointer.param = value`` and ``pointer[idx].param = value`` forms.

    Args:
        line: Single HOC source line (comments should be stripped).

    Returns:
        Tuple ``(pointer, param, value)`` with array brackets stripped from
        ``pointer``, or ``None`` when the line does not match.
    """
    m = _DOT_ASSIGN_RE.match(line)
    if m is None:
        return None
    lhs = m.group(1)
    value = m.group(2).strip().rstrip(";").strip()
    pointer_part, param = lhs.split(".", 1)
    pointer = utils.strip_array_index(pointer_part)
    return pointer, param.strip(), value


def extract_file_instances(
    repo_root: Path, hoc_relpath: str, blueprint_registry: dict[str, dict]
) -> dict[str, dict]:
    """Extract object instances and parameter bindings from one HOC-family file.

    Only records ``new`` instantiations when the class is in ``blueprint_registry``
    and the base name was declared via ``objref``. Dot-parameter assignments
    override blueprint defaults on matching instances.

    Args:
        repo_root: Absolute path to the NEURON project root.
        hoc_relpath: Repository-relative HOC-family path.
        blueprint_registry: Output of ``build_blueprint_registry``.

    Returns:
        ``{instance_name: {class, is_array, location, parameters}}``.
    """
    text = utils.read_text_file(repo_root / hoc_relpath)
    lines = utils.strip_hoc_comments(text).splitlines()

    active_pointers: set[str] = set()
    for line in lines:
        active_pointers.update(parse_objref_pointers(line))

    extracted_instances: dict[str, dict] = {}
    for line in lines:
        parsed = parse_instantiation(line)
        if parsed is None:
            continue
        base_name, class_name, is_array, location = parsed
        if class_name in blueprint_registry and base_name in active_pointers:
            blueprint = blueprint_registry[class_name]
            extracted_instances[base_name] = {
                "class": class_name,
                "is_array": is_array,
                "location": location,
                "parameters": copy.deepcopy(blueprint["parameters"]),
            }

    for line in lines:
        binding = parse_parameter_binding(line)
        if binding is None:
            continue
        pointer, param, value = binding
        if pointer in extracted_instances:
            extracted_instances[pointer]["parameters"][param] = value

    return extracted_instances


def flatten_instances(per_file_instances: dict[str, dict[str, dict]]) -> list[dict]:
    """Flatten {hoc_relpath: {name: props}} into a sorted list of instance records."""
    records: list[dict] = []
    for hoc_relpath in sorted(per_file_instances):
        instances = per_file_instances[hoc_relpath]
        for name in sorted(instances):
            props = instances[name]
            records.append(
                {
                    "id": name,
                    "class": props["class"],
                    "source_file": hoc_relpath,
                    "is_array": props["is_array"],
                    "location": props["location"],
                    "parameters": props["parameters"],
                }
            )
    return records


def build_simulation_flow(
    repo_root: Path, hoc_relpaths: list[str], mod_relpaths: list[str]
) -> dict:
    """Run Pass 3 and return the ``simulation_flow`` export subdictionary.

    Args:
        repo_root: Absolute path to the NEURON project root.
        hoc_relpaths: Discovered HOC-family relative paths.
        mod_relpaths: Discovered ``.mod`` relative paths.

    Returns:
        ``{"blueprints": sorted class names, "instances": [...]}``.
        ``blueprints`` is a sorted list of registered class name strings, not
        the full ``{class: {parameters}}`` registry. Each instance record
        contains ``id``, ``class``, ``source_file``, ``is_array``, ``location``,
        and ``parameters``.
    """
    blueprint_registry = build_blueprint_registry(repo_root, hoc_relpaths, mod_relpaths)
    per_file_instances: dict[str, dict[str, dict]] = {
        hoc_relpath: extract_file_instances(repo_root, hoc_relpath, blueprint_registry)
        for hoc_relpath in hoc_relpaths
    }
    return {
        "blueprints": sorted(blueprint_registry),
        "instances": flatten_instances(per_file_instances),
    }
