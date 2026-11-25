#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
SOURCE=artifacts/ubuntu-w600d-rootfs.tar
CLEAN=artifacts/ubuntu-w600d-rootfs.no-container.tar
BACKUP=artifacts/ubuntu-w600d-rootfs.with-container-markers.tar
test -f "$SOURCE"
test ! -e "$CLEAN"
test ! -e "$BACKUP"
python3 scripts/strip-container-runtime-markers.py "$SOURCE" "$CLEAN"
mv "$SOURCE" "$BACKUP"
mv "$CLEAN" "$SOURCE"
sha256sum "$SOURCE" > artifacts/rootfs-SHA256SUMS
printf 'Hardware rootfs normalized; original archive retained at %s\n' "$BACKUP"
