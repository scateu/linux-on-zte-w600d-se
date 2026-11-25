#!/usr/bin/env python3
from collections import defaultdict
from datetime import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
RECIPE = ROOT / "build/linux-7.3.6"
REPORT_PATH = ROOT / "manifests/CLEANUP-REPORT.json"
REPORT = {"state": "in_progress", "operations": [], "compressed_backups": []}
UBOOT = ROOT / "bootloader/usb-uboot"
CLOUDBOOK = RECIPE / "reference/cloudbook-air-mainline-linux"
BACKUPS = ROOT / "recovery/factory-backups"
REPOSITORIES = (UBOOT, CLOUDBOOK)


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def files(folder):
    for parent, directories, filenames in os.walk(folder, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in (".git", "__pycache__"))
        for name in sorted(filenames):
            path = Path(parent) / name
            if path.is_file() and not path.is_symlink():
                yield path


def record(action, source, destination=None, **details):
    entry = {"action": action, "source": source.relative_to(WORKSPACE).as_posix(), **details}
    if destination is not None:
        entry["destination"] = destination.relative_to(WORKSPACE).as_posix()
    REPORT["operations"].append(entry)
    REPORT_PATH.write_text(json.dumps(REPORT, indent=2) + "\n")


def move(source, destination):
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    record("move", source, destination)


def remove(path, reason, canonical=None):
    checksum = digest(path)
    if canonical is not None and checksum != digest(canonical):
        raise ValueError(f"Not an exact duplicate: {path}")
    record("remove", path, canonical, sha256=checksum, bytes=path.stat().st_size, reason=reason)
    path.unlink()


def transfer(source, destination):
    if destination.exists():
        if digest(source) == digest(destination):
            remove(source, "Exact duplicate of retained file", destination)
            return
        destination = destination.with_name(destination.name + ".retained-" + digest(source)[:12])
    move(source, destination)


def empty_tree(folder):
    for parent, directories, filenames in os.walk(folder, topdown=False):
        if filenames:
            raise ValueError(f"Unexpected remaining files: {parent}")
        Path(parent).rmdir()
    record("remove-empty-directory", folder)


def alias(path, canonical):
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(os.path.relpath(canonical, path.parent), target_is_directory=canonical.is_dir())
    record("alias", path, canonical)


def duplicate_tree(duplicate, canonical):
    for path in list(files(duplicate)):
        counterpart = canonical / path.relative_to(duplicate)
        if counterpart.is_file() and digest(path) == digest(counterpart):
            remove(path, "Exact duplicate reference", counterpart)
        else:
            transfer(path, ROOT / "reference/retained-deltas" / duplicate.name / path.relative_to(duplicate))
    empty_tree(duplicate)
    alias(duplicate, canonical)


def old_notes(folder, label):
    for path in list(files(folder)):
        relative = path.relative_to(folder)
        if "logs" in relative.parts:
            tail = Path(*relative.parts[relative.parts.index("logs") + 1:])
            transfer(path, ROOT / "logs" / label / tail)
        elif path.suffix == ".md":
            transfer(path, ROOT / "docs/history" / label / relative)
        elif "linux-7.3.6-build" in relative.parts:
            tail = Path(*relative.parts[relative.parts.index("linux-7.3.6-build") + 1:])
            canonical = RECIPE / tail
            if canonical.is_file() and digest(path) == digest(canonical):
                remove(path, "Exact duplicate current recipe", canonical)
            elif path.suffix in (".patch", ".dts", ".dtb", ".conf", ".base64"):
                transfer(path, ROOT / "reference/legacy-display" / label / relative)
            else:
                remove(path, "Superseded recipe helper; current recipe retained")
        elif path.name in ("serial_console.py", "dtb_inventory.py"):
            transfer(path, ROOT / "tools" / path.name)
        elif path.suffix in (".py", ".sh"):
            transfer(path, ROOT / "tools/legacy-display-tests" / label / relative)
        else:
            transfer(path, ROOT / "reference/legacy-display" / label / relative)
    empty_tree(folder)


