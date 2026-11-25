#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
for candidate in \
    reference/cloudbook-mainline-6.12/patches/0005-mt76-mt7663s-w103d-isolated.patch \
    patches/0005b-mt7663-combo-linux-7.3.patch \
    reference/cloudbook-mainline-6.12/patches/0011-mt76-mt7663s-w103d-sanitize-wiphy.patch \
    reference/cloudbook-mainline-6.12/patches/0012-mt76-mt7663s-w103d-fix-band-switch-disconnect.patch \
    reference/cloudbook-mainline-6.12/patches/0013-mt76-mt7663s-w103d-tx-ampdu-and-sdio-throughput.patch \
    patches/0005c-mt7663-w600d-board-guards.patch; do
    git apply --check --directory=src/linux-7.3.6 "$candidate"
    git apply --directory=src/linux-7.3.6 "$candidate"
done
