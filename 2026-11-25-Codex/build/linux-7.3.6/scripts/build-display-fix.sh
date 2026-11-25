#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
SOURCE="$ROOT/src/linux-7.3.6"
OUTPUT="$ROOT/out/kernel-7.3.6"
ARTIFACTS="$ROOT/artifacts/kernel-edp-lanes-fix"
export ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
mkdir -p "$ARTIFACTS" "$ROOT/logs"
exec > >(tee "$ROOT/logs/build-kernel-edp-lanes-fix.log") 2>&1
test "$(make -s -C "$SOURCE" O="$OUTPUT" kernelrelease)" = 7.3.6-w600d-usb
grep -qx 'CONFIG_ROCKCHIP_ANALOGIX_DP=y' "$OUTPUT/.config"
bash "$ROOT/scripts/apply-edp-lane-fix.sh"
make -C "$SOURCE" O="$OUTPUT" DTC_FLAGS=-@ -j"${JOBS:-24}" Image rockchip/rk3568-zte-w600d-mainline-v3.dtb
cp "$OUTPUT/arch/arm64/boot/Image" "$ARTIFACTS/Image"
cp "$OUTPUT/arch/arm64/boot/dts/rockchip/rk3568-zte-w600d-mainline-v3.dtb" "$ARTIFACTS/rk3568-zte-w600d-mainline.dtb"
cp "$OUTPUT/System.map" "$ARTIFACTS/System.map-7.3.6-w600d-usb"
cp "$OUTPUT/.config" "$ARTIFACTS/config-7.3.6-w600d-usb"
python3 "$ROOT/scripts/validate-board.py" "$ARTIFACTS/rk3568-zte-w600d-mainline.dtb"
python3 "$ROOT/scripts/validate-kernel-config.py" "$ARTIFACTS/config-7.3.6-w600d-usb"
cd "$ARTIFACTS"
sha256sum Image rk3568-zte-w600d-mainline.dtb System.map-7.3.6-w600d-usb config-7.3.6-w600d-usb > SHA256SUMS
printf '\nDisplay-fix kernel built separately; hardware validation still required.\n'
