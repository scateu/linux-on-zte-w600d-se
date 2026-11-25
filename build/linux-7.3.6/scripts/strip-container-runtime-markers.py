#!/usr/bin/env python3
import argparse
from pathlib import Path
import tarfile


MARKERS = {".dockerenv", "run/.containerenv", "run/systemd/container"}


def normalized_name(name):
    while name.startswith("./"):
        name = name[2:]
    return name.rstrip("/")


def main():
    parser = argparse.ArgumentParser(description="Remove container runtime markers from an exported hardware rootfs tar")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    source = arguments.source.resolve(strict=True)
    destination = arguments.destination.absolute()
    if not source.is_file() or destination.exists():
        raise SystemExit("Expected an existing input tar and a new output path")
    removed = []
    with source.open("rb") as input_file, destination.open("xb") as output_file:
        with tarfile.open(fileobj=input_file, mode="r|") as input_tar:
            with tarfile.open(fileobj=output_file, mode="w|", format=tarfile.PAX_FORMAT) as output_tar:
                for member in input_tar:
                    name = normalized_name(member.name)
                    if name in MARKERS:
                        removed.append(name)
                        continue
                    content = input_tar.extractfile(member) if member.isfile() else None
                    output_tar.addfile(member, content)
                    if content is not None:
                        content.close()
    with tarfile.open(destination, mode="r|") as output_tar:
        if any(normalized_name(member.name) in MARKERS for member in output_tar):
            raise SystemExit("Container marker remains in output tar")
    print("Container markers removed: " + (", ".join(removed) or "none present"))
    print("Other file metadata, numeric ownership, modes and link targets preserved")


if __name__ == "__main__":
    main()
