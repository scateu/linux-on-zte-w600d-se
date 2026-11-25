# Current reproducible build: Docker special files fixed

This supersedes **BUILD-READY.md** and all earlier entry points. Use:

```sh
ssh trash
cd /home/k/codex-workdir-nov-24-2026
export ALL_PROXY=socks5://192.168.1.5:1080
export APT_PROXY=socks5h://192.168.1.5:1080
JOBS=24 bash scripts/build-verified-image.sh
```

Ubuntu 24.04.5 ARM64 is the real laptop operating system: systemd,
LightDM/XFCE, NetworkManager, normal apt and matched 7.3.6-w600d-usb
modules. Docker/QEMU-user are build-host tools only. Kernel patches,
native KDC panel/keyboard wiring, disabled eMMC, and board validators
are described in README.md. Archive versions are fixed in prepare-sources.sh;
published SHA256 manifests and verified downloads are retained on the server.
Ubuntu package versions are recorded; apt repository
contents evolve, so future builds are not claimed bit-for-bit identical.

Correct phases:

1. `prepare-sources.sh`: official kernel and Ubuntu Base archives.
2. `build-userspace-v2.sh` with **rootfs/Dockerfile.v3**: install packages
   in a separate cached layer, then configure accounts and services. A
   minimal Dockerfile-only context avoids sending generated disk images
   to Docker. Apt update fails immediately on repository/proxy errors.
3. `build-kernel-v2.sh`, then `finalize-kernel-symbols.sh`: final v3 DTB,
   explicit `DTC_FLAGS=-@`, board/config validation and matching modules.
4. **build-desktop-rootfs-v2.sh** with rootfs/Dockerfile.final: module
   integration and SSH service/socket masking; Docker export followed by
   offline hostname/hosts/resolver normalization under fakeroot. Its
   separate context contains only the final Dockerfile, desktop instructions
   and matching modules; it never uploads generated rootfs/disk images.
5. `assemble-image.sh`: portable 6 GiB MBR image, 512 MiB FAT32 boot,
   remaining ext4 root, checked filesystems, SHA256 sums and zstd.
6. Optional `assemble-capacity-image.sh 30943995904` for the authorized
   Kingston: regular-file ext4 expansion, 29510 MiB final image, then
   separately confirmed `flash-usb-native.py` (FLASH-NATIVE.md).

## Why offline special-file normalization is essential

Docker mounts `/etc/hostname`, `/etc/hosts` and `/etc/resolv.conf` into
build/run containers. Replacing resolv.conf with a symlink during RUN
failed with `Device or resource busy`, after all Ubuntu packages had
installed. Writes to the other two mounted files would not reliably
persist into the exported image either. The new Dockerfile never tries
to replace these mounts. The exporter modifies the **ordinary extracted
rootfs tree**, explicitly preserving numeric ownership, before making
the final rootfs tar. It verifies the hostname, resolver symlink and
both SSH masks; the assembler reports key filesystem ownership.

## One-time recovery of this session's package build

Failed legacy build container `3174e1257e7e` exited at the resolver-symlink
operation, after package installation, cleaning, account/service setup
and machine-id reset. Saving its filesystem with `docker commit` avoids
another full ARM64 emulated package installation. The normal recipe
above does **not** depend on that container: it builds the same userspace
from the pinned official Ubuntu Base using Dockerfile.v3. Finalization
also checks `dpkg --audit`, the required desktop packages, absence of
build-only proxy/service inhibition, and an empty machine-id.

## Acceptance and safety

Factory flow: patched original eMMC vendor U-Boot -> USB extlinux ->
native Linux 7.3.6 -> USB Ubuntu XFCE. No second USB U-Boot is required
or included in this new image. Removing USB while powered off should
retain the original Android path; physical fallback remains to be observed.
No new eMMC write or saveenv is part of this task. See FACTORY-UBOOT.md
for per-machine original-image backup/patch/recovery procedures.

User `linux` and root UART autologin/passwordless sudo are deliberately
permissive bring-up settings. SSH service and socket are masked. Read
FIRST-STEPS.txt and harden the account/autologin/sudo before daily use.
Offline build and flash success do not establish panel or keyboard
operation on this kernel; those require the first real laptop boot.

## Offline distribution of the recipe

`bash scripts/package-release-recipe.sh artifacts/CHOSEN-NEW-NAME.tar.gz`
packages the current scripts, board sources, exact reference PHY patch,
factory-patch tool/guides, config/package manifests and saved publisher
checksum metadata. It refuses to overwrite an existing bundle. The
separate `.SHA256SUMS` file identifies that exact bundle. Source archives
and disk images remain on the server; the recipe does not embed them.
