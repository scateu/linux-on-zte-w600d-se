# W600D USB Ubuntu build — November 24, 2026

**Current build entry point:** `BUILD-VERIFIED.md` and
`scripts/build-verified-image.sh`. Older START-HERE/BUILD-READY instructions
and older numbered scripts are retained as research history, not alternative
production bootflows. The current recipe uses minimal Docker build contexts
and offline hostname/hosts/resolver normalization after export.

## Goal and confirmed boundary

```text
Factory W600D SE / RK3568 / 2 GB
  -> its own eMMC vendor U-Boot, patched to scan USB first
  -> USB FAT /extlinux/extlinux.conf
  -> Linux Image + this board's DTB
  -> USB ext4 Ubuntu rootfs -> local console and XFCE desktop

Power off -> remove USB -> power on -> original Android boot path
```

No second/mainline USB U-Boot, USB boot.scr, Android boot image or eMMC Linux
installation is required. Do not copy another laptop's whole bootloader image.

The previous BSP 5.10 test verified physical keyboard events and white pixels
on this laptop. A successful 7.3.6 build does not establish hardware success:
the new kernel, desktop, keyboard and Android fallback must be tested after
flashing the new USB. Wi-Fi, Bluetooth, audio, battery and suspend are outside
this first display/keyboard acceptance and are not advertised as working.

## Selected versions

- Linux **7.3.6**, kernel.org's latest stable on November 24, 2026, released
  November 23. The newer 7.4-rc4 is a release candidate, not used here.
- Ubuntu **24.04.5 LTS ARM64** official Ubuntu Base archive, expanded with normal
  Ubuntu packages into a complete XFCE/systemd desktop installation.
- Source and base archive checksums are checked against their publishers'
  HTTPS checksum files. These checks are not a claim of GPG signature validation.
- Exact kernel config and package-version list are saved. This is an auditable,
  repeatable build recipe, not a claim of bit-for-bit reproducibility: apt uses
  current Noble repositories and filesystem timestamps vary.

## Build host and prerequisites

Build on `trash` (x86_64 Ubuntu), in:

```sh
ssh trash
cd /home/k/codex-workdir-nov-24-2026
export ALL_PROXY=socks5://192.168.1.5:1080
export APT_PROXY=socks5h://192.168.1.5:1080
```

Curl uses the SOCKS5 proxy. Apt inside the ARM64 build container uses SOCKS5h,
which resolves repository hostnames through the proxy. No proxy setting is
left in the completed laptop rootfs.

Required host tools: ARM64 GCC/binutils, make, flex, bison, bc, libssl-dev,
libelf-dev, patch, rg, dtc/fdtget, python3, curl, xz, tar, fakeroot, mtools,
dosfstools, e2fsprogs, util-linux/sfdisk, zstd and Docker. The host's existing
QEMU ARM64 binfmt handler has the `F` flag and executes the ARM64 Ubuntu build
containers. No change to host binfmt or package installation was needed.

Docker must already be usable by the build user. Source, recipes, output,
rootfs export and disk images live in this workdir; Docker uses its existing
normal layer/cache storage. No sudo is required to assemble a regular image
file. Building the rootfs container does not mean the laptop runs containers:
`docker export` supplies an ordinary on-disk Ubuntu installation.

## Copy the build inputs from the Mac workspace

```sh
rsync -a 2026-11-24-Codex2/linux-7.3.6-build/ \
  trash:/home/k/codex-workdir-nov-24-2026/
rsync -a ref/eastwoodnet_cloudbook-air-mainline-linux/mainline-6.12/ \
  trash:/home/k/codex-workdir-nov-24-2026/reference/cloudbook-mainline-6.12/
```

The required reference input is patch
`reference/cloudbook-mainline-6.12/patches/0009-phy-rockchip-naneng-edp.patch`.
It adds the missing Naneng eDP PHY. Its optional BOE N44 override remains
inactive: this ZTE board does not set `zte,edp-v12-v13`.

## One-command build

```sh
JOBS=24 bash scripts/build-verified-image.sh
```

