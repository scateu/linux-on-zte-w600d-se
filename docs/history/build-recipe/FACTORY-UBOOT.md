# Factory U-Boot USB-first patch: scope and repeatability

The current laptop's patch is already installed. This document does not
authorize or perform another eMMC flash. A new factory machine must first
be confirmed as the same W600D SE board/firmware family and must have a
verified recovery route and permission to modify its bootloader.

## Keep the machine's own vendor bootloader

Patch only the built-in default environment of its original Rockchip FIT
vendor U-Boot. Preserve DDR/SPL, trusted firmware, Android boot partitions,
partition layout and the unmodified rescue U-Boot copy/slot. Never write an
unsigned mainline U-Boot into eMMC on the assumption that USB chain-loading
success implies secure-boot compatibility.

The established patch's flat bootcmd is:

```text
run bootcmd_usb0;run bootcmd_mmc0;usb stop;boot_fit;boot_android ${devtype} ${devnum};run distro_bootcmd;
```

This scans USB extlinux first, then the existing eMMC scan, then the stock
Android boot sequence. An absent USB or a returned scan falls through;
removing USB before power-on does not select an eMMC Linux install because
this project never installs Linux there. A present but failed Linux kernel
may hang after transfer of control; remove USB while powered off to recover.

Do not put a top-level `if ... fi` in bootcmd. Previous W600D experiments
found vendor Android boot resets with that form. Preserve the original
bootdelay (the established v15 patch keeps it at 0) and do not assume a
different factory firmware contains an identical environment layout.

## Per-machine backup and offline build

Before flashing, obtain and archive the **new machine's own** stock
`uboot_a`, `uboot_b`, misc/A-B metadata and partition information using the
previous project's read-only backup procedure. Record complete SHA-256,
size, board model, firmware/build banner and active/verified Android slot.
Do not use another laptop's raw backup as the source image.

On the build host, after copying the established environment patch tool:

```sh
python3 -I reference/patch-uboot-env.py \
  factory-machine-backup/uboot_a.img factory-machine-backup/uboot_a-usb-first.img
sha256sum factory-machine-backup/uboot_a*.img
```

The supplied tool expects two identical FIT copies, patches only the first,
and recalculates the U-Boot payload hash. The second FIT copy remains stock.
Its existing checks failing on a new image is a stop condition, not a reason
to remove the checks. It invalidates the original FIT signature; acceptance
was demonstrated on this firmware's SPL, not promised for every factory
variant or secure-boot configuration.

## Controlled installation and checks

Use the previously validated Android/root-assisted procedure only after
verifying partition identities, backup/recovery, and the current active slot.
The previous project's helper can alter A/B activation/retry state; do not
run it blindly on a new factory machine. Keep `uboot_b` stock as rescue.
Write only the confirmed vendor U-Boot partition, read it back and compare
the exact hash. Test original Android with USB absent, then this new USB.

Authoritative original research:

- `ref/u-boot-zte-w600d-se/_RESEARCH/docs/HOWTO-patch-uboot.md`
- `ref/u-boot-zte-w600d-se/_RESEARCH/docs/partitions.md`
- `ref/u-boot-zte-w600d-se/_RESEARCH/tools/patch-uboot-env.py`

Copies of the patch guide, partitions document and tool were placed in
the server workdir's `reference/` directory for offline reproduction.

Factory flashing is intentionally not combined with the USB build or USB
writer. This recipe's acceptance is the complete sequence: vendor USB-first
patch -> new USB Linux with display and keyboard -> shutdown/remove USB ->
original Android. Each stage must be observed on the intended machine.
