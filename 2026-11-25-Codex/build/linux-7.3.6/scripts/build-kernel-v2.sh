#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
SOURCE="$ROOT/src/linux-7.3.6"
OUTPUT="$ROOT/out/kernel-7.3.6"
ARTIFACTS="$ROOT/artifacts/kernel"
JOBS=${JOBS:-24}
export ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
mkdir -p "$OUTPUT" "$ARTIFACTS" "$ROOT/logs"
exec > >(tee "$ROOT/logs/build-kernel-7.3.6.log") 2>&1
if ! test -f "$SOURCE/drivers/phy/rockchip/phy-rockchip-naneng-edp.c"; then
    patch --batch --fuzz=0 -d "$SOURCE" -p1 < "$ROOT/reference/cloudbook-mainline-6.12/patches/0009-phy-rockchip-naneng-edp.patch"
fi
if ! rg -q RK3568_EDP "$SOURCE/include/drm/bridge/analogix_dp.h"; then
    patch --batch --fuzz=0 -d "$SOURCE" -p1 < "$ROOT/patches/0002-rk3568-analogix-7.3.patch"
fi
cp "$ROOT/"rk3568-zte-w600d-mainline*.dts "$SOURCE/arch/arm64/boot/dts/rockchip/"
if ! test -f "$OUTPUT/.config"; then
    make -C "$SOURCE" O="$OUTPUT" defconfig
fi
for option in ARCH_ROCKCHIP DEVTMPFS DEVTMPFS_MOUNT EXT4_FS VFAT_FS NLS_CODEPAGE_437 NLS_ISO8859_1 NLS_UTF8 USB USB_XHCI_HCD USB_XHCI_PLATFORM USB_EHCI_HCD USB_EHCI_HCD_PLATFORM USB_OHCI_HCD USB_OHCI_HCD_PLATFORM USB_DWC3 USB_DWC3_HOST USB_STORAGE SCSI BLK_DEV_SD PHY_ROCKCHIP_INNO_USB2 PHY_ROCKCHIP_NANENG_COMBO_PHY PHY_ROCKCHIP_NANENG_EDP INPUT_EVDEV HID HID_GENERIC USB_HID VT VT_CONSOLE CONSOLE_TRANSLATIONS DRM DRM_ROCKCHIP ROCKCHIP_ANALOGIX_DP ROCKCHIP_VOP2 DRM_PANEL_EDP DRM_PANFROST DRM_FBDEV_EMULATION FB FRAMEBUFFER_CONSOLE FONT_8x16 FONT_TER16x32 PWM PWM_ROCKCHIP BACKLIGHT_CLASS_DEVICE BACKLIGHT_PWM REGULATOR_FIXED_VOLTAGE MFD_RK8XX_I2C REGULATOR_RK808 I2C_RK3X ROCKCHIP_IOMMU ROCKCHIP_PM_DOMAINS SERIAL_8250 SERIAL_8250_DW SERIAL_8250_CONSOLE USB_NET_DRIVERS USB_RTL8152 USB_NET_AX8817X USB_NET_AX88179_178A USB_NET_CDCETHER USB_NET_CDC_NCM CONFIGFS_FS FHANDLE INOTIFY_USER SIGNALFD TIMERFD EPOLL CGROUPS SECCOMP SECCOMP_FILTER NAMESPACES DEBUG_FS; do
    "$SOURCE/scripts/config" --file "$OUTPUT/.config" --enable "$option"
done
for option in CPU_FREQ FRAMEBUFFER_CONSOLE_DEFERRED_TAKEOVER USB_UAS DRM_SIMPLEDRM; do
    "$SOURCE/scripts/config" --file "$OUTPUT/.config" --disable "$option"
done
"$SOURCE/scripts/config" --file "$OUTPUT/.config" --set-str LOCALVERSION -w600d-usb --disable LOCALVERSION_AUTO
make -C "$SOURCE" O="$OUTPUT" olddefconfig
python3 "$ROOT/scripts/validate-kernel-config.py" "$OUTPUT/.config"
make -C "$SOURCE" O="$OUTPUT" -j"$JOBS" Image modules rockchip/rk3568-zte-w600d-mainline-v2.dtb
make -C "$SOURCE" O="$OUTPUT" INSTALL_MOD_PATH="$ARTIFACTS/modules" INSTALL_MOD_STRIP=1 modules_install
cp "$OUTPUT/arch/arm64/boot/Image" "$ARTIFACTS/Image"
cp "$OUTPUT/arch/arm64/boot/dts/rockchip/rk3568-zte-w600d-mainline-v2.dtb" "$ARTIFACTS/rk3568-zte-w600d-mainline.dtb"
cp "$OUTPUT/.config" "$ARTIFACTS/config-7.3.6-w600d-usb"
cp "$OUTPUT/System.map" "$ARTIFACTS/System.map-7.3.6-w600d-usb"
make -s -C "$SOURCE" O="$OUTPUT" kernelrelease > "$ARTIFACTS/kernelrelease"
cd "$ARTIFACTS"
sha256sum Image rk3568-zte-w600d-mainline.dtb config-7.3.6-w600d-usb > SHA256SUMS
printf '\nKernel build completed. Hardware validation still required.\n'
