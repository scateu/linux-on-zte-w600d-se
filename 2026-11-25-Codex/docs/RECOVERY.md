# Preserved recovery data and extraction

The cleanup did **not** discard unique raw factory/recovery backups. Each
.img/.bin in `../recovery/factory-backups/` was compressed losslessly, then
decompressed and checked against its original size and SHA256 **before** the
raw file was removed. All 21 original raw backup paths can be recovered.
Identical compressed copies use relative aliases; differing boot-slot and
bootloader snapshots remain distinct. Original DTS/DTB/BMP/metadata are readable.

These backups belong to this laptop. They are not a complete factory disk:
Android super and userdata are not included. Per-machine security, serial/MAC
and factory data must not be transplanted onto another laptop. The later
uboot-backup-20261106-v14 directory contains a genuine later snapshot, not
necessarily factory-stock bytes.

## Extract outside the workspace

From `2026-11-25-Codex/`, use a **new** destination:

```sh
python3 tools/extract-backups.py /tmp/w600d-restored
```

This restores all recorded raw backups, validates their hashes/sizes and
copies the original raw SHA256SUMS files. It never opens or writes a device.
For just one image:

```sh
python3 tools/extract-backups.py /tmp/w600d-logo \
  --only w600d-backup/logo.img
```

On Linux, after full extraction:

```sh
cd /tmp/w600d-restored/w600d-backup
sha256sum -c SHA256SUMS
```

Do **not** run an original raw SHA256SUMS file directly inside the compressed
backup directory: its filenames and hashes refer to the decompressed images.
Never flash .gz data directly. Extraction is not authorization to flash.
Review the model-specific historical debrick notes before any recovery write;
their IP addresses, disk letters and proposed Android erase layouts are not
current instructions.

## Cleanup policy and audit

- Both original repositories moved with their .git histories and pre-existing
  tracked changes intact; no reset, commit or branch creation occurred.
- Old date folders, duplicate archive copies and ref/ were consolidated and
  removed after transferring useful notes, logs, sources and recovery data.
- Removed: old USB kernels/initrds, generated logo example/preview, generated
  U-Boot patch experiments and superseded build wrappers/Dockerfiles.
- Current tested Image/DTB/config/System.map and all active recipe dependencies
  remain. Required generated typewriter font/Wubi C data remain too.
- Exact large duplicates (64 KiB and above) share one physical copy. External
  paths use relative symlinks; the duplicate Git-tracked U-Boot binary uses a
  hardlink to preserve its Git file type, permissions and clean tracked state.
- Git object stores were not deduplicated or rewritten. Do not overwrite a
  hardlinked tracked binary in place: build into out/ and replace files instead.

`../manifests/CLEANUP-REPORT.json` records all moves, removals, hashes, compressed
backup mappings and aliases. `pre-cleanup/` keeps the original file inventory,
snapshot origin map, checksums and validation record. The updated SOURCE-MAP
records retained-file provenance by original checksum; ALIASES.json records
current relative links. Histories in `../docs/history/` retain their original
wording, so their old paths/status/erase proposals may be obsolete.

To verify the consolidated tree, backup recovery, aliases and Git state:

```sh
python3 tools/verify-workspace.py verify
```

This reads local research files only, not USB/eMMC. After deliberate non-Git
file edits, regenerate `python3 tools/verify-workspace.py manifest`, then verify.
Git changes intentionally fail the preserved-checkpoint check until separately reviewed.
`cleanup-workspace.py --apply` is a one-time destructive helper and deliberately
refuses a second run; do not delete its audit report to bypass that guard.
