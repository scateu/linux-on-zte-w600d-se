# Internal display works — November 24, 2026

## Result and current state

**The user confirmed: "screen turned all white" after the RAM-only test.**

Linux drives the internal eDP panel at 1920×1080p60 through VP1/Smart0.
The display-chain changes exist only in the loaded device tree in RAM.
The existing USB Image, DTB, extlinux configuration and boot scripts were not
edited. No `saveenv`, flash command, eMMC/GPT/misc write or slot modification
was issued by this session. Vendor bootloader behavior is a separate boundary;
this is not a byte-for-byte verification of all persistent storage.

The target is running `/bin/sh` as PID 1. USB root is still read-only:

```text
/dev/root / ext4 ro,relatime 0 0
```

Do not exit this shell or send Ctrl-D. Do not reboot merely to repeat the test:
the original on-disk DTB still disables the display chain, so these RAM changes
will be lost. The screen is left white, not blanked or powered down.

Active serial exec session: `83306`, connected to `127.0.0.1:5000`.
Check that session before creating another TCP client. Existing logger commands:
`:quit` disconnects locally; `:break` explicitly sends target Ctrl-C.
No input reader or display-test process remains running after the commands below.

Authoritative serial capture prefix:

```text
2026-11-24-Codex2/logs/serial-20261124T113221-669340+0800
```

The `.jsonl` contains timestamped RX/TX; `.rx.bin` and `.tx.bin` preserve bytes.
The physical white-screen confirmation is in the user conversation, not the
serial stream. All host times below are November 24, 2026, Asia/Shanghai (+08:00).

## Reboot and U-Boot preflight

The previously pending sync/remount completed. `/proc/mounts` explicitly confirmed
USB ext4 root read-only before the approved reboot. No eMMC partition was mounted.
An initial Ctrl-C burst cancelled the reboot command before it executed; a retry
with a one-second delay produced one actual reboot and stopped at vendor U-Boot.

Observed U-Boot: `2017.09`, built May 29, 2024. Environment:

```text
kernel_addr_r=0x00280000
fdt_addr_r=0x0a100000
ramdisk_addr_r=0x0a200000
bootdelay=0
```

`fdt_high`, `console` and `baudrate` were undefined. Commands `load`, `fdt`
and `booti` were available. Original bootargs were Android-derived and included
`edp_name=guoxian-30NK`; they were replaced only in the current RAM environment.

`usb start` at 11:35:28 found one Fanxiang F313 storage device. `part list usb 0`:

| Partition | Start sector | Sectors | PARTUUID | Type |
| --- | --- | --- | --- | --- |
| USB 0:1 | 2048 | 1048576 | `12345678-01` | DOS type `0c` |
| USB 0:2 | 1050624 | 60389377 | `12345678-02` | DOS type `83` |

`ls usb 0:1 /boot` verified the existing files before loading:
`Image` = 36506112 bytes; `rk3568-laptop-zte.dtb` = 165657 bytes.
The loaded DT model was `ZTE W600D SE (PVT-CS)`.

## Exact RAM-only boot sequence

These are the commands actually executed, split into individual lines for reuse.
Wait for each U-Boot prompt, particularly after USB scanning/loading. Verify the
environment, storage numbering and files anew before reusing on a later boot.

```text
usb start
usb storage
part list usb 0
ls usb 0:1 /boot
load usb 0:1 ${kernel_addr_r} /boot/Image
load usb 0:1 ${fdt_addr_r} /boot/rk3568-laptop-zte.dtb
fdt addr ${fdt_addr_r}
fdt resize 0x1000
fdt set /syscon@fdcb0000/edp-phy status okay
fdt set /edp@fe0c0000 status okay
fdt set /pwm@fdd70020 status okay
fdt set /vcc3v3-lcd-edp status okay
fdt set /backlight status okay
fdt set /edp-panel status okay
fdt set /edp@fe0c0000/ports/port@0/endpoint@1 status okay
fdt set /display-subsystem/route/route-edp status okay
setenv bootargs earlycon=uart8250,mmio32,0xfe660000,115200n8 console=tty0 console=ttyS2,115200n8 clk_ignore_unused pd_ignore_unused root=PARTUUID=12345678-02 rootdelay=5 rootwait ro init=/bin/sh
booti ${kernel_addr_r} - ${fdt_addr_r}
```

Before `booti`, `fdt print ... status` verified all eight nodes were `okay`;
VP0's `/edp@fe0c0000/ports/port@0/endpoint@0` remained `disabled`.
The existing VP1 peer `/vop@fe040000/ports/port@1/endpoint@2` and route connection
were retained. Backlight `pwms = <0x11c 0 0x61a8 0>` was explicitly rechecked
unchanged. No GPIO, timing, voltage or PHY tuning property was added.

**PWM2 is correct:** PWM2m1/GPIO0_B6, 25000 ns, normal polarity. Panel power is
GPIO2_D5; panel enable GPIO2_D4; backlight enable GPIO2_D3, all active high.
Do not use the earlier PWM8 hypothesis or transplant CloudBook Air pin wiring.

Image load: 11:36:29. DTB load: 11:36:37. `booti`: 11:37:33.
Do not run normal `bootcmd`/extlinux after these changes: it could reload the DTB.

## Nonfatal warnings and console limitation

U-Boot printed `Sysmem Error: Found there is region overflow!`, marking its
`FDT_DTBO` bookkeeping region at `0x0a100000` through `0x0a12590c` as overflowing.
It continued, reserved `0x2a000` bytes at that address and booted Linux. The cause
is not conclusively diagnosed; this warning must be recorded rather than hidden.
Expanded-FDT bookkeeping is a candidate to investigate before making a durable
boot recipe. Do not treat the successful test as proof all allocations are ideal.

