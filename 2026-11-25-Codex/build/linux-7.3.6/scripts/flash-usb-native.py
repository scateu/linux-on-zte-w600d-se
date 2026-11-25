#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def run_json(command):
    return json.loads(subprocess.check_output(command, text=True))


def inventory(device):
    result = run_json([
        "lsblk", "--json", "--bytes", "--paths", "-o",
        "NAME,TYPE,SIZE,MODEL,SERIAL,TRAN,RO,MOUNTPOINTS", str(device),
    ])["blockdevices"]
    if len(result) != 1:
        raise SystemExit("Expected exactly one whole disk")
    return result[0]


def descendants(device):
    yield device
    for child in device.get("children", []):
        yield from descendants(child)


def main():
    parser = argparse.ArgumentParser(description="Guarded native USB flash with uncached read-back verification")
    parser.add_argument("image", type=Path)
    parser.add_argument("device", type=Path)
    parser.add_argument("--confirm-erase")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--tool-image", default="archlinux:latest")
    arguments = parser.parse_args()
    image = arguments.image.resolve(strict=True)
    device = arguments.device.resolve(strict=True)
    if not image.is_file() or not device.is_block_device():
        raise SystemExit("Expected a regular image and a whole block device")
    image_bytes = image.stat().st_size
    if not image_bytes or image_bytes % (1024 * 1024):
        raise SystemExit("Expected a nonempty whole-MiB image for aligned direct verification")
    target = inventory(device)
    if target["type"] != "disk" or target["tran"] != "usb" or target["ro"]:
        raise SystemExit("Refusing non-USB, partition, or read-only target")
    serial = (target.get("serial") or "").strip()
    if not serial:
        raise SystemExit("Refusing USB without a stable serial")
    if int(target["size"]) < image_bytes:
        raise SystemExit("USB is smaller than the image")
    if any(mount for item in descendants(target) for mount in item.get("mountpoints", []) or []):
        raise SystemExit("Refusing mounted disk or partitions")
    confirmation = f"{device}:{serial}"
    print(json.dumps(target, indent=2), flush=True)
    if arguments.confirm_erase != confirmation:
        print(f"No write performed. Required confirmation: --confirm-erase {confirmation}")
        return
    if not re.fullmatch(r"[0-9a-f]{64}", arguments.expected_sha256 or ""):
        raise SystemExit("A lowercase --expected-sha256 from the image manifest is required")
    checksum = hashlib.sha256()
    with image.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            checksum.update(block)
    if checksum.hexdigest() != arguments.expected_sha256:
        raise SystemExit("Image checksum differs from the manifest; no write performed")
    tools = run_json(["docker", "image", "inspect", arguments.tool_image])[0]
    if tools["Architecture"] != "amd64" or tools["Os"] != "linux":
        raise SystemExit("Expected a cached native Linux amd64 tool image")
    subprocess.run([
        "docker", "run", "--rm", "--pull", "never", "--network", "none",
        "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        tools["Id"], "/bin/bash", "-ec",
        "command -v dd; command -v sha256sum; command -v cut",
    ], check=True)
    if inventory(device) != target:
        raise SystemExit("Device identity or mounts changed; no write performed")
    print(f"Erasing {device} serial {serial}; native tool image {tools['Id']}", flush=True)
    subprocess.run([
        "docker", "run", "--rm", "--pull", "never", "--network", "none",
        "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--device", f"{device}:/dev/usb-target:rw",
        "--mount", f"type=bind,src={image},dst=/image.img,readonly",
        tools["Id"], "/bin/bash", "-euo", "pipefail", "-c",
        'dd if=/image.img of=/dev/usb-target bs=8M conv=fsync status=progress; '
        'disk_hash=$(dd if=/dev/usb-target bs=1M count="$1" iflag=direct status=progress '
        '| sha256sum | cut -d" " -f1); '
        'test "$disk_hash" = "$2"; '
        'printf "USB direct read-back SHA256 verified: %s\\n" "$disk_hash"',
        "flash-usb", str(image_bytes // (1024 * 1024)), arguments.expected_sha256,
    ], check=True)
    print("Flashed and uncached full-image read-back verified. Hardware boot acceptance remains pending.")


if __name__ == "__main__":
    main()
