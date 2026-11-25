# ZTE W600D SE Linux bring-up — 2026-11-24

## Objective and current status

Bring up the internal display and keyboard while retaining the existing
Android installation and USB chain-boot workflow. The user reports that the
machine is powered off; no live hardware result has been collected yet.
See `memory.md` for the resume state, DTB discovery and snapshot hashes.
The first connection attempt was denied by this task's sandbox; keep the
machine powered off until localhost access is available and logging is connected.

Work plan:

1. Capture an unchanged cold boot and inspect the running kernel/device tree.
2. Verify keyboard events independently of display and console routing.
3. Diagnose eDP driver binding, PHY, panel, power and VOP routing; test reversible
   changes first, and preserve working USB boot files before any replacements.

## Safety boundaries

- No writes to eMMC, its boot areas, GPT, `misc`, `uboot_*`, `trust_*`, or Android
  partitions. Do not run flash/install scripts from either reference project.
- Do not use `saveenv`, change slot metadata, reboot or power-cycle without
  coordinating with the user. Prefer observation and RAM-only boot experiments.
- Existing notes warn that vendor U-Boot can decrement slot-A boot attempts even
  when booting USB. Current counters are unknown; avoid unnecessary reboots.
- The similar CloudBook Air is not this board: its keyboard power GPIO0_C7 and
  1920x1200 BOE panel must not be copied onto this GPIO3_A3 / 1920x1080 laptop.
- With `init=/bin/sh`, the shell is PID 1. Do not exit it. Mount `/proc`, `/sys`
  and debugfs only as needed; inspect existing mounts first.

## Serial capture

Endpoint: `tcp://127.0.0.1:5000`. This is an existing serial bridge; baud rate is
controlled upstream, not by this TCP client. Another `nc` connection was visible
when inspected, so avoid typing through two clients concurrently.

```sh
python3 2026-11-24-Codex/serial_console.py
```

Connection alone transmits nothing. Input is line-oriented and Enter sends CR.
`:break` explicitly sends Ctrl-C to the target; `:quit` disconnects locally.
A local Ctrl-C disconnects the logger rather than intentionally interrupting the
target. Under `logs/`, each session writes exact RX/TX bytes and a timestamped
JSONL journal with direction, hex bytes and decoded text. Logs can contain serial
numbers, addresses and other private device information.

## Baseline evidence

Reference files are snapshots, not proof of what is on the live USB today.

- `ref/usbdisk-Nov-24/extlinux/extlinux.conf` loads `/boot/Image` and
  `/boot/rk3568-laptop-zte.dtb`, root `PARTUUID=12345678-02`, `init=/bin/sh`,
  UART2 at `0xfe660000`, `console=tty0 console=ttyS2,115200n8`,
  `clk_ignore_unused pd_ignore_unused`. It does not load an initrd.
- `ref/2026-11-23/03-has-bash.txt` records BSP kernel
  `5.10.160-g6c6e1238ebb1-dirty`, model `ZTE W600D SE (PVT-CS)`.
- That log records `gpio-99 (w600d-keyboard-power): hogged as output/high` and
  SINO WEALTH USB keyboard `258a:0001` registered through
  `usbhost/fd000000.dwc3`, USB port `7-1`. This establishes enumeration, not
  physical key-event delivery or a usable local console.
- Linux binds VOP2 and HDMI but no eDP binding is visible in that log. DRM says
  `Cannot find any crtc or sizes`; the HDMI connector has no modes. Prioritize
  checking the active eDP node, driver availability and deferred probes before
  changing VOP plane allocation.
- Vendor U-Boot successfully reads a 1920x1080 eDP mode, clock 141020 kHz,
  and displays using VP1 / Smart0. It also logs board-specific eDP voltage
  handling. Its working setup is an important board-specific baseline.
- Linux's actual command line in the November 23 log has duplicate
  `console=ttyS2,115200n8`, despite the extlinux APPEND line including `tty0`.
  Inspect the live `/proc/cmdline` and DT `/chosen/bootargs`; do not assume local
  console configuration survived the bootloader unchanged.
- The same log reports unaligned reserved DRM logo memory: base `0x7df00000`,
  size `0xbddc36`, required alignment `0x1000`. This may affect logo handover,
  but does not by itself explain the missing eDP connector.
- `ref/usbdisk-Nov-24/zte_w600d_linux.dts` is a synthesized draft with placeholder
  clocks and an incorrectly placed GPIO hog, not a trustworthy complete board
  DTS. The actual extlinux target is the compiled `rk3568-laptop-zte.dtb`.

## Useful references

- `ref/u-boot-zte-w600d-se/_RESEARCH/memory.md`: prior board/bootloader findings.
- `ref/u-boot-zte-w600d-se/_RESEARCH/docs/partitions.md`: eMMC map and boot chain.
- `ref/u-boot-zte-w600d-se/_RESEARCH/docs/HOWTO-uboot-shell.md`: known-working
  U-Boot keyboard power and vendor-display takeover.
- `ref/backups/zte-book.dts`: slot-B Android device tree.
- `ref/backups/w600d-backup/resource_a/w600dse-pvt-cs.dts`: board-specific slot-A
  resource tree used for vendor bootloader display configuration.
- `ref/2026-11-11/`: earlier Linux display and VOP-routing experiments.
- `ref/2026-11-23/`: most recent available Linux and vendor-U-Boot transcripts.
- `ref/eastwoodnet_cloudbook-air-mainline-linux/`: comparison only; a different
  RK3568 laptop with mainline 6.12, custom eDP/PHY patches, different power GPIOs
  and a different panel. Its kexec notes warn that U-Boot normally supplies memory
  banks, so a replacement DTB without `/memory` cannot safely be used for kexec.

## First live inspection

Read `uname -a`, `/proc/cmdline`, `/proc/mounts`, `/proc/bus/input/devices`,
`/proc/modules`, `/sys/class/drm`, `/sys/class/backlight`, and dmesg. Inspect
debugfs `devices_deferred`, `gpio`, DRM state and available clock/PHY information
after mounting debugfs if needed. Determine shell tools and safe USB transfer
options before proposing any on-device file changes.

Distinguish USB enumeration, input-event verification, DRM connector/mode
verification and the user's physical confirmation of screen output.
