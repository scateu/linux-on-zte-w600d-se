# ZTE W600D SE removable Linux bring-up

Sources, board DTS, patches, build recipes and research for booting Ubuntu
from USB while preserving the laptop's original Android installation.
Start with [the consolidated index](2026-11-25-Codex/README.md) and
[the hardware checkpoint](2026-11-25-Codex/CURRENT.md).

## Clone and prepare

```sh
git clone --recurse-submodules YOUR_GITHUB_REPOSITORY_URL zte-book
cd zte-book
bash 2026-11-25-Codex/tools/setup-references.sh
git config core.hooksPath .githooks
```

The two original reference repositories are pinned submodules, not duplicate
embedded repositories. Their histories and existing files remain local;
this repository uploads their commit references rather than their binaries.
Setup recreates the vendor patch-directory alias and applies the preserved
CloudBook local text override without resetting either repository.

## What Git tracks

- Guides, research notes, authored DTS/DTSI, patches, configuration and scripts.
- Small build records, source/checksum provenance and cleanup audit.
- Pinned external reference commits and the patch needed for the local override.

Compiled kernels/DTBs/U-Boot/scripts, raw or compressed backups, disk images,
serial logs, downloads, output directories and caches are ignored. They are
not deleted. Necessary large font/Wubi sources remain in the U-Boot submodule.
The local pre-commit hook rejects ordinary staged files larger than **1 MiB**;
Git ignore patterns alone cannot filter arbitrary files by size.

The full-snapshot verifier includes ignored local backups and tested binaries.
It is useful for the complete original workspace, not a source-only GitHub clone.
A fresh clone must build its own kernel/rootfs and use its own device backups.

See [GitHub publication notes](2026-11-25-Codex/docs/GIT-REPOSITORY.md) for
initial push commands, local overrides and the ignored-file policy.
No complete desktop/trackpad/DHCP/Android-fallback acceptance is implied.
