# Current recorded checkpoint — November 25, 2026

This consolidates the last hardware observations on November 24, 2026 (+08:00)
and the user's subsequent confirmations. The laptop was not queried or changed
while making this snapshot; device names, sessions, and addresses must be
rediscovered before acting.

Workspace-only cleanup on November 25 moved useful research into this tree,
compressed and verified recovery backups, removed obsolete/duplicate data and
preserved both Git repositories. It adds no new hardware acceptance results.
The four consolidated bootloader/logo/hardware guides and `docs/RECOVERY.md`
are indexed in README.md; older notes are now in `docs/history/`.

## Latest live follow-up — November 25, 2026

- The laptop was queried and reboot-tested after the archival snapshot below.
- The v4 DTB enabled factory-wired I2C4 power/reset and HID-over-I2C. Actual
  trackpad ID is **093a:0255**; `hid_multitouch` and Xorg/libinput bind it.
  Motion, contact/release and left-button events were recorded. Tap-to-click
  is configured and loaded after reboot; right-click behavior remains to verify.
- Docker markers were backed up/removed. `systemd-detect-virt` reports `none`,
  udev and ttyS2 work, and console-getty stays inactive across reboot.
- USB Ethernet uses `cdc_ether`. The Ubuntu NetworkManager default excluded
  Ethernet; a narrow override now permits it. DHCP automatically reconnects
  after service restart and a complete reboot: last address `192.168.1.220/24`.
- Network time synchronized automatically, correcting the stale 2017 RTC date.
- The v5-sdio diagnostic boot used the original kernel #3. SDIO at
  `fe2c0000` enumerates **037a:7603** (Wi-Fi) and **037a:7663** (Bluetooth):
  the same MediaTek MT7663S pair as CloudBook. Factory Unisoc nodes were
  misleading; no Unisoc module was installed.
- The current live boot uses **7.3.6-w600d-usb-wifi #1** and **v6-wifi-bt**.
  CloudBook's isolated driver/stability patches required both the 7.3 lifecycle
  adaptation and our 0005c board-ID guards. After the latter module-only update,
  Wi-Fi initializes, loads N9 firmware, and NetworkManager successfully scans
  many 2.4 GHz and 5 GHz access points. Association/DHCP over Wi-Fi and
  sustained throughput still need a user-selected network and acceptance.
- Bluetooth initializes through the shared combo coordinator with result=0;
  a powered HCI controller is present. No Bluetooth pairing has been tested.
- Display remains connected at 1920x1080, Xorg/libinput retains trackpad input,
  and Ethernet DHCP/NTP return after reboot. The boot FAT mount timeout is now
  90 seconds and its read-only mount succeeds after the final reboot.
- The normal entry selects `/boot/Image.wifi-20261125`. Original Image/v3 rescue
  entries are unchanged. Radio-module rollback is under
  `/root/w600d-debug-backups/20261125T1512-radio-board-guards`; the previous v5
  boot config/DTB is under `20261125T145740-wifi-bt-v6` in the same backup root.
- Fresh full-image entry: `build/linux-7.3.6/scripts/build-wifi-image.sh`.
  Kernel/module builds and file-only live deployment are validated. This new
  complete-image wrapper has syntax checks, not an end-to-end image/flash test.
- Original Image, v3/v4 DTBs, old modules, rescue entries and Android/eMMC are
  preserved. USB FAT is read-only except during guarded, file-only updates.
- Investigation/rollback/build details: `docs/TRACKPAD-AND-WIFI.md`.

The following sections preserve the older November 24 checkpoint and are
historical where they differ from this live follow-up.

## Confirmed on the corrected mainline boot

- ZTE W600D SE, RK3568, 2 GB RAM; USB Ubuntu 24.04.5/XFCE.
- Kernel `7.3.6-w600d-usb`, corrected build banner:
  `#3 SMP PREEMPT Tue Nov 24 17:10:47 CST 2026`.
