#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <NEURON_PROJECT_ROOT> <GRAPH_CYJS_FILE> [-- extra gui_app args]" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")" && pwd)"
NEURON_ROOT="$(cd "$1" && pwd)"
CYJS_PATH="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
shift 2

cd "$ROOT"
exec python -m src.gui_app -i "$NEURON_ROOT" -d "$CYJS_PATH" "$@"