This downloads/verifies the source and Ubuntu archive, imports the ARM64
build base, builds Ubuntu packages and the kernel, finalizes the board DTB,
exports Ubuntu, and assembles/checks the disk image. It never flashes a disk.
It refuses to overwrite an existing final disk image; keep completed output
in a separate archive before deliberately rebuilding.

Individual phases, in order:

```sh
bash scripts/prepare-sources.sh
bash scripts/build-userspace-v2.sh
bash scripts/build-kernel-v2.sh
bash scripts/finalize-kernel-symbols.sh
bash scripts/build-desktop-rootfs-v2.sh
bash scripts/assemble-image.sh
```

**Do not boot or ship intermediate v1/v2 DTBs.** The finalization phase applies
the audited I/O supply mapping and the native panel clock, validates them,
and replaces the staged DTB with the validated v3 result. The unversioned
early kernel/rootfs scripts and Dockerfile are superseded experiments, not
the supported build entry points. Existing-file edits were denied by the
Mac's file access policy, so corrected revisions were saved as new files.

## Board-specific changes

- Preserve the tested 2 GB RAM map, including the vendor firmware holes.
- Panel is **KDC KD140N1930A02**, read from live EDID; 1920x1080, 141020 kHz.
  EDID is saved in `panel-edid.base64`, not borrowed from the BOE reference.
- Naneng eDP PHY at 0xfdcb0000 and Analogix controller at 0xfe0c0000.
- Enable VP1 -> eDP -> generic EDID-driven panel, VOP2/IOMMU and PWM backlight.
- GPIO2_D5 panel power, GPIO2_D4 panel enable, GPIO2_D3 backlight enable.
- Backlight is **PWM2m1/GPIO0_B6**, 25000 ns, not reference-board PWM8.
- GPIO3_A3 hog supplies the SINO WEALTH 258a:0001 USB keyboard.
- Enable both relevant USB xHCI blocks, USB2 PHYs, USB storage and USB HID.
- Original IO supply mapping: pmuio2 -> LDO6/vcc3v3_pmu (3.3 V), vccio1 ->
  LDO4/vccio_acodec, vccio3 -> LDO5/vccio_sd, vccio4 -> DCDC5/vcc_1v8,
  vccio5/6/7 -> SWITCH1/vcc_3v3. Validation checks every phandle.
- Add RK3568 identification to upstream Analogix helpers/chip table. Do not
  blindly apply the reference's old 6.12 bridge patch: much of generic PHY
  configuration is already present in 7.3.6 and interfaces changed.
- Add a fractional VPLL table rate of 564080000 Hz. Parameters yield
  `24 MHz * (47 + 111848/2^24) / 2`, approximately 564.08 MHz, divided by four
  for the panel's 141.02 MHz pixel clock. Actual clock/link behavior still
  requires hardware measurement; this is not a report of a tested 7.3.6 mode.
- Build storage, eDP, backlight, HID, serial and framebuffer console in, so
  root mount and local text display do not depend on an initramfs.
- Disable eMMC/SDMMC in DT. Ubuntu cannot mount Android partitions through
  these controllers. Keep CPU DVFS disabled and the known bring-up clock/PD
  ignore flags and `cpuidle.off=1` until power management is validated.

## Normal Ubuntu system configuration

Default boot uses `/sbin/init`, not `/bin/sh`. Systemd starts LightDM/XFCE,
NetworkManager and local tty1/serial gettys. The local desktop and tty1
automatically log in as **linux**; the diagnostic UART logs in as root.
The linux user has passwordless sudo for bring-up. Both SSH service and socket
are disabled and masked in the final image.

Before treating it as secured daily-use media:

```sh
sudo passwd linux
sudo rm /etc/sudoers.d/90-local-bringup
```

Then remove unwanted local/serial autologin overrides. Only enable SSH after
setting a strong password or authorized key and generating fresh host keys.
These intentional development-image defaults are documented on the desktop
in `FIRST-STEPS.txt`.

## Disk image layout and outputs

```text
artifacts/w600d-ubuntu-xfce-7.3.6-20261124.img       6 GiB regular disk image
artifacts/w600d-ubuntu-xfce-7.3.6-20261124.img.zst   compressed distribution copy
artifacts/usb-image-SHA256SUMS                     raw/compressed checksums

MBR disk ID: 24c0d202
p1: start 1 MiB, 512 MiB FAT32, W600D_BOOT, PARTUUID 24c0d202-01
p2: start 513 MiB, remainder ext4, W600D_ROOT, PARTUUID 24c0d202-02
```

