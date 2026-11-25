# New USB Linux release — November 24, 2026

## Current checkpoint

At 16:39 +08:00, the complete image had been submitted to the authorized
Kingston USB, and `dd conv=fsync` was still flushing. **Do not remove it
until the full uncached read-back SHA256 has passed.** Native Linux 7.3.6
has not yet booted on the laptop; display, physical keyboard, desktop and
USB-removed Android fallback are still acceptance tasks, not proven results.

The old BSP 5.10 white-screen and physical-keyboard tests remain useful
hardware evidence, but are not a claim that the new mainline image works.
The old sole serial session `81726` ended when the TCP bridge closed.
No serial connection is currently active; restore `localhost:5000` before
the new laptop boot, and use one logged client only.

## Bootflow: the new drive has no second U-Boot

```text
Rockchip BootROM -> original eMMC DDR/SPL/firmware/vendor U-Boot
    -> already-patched flat USB-first bootcmd
    -> new USB p1 /extlinux/extlinux.conf
    -> new USB p1 /boot/Image + final W600D DTB
    -> new USB p2 Ubuntu /sbin/init -> LightDM -> XFCE

Shutdown -> remove USB -> power on -> original vendor Android path
```

This replaces the old USB chain-loader experiment for the new image.
The old USB is preserved. The new USB contains **no USB U-Boot, boot.scr,
or raw Rockchip loader**. No further eMMC flash or `saveenv` was issued.
The Linux DT disables eMMC/SDMMC nodes so the new OS cannot mount Android
through those controllers. Vendor firmware may still update its own boot
retry metadata during normal starts; do not claim every eMMC byte is immutable.

## Authorized physical drive and layout

- Build host: `ssh trash`, user `k`, hostname `k-trash`.
- Workdir: `/home/k/codex-workdir-nov-24-2026`.
- Authorized whole disk: `/dev/sdb`, Kingston DataTraveler 3.0, USB.
- Serial: `E0D55E625BE9F440F84702D0`; capacity `30943995904` bytes.
- All descendants were unmounted, transport/serial/capacity/read-only state
  checked twice by the guarded writer immediately before writing.
- `/dev/sda` is the server's internal Samsung SSD: never a flash target.

| Item | Value |
| --- | --- |
| Partition table | MBR, disk ID `24c0d202` |
| p1 | start 1 MiB, 512 MiB FAT32, `W600D_BOOT`, PARTUUID `24c0d202-01` |
| p2 | start 513 MiB, 28997 MiB ext4, `W600D_ROOT`, PARTUUID `24c0d202-02` |
| Whole image | 29510 MiB, `30943477760` bytes |
| Unused physical tail | `518144` bytes, outside both partitions/image verification |

Two copies share PARTUUIDs: never connect two of these Linux USBs to the
laptop at the same time. A portable 6 GiB image is retained separately
for 8 GB or larger media; this Kingston-specific variant fills its capacity
by growing a regular-file copy of ext4 offline before flashing.

## Software and exact output hashes

Linux **7.3.6-w600d-usb**, built from checksum-verified kernel.org 7.3.6
source, with Ubuntu **24.04.5 LTS ARM64** expanded from official Ubuntu Base
into XFCE, LightDM, systemd, NetworkManager, normal apt and diagnostic tools.
Docker/QEMU-user are build-host tooling only, not a runtime requirement.

Server `artifacts/` contains:

```text
w600d-ubuntu-xfce-7.3.6-20261124-usb-29510MiB.img
SHA256 ec9bd70d021c829a528e52e9f9642162932b528ffddf3d7ab696497e8e5926d2

w600d-ubuntu-xfce-7.3.6-20261124-usb-29510MiB.img.zst
SHA256 ddf12f7a702c6868e80936fd01120887ef4785a464d3b054fad0513f27340272

kernel/Image
SHA256 8833f5368f69a9423c45c7e68d76827b3ac43f6eae5f6e208c58c469b8e90b13

kernel/rk3568-zte-w600d-mainline.dtb
SHA256 4e7156892cfaa29da5d73b217d6e846c01af9b6e6d449323192463dc551e942d

kernel/config-7.3.6-w600d-usb
SHA256 13a567071ccd42b1dab2baa32cc58e7f9471f1ec19a19969b5e9fbdfc9bd597a
```

The compressed full-capacity image is roughly 432 MiB because its free
space compresses well. Decompress it to the raw image before using the
guarded writer. The complete raw/compressed checksums and partition JSON
are saved alongside the images. Source/base checksums and release metadata
are retained under `downloads/`; package versions and build logs are saved.

## Board-specific changes and checked boundary

- Imported the comparison project's Naneng eDP PHY patch; adapted RK3568
  Analogix identification/table to 7.3.6's existing generic PHY framework.
