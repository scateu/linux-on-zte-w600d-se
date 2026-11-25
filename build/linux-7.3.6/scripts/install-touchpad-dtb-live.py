#!/usr/bin/env python3
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


EXPECTED_SERIAL = "E0D55E625BE9F440F84702D0"
EXPECTED_BYTES = 30943995904
DTB_VARIANTS = {
    "touchpad-v4": ("rk3568-zte-w600d-mainline.dtb", "rk3568-zte-w600d-mainline-v4-touchpad.dtb"),
    "sdio-v5": ("rk3568-zte-w600d-mainline-v4-touchpad.dtb", "rk3568-zte-w600d-mainline-v5-sdio.dtb"),
    "wifi-bt-v6": ("rk3568-zte-w600d-mainline-v5-sdio.dtb", "rk3568-zte-w600d-mainline-v6-wifi-bt.dtb"),
}


def output(*arguments):
    return subprocess.check_output(arguments, text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Guarded, file-only live USB touchpad DTB update")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--normalize-container-markers", action="store_true")
    parser.add_argument("--variant", choices=DTB_VARIANTS, default="touchpad-v4")
    parser.add_argument("--image", type=Path)
    parser.add_argument("--image-sha256")
    arguments = parser.parse_args()
    old_dtb_name, new_dtb_name = DTB_VARIANTS[arguments.variant]
    if arguments.variant == "wifi-bt-v6":
        if not arguments.image or not arguments.image_sha256:
            raise ValueError("Wi-Fi v6 requires the matching kernel Image and checksum")
        if digest(arguments.image) != arguments.image_sha256:
            raise ValueError("Candidate kernel Image checksum differs")
        with arguments.image.open("rb") as image:
            if image.read(64)[56:60] != b"ARM\x64":
                raise ValueError("Candidate is not an ARM64 kernel Image")
    elif arguments.image or arguments.image_sha256:
        raise ValueError("Kernel replacement is only allowed for the Wi-Fi v6 variant")
    boot = Path("/media/boot")
    root_device = output("findmnt", "-n", "-o", "SOURCE", "--target", "/")
    boot_device = output("findmnt", "-n", "-o", "SOURCE", "--target", str(boot))
    root_block = Path(root_device).name
    disk = (Path("/sys/class/block") / root_block).resolve(strict=True).parent.name
    identity = json.loads(output("lsblk", "-J", "-d", "-b", "-o",
                                 "NAME,TRAN,SERIAL,SIZE", "/dev/" + disk))["blockdevices"]
    if len(identity) != 1 or identity[0]["tran"] != "usb" or \
            identity[0]["serial"] != EXPECTED_SERIAL or identity[0]["size"] != EXPECTED_BYTES:
        raise ValueError("Unexpected USB identity; refusing any write")
    if root_device != "/dev/" + disk + "2" or boot_device != "/dev/" + disk + "1":
        raise ValueError("Root and boot are not the expected partitions of the same USB")
    if output("findmnt", "-n", "-o", "FSTYPE", "--target", str(boot)) != "vfat":
        raise ValueError("Boot mount is not FAT")
    if "ro" not in output("findmnt", "-n", "-o", "OPTIONS", "--target", str(boot)).split(","):
        raise ValueError("Boot must start read-only")
    if digest(arguments.candidate) != arguments.sha256:
        raise ValueError("Candidate DTB checksum differs")
    config = boot / "extlinux/extlinux.conf"
    original = config.read_text()
    prefix, normal = original.split("LABEL ubuntu-xfce\n")
    section, separator, remaining = normal.partition("\nLABEL ")
    old_line = "    FDT /boot/" + old_dtb_name
    if section.count(old_line) != 1:
        raise ValueError("Unexpected normal boot entry; refusing to rewrite it")
    updated = prefix + "LABEL ubuntu-xfce\n" + section.replace(
        old_line, "    FDT /boot/" + new_dtb_name) + separator + remaining
    image_destination = boot / "boot/Image.wifi-20261125"
    image_staging = image_destination.with_name(image_destination.name + ".staged")
    if arguments.image:
        if section.count("    LINUX /boot/Image\n") != 1:
            raise ValueError("Unexpected desktop kernel line; refusing to rewrite it")
        if image_destination.exists() or image_staging.exists():
            raise FileExistsError("Wi-Fi Image or staging file already exists")
        updated = prefix + "LABEL ubuntu-xfce\n" + section.replace(
            old_line, "    FDT /boot/" + new_dtb_name).replace(
            "    LINUX /boot/Image\n", "    LINUX /boot/Image.wifi-20261125\n") + separator + remaining
    destination = boot / "boot" / new_dtb_name
    staged_dtb = destination.with_name(destination.name + ".staged")
    staged_config = config.with_name(config.name + "." + arguments.variant + ".staged")
    if any(path.exists() for path in (destination, staged_dtb, staged_config)):
        raise FileExistsError("Candidate or staging name exists; inspect it instead of overwriting")
    print("Verified USB identity, FAT mount, candidate hash and desktop-only FDT replacement")
    if not arguments.apply:
        print("Dry run; no writes performed")
        return
    if os.geteuid() != 0:
        raise PermissionError("Apply requires root")
    if arguments.image:
        release = "7.3.6-w600d-usb-wifi"
        module = Path("/lib/modules") / release / \
            "kernel/drivers/net/wireless/mediatek/mt76/mt7663s/mt7663s.ko"
        if output("modinfo", "-F", "vermagic", str(module)).split()[0] != release:
            raise ValueError("Matching Wi-Fi modules must be installed before changing boot")
        for filename, expected in {
            "mt7663_n9_v3.bin": "d8b8488f37f65e41ded9a911950afb000d236b36e5aa94ad9650ad0c3a86fd45",
            "mt7663pr2h.bin": "534f2152f9b0f48dfcec9c1727b0bab9a3727a655d76d5ec818cc39a55602336",
        }.items():
            if digest(Path("/lib/firmware/mediatek") / filename) != expected:
                raise ValueError("Matching MediaTek firmware must be installed before changing boot")
    backup = Path("/root/w600d-debug-backups") / (
        datetime.now().strftime("%Y%m%dT%H%M%S-") + arguments.variant)
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(config, backup / "extlinux.conf")
    shutil.copy2(boot / "boot" / old_dtb_name, backup / "original.dtb")
    (backup / "update.json").write_text(json.dumps({
        "usb": identity[0], "candidate_sha256": arguments.sha256,
        "original_dtb_sha256": digest(backup / "original.dtb"),
        "original_config_sha256": digest(backup / "extlinux.conf"),
        "candidate_image_sha256": arguments.image_sha256,
    }, indent=2) + "\n")
    subprocess.run(["mount", "-o", "remount,rw", str(boot)], check=True)
    try:
        if arguments.image:
            with image_staging.open("xb") as target, arguments.image.open("rb") as source:
                shutil.copyfileobj(source, target)
                target.flush()
                os.fsync(target.fileno())
            if digest(image_staging) != arguments.image_sha256:
                raise ValueError("Staged kernel Image checksum differs")
            os.replace(image_staging, image_destination)
        with staged_dtb.open("xb") as target, arguments.candidate.open("rb") as source:
            shutil.copyfileobj(source, target)
            target.flush()
            os.fsync(target.fileno())
        if digest(staged_dtb) != arguments.sha256:
            raise ValueError("Staged DTB checksum differs")
        with staged_config.open("x") as target:
            target.write(updated)
            target.flush()
            os.fsync(target.fileno())
        os.replace(staged_dtb, destination)
        os.replace(staged_config, config)
        os.sync()
    finally:
        subprocess.run(["mount", "-o", "remount,ro", str(boot)], check=True)
    if arguments.normalize_container_markers:
        for relative in (".dockerenv", "run/.containerenv", "run/systemd/container"):
            marker = Path("/") / relative
            if marker.is_file() and not marker.is_symlink():
                shutil.copy2(marker, backup / relative.replace("/", "-"))
                marker.unlink()
        os.sync()
    print(f"Installed {destination}; boot remounted read-only; rollback files: {backup}")
    print("Original DTB/Image, rescue entries and Android/eMMC are retained; reboot to test")


if __name__ == "__main__":
    main()
