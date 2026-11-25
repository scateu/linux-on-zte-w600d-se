# Mainline USB build progress — November 24, 2026

## Objective and safety boundary

Factory machine -> patch only its original vendor U-Boot USB-first boot sequence
-> USB Linux -> remove USB and boot original Android. No USB mainline U-Boot is
required. This session builds in `/home/k/codex-workdir-nov-24-2026` on `trash`.
No eMMC write or new USB disk write has been performed for this build.

## Kernel selection

The user requested the latest 6.x or 7.x kernel, not BSP 5.10. On November 24,
2026, kernel.org `releases.json` fetched from `trash` reports latest stable
**7.3.6**, released **November 23, 2026**; mainline is **7.4-rc4**. Target 7.3.6,
not the release candidate. The saved release metadata is on the server in
`downloads/kernel-org-releases-20261124.json`.

The first unproxied download was too slow and stopped incomplete. The user
provided `ALL_PROXY=socks5://192.168.1.5:1080`; the proxy was tested successfully.
Resume through that proxy and checksum-verify before extracting or building.

## Plan

1. Inspect latest upstream RK3568 eDP support; adapt only missing driver pieces.
2. Write a ZTE-specific mainline DTS using tested wiring and live EDID.
3. Build Image, DTBs and matching modules with framebuffer console and USB HID.
4. Build a Debian 13 ARM64 rootfs with local tty1 and serial getty services.
5. Assemble and inspect a USB disk image; document all build and recovery steps.
6. Identify and explicitly confirm a new USB target before destructive writing.
7. Hardware-test the new kernel, physical display, and keyboard; do not claim
   success merely from a clean build.

## Exact machine facts

- Live kernel: 5.10.160-g6c6e1238ebb1-dirty, for reference only.
- Live MemTotal: 2007908 KiB; this is the 2 GB W600D, not the reference's 4 GB.
- Live eDP EDID identifies **KDC KD140N1930A02**.
- Native mode: 1920x1080, pixel clock 141020 kHz; H 1920/1968/2000/2080,
  V 1080/1090/1102/1130.
- Panel power GPIO2_D5, panel enable GPIO2_D4, backlight enable GPIO2_D3.
- Backlight PWM2m1, GPIO0_B6, 25000 ns period; not reference-board PWM8.
- Keyboard SINO WEALTH 258a:0001, powered by GPIO3_A3.
- Do not enable the other board's BOE N44 PHY voltage override.

EDID is preserved in `linux-7.3.6-build/panel-edid.base64`. The fresh sole serial
logger is exec session 81726, capture
`logs/serial-20261124T144142-546518+0800`. The earlier session 53680 had closed.
Only read-only serial diagnostics were sent; no reboot was performed.

## Rootfs build prerequisite

`trash` has Docker access, ARM64 cross GCC, dtc, QEMU user emulation and mtools.
Passwordless sudo is unavailable, so use unprivileged filesystem image tools
and Docker for ARM64 package installation rather than changing host services.
The direct GitHub Debian rootfs URL returned 404. The recipe instead fetches
the official `docker.io/library/debian:trixie-slim` ARM64 manifest and layer
through curl's SOCKS proxy, verifies their SHA-256 digests and imports the base
locally. The registry ARM64 digest is pinned in a saved manifest JSON.

Status: source download and rootfs preparation in progress; no new-kernel
hardware validation yet. The existing USB's successful BSP white-screen test
is not evidence that this mainline port already works.
