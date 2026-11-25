#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
KERNEL_ARTIFACTS=${KERNEL_ARTIFACTS:-artifacts/kernel}
KERNEL_RELEASE=$(cat "$KERNEL_ARTIFACTS/kernelrelease")
BOARD_DTB=${BOARD_DTB:-rk3568-zte-w600d-mainline.dtb}
case "$KERNEL_RELEASE" in
    7.3.6-w600d-usb|7.3.6-w600d-usb-wifi) ;;
    *) printf 'Unexpected kernel release: %s\n' "$KERNEL_RELEASE" >&2; exit 1 ;;
esac
mkdir -p artifacts logs
exec > >(tee logs/build-desktop-rootfs-v2.log) 2>&1
test ! -e out/rootfs-final-export || { printf 'Refusing to reuse rootfs export tree\n' >&2; exit 1; }
test ! -e artifacts/ubuntu-w600d-rootfs.tar || { printf 'Refusing to overwrite final rootfs tar\n' >&2; exit 1; }
test -d "$KERNEL_ARTIFACTS/modules/lib/modules/$KERNEL_RELEASE"
python3 scripts/validate-board.py "$KERNEL_ARTIFACTS/$BOARD_DTB"
CONTEXT=$(mktemp -d "$ROOT/out/desktop-context-XXXXXX")
mkdir -p "$CONTEXT/rootfs" "$CONTEXT/artifacts/kernel/modules" "$CONTEXT/artifacts/firmware"
cp rootfs/Dockerfile.final rootfs/FIRST-STEPS.txt "$CONTEXT/rootfs/"
cp -a rootfs/overlay "$CONTEXT/rootfs/"
tar --exclude=build --exclude=source -C "$KERNEL_ARTIFACTS/modules" -cf - lib/modules | \
    tar -C "$CONTEXT/artifacts/kernel/modules" -xf -
if [ "$KERNEL_RELEASE" = 7.3.6-w600d-usb-wifi ]; then
    (cd artifacts/firmware && sha256sum -c SHA256SUMS)
    cp -a artifacts/firmware/mediatek artifacts/firmware/LICENSES "$CONTEXT/artifacts/firmware/"
fi
printf 'Minimal desktop integration context: %s\n' "$CONTEXT"
docker build --platform linux/arm64 --network none --build-arg "KERNEL_RELEASE=$KERNEL_RELEASE" \
    -f "$CONTEXT/rootfs/Dockerfile.final" -t w600d-ubuntu-xfce:7.3.6 "$CONTEXT"
docker run --rm --network none --platform linux/arm64 -e "KERNEL_RELEASE=$KERNEL_RELEASE" \
    w600d-ubuntu-xfce:7.3.6 /bin/sh -ec '
    test -x /sbin/init
    test -x /usr/bin/xfce4-session
    test -d "/lib/modules/$KERNEL_RELEASE"
    if [ "$KERNEL_RELEASE" = 7.3.6-w600d-usb-wifi ]; then
        test -f /lib/firmware/mediatek/mt7663_n9_v3.bin
        test -f /lib/firmware/mediatek/mt7663pr2h.bin
        test -f /lib/firmware/LICENSES/LICENCE.mediatek
        dpkg-query -W wpasupplicant wireless-regdb bluez libinput-tools
    fi
    test "$(readlink /etc/systemd/system/ssh.socket)" = /dev/null
    test "$(readlink /etc/systemd/system/ssh.service)" = /dev/null
    test "$(readlink /etc/systemd/system/default.target)" = /lib/systemd/system/graphical.target || test "$(readlink /etc/systemd/system/default.target)" = /usr/lib/systemd/system/graphical.target
    test ! -e /etc/apt/apt.conf.d/90-build-proxy
    test ! -e /usr/sbin/policy-rc.d
    test ! -s /etc/machine-id
    test -z "$(dpkg --audit)"
    dpkg-query -W xfce4 lightdm systemd-sysv network-manager
    dpkg-query -W -f="\${binary:Package}\t\${Version}\n"
' > artifacts/rootfs-package-versions.txt
CONTAINER=$(docker create --platform linux/arm64 w600d-ubuntu-xfce:7.3.6)
trap 'docker rm "$CONTAINER" >/dev/null' EXIT
docker export "$CONTAINER" -o artifacts/ubuntu-w600d-rootfs.raw.tar
fakeroot bash -c '
    set -euo pipefail
    mkdir -p out/rootfs-final-export
    tar --same-owner -xpf artifacts/ubuntu-w600d-rootfs.raw.tar -C out/rootfs-final-export
    chown 0:0 out/rootfs-final-export
    install -m 644 rootfs/image-hostname out/rootfs-final-export/etc/hostname
    install -m 644 rootfs/image-hosts out/rootfs-final-export/etc/hosts
    rm -f out/rootfs-final-export/etc/resolv.conf
    ln -s /run/systemd/resolve/stub-resolv.conf out/rootfs-final-export/etc/resolv.conf
    install -m 644 artifacts/rootfs-package-versions.txt out/rootfs-final-export/usr/share/w600d-package-versions.txt
    chown 0:0 out/rootfs-final-export/etc/hostname out/rootfs-final-export/etc/hosts out/rootfs-final-export/usr/share/w600d-package-versions.txt
    chown -h 0:0 out/rootfs-final-export/etc/resolv.conf
    test "$(cat out/rootfs-final-export/etc/hostname)" = w600d-linux
    test "$(readlink out/rootfs-final-export/etc/resolv.conf)" = /run/systemd/resolve/stub-resolv.conf
    test "$(readlink out/rootfs-final-export/etc/systemd/system/ssh.service)" = /dev/null
    test "$(readlink out/rootfs-final-export/etc/systemd/system/ssh.socket)" = /dev/null
    tar --numeric-owner -cpf artifacts/ubuntu-w600d-rootfs.tar -C out/rootfs-final-export .
'
sha256sum artifacts/ubuntu-w600d-rootfs.tar > artifacts/rootfs-SHA256SUMS
printf '\nUbuntu XFCE rootfs exported with offline hostname/hosts/resolver normalization.\n'
