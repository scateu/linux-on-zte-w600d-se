# W600D SE partition and hardware evidence

These are recorded observations from this laptop, not a universal layout
for every factory firmware. Confirm a new laptop's GPT, board identity and
active slot before applying any bootloader patch.

**Current goal: leave Android and its partition table intact.** The original
research `partitions.md` section 5 proposed wiping Android for eMMC Linux.
That proposal is historical and explicitly **not our removable-USB plan**.
The same warning applies to old logo/recovery/Linux-install notes that discuss
erasing Android or replacing the eMMC layout.

## Original eMMC layout

Recorded eMMC: `A3A551`, 60,620,800 sectors of 512 bytes, GPT.
Numbers below come from the saved partition dump and original image analysis.

| Part | Start sector | Recorded size | Name / contents |
| --- | ---: | --- | --- |
| raw | 64 | within first 4 MiB | Rockchip DDR/SPL/idbloader |
| p1 | 8192 | 4 MiB | security / secure storage |
| p2 | 16384 | 4 MiB | uboot_a, FIT, observed distro fallback support |
| p3 | 24576 | 4 MiB | uboot_b, different factory build; not interchangeable blindly |
| p4 | 32768 | 4 MiB | trust_a; saved image all zeros |
| p5 | 40960 | 4 MiB | trust_b; saved image all zeros |
| p6 | 49152 | 4 MiB | misc, A/B metadata and boot control block |
| p7 | 57344 | 4 MiB | dtbo_a |
| p8 | 65536 | 4 MiB | dtbo_b |
| p9 | 73728 | 1 MiB | vbmeta_a |
| p10 | 75776 | 1 MiB | vbmeta_b |
| p11 | 77824 | 160 MiB | boot_a, Android kernel/ramdisk/RSCE |
| p12 | 405504 | 160 MiB | boot_b, other Android slot |
| p13 | 733184 | 1.5 GiB | backup, recorded empty ext4 |
| p14 | 3878912 | 384 MiB | cache |
| p15 | 4665344 | 16 MiB | metadata |
| p16 | 4698112 | 1 MiB | baseparameter, vendor display modes |
| p17 | 4700160 | 32 MiB | logo, tested power-on BMP copies |
| p18 | 4765696 | 32 MiB | zteparameter, per-device factory data |
| p19 | 4831232 | about 5 GiB | super, Android dynamic partitions; **not backed up** |
| p20 | 15325184 | about 21.6 GiB | userdata; **not included in these backups** |

ATF/OP-TEE were observed inside the U-Boot FIT; empty trust images do not
mean those runtime components are absent. The primary/backup GPT and early
eMMC region were also saved. This is **not a complete factory-disk backup**.

## Hardware mapping used by the tested Linux tree

| Item | Evidence / current setting |
| --- | --- |
| SoC / RAM | RK3568; 2 GiB with firmware-reserved holes described in the DTS |
| Factory board selection | Saved RSCE variant w600dse-pvt-cs; recorded SARADC ch1/ch4 938/779 |
| Panel | Native 1920 x 1080 EDID; tested pixel clock 141.020 MHz |
| Display pipeline | VOP2 VP1 -> Analogix eDP -> panel; Naneng eDP PHY |
| Display clocks | VPLL 564.080 MHz, DCLK_VOP1 141.020 MHz in v3 DTS |
| Panel power / enable | GPIO2_D5 / GPIO2_D4, active high |
| Backlight | PWM2 mode 1, 25,000 ns period; GPIO2_D3 enable |
| Keyboard | USB HID 258a:0001; GPIO3_A3 power hog high |
| USB power | GPIO3_A0 host supply, GPIO0_C4 other USB/OTG supply |
| Diagnostic UART | uart2 / ttyS2, 115200 8N1; bridge tcp://localhost:5000 |
| USB Ethernet | 0fe6:9900, cdc_ether; managed DHCP confirmed across November 25 reboot |
| Trackpad | I2C4 0x2c, HID 093a:0255; GPIO3_B4 power, GPIO3_A1 reset-enable, GPIO3_B3 low-level IRQ |
| Wi-Fi/Bluetooth | Live SDIO 037a:7603 / 037a:7663; MediaTek MT7663S, despite generic factory Unisoc nodes |

These pins are this board's current authored settings, not proof that every
peripheral is finished. The related CloudBook project is a comparison source,
not a pin-for-pin substitute. `CURRENT.md` records what the user actually
confirmed. November 25 added trackpad input, Ethernet DHCP, two-band Wi-Fi scans
and Bluetooth controller initialization;
full desktop/right-click and unplugged Android fallback still need acceptance.

## Where the descriptions came from

The canonical factory evidence is `../recovery/factory-backups/`:

- `w600d-backup/partitions.txt`, `getprop.txt`: original device metadata.
- `device.dtb`, `zte-book.dts`: saved Android device-tree evidence.
- `w600d-backup/device_slot_b.{dtb,dts}`, `live.{dtb,dts}`: slot/live dumps.
- `w600d-backup/resource_a/`: extracted factory resource DTBs and charging BMPs;
  matching w600dse-pvt-cs DTS/DTB retained.
- `../logs/ref-2026-11-23/04-u-boot-原厂printenv.txt`: saved factory environment.
- `../bootloader/usb-uboot/_RESEARCH/docs/partitions.md`: full original offsets,
  boot-image/RSCE/misc analysis; its erase proposal is historical only.

Ubuntu does not generate the board wiring. We decompile factory DTBs for
reference, combine that information with upstream RK3568 DTSI and measurements,
and manually port a mainline board DTS. `DEVICE-TREE.md` explains the include
chain and compilation; `../build/linux-7.3.6/` keeps the complete authored DTS
include chain, EDID, eDP patches and board-adapted radio patches.

## Backups are compressed, not discarded

Original raw .img/.bin files are now lossless .gz files; identical backups
share one canonical compressed copy via relative aliases. `RECOVERY.md`
explains verified extraction. Both Android boot-slot images are retained:
their original SHA256s differ, so they were **not** deduplicated as if equal.
Per-device security/factory data must not be transplanted to another machine.
