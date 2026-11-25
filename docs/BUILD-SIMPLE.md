# Ubuntu to a bootable W600D USB: tiny explanation

- **Ubuntu is the house:** use official Ubuntu 24.04.5 ARM64 Base; add systemd, XFCE, LightDM and NetworkManager.
- **DTS is the wiring map:** describe this laptop's screen, keyboard, trackpad and SDIO radio; compile v6-wifi-bt into a DTB.
- **Kernel is the brain:** build Linux 7.3.6 with our eDP patches and board-adapted CloudBook radio patches; produce `Image`, DTB and matching modules.
- **USB has two boxes:** first 512 MB FAT32 for boot; the rest ext4 for Ubuntu.
- **Put files in their boxes:** FAT gets Image/DTB; ext4 gets Ubuntu, `/lib/modules/7.3.6-w600d-usb-wifi/` and verified MediaTek firmware/license.
- **Extlinux gives directions:** FAT `/extlinux/extlinux.conf` names the Image, DTB, `root=PARTUUID=24c0d202-02` and `init=/sbin/init`.
- **If Docker helped build Ubuntu:** strip `/.dockerenv` after export; keep only the intended UART getty, not the competing console getty.
- **Power on:** patched original eMMC U-Boot reads the USB and starts Linux; removing USB while powered off keeps the original Android path. Physical Android fallback still needs testing.

Full clean-directory recipe: `build/linux-7.3.6/scripts/build-wifi-image.sh`.
Details: `BUILD-CURRENT.md`, `DIY-FROM-UPSTREAM.md` and `TRACKPAD-AND-WIFI.md`.

Current checkpoint: display/keyboard, I2C4 trackpad input and Ethernet DHCP work; Wi-Fi now scans both bands and Bluetooth initializes. Wi-Fi login/traffic and trackpad right-click/scrolling still need user acceptance. NTP works, ttyS2 works and console-getty stays inactive after reboot. Change only relevant USB files during debugging. See `TRACKPAD-AND-WIFI.md` and `CURRENT.md`.
