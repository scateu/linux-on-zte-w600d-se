# Current checkpoint — November 24, 2026, +08:00

## New USB/mainline phase — supersedes the historical resume state below

Read **NEW-USB-RELEASE.md** first. Linux 7.3.6 and Ubuntu 24.04.5 XFCE are
built on trash; the authorized new Kingston /dev/sdb has received the complete
29510 MiB image and is currently flushing before uncached read-back verification.
Do not remove it yet. This new USB boots directly from original vendor eMMC
U-Boot via USB extlinux; it includes no second USB U-Boot or boot.scr.

The screen/keyboard evidence below belongs to the older 5.10 BSP tests, not
the new mainline image. No new-kernel hardware acceptance has occurred.
All serial session IDs below are historical. Last live session 81726 closed
when its TCP bridge ended; no client is currently active at localhost:5000.
Do not assume a PID1 shell is still running or reuse old session IDs.

Current build recipe: linux-7.3.6-build/BUILD-VERIFIED.md. New USB uses 512 MiB
FAT32 boot and the remaining capacity as ext4 Ubuntu root. Android/eMMC was
not reflashed. After successful read-back, coordinate new USB/power/serial,
verify display and keyboard, then shutdown/remove USB and observe Android.

## Historical BSP checkpoint follows

## Read this first

**The internal display is working.** The user confirmed: "screen turned all white".
The complete reproducible RAM-only test is in `display-success.md`.

This file and `display-success.md` supersede the preflight resume state in
`README.md`, `memory.md` and `ram-display-test.md`. An attempted `apply_patch`
update of those existing files was denied with `Operation not permitted`, even
with requested escalation. Adding these new files succeeded. Do not interpret
the older black-screen/pending-remount descriptions as the current machine state.

## Target and serial state

- Target is running `/bin/sh` as PID 1, not stopped at U-Boot.
- `/dev/root / ext4 ro,relatime`: USB root is read-only; no eMMC partition mounted.
- proc, sysfs and debugfs are mounted for observation.
- Active serial exec session: `83306`, `127.0.0.1:5000`.
- Current capture: `logs/serial-20261124T113221-669340+0800` with JSONL/RX/TX files.
- No test process or keyboard reader remains running; the screen is left white.
- Do not exit PID 1, send Ctrl-D, or create a second serial client without checking
  the existing session. `:quit` is a local disconnect; `:break` sends target Ctrl-C.
- Do not reboot just to inspect: the eight display status changes exist only in RAM.

## Completed operations and evidence

1. Synced and remounted USB root read-only; `/proc/mounts` verified `ro`.
2. Completed one actual reboot and intercepted vendor U-Boot 2017.09.
3. Loaded existing USB 0:1 `/boot/Image` at `0x00280000`, DTB at `0x0a100000`.
4. Expanded the loaded FDT and enabled PHY/eDP/PWM2/panel supply/panel/backlight,
   VP1 input and eDP route. Kept VP0 input disabled and all wiring unchanged.
5. Used RAM bootargs with USB `PARTUUID=12345678-02`, `ro init=/bin/sh`, then `booti`.
6. Verified eDP-1 connected/enabled, 1920×1080p60 on VP1/Smart0, 141020 kHz.
7. Verified fb0 character device 29:0, virtual size 1920×1080, 32 bpp, stride 7680.
8. Wrote exactly 8294400 white bytes. Scanout initially still used the old RG24 logo.
9. `printf '0,0\n' > /sys/class/graphics/fb0/pan` switched scanout to Linux XR24 fb184.
10. User confirmed the whole internal screen turned white.

Backlight is 200/255. PWM2 at `0xfdd70020` is requested/enabled, 25000 ns period,
19607 ns duty, normal polarity. Do not switch to PWM8: the raw Android DTB proves
PWM2/GPIO0_B6 is this board's wiring. Panel supply and backlight-enable GPIOs were high.

No USB Image/DTB/extlinux/script replacement, `saveenv`, flash/eMMC/GPT/misc write
or slot modification was issued by us. Vendor bootloader behavior was not audited
byte-for-byte. The nonfatal FDT_DTBO allocation warning and logo alignment warning
are recorded in `display-success.md`; do not hide them or reset to investigate.

## Keyboard and remaining work

The previous boot verified 60 physical key press/release pairs from the SINO WEALTH
258a:0001 keyboard. **After this reboot the main keyboard is event1, not event2.**
`event2` is System Control and `event3` Consumer Control. Rediscover via
`/proc/bus/input/devices` on each boot. The touchpad enumerates on event4/event5;
no new physical touchpad test is claimed.

Hardware display pixels and physical keyboard input are verified. A normal local
text console is not: this kernel lacks `CONFIG_FRAMEBUFFER_CONSOLE`, and requested
tty0 bootargs are still rewritten to duplicate ttyS2. Next phase is a matching
kernel with framebuffer-console/font support, plus a tty1 shell/getty and review
of that bootarg fixup. Persistent installation requires a separate reversible plan.
