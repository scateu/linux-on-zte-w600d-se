#!/usr/bin/env python3
from pathlib import Path
import sys


required = "ARCH_ROCKCHIP DEVTMPFS DEVTMPFS_MOUNT EXT4_FS VFAT_FS USB_XHCI_HCD USB_DWC3 USB_STORAGE SCSI BLK_DEV_SD PHY_ROCKCHIP_INNO_USB2 PHY_ROCKCHIP_NANENG_COMBO_PHY PHY_ROCKCHIP_NANENG_EDP INPUT_EVDEV USB_HID VT VT_CONSOLE DRM DRM_ROCKCHIP ROCKCHIP_ANALOGIX_DP ROCKCHIP_VOP2 DRM_PANEL_EDP DRM_FBDEV_EMULATION FRAMEBUFFER_CONSOLE PWM_ROCKCHIP BACKLIGHT_PWM MFD_RK8XX_I2C REGULATOR_RK808 SERIAL_8250_DW SERIAL_8250_CONSOLE FHANDLE CGROUPS".split()
configuration = Path(sys.argv[1]).read_text().splitlines()
missing = [option for option in required if f"CONFIG_{option}=y" not in configuration]
if missing:
    raise SystemExit("Required built-in options missing: " + ", ".join(missing))
print("Validated required built-in boot, display, keyboard and systemd options")
