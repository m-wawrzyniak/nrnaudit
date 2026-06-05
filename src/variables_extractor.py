"""Pass 2: variable and unit extraction from .mod and .hoc files."""

from __future__ import annotations

import re
from pathlib import Path

from src import mod_parser, utils

VARIABLE_BLOCKS = ("PARAMETER", "ASSIGNED", "STATE", "CONSTANT")
NEURON_UNITS: frozenset[str] = frozenset(
    {
        "mV",
        "V",
        "ms",
        "s",
        "mA/cm2",
        "uA/cm2",
        "nA",
        "pA",
        "uA",
        "mho/cm2",
        "S/cm2",
        "mS/cm2",
        "uS",
        "nS",
        "pS",
        "mho",
        "mM",
        "uM",
        "nM",
        "um",
        "um2",
        "um3",
        "cm2",
        "uF/cm2",
        "uF/cm^2",
        "pF",
        "ohm*cm",
        "Mohm",
        "ohm",
        "/ms",
        "1/ms",
        "Hz",
        "kHz",
        "degC",
        "mol",
        "umol",
    }
)
KNOWN_UNITS = NEURON_UNITS

UNIT_ALIASES: dict[str, str] = {
    "ohm.cm": "ohm*cm",
    "ohm.cm2": "ohm*cm",
    "ohm*cm2": "ohm*cm",
    "ohmcm": "ohm*cm",
    "ohmcm2": "ohm*cm",
    "ms-1": "1/ms",
    "ms^-1": "1/ms",
    "/s": "Hz",
}

UNIT_LEVENSHTEIN_MAX = 2
RESOLUTION_FILE_NA = "NA"
ION_VOLTAGE_UNIT = "mV"
ION_CURRENT_UNIT = "mA/cm2"
ION_CONCENTRATION_UNIT = "mM"

HOC_CONTROL_KEYWORDS = frozenset(
    {"for", "while", "if", "else", "return", "func", "proc", "print", "printf", "iterator"}
)

_NAME_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)")
_UNIT_RE = re.compile(r"\(([^)]*)\)")
_EXPLICIT_HOC_RE = re.compile(
    r"\b(?:strdef|objref|create|double)\s+([A-Za-z_][A-Za-z0-9_]*)"
)
_INLINE_COMMENT_BODY_RE = re.compile(r"//(.*)$")
_SUFFIX_RE = re.compile(r"\bSUFFIX\s+([A-Za-z_][A-Za-z0-9_]*)")
_POINT_PROCESS_RE = re.compile(r"\bPOINT_PROCESS\s+([A-Za-z_][A-Za-z0-9_]*)")
_READ_WRITE_RE = re.compile(
    r"\b(?:READ|WRITE)\s+(.*?)(?=\bREAD\b|\bWRITE\b|\bVALENCE\b|$)"
)
_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_][\w.\s]*?)\s*=\s*([^=].*)$")
_SIDE_IDENT_RE = re.compile(
    r"(?<![0-9A-Za-z_.])[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
)
_CANON_RE = re.compile(r"[^a-z0-9]")


def extract_block_body(text: str, block_name: str) -> str | None:
    """Return inner text of the first `block_name { ... }` block, or None."""
    pattern = re.compile(r"\b" + re.escape(block_name) + r"\s*\{")
    m = pattern.search(text)
    if m is None:
        return None
    return utils.extract_brace_body(text, m.end())


def parse_mod_block_lines(block_body: str) -> list[dict]:
    """Extract [{name, unit}] from a single NMODL declaration block body."""
    results: list[dict] = []
    stripped_body = utils.strip_mod_comments(block_body)
    for raw_line in stripped_body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("?") or line.startswith("~"):
            continue
        name_match = _NAME_RE.match(line)
        if name_match is None:
            continue
        name = name_match.group(1)
        unit_match = _UNIT_RE.search(line)
        unit = unit_match.group(1).strip() if unit_match else "???"
        results.append({"name": name, "unit": unit})
    return results


def extract_mod_variables(repo_root: Path, mod_relpath: str) -> list[dict]:
    """Return deduplicated [{name, unit}] from all declaration blocks in a .mod file."""
    text = utils.read_text_file(repo_root / mod_relpath)
    seen_names: set[str] = set()
    variables: list[dict] = []
    for block_name in VARIABLE_BLOCKS:
        body = extract_block_body(text, block_name)
        if body is None:
            continue
        for var in parse_mod_block_lines(body):
            if var["name"] not in seen_names:
                seen_names.add(var["name"])
                variables.append(var)
    return variables


