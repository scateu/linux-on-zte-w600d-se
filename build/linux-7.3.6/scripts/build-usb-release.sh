#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
VERSION=${1:?Usage: build-usb-release.sh RELEASE_ID}
[[ "$VERSION" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]*$ ]]
NAME="w600d-ubuntu-xfce-7.3.6-usb-$VERSION"
RELEASE="$ROOT/artifacts/releases/$VERSION"
test ! -e "$RELEASE" || { printf "Release already exists: %s\n" "$RELEASE" >&2; exit 1; }
test "$(cat "$ROOT/artifacts/kernel-wifi/kernelrelease")" = 7.3.6-w600d-usb-wifi
mkdir -p "$ROOT/out"
WORK=$(mktemp -d "$ROOT/out/usb-release-XXXXXX")
printf "Assembly work and logs: %s\n" "$WORK"
cp -a "$ROOT/rootfs" "$ROOT/scripts" "$ROOT/extlinux.conf" "$ROOT/panel-edid.base64" "$WORK/"
cd "$WORK"
mkdir artifacts out
ln -s "$ROOT/artifacts/kernel-wifi" artifacts/kernel-wifi
ln -s "$ROOT/artifacts/firmware" artifacts/firmware
export KERNEL_ARTIFACTS=artifacts/kernel-wifi
export BOARD_DTB=rk3568-zte-w600d-mainline-v6-wifi-bt.dtb
(cd "$KERNEL_ARTIFACTS" && sha256sum -c SHA256SUMS)
USB_PREVIEW=1 bash scripts/build-desktop-rootfs-v2.sh
bash scripts/normalize-container-markers.sh
IMAGE="$WORK/artifacts/$NAME.img" IMAGE_MIB=4096 bash scripts/assemble-image.sh
zstd -t "artifacts/$NAME.img.zst"
mkdir -p "$ROOT/artifacts/releases"
mkdir "$RELEASE"
cd artifacts
sha256sum "$NAME.img.zst" > SHA256SUMS
sha256sum "$NAME.img" > IMAGE-SHA256SUMS
mv -- "$NAME.img" "$NAME.img.zst" SHA256SUMS IMAGE-SHA256SUMS \
    usb-partitions.json rootfs-package-versions.txt "$RELEASE/"
printf "Release files: %s\n" "$RELEASE"