def git_state(folder):
    environment = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    def git(*arguments):
        return subprocess.check_output(
            ["git", "-C", str(folder), *arguments], env=environment, text=True
        ).rstrip("\n")
    return {
        "head": git("rev-parse", "HEAD"),
        "origin": git("remote", "get-url", "origin"),
        "tracked_status": git("status", "--porcelain", "--untracked-files=no"),
    }


def allocated_bytes(folder):
    inodes = set()
    total = 0
    for parent, directories, filenames in os.walk(folder, followlinks=False):
        for name in filenames:
            path = Path(parent) / name
            if path.is_symlink() or not path.is_file():
                continue
            status = path.stat()
            identity = (status.st_dev, status.st_ino)
            if identity not in inodes:
                inodes.add(identity)
                total += status.st_blocks * 512
    return total


def verify_checksums(folder, checksum_file):
    for line in checksum_file.read_text().splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(None, 1)
        relative = relative.lstrip(" *")
        if digest(folder / relative) != expected:
            raise ValueError(f"Checksum mismatch: {folder / relative}")


def compress_backups():
    canonical = {}
    for path in list(files(BACKUPS)):
        if path.suffix not in (".img", ".bin"):
            continue
        checksum = digest(path)
        size = path.stat().st_size
        compressed = path.with_name(path.name + ".gz")
        if compressed.exists() or compressed.is_symlink():
            raise FileExistsError(compressed)
        key = (size, checksum)
        if key in canonical:
            alias(compressed, canonical[key])
        else:
            temporary = compressed.with_name(compressed.name + ".partial")
            with path.open("rb") as source, temporary.open("xb") as output:
                with gzip.GzipFile(filename="", mode="wb", fileobj=output,
                                   compresslevel=6, mtime=0) as stream:
                    shutil.copyfileobj(source, stream, 1048576)
            temporary.rename(compressed)
            canonical[key] = compressed
        restored_hash = hashlib.sha256()
        restored_size = 0
        with gzip.open(compressed, "rb") as stream:
            for chunk in iter(lambda: stream.read(1048576), b""):
                restored_hash.update(chunk)
                restored_size += len(chunk)
        if restored_hash.hexdigest() != checksum or restored_size != size:
            raise ValueError(f"Lossless compression verification failed: {path}")
        REPORT["compressed_backups"].append({
            "original": path.relative_to(ROOT).as_posix(),
            "compressed": compressed.relative_to(ROOT).as_posix(),
            "original_sha256": checksum,
            "original_bytes": size,
            "compressed_sha256": digest(compressed),
        })
        record("compress-and-remove-raw", path, compressed,
               sha256=checksum, bytes=size, verified_decompressed=True)
        path.unlink()
        print(f"Verified and compressed {path.relative_to(ROOT)}", flush=True)


def priority(path):
    if path.is_relative_to(RECIPE):
        category = 0
    elif path.is_relative_to(UBOOT):
        category = 1
    elif path.is_relative_to(BACKUPS):
        category = 2
    elif path.is_relative_to(ROOT / "artifacts"):
        category = 3
    else:
        category = 4
    return (category, len(path.parts), path.as_posix())


def deduplicate_large_files():
    sizes = defaultdict(list)
    for path in files(ROOT):
        if path.stat().st_size >= 65536:
            sizes[path.stat().st_size].append(path)
    for candidates in sizes.values():
        if len(candidates) < 2:
            continue
        groups = defaultdict(list)
        for path in candidates:
            groups[digest(path)].append(path)
        for checksum, group in groups.items():
            canonical, *duplicates = sorted(group, key=priority)
            for path in duplicates:
                if path.samefile(canonical):
                    continue
                if any(path.is_relative_to(repo) for repo in REPOSITORIES):
                    if (path.stat().st_mode & 0o777) != (canonical.stat().st_mode & 0o777):
                        raise ValueError(f"Duplicate Git file has different permissions: {path}")
                    temporary = path.with_name(path.name + ".dedup-link")
                    os.link(canonical, temporary)
                    temporary.replace(path)
                    record("hardlink", path, canonical, sha256=checksum,
                           reason="One physical copy; preserve Git file type and permissions")
                else:
                    remove(path, "Exact large-file duplicate; relative alias retained", canonical)
                    alias(path, canonical)


