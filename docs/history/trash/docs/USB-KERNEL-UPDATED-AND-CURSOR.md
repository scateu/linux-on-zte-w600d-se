# Kernel-only USB update and first visible mainline output

Date: 2026-11-24. This supersedes the pending USB-update status in
`USB-FILE-ONLY-DEBUG.md` and `MAINLINE-FIRST-BOOT.md`.

## USB update completed, about 17:20 +08:00

On `trash`, `/dev/sdb` was confirmed as the authorized 30943995904-byte
Kingston DataTraveler 3.0, serial `E0D55E625BE9F440F84702D0`. Both partitions
were unmounted and retained their original UUIDs and labels.

The guarded file updater completed successfully with exit status zero:

- Staged the 43792896-byte corrected kernel on FAT `/dev/sdb1`.
- Synced, renamed the old kernel to `/boot/Image.pre-lanes-20261124`,
  activated the staged file as `/boot/Image`, and synced again.
- The original kernel remains available on FAT for rollback.
- DTB, extlinux, MBR, ext4 root and eMMC were not modified by this update.
- No full-disk write, full-disk read-back or kernel-content read-back.
  Directory listings and the build source checksum were checked instead.

Corrected source Image SHA256:
`0b0c71f33eed1057e9857e65ff60b9fecb248d7ed394408af4c240fb64c8638d`.
The original whole-image checksum no longer describes the updated USB.
Build-host log: `logs/usb-kernel-files-update-20261124.log`.

Mtools emitted `Hidden (32) does not match sectors (63)` while accessing
the pre-existing FAT geometry. All staging/rename/list operations completed
successfully. No unrelated geometry change was attempted.

## Physical boot observation

The user returned the USB to the laptop and powered on. Captured flow is:

```text
original eMMC DDR/SPL/ATF/U-Boot 2017.09
 -> /extlinux/extlinux.conf on USB
 -> /boot/Image and unchanged mainline DTB
 -> Linux 7.3.6-w600d-usb
 -> Ubuntu systemd and LightDM
```

The Linux banner confirms the corrected incremental build:
`#3 SMP PREEMPT Tue Nov 24 17:10:47 CST 2026`.
Do not confuse the vendor U-Boot's earlier `Link Training success!` line
with Linux link-training diagnostics.

The user reported a blinking cursor, then a visible mouse cursor, and
confirmed **Ctrl+Alt+F1 switches to the text console**. This is real
internal display output and physical keyboard shortcut delivery on the
new kernel. A complete XFCE desktop and normal typing still need testing;
a cursor alone is not full graphical-session acceptance.

## Newly identified rootfs integration issue

The new boot explicitly prints `Detected virtualization docker.`. The
offline exported Ubuntu rootfs contains a zero-byte `/.dockerenv` from
Docker, although this is a real hardware boot. Systemd starts both
`console-getty.service` and `serial-getty@ttyS2.service`; `/dev/console`
also points at the UART. Commands entered over serial are being consumed
as console login usernames instead of reaching the intended root shell.
The configured `linux` account has passwordless sudo and tty1 autologin;
no account password was configured in Dockerfile.v3, so do not guess a
password at the competing console login prompt.

The user is asked to run `sudo systemctl stop console-getty` on the
working text console. Once UART access is restored, inspect the live
system, remove Docker-only marker(s) from the USB rootfs, and ensure the
duplicate getty cannot return. Update the offline rootfs recipe to remove
container-runtime markers after Docker export, not merely inside RUN,
where Docker can reintroduce them.

Current status: kernel file update complete; visible internal display and
physical keyboard VT switching confirmed. XFCE desktop completion and
normal key-event capture pending. UART recovery is in progress. No
additional full USB flash is needed for these rootfs-file corrections.
