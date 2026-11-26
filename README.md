# ZTE W600D SE removable Linux bring-up

Sources, board DTS, patches, build recipes and research for booting Ubuntu
from USB while preserving the laptop's original Android installation.

Collected November 25, 2026 (+08:00), from the November 24 local research
and `/home/k/codex-workdir-nov-24-2026` on `trash`.

Consolidated and cleaned November 25, 2026: useful material from both earlier
date folders, the duplicate archive and ref/ now lives here. Those old
directories were removed. Unique recovery images were retained losslessly,
not discarded; both original Git repositories and their histories were moved.

**Installing? See [USB preview installation](docs/INSTALL.md).**
For development, start with `CURRENT.md`, then `docs/DIY-FROM-UPSTREAM.md`. This is a
source-and-evidence handoff, not a claim that the laptop is completely finished.
The current live kernel is **7.3.6-w600d-usb-wifi**, with Ubuntu
**24.04.5 ARM64 Base plus XFCE**. These version numbers are reproduction inputs,
not a claim about the latest upstream release today.

The workspace now lives directly at the zte-book Git repository root. Git tracks
sources/guides/patches and pins both reference repositories as submodules;
large/generated artifacts and private backups remain ignored on disk.
See `docs/GIT-REPOSITORY.md` and run `tools/setup-references.sh` after a recursive
clone. The verification below is for the complete local snapshot, not a
source-only GitHub clone without its ignored backups/tested binaries.

## Clone and prepare

```sh
git clone --recurse-submodules YOUR_GITHUB_REPOSITORY_URL zte-book
cd zte-book
bash tools/setup-references.sh
git config core.hooksPath .githooks
```

The two original reference repositories are pinned submodules, not duplicate
embedded repositories. Their histories and existing files remain local;
this repository uploads their commit references rather than their binaries.
Setup recreates the vendor patch-directory alias and applies the preserved
CloudBook local text override without resetting either repository.

## What Git tracks

- Guides, research notes, authored DTS/DTSI, patches, configuration and scripts.
- Small build records, source/checksum provenance and cleanup audit.
- Pinned external reference commits and the patch needed for the local override.

Compiled kernels/DTBs/U-Boot/scripts, raw or compressed backups, disk images,
serial logs, downloads, output directories and caches are ignored. They are
not deleted. Necessary large font/Wubi sources remain in the U-Boot submodule.
The local pre-commit hook rejects ordinary staged files larger than **1 MiB**;
Git ignore patterns alone cannot filter arbitrary files by size.

A fresh clone must build its own kernel/rootfs and use its own device backups.
See [GitHub publication notes](docs/GIT-REPOSITORY.md) for initial push commands,
local overrides and the ignored-file policy. No complete desktop/trackpad/DHCP/
Android-fallback acceptance is implied; see the live follow-up in `CURRENT.md`.

## Goal and bootflow

```text
Machine's own factory eMMC DDR/SPL/ATF/U-Boot, patched once to scan USB first
  -> USB /extlinux/extlinux.conf
  -> USB /boot/Image + /boot/rk3568-zte-w600d-mainline.dtb
  -> USB Ubuntu /sbin/init
```

The default Linux USB path needs **no second U-Boot, root `boot.scr`, or raw
Rockchip loader**. The optional native build lives in `/native-uboot/` and is
only chainloaded manually.
With USB removed before power-on, the configured bootcmd falls through to
original Android. That physical fallback test is still outstanding.
The optional typewriter stick is different: factory U-Boot -> vendor boot.scr
-> RAM shim -> second U-Boot -> typewriter. Do not mix its files into Linux USB.

## Directory map

