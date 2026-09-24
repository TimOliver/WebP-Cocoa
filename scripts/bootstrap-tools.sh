#!/bin/bash
# Install the exact upstream macOS tools under this checkout. No Homebrew state.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/build/tools"
mkdir -p "$TOOLS"

python3 - "$ROOT/toolchain.json" <<'PY'
import json, sys
tools = json.load(open(sys.argv[1]))["tools"]
assert tools["cmake"] == "4.1.1", "Update bootstrap download/hash with the lockfile"
assert tools["ninja"] == "1.13.2", "Update bootstrap download/hash with the lockfile"
PY

fetch() {
    local url="$1" output="$2" checksum="$3"
    if [[ ! -f "$output" ]] || ! echo "$checksum  $output" | shasum -a 256 -c - >/dev/null 2>&1; then
        curl --fail --location --retry 3 "$url" --output "$output.tmp"
        echo "$checksum  $output.tmp" | shasum -a 256 -c -
        mv "$output.tmp" "$output"
    fi
}

fetch "https://github.com/Kitware/CMake/releases/download/v4.1.1/cmake-4.1.1-macos-universal.tar.gz" \
    "$TOOLS/cmake.tar.gz" "3cd1da5341618645bdc85a3b99e273f29c4d48db2f545925a658db992e61f6f9"
fetch "https://github.com/ninja-build/ninja/releases/download/v1.13.2/ninja-mac.zip" \
    "$TOOLS/ninja.zip" "c99048673aa765960a99cf10c6ddb9f1fad506099ff0a0e137ad8960a88f321b"

tar -xzf "$TOOLS/cmake.tar.gz" -C "$TOOLS"
mkdir -p "$TOOLS/bin"
unzip -o -q "$TOOLS/ninja.zip" -d "$TOOLS/bin"
ln -sf "$TOOLS/cmake-4.1.1-macos-universal/CMake.app/Contents/bin/cmake" "$TOOLS/bin/cmake"
ln -sf "$TOOLS/cmake-4.1.1-macos-universal/CMake.app/Contents/bin/ctest" "$TOOLS/bin/ctest"
"$TOOLS/bin/cmake" --version
"$TOOLS/bin/ninja" --version
if [[ -n "${GITHUB_PATH:-}" ]]; then
    echo "$TOOLS/bin" >> "$GITHUB_PATH"
fi
echo "For local builds: export PATH=\"$TOOLS/bin:\$PATH\""
