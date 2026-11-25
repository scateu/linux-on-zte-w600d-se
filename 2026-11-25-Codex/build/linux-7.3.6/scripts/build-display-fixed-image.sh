#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
bash scripts/prepare-sources.sh
bash scripts/build-userspace-v2.sh
bash scripts/build-kernel-v2.sh
bash scripts/apply-edp-lane-fix.sh
bash scripts/finalize-kernel-symbols.sh
bash scripts/build-desktop-rootfs-v2.sh
bash scripts/normalize-container-markers.sh
bash scripts/assemble-image.sh
