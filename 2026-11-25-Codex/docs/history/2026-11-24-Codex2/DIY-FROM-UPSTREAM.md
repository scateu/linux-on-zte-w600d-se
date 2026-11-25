# DIY procedure: factory W600D SE to removable Ubuntu USB

This is the order for reproducing this board's current Linux build, not a
generic Ubuntu installer. The pinned inputs are Linux 7.3.6 and Ubuntu
24.04.5 ARM64 Base. No claim is made that these are the latest releases on
the day this guide is read. Screen and keyboard have been demonstrated;
trackpad and DHCP are separate unfinished bring-up items.

## 0. Patch the factory U-Boot once

Back up this machine's own `uboot_a`, `uboot_b`, partition layout and A/B
metadata; keep a verified recovery method. Use the established environment
patcher to make its original vendor U-Boot scan USB extlinux before falling
back to Android. Do not replace DDR/SPL/ATF or install Linux in eMMC. Keep
the rescue U-Boot copy stock. Different factory firmware failing the patcher's
checks is a stop condition, not permission to remove its checks.

See `linux-7.3.6-build/FACTORY-UBOOT.md` for the exact bootcmd and procedure.
This stage is already done on the current laptop; do not reflash it for
kernel, DTS or Ubuntu changes.

## 1. Prepare the build computer

Use an ARM64 cross compiler (`aarch64-linux-gnu-gcc`), kernel build tools,
device-tree compiler, filesystem tools and tar. The existing `trash` host
is x86_64, so its ARM64 Ubuntu package installation uses Docker plus QEMU
binfmt; that is a build tool, not how the laptop runs Linux. An ARM64 build
computer can install the ARM64 rootfs packages natively instead.

The working recipe is under `/home/k/codex-workdir-nov-24-2026` on `trash`.
Keep separate clean output directories for a new build; old recipes refuse
to overwrite several completed archives/images.

## 2. Download and unpack the two upstream inputs

- `linux-7.3.6.tar.xz` from kernel.org: the kernel source.
- `ubuntu-base-24.04.5-base-arm64.tar.gz` from Ubuntu: ARM64 userspace files.

Verify both archives against their publishers' SHA256 lists, then unpack.
Ubuntu Base is not a board-ready desktop image and does not supply our
custom laptop kernel. `scripts/prepare-sources.sh` contains the exact URLs
and checksum checks; its proxy is `socks5://192.168.1.5:1080`.

## 3. Apply the board-support patches to Linux

From the extracted Linux source, apply these in order with `patch -p1`
and zero fuzz; stop on a failed hunk:

1. `reference/cloudbook-mainline-6.12/patches/0009-phy-rockchip-naneng-edp.patch`
   adds the RK3568 Naneng eDP PHY.
2. `patches/0002-rk3568-analogix-7.3.patch` adds RK3568 Analogix identification.
3. `patches/0003-kdc-141020khz-vpll.patch` adds the native panel clock rate.
4. `patches/0004-analogix-complete-phy-lanes.patch` supplies lane counts to
   the PHY rate/voltage callbacks; omitting it caused the black screen.

Use our pinned Linux 7.3.6 adaptation, not the reference's complete 6.12
Analogix patch. Do not enable its optional BOE N44 panel voltage override
on this laptop's KDC panel.

## 4. Add this laptop's DTS sources

Copy all three `rk3568-zte-w600d-mainline*.dts` files from the recipe into
Linux `arch/arm64/boot/dts/rockchip/`. The final v3 source includes v2,
which includes the base source; keeping only v3 is insufficient.

They describe the actual 2 GB RAM map, KDC panel, power supplies, PWM2
backlight, keyboard power and VP1-to-eDP connection. They also disable
Linux access to Android's eMMC/SDMMC nodes. Do not borrow the comparison
laptop's RAM size, panel, PWM or I/O voltage map.

Compile **v3**, never boot the intermediate v1/v2 DTBs. DTS is source;
DTB is the compiled binary that U-Boot hands to Linux.

## 5. Configure and build Image, modules and final DTB

Use the saved, validated `config-7.3.6-w600d-usb`, rather than assuming
plain arm64 defconfig enables every required driver. On `trash`, a copy
is in `artifacts/kernel-edp-lanes-fix/`. Important boot/display/input
drivers are built in so USB root and the display do not need an initramfs.

With `KERNEL` and `BUILD` set to absolute source/output paths:

