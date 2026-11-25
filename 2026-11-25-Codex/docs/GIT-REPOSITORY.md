# Source-only Git repository and GitHub publication

Git root: `/Users/k/zte-book`; initial branch: main. The dated directory stays
inside the repository so future dated work can be added without moving sources.
The commit author is taken from the user's original U-Boot effort:
Wang Kang <scateu@gmail.com>. Identity/hook configuration is repository-local.
No GitHub repository was created and no remote push was performed by setup.

## References are real submodules

- bootloader/usb-uboot pins c6283107a754a2baeb48843c11dc0640a77a0444
  from scateu/u-boot-zte-w600d-se.
- build/linux-7.3.6/reference/cloudbook-air-mainline-linux pins
  3a031bd9fd3d6c79d9ad0444af5088d0c21d4a43 from eastwoodnet's comparison project.

The original nested histories and working files were preserved, not deleted
or reset. Git uploads the submodule commit IDs, not their prebuilt binaries.
The CloudBook's existing symlink-to-text local change is preserved as
build/linux-7.3.6/reference-overrides/cloudbook-local.patch. After a recursive
clone, tools/setup-references.sh applies that exact override and creates
usb-uboot/patches -> patches_for_upstream. It is idempotent and checks both pins.

Submodule ignore=dirty keeps intentional working-tree overrides and generated
files from making parent status noisy. A changed reference HEAD still appears.
Inspect git -C SUBMODULE_PATH status --short directly before updating a pin;
new submodule commits must be published in their own upstream repository first.
Do not run reset/clean/update forcibly against the original local references.

## Ignored versus retained

Root .gitignore excludes compiled Images/DTBs/U-Boot/scripts, System.map,
modules/objects, raw and compressed images/backups, BMPs, downloads, output
directories, serial logs, caches and obvious credential/private-device dumps.
These files remain on disk; ignore is not deletion. Hardware description DTS,
patches, kernel config, small records and authored guides remain tracked.
The external U-Boot repository retains required large generated C source data.

Git cannot express a file-size limit in .gitignore. The tracked pre-commit hook
checks staged blob sizes and refuses ordinary files over 1 MiB. Setup enables
it locally using git config core.hooksPath .githooks; enable it after cloning too.
The full snapshot SHA256 verifier covers ignored backups/artifacts and cannot
verify a source-only clone until those local files have been independently restored.

## First push

Create an empty GitHub repository, choose its visibility after reviewing the
research notes, and do not initialize it with a separate README/license commit.
Then, from the repository root, substitute its actual SSH or HTTPS URL:

```sh
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Nothing is published until that explicit push. Preserve licensing notices
of reference sources; no new blanket project license was chosen here.
Fresh users should clone with --recurse-submodules, run the reference setup,
and follow BUILD-CURRENT.md. Private machine backups are not supplied by GitHub.
