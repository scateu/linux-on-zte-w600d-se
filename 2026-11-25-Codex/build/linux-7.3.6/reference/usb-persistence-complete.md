# USB display changes installed — November 24, 2026, +08:00

## Authoritative current checkpoint

**The authorized USB write is complete, synced and verified by readback after
unmounting and remounting the boot partition read-only.** This file supersedes
the pending installation state in `usb-persistence-pending.md` and the older
serial/session/persistence state in `CURRENT.md`, `memory.md` and `README.md`.
Existing-file Markdown updates remain permission-blocked, so this completion
checkpoint was added as a new file.

The target was not rebooted during this installation. It remains in `/bin/sh`
as PID 1, with eDP connected/enabled and the previously confirmed white screen.
The saved diagnostic script was also executed successfully in this running boot.
The newly installed default boot entry has not yet been tested by a reboot.

Final target mounts at 12:18:16:

```text
/dev/root / ext4 ro,relatime 0 0
devtmpfs /dev devtmpfs rw,relatime,size=986260k,nr_inodes=246565,mode=755 0 0
proc /proc proc rw,relatime 0 0
sysfs /sys sysfs rw,relatime 0 0
debugfs /sys/kernel/debug debugfs rw,relatime 0 0
```

USB boot FAT is **unmounted** from `/media`; USB ext4 root stayed read-only
throughout. No eMMC partition was mounted. Do not unplug the USB root or exit
PID 1. No `saveenv`, eMMC/GPT/misc/slot write, flash command or additional reboot
was issued.

Active serial exec session: **`53680`**, connected to `127.0.0.1:5000`.
Check the existing session before opening another TCP client. The successful
installation capture prefix is:

```text
2026-11-24-Codex2/logs/serial-20261124T120921-403566+0800
```

It has timestamped `.jsonl`, exact `.rx.bin` and `.tx.bin` files. Earlier sessions
`83306`, `26723` and `94753` are ended, not current.

## What was written

Paths in this section are **relative to the USB FAT boot partition**, not the
running ext4 root. The FAT partition was temporarily mounted at `/media`.

| USB boot-partition path | Purpose |
| --- | --- |
| `/boot/rk3568-laptop-zte-edp-20261124.dtb` | New display-enabled DTB |
| `/extlinux/extlinux.conf` | Default selects new DTB; original-DTB rollback entry added |
| `/boot/codex2-fb-white-test.sh` | Manual, geometry-checked white framebuffer test and pan handover |
| `/codex2-backup-20261124/rk3568-laptop-zte.dtb` | Verified copy of the original DTB |
| `/codex2-backup-20261124/extlinux.conf` | Verified copy of the original boot configuration |
| `/codex2-backup-20261124/SHA256SUMS` | Checksums for both original-file backups |

The original `/boot/rk3568-laptop-zte.dtb` and `/boot/Image` were **not modified**;
their final hashes match the pre-write hashes. Boot scripts were not modified.
No files on ext4 root were edited.

The new DTB implements exactly the eight already-tested `disabled` → `okay`
status changes: eDP PHY, eDP controller, PWM2, panel supply, backlight, panel,
VP1 input endpoint and eDP route. VP0 input remains disabled. GPIOs, phandles,
PWM2m1 wiring, period/polarity, graph links and all other properties are retained.
Do not redirect the backlight to PWM8.

Host `prepare_persistent_display.py` validated parsed-tree equality except for
those eight statuses. On target, Perl generated the staged DTB from the exact
hash-matched original using the manifest offsets. Its checksum matched the host
artifact before publication and again after read-only remount. Shorter property
values are followed by FDT_NOP tokens, preserving the original DT header,
structure/string block locations and total file size of 165657 bytes.

## Boot configuration and rollback choice

Host copy: `extlinux-display.conf`. The installed configuration keeps
`DEFAULT w600d` and `TIMEOUT 30`:

- `LABEL w600d`: `/boot/Image` with `/boot/rk3568-laptop-zte-edp-20261124.dtb`.
- `LABEL w600d-original`: the same Image with `/boot/rk3568-laptop-zte.dtb`.

Both APPEND lines retain the original arguments exactly, including
`root=PARTUUID=12345678-02`, clock/domain preservation and `init=/bin/sh`.
**The original on-disk `rw` option was retained.** Current root is read-only
because this running RAM test booted with `ro`; a later normal extlinux boot
will request read/write root again. No new init program was installed.

Select `w600d-original` in the extlinux menu for the original disabled-display
DTB. To restore the complete original configuration later, with `/media` unused:

