# Session memory — November 24, 2026 (+08:00)

**Historical BSP memory:** the resume state below is not current. Read
CURRENT.md and NEW-USB-RELEASE.md for the new mainline/Ubuntu USB build,
flash state and remaining physical acceptance. Old serial IDs are closed;
white-screen/key-event results do not prove the new 7.3.6 image works.

## Resume state

- Goal: internal display and keyboard under USB-booted Linux, retaining Android.
- Last confirmed target state: running `init=/bin/sh`, shell PID 1; never exit it.
- Latest serial exec session: `6533`, connected to `127.0.0.1:5000`. Check whether
  it is still active before starting another TCP client. Earlier session `61879`
  ended when the bridge closed its TCP connection; reconnecting did not reboot.
- The user confirms the screen is black and physically pressed keyboard keys.
- Keyboard event delivery is verified, not just USB enumeration.
- User explicitly approved sync/remount USB root read-only, reboot, and a RAM-only
  U-Boot display test. Verify remount success and preserve persistent boot files.
- Before this checkpoint, no reboot, eDP/clock/GPIO change, boot-file replacement,
  or eMMC write was performed by us. Only inspection and proc/sysfs/debugfs mounts.
- Earlier Markdown updates failed with `Operation not permitted`; the user has
  requested this new directory. Do not assume the old Markdown reflects live state.

## Serial evidence

Capture prefixes, relative to the workspace:

- `2026-11-24-Codex/logs/serial-20261124T100424-368782+0800`: unchanged boot,
  initial runtime inspection, kernel configuration and disabled DT properties.
- `2026-11-24-Codex/logs/serial-20261124T110331-297137+0800`: reconnection,
  live PWM phandles, physical keyboard capture and reboot precheck.

Each prefix has timestamped JSONL and exact RX/TX binaries. Initial undecodable
bytes were followed by readable U-Boot/Linux output; do not infer a sustained
baud mismatch. Target wall-clock/input timestamps are not the host capture clock.

## Keyboard result

- SINO WEALTH USB keyboard `258a:0001`, controller `fd000000.dwc3`, USB port `7-1`.
- GPIO99 / GPIO3_A3 (`w600d-keyboard-power`) is hogged output/high.
- `/proc/bus/input/devices` maps its main interface to `/dev/input/event2`.
- Bounded reader used: `timeout 180s stdbuf -oL od -An -v -t x1 -w24 /dev/input/event2`.
- Reader fd 3 was verified open on event2. Capture decoded 343 complete 24-byte
  input-event rows, including 120 EV_KEY events: 60 presses and 60 releases.
- Keycode pair counts: 31=6, 32=16, 33=21, 34=17; no repeat events were counted.
- This verifies physical keyboard input for the tested keys, not every key or
  delivery to a local shell. The bounded reader had exited by the reboot precheck.

## Display diagnosis and PWM correction

The live DT explicitly disables these nodes:

| Node | Role |
| --- | --- |
| `/syscon@fdcb0000/edp-phy` | eDP PHY |
| `/edp@fe0c0000` | eDP controller |
| `/edp@fe0c0000/ports/port@0/endpoint@0` | VP0 input; keep disabled for VP1 test |
| `/edp@fe0c0000/ports/port@0/endpoint@1` | VP1 input; enable for the test |
| `/display-subsystem/route/route-edp` | BSP display/boot-logo route |
| `/vcc3v3-lcd-edp` | Panel power regulator |
| `/edp-panel` | Simple panel |
| `/backlight` | PWM backlight |
| `/pwm@fdd70020` | Correct backlight controller, PWM2 |

The stored USB DTB has the same disabled display chain. Its VP1 VOP peer is
`/vop@fe040000/ports/port@1/endpoint@2`; VP1 is enabled and peer linkage exists.
Do not enable both eDP input routes blindly or transplant another board's graph.

**Correction:** I initially called the PWM2 reference incorrect and proposed PWM8.
Direct phandle resolution in the raw Android DTB proves PWM2 is correct. The raw
Android source is
`../ref/backups/w600d-backup/resource_a/rk3568-w600dse-pvt-cs___saradc_ch1=938___saradc_ch4=779.dtb`.

