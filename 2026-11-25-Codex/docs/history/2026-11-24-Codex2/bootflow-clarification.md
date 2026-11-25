# Bootflow clarification — November 24, 2026

## Short answer

There are two full U-Boot binaries available, but the latest captured boot
executed only the eMMC vendor U-Boot. It loaded Linux directly from USB using
extlinux. The USB mainline U-Boot and its chain-loader were not executed.

Reading the kernel from USB is not the same as running the USB U-Boot.

## Latest confirmed path

```text
Rockchip BootROM
  -> eMMC idbloader/SPL
  -> ARM Trusted Firmware / vendor firmware stages
  -> eMMC vendor U-Boot 2017.09 (May 29, 2024 build; previously patched USB-first)
  -> USB device 0, FAT partition 1: /extlinux/extlinux.conf
  -> default entry w600d
  -> USB /boot/Image + /boot/rk3568-laptop-zte-edp-20261124.dtb
  -> Linux, USB partition 2 rootfs (PARTUUID=12345678-02)
  -> /bin/sh as PID 1 (init=/bin/sh)
```

The controlled reboot at 12:21:07 +08:00 is recorded in
`logs/serial-20261124T120921-403566+0800.jsonl`. It shows the vendor U-Boot
banner, USB extlinux discovery, retrieval of the kernel and new DTB, and
`Starting kernel`. There is no second full U-Boot banner or retrieval of the
USB U-Boot/chain-loader binaries in this boot. See also
`persistent-boot-test.md`, section "Controlled reboot and automatic boot path".

The SPL banner describes an earlier boot stage; it is not evidence that the
USB mainline U-Boot ran.

## Your earlier two-U-Boot chain-loading path

```text
BootROM -> eMMC SPL/firmware -> eMMC vendor U-Boot
  -> USB FAT partition 1: /boot.scr
  -> load u-boot-w600d.bin at 0x00800000
  -> load w600d-chain.bin at 0x10000000
  -> usb stop; go 0x10000000
  -> chain shim cleans/disables caches and MMU, then jumps to 0x00800000
  -> USB mainline U-Boot 2027.01-rc1
  -> its display/keyboard shell or subsequent boot commands
```

The original chain is documented in
`../ref/u-boot-zte-w600d-se/_RESEARCH/docs/HOWTO-uboot-shell.md` and its commands
are in `../ref/u-boot-zte-w600d-se/_RESEARCH/assets/uboot/chain/boot.cmd`.

With the current USB contents, the vendor scan successfully selects extlinux
and boots Linux without reaching that chain-loader script. The captured log
establishes which route ran; it does not by itself prove every detail of the
vendor's script-versus-extlinux search order.

## What this session changed

- Added the display-enabled Linux DTB and selected it in USB extlinux.
- Added an original-DTB rollback entry and a manual framebuffer test script.
- Did not change or remove the USB U-Boot, chain-loader, or boot scripts.
- Did not flash eMMC or issue saveenv. The USB-first vendor patch predates this
  session. Vendor firmware does update its own retry metadata during boot;
  this is documented separately in `persistent-boot-test.md`.

The white-screen result is a Linux framebuffer test, not a USB U-Boot test.
No reboot, serial command, USB change, or eMMC change was performed to prepare
this clarification; only this host-side Markdown document was added.
