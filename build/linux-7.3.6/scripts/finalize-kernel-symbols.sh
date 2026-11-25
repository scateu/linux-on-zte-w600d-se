#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
SOURCE="$ROOT/src/linux-7.3.6"
OUTPUT="$ROOT/out/kernel-7.3.6"
ARTIFACTS="$ROOT/artifacts/kernel"
export ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
exec > >(tee "$ROOT/logs/finalize-kernel.log") 2>&1
test "$(cat "$ARTIFACTS/kernelrelease")" = 7.3.6-w600d-usb
if ! rg -q 'RK3036_PLL_RATE\(564080000' "$SOURCE/drivers/clk/rockchip/clk-rk3568.c"; then
    patch --batch --fuzz=0 -d "$SOURCE" -p1 < "$ROOT/patches/0003-kdc-141020khz-vpll.patch"
fi
cp "$ROOT/"rk3568-zte-w600d-mainline*.dts "$SOURCE/arch/arm64/boot/dts/rockchip/"
make -C "$SOURCE" O="$OUTPUT" DTC_FLAGS=-@ -j"${JOBS:-24}" Image rockchip/rk3568-zte-w600d-mainline-v3.dtb
cp "$OUTPUT/arch/arm64/boot/Image" "$ARTIFACTS/Image"
cp "$OUTPUT/arch/arm64/boot/dts/rockchip/rk3568-zte-w600d-mainline-v3.dtb" "$ARTIFACTS/rk3568-zte-w600d-mainline.dtb"
cp "$OUTPUT/System.map" "$ARTIFACTS/System.map-7.3.6-w600d-usb"
python3 "$ROOT/scripts/validate-board.py" "$ARTIFACTS/rk3568-zte-w600d-mainline.dtb"
cd "$ARTIFACTS"
sha256sum Image rk3568-zte-w600d-mainline.dtb config-7.3.6-w600d-usb > SHA256SUMS
