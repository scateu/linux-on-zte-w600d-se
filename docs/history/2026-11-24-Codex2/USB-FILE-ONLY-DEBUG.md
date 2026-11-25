# USB debugging: kernel-only update, 2026-11-24

The user explicitly prefers related-file updates over repeated 32 GB
flashes. Linux was cleanly powered down via `sync; systemctl poweroff`;
serial confirmed all filesystems detached and `reboot: Power down`.
The USB can then be moved to build host `trash` for this update.

## Corrected kernel

Built with `JOBS=24 bash scripts/build-display-fix.sh` on `trash`.
It supplies lane counts in Analogix rate and voltage configuration,
fixing the observed Naneng PHY `-EINVAL` before PLL/link training.
Both exact patch application and repeated idempotent application pass.
Board and built-in kernel-option validators pass.

```text
artifacts/kernel-edp-lanes-fix/Image
0b0c71f33eed1057e9857e65ff60b9fecb248d7ed394408af4c240fb64c8638d

artifacts/kernel-edp-lanes-fix/rk3568-zte-w600d-mainline.dtb
4e7156892cfaa29da5d73b217d6e846c01af9b6e6d449323192463dc551e942d

artifacts/kernel-edp-lanes-fix/config-7.3.6-w600d-usb
13a567071ccd42b1dab2baa32cc58e7f9471f1ec19a19969b5e9fbdfc9bd597a
```

DTB and configuration hashes exactly match the first USB release. The
Analogix driver is built-in; kernel release remains 7.3.6-w600d-usb.
Thus the immediate update changes **only FAT `/boot/Image`**, not the
DTB, extlinux, partition table, ext4 root or matching module installation.
Original source artifacts and full images remain preserved on the server.
The original full-image checksum no longer describes a file-updated USB.

## Guarded updater

```sh
cd /home/k/codex-workdir-nov-24-2026
bash scripts/build-native-mtools.sh
python3 scripts/update-usb-kernel-files.py \
  artifacts/kernel-edp-lanes-fix/Image /dev/sdb \
  --expected-sha256 0b0c71f33eed1057e9857e65ff60b9fecb248d7ed394408af4c240fb64c8638d \
  --confirm-update /dev/sdb:E0D55E625BE9F440F84702D0
```

The updater refuses other devices, wrong partition UUIDs/labels/sizes,
mounted filesystems, changed disk identity and wrong source hash. Only
the authorized USB **boot partition** is passed to a networkless,
read-only-root, all-capabilities-dropped native Docker container. No
SYS_ADMIN, privileged mode, host root mount, `/dev/sda` or ext4 partition
is exposed. Docker access remains root-equivalent in general; this
specific invocation is deliberately partition-scoped.

Native mtools are copied from the build host with its matching glibc,
loader and gconv character-set modules into an approximately 11.6 MB build
context for a scratch image; no ARM emulation or package download. The
gconv modules are required for FAT codepage conversion, even for a test
with ASCII filenames.
It stages the corrected Image, syncs, renames the original to
`/boot/Image.pre-lanes-20261124`, activates the staged Image, and syncs.
Existing staged/rollback names cause refusal rather than destructive retry.
If activation fails while the USB remains connected, it attempts rollback.
Do not unplug during staging or either rename. A power failure between
renames may require restoring the retained old Image name before boot.

Only directory metadata is inspected after writing. No full-disk or
kernel-content read-back is performed, respecting the earlier request
to skip read-back. Source checksum and file sizes are not proof that
the physical media's contents have been hashed or that display works.

## Next acceptance test

After the updater succeeds and USB I/O is idle, return it to the powered-off
laptop. Keep only the existing serial logger connected, then power on.
Check that PHY configuration and eDP link training no longer fail, ask
for physical screen observation, and capture real event0 keyboard presses.
Neither display nor keyboard success is claimed before that test.

## Validated checkpoint, about 17:17 +08:00

- Kernel build, board validation and built-in-option validation pass.
- Patch applies with zero fuzz and repeated application is safely detected.
- Python updater compiles and shell scripts pass syntax checks.
- On an 8 MB regular FAT test image, the native tool container successfully
  copies/stages, retains the original by rename, activates the replacement,
  lists both files, and a test-file content comparison passes. The regular
  file test runs as its owning UID, not with DAC-override capabilities.
- The physical updater runs as root for the root-owned passed-in device
  node, still with all capabilities dropped; no host mount privilege.
- Separate fresh Ubuntu userspace build passed and its package versions
  match the flashed release; no additional rootfs rewrite is needed.
- `trash` still has only its internal Samsung `/dev/sda`, no returned USB.
  Never substitute that disk. Wait for the authorized Kingston to appear.

Status: corrected kernel and safe updater ready; **USB file update not yet
performed**, display not yet retested, physical keyboard events not yet
confirmed on this kernel. Linux laptop is cleanly powered down.