def classify_ion_unit(var_name: str) -> str:
    """Map a USEION variable name to a standard unit by NEURON naming convention."""
    if var_name.startswith("e"):
        return ION_VOLTAGE_UNIT
    if var_name.startswith("i"):
        return ION_CURRENT_UNIT
    if var_name.endswith("i") or var_name.endswith("o"):
        return ION_CONCENTRATION_UNIT
    return "???"


def extract_useion_variables(neuron_body: str) -> list[str]:
    """Return identifiers listed after READ/WRITE across all USEION lines."""
    names: list[str] = []
    for line in neuron_body.splitlines():
        if "USEION" not in line:
            continue
        for m in _READ_WRITE_RE.finditer(line):
            names.extend(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", m.group(1)))
    return names


def extract_suffix_name(neuron_body: str) -> str | None:
    """Return the SUFFIX name declared in a NEURON block, or None."""
    m = _SUFFIX_RE.search(neuron_body)
    return m.group(1) if m else None


def extract_point_process_name(neuron_body: str) -> str | None:
    """Return the POINT_PROCESS name declared in a NEURON block, or None."""
    m = _POINT_PROCESS_RE.search(neuron_body)
    return m.group(1) if m else None


def build_mod_registry_entries(repo_root: Path, mod_relpath: str) -> dict[str, str]:
    """Map exposed variable names to units for one .mod file per namespace rules."""
    text = utils.read_text_file(repo_root / mod_relpath)
    stripped = utils.strip_mod_comments(text)
    entries: dict[str, str] = {}
    neuron_body = mod_parser.extract_neuron_block_body(stripped)
    if neuron_body is None:
        return entries
    for ion_var in extract_useion_variables(neuron_body):
        entries.setdefault(ion_var, classify_ion_unit(ion_var))
    block_vars = extract_mod_variables(repo_root, mod_relpath)
    suffix = extract_suffix_name(neuron_body)
    point_process = extract_point_process_name(neuron_body)
    if suffix is not None:
        for var in block_vars:
            entries.setdefault(f"{var['name']}_{suffix}", var["unit"])
    elif point_process is not None:
        for var in block_vars:
            entries.setdefault(var["name"], var["unit"])
    return entries


def build_global_mod_registry(
    repo_root: Path, mod_relpaths: list[str]
) -> tuple[dict[str, str], dict[str, str]]:
    """Merge per-file registries into global name->unit and name->mod-filename maps."""
    registry: dict[str, str] = {}
    registry_files: dict[str, str] = {}
    for mod_relpath in mod_relpaths:
        mod_filename = Path(mod_relpath).name
        for name, unit in build_mod_registry_entries(repo_root, mod_relpath).items():
            if name not in registry:
                registry[name] = unit
                registry_files[name] = mod_filename
    return registry, registry_files


def uf_add(parent: dict[str, str], node: str) -> None:
    """Register a node as its own singleton set if not already present."""
    if node not in parent:
        parent[node] = node


def uf_find(parent: dict[str, str], node: str) -> str:
    """Return the representative root of a node, with path compression."""
    root = node
    while parent[root] != root:
        root = parent[root]
    while parent[node] != root:
        parent[node], node = root, parent[node]
    return root


def uf_union(parent: dict[str, str], a: str, b: str) -> None:
    """Merge the sets containing a and b."""
    uf_add(parent, a)
    uf_add(parent, b)
    ra, rb = uf_find(parent, a), uf_find(parent, b)
    if ra != rb:
        parent[ra] = rb


def uf_groups(parent: dict[str, str]) -> list[set[str]]:
    """Return all disjoint sets as a list of member sets."""
    groups: dict[str, set[str]] = {}
    for node in parent:
        groups.setdefault(uf_find(parent, node), set()).add(node)
    return list(groups.values())


def first_token(text: str) -> str:
    """Return the first identifier in a string, or '' if none."""
    m = _NAME_RE.search(text)
    return m.group(0) if m else ""


def sanitize_side(side: str) -> str | None:
    """Extract a single variable name from one side of an assignment (strip prefix/number)."""
    m = _SIDE_IDENT_RE.search(side)
    if m is None:
        return None
    return m.group(0).split(".")[-1]


def split_inline_comment(line: str) -> tuple[str, str]:
    """Split a line into (code, comment) at the first '//' (comment kept with '//')."""
    idx = line.find("//")
    if idx == -1:
        return line, ""
    return line[:idx], line[idx:]


def extract_hoc_explicit_variables(text: str) -> list[dict]:
    """Return [{name, unit: 'N/A'}] for strdef/objref/create/double declarations."""
    return [
        {"name": m.group(1), "unit": "N/A"}
        for m in _EXPLICIT_HOC_RE.finditer(text)
    ]


def edit_distance(a: str, b: str) -> int:
    """Compute the Levenshtein edit distance between two strings."""
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(current[j - 1] + 1, previous[j] + 1, previous[j - 1] + (ca != cb))
            )
        previous = current
    return previous[-1]