```sh
export ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
mkdir -p "$BUILD"
cp config-7.3.6-w600d-usb "$BUILD/.config"
make -C "$KERNEL" O="$BUILD" olddefconfig
make -C "$KERNEL" O="$BUILD" -j24 DTC_FLAGS=-@ \
  Image modules rockchip/rk3568-zte-w600d-mainline-v3.dtb
```

Outputs are `arch/arm64/boot/Image`, modules, and
`arch/arm64/boot/dts/rockchip/rk3568-zte-w600d-mainline-v3.dtb` under BUILD.
Run the recipe's board and kernel-config validators. Install matching
modules into the rootfs using `modules_install` with `INSTALL_MOD_PATH`
pointing at that rootfs, preserving the `7.3.6-w600d-usb` release name.

## 6. Turn Ubuntu Base into the Ubuntu rootfs

Inside an ARM64 environment, install systemd/systemd-sysv, XFCE, LightDM,
NetworkManager, input/Xorg/Mesa packages and normal Ubuntu utilities.
Create a user, enable the desired desktop/network services, set hostname,
locale and `/etc/fstab`, and install the matching kernel modules.

For your own usable system, set a real user password; the current image's
UART root autologin and passwordless sudo are temporary bring-up settings.
Configure ttyS2 serial login without a competing console getty. If Ethernet
is meant to use NetworkManager/DHCP, verify that the interface is managed;
installing NetworkManager alone did not establish this on the current image.

If using Docker, export it to an ordinary filesystem and remove Docker
runtime markers **after export**, particularly `/.dockerenv`. Normalize
hostname, hosts and resolver files offline. Preserve numeric UID/GID, modes
and symlinks; do not copy the entire rootfs as an ordinary user or blindly
chown every user's home to root. See `ROOTFS-CONTAINER-MARKERS.md`.

## 7. Prepare and populate the USB

Identify the actual USB with `lsblk` before destructive formatting. On the
build host, the authorized Kingston was `/dev/sdb`; `/dev/sda` is the host's
internal SSD and must not be targeted.

Create an MBR layout with p1 starting at 1 MiB, 512 MiB FAT32 and bootable;
p2 starts at 513 MiB and is ext4 using the remaining desired space. Mount
both. Copy the prepared rootfs into p2, preserving numeric ownership/modes.
You can do this directly without writing a padded 32 GB whole-disk image.

On p1, place:

```text
/boot/Image
/boot/rk3568-zte-w600d-mainline.dtb
/extlinux/extlinux.conf
```

The unversioned DTB filename on FAT is a copy of the **compiled v3** DTB.
On p2, put Ubuntu and `/lib/modules/7.3.6-w600d-usb/`. No second U-Boot,
Rockchip raw USB loader or boot.scr is required for this bootflow.

## 8. Write extlinux.conf with the correct root partition

Get the actual p2 PARTUUID with `blkid`. `24c0d202-02` is valid for our
existing image's MBR ID `0x24c0d202`; a newly partitioned USB can have a
different ID. Replace ROOT-PARTUUID below with your actual value.

```text
DEFAULT linux
TIMEOUT 50

LABEL linux
    LINUX /boot/Image
    FDT /boot/rk3568-zte-w600d-mainline.dtb
    APPEND earlycon=uart8250,mmio32,0xfe660000 console=tty1 console=ttyS2,115200n8 root=PARTUUID=ROOT-PARTUUID rootwait rootdelay=5 rw init=/sbin/init clk_ignore_unused pd_ignore_unused cpuidle.off=1 usbcore.autosuspend=-1 loglevel=4
```

Set the matching root PARTUUID in `/etc/fstab` too. These power/clock flags
are the current bring-up configuration, not a claim that suspend or power
management is finished. `init=/bin/sh` is a rescue shell, not the normal
desktop boot configuration.

## 9. Sync, unmount, boot and test

Sync and unmount the USB, insert it in the powered-off laptop, then power on.
Observe original U-Boot loading USB extlinux, the new kernel, Ubuntu and
the display/keyboard. Then shut Linux down cleanly, remove USB and verify
the original Android boots. Physical Android fallback is still an acceptance
test, not something to infer only from the configured bootcmd.

During debugging, replace only the changed Image/DTB/modules/rootfs files;
keep rollback copies. Do not repeatedly write/read the whole 32 GB disk.

## Existing automated equivalent

`scripts/build-display-fixed-image.sh` performs the Linux, Ubuntu and image
phases with the lane fix and post-export marker stripping. It does not
perform the factory eMMC patch or flash the USB. The steps above explain
what its phases do so you can reproduce or modify them yourself.
