# RAM-only display test — November 24, 2026

## Authorization and preflight

The user explicitly approved syncing/remounting USB root read-only, rebooting,
and intercepting U-Boot for this test. Persistent boot files must remain unchanged.

The live precheck confirmed shell PID 1, USB ext4 root read/write, and only
devtmpfs, proc, sysfs and debugfs besides root. No eMMC partitions were mounted.
The actual command line still has two ttyS2 consoles and `init=/bin/sh`.

Command sent through logger session `6533`:

```sh
if sync; then
    if mount -o remount,ro /; then
        printf 'root remount reported success\n'
    else
        printf 'ROOT REMOUNT FAILED: DO NOT REBOOT\n'
    fi
else
    printf 'SYNC FAILED: DO NOT REBOOT\n'
fi
cat /proc/mounts
```

`sync completed` was observed after a USB reset/read error at kernel uptime
4851.66 s, sector 39081688. The read-only remount is still pending at this
checkpoint. Do not reboot until `/proc/mounts` explicitly confirms ext4 root `ro`.

## Planned boot interception

After the successful remount, disconnect the current logger locally with
`:quit`, not Ctrl-C to the target. Reconnect the existing serial logger with a
stdin producer that sends the approved reboot command, then repeated explicit
`:break` commands during early boot, and finally forwards interactive input.
This keeps one TCP sender and exact RX/TX logging. Store new captures in `logs/`
under this directory. No reboot command has been sent at this checkpoint.

## Planned RAM DT changes

Inspect the actual U-Boot environment, USB storage and command availability first.
Load the existing `/boot/Image` and `/boot/rk3568-laptop-zte.dtb` from the verified
USB partition, select the loaded working FDT and expand its scratch space.

Enable only the following existing nodes for the first display experiment:

- `/syscon@fdcb0000/edp-phy`
- `/edp@fe0c0000`
- `/pwm@fdd70020`
- `/vcc3v3-lcd-edp`
- `/backlight`
- `/edp-panel`
- `/edp@fe0c0000/ports/port@0/endpoint@1`
- `/display-subsystem/route/route-edp`

Keep VP0 input disabled. VP1's existing VOP peer is
`/vop@fe040000/ports/port@1/endpoint@2`. Keep `/backlight/pwms` and PWM2m1 pinmux
unchanged; the raw Android DTB confirms these are correct. Do not enable PWM8
or copy GPIO/PHY/graph overrides from the CloudBook Air project.

Set only RAM boot arguments, retaining `init=/bin/sh`, serial logging and unused
clock/power-domain preservation, but boot USB root read-only. Do not use `saveenv`
or edit extlinux, Image, DTB, boot scripts, eMMC, GPT or slot metadata.

## Required observations after boot

1. Mount proc/sysfs only as needed and inspect eDP driver binding and deferred probes.
2. Check DRM eDP connector status/modes, backlight registration and `/dev/fb0`.
3. Ask the user about illumination and test visible pixels with a bounded buffer
   write only after checking framebuffer geometry/stride/bpp and character-device identity.
4. Treat a local text console separately: this kernel lacks fbcon.
5. Record actual edits, addresses, boot arguments, logs and user-confirmed results.

No display test result is claimed by this preflight checkpoint.
