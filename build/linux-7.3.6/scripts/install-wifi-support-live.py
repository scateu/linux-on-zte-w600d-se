#!/usr/bin/env python3
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile


RELEASE = "7.3.6-w600d-usb-wifi"
FIRMWARE = {
    "mediatek/mt7663_n9_v3.bin": "d8b8488f37f65e41ded9a911950afb000d236b36e5aa94ad9650ad0c3a86fd45",
    "mediatek/mt7663pr2h.bin": "534f2152f9b0f48dfcec9c1727b0bab9a3727a655d76d5ec818cc39a55602336",
    "LICENSES/LICENCE.mediatek": "a90d3f66704d85889945fec5525ea77622549da83aced1aac99828383f8f1805",
}


def output(*arguments):
    return subprocess.check_output(arguments, text=True).strip()


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Guarded USB-only matching Wi-Fi modules and firmware install")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--modules-sha256", required=True)
    parser.add_argument("--apply", action="store_true")
    arguments = parser.parse_args()
    root_device = output("findmnt", "-n", "-o", "SOURCE", "--target", "/")
    disk = (Path("/sys/class/block") / Path(root_device).name).resolve(strict=True).parent.name
    identity = json.loads(output("lsblk", "-J", "-d", "-b", "-o", "NAME,TRAN,SERIAL,SIZE",
                                 "/dev/" + disk))["blockdevices"]
    if len(identity) != 1 or identity[0]["tran"] != "usb" or \
            identity[0]["serial"] != "E0D55E625BE9F440F84702D0" or \
            identity[0]["size"] != 30943995904 or root_device != "/dev/" + disk + "2":
        raise ValueError("Unexpected USB root; refusing any write")
    destination = Path("/lib/modules") / RELEASE
    if destination.exists():
        raise FileExistsError("Matching module tree already exists; inspect it instead of overwriting")
    archive_path = arguments.bundle / ("modules-" + RELEASE + ".tar.gz")
    if digest(archive_path) != arguments.modules_sha256:
        raise ValueError("Module archive checksum differs")
    for relative, expected in FIRMWARE.items():
        if digest(arguments.bundle / relative) != expected:
            raise ValueError("Firmware or license checksum differs: " + relative)
    prefix = PurePosixPath("lib/modules") / RELEASE
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or \
                    not path.is_relative_to(prefix) or not (member.isfile() or member.isdir()) or \
                    member.mode & 0o7000:
                raise ValueError("Unsafe module archive member: " + member.name)
        if not any(member.name.endswith("/mt7663s/mt7663s.ko") for member in members):
            raise ValueError("Missing MediaTek Wi-Fi module")
        print("Verified USB identity, archive paths/types, module checksum and pinned firmware/license")
        if not arguments.apply:
            print("Dry run; no writes performed")
            return
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        staging = Path("/lib/modules") / (".w600d-wifi-staged-" + stamp)
        staging.mkdir(mode=0o700)
        archive.extractall(staging, members=members, filter="data")
        staged_modules = staging / prefix
        module = staged_modules / "kernel/drivers/net/wireless/mediatek/mt76/mt7663s/mt7663s.ko"
        if output("modinfo", "-F", "vermagic", str(module)).split()[0] != RELEASE:
            raise ValueError("Wi-Fi module vermagic differs")
        os.replace(staged_modules, destination)
        shutil.rmtree(staging)
    subprocess.run(["depmod", RELEASE], check=True)
    backup = Path("/root/w600d-debug-backups") / (stamp + "-wifi-support")
    backup.mkdir(parents=True)
    for relative in FIRMWARE:
        target = Path("/lib/firmware") / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        staged = target.with_name(target.name + ".w600d-staged")
        with staged.open("xb") as stream, (arguments.bundle / relative).open("rb") as source:
            shutil.copyfileobj(source, stream)
            stream.flush()
            os.fsync(stream.fileno())
        staged.chmod(0o644)
        os.replace(staged, target)
    (backup / "update.json").write_text(json.dumps({
        "usb": identity[0], "release": RELEASE,
        "modules_sha256": arguments.modules_sha256, "firmware": FIRMWARE,
    }, indent=2) + "\n")
    os.sync()
    print(f"Installed separate {RELEASE} modules and firmware; backups: {backup}")
    print("Old modules, boot entries and Android/eMMC remain unchanged; stage Image/DTB separately")


if __name__ == "__main__":
    main()
