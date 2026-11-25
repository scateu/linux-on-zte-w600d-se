#!/usr/bin/env python3
import argparse
from collections import defaultdict
from datetime import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "manifests"
CHECKSUMS = MANIFESTS / "SHA256SUMS"


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def inventory():
    regular = []
    aliases = []
    for parent, directories, filenames in os.walk(ROOT, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in (".git", "__pycache__"))
        for name in sorted(directories + filenames):
            path = Path(parent) / name
            if path.is_symlink():
                target = path.resolve(strict=True)
                if not target.is_relative_to(ROOT):
                    raise ValueError(f"Alias escapes consolidated tree: {path}")
                aliases.append({"path": path.relative_to(ROOT).as_posix(),
                                "target": os.readlink(path)})
            elif path.is_file() and path != CHECKSUMS:
                regular.append(path)
    return sorted(regular), sorted(aliases, key=lambda entry: entry["path"])


def generate():
    report = json.loads((MANIFESTS / "CLEANUP-REPORT.json").read_text())
    if report["state"] != "complete":
        raise ValueError("Cleanup is not complete; consult CLEANUP-REPORT.json")
    origins = defaultdict(set)
    for entry in json.loads((MANIFESTS / "pre-cleanup/FILES.json").read_text()):
        origins[entry["sha256"]].add(entry["path"])
    previous = json.loads((MANIFESTS / "pre-cleanup/SOURCE-MAP.json").read_text())
    for entry in previous["sources"]:
        origins[entry["source_sha256"]].add(entry["source"])
    compressed = {entry["compressed"]: entry for entry in report["compressed_backups"]}
    regular, aliases = inventory()
    (MANIFESTS / "ALIASES.json").write_text(json.dumps(aliases, indent=2) + "\n")
    sources = []
    for path in regular:
        relative = path.relative_to(ROOT).as_posix()
        if relative in ("manifests/SOURCE-MAP.json", "manifests/ALIASES.json"):
            continue
        checksum = digest(path)
        entry = {"path": relative, "sha256": checksum, "bytes": path.stat().st_size,
                 "original_sources": sorted(origins[checksum])}
        if relative in compressed:
            raw = compressed[relative]
            entry["raw_sha256"] = raw["original_sha256"]
            entry["raw_bytes"] = raw["original_bytes"]
            entry["original_sources"] = sorted(origins[raw["original_sha256"]])
        sources.append(entry)
    (MANIFESTS / "SOURCE-MAP.json").write_text(json.dumps({
        "consolidated_at": datetime.now().astimezone().isoformat(),
        "provenance": "pre-cleanup/FILES.json, pre-cleanup/SOURCE-MAP.json and CLEANUP-REPORT.json",
        "sources": sources,
    }, indent=2) + "\n")
    regular, aliases = inventory()
    CHECKSUMS.write_text("".join(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n"
                                 for path in regular))
    print(f"Recorded {len(regular)} regular files and {len(aliases)} relative aliases.")


def verify_gzip(report):
    verified = {}
    for entry in report["compressed_backups"]:
        path = ROOT / entry["compressed"]
        if digest(path) != entry["compressed_sha256"]:
            raise ValueError(f"Compressed backup changed: {path}")
        key = path.resolve()
        if key not in verified:
            checksum = hashlib.sha256()
            size = 0
            with gzip.open(path, "rb") as stream:
                for chunk in iter(lambda: stream.read(1048576), b""):
                    checksum.update(chunk)
                    size += len(chunk)
            verified[key] = (checksum.hexdigest(), size)
        if verified[key] != (entry["original_sha256"], entry["original_bytes"]):
            raise ValueError(f"Raw backup recovery verification failed: {path}")
    print(f"Verified lossless recovery of {len(report['compressed_backups'])} raw backups.")


def verify_repositories(report):
    environment = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    for relative, expected in report["repositories"].items():
        repo = ROOT / relative
        for key, arguments in (
            ("head", ("rev-parse", "HEAD")),
            ("origin", ("remote", "get-url", "origin")),
            ("tracked_status", ("status", "--porcelain", "--untracked-files=no")),
        ):
            actual = subprocess.check_output(["git", "-C", str(repo), *arguments],
                                             env=environment, text=True).rstrip("\n")
            if actual != expected[key]:
                raise ValueError(f"Repository {key} changed: {relative}")
    print("Both Git HEADs, origins and pre-existing tracked changes are preserved.")


def verify_large_duplicates(regular):
    groups = defaultdict(set)
    sizes = defaultdict(list)
    for path in regular:
        status = path.stat()
        if status.st_size >= 65536:
            sizes[status.st_size].append(path)
    for size, candidates in sizes.items():
        if len(candidates) < 2:
            continue
        for path in candidates:
            status = path.stat()
            groups[(size, digest(path))].add((status.st_dev, status.st_ino))
    if any(len(inodes) > 1 for inodes in groups.values()):
        raise ValueError("Independent-storage duplicate files >=64 KiB remain")
    print("No independent-storage large-file duplicates remain outside .git.")


def verify():
    regular, aliases = inventory()
    expected_paths = set()
    for line in CHECKSUMS.read_text().splitlines():
        expected, relative = line.split("  ", 1)
        path = ROOT / relative
        if digest(path) != expected:
            raise ValueError(f"Checksum mismatch: {relative}")
        expected_paths.add(relative)
    actual_paths = {path.relative_to(ROOT).as_posix() for path in regular}
    if actual_paths != expected_paths:
        raise ValueError(f"Manifest file inventory changed: {actual_paths ^ expected_paths}")
    if aliases != json.loads((MANIFESTS / "ALIASES.json").read_text()):
        raise ValueError("Relative alias inventory changed")
    report = json.loads((MANIFESTS / "CLEANUP-REPORT.json").read_text())
    if report["state"] != "complete":
        raise ValueError("Cleanup report is not complete")
    verify_gzip(report)
    verify_repositories(report)
    verify_large_duplicates(regular)
    print(f"Verified {len(regular)} checksums and {len(aliases)} aliases; no physical drive read.")


def main():
    parser = argparse.ArgumentParser(description="Manifest or verify the consolidated research tree")
    parser.add_argument("action", choices=("manifest", "verify"))
    arguments = parser.parse_args()
    {"manifest": generate, "verify": verify}[arguments.action]()


if __name__ == "__main__":
    main()
