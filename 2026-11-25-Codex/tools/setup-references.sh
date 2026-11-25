#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
UBOOT="$ROOT/bootloader/usb-uboot"
CLOUDBOOK="$ROOT/build/linux-7.3.6/reference/cloudbook-air-mainline-linux"
OVERRIDE="$ROOT/build/linux-7.3.6/reference-overrides/cloudbook-local.patch"

check_reference() {
    local directory=$1 expected=$2 actual
    if [ ! -d "$directory/.git" ] && [ ! -f "$directory/.git" ]; then
        printf 'Missing reference: %s; clone with --recurse-submodules first.\n' "$directory" >&2
        exit 1
    fi
    actual=$(git -C "$directory" rev-parse HEAD)
    if [ "$actual" != "$expected" ]; then
        printf 'Reference revision differs: %s is %s, expected %s; not changing it.\n' "$directory" "$actual" "$expected" >&2
        exit 1
    fi
}

check_reference "$UBOOT" c6283107a754a2baeb48843c11dc0640a77a0444
check_reference "$CLOUDBOOK" 3a031bd9fd3d6c79d9ad0444af5088d0c21d4a43

if [ -L "$UBOOT/patches" ]; then
    [ "$(readlink "$UBOOT/patches")" = patches_for_upstream ] || {
        printf 'Unexpected existing patch alias; not replacing it.\n' >&2
        exit 1
    }
elif [ -e "$UBOOT/patches" ]; then
    printf 'Unexpected existing patches path; not replacing it.\n' >&2
    exit 1
else
    ln -s patches_for_upstream "$UBOOT/patches"
fi

if git -C "$CLOUDBOOK" apply --reverse --check "$OVERRIDE" 2>/dev/null; then
    printf 'CloudBook local override already present.\n'
else
    git -C "$CLOUDBOOK" apply --check "$OVERRIDE"
    git -C "$CLOUDBOOK" apply "$OVERRIDE"
fi
printf 'Both pinned references are ready; no reset or boot-device access performed.\n'
