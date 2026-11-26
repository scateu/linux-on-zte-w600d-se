#!/usr/bin/env python3
import gzip
import hashlib
import importlib.util
import pathlib
import re
import struct
import sys


def main():
    path = pathlib.Path(sys.argv[1])
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as stream:
        image = stream.read()
    root = pathlib.Path(__file__).resolve().parents[2]
    parser_path = root / "bootloader/usb-uboot/01_vendor-env_patch_uboot_a/patch-uboot-env.py"
    spec = importlib.util.spec_from_file_location("factory_parser", parser_path)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    print(f"Raw backup: {len(image)} bytes, SHA256={hashlib.sha256(image).hexdigest()}")
    if len(image) != 0x400000:
        raise SystemExit("Expected this laptop's 4 MiB two-FIT backup")
    print(f"FIT copies identical: {image[:0x200000] == image[0x200000:]}")
    for base in (0, 0x200000):
        blob = image[base:base + 0x200000]
        if blob[:4] != bytes.fromhex("d00dfeed"):
            raise SystemExit(f"Missing FIT at {base:#x}")
        total = struct.unpack_from(">I", blob, 4)[0]
        if not 40 <= total <= len(blob):
            raise SystemExit("Invalid FIT header length")
        position = parser.u32(blob, "images/uboot", "data-position")
        size = parser.u32(blob, "images/uboot", "data-size")
        load = parser.u32(blob, "images/uboot", "load")
        if position < total or position + size > len(blob):
            raise SystemExit("Invalid external payload extent")
        payload = blob[position:position + size]
        offset, length = parser.fdt_prop(blob, "images/uboot/hash", "value")
        digest = hashlib.sha256(payload).digest()
        if length != 32 or digest != blob[offset:offset + length]:
            raise SystemExit(f"U-Boot payload hash mismatch at {base:#x}")
        print(f"\nFIT {base:#x}: payload={position:#x}, bytes={size}, load={load:#x}")
        print(f"Verified payload SHA256={digest.hex()}")
        for match in re.finditer(rb"U-Boot 2017\.09[^\x00\r\n]*", payload):
            print(match.group().decode("ascii", errors="replace"))
        for name in ("bootcmd", "bootdelay", "scan_dev_for_boot",
                     "scan_dev_for_extlinux", "scan_dev_for_scripts", "boot_scripts"):
            key = name.encode() + b"="
            offset = payload.find(key)
            if offset >= 0:
                end = payload.find(b"\0", offset)
                print(payload[offset:end].decode("ascii", errors="replace"))
        for symbol in (b"vop2_initial", b"analogix_dp_set_link_bandwidth",
                       b"analogix_dp_set_lane_count", b"analogix_dp_set_lane_link_training"):
            offset = payload.find(symbol + b"\0")
            print(f"String {symbol.decode()}: " +
                  (f"payload+{offset:#x}" if offset >= 0 else "not found"))
    print("\nRead-only inspection completed; no image or device modified.")


if __name__ == "__main__":
    main()