def normalize_unit_token(token: str) -> str:
    """Strip trailing punctuation and apply explicit unit aliases."""
    cleaned = token.strip().strip(";,)!")
    lowered = cleaned.lower()
    return UNIT_ALIASES.get(lowered, cleaned)


def match_unit_by_levenshtein(token: str) -> str | None:
    """Return the closest KNOWN_UNITS entry within UNIT_LEVENSHTEIN_MAX edits."""
    if len(token) < 4:
        return None
    best: str | None = None
    best_dist = UNIT_LEVENSHTEIN_MAX + 1
    for known in KNOWN_UNITS:
        dist = edit_distance(token.lower(), known.lower())
        if dist <= UNIT_LEVENSHTEIN_MAX and dist < best_dist:
            best = known
            best_dist = dist
    return best


def resolve_unit_token(token: str) -> str | None:
    """Resolve a single comment token to a known unit, or None."""
    normalized = normalize_unit_token(token)
    if normalized in KNOWN_UNITS:
        return normalized
    return match_unit_by_levenshtein(normalized)


def try_spaced_unit_token(first: str, second: str) -> str | None:
    """Resolve two adjacent comment tokens like 'ohm cm2' to a known unit."""
    t1 = normalize_unit_token(first).lower()
    t2 = normalize_unit_token(second).lower()
    if t1 == "ohm" and t2 in {"cm", "cm2", "*cm", "*cm2"}:
        return "ohm*cm"
    if t1 in {"ohm", "ohm*"} and t2 in {"cm", "cm2"}:
        return "ohm*cm"
    combined = normalize_unit_token(f"{first}{second}")
    if combined in KNOWN_UNITS:
        return combined
    combined_spaced = normalize_unit_token(f"{first}*{second}")
    if combined_spaced in KNOWN_UNITS:
        return combined_spaced
    return match_unit_by_levenshtein(combined)


def extract_units_from_comment_body(body: str) -> list[str]:
    """Return all known units found in a // comment body, longest matches first."""
    tokens = re.findall(r"\S+", body)
    found: list[str] = []
    seen: set[str] = set()
    index = 0
    while index < len(tokens):
        token = tokens[index]
        unit = None
        consumed = 0
        if index + 1 < len(tokens):
            unit = try_spaced_unit_token(token, tokens[index + 1])
            if unit is not None:
                consumed = 1
        if unit is None:
            unit = resolve_unit_token(token)
        if unit is not None and unit not in seen:
            found.append(unit)
            seen.add(unit)
        index += 1 + consumed
    for known in sorted(KNOWN_UNITS, key=len, reverse=True):
        if known in body and known not in seen:
            found.append(known)
            seen.add(known)
    return found


def guess_unit_from_comment(line: str) -> str:
    """Return the best unit string from a // comment, or '???'."""
    m = _INLINE_COMMENT_BODY_RE.search(line)
    if m is None:
        return "???"
    units = extract_units_from_comment_body(m.group(1))
    return units[0] if units else "???"


def is_parsed_unit(unit: str) -> bool:
    """Return True when a unit string represents a successfully parsed value."""
    return unit != "???"


def collect_comment_hint(code: str, comment: str) -> tuple[str, str] | None:
    """Return (var_name, unit) when a line carries a known unit in its // comment."""
    unit = guess_unit_from_comment(comment)
    if not is_parsed_unit(unit):
        return None
    m = _ASSIGN_RE.match(code)
    if m is not None:
        lhs = sanitize_side(m.group(1))
        if lhs is not None:
            return lhs, unit
    explicit = _EXPLICIT_HOC_RE.search(code)
    if explicit is not None:
        return explicit.group(1), unit
    stripped = code.strip()
    if stripped and first_token(stripped) not in HOC_CONTROL_KEYWORDS:
        ident = sanitize_side(stripped)
        if ident is not None:
            return ident, unit
    return None


