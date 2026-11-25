#!/usr/bin/env bash
set -euo pipefail
IMAGE=${1:?Usage: check-userspace.sh Docker-image-tag}
docker run --rm --network none --platform linux/arm64 "$IMAGE" /bin/sh -ec '
    test -z "$(dpkg --audit)"
    test -x /sbin/init
    test -x /usr/bin/Xorg
    test -x /usr/bin/xfce4-session
    test -f /usr/share/xsessions/xfce.desktop
    test "$(readlink /etc/systemd/system/ssh.service)" = /dev/null
    test "$(readlink /etc/systemd/system/ssh.socket)" = /dev/null
    test ! -e /etc/apt/apt.conf.d/90-build-proxy
    test ! -e /usr/sbin/policy-rc.d
    test ! -s /etc/machine-id
    id linux >/dev/null
    dpkg-query -W
'