```sh
mount -t vfat -o rw /dev/sda1 /media &&
    (cd /media/codex2-backup-20261124 && sha256sum -c SHA256SUMS) &&
    cp /media/codex2-backup-20261124/extlinux.conf /media/extlinux/extlinux.conf &&
    sync &&
    umount /media
```

These are rollback instructions, **not commands executed during installation**.
If a step fails, inspect mount state; do not reset or unplug storage blindly.

## Manual display diagnostic after a later boot

The persistent DTB enables the display hardware. It does not create framebuffer
console support or automatically run the white-screen diagnostic. The kernel
still lacks `CONFIG_FRAMEBUFFER_CONSOLE`; a local keyboard-driven text shell is
a separate next phase.

If fb0 exists but loader-logo scanout still hides framebuffer writes, the saved
script checks the exact 1920×1080/32-bpp/7680-stride layout, writes 8294400 white
bytes, then requests the previously verified `fb0/pan` handover. From the PID-1
shell after a later boot, with `/media` unused:

```sh
mount -t vfat -o ro /dev/sda1 /media &&
    sh /media/boot/codex2-fb-white-test.sh
umount /media
```

Run the script with `sh`, not by exiting PID 1. It mounts proc/sysfs if needed,
does not modify boot files, and is intentionally manual. The script passed host
and target `sh -n`, and its installed copy ran successfully before final readback:
`1080+0` records, `8294400 bytes` written, followed by pan.

Physical keyboard events were verified in the earlier boot. Current main
keyboard is `/dev/input/event1`; event2 is System Control. Rediscover input
numbering after a reboot rather than relying on the earlier event2 assignment.

## Installation and verification evidence

The serial preflight verified PID 1, root read-only, no other mounted disk,
unused `/media`, and `/dev/sda1` start 2048/size 1048576 sectors. The partition
is the expected USB boot FAT; `/dev/sda2` is root. The live original DTB and
extlinux.conf hashes exactly matched the inspected host snapshot.

Timeline:

- 12:09:21: sole-client logger connected; readable serial restored.
- 12:11:21: boot FAT remounted writable; backup copies made, synced and hashed.
- Staged DTB/config/script hashes matched their host-prepared counterparts.
- New DTB was published and synced **before** switching boot configuration.
- 12:17:04: configuration activated and synced; both boot entries printed.
- 12:17:30: saved diagnostic ran; FAT unmounted, then remounted read-only.
- Readback checked all installed hashes, preserved DTB/Image and backup manifest.
- 12:18:16: FAT unmounted again; final mount list verified root still read-only.

Readback SHA256 values:

```text
New display DTB:
ae39fab24eba06fcee147abcf76e7ba3f374bcf874b3fc123d54b09c83fdb7d0

Installed extlinux.conf:
24ec0bdbf79d5551f2dec3028e774e65c5fd0e6aed74d2624209a38ce74e31a2

Installed manual white-test script:
71a9e65def791038a3e43af6808dc239ab92ea20d4d1fc1654c4afa7535df5a6

Preserved original DTB (and backup):
4578807d00d97eed27227955e10251ff195f2de38d3d3b783965dc2b5057aa8e

Original extlinux.conf backup:
5ef3b7c8b83a42b9d4011cff4a43a31da5984110068672edda63fde1e21559bb

Preserved Image, before and after installation:
470eccce48e9b780c3dc1f76c7144829a10c15e80517c3dcf45c01240d40f863
```

Host verification also parsed the serial JSONL and asserted that the installed
file hashes appeared in the post-remount RX stream, both backup checks reported
OK, and the final boot-unmounted/root-read-only markers were present.

## Warnings and transfer lessons

The first writable FAT remount reported that the volume had not been properly
unmounted and some data might be corrupt. No fsck or repair was run. The selected
source files and backup hashes were valid; installation/readback succeeded.
The later read-only remount reported only the existing utf8/case-sensitivity
warning. Do not claim this proves the whole filesystem is free from corruption;
any filesystem repair should be a separate offline, backed-up operation.

One 1200-plus-character script-transfer line exceeded the host PTY canonical
input capacity and stalled **before transmission**. JSONL confirmed there was
no TX record for that line. Local Ctrl-U cleared it without target interruption;
the script payload was then transferred as two short shell-variable assignments.
Keep individual interactive commands below 1000 bytes, preferably well below;
verify the logger TX record before diagnosing a long-line stall as a board fault.

The prior RAM boot's nonfatal FDT_DTBO allocation warning and logo-memory alignment
warning remain documented in `display-success.md`. This installation did not
reboot to investigate them, replace the kernel, or claim a working text console.
