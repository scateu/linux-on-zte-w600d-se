# Ubuntu to a bootable W600D USB: tiny explanation

- **Ubuntu is the house:** use official Ubuntu 24.04.5 ARM64 Base; add systemd, XFCE, LightDM and NetworkManager.
- **DTS is the wiring map:** describe this laptop's panel, backlight and keyboard power; compile the final v3 DTS into a DTB.
- **Kernel is the brain:** build Linux 7.3.6 with our RK3568 eDP patches and required USB/input/display drivers; produce `Image`, DTB and matching modules.
- **USB has two boxes:** first 512 MB FAT32 for boot; the rest ext4 for Ubuntu.
- **Put files in their boxes:** FAT gets `/boot/Image` and `/boot/rk3568-zte-w600d-mainline.dtb`; ext4 gets Ubuntu and `/lib/modules/7.3.6-w600d-usb/`.
- **Extlinux gives directions:** FAT `/extlinux/extlinux.conf` names the Image, DTB, `root=PARTUUID=24c0d202-02` and `init=/sbin/init`.
- **If Docker helped build Ubuntu:** strip `/.dockerenv` after export; keep only the intended UART getty, not the competing console getty.
- **Power on:** patched original eMMC U-Boot reads the USB and starts Linux; removing USB while powered off keeps the original Android path. Physical Android fallback still needs testing.

Full clean-output build recipe on `trash`: `/home/k/codex-workdir-nov-24-2026/scripts/build-display-fixed-image.sh`.
Details: `ROOTFS-CONTAINER-MARKERS.md`, `USB-FILE-ONLY-DEBUG.md`, and `linux-7.3.6-build/BUILD-VERIFIED.md` (the new entry supersedes its older entry command).

Current hardware checkpoint: internal text display and Ctrl+Alt+F1 keyboard switching work; a mouse cursor is visible in graphics mode. Complete XFCE session and trackpad operation are not yet verified. Ethernet and its cable are inserted; DHCP is not yet checked. The user stopped `console-getty`, but UART has not returned a usable shell; restart `serial-getty@ttyS2` from tty1 before further live diagnosis. During debugging, change only relevant USB files, not the whole 32 GB image.
