# Mainline first boot: black screen diagnosis, 2026-11-24

This is the new Ubuntu USB with Linux **7.3.6-w600d-usb**, not the older
BSP 5.10 USB. Earlier white-screen tests do not establish mainline success.

## Confirmed on the running laptop, about 17:06 +08:00

- Kernel: `uname -r` reports `7.3.6-w600d-usb`.
- USB root: `/dev/sda2`, ext4, read-write; PID 1 is systemd `/sbin/init`.
  This is the laptop's USB device, not the build server's internal `/dev/sda`.
- `lightdm` is active; Xorg and `xfce4-session` are running.
- Xorg uses the Rockchip display, eDP-1 at 1920x1080, with Panfrost
  Mali-G52 acceleration. DRM state contains a 1920x1080 Xorg framebuffer.
- eDP connector reports connected and enabled, but the physical screen is
  black. Those logical statuses do not prove a trained, transmitting link.
- Backlight reports brightness 200/255 and `bl_power=0`. PWM2 has normal
  polarity, 25000 ns period and approximately 19584 ns actual duty.
- DRM pixel mode is 141020 kHz; actual `dclk_vop1` is 141000000 Hz,
  parent VPLL 564000000 Hz. Not the immediate failure diagnosed below.
- SINO WEALTH 258a:0001 keyboard enumerates as event0, with additional
  system-control event1 and consumer-control event2. Physical key event
  delivery still needs a new-kernel observation; enumeration alone is not
  keyboard acceptance.
- No configured network interface other than loopback.

## Immediate display failure and fix

The boot log repeatedly shows:

```text
rockchip-edpphy-naneng fdcb0000.edp-phy: invalid params for phy configure
analogix_dp_set_link_bandwidth: phy_configure() failed: -22
Wait for pll lock failed -110
eDP link training failed (-110)
too many times retry set bridge, give it up
```

The imported Naneng PHY validates `opts->dp.lanes` for **every** configure
call and its rate setup uses that count to power up active transmitters.
Linux 7.3.6 Analogix creates zero-initialized options but supplies no lanes
in the rate and voltage callbacks. Its lane-only callback supplies lanes,
but rate setup fails first, before that callback is reached.

The successful reference's 6.12 Analogix patch explicitly populated lanes
in both callbacks. The initial 7.3 port reused the existing generic-PHY
callbacks and missed these two fields. Fix the bridge to supply
`dp->link_train.lane_count` for rate and voltage requests; do **not** weaken
PHY validation or copy the reference panel's fixed swing/pre-emphasis.

Reproducible fix: `linux-7.3.6-build/patches/0004-analogix-complete-phy-lanes.patch`.
Existing recipe files could not be edited due to filesystem permissions,
so the new authoritative full-image entry is:

```sh
cd /home/k/codex-workdir-nov-24-2026
JOBS=24 bash scripts/build-display-fixed-image.sh
```

It applies the lane fix before final kernel/DTB and desktop integration.
For an incremental kernel-only build, preserving original release artifacts:

```sh
JOBS=24 bash scripts/build-display-fix.sh
```

Output goes to `artifacts/kernel-edp-lanes-fix/`; the driver is built-in
and the config/release are unchanged. Initial USB image and previously
published hashes still describe the pre-fix release; the rebuilt kernel
needs separate hashes and physical validation.

## Serial capture and safety

- Sole logger uses `2026-11-24-Codex/serial_console.py` and TCP port 5000.
- Capture: `logs/serial-20261124T165530-131412+0800.{jsonl,rx.bin,tx.bin}`.
- A competing `nc` reader stole/garbled parts of initial boot; later the
  logger is the only established client. Avoid concurrent serial readers.
- An interactive `top` was quit with `q`; no reboot or power cut was
  required for this diagnosis.
- USB-only boot remains original eMMC firmware/U-Boot -> USB extlinux ->
  Linux Image/DTB -> Ubuntu. No second USB U-Boot in the new image.
- No eMMC write or `saveenv`; do not restart the skipped full-disk read-back.
- Status: corrected kernel built and validated; file-only updater tested.
  USB not yet visible on `trash`, so the fix is not installed or physically
  validated. Continue with `USB-FILE-ONLY-DEBUG.md`.

## Build reproducibility follow-up

The independent fresh official-Ubuntu userspace recipe finished successfully
on 2026-11-24. Tag `w600d-ubuntu-xfce-clean-check:24.04.5` was built from
Dockerfile.v3, passed `check-userspace.sh`, and its package versions matched
the already-flashed release. It does not replace the running release or USB.