| Path | Purpose |
| --- | --- |
| `CURRENT.md` | Latest recorded hardware status and remaining work |
| `docs/FACTORY-UBOOT-PATCH.md` | Patch the original factory bootcmd once, preserving Android |
| `docs/USB-UBOOT-TYPEWRITER.md` | Second USB U-Boot, correct boot.cmd/boot-nc.cmd to boot.scr generator, typewriter |
| `docs/NATIVE-UBOOT.md` | Mainline-based LCD and keyboard prototype: build, test, Ubuntu panic, rollback, potential eMMC replacement |
| `docs/BOOT-LOGO.md` | Proven boot BMP location, format, offline generation and undo safeguards |
| `docs/PARTITIONS-AND-HARDWARE.md` | Original partition map, board wiring and evidence sources |
| `docs/RECOVERY.md` | Lossless backup extraction, deduplication policy and cleanup audit |
| `docs/DIY-FROM-UPSTREAM.md` | Numbered manual procedure, factory patch through USB boot |
| `docs/BUILD-CURRENT.md` | Fresh build-host setup, current recipe entry point, outputs |
| `docs/DEVICE-TREE.md` | Where DTS information comes from; board wiring and include chain |
| `docs/BOOTFLOW.md` | Factory patch scope, direct USB boot, Android fallback |
| `docs/DEBUGGING.md` | Black-screen root cause, file-only updates, UART/getty issues |
| `docs/TRACKPAD-AND-WIFI.md` | I2C4 trackpad, persistent Ethernet DHCP, MT7663S radio patches and rollback |
| `build/linux-7.3.6/` | Build-host recipe: DTS, patches, rootfs definitions, scripts and config |
| `build/linux-7.3.6/reference/cloudbook-mainline-6.12/` | Comparison project, including required Naneng PHY patch |
| `artifacts/kernel-tested/` | Corrected Image, final DTB, exact config, System.map and upstream build checksums |
| `artifacts/build-records/` | Package versions, build environment, partition maps and historical image hashes |
| `bootloader/usb-uboot/` | Original U-Boot/typewriter Git repository, scripts, patches and prebuilts |
| `build/linux-7.3.6/reference/cloudbook-air-mainline-linux/` | Complete original comparison Git repository, with local changes preserved |
| `recovery/factory-backups/` | All collected unique recovery images as verified .gz files; readable DTB/DTS/BMP/metadata |
| `reference/factory-device-tree/` | Relative alias to canonical factory evidence, no second copy |
| `reference/upstream-linux-7.3.6/` | RK3568 common DTSI files copied from the kernel source |
| `reference/download-metadata/` | Recorded upstream release metadata and archive checksum lists |
| `reference/u-boot-research/` | Relative alias to bootloader/usb-uboot/_RESEARCH |
| `reference/legacy-usb-Nov-24/` | Small historical boot/DTS inputs; obsolete kernels/initrds removed |
| `logs/` | Serial captures and build/flash/update logs, separated by source |
| `docs/history/` | Unique earlier Markdown and build notes, labelled historical |
| `tools/` | Serial console, DTB inventory, backup extraction and workspace verification |
| `manifests/` | Current checksums/origins/aliases, original manifests and detailed cleanup report |

The build recipe retains its original relative directory layout so its scripts
can find their patches, DTS sources and references. Preserve relative aliases
when copying it. Its old overview documents moved to `docs/history/build-recipe/`;
superseded build wrappers were removed. Use `docs/BUILD-CURRENT.md` here.
Older notes may describe 5.10 tests,
two-stage U-Boot loading, a black screen, or a pending full-disk read-back.
Those are history, not instructions to repeat those operations. In particular,
old proposals to erase Android/repartition eMMC are **not the current plan**.

## Native U-Boot experiment

The [native-display U-Boot guide](docs/NATIVE-UBOOT.md) records how to reproduce
and manually chainload the mainline-based prototype. The installed USB build
showed a readable LCD countdown, and the built-in keyboard stopped it and ran
`version`. The preceding build panicked handing display control to Ubuntu;
direct Linux boot from the exact installed binary is still unverified.
Keep factory U-Boot → USB extlinux as the default. The prototype still depends
on factory SPL/DDR/secure firmware and **must not be flashed to `uboot_a`**.

## Safety and completeness

- Original useful files were consolidated locally, exact duplicates removed
  and recovery images compressed only after verifying decompressed SHA256.
  No USB/eMMC write, reboot, serial interaction, remote-host modification,
  kernel rebuild or physical full-disk read-back occurred during cleanup.
- The source recipe includes all four necessary eDP patches, the board DTS
  source files, the validated kernel config, and post-export Docker-marker
  stripping. The complete tested Image and DTB are included too.
- The 1.2 GB rootfs tar, approximately 90 MB module tree, full kernel source
  archive/tree, and whole-disk images remain on `trash`; they are reproducible
  from the included recipe. Per-machine recovery backups now live under
  `recovery/factory-backups/`; never transplant them into another laptop.
  Android super/userdata are not included: this is not a complete factory disk backup.
- The original whole-image hashes are historical: the USB's Image was replaced
  afterward. They do not verify the currently updated physical USB.
- Bring-up autologin/passwordless sudo are not production security defaults.
  Trackpad motion/left-click, managed Ethernet DHCP and normal hardware-mode
  boot are now recorded. Wi-Fi, complete visible XFCE/right-click acceptance
  and Android fallback remain unfinished.

## Verify this copy

```sh
python3 tools/verify-workspace.py verify
```

This hashes local files, verifies lossless backup recovery and relative aliases,
checks both Git HEADs/tracked state and rejects remaining independent-storage
large duplicates. It does not read a USB drive. Linux
`sha256sum -c manifests/SHA256SUMS` checks the regular-file hashes only.
`manifests/SOURCE-MAP.json` records retained-file origins by checksum;
`CLEANUP-REPORT.json` records moved/removed/compressed paths and original hashes.
`manifests/pre-cleanup/` preserves the original inventory and snapshot manifests.
