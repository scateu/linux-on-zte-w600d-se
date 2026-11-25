#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
mkdir -p out/usb-image artifacts logs
exec > >(tee logs/assemble-image.log) 2>&1
IMAGE="$ROOT/artifacts/w600d-ubuntu-xfce-7.3.6-20261124.img"
test ! -e "$IMAGE" || { printf 'Refusing to overwrite existing image: %s\n' "$IMAGE" >&2; exit 1; }
python3 scripts/validate-board.py artifacts/kernel/rk3568-zte-w600d-mainline.dtb
python3 scripts/validate-kernel-config.py artifacts/kernel/config-7.3.6-w600d-usb
test -s artifacts/ubuntu-w600d-rootfs.tar
truncate -s 512M out/usb-image/boot.fat
mkfs.vfat -F 32 -n W600D_BOOT out/usb-image/boot.fat
mmd -i out/usb-image/boot.fat ::/boot ::/extlinux
mcopy -i out/usb-image/boot.fat artifacts/kernel/Image ::/boot/Image
mcopy -i out/usb-image/boot.fat artifacts/kernel/rk3568-zte-w600d-mainline.dtb ::/boot/
mcopy -i out/usb-image/boot.fat extlinux.conf ::/extlinux/extlinux.conf
ROOTFS_BYTES=$(( (6 * 1024 - 513) * 1024 * 1024 ))
truncate -s "$ROOTFS_BYTES" out/usb-image/rootfs.ext4
fakeroot bash -c '
    set -euo pipefail
    mkdir -p out/usb-image/rootfs
    tar --same-owner -xpf artifacts/ubuntu-w600d-rootfs.tar -C out/usb-image/rootfs
    chown 0:0 out/usb-image/rootfs
    mkfs.ext4 -F -L W600D_ROOT -U 24c0d202-0002-4000-8000-000000000002 -E root_owner=0:0 -d out/usb-image/rootfs out/usb-image/rootfs.ext4
'
e2fsck -fn out/usb-image/rootfs.ext4
truncate -s 6G "$IMAGE"
printf 'label: dos\nlabel-id: 0x24c0d202\nunit: sectors\n\nstart=2048, size=1048576, type=c, bootable\nstart=1050624, type=83\n' | sfdisk "$IMAGE"
dd if=out/usb-image/boot.fat of="$IMAGE" bs=1M seek=1 conv=notrunc,sparse status=progress
dd if=out/usb-image/rootfs.ext4 of="$IMAGE" bs=1M seek=513 conv=notrunc,sparse status=progress
sfdisk --verify "$IMAGE"
sfdisk --json "$IMAGE" > artifacts/usb-partitions.json
mdir -i out/usb-image/boot.fat ::/boot ::/extlinux
debugfs -R 'stat /home/linux' out/usb-image/rootfs.ext4
debugfs -R 'stat /etc/shadow' out/usb-image/rootfs.ext4
debugfs -R 'cat /etc/fstab' out/usb-image/rootfs.ext4
cd artifacts
sha256sum "$(basename "$IMAGE")" > usb-image-SHA256SUMS
zstd -T4 -3 --keep "$IMAGE" -o "$IMAGE.zst"
sha256sum "$(basename "$IMAGE").zst" >> usb-image-SHA256SUMS
printf '\nImage assembled and filesystem checked. Not yet flashed or hardware-tested.\n'
