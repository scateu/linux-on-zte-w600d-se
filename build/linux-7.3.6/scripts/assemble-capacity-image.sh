#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
CAPACITY_BYTES=${1:?Usage: assemble-capacity-image.sh USB-capacity-in-bytes}
[[ "$CAPACITY_BYTES" =~ ^[0-9]+$ ]] || { printf 'Capacity must be an integer byte count\n' >&2; exit 1; }
TOTAL_MIB=$(( CAPACITY_BYTES / 1024 / 1024 ))
(( TOTAL_MIB >= 6144 )) || { printf 'Capacity must be at least 6 GiB\n' >&2; exit 1; }
IMAGE="$ROOT/artifacts/w600d-ubuntu-xfce-7.3.6-20261124-usb-${TOTAL_MIB}MiB.img"
WORK="$ROOT/out/usb-capacity-${TOTAL_MIB}MiB"
test ! -e "$IMAGE" || { printf 'Refusing to overwrite existing image: %s\n' "$IMAGE" >&2; exit 1; }
test ! -e "$WORK" || { printf 'Refusing to reuse existing assembly directory: %s\n' "$WORK" >&2; exit 1; }
test -s artifacts/usb-image-SHA256SUMS
test -s out/usb-image/boot.fat
test -s out/usb-image/rootfs.ext4
mkdir -p "$WORK" logs
exec > >(tee "logs/assemble-capacity-${TOTAL_MIB}MiB.log") 2>&1
python3 scripts/validate-board.py artifacts/kernel/rk3568-zte-w600d-mainline.dtb
python3 scripts/validate-kernel-config.py artifacts/kernel/config-7.3.6-w600d-usb
fsck.vfat -n out/usb-image/boot.fat
e2fsck -fn out/usb-image/rootfs.ext4
cp --reflink=auto --sparse=always out/usb-image/rootfs.ext4 "$WORK/rootfs.ext4"
truncate -s "$(( (TOTAL_MIB - 513) * 1024 * 1024 ))" "$WORK/rootfs.ext4"
resize2fs "$WORK/rootfs.ext4"
e2fsck -fn "$WORK/rootfs.ext4"
truncate -s "${TOTAL_MIB}M" "$IMAGE"
printf 'label: dos\nlabel-id: 0x24c0d202\nunit: sectors\n\nstart=2048, size=1048576, type=c, bootable\nstart=1050624, type=83\n' | sfdisk "$IMAGE"
dd if=out/usb-image/boot.fat of="$IMAGE" bs=1M seek=1 conv=notrunc,sparse status=progress
dd if="$WORK/rootfs.ext4" of="$IMAGE" bs=1M seek=513 conv=notrunc,sparse status=progress
sfdisk --verify "$IMAGE"
sfdisk --json "$IMAGE" > "artifacts/usb-capacity-${TOTAL_MIB}MiB-partitions.json"
debugfs -R 'stat /home/linux' "$WORK/rootfs.ext4"
debugfs -R 'stat /etc/shadow' "$WORK/rootfs.ext4"
debugfs -R 'stat /etc/systemd/system/ssh.service' "$WORK/rootfs.ext4"
debugfs -R 'stat /etc/systemd/system/ssh.socket' "$WORK/rootfs.ext4"
debugfs -R 'cat /etc/fstab' "$WORK/rootfs.ext4"
cd artifacts
sha256sum "$(basename "$IMAGE")" > "usb-capacity-${TOTAL_MIB}MiB-SHA256SUMS"
zstd -T4 -3 --keep "$IMAGE" -o "$IMAGE.zst"
sha256sum "$(basename "$IMAGE").zst" >> "usb-capacity-${TOTAL_MIB}MiB-SHA256SUMS"
printf '\nFull-capacity regular-file image ready; no physical drive was accessed.\n'
printf 'Image bytes: %s; unused end-of-disk bytes: %s\n' "$(( TOTAL_MIB * 1024 * 1024 ))" "$(( CAPACITY_BYTES - TOTAL_MIB * 1024 * 1024 ))"
