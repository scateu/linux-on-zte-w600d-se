# Saved USB boot test passed — November 24, 2026, +08:00

## Latest authoritative checkpoint

**The saved USB configuration has now been reboot-tested successfully.**
Vendor U-Boot automatically selected `w600d`, loaded the installed display DTB,
and started Linux without any manual U-Boot environment or FDT edits. Linux
bound eDP and registered fb0. The saved USB framebuffer diagnostic then ran,
and the user confirmed: "screen to all white."

This checkpoint supersedes the "not reboot-tested yet" status in
`usb-persistence-complete.md`. That file still documents the installation,
verified hashes, preserved original files and rollback instructions.
Older preflight/session states elsewhere in this directory are historical.

The target remains running `/bin/sh` as PID 1. Root is read-only again; boot FAT
is unmounted. eDP-1 is connected/enabled, with Linux XR24 pixels on VP1/Smart0
at 1920×1080p60. The screen is left white. There is no background test reader.
Do not exit PID 1, send Ctrl-D, unplug USB root or reboot just to inspect.

Active serial exec session: **`53680`**, `127.0.0.1:5000`. The same logged session
captured installation and this reboot test:

```text
2026-11-24-Codex2/logs/serial-20261124T120921-403566+0800
```

Each capture has timestamped JSONL and exact RX/TX binaries. This test starts at
the `sysrq: Resetting` RX marker after the 12:21:07 reboot command. Physical
screen observations are in the user conversation, not the serial stream.

## Controlled reboot and automatic boot path

The user approved the proposed controlled reboot. Preflight confirmed root
`ro,relatime`, no mounted boot FAT or eMMC partition, shell PID 1, and successful
`sync`. At **12:21:07.878090** the only reboot command was:

```sh
printf b > /proc/sysrq-trigger
```

No Ctrl-C boot interception or second reboot was performed. The CPU stopping
backtraces immediately after SysRq accompanied the requested reset; they are
not a claim of a spontaneous kernel panic.

Observed automatic boot:

1. SPL and vendor U-Boot 2017.09 (May 29, 2024) started.
2. USB Fanxiang F313 device 0, partition 1, was scanned.
3. `/extlinux/extlinux.conf` was read: **571 bytes**, matching the installed file.
4. Default entry **`1: w600d`** was selected automatically.
5. `/boot/Image` loaded: **36506112 bytes**.
6. `/boot/rk3568-laptop-zte-edp-20261124.dtb` loaded: **165657 bytes**.
7. Linux `5.10.160-g6c6e1238ebb1-dirty` started with the correct board model.
8. At boot uptime 16.741 s, DRM bound `fe0c0000.edp`; at 16.857 s, fb0 registered.
9. Root mounted at 22.248 s; a USB read/reset delay preceded init.
10. At 54.228 s, `/bin/sh` started as init. `SAVED BOOT pid=1` confirmed the shell.

The captured path shows vendor U-Boot reading USB extlinux directly; no second
full USB U-Boot banner or chain-loader file retrieval was observed in this test.
This describes the observed path, not every possible chain-load workflow.

Actual kernel command line:

```text
earlycon=uart8250,mmio32,0xfe660000 console=ttyS2,115200n8 console=ttyS2,115200n8 clk_ignore_unused pd_ignore_unused root=PARTUUID=12345678-02 rootdelay=5 rootwait rw  init=/bin/sh
```

As intended during installation, original extlinux APPEND arguments were retained,
including **`rw init=/bin/sh`**. The requested tty0 console is still rewritten to
a duplicate ttyS2; kernel framebuffer-console support is still absent.

## Boot logo versus Linux framebuffer

The user first reported that the screen remained at the **中国移动云电脑** logo.
This was not evidence that Linux had failed to boot: the serial PID-1 shell
was already active. The retained boot-logo scanout and missing text console
explain why reaching the shell did not visibly replace that logo.

Root was synced and remounted read-only before the diagnostic. The operation
suffered additional USB read timeouts but completed; `/proc/mounts` explicitly
confirmed `/dev/root / ext4 ro,relatime`.

At **12:25:38.185662**, with root read-only, the saved script was run from the
USB FAT partition mounted read-only:

```sh
mount -t vfat -o ro /dev/sda1 /media &&
    sh /media/boot/codex2-fb-white-test.sh
```

The script confirmed the expected framebuffer geometry, wrote **1080 full rows /
8294400 bytes**, and requested `printf '0,0\n' > /sys/class/graphics/fb0/pan`.
Linux then logged `Freeing drm_logo memory: 12152K`. The user confirmed that the
internal screen changed to entirely white.

**This diagnostic is manual, not an automatic boot service.** A later boot may
retain the vendor logo again until fbdev/DRM userspace takes over. Neither this
test nor the persistent DTB adds a normal keyboard-driven text console.

## Live persisted DT and hardware verification

Readback from `/sys/firmware/devicetree/base` after the automatic boot verified
all eight saved status changes:

