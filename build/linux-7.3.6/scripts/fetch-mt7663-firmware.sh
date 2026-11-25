#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export ALL_PROXY="${ALL_PROXY:-socks5://192.168.1.5:1080}"
ARTIFACTS="$ROOT/artifacts/firmware"
CACHE="$ROOT/downloads/mediatek-20261125"
REVISION=16a7a3f83c2f83239b0395faac8da4acbbbb0ffe
BASE="https://gitlab.com/kernel-firmware/linux-firmware/-/raw/$REVISION"
API="https://gitlab.com/api/v4/projects/kernel-firmware%2Flinux-firmware/repository/files"
mkdir -p "$ARTIFACTS/mediatek" "$ARTIFACTS/LICENSES"
for filename in mt7663_n9_v3.bin mt7663pr2h.bin; do
    destination="$ARTIFACTS/mediatek/$filename"
    if [ ! -f "$destination" ]; then
        if [ -f "$CACHE/$filename" ]; then
            cp "$CACHE/$filename" "$destination"
        else
            test ! -e "$destination.partial"
            curl -fLsS --connect-timeout 15 --max-time 120 \
                "$BASE/mediatek/$filename" -o "$destination.partial"
            mv "$destination.partial" "$destination"
        fi
    fi
done
cd "$ARTIFACTS"
printf '%s\n' \
    'd8b8488f37f65e41ded9a911950afb000d236b36e5aa94ad9650ad0c3a86fd45  mediatek/mt7663_n9_v3.bin' \
    '534f2152f9b0f48dfcec9c1727b0bab9a3727a655d76d5ec818cc39a55602336  mediatek/mt7663pr2h.bin' \
    > SHA256SUMS
if [ ! -f LICENSES/LICENCE.mediatek ]; then
    if [ -f "$CACHE/LICENCE.mediatek" ]; then
        cp "$CACHE/LICENCE.mediatek" LICENSES/
    else
        curl -fLsS --connect-timeout 15 --max-time 120 \
            "$API/LICENSES%2FLICENCE.mediatek/raw?ref=$REVISION" \
            -o LICENSES/LICENCE.mediatek.partial
        mv LICENSES/LICENCE.mediatek.partial LICENSES/LICENCE.mediatek
    fi
fi
printf '%s\n' \
    'a90d3f66704d85889945fec5525ea77622549da83aced1aac99828383f8f1805  LICENSES/LICENCE.mediatek' \
    >> SHA256SUMS
sha256sum -c SHA256SUMS
printf 'Verified official MediaTek firmware at %s; license retained.\n' "$REVISION"
