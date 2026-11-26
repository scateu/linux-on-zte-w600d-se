# Patch the factory boot sequence, once

The current laptop already has this patch. Do not reflash eMMC for kernel,
DTS, desktop or typewriter USB updates. This guide records how to prepare
another **matching factory machine** safely; cleanup itself performs no flash.
Run local commands from the repository root.

## What changes, and what does not

The tested v15 default bootcmd is:

```text
run bootcmd_usb0;run bootcmd_mmc0;usb stop;boot_fit;boot_android ${devtype} ${devnum};run distro_bootcmd;
```

USB is tried first, then eMMC scanning, then the original vendor Android
sequence when scans return. `usb stop` prevents the vendor Android path
inheriting active USB state. Keep the **flat sequence**: earlier top-level
if/fi variants reset this vendor build.

- Keep the factory bootdelay at **0**; v15 does not replace it.
- Clear bootcmd_pxe to free space in the fixed-size compiled environment.
- Only the U-Boot payload's default environment and its FIT SHA256 are patched.
- Patcher modifies FIT copy zero and leaves copy one at `0x200000` unchanged.
- Preserve SPL/DDR/ATF, the Android partitions, GPT, misc and the rescue slot.

The observed loader accepted an updated payload hash without enforcing the
now-stale FIT RSA signature. That observation is firmware-specific, **not** a
promise about another laptop's secure-boot policy.

## Back up that exact machine first

From a fresh Git checkout, run `git submodule update --init bootloader/usb-uboot`
to obtain the patcher and ADB helper.

1. Confirm model, firmware, by-name partitions, active A/B slot and rescue path.
2. Obtain its own stock uboot_a, uboot_b and misc; save sizes and SHA256SUMS.
   Keep early eMMC/GPT, boot resources and per-device factory backups too.
3. Keep the second FIT copy and the other usable bootloader slot stock.
4. Do not use our saved/prebuilt image as a universal factory image.

A stock B is not an unconditional fallback for a damaged or hung A. See
[W600D SE A/B boot retries](AB-BOOT-RETRIES.md) before changing any bootloader
partition or `misc`.

The preserved Android-root helper can dump the three essential partitions:

```sh
bash bootloader/usb-uboot/01_vendor-env_patch_uboot_a/w600d-uboot-a.sh \
  -s "$ADB_SERIAL" backup /path/to/that-machines-backup
```

Set ADB_SERIAL to the actual Android connection; the helper requires working
root access through su 0. Re-establish identity/root/slot state before use.
The compressed backups under recovery/ are historical copies from this laptop,
including a later v14 backup; a date-named backup is not necessarily pristine.

## Generate the patch offline

```sh
python3 -I bootloader/usb-uboot/01_vendor-env_patch_uboot_a/patch-uboot-env.py \
  /path/to/that-machines-backup/uboot_a.img \
  /path/to/that-machines-backup/uboot_a-usbfirst.img
```

Omitting VAR=VALUE overrides selects the established v15 defaults.
The patcher checks the sampled image layout, original payload hash, existing
variable names and environment capacity, and regenerates the FIT payload hash.
**Stop on any assertion or mismatch.** Do not bypass checks, force another
firmware layout into this script, or replace the factory loader with a generic
U-Boot image. Review changed offsets/bytes and verify the rescue copy remains
identical before considering any write.

## Installation is a separate, explicit decision

After identity, backup, offline verification and recovery readiness are
established, the original helper's flash subcommand writes **uboot_a only** and
asks for confirmation. Do not set YES=1 to bypass its prompts:

```sh
bash bootloader/usb-uboot/01_vendor-env_patch_uboot_a/w600d-uboot-a.sh \
  -s "$ADB_SERIAL" flash /path/to/that-machines-backup/uboot_a-usbfirst.img
```

After read-back verification the helper uses `bootctl` to make A a trial slot,
which **does** update `misc`. Boot Android without the USB and verify the
running slot is `_a` and A is marked successful before repeated USB boots:

```sh
adb -s "$ADB_SERIAL" shell getprop ro.boot.slot_suffix
adb -s "$ADB_SERIAL" shell 'su 0 sh -c "bootctl is-slot-marked-successful 0"'
```

Stop if either check fails. Review
`../bootloader/usb-uboot/_RESEARCH/docs/HOWTO-patch-uboot.md` and
`HOWTO-uboot-shell.md` before following that device-specific write procedure.
No write command needs to run merely to use this consolidated workspace.

Then choose one removable USB workflow:

- **Linux:** factory U-Boot -> extlinux -> Image/DTB -> Ubuntu. No USB U-Boot.
- **Typewriter:** factory U-Boot -> vendor boot.scr -> RAM shim -> USB U-Boot.

Power off before swapping sticks. Without USB, the configured command falls
through toward original Android, but the final physical unplugged-Android
acceptance test is still outstanding. A bad kernel/RAM handoff cannot return
to the old loader; recover by powering off and removing USB.
