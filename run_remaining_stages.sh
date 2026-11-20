#!/bin/bash
# Root wrapper delegating to scripts/run_remaining_stages.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/scripts/run_remaining_stages.sh" "$@"
