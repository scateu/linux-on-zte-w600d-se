# Current reproducible build recipe

Use the recipe in `../build/linux-7.3.6/`. It was copied from the working
build host and contains its reference patch, board DTS include chain, exact
validated config, Ubuntu definitions and lane/marker/trackpad fixes. This guide supersedes
the historical recipe README and older build entry points.

## Fresh work directory on trash

The original build remains in `/home/k/codex-workdir-nov-24-2026`.
Use a separate empty directory for reproduction; several scripts deliberately
refuse to overwrite completed rootfs exports, images and rollback archives.

From the original Mac workspace, after inspecting that the destination is new:

```sh
rsync -a build/linux-7.3.6/ \
  trash:/home/k/codex-workdir-nov-25-2026/
ssh trash
cd /home/k/codex-workdir-nov-25-2026
export ALL_PROXY=socks5://192.168.1.5:1080
export APT_PROXY=socks5h://192.168.1.5:1080
mkdir -p out/kernel-7.3.6
cp config/config-7.3.6-w600d-usb out/kernel-7.3.6/.config
JOBS=24 bash scripts/build-display-fixed-image.sh
```

This is a documented command sequence, not something executed during snapshot
collection. Prerequisites include the ARM64 cross compiler, kernel build tools,
dtc, Docker with ARM64 QEMU binfmt on x86_64, fakeroot, filesystem/partition
utilities, mtools, zstd, curl and rg. The saved host environment record is
`../artifacts/build-records/build-host-environment.txt`.

## What the current wrapper does

For the **v6 Wi-Fi/Bluetooth build**, replace the final command above with:

```sh
JOBS=24 bash scripts/build-wifi-image.sh
```

Use a clean recipe directory without an extracted Linux source. This adds
CloudBook 0005/0011/0012/0013 plus our 0005b Linux-7.3 lifecycle and 0005c board-ID
adaptations. It selects `7.3.6-w600d-usb-wifi`, includes both pinned MediaTek
firmware files/license and integrates the v6 DTB, touchpad/network overlays
and radio tools. Outputs are in `artifacts/kernel-wifi/` and
`artifacts/w600d-ubuntu-xfce-7.3.6-wifi-20261125.img[.zst]`.
The original display-only outputs below remain the baseline recipe.
The Wi-Fi full-image wrapper has syntax checks, not an end-to-end flash test;
the live USB is being validated with file-only updates. See `TRACKPAD-AND-WIFI.md`.

1. Downloads/checksum-verifies pinned Linux 7.3.6 and Ubuntu 24.04.5 ARM64 Base.
2. Builds Ubuntu userspace with `rootfs/Dockerfile.v3`.
3. Adds Naneng PHY support and our RK3568 Analogix adaptation; builds the kernel
   and matching modules with the validated configuration.
4. Applies `0004-analogix-complete-phy-lanes.patch`.
5. Adds `0003-kdc-141020khz-vpll.patch`, rebuilds Image and final **v4-touchpad** DTB,
   and validates the result with symbol support enabled (`DTC_FLAGS=-@`).
6. Integrates modules, services, Ethernet-management and tap-to-click overlays
   using `rootfs/Dockerfile.final`.
7. Removes container-runtime markers from the exported rootfs archive.
8. Builds a regular-file USB image with 512 MiB FAT32 boot and ext4 root.

The historical kernel builder creates an intermediate v2 DTB before finalization.
It must never be booted or copied to USB; final v4 retains the validated v3
display settings and adds the verified trackpad wiring for this
board. To avoid intermediate builds when doing the work manually, follow the
patch order and v4 build in `DIY-FROM-UPSTREAM.md`.

## Final outputs

### Compact USB preview

After building or restoring `artifacts/kernel-wifi/`, `artifacts/firmware/`,
and the `w600d-ubuntu-xfce-base:24.04.5` Docker image, run from
`build/linux-7.3.6/` (or the equivalent recipe directory on the build host):

```sh
bash scripts/build-usb-release.sh preview-20261126-r2
```

This reuses the checked v6 kernel/DTB, builds the ARM64 desktop rootfs with
Ubuntu `cloud-guest-utils` (`APT_PROXY` optional), and assembles a 4 GiB MBR
image with 512 MiB FAT32 boot plus ext4 root. It writes only regular files.
Raw and compressed images, separate SHA-256 manifests, package versions and
the partition map go to `artifacts/releases/preview-20261126-r2/`.

`w600d-grow-root.service` runs at first normal boot. It checks that the
mounted root is the expected ext4 partition on a USB disk, grows partition
2 and then the live filesystem, and records completion only on success.
It does not touch the FAT boot partition or eMMC. Check it on real hardware
with `journalctl -b -u w600d-grow-root.service` and `df -h /`.

### Older development outputs

Under the fresh recipe directory:

```text
artifacts/kernel/Image
artifacts/kernel/rk3568-zte-w600d-mainline.dtb
artifacts/kernel/config-7.3.6-w600d-usb
artifacts/kernel/System.map-7.3.6-w600d-usb
artifacts/kernel/kernelrelease
artifacts/kernel/modules/lib/modules/7.3.6-w600d-usb/
artifacts/ubuntu-w600d-rootfs.tar
artifacts/rootfs-package-versions.txt
artifacts/w600d-ubuntu-xfce-7.3.6-20261124.img
artifacts/w600d-ubuntu-xfce-7.3.6-20261124.img.zst
```

The wrapper initially makes a **6 GiB regular-file image**, not a full-capacity
flash. The existing capacity assembler can expand that image's root partition:

```sh
bash scripts/assemble-capacity-image.sh 30943995904
```

That byte count is the recorded Kingston capacity, not a universal USB size.
This creates a 29510 MiB image with the same 512 MiB FAT partition; it does not
access or flash a physical device. For a different USB, use its verified capacity.
Direct filesystem population is also explained in the manual guide and avoids
writing a padded whole-drive image.

## Patch inventory

| Manual order | Recipe path | Purpose |
| --- | --- | --- |
| 1 | `reference/cloudbook-mainline-6.12/patches/0009-phy-rockchip-naneng-edp.patch` | RK3568 Naneng eDP PHY support |
| 2 | `patches/0002-rk3568-analogix-7.3.patch` | Mainline 7.3.6 RK3568 Analogix adaptation |
| 3 | `patches/0003-kdc-141020khz-vpll.patch` | KDC panel clock rate |
| 4 | `patches/0004-analogix-complete-phy-lanes.patch` | Required PHY lane count in rate/voltage callbacks |

The CloudBook patch keeps its original filename `0009`; it is the **first**
patch in our manual recipe, not a missing patch 0001. The rest of that project's
patches/DTS files are comparison material. Do not apply the BOE N44 voltage
override or substitute its board DTS on this KDC-panel laptop.

## Kernel/config and security checks

The saved config is in `config/config-7.3.6-w600d-usb` within the recipe.
The board and config validators are `scripts/validate-board.py` and
`scripts/validate-kernel-config.py`. Drivers needed before mounting USB root
are built in, so this boot recipe needs no initramfs. If that configuration
changes, reassess early boot dependencies rather than simply omitting an initrd.

The rootfs has UART root autologin, a tty1 `linux` autologin account and
passwordless sudo as temporary bring-up conveniences. SSH service/socket are
masked. Configure real passwords and the desired access policy before ordinary
use; do not expose this diagnostic setup as a production system.

No factory eMMC patch or physical USB flash is part of the build wrapper.
The guarded USB writer is tied to the recorded Kingston identity; inspect it
before use, re-identify the drive, and obtain approval for destructive operations.
For debugging the existing USB, see `DEBUGGING.md` and update files only.
