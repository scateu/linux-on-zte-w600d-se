#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
export ALL_PROXY="${ALL_PROXY:-socks5://192.168.1.5:1080}"
mkdir -p downloads src out artifacts logs
fetch() {
    curl --proxy "$ALL_PROXY" -fLsS --retry 3 --connect-timeout 20 --max-time 1200 "$1" -o "$2"
}
if ! test -f downloads/kernel-org-releases-20261124.json; then
    fetch https://www.kernel.org/releases.json downloads/kernel-org-releases-20261124.json
fi
if ! test -f downloads/kernel-7x-sha256sums.asc; then
    fetch https://cdn.kernel.org/pub/linux/kernel/v7.x/sha256sums.asc downloads/kernel-7x-sha256sums.asc
fi
if ! test -f downloads/linux-7.3.6.tar.xz; then
    fetch https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.3.6.tar.xz downloads/linux-7.3.6.tar.xz
fi
EXPECTED=$(awk '$2 == "linux-7.3.6.tar.xz" {print $1}' downloads/kernel-7x-sha256sums.asc)
test -n "$EXPECTED"
printf '%s  %s\n' "$EXPECTED" downloads/linux-7.3.6.tar.xz | sha256sum -c -
if ! test -d src/linux-7.3.6; then
    tar -xJf downloads/linux-7.3.6.tar.xz -C src
fi
UBUNTU_BASE=https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release
if ! test -f downloads/ubuntu-base-SHA256SUMS; then
    fetch "$UBUNTU_BASE/SHA256SUMS" downloads/ubuntu-base-SHA256SUMS
fi
if ! test -f downloads/ubuntu-base-24.04.5-base-arm64.tar.gz; then
    fetch "$UBUNTU_BASE/ubuntu-base-24.04.5-base-arm64.tar.gz" downloads/ubuntu-base-24.04.5-base-arm64.tar.gz
fi
EXPECTED=$(awk '$2 ~ /ubuntu-base-24[.]04[.]5-base-arm64[.]tar[.]gz$/ {print $1}' downloads/ubuntu-base-SHA256SUMS)
test -n "$EXPECTED"
printf '%s  %s\n' "$EXPECTED" downloads/ubuntu-base-24.04.5-base-arm64.tar.gz | sha256sum -c -
docker import --platform linux/arm64 downloads/ubuntu-base-24.04.5-base-arm64.tar.gz w600d-ubuntu-base:24.04.5
docker run --rm --platform linux/arm64 w600d-ubuntu-base:24.04.5 uname -m