def update_routine_scope(
    code: str, in_routine: bool, bracket_depth: int
) -> tuple[bool, int]:
    """Track func/proc entry and brace depth for Pass 2 scope blinding."""
    bracket_depth += code.count("{")
    bracket_depth -= code.count("}")
    stripped = code.lstrip()
    if stripped.startswith(("func ", "proc ")):
        in_routine = True
    if in_routine and bracket_depth == 0:
        in_routine = False
    return in_routine, bracket_depth


def should_skip_pass2_line(raw_line: str, code: str) -> bool:
    """Return True when Pass 2 must ignore this line (Pass 3 handles it separately)."""
    if "= new " in raw_line:
        return True
    stripped = code.lstrip()
    for prefix in ("for ", "while ", "if ", "else ", "return "):
        if stripped.startswith(prefix):
            return True
    return False


def collect_hoc_pools(text: str) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Return (parent, heuristic_hints, explicit_vars) from block-comment-stripped HOC text."""
    parent: dict[str, str] = {}
    heuristic_hints: dict[str, str] = {}
    explicit_vars: dict[str, str] = {
        var["name"]: "N/A" for var in extract_hoc_explicit_variables(text)
    }
    in_routine = False
    bracket_depth = 0
    for raw_line in text.splitlines():
        code, comment = split_inline_comment(raw_line)
        in_routine, bracket_depth = update_routine_scope(
            code, in_routine, bracket_depth
        )
        if in_routine or should_skip_pass2_line(raw_line, code):
            continue
        hint = collect_comment_hint(code, comment)
        if hint is not None:
            heuristic_hints[hint[0]] = hint[1]
        m = _ASSIGN_RE.match(code)
        if m is None:
            continue
        lhs_raw, rhs_raw = m.group(1), m.group(2)
        if first_token(lhs_raw) in HOC_CONTROL_KEYWORDS:
            continue
        lhs = sanitize_side(lhs_raw)
        if lhs is None:
            continue
        rhs = sanitize_side(rhs_raw)
        if rhs is None:
            uf_add(parent, lhs)
        else:
            uf_union(parent, lhs, rhs)
    return parent, heuristic_hints, explicit_vars


def canonical(name: str) -> str:
    """Lowercase a name and strip all non-alphanumeric characters."""
    return _CANON_RE.sub("", name.lower())


def match_pool_against_registry(
    members: list[str],
    registry: dict[str, str],
    registry_files: dict[str, str],
    canonical_registry: dict[str, str],
    canonical_registry_files: dict[str, str],
) -> tuple[str, str, str] | None:
    """Run registry tiers 0-3; return (unit, method, mod filename) on first parsed match."""
    for var in members:
        if var in registry and is_parsed_unit(registry[var]):
            return registry[var], "exact", registry_files[var]
    for var in members:
        c = canonical(var)
        if c in canonical_registry and is_parsed_unit(canonical_registry[c]):
            return canonical_registry[c], "canonical", canonical_registry_files[c]
    for var in members:
        if len(var) > 3:
            for key, unit in registry.items():
                if var in key and is_parsed_unit(unit):
                    return unit, "substring", registry_files[key]
    for var in members:
        if len(var) > 4:
            for key, unit in registry.items():
                if edit_distance(var, key) <= 2 and is_parsed_unit(unit):
                    return unit, "levenshtein", registry_files[key]
    return None


def match_pool_registry_undefined(
    members: list[str],
    registry: dict[str, str],
    registry_files: dict[str, str],
    canonical_registry: dict[str, str],
    canonical_registry_files: dict[str, str],
) -> str | None:
    """Return the mod filename when a pool member matches the registry with unit '???'."""
    for var in members:
        if var in registry and not is_parsed_unit(registry[var]):
            return registry_files[var]
    for var in members:
        c = canonical(var)
        if c in canonical_registry and not is_parsed_unit(canonical_registry[c]):
            return canonical_registry_files[c]
    for var in members:
        if len(var) > 3:
            for key, unit in registry.items():
                if var in key and not is_parsed_unit(unit):
                    return registry_files[key]
    for var in members:
        if len(var) > 4:
            for key, unit in registry.items():
                if edit_distance(var, key) <= 2 and not is_parsed_unit(unit):
                    return registry_files[key]
    return None


def match_pool_waterfall(
    members: list[str],
    registry: dict[str, str],
    registry_files: dict[str, str],
    canonical_registry: dict[str, str],
    canonical_registry_files: dict[str, str],
    heuristic_hints: dict[str, str],
) -> tuple[str, str, str] | None:
    """Run the full resolution waterfall including HOC // comment unit hints."""
    match = match_pool_against_registry(
        members,
        registry,
        registry_files,
        canonical_registry,
        canonical_registry_files,
    )
    if match is not None:
        return match
    undefined_file = match_pool_registry_undefined(
        members,
        registry,
        registry_files,
        canonical_registry,
        canonical_registry_files,
    )
    if undefined_file is not None:
        return "???", "resolved_undefined", undefined_file
    for var in members:
        if var in heuristic_hints:
            return heuristic_hints[var], "heuristic", RESOLUTION_FILE_NA
    return None


