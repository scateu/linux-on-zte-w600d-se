# Where this laptop's device tree comes from

Ubuntu does not generate our laptop wiring description. The mainline board
DTS was manually authored/ported from upstream SoC definitions, factory Android
information, previous investigation and actual serial/panel tests.

```text
Factory Android DTB -> readable reference DTS
                           + upstream RK3568 DTSI
                           + board-specific measurements
                       -> manually adapted Linux board DTS
                       -> kernel build -> final DTB -> U-Boot -> Linux
```

## Factory information

Original dumps are in `../recovery/factory-backups/`;
`../reference/factory-device-tree/` is a relative alias to the same evidence:

- `zte-book.dts`: saved slot-B Android tree, as identified in the original notes.
- `device.dtb` and `w600d-backup/device_slot_b.{dtb,dts}`: saved Android blobs/trees.
- `w600d-backup/live.{dtb,dts}`: earlier live-device dump.
- `w600d-backup/resource_a/w600dse-pvt-cs.dts` and its matching named DTB:
  board-specific slot-A resource tree used in vendor bootloader display setup.

A factory blob can be made readable with:

```sh
dtc -I dtb -O dts -o factory.dts factory.dtb
```

This is decompilation, not recovery of the exact original source, comments or
include structure. Vendor bindings and upstream bindings can differ, so a
decompiled Android tree is a reference, not automatically a mainline-ready DTS.
The collected raw partition backups are now preserved losslessly as .gz files;
`RECOVERY.md` explains verified extraction. The original checksum lists describe
raw images, not their compressed bytes. Android super/userdata were not captured,
so the backup collection is not a complete factory-disk image.

## Upstream information

The main board file includes `rk3568.dtsi` from Linux
`arch/arm64/boot/dts/rockchip/`; that includes `rk356x-base.dtsi`.
Copies from the pinned source tree are in `../reference/upstream-linux-7.3.6/`.
They are reading references; the build obtains the complete kernel source
and binding headers rather than attempting to compile this partial excerpt.

The comparison CloudBook project is under
`../build/linux-7.3.6/reference/cloudbook-mainline-6.12/`.
Its PHY implementation and display investigation helped, but its panel,
memory size, GPIOs and I/O supplies are not this laptop's wiring.

## Our source chain

The production include-chain files live at `../build/linux-7.3.6/`:

```text
rk3568-zte-w600d-mainline-v6-wifi-bt.dts
  includes rk3568-zte-w600d-mainline-v5-sdio.dts
    includes rk3568-zte-w600d-mainline-v4-touchpad.dts
      includes rk3568-zte-w600d-mainline-v3.dts
        includes rk3568-zte-w600d-mainline-v2.dts
          includes rk3568-zte-w600d-mainline.dts
            includes upstream rk3568.dtsi
```

**Build v6 for display, trackpad and Wi-Fi/Bluetooth.** v3 supplies the corrected
I/O supply choices and display clock; v4 adds the factory-matched I2C4
touchpad and power/reset sequence. v5 enables the verified SDIO radio at
25 MHz; v6 adds GPIO2_B7 Bluetooth reset-enable. eMMC remains disabled.
v1/v2 are not boot targets. The display-only wrapper retains v4 as its baseline.

Kernel build target:

```sh
make -C "$KERNEL" O="$BUILD" ARCH=arm64 \
  CROSS_COMPILE=aarch64-linux-gnu- DTC_FLAGS=-@ \
  rockchip/rk3568-zte-w600d-mainline-v6-wifi-bt.dtb
```

For new Wi-Fi images, the compiled v6 binary is installed on FAT as
`/boot/rk3568-zte-w600d-mainline.dtb`; extlinux points to that unversioned
filename. Renaming the binary does not change which DTS generated it.

The live debug USB instead retains its original v3 DTB and uses a distinct
v6 filename for normal boot, with `/boot/Image.wifi-20261125`. See
`TRACKPAD-AND-WIFI.md` for actual HID ID, input events, radio patches,
successful scans and rollback paths. DTS alone cannot replace those patches
or the matching modules and firmware in the Ubuntu rootfs.

## Verified board facts encoded in our sources

| Item | This W600D SE |
| --- | --- |
| SoC/RAM | RK3568, 2 GB; actual reserved-memory-aware RAM map retained |
| Panel | KDC KD140N1930A02, EDID 1920 x 1080, 141020 kHz pixel clock |
| Panel supply | GPIO2_D5 |
| Panel enable | GPIO2_D4 |
| Backlight enable | GPIO2_D3 |
| Backlight PWM | PWM2m1 / GPIO0_B6, 25000 ns period; not CloudBook PWM8 |
| Bring-up brightness | 200/255 |
| Keyboard | USB 258a:0001, power GPIO3_A3 |
| Display path | VP1 to eDP |
| pmuio2 supply | LDO6 / vcc3v3_pmu, 3.3 V |
| vccio1 / vccio3 | LDO4 / LDO5 |
| vccio4 | DCDC5, 1.8 V |
| vccio5/6/7 | SWITCH1, 3.3 V |

Panel EDID is preserved as `../build/linux-7.3.6/panel-edid.base64`.
Linux eMMC/SDMMC nodes and CPU DVFS are disabled for this removable bring-up.
Power/clock-preservation flags remain intentional bring-up settings; suspend,
DVFS and full peripheral support are not claimed complete.