| Node | Live status |
| --- | --- |
| `/syscon@fdcb0000/edp-phy` | `okay` |
| `/edp@fe0c0000` | `okay` |
| `/pwm@fdd70020` | `okay` |
| `/vcc3v3-lcd-edp` | `okay` |
| `/backlight` | `okay` |
| `/edp-panel` | `okay` |
| `/edp@fe0c0000/ports/port@0/endpoint@1` | `okay` |
| `/display-subsystem/route/route-edp` | `okay` |
| `/edp@fe0c0000/ports/port@0/endpoint@0` | `disabled` — VP0 intentionally unused |

This is hardware-boot validation of the prepared DTB, including its FDT_NOP
layout preservation, not merely the earlier offline parser validation.

DRM summary after the saved script:

- VP0 disabled; VP1 active on eDP-1 / Smart0-win0.
- 1920×1080p60; requested/real clock both 141020 kHz; RGB888_1X24 bus.
- Horizontal timing `1920 1968 2000 2080`; vertical `1080 1090 1102 1130`.
- Linux scanout format XR24 little-endian, pitch 7680, offset 0.
- fb0 virtual size `1920,1080`, stride `7680`, bpp `32`.
- eDP status `connected`, connector `enabled`.
- PWM2 requested/enabled: period 25000 ns, duty 19607 ns, normal polarity.
- Deferred probes contain only `mtd_vendor_storage`.

Vendor U-Boot's EDID report identifies KDC panel **KD140N1930A0**, product code
0802, and reports successful two-lane link training with link rate `0x0a`.
Those are vendor boot-stage observations, not a separate Linux link-rate readback.

The main SINO WEALTH keyboard `258a:0001` enumerated again on USB 7-1 and is
`/dev/input/event1`. System Control is event2; Consumer Control event3.
Touchpad I2C HID `093a:0255` remains event4/event5. No new physical key or touchpad
test was performed; the earlier 60 physical key press/release pairs remain the
input-delivery evidence. Rediscover event numbering after every reboot.

## Remaining warnings — not hidden by the passing display test

### USB root read reliability

Read/reset delays occurred at kernel uptimes approximately 54, 129, 182, 213
and 243 seconds. The remount path reported 30-second READ timeouts and I/O errors
at sectors **39081688** and **55838920**. The reported operations were READs.
Commands could therefore appear stalled even while the PID-1 shell and display
were functioning. Root read-only remount ultimately succeeded.

USB read/reset problems also existed before enabling eDP. This test does not
diagnose their cause or prove the storage/filesystem healthy. No fsck, drive
replacement, USB quirk, power-management override or unrelated driver fix was
attempted. Treat this as a separate reliability issue before relying on the
USB root for substantial further work.

### Vendor FDT allocation bookkeeping

`Sysmem Error: Found there is region overflow!` recurred during **automatic
extlinux boot without any manual `fdt resize`**. This is important new evidence:
the warning cannot be attributed solely to the earlier scratch-space resize.
The tracked FDT_DTBO region remained `0x0a100000` through `0x0a12590c`, smaller
than the 165657-byte loaded USB DTB. A stale/smaller vendor allocation record
is a plausible explanation, not a verified root-cause fix.

The boot continued successfully. The pre-existing logo-memory alignment warning
also recurred; the subsequent fbdev handover released logo memory. Do not reboot
repeatedly or change memory reservations just to suppress these warnings.

### Vendor retry metadata

Vendor U-Boot read recovery/misc and ZTE retry metadata, reporting retry **5**,
boot_times **421**, change_times **15**, then logged **`rewrite zte_retry 4`**.
Slot A still reported successful=1, tries-remain=0. No retry/slot write command
was issued by us, but this vendor behavior means we must not claim that an
authorized reboot leaves every eMMC metadata byte unchanged. Raw misc/retry
bytes were not reread or repaired. Minimize unnecessary additional reboots.

## Final state and next phase

At **12:26:48.770358**, boot FAT had been unmounted again, `/proc/mounts` showed
root `ro,relatime` plus devtmpfs/proc/sysfs/debugfs only, and `PID=1` was confirmed.
No persistent boot files were edited during this reboot test, and no eMMC write
command was issued. The saved original-DTB rollback entry and verified backups
from `usb-persistence-complete.md` remain available; rollback itself was not tested.

Host validation parsed the post-reset RX stream and asserted automatic default
DTB selection, eDP/fb0 binding, all eight live statuses, VP0 disabled, successful
white write and logo release, 1080p XR24 scanout, and final FAT-unmounted/root-ro
state. Visual white pixels were independently confirmed by the user.

Next display/usability phase: a matching kernel with framebuffer-console and
font support, an intentional tty1 shell/getty, and review of the tty0 bootarg
rewrite. USB root reliability should be addressed as a separate issue. The
current milestone is verified persistent display enablement and manual Linux
pixel output, not a complete desktop or local text-console bring-up.
