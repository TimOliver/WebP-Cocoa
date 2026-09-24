#!/bin/sh
# BSD-3-Clause. Copyright (c) 2019-2026, Google, Tim Oliver.
# Keep the original entry point; resolve paths relative to the repository.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/scripts/build.py" "$@"
