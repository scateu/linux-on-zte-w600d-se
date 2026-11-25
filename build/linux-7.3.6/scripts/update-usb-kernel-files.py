#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def inventory(device):
    data = json.loads(subprocess.check_output([
        "lsblk", "--json", "--bytes", "--paths", "-o",
        "NAME,TYPE,SIZE,MODEL,SERIAL,TRAN,RO,FSTYPE,LABEL,PARTUUID,MOUNTPOINTS",
        str(device),
    ], text=True))["blockdevices"]
    if len(data) != 1:
        raise SystemExit("Expected exactly one whole disk")
    return data[0]


def descendants(device):
    yield device
    for child in device.get("children", []):
        yield from descendants(child)


def main():
    parser = argparse.ArgumentParser(description="Update only W600D USB FAT /boot/Image, preserving rollback")
    parser.add_argument("kernel", type=Path)
    parser.add_argument("device", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--confirm-update")
    arguments = parser.parse_args()
    kernel = arguments.kernel.resolve(strict=True)
    device = arguments.device.resolve(strict=True)
    if not kernel.is_file() or not device.is_block_device():
        raise SystemExit("Expected a regular kernel Image and a whole block device")
    if not 1024 * 1024 < kernel.stat().st_size < 128 * 1024 * 1024:
        raise SystemExit("Unexpected kernel Image size")
    if not re.fullmatch(r"[0-9a-f]{64}", arguments.expected_sha256):
        raise SystemExit("Expected a lowercase SHA256 from the build manifest")
    checksum = hashlib.sha256()
    with kernel.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            checksum.update(block)
    if checksum.hexdigest() != arguments.expected_sha256:
        raise SystemExit("Kernel source SHA256 mismatch; no USB write")
    target = inventory(device)
    if target["type"] != "disk" or target["tran"] != "usb" or target["ro"]:
        raise SystemExit("Refusing a non-USB, partition, or read-only device")
    serial = (target.get("serial") or "").strip()
    if serial != "E0D55E625BE9F440F84702D0" or int(target["size"]) != 30943995904:
        raise SystemExit("Refusing a disk other than the authorized Kingston USB")
    if any(mount for item in descendants(target) for mount in item.get("mountpoints", []) or []):
        raise SystemExit("Refusing mounted USB or partitions")
    partitions = target.get("children", [])
    boot_matches = [part for part in partitions if part.get("partuuid") == "24c0d202-01"]
    root_matches = [part for part in partitions if part.get("partuuid") == "24c0d202-02"]
    if len(boot_matches) != 1 or len(root_matches) != 1:
        raise SystemExit("Expected the new Linux USB partition UUIDs")
    boot = boot_matches[0]
    if boot.get("fstype") != "vfat" or boot.get("label") != "W600D_BOOT" or int(boot["size"]) != 536870912:
        raise SystemExit("Unexpected FAT32 boot partition")
    if root_matches[0].get("fstype") != "ext4" or root_matches[0].get("label") != "W600D_ROOT":
        raise SystemExit("Unexpected Linux root partition")
    print(json.dumps(target, indent=2), flush=True)
    confirmation = f"{device}:{serial}"
    if arguments.confirm_update != confirmation:
        print(f"No write performed. Required confirmation: --confirm-update {confirmation}")
        return
    tools = json.loads(subprocess.check_output([
        "docker", "image", "inspect", "w600d-native-mtools:20261124",
    ], text=True))[0]
    if tools["Architecture"] != "amd64" or tools["Os"] != "linux":
        raise SystemExit("Expected native Linux amd64 tools")
    base = [
        "docker", "run", "--rm", "--pull", "never", "--network", "none",
        "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--env", "MTOOLSRC=/dev/null",
        "--device", f'{boot["name"]}:/dev/w600d-boot:rw',
        "--mount", f"type=bind,src={kernel},dst=/kernel.Image,readonly",
        tools["Id"],
    ]

    def mtools(tool, *parameters, check=True):
        if inventory(device) != target:
            raise SystemExit("USB identity or mount state changed; stopping")
        return subprocess.run(base + [f"/usr/bin/{tool}", "-i", "/dev/w600d-boot", *parameters],
                              check=check)

    active = "::/boot/Image"
    staged = "::/boot/Image.lanes-new"
    rollback = "::/boot/Image.pre-lanes-20261124"
    mtools("mdir", active)
    for name in (staged, rollback):
        if mtools("mdir", name, check=False).returncode == 0:
            raise SystemExit(f"Refusing existing {name}; inspect prior update before retrying")
    print(f"Writing only {boot['name']} {staged}; old Image remains intact", flush=True)
    mtools("mcopy", "/kernel.Image", staged)
    subprocess.run(["sync"], check=True)
    mtools("mdir", staged)
    mtools("mren", active, rollback)
    try:
        mtools("mren", staged, active)
    except subprocess.CalledProcessError:
        mtools("mren", rollback, active)
        subprocess.run(["sync"], check=True)
        raise
    subprocess.run(["sync"], check=True)
    mtools("mdir", active)
    mtools("mdir", rollback)
    print("File update and sync complete. Old Image retained for rollback.", flush=True)
    print(f"Source Image SHA256: {checksum.hexdigest()}", flush=True)
    print("DTB, extlinux, partition table, ext4 root and eMMC untouched.", flush=True)
    print("No full-disk or kernel-content read-back performed; hardware boot test required.", flush=True)


if __name__ == "__main__":
    main()
