# Session memory — 2026-11-24 (Asia/Shanghai)

## Resume here

- User's objective: internal display and keyboard under USB-booted Linux.
- Machine was reported powered off. Do not ask for power until serial capture
  is actually connected; user will plug power on when we confirm readiness.
- TCP endpoint `127.0.0.1:5000` exists: `lsof` showed an SSH-forward listener
  plus an existing `nc` client. Do not send through competing clients.
- Attempting the new Python serial logger failed at `socket.connect()` with
  `PermissionError: [Errno 1] Operation not permitted`. This task's filesystem/
  network sandbox forbids the connection. No console bytes were transmitted.
  Localhost network access needs to be enabled before autonomous live work.
- User requested a direct `nc localhost 5000` retry. It exited with status 1;
  `nc -vz -w 3 localhost 5000` then reported twice:
  `connectx to localhost port 5000 (tcp) failed: Operation not permitted`.
  The connection remains blocked for netcat as well as Python; no live session
  was established and no bytes were sent to the laptop.
- No reference files, live USB files, firmware or partitions were modified.
- Notes and tools are confined to this directory; the attempted session has
  a journal and empty RX/TX binary files under `logs/`.

## Important offline discovery

The actual extlinux DTB snapshot is
`ref/usbdisk-Nov-24/boot/rk3568-laptop-zte.dtb`. A read-only binary FDT inspection
found **all these nodes explicitly `status = "disabled"`**:

| Node | Function |
| --- | --- |
| `/syscon@fdcb0000/edp-phy` | RK3568 eDP PHY |
| `/edp@fe0c0000` | eDP controller |
| `/edp@fe0c0000/ports/port@0/endpoint@0` | VOP input endpoint 0 |
| `/edp@fe0c0000/ports/port@0/endpoint@1` | VOP input endpoint 1 |
| `/display-subsystem/route/route-edp` | BSP eDP boot-logo route |
| `/vcc3v3-lcd-edp` | Panel power regulator |
| `/backlight` | PWM backlight |
| `/edp-panel` | `simple-panel` display |

The overall `/display-subsystem` is enabled and its HDMI route is enabled.
This explains why the November 23 Linux transcript binds VOP2 + HDMI but no eDP:
the stored tree disables the display chain. **This is an offline inference,
not verification that the currently attached USB has identical bytes.**

The Image snapshot contains the exact banner for
`5.10.160-g6c6e1238ebb1-dirty`, build date November 10, 2026, and strings for
`rockchip,rk3568-edp-phy`, `analogix_dp` and `simple-panel`. Driver-related
strings are encouraging but are not a substitute for verifying the kernel
configuration and successful runtime binding.

The correct keyboard hog is already present in the compiled tree:
`/pinctrl/gpio3@fe760000/keyboard-power-hog`, `gpios = <3 0>`, `output-high`.
The November 23 log confirms GPIO99 high and USB `258a:0001` enumeration.
Physical events and local-console delivery remain unverified.

## Reproducible host inspection

```sh
python3 2026-11-24-Codex/dtb_inventory.py \
  ref/usbdisk-Nov-24/boot/rk3568-laptop-zte.dtb \
  --match edp --match backlight --match keyboard-power --match chosen
```

The utility reads version-17 FDT blobs directly, includes all nodes (including
empty ones), reports raw property bytes, and does not edit or recompile DTBs.
Host `dtc`, `fdtget`, `fdtput` and `aarch64-elf-gcc` were not found on PATH.

Offline validation passed: the inventory parser read all 24 supplied DTB blobs,
rejected a truncated input, and confirmed the disabled eDP/backlight and keyboard
GPIO properties. A mocked serial session verified exact binary RX/TX logging,
CR conversion, explicit Ctrl-C transmission and local quit. That test used no
network and does not resolve the real connection denial.

SHA-256 of supplied snapshots:

- `boot/Image`: `470eccce48e9b780c3dc1f76c7144829a10c15e80517c3dcf45c01240d40f863`
- `boot/rk3568-laptop-zte.dtb`: `4578807d00d97eed27227955e10251ff195f2de38d3d3b783965dc2b5057aa8e`
- `extlinux/extlinux.conf`: `5ef3b7c8b83a42b9d4011cff4a43a31da5984110068672edda63fde1e21559bb`

## Next live steps after network access is restored

1. Start `serial_console.py` in a persistent PTY session; confirm it says
   connected before inviting power-on. Capture the unchanged boot first.
2. With `init=/bin/sh`, never exit PID 1. Inspect mounts before mounting proc,
   sysfs or debugfs. Record kernel version, cmdline, DT eDP status, dmesg,
   input devices, DRM connectors and deferred devices.
3. Ask the user to press a key while reading the matching input event device
   with available tools. Registration alone does not prove usable input.
4. Compare active device-tree status to the disabled snapshot. If identical,
   a coordinated, RAM-only U-Boot FDT edit is a promising first display test.
   Work out required PWM status, GPIO polarity, regulator supplies, graph
   endpoints and panel timings before sending edits. Avoid enabling conflicting
   VOP endpoints or changing HDMI/VP allocations blindly.
5. Retain Android and the known-working USB files. No eMMC/misc/slot writes or
   uncoordinated reboots. Slot-A retry counters are unknown and old notes warn
   that USB chain-boots may consume them.

## Comparison project caution

The CloudBook Air project is a different board. It uses GPIO0_C7 keyboard power
and a BOE 1920x1200 panel; ours uses GPIO3_A3 and the vendor bootloader detects
1920x1080 / 141020 kHz. Do not transplant its DTS or mainline eDP PHY voltage
override directly. Our supplied kernel is BSP 5.10, not its patched 6.12.
