# Debugging without rewriting the USB

## Mainline black-screen root cause and fix

The first Linux 7.3.6 boot reported a connected/enabled eDP connector and ran
XFCE, but Linux link training failed:

```text
rockchip-edpphy-naneng: invalid params for phy configure
analogix_dp_set_link_bandwidth: phy_configure() failed: -22
Wait for pll lock failed -110
```

The imported Naneng PHY requires a valid lane count. Analogix's rate/voltage
callbacks did not populate `phy_cfg.dp.lanes` on those calls.
`../build/linux-7.3.6/patches/0004-analogix-complete-phy-lanes.patch` supplies
`dp->link_train.lane_count`. The corrected kernel subsequently produced
visible screen output and working Ctrl+Alt+F1 on the laptop.

Do not confuse vendor U-Boot's `Link Training success!` with Linux successfully
training the link. Connected DRM status and running desktop processes alone
were not enough to demonstrate pixels on this screen.

## Only update the files that changed

- Kernel built-in driver change: replace `/boot/Image` on FAT.
- Wiring/timing-only change: build final v3 DTB and replace its FAT file.
- Module change: update matching `/lib/modules/7.3.6-w600d-usb/` on ext4 too.
- Service/rootfs change: update only the relevant ext4 files and preserve owners,
  modes and symlinks.
- Boot arguments: edit only extlinux, retaining rescue entries and a rollback.

Identify the USB by capacity, serial and partition layout before writes, and
never write while the same drive is mounted or active in the laptop. If updating
offline, cleanly shut down and move it to the host first. Keep staged/rollback
filenames, sync, unmount/eject, then return it to the powered-off laptop.

The guarded host updater is
`../build/linux-7.3.6/scripts/update-usb-kernel-files.py`. It is tied to the
recorded Kingston and refuses unexpected/mounted devices and existing staging
or rollback names. The current USB already contains
`/boot/Image.pre-lanes-20261124`, so rerunning the same updater blindly will
refuse. Inspect and plan a new rollback name rather than deleting the evidence.

That November 24 update replaced only Image; no DTB/extlinux/MBR/rootfs/eMMC
write accompanied it. Whole-drive flashes/read-backs are not required for
these incremental debug changes. The user explicitly skipped the original
full-disk read-back; do not restart it just because an old log says pending.

## UART and duplicate getty

Use a single client on `tcp://localhost:5000`:

```sh
python3 tools/serial_console.py --host 127.0.0.1 --port 5000 --log-dir logs/live
```

Run that command from the snapshot root. Enter sends UART CR, `:break` sends
Ctrl-C, and `:quit` disconnects locally. A second nc client can steal output.
Check the prompt and who owns the UART before transmitting commands.

Docker export left `/.dockerenv` on the actual hardware rootfs. Systemd detected
`docker` and started `console-getty` alongside `serial-getty@ttyS2`; both
consumed UART input. The user restored access from tty1 with:

```sh
sudo systemctl stop console-getty
sudo systemctl restart serial-getty@ttyS2
```

Those were runtime-only repairs. The live marker still existed in the last
query; persistent cleanup and a clean reboot are pending. Keep tty1 and ttyS2
login, remove only container runtime markers, and prevent duplicate console
getty. PID1's already-selected container mode persists until reboot.

The **build** fix is included: `scripts/normalize-container-markers.sh` and
`scripts/strip-container-runtime-markers.py` remove only `.dockerenv`,
`run/.containerenv` and `run/systemd/container` after export, preserving tar
metadata. Removing them only in a Docker RUN step is insufficient.
See `ROOTFS-CONTAINER-MARKERS.md` for the retained original archive.

## Next diagnostic boundaries

- Ethernet: recheck after the interrupted command, identify the bound driver
  through sysfs, inspect NetworkManager policy and then request DHCP. Do not
  assume a driver based solely on the adapter's marketing name.
- Trackpad: compare this machine's factory nodes/power/reset/interrupt wiring
  and available drivers. The CloudBook touchpad DTS is comparison-only.
- Display: confirm a complete visible XFCE desktop and physical typing, not
  merely processes, a cursor or a DRM status flag.
- Power management: existing clock/power preservation flags and disabled DVFS
  are bring-up safeguards, not completed suspend/power-management support.
