#!/bin/bash
# Root wrapper delegating to scripts/run_all_pipelines.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/scripts/run_all_pipelines.sh" "$@"
