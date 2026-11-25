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

## Next work, in order

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