Linux printed a pre-existing DRM boot-logo reservation alignment error:
base `0x7df00000`, size `0xbddc36`, required alignment `0x1000`.
Nevertheless eDP bound and fbdev registered. A later framebuffer pan released
12152 KiB of logo memory; see the handover below.

Actual kernel command line still replaces the requested tty0 console with a
second ttyS2 and strips earlycon's explicit baud option:

```text
earlycon=uart8250,mmio32,0xfe660000 console=ttyS2,115200n8 console=ttyS2,115200n8 clk_ignore_unused pd_ignore_unused root=PARTUUID=12345678-02 rootdelay=5 rootwait ro init=/bin/sh
```

This kernel has `CONFIG_DRM_FBDEV_EMULATION=y`, but `CONFIG_FRAMEBUFFER_CONSOLE`
is not set. **Working display pixels are not a working local text console.**
The DRM state label `allocated by = [fbcon]` describes its fb-helper allocation;
it does not override the verified missing kernel configuration.

## Linux observations

Kernel: `5.10.160-g6c6e1238ebb1-dirty`, November 10, 2026 build.
Mounted proc, sysfs and debugfs for inspection; root remained read-only.

```sh
[ -r /proc/cmdline ] || mount -t proc proc /proc
[ -d /sys/class/drm ] || mount -t sysfs sysfs /sys
[ -r /sys/kernel/debug/dri/0/state ] || mount -t debugfs debugfs /sys/kernel/debug
```

Verified:

- `fe0c0000.edp` bound to `rockchip-drm`; `/dev/fb0` is character device `29:0`.
- `/sys/class/drm/card0-eDP-1/status` = `connected`, `enabled` = `enabled`.
- eDP mode list contains two `1920x1080` entries.
- `/sys/class/graphics/fb0/virtual_size` = `1920,1080`, stride `7680`, bpp `32`.
- Backlight brightness/actual/max = `200/200/255`; `bl_power` = `0`.
- PWM2 is requested/enabled: period `25000 ns`, duty `19607 ns`, normal polarity.
- GPIO91 (backlight enable), GPIO93 (panel supply) and GPIO99 (keyboard power)
  were observed output/high. Panel-enable GPIO92 was not separately sampled.
- Deferred probes contain only `mtd_vendor_storage`.
- `/sys/kernel/debug/dri/0/summary`: VP1 active, eDP-1, RGB888_1X24,
  `1920x1080p60`, requested/real clock both `141020 kHz`.
- Mode timings: H `1920 1968 2000 2080`; V `1080 1090 1102 1130`.

## The essential boot-logo-to-fbdev handover

At first, DRM scanned out **fb181**, a loader-logo `RG24` buffer, pitch `5760`,
offset `6221878`, object size `12443648`. Linux `/dev/fb0` instead exposes a
32-bit buffer. Writing fb0 alone did not replace the loader-logo scanout.

At 11:39:18 the geometry-checked command wrote exactly 8294400 bytes of white:

```sh
if [ -c /dev/fb0 ] &&
   [ "$(cat /sys/class/graphics/fb0/virtual_size)" = '1920,1080' ] &&
   [ "$(cat /sys/class/graphics/fb0/stride)" = 7680 ] &&
   [ "$(cat /sys/class/graphics/fb0/bits_per_pixel)" = 32 ]; then
    dd if=/dev/zero bs=7680 count=1080 2>/dev/null |
        tr '\000' '\377' |
        dd of=/dev/fb0 bs=7680 count=1080 iflag=fullblock conv=notrunc
else
    printf 'GEOMETRY CHECK FAILED: no framebuffer write\n'
fi
```

`dd` confirmed `1080+0` records and `8294400 bytes` written. DRM still showed
the old RG24 logo buffer. **At 11:40:15, this additional RAM-only action switched
scanout to the Linux framebuffer without changing resolution:**

```sh
printf '0,0\n' > /sys/class/graphics/fb0/pan
```

Afterward Smart0/VP1 scanned **fb184**, `XR24` little-endian, pitch `7680`,
offset `0`, object size `8294400`. Linux logged `Freeing drm_logo memory: 12152K`.
The user then confirmed the entire internal screen turned white.

This handover matters for later diagnostics: a valid fb0 plus a successful write
does not guarantee those bytes are the currently scanned-out buffer.

## Keyboard and next phase

Physical key events were already proven in the preceding boot: 60 press/release
pairs from SINO WEALTH `258a:0001`; details are in `memory.md`. On **this** boot,
`/proc/bus/input/devices` maps the main keyboard to **event1**, not event2.
`event2` is now its System Control interface, and `event3` Consumer Control.
Always rediscover the main interface after reboot; do not hard-code event2.
The touchpad also enumerates as I2C HID `093a:0255`, event4/event5; this is
enumeration evidence, not a new physical touchpad test.

The hardware milestones are now: physical keyboard events verified and internal
Linux framebuffer pixels visually verified. For a normal keyboard-driven local
text shell, the next phase is a matching kernel with `CONFIG_FRAMEBUFFER_CONSOLE=y`
(and an appropriate built-in font), plus an intentional tty1/getty or local shell
and review of the tty0 bootarg rewrite. Do not exit PID 1 to start it.
Any persistent DTB/kernel/extlinux change requires a separate reversible plan;
none was made during this RAM-only experiment.