def resolve_pool(
    pool: set[str],
    registry: dict[str, str],
    registry_files: dict[str, str],
    canonical_registry: dict[str, str],
    canonical_registry_files: dict[str, str],
    heuristic_hints: dict[str, str],
) -> list[dict]:
    """Resolve one equivalence pool into variable dicts with resolution metadata."""
    members = sorted(pool)
    match = match_pool_waterfall(
        members,
        registry,
        registry_files,
        canonical_registry,
        canonical_registry_files,
        heuristic_hints,
    )
    if match is not None:
        unit, method, resolution_file = match
    else:
        unit, method, resolution_file = "???", "unresolved", RESOLUTION_FILE_NA
    return [
        {
            "name": v,
            "unit": unit,
            "resolution_method": method,
            "resolution_file": resolution_file,
        }
        for v in members
    ]


def build_canonical_registry_maps(
    registry: dict[str, str], registry_files: dict[str, str]
) -> tuple[dict[str, str], dict[str, str]]:
    """Build canonical name->unit and name->mod-filename maps from the global registry."""
    canonical_registry: dict[str, str] = {}
    canonical_registry_files: dict[str, str] = {}
    for key, unit in registry.items():
        c = canonical(key)
        if c not in canonical_registry:
            canonical_registry[c] = unit
            canonical_registry_files[c] = registry_files[key]
    return canonical_registry, canonical_registry_files


def extract_hoc_variables(
    repo_root: Path,
    hoc_relpath: str,
    registry: dict[str, str],
    registry_files: dict[str, str],
) -> list[dict]:
    """Resolve a .hoc file's variables via equivalence pooling + the registry waterfall."""
    raw_text = utils.read_text_file(repo_root / hoc_relpath)
    block_stripped = utils.strip_hoc_block_comments(raw_text)
    parent, heuristic_hints, explicit_vars = collect_hoc_pools(block_stripped)
    canonical_registry, canonical_registry_files = build_canonical_registry_maps(
        registry, registry_files
    )
    resolved: list[dict] = [
        {
            "name": name,
            "unit": unit,
            "resolution_method": "explicit_declaration",
            "resolution_file": RESOLUTION_FILE_NA,
        }
        for name, unit in explicit_vars.items()
    ]
    for group in uf_groups(parent):
        pool = group - explicit_vars.keys()
        if pool:
            resolved.extend(
                resolve_pool(
                    pool,
                    registry,
                    registry_files,
                    canonical_registry,
                    canonical_registry_files,
                    heuristic_hints,
                )
            )
    return resolved


def build_hoc_variables_map(
    repo_root: Path,
    hoc_relpaths: list[str],
    registry: dict[str, str],
    registry_files: dict[str, str],
) -> dict[str, list[dict]]:
    """Map each hoc relpath to its resolved variables list."""
    return {
        p: extract_hoc_variables(repo_root, p, registry, registry_files)
        for p in hoc_relpaths
    }


def build_mod_variables_map(
    repo_root: Path, mod_relpaths: list[str]
) -> dict[str, list[dict]]:
    """Map each mod relpath to its extracted variables list."""
    return {p: extract_mod_variables(repo_root, p) for p in mod_relpaths}
