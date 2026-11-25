# Current reproducible build recipe

Use the recipe in `../build/linux-7.3.6/`. It was copied from the working
build host and contains its reference patch, three DTS files, exact validated
config, Ubuntu definitions and latest lane/marker fixes. This guide supersedes
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

1. Downloads/checksum-verifies pinned Linux 7.3.6 and Ubuntu 24.04.5 ARM64 Base.
2. Builds Ubuntu userspace with `rootfs/Dockerfile.v3`.
3. Adds Naneng PHY support and our RK3568 Analogix adaptation; builds the kernel
   and matching modules with the validated configuration.
4. Applies `0004-analogix-complete-phy-lanes.patch`.
5. Adds `0003-kdc-141020khz-vpll.patch`, rebuilds Image and final **v3** DTB,
   and validates the result with symbol support enabled (`DTC_FLAGS=-@`).
6. Integrates modules and services using `rootfs/Dockerfile.final`.
7. Removes container-runtime markers from the exported rootfs archive.
8. Builds a regular-file USB image with 512 MiB FAT32 boot and ext4 root.

The historical kernel builder creates an intermediate v2 DTB before finalization.
It must never be booted or copied to USB; only final v3 is validated for this
board. To avoid intermediate builds when doing the work manually, follow the
patch order and v3 build in `DIY-FROM-UPSTREAM.md`.

## Final outputs

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