- Internal screen showed a blinking cursor and then a mouse cursor.
- User confirmed Ctrl+Alt+F1 works and subsequently entered sudo commands on tty1.
- Xorg, xfce4-session, xfwm4, xfce4-panel and xfdesktop ran. The last query
  reported no failed systemd units. A complete visible XFCE desktop has not
  been explicitly accepted by the user.
- Keyboard USB ID `258a:0001`; the last mainline input inventory had keyboard,
  system-control, consumer-control and RK805 power-key devices, but no trackpad.
- The UART root shell was recovered after the user stopped `console-getty`
  and restarted `serial-getty@ttyS2` on tty1. Those changes were runtime-only.

## Last network and trackpad state

- USB Ethernet `0fe6:9900` identified as ICS Advent USB 10/100 LAN.
- Last confirmed interface `enxbc2b02039829`, MAC `bc:2b:02:03:98:29`:
  DOWN, no IP address, unmanaged by NetworkManager.
- The follow-up DHCP activation command was interrupted; whether it reached
  the target is unknown. Recheck before repeating it. The actual bound Ethernet
  driver has not been established.
- Trackpad is not working and did not enumerate in the last mainline input
  inventory. Older vendor-kernel touchpad observations are not mainline proof.

## What is on the current USB

- Original vendor eMMC U-Boot loads USB extlinux directly; no USB U-Boot.
- The November 24 approximately 17:20 update changed **only FAT `/boot/Image`**.
- Previous kernel retained as `/boot/Image.pre-lanes-20261124`.
- DTB, extlinux, MBR, ext4 root and eMMC were unchanged in that update.
- No full-disk read-back was completed; the user explicitly requested skipping it.
- The live USB rootfs still had `/.dockerenv` in the last confirmed query.
  Its persistent removal/masking and a clean reboot have not been completed.

## What is ready on the build host

- Corrected tested artifacts are in `artifacts/kernel-edp-lanes-fix/` on `trash`;
  copies are in this snapshot's `artifacts/kernel-tested/`.
- Original canonical host `artifacts/kernel/` predates the lane fix. Do not
  assemble a new release using it blindly. The current fresh-build wrapper
  rebuilds and finalizes the corrected kernel into the canonical output.
- Host `artifacts/ubuntu-w600d-rootfs.tar` was normalized after export to remove
  container markers. The original marker-containing archive was retained.
- Existing full-disk images and older recipe tarballs predate one or both
  corrections. This snapshot contains the newer source recipe, not a claim
  those old images were regenerated.

## Original next-work list (superseded by the live follow-up)

1. Recheck UART ownership and Ethernet state; identify the actual bound driver
   and NetworkManager policy, then establish DHCP narrowly.
2. Remove live USB container-runtime markers, retain tty1/ttyS2 logins, prevent
   duplicate console-getty, and cleanly reboot to verify normal hardware mode.
3. Confirm a full visible XFCE desktop and normal physical keyboard input.
4. Diagnose the trackpad from this board's factory device tree and wiring;
   do not borrow CloudBook GPIOs or probe unrelated PMIC buses blindly.
5. Make only necessary Image/DTB/modules/rootfs-file updates with rollback.
6. Cleanly shut down, remove USB, and physically verify original Android boots.

## Connection and device reminders

Serial bridge is `tcp://localhost:5000`; use one client only. Historical
session IDs are not reliable instructions to reconnect. Last mainline capture:
`logs/2026-11-24-Codex2/serial-20261124T165530-131412+0800.jsonl`.

On `trash`, the previously authorized USB was Kingston DataTraveler 3.0,
serial `E0D55E625BE9F440F84702D0`, 30943995904 bytes, `/dev/sdb`.
Host `/dev/sda` is an internal Samsung SSD, not the USB. On the laptop the USB
may instead be `/dev/sda`; never infer identity from a device letter alone.