- Final **v3 DTB only**, with explicit `DTC_FLAGS=-@`; symbols and wiring
  are checked by `validate-board.py`. Never boot intermediate v1/v2 DTBs.
- Physical ZTE panel is KDC KD140N1930A02, 1920x1080, 141020 kHz EDID.
  Added native VPLL 564080000 / 4; actual hardware clock/link remains untested.
- Panel supply GPIO2_D5, enable GPIO2_D4, backlight GPIO2_D3; PWM2m1 on
  GPIO0_B6, 25000 ns period. Do not copy reference PWM8 or its BOE override.
- SINO WEALTH keyboard `258a:0001`, power hog GPIO3_A3.
- Correct 2 GB memory and original IO supply mapping, especially **pmuio2
  at 3.3 V**. The intermediate wrong 1.8 V mapping was fixed before use.
- USB root, HID, serial, native eDP/PWM and framebuffer console built in;
  matching 7.3.6-w600d-usb modules installed. CPU DVFS remains disabled.
- Keep bring-up flags `clk_ignore_unused pd_ignore_unused cpuidle.off=1
  usbcore.autosuspend=-1` until power management is physically validated.

## Build fixes and reproducible entry point

Use `linux-7.3.6-build/BUILD-VERIFIED.md` and:

```sh
ssh trash
cd /home/k/codex-workdir-nov-24-2026
export ALL_PROXY=socks5://192.168.1.5:1080
export APT_PROXY=socks5h://192.168.1.5:1080
JOBS=24 bash scripts/build-verified-image.sh
bash scripts/assemble-capacity-image.sh 30943995904
```

Do this in a fresh workdir with the recipe inputs/reference PHY patch;
image/export scripts deliberately refuse to overwrite final outputs.
`FACTORY-UBOOT.md` describes per-machine original-image backup, offline
bootcmd patch, recovery precautions and explicitly separate eMMC installation.

Docker's mounted hostname/hosts/resolver files cannot be finalized reliably
inside RUN; replacing resolv.conf failed after all packages installed.
The release preserved that completed installation, finalized modules/services,
then normalized these files in an ordinary extracted rootfs under fakeroot.
The corrected clean recipe separates apt installation from configuration and
uses tiny, explicit contexts instead of uploading generated images to Docker.
The optional clean rebuild first failed while the supplied proxy was unreachable;
the proxy returned and a separate validation-tag rebuild is running. The actual
release's dpkg audit, package presence and service checks have already passed.

Filesystem checks passed before writing; FAT boot Image/DTB/extlinux extracted
from the assembled image compared byte-for-byte with the intended artifacts.
Checks also covered root/home/shadow/sudoers ownership, empty machine-id,
normalized resolver/hostname, disabled/masked SSH service **and socket**, and
absence of the build-only proxy and service inhibitor.

## Why no sudo password was needed

User `k` already belonged to `docker`; the root-owned daemon socket was
group-accessible. With the user's explicit whole-`/dev/sdb` permission, the
writer used a cached native amd64 tooling container with only this USB
passed as `/dev/usb-target` and the disk image bound read-only. No `sudo dd`,
password acquisition or permission change was performed. Docker-group access
is administrator-level capability; capability dropping does not remove a root
process's ability to write an explicitly passed root-owned block device.

The container has no network, a read-only root, no extra capabilities and no
other disk exposure. The writer verifies the source SHA256 before writing,
does `dd conv=fsync`, then `dd iflag=direct` over the entire image-sized
region and requires a matching SHA256. See `FLASH-NATIVE.md` and
`logs/flash-kingston-20261124.log` on trash for the exact mechanism and result.

## First real laptop acceptance

1. Wait for successful complete flash/read-back; keep the old USB intact.
2. Restore the TCP serial bridge, connect one logged client, power the laptop
   off, insert the new USB in the known-working port, then power on.
3. Capture vendor U-Boot -> USB extlinux -> `Linux version 7.3.6-w600d-usb`
   -> USB root -> systemd/LightDM. No second full U-Boot should appear.
4. Observe the internal XFCE display and physical keyboard typing in Terminal.
   Use UART dmesg/journal, DRM sysfs and input devices/evtest for diagnosis.
5. Run `sudo poweroff`, wait for completion, remove USB, then power on and
   observe the original Android UI. Never unplug the running Linux rootfs.

Bring-up defaults: local `linux` desktop/tty1 autologin, UART root autologin,
passwordless sudo; SSH service/socket masked. Run `sudo passwd linux`, remove
`/etc/sudoers.d/90-local-bringup`, and disable unwanted autologin before daily
use. Wi-Fi, Bluetooth, audio, battery, suspend and touchpad are not advertised
as working. No full-system QEMU boot was performed; offline checks cannot
replace physical display/keyboard/fallback acceptance.
