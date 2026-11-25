#!/usr/bin/env python3
import subprocess
import sys


LIMIT = 1048576


def main():
    records = subprocess.check_output(["git", "ls-files", "--stage", "-z"])
    entries = []
    for record in records.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, object_id, stage = metadata.split()
        if mode == b"160000":
            continue
        entries.append((object_id, path.decode("utf-8", "surrogateescape")))
    if not entries:
        return
    sizes = subprocess.check_output(
        ["git", "cat-file", "--batch-check=%(objectsize)"],
        input=b"".join(object_id + b"\n" for object_id, path in entries),
    ).splitlines()
    oversized = [(path, int(size)) for (object_id, path), size in zip(entries, sizes)
                 if int(size) > LIMIT]
    if oversized:
        for path, size in oversized:
            print(f"Refusing large staged file ({size} bytes): {path}", file=sys.stderr)
        raise SystemExit("Keep files larger than 1 MiB outside Git; use release assets or external storage.")
    print(f"Checked {len(entries)} staged files: none exceeds 1 MiB.")


if __name__ == "__main__":
    main()
