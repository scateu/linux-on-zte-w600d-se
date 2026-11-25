# Guarded USB flashing on trash

The full-capacity assembler is documented in `USB-CAPACITY.md`; the
portable build remains documented in `BUILD-READY.md`. The original
`flash-usb.py` uses the target ARM64 Ubuntu image as tooling. For a roughly
31 GB USB, use `flash-usb-native.py` on the x86_64 build host instead, to
avoid emulating the writer and SHA256 verifier.

The native writer uses an already cached Linux amd64 `archlinux:latest`
Docker image **only as build-host tooling**, never as the laptop rootfs.
It resolves the cached image to its immutable image ID before running,
uses no network, exposes only the explicitly selected whole USB device
and read-only disk-image file, and drops all container capabilities. It
does not need a privileged container, the internal server disk, or sudo.
On a new build server, provision equivalent cached native coreutils/bash
tooling first; `--tool-image` selects it. The script refuses non-amd64
tooling.

Dry run, which never writes:

```sh
python3 scripts/flash-usb-native.py \
  artifacts/w600d-ubuntu-xfce-7.3.6-20261124-usb-29510MiB.img /dev/sdb
```

After explicit permission, immediately recheck `lsblk` model, serial,
USB transport and that every descendant is unmounted. The writer repeats
these checks, refuses read-only devices and insufficient capacity, and
requires both the exact erase confirmation and a matching image SHA256:

```sh
set -o pipefail
IMAGE=artifacts/w600d-ubuntu-xfce-7.3.6-20261124-usb-29510MiB.img
HASH=$(awk -v name="$(basename "$IMAGE")" '$2 == name {print $1}' \
  artifacts/usb-capacity-29510MiB-SHA256SUMS)
python3 scripts/flash-usb-native.py "$IMAGE" /dev/sdb \
  --expected-sha256 "$HASH" \
  --confirm-erase /dev/sdb:E0D55E625BE9F440F84702D0 \
  2>&1 | tee logs/flash-kingston-20261124.log
```

These exact names identify the authorized Kingston, not a general license
to erase future `/dev/sdb` devices. If its identity changes, stop.

The writer checks the source file's complete hash **before writing**, then
uses `dd conv=fsync` for the write and `dd iflag=direct` for a complete,
aligned, uncached read-back of the image-sized disk region. It requires an
exact checksum match. The last sub-MiB tail outside the image is neither
used by the partition table nor claimed as verified. A failed checksum or
direct read is a failed flash; do not present it as ready for hardware boot.

Flashing is destructive to this USB only. Native display and keyboard,
normal desktop boot, and USB-removed Android fallback still require tests
on the physical laptop.
