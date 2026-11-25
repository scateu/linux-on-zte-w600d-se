#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
CONTEXT="$ROOT/out/native-mtools-context"
test "$(uname -m)" = x86_64
mkdir -p "$CONTEXT/native/usr/bin" "$CONTEXT/native/usr/lib/x86_64-linux-gnu" "$CONTEXT/native/lib/x86_64-linux-gnu" "$CONTEXT/native/lib64"
for tool in mcopy mren mdir; do
    cp /usr/bin/mtools "$CONTEXT/native/usr/bin/$tool"
done
cp -L /lib/x86_64-linux-gnu/libc.so.6 "$CONTEXT/native/lib/x86_64-linux-gnu/libc.so.6"
cp -L /lib64/ld-linux-x86-64.so.2 "$CONTEXT/native/lib64/ld-linux-x86-64.so.2"
cp -a /usr/lib/x86_64-linux-gnu/gconv "$CONTEXT/native/usr/lib/x86_64-linux-gnu/"
docker build --network none --file "$ROOT/rootfs/Dockerfile.mtools" --tag w600d-native-mtools:20261124 "$CONTEXT"
docker run --rm --pull never --network none --read-only --cap-drop ALL --security-opt no-new-privileges w600d-native-mtools:20261124 /usr/bin/mcopy -V
