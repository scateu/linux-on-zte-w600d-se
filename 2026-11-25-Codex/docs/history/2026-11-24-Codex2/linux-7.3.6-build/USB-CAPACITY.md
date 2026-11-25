# Authorized Kingston USB: full-capacity image

The user authorized overwriting the whole `/dev/sdb` on `trash` on
2026-11-24, recommending a 512 MB FAT32 first partition. This authorization
does not apply to `/dev/sda`, any other USB, or the laptop's eMMC.

Last read-only identification before assembly:

- Kingston DataTraveler 3.0, USB transport.
- Serial `E0D55E625BE9F440F84702D0`.
- Device `/dev/sdb`, capacity `30943995904` bytes; existing partition unmounted.
- Server `/dev/sda` is its internal Samsung SSD and must never be targeted.

The normal `BUILD-READY.md` procedure creates a portable 6 GiB image.
For this USB, grow a **regular-file copy** of its checked ext4 filesystem
offline, preserving the portable image and avoiding privileged live-disk
partition resizing:

```sh
ssh trash
cd /home/k/codex-workdir-nov-24-2026
bash scripts/assemble-capacity-image.sh 30943995904
```

Layout: MBR `24c0d202`; first partition starts at 1 MiB and is **512 MiB
FAT32**, label `W600D_BOOT`; second starts at 513 MiB and is ext4,
label `W600D_ROOT`, filling the image. Image size is USB capacity rounded
down to a whole MiB, leaving less than 1 MiB unused at the physical end.
PARTUUIDs remain `24c0d202-01` and `24c0d202-02`, so extlinux and fstab
do not need device-name changes. Never attach two copies of this image
to the laptop simultaneously because they share these identifiers.

Assembly validates the board DTB, built-in kernel options, FAT and ext4
filesystems, then records the partition table and image/compressed-image
SHA256 sums. Assembly touches regular files only. A separate guarded
whole-disk writer must recheck device identity and mounts immediately
before any destructive flash.

The boot flow is original patched **eMMC vendor U-Boot -> USB extlinux ->
Linux 7.3.6 -> USB Ubuntu XFCE**. This new USB contains no second U-Boot,
`boot.scr`, or bootloader installed in its raw sectors. Linux's eMMC and
SDMMC controller DT nodes remain disabled. No further eMMC patch or
`saveenv` is part of this flash operation.

Build checks are not hardware acceptance. After flashing, capture the
first boot over the existing sole serial connection, check the native
panel and physical keyboard on 7.3.6, then shut down, remove USB and
observe the original Android fallback. Until then, do not describe the
new image as display/keyboard proven.