| Property | Android DTB | USB DTB |
| --- | --- | --- |
| Backlight PWM controller | PWM2 at `0xfdd70020`, enabled | Same controller, disabled |
| PWM phandle | `0x132` | `0x11c` |
| PWM period/polarity | 25000 ns / normal | Same |
| Pinmux | PWM2m1: GPIO0_B6, function 4 | Same |
| Panel power enable | GPIO2_D5, active high | Same |
| Panel enable | GPIO2_D4, active high | Same |
| Backlight enable | GPIO2_D3, active high | Same |

Keep USB `/backlight/pwms = <0x11c 0 0x61a8 0>` unchanged. Do not redirect it
to PWM8 (`0xfe6f0000`, USB phandle `0x1c1`), which belongs to the other board's setup.
The raw Android PHY has a board-specific `edp_phy_set` boolean, absent from the
USB PHY. Its effect in this 5.10 driver is unverified; do not treat it as volts.

## Kernel, DRM and console

- Kernel `5.10.160-g6c6e1238ebb1-dirty`, build November 10, 2026.
- Enabled config: DRM_ROCKCHIP, ROCKCHIP_ANALOGIX_DP, DRM_ANALOGIX_DP,
  DRM_PANEL_SIMPLE, PHY_ROCKCHIP_NANENG_EDP, DRM_FBDEV_EMULATION, VT, VT_CONSOLE.
- `CONFIG_FRAMEBUFFER_CONSOLE` and `CONFIG_OF_OVERLAY` are not set.
- Registered drivers include rockchip-dp, rockchip-edpphy-naneng, panel-simple,
  and pwm-backlight. They cannot bind the disabled eDP/panel/backlight nodes.
- DRM binds VOP2 + HDMI only. HDMI is disconnected with no modes; no eDP connector,
  no `/dev/fb0`, and no entries in `/sys/class/graphics`. tty0/tty1 devices exist.
- Debugfs `devices_deferred` lists only `mtd_vendor_storage`, not eDP.
- Extlinux APPEND includes tty0, but the actual kernel command line contains two
  ttyS2 console arguments and no tty0. The precise bootloader fixup is unverified.
- Vendor U-Boot drives 1920x1080 / 141020 kHz on VP1/Smart0, two lanes, link rate
  0x0a, with ZTE-specific training voltage handling. Linux binding/pixels must be
  tested separately from text console support and vendor logo handover.
- DRM logo reservation alignment error: base 0x7df00000, size 0xbddc36, required
  0x1000 alignment. Do not let this distract from the disabled eDP chain.

## USB reliability and reboot gate

- Root is USB `/dev/sda2`, ext4, initially read/write; no eMMC partitions mounted.
- Storage is Fanxiang, 480 Mbit/s, through `usbdrd/fcc00000.dwc3`, USB port `5-1`.
  Runtime PM is already `on` / `active`; do not assume autosuspend is the cause.
- Repeated resets and 30–31 second SCSI timeouts cause READ I/O errors, including
  sectors 38800392, 39073360, 39096464 and 39094440. External binaries may stall.
- `/usr/bin/sync` exists; no reboot executable was found on PATH. The writable
  `/proc/sysrq-trigger` interface exists but had not been used at this checkpoint.
- Sync and remount root read-only, confirm `/proc/mounts`, then perform the approved
  reboot. Do not reset blindly if sync/remount reports failure or is still running.
- Boot the RAM test with `init=/bin/sh` and USB root read-only. After eDP binding,
  inspect mode/backlight/fbdev and use a bounded framebuffer test for visible pixels;
  absent fbcon means a local text console is a separate follow-up.

## Snapshot and boot-path boundaries

- Actual observed boot reads `/extlinux/extlinux.conf`, `/boot/Image`, and
  `/boot/rk3568-laptop-zte.dtb` through vendor U-Boot. No second U-Boot banner was
  observed in this capture; the user's general chain-load workflow still exists.
- Do not execute the stored `boot/boot.cmd` as this test: it references different
  kernel/DTB files, root=/dev/ram0 without a loaded initrd, and mismatched DT paths.
- Snapshot hashes and offline parser validation are in the previous directory's
  `memory.md`. No live USB Image/DTB hash comparison has been performed.
- The old directory is not a Git checkout. Host dtc/fdtget/fdtput and an AArch64
  Linux cross-compiler were not found; native clang alone is not a verified build setup.
