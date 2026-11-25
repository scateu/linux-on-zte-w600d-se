#!/usr/bin/env python3
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
BACKUPS = ROOT / "recovery/factory-backups"


def main():
    parser = argparse.ArgumentParser(description="Restore verified raw backups; never flash a device")
    parser.add_argument("destination", type=Path)
    parser.add_argument("--only", help="One backup relative to recovery/factory-backups, e.g. w600d-backup/logo.img")
    arguments = parser.parse_args()
    destination = arguments.destination.resolve()
    if destination.is_relative_to(ROOT):
        parser.error("Extract outside the consolidated tree so raw duplicates are not reintroduced")
    report = json.loads((ROOT / "manifests/CLEANUP-REPORT.json").read_text())
    entries = report["compressed_backups"]
    if arguments.only:
        selected = "recovery/factory-backups/" + arguments.only
        entries = [entry for entry in entries if entry["original"] == selected]
        if not entries:
            parser.error(f"No recorded raw backup named {arguments.only}")
    planned = []
    for entry in entries:
        relative = Path(entry["original"]).relative_to("recovery/factory-backups")
        output = destination / relative
        if output.exists() or output.is_symlink() or output.with_name(output.name + ".partial").exists():
            raise FileExistsError(output)
        planned.append((entry, output))
    for entry, output in planned:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(output.name + ".partial")
        checksum = hashlib.sha256()
        size = 0
        with gzip.open(ROOT / entry["compressed"], "rb") as source, temporary.open("xb") as stream:
            for chunk in iter(lambda: source.read(1048576), b""):
                checksum.update(chunk)
                size += len(chunk)
                stream.write(chunk)
        if checksum.hexdigest() != entry["original_sha256"] or size != entry["original_bytes"]:
            raise ValueError(f"Restored backup failed verification: {temporary}")
        temporary.rename(output)
        print(f"Verified {output}")
    if not arguments.only:
        for checksum_file in BACKUPS.rglob("SHA256SUMS"):
            if checksum_file.is_file():
                output = destination / checksum_file.relative_to(BACKUPS)
                if not output.exists():
                    output.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(checksum_file, output)


if __name__ == "__main__":
    main()
