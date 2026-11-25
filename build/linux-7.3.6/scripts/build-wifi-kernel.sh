#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
SOURCE="$ROOT/src/linux-7.3.6"
OUTPUT="$ROOT/out/kernel-7.3.6-wifi"
ARTIFACTS="$ROOT/artifacts/kernel-wifi"
export ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
test -f "$SOURCE/drivers/net/wireless/mediatek/mt76/mt7663s/mt7663s_w103d.c"
test -f "$SOURCE/include/linux/mt7663-combo.h"
test -f "$SOURCE/drivers/phy/rockchip/phy-rockchip-naneng-edp.c"
grep -Fq 'of_machine_is_compatible("zte,w600d-se")' \
    "$SOURCE/drivers/net/wireless/mediatek/mt76/mt7663s/mt7663s_w103d.c"
grep -Fq 'bool w103d = mt7663s_w103d_active();' \
    "$SOURCE/drivers/net/wireless/mediatek/mt76/mt7663s/sdio_mcu.c"
grep -Fq 'of_machine_is_compatible("zte,w600d-se")' \
    "$SOURCE/drivers/bluetooth/btmtksdio-w103d.h"
mkdir -p "$OUTPUT" "$ARTIFACTS" "$ROOT/logs"
exec > >(tee "$ROOT/logs/build-kernel-wifi-7.3.6.log") 2>&1
if [ ! -f "$OUTPUT/.config" ]; then
    cp "$ROOT/config/config-7.3.6-w600d-usb" "$OUTPUT/.config"
fi
for option in MT7663S BT_MTKSDIO; do
    "$SOURCE/scripts/config" --file "$OUTPUT/.config" --module "$option"
done
"$SOURCE/scripts/config" --file "$OUTPUT/.config" --enable MT7663S_W103D_COMBO \
    --set-str LOCALVERSION -w600d-usb-wifi --disable LOCALVERSION_AUTO
cp "$ROOT/"rk3568-zte-w600d-mainline*.dts "$SOURCE/arch/arm64/boot/dts/rockchip/"
make -C "$SOURCE" O="$OUTPUT" olddefconfig
python3 "$ROOT/scripts/validate-kernel-config.py" "$OUTPUT/.config"
grep -qx 'CONFIG_MT7663S=m' "$OUTPUT/.config"
grep -qx 'CONFIG_BT_MTKSDIO=m' "$OUTPUT/.config"
grep -qx 'CONFIG_MT7663S_W103D_COMBO=y' "$OUTPUT/.config"
test "$(make -s -C "$SOURCE" O="$OUTPUT" kernelrelease)" = 7.3.6-w600d-usb-wifi
make -C "$SOURCE" O="$OUTPUT" DTC_FLAGS=-@ -j"${JOBS:-24}" \
    Image modules rockchip/rk3568-zte-w600d-mainline-v6-wifi-bt.dtb
make -C "$SOURCE" O="$OUTPUT" INSTALL_MOD_PATH="$ARTIFACTS/modules" \
    INSTALL_MOD_STRIP=1 modules_install
cp "$OUTPUT/arch/arm64/boot/Image" "$ARTIFACTS/Image"
cp "$OUTPUT/arch/arm64/boot/dts/rockchip/rk3568-zte-w600d-mainline-v6-wifi-bt.dtb" \
    "$ARTIFACTS/rk3568-zte-w600d-mainline-v6-wifi-bt.dtb"
cp "$OUTPUT/.config" "$ARTIFACTS/config-7.3.6-w600d-usb-wifi"
cp "$OUTPUT/System.map" "$ARTIFACTS/System.map-7.3.6-w600d-usb-wifi"
printf '%s\n' 7.3.6-w600d-usb-wifi > "$ARTIFACTS/kernelrelease"
python3 "$ROOT/scripts/validate-board.py" "$ARTIFACTS/rk3568-zte-w600d-mainline-v6-wifi-bt.dtb"
tar --numeric-owner --owner=0 --group=0 -czf "$ARTIFACTS/modules-7.3.6-w600d-usb-wifi.tar.gz" \
    --exclude='lib/modules/7.3.6-w600d-usb-wifi/build' \
    --exclude='lib/modules/7.3.6-w600d-usb-wifi/source' \
    -C "$ARTIFACTS/modules" lib/modules/7.3.6-w600d-usb-wifi
cd "$ARTIFACTS"
sha256sum Image rk3568-zte-w600d-mainline-v6-wifi-bt.dtb \
    config-7.3.6-w600d-usb-wifi System.map-7.3.6-w600d-usb-wifi \
    modules-7.3.6-w600d-usb-wifi.tar.gz > SHA256SUMS
printf '\nWi-Fi kernel built under a distinct release; original Image/modules are untouched.\n'