def validate_result():
    verify_checksums(ROOT / "artifacts/kernel-tested",
                     ROOT / "artifacts/kernel-tested/SHA256SUMS")
    for repo in REPOSITORIES:
        expected = REPORT["repositories"][repo.relative_to(ROOT).as_posix()]
        if git_state(repo) != expected:
            raise ValueError(f"Repository HEAD/origin/tracked changes were altered: {repo}")
    for parent, directories, filenames in os.walk(ROOT, followlinks=False):
        directories[:] = [name for name in directories if name != ".git"]
        for name in directories + filenames:
            path = Path(parent) / name
            if path.is_symlink():
                target = path.resolve(strict=True)
                if not target.is_relative_to(ROOT):
                    raise ValueError(f"Alias escapes consolidated tree: {path}")


def apply_cleanup():
    if sys.argv[1:] != ["--apply"]:
        raise SystemExit("Usage: cleanup-workspace.py --apply (one-time, destructive cleanup)")
    if REPORT_PATH.exists():
        raise FileExistsError("Cleanup already started; consult its report, do not rerun")
    original_uboot = WORKSPACE / "ref/u-boot-zte-w600d-se"
    original_cloudbook = WORKSPACE / "ref/eastwoodnet_cloudbook-air-mainline-linux"
    for path in (UBOOT, CLOUDBOOK, BACKUPS, ROOT / "manifests/pre-cleanup"):
        if path.exists() or path.is_symlink():
            raise FileExistsError(path)
    for path in (original_uboot, original_cloudbook, WORKSPACE / "ref/backups",
                 WORKSPACE / "2026-11-24-Codex", WORKSPACE / "2026-11-24-Codex2",
                 ROOT / "archive"):
        if not path.is_dir():
            raise FileNotFoundError(path)
    print("Checking original snapshot and recovery checksums...", flush=True)
    verify_checksums(ROOT, ROOT / "manifests/SHA256SUMS")
    for folder in (WORKSPACE / "ref/backups/w600d-backup",
                   WORKSPACE / "ref/backups/uboot-backup-20261106-v14"):
        verify_checksums(folder, folder / "SHA256SUMS")
    REPORT["started_at"] = datetime.now().astimezone().isoformat()
    REPORT["allocated_bytes_before"] = allocated_bytes(WORKSPACE)
    REPORT["repositories"] = {
        UBOOT.relative_to(ROOT).as_posix(): git_state(original_uboot),
        CLOUDBOOK.relative_to(ROOT).as_posix(): git_state(original_cloudbook),
    }
    inventory = [{"path": path.relative_to(WORKSPACE).as_posix(),
                  "sha256": digest(path), "bytes": path.stat().st_size}
                 for path in files(WORKSPACE)]
    previous = ROOT / "manifests/pre-cleanup"
    previous.mkdir(parents=True)
    (previous / "FILES.json").write_text(json.dumps(inventory, indent=2) + "\n")
    for name in ("SOURCE-MAP.json", "SHA256SUMS", "VALIDATION.md"):
        move(ROOT / "manifests" / name, previous / name)

    print("Moving both repositories and recovery backups...", flush=True)
    move(original_uboot, UBOOT)
    alias(UBOOT / "patches", UBOOT / "patches_for_upstream")
    move(original_cloudbook, CLOUDBOOK)
    duplicate_tree(RECIPE / "reference/cloudbook-mainline-6.12", CLOUDBOOK / "mainline-6.12")
    move(WORKSPACE / "ref/backups", BACKUPS)
    alias(BACKUPS / "original-backup-SHA256SUMS", BACKUPS / "w600d-backup/SHA256SUMS")
    duplicate_tree(ROOT / "reference/u-boot-research", UBOOT / "_RESEARCH")
    duplicate_tree(ROOT / "reference/factory-device-tree", BACKUPS)

    print("Consolidating authored notes, logs, and historical small inputs...", flush=True)
    for label in ("2026-11-24-Codex", "2026-11-24-Codex2"):
        old_notes(WORKSPACE / label, label)
        old_notes(ROOT / "archive" / label, label)
    old_notes(ROOT / "archive/trash", "trash")
    remove(ROOT / "archive/README.md", "Obsolete duplicate-archive index; consolidated index replaces it")
    empty_tree(ROOT / "archive")
    for label in ("2026-11-11", "2026-11-23"):
        move(WORKSPACE / "ref" / label, ROOT / "logs" / ("ref-" + label))
    transfer(WORKSPACE / "ref/notes-2026-11-10.txt", ROOT / "docs/history/early/notes-2026-11-10.txt")

    legacy_usb = ROOT / "reference/legacy-usb-Nov-24"
    move(WORKSPACE / "ref/usbdisk-Nov-24", legacy_usb)
    for relative in ("boot/Image", "boot/vmlinuz-6.18.45-current-arm64",
                     "boot/initrd-custom.img", "boot/initrd.img-6.18.45-current-arm64"):
        remove(legacy_usb / relative, "Superseded USB kernel/initrd; tested modern kernel and recipe retained")
    for path in list(files(WORKSPACE / "ref/research")):
        if path.name not in ("logo_w600d.img", "logo_w600d.img.bmp"):
            raise ValueError(f"Unexpected logo experiment: {path}")
        remove(path, "Rebuildable logo example; stock logo, generator and format analysis retained")
    empty_tree(WORKSPACE / "ref/research")
    empty_tree(WORKSPACE / "ref")
    experiments = BACKUPS / "uboot-patch-experiement"
    for path in list(files(experiments)):
        if path.name not in ("v13-usb-first.img", "v14-diag.img", "v15-usb-first-bd0.img"):
            raise ValueError(f"Unexpected patch experiment: {path}")
        remove(path, "Generated patch experiment; original backups, v15 patcher and prebuilt USB-first image retained")
    empty_tree(experiments)

    inactive_scripts = (
        "build-all.sh", "build-desktop-rootfs.sh", "build-kernel.sh", "build-ready-image.sh",
        "build-release.sh", "build-rootfs-v2.sh", "build-rootfs.sh", "build-userspace.sh",
        "build-verified-image.sh", "fetch-debian.py", "finalize-kernel.sh", "flash-usb.py",
        "package-release-recipe.sh",
    )
    for name in inactive_scripts:
        remove(RECIPE / "scripts" / name, "Superseded by the current display-fixed recipe")
    for name in ("Dockerfile", "Dockerfile.v2"):
        remove(RECIPE / "rootfs" / name, "Superseded by Dockerfile.v3 and Dockerfile.final")
    remove(ROOT / "tools/collect-snapshot.py", "One-time collector replaced by verify-workspace.py; origin map retained")
    compress_backups()
    deduplicate_large_files()
    validate_result()
    REPORT["state"] = "complete"
    REPORT["completed_at"] = datetime.now().astimezone().isoformat()
    REPORT["allocated_bytes_after_cleanup"] = allocated_bytes(WORKSPACE)
    REPORT_PATH.write_text(json.dumps(REPORT, indent=2) + "\n")
    print(f"Cleanup complete: {len(REPORT['operations'])} audited operations.", flush=True)


if __name__ == "__main__":
    try:
        apply_cleanup()
    except Exception as error:
        if REPORT_PATH.exists():
            REPORT["state"] = "stopped"
            REPORT["error"] = str(error)
            REPORT_PATH.write_text(json.dumps(REPORT, indent=2) + "\n")
        raise
