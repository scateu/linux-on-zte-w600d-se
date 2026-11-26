#!/usr/bin/env bash
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
WORK=${WORK:-/home/k/codex-workdir-nov-24-2026/uboot-native}
REV=9d67454e920b3908529c9fc642a8c911db040896
SOURCE=$WORK/src/u-boot
OUTPUT=$WORK/out/build
STICK=$WORK/artifacts/stick
CROSS_COMPILE=${CROSS_COMPILE:-aarch64-linux-gnu-}
JOBS=${JOBS:-$(nproc)}

mkdir -p "$WORK/src" "$OUTPUT" "$STICK" "$WORK/logs"
if [ ! -d "$SOURCE/.git" ]; then
	git init -q "$SOURCE"
	git -C "$SOURCE" remote add origin https://github.com/u-boot/u-boot.git
	git -C "$SOURCE" fetch --depth=1 origin "$REV"
	git -C "$SOURCE" checkout --detach -q FETCH_HEAD
fi
test "$(git -C "$SOURCE" rev-parse HEAD)" = "$REV"

for PATCH in "$HERE"/patches/*.patch; do
	if git -C "$SOURCE" apply --reverse --check "$PATCH" 2>/dev/null; then
		printf 'Patch already applied: %s\n' "$(basename "$PATCH")"
	else
		git -C "$SOURCE" apply --check "$PATCH"
		git -C "$SOURCE" apply "$PATCH"
	fi
done
cp -R "$HERE/overlay/." "$SOURCE/"

make -C "$SOURCE" O="$OUTPUT" CROSS_COMPILE="$CROSS_COMPILE" \
	NO_PYTHON=1 zte-w600d-native-rk3568_defconfig
make -C "$SOURCE" O="$OUTPUT" CROSS_COMPILE="$CROSS_COMPILE" \
	NO_PYTHON=1 -j"$JOBS" u-boot.bin 2>&1 | tee "$WORK/logs/build.log"
python3 -I "$HERE/validate-build.py" "$OUTPUT"

"${CROSS_COMPILE}gcc" -c "$REPO/bootloader/usb-uboot/chain/chain.S" \
	-o "$WORK/out/chain.o"
"${CROSS_COMPILE}ld" -Ttext=0x10000000 "$WORK/out/chain.o" \
	-o "$WORK/out/chain.elf"
"${CROSS_COMPILE}objcopy" -O binary "$WORK/out/chain.elf" \
	"$STICK/w600d-native-chain.bin"
cp "$OUTPUT/u-boot.bin" "$STICK/u-boot-w600d-native.bin"
python3 -I "$REPO/bootloader/usb-uboot/chain/mkscr.py" \
	"$HERE/boot-native.cmd" "$STICK/boot-native.scr"
printf '%s\n' "$REV" > "$WORK/artifacts/UPSTREAM_REV"
(cd "$STICK" && sha256sum *.bin *.scr > SHA256SUMS)
printf '\nExperimental files: %s\n' "$STICK"
printf '%s\n' 'No USB/eMMC deployment performed. Keep boot-native.scr non-default.'
