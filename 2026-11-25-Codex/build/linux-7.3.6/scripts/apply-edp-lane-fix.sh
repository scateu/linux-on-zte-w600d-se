#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
SOURCE="$ROOT/src/linux-7.3.6"
PATCH="$ROOT/patches/0004-analogix-complete-phy-lanes.patch"
if patch --dry-run --batch --fuzz=0 --forward -d "$SOURCE" -p1 < "$PATCH"; then
    patch --batch --fuzz=0 --forward -d "$SOURCE" -p1 < "$PATCH"
else
    patch --dry-run --batch --force --fuzz=0 --reverse -d "$SOURCE" -p1 < "$PATCH"
fi