Use an **8 GB or larger** USB for the portable image. For the authorized
Kingston on trash, `assemble-capacity-image.sh 30943995904` grows a regular-file
copy offline to 29510 MiB: 512 MiB FAT32 boot and 28997 MiB ext4 root. See
USB-CAPACITY.md; the portable 6 GiB image remains available separately.
Flashing destroys the new USB's current partition table and data. It does
not copy a Rockchip loader to USB's raw boot sectors: the vendor eMMC loader
is intentionally retained.

FAT contains only `boot/Image`, the final board DTB and
`extlinux/extlinux.conf`. Normal XFCE, text-only and read-only emergency-shell
entries are provided. There is no chain-loading boot.scr or USB U-Boot.
Rootfs contains the matching 7.3.6-w600d-usb modules. FAT is mounted read-only
at `/media/boot`; root is Ubuntu ext4. Build logs are in `logs/`.

## Flashing: only after identifying the new USB

Plug the new drive into **trash**, not the laptop. Inspect:

```sh
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL,SERIAL,TRAN
python3 scripts/flash-usb-native.py \
  artifacts/w600d-ubuntu-xfce-7.3.6-20261124.img /dev/disk/by-id/usb-EXACT_ID
```

That command is a dry run without `--confirm-erase`. It requires a whole USB
disk, a stable serial, sufficient capacity and no mounted descendant. Never
substitute the host's internal `/dev/sda` based on another machine's example.
Unmount only this USB's volumes through the desktop/udisksctl first.

After confirming the displayed model, serial, size and resolved device,
repeat with the exact confirmation string printed by the dry run:

```sh
python3 scripts/flash-usb-native.py IMAGE EXACT_USB \
  --expected-sha256 EXACT_IMAGE_SHA256_FROM_MANIFEST \
  --confirm-erase /dev/CONFIRMED_DEVICE:CONFIRMED_SERIAL
```

The native writer uses cached Linux amd64 tooling with only the selected
block device and read-only image exposed. It does not require a privileged
container or passwordless sudo, but Docker-group access to the root daemon
is itself administrator-level access. It hashes the source before writing,
fsyncs, then compares an uncached direct-read SHA256 of the entire image-sized
disk region with the manifest. See FLASH-NATIVE.md for exact commands and
safeguards. Save that read-back result before ejecting. Disk writing is an explicit,
separate operation; build scripts cannot accidentally flash a device.

## Laptop acceptance procedure

1. Keep the old known-working USB intact. Arrange the sole logged UART
   connection before power-on; do not open a competing serial client.
2. Shut down the laptop before changing USB. Insert the newly flashed drive
   in the known-working boot USB port and power on.
3. Log must show eMMC vendor U-Boot finding USB extlinux, the new Image/DTB,
   `Linux version 7.3.6-w600d-usb`, USB root mount and systemd startup. No second
   full U-Boot should appear.
4. Confirm the internal screen displays XFCE, open Terminal with the physical
   keyboard, type a sentence, and verify touchpad/cursor separately if desired.
5. On serial, inspect `uname -a`, `cat /proc/cmdline`, `journalctl -b`,
   `/sys/class/drm/*eDP*/status`, `/proc/bus/input/devices` and evtest.
6. Run `sudo poweroff`, wait for shutdown, remove USB, then power on again.
   Confirm the original Android UI appears. Do not unplug the running rootfs.

If display fails but UART works, keep the log and diagnose deferred probes,
eDP AUX/EDID, link training, framebuffer registration, PWM and Xorg errors;
do not repeatedly reboot or flash eMMC to guess at a fix. The text-only
extlinux entry avoids LightDM; the emergency shell keeps root read-only but
runs as PID1, so never exit it or send Ctrl-D.

The vendor U-Boot writes its own retry/boot metadata during normal starts.
"Android retained" means no Linux install or explicit flash into Android
partitions, not a promise that every eMMC metadata byte remains unchanged.
