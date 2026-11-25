# ZTE W600D SE Linux bring-up — November 24, 2026

Continue bringing up the internal display and keyboard while preserving Android
and the existing USB boot files. This directory continues `../2026-11-24-Codex/`.
All host timestamps use Asia/Shanghai (+08:00).

## Verified status

- Linux `5.10.160-g6c6e1238ebb1-dirty` boots from USB to a PID-1 `/bin/sh` shell.
- Internal keyboard delivers real Linux input events: 60 press/release pairs
  were decoded from `/dev/input/event2`; local-console delivery is separate.
- User confirms the internal screen is black.
- The active DT disables the eDP PHY/controller, panel power, panel, backlight,
  eDP input endpoints/route, and the backlight's PWM2 controller.
- **PWM2 is correct for this board.** Raw Android DTB inspection disproved the
  earlier PWM8 hypothesis. No PWM-controller change was applied.
- eDP/panel/backlight drivers are compiled in, but framebuffer-console support
  and live device-tree overlays are not. A visible-pixel test does not require
  a working text console.
- USB root-device read errors cause resets and long external-command delays.

## Authorized next operation

The user has approved syncing/remounting USB root read-only, rebooting into
U-Boot, and applying a RAM-only display test. This is authorization, not a claim
that the test has already happened. Record its result in `memory.md`.

1. Confirm mounts and sync/remount USB root read-only; verify success before reboot.
2. Intercept U-Boot and inspect its actual environment and available commands.
3. Load the existing Image/DTB, enable this board's eDP chain and PWM2 in RAM,
   keep the correct existing PWM phandle/pinmux, and use the VP1 input route.
4. Boot the USB root read-only, inspect DRM/backlight/fbdev, and test visible pixels.
5. Address local text-console support after display binding works.

## Safety and references

- Never exit the PID-1 shell or send Ctrl-D. Do not use `saveenv`, flash scripts,
  eMMC/GPT/misc/slot writes, or persistent USB boot-file replacements.
- Vendor U-Boot can update A/B metadata independently of our commands; minimize
  retries. Observed boot logs say slot A successful=1, tries-remain=0, but current
  `misc` bytes have not been read back.
- Use `memory.md` for resume state and board-specific wiring. Use the previous
  directory's `serial_console.py` and `dtb_inventory.py` rather than copying tools.
- Partition/bootloader notes: `../ref/u-boot-zte-w600d-se/_RESEARCH/docs/partitions.md`
  and `../ref/u-boot-zte-w600d-se/_RESEARCH/memory.md`.
- The CloudBook Air project is a strategy reference, not a drop-in DTS: its
  keyboard GPIO, panel resolution and PWM controller differ from this laptop.
