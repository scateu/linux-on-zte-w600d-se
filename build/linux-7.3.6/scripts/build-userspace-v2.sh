#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
mkdir -p logs out
exec > >(tee logs/build-userspace-v2.log) 2>&1
CONTEXT=$(mktemp -d "$ROOT/out/userspace-context-XXXXXX")
cp rootfs/Dockerfile.v3 "$CONTEXT/Dockerfile"
printf 'Minimal userspace build context: %s\n' "$CONTEXT"
docker build --platform linux/arm64 --network host --target userspace \
    --build-arg "APT_PROXY=${APT_PROXY:-socks5h://192.168.1.5:1080}" \
    -t "${USERSPACE_IMAGE:-w600d-ubuntu-xfce-base:24.04.5}" "$CONTEXT"
