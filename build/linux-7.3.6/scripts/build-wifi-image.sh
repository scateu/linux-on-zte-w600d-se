#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
test ! -d src/linux-7.3.6 || { printf 'Use a clean recipe directory for this full build\n' >&2; exit 1; }
test ! -e artifacts/ubuntu-w600d-rootfs.tar
mkdir -p out/kernel-7.3.6
cp config/config-7.3.6-w600d-usb out/kernel-7.3.6/.config
bash scripts/prepare-sources.sh
bash scripts/build-userspace-v2.sh
bash scripts/build-kernel-v2.sh
bash scripts/apply-edp-lane-fix.sh
bash scripts/finalize-kernel-symbols.sh
bash scripts/apply-wifi-patches.sh
bash scripts/build-wifi-kernel.sh
bash scripts/fetch-mt7663-firmware.sh
export KERNEL_ARTIFACTS=artifacts/kernel-wifi
export BOARD_DTB=rk3568-zte-w600d-mainline-v6-wifi-bt.dtb
export IMAGE="$ROOT/artifacts/w600d-ubuntu-xfce-7.3.6-wifi-20261125.img"
bash scripts/build-desktop-rootfs-v2.sh
bash scripts/normalize-container-markers.sh
bash scripts/assemble-image.sh
