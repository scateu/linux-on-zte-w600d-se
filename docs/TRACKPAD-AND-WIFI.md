# Trackpad and wireless bring-up — November 25, 2026

## Initial live observations

- Laptop kernel: `7.3.6-w600d-usb`, build #3, existing working display.
- USB Ethernet is bound to `cdc_ether`; DHCP works. Address observed:
  `192.168.1.219/24`, default gateway `192.168.1.1`.
- Only I2C0/PMIC and the eDP AUX I2C adapter existed. I2C4 was disabled.
- Input devices were the three USB keyboard interfaces and RK805 power key.
- No MMC/SDIO device was enumerated; wireless controller remained disabled.
- USB root: `/dev/sda2`; FAT boot: `/dev/sda1` mounted read-only at
  `/media/boot`. Rediscover device identity rather than trusting these names.
- Main SSH service is masked. A separate key-only diagnostic SSH listener on
  port 2222 uses keys/configuration under `/run`, not persistent login changes.
- `/.dockerenv` remains present; normal hardware-mode reboot is still needed.

## Trackpad evidence and proposed v4 tree

The selected factory `w600dse-pvt-cs` DTS describes:

- I2C4 at `fe5d0000`, mux `i2c4m0_xfer`.
- HID-over-I2C device address `0x2c`, HID descriptor register `0x20`.
- Interrupt GPIO3_B3, active-low level; factory pull-up.
- `gpio-power`: GPIO3_B4, active high.
- `gpio-reseten`: GPIO3_A1, active high.

These touchpad pins match the pinned CloudBook reference; its keyboard power
pin and panel differ. Live Wi-Fi IDs later proved identical. Its mainline DTS models the sequence
using two chained fixed regulators: GPIO3_B4 high, wait 10 ms, then GPIO3_A1
high, wait before reading the HID descriptor. This models enable/reset lines;
the second regulator is not evidence of a separate physical 1.8 V supply.

`build/linux-7.3.6/rk3568-zte-w600d-mainline-v4-touchpad.dts` includes the
hardware-tested v3 display tree and adds only this power chain and I2C4 device.
It does not enable eMMC or Wi-Fi. The existing kernel contains `i2c_hid_of`
and `hid_multitouch` modules, so the first test needs only a new DTB.

## Build only the new DTB

On `trash`, inside the existing `/home/k/codex-workdir-nov-24-2026` recipe:

```sh
cp rk3568-zte-w600d-mainline*.dts src/linux-7.3.6/arch/arm64/boot/dts/rockchip/
make -C src/linux-7.3.6 O="$PWD/out/kernel-7.3.6" \
  ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- DTC_FLAGS=-@ \
  rockchip/rk3568-zte-w600d-mainline-v4-touchpad.dtb
```

Keep the old DTB and rescue boot entries. Stage the new DTB under a distinct
FAT filename and point only the normal desktop entry to it. Verify hashes,
sync and remount FAT read-only before reboot. Do not overwrite Image, modules,
the partition table, factory U-Boot, or any Android/eMMC partition for this test.

## Factory wireless descriptions are not hardware IDs

The selected factory DTS enables `unisoc,marlin3`, `sprd,sc2355-WiFi` and
`sprd,mtty`; its firmware path is `/vendor/etc/firmware/wcnmodem.bin`.
This initially suggested Unisoc, but the v5 live SDIO result disproves that
hypothesis: function 1 is **037a:7603**, function 2 is **037a:7663**, exactly
the CloudBook MediaTek MT7663S Wi-Fi/Bluetooth pair. Use the live IDs, not
the generic factory platform nodes, to choose the driver.

The next step is the CloudBook isolated mt76 driver and matching MediaTek
firmware. Factory nodes alone did not prove the chip ID or compatible firmware.
Do not scan the PMIC bus, force a GPIO
already owned by another device, or load unmatched vendor modules into Linux 7.3.6.

## Sources and evidence

- Factory: `recovery/factory-backups/w600d-backup/resource_a/w600dse-pvt-cs.dts`.
- Pinned CloudBook: `build/linux-7.3.6/reference/cloudbook-air-mainline-linux/`,
  especially `mainline-6.12/rk3568-ecloudbook-air-24rtw.dts`,
  `rk3568-ecloudbook-air-24rtw-v11-touchpad.dts`, and the top-level README.
- Kernel: `Documentation/devicetree/bindings/input/hid-over-i2c.yaml` and
  `drivers/hid/i2c-hid/i2c-hid-of.c` in the existing 7.3.6 build-host source.
- Raw UART: `logs/live-20261125-input-network/` (ignored by Git).

Hardware acceptance and further changes must be recorded here after each test.

## v4 reboot result

- Factory U-Boot loaded the new v4 filename from USB; Image remained identical.
- I2C4 enumerated at `4-002c`. The actual HID ID is **093a:0255**, not the
  CloudBook's 0911:5288. `hid_multitouch` bound without any new kernel patch.
- Mouse and touchpad appeared as `/dev/input/event4` and `/dev/input/event5`.
- Xorg/libinput registered the touchpad. A 30-second evtest recorded finger
  movement, contact/release and physical left-button press/release events.
- libinput warns that the clickpad advertises BTN_RIGHT; it still registers
  the device. Investigate actual right-click behavior before adding a quirk.
- Container markers were backed up and removed. After reboot,
  `systemd-detect-virt` reports `none`; udev and ttyS2 are active and
  console-getty is inactive. Normal hardware mode is restored.
- Ethernet DHCP did not survive reboot: Ubuntu's library default
  `10-globally-managed-devices.conf` explicitly excludes Ethernet from
  NetworkManager. The new rootfs override permits Ethernet as well as its
  existing Wi-Fi/mobile types. A persistent DHCP connection is the next test.
- The laptop clock is wrong: it read August 6, 2017 during this November 25,
  2026 experiment. Thus the actual rollback directory is
  `/root/w600d-debug-backups/20170806T120728-touchpad-v4`, despite the real date.
  Network time synchronization must be checked after DHCP is restored.

The fresh-build finalizer now selects v4 while retaining the canonical generic
DTB filename used by new images. The live debug USB uses a separate v4 filename
and unchanged old rescue DTB. The rootfs overlay includes the narrow Ethernet
management fix and CloudBook-style libinput tap-to-click setting.

## Guarded live USB installation

`scripts/install-touchpad-dtb-live.py` runs on the laptop, not on `trash`.
It checks the recorded Kingston serial/capacity, common USB parent of root/FAT,
read-only FAT mount, candidate SHA256 and the exact normal desktop FDT line.
Without `--apply` it validates only. With `--apply` it saves rollback files on
USB ext4, stages the DTB and config with checksums/fsync, changes only the
normal desktop FDT filename, syncs and restores FAT read-only. Rescue entries
keep the untouched original DTB. It never opens a block device for writing.

After transferring the candidate into RAM, run on the laptop:

```sh
python3 /run/install-touchpad-dtb-live.py /run/w600d-codex-ssh/trackpad-v4.dtb \
  --sha256 e6bad7de98cda606c75740f2386e7717cc56b59a2a580ae7984ac43707ccc8df
```

Review the dry run, then repeat with `--apply`. The optional
`--normalize-container-markers` backs up/removes only container detection
markers from this USB rootfs. Systemd's already-selected mode changes only
after reboot; keep the working tty1 and ttyS2 login units.

## SDIO-only v5 diagnostic candidate

The v5 source includes v4 and enables only the factory Wi-Fi `sdmmc1` host
at `fe2c0000`. eMMC (`sdhci`) and removable-card (`sdmmc0`) remain disabled.
It uses factory/CloudBook-matching GPIO0_A5 active-low power, GPIO0_B5
active-high reset and the RK809 second 32 kHz output, with a 200 ms delay.
The driver's rfkill GPIO parser honors the factory active-low vbat flag.

Start at 25 MHz in legacy mode, suppressing CMD11/UHS. The existing v3/v4
1.8 V VCCIO4 wiring remains unchanged; no PMIC voltage change is introduced.
This is an enumeration experiment, not a Wi-Fi acceptance result. It does
not install a driver or firmware and does not change the fresh-image v4 default.
The live updater accepts `--variant sdio-v5` to stage v5 from a current v4
desktop boot entry, retaining its prior DTB and the original rescue entries.

Before SDIO enumeration, Unisoc driver source was inspected on `trash`:
`reference/linux-orangepi-uwe5622/drivers/net/wireless/uwe5622`, from
Orange Pi `orange-pi-6.6-rk35xx`, commit
`122b41d84d018af909a766e48f3f90cbea9868e0`.
The 6.18 branch lacked this driver. The 6.6 driver has separate BSP, Wi-Fi
and Bluetooth modules; it is not a binary-compatible Linux 7.3.6 module.
Its SDIO table uses `(0, 0)` and its chip-ID logic distinguishes Marlin3 and
Marlin3-lite. Its Linux 7.3.6 compile failed on removed legacy GPIO/wakeup
APIs. It was never installed. The actual MediaTek IDs make this driver
irrelevant; do not continue that port for this laptop.

The v5 boot enumerated both MediaTek functions at 25 MHz without CMD11 and
preserved trackpad, keyboard, DHCP and network time. Tap-to-click configuration
was loaded by Xorg after reboot. DHCP automatically returned as
`192.168.1.220/24`, proving the persistent NetworkManager fix across reboot.
No MediaTek driver or firmware was present on this USB at that point.
Rollback to v4: `/root/w600d-debug-backups/20261125T124353-sdio-v5`.

## MediaTek kernel build and first v6 boot

The official Linux-firmware project supplies the two requested files:

| File | SHA256 |
| --- | --- |
| `mediatek/mt7663_n9_v3.bin` | `d8b8488f37f65e41ded9a911950afb000d236b36e5aa94ad9650ad0c3a86fd45` |
| `mediatek/mt7663pr2h.bin` | `534f2152f9b0f48dfcec9c1727b0bab9a3727a655d76d5ec818cc39a55602336` |

Downloads are under `downloads/mediatek-20261125/` on `trash`. The Armbian
firmware repository did not contain these files; do not claim it supplied them.
Exact provenance is in `reference/download-metadata/mt7663s-firmware.json`:
official revision `16a7a3f83c2f83239b0395faac8da4acbbbb0ffe`, with the manufacturer's
`LICENSES/LICENCE.mediatek` retained. The license SHA256 is
`a90d3f66704d85889945fec5525ea77622549da83aced1aac99828383f8f1805`.
The raw GitLab license URL returned HTTP 403; its pinned repository-files API
worked. `scripts/fetch-mt7663-firmware.sh` verifies all three hashes.

CloudBook patches 0005, 0011, 0012 and 0013 apply to Linux 7.3.6 using
`git apply`. GNU patch misinterprets the zero-index new-file headers in 0005;
use Git's parser rather than force-reversing it.
Patch 0006 needs one context adaptation: Linux 7.3.6 replaced
`device_init_wakeup(dev, true)` with `devm_device_init_wakeup(dev)` in
`btmtksdio_probe`. The adapted patch is
`patches/0005b-mt7663-combo-linux-7.3.patch`; the original reference is untouched.

`scripts/build-wifi-kernel.sh` uses a separate output/artifact directory and
release **7.3.6-w600d-usb-wifi**, preserving the working kernel/module tree.
It enables modular MT7663S/BT_MTKSDIO and shared combo lifecycle coordination.
v6-wifi-bt includes v5 and adds the factory GPIO2_B7 Bluetooth reset-enable
regulator, matching the CloudBook power model. SDIO stays at conservative
25 MHz for the first radio test; eMMC remains disabled.

After preparing the existing display-patched 7.3.6 source, apply in this order:

```sh
git apply --directory=src/linux-7.3.6 \
  reference/cloudbook-mainline-6.12/patches/0005-mt76-mt7663s-w103d-isolated.patch
git apply --directory=src/linux-7.3.6 patches/0005b-mt7663-combo-linux-7.3.patch
for patch in \
  0011-mt76-mt7663s-w103d-sanitize-wiphy.patch \
  0012-mt76-mt7663s-w103d-fix-band-switch-disconnect.patch \
  0013-mt76-mt7663s-w103d-tx-ampdu-and-sdio-throughput.patch; do
  git apply --directory=src/linux-7.3.6 \
    "reference/cloudbook-mainline-6.12/patches/$patch"
done
git apply --directory=src/linux-7.3.6 patches/0005c-mt7663-w600d-board-guards.patch
JOBS=32 bash scripts/build-wifi-kernel.sh
```

Run these patches once on the prepared source; check applicability first.
The reference's 0007 mac80211 rate-reporting patch is not required for this
initial radio test and is not applied. Build success alone is not radio acceptance.

The first v6 reboot used `7.3.6-w600d-usb-wifi #1`, built November 25 at
14:40:06 CST. Display remained connected at 1920x1080; Xorg/libinput retained
the trackpad; Ethernet DHCP and NTP recovered; console-getty remained inactive.
Bluetooth exposed powered controller `A8:4F:A4:22:2D:E4`, but Wi-Fi was
unavailable. The generic MCU path logged a patch-semaphore failure and a
misleading fallback request for `mt7663pr2h_rebb.bin`, despite the primary
firmware being installed and hash-verified.

Root cause: the CloudBook patches activate only for `zte,w103d`. Our actual
board compatible is `zte,w600d-se`; compiling those patches alone did **not**
activate the isolated transport or combo coordinator. New
`patches/0005c-mt7663-w600d-board-guards.patch` extends the five relevant checks
to this specific board, including MCU transport, VHT policy and Bluetooth
lifecycle coordination. It preserves other boards' behavior and does not
pretend our panel or whole board is the CloudBook. Apply it **after** reference
0013, or use `scripts/apply-wifi-patches.sh` once on display-patched source.

Initial v6 rollback records:
- `/root/w600d-debug-backups/20261125T145515-wifi-support`: support install record.
- `/root/w600d-debug-backups/20261125T145740-wifi-bt-v6`: prior v5 config/DTB.
- Normal FAT Image is `/boot/Image.wifi-20261125`; original `/boot/Image` and
  original v3 rescue entries remain unchanged.

The boot FAT mount also missed its 10-second device timeout during slower
coldplug. Mounting it read-only after startup worked. The saved overlay now
uses 90 seconds; this does not change USB identity, partitioning or bootflow.

## Reproduction and file-only deployment

For a **new, empty recipe directory**, run `scripts/build-wifi-image.sh`.
It builds the existing display baseline, applies the six radio patches in
order, builds v6 and its distinct module release, fetches pinned firmware,
integrates the Ubuntu overlays/tools, strips Docker markers and assembles a
6 GiB regular-file image named `w600d-ubuntu-xfce-7.3.6-wifi-20261125.img`.
It never accesses a physical USB or eMMC. This wrapper is syntax-checked;
the full new image has not yet been built/flashed end-to-end.

For an already display-patched source tree, apply the radio patches once:

```sh
bash scripts/apply-wifi-patches.sh
JOBS=32 bash scripts/build-wifi-kernel.sh
bash scripts/fetch-mt7663-firmware.sh
```

Do not repeat patch application on the working `trash` tree. Its patches are
already applied. `artifacts/kernel-wifi/` contains Image, v6 DTB, config,
System.map, kernelrelease, matching module tar and SHA256SUMS. Module packaging
excludes absolute `build`/`source` links. Firmware artifacts are separate.

For the recorded Kingston **live debug USB only**, stage those artifacts under
`/run/w600d-wifi-20261125/`, including `mediatek/` and `LICENSES/`. Run the
support installer with its module-tar hash (dry run, then `--apply`):

```sh
python3 /run/install-wifi-support-live.py /run/w600d-wifi-20261125 \
  --modules-sha256 MODULE_ARCHIVE_SHA256
```

Next run `install-touchpad-dtb-live.py` with `--variant wifi-bt-v6`, the v6
DTB/hash and `--image`/`--image-sha256` (dry run, then `--apply`). These guarded
installers refuse other USB identities and existing destination names; they
are **not** generic flashing tools. The boot updater checks matching modules
and both pinned firmware hashes before switching the normal entry.
Do not extract arbitrary module archives as root or overwrite an existing
release without specific backup/validation. Reboot only after sync and FAT
read-only remount; collect serial, probe, scan and input regression results.

## Board-guard update: successful radio boot

Only `mt7663s.ko` and `btmtksdio.ko` needed recompilation for 0005c. They were
hash/ARM64-vermagic checked, backed up and replaced on the USB root, followed
by depmod. The Image and v6 DTB hashes remained identical. Rollback:
`/root/w600d-debug-backups/20261125T1512-radio-board-guards/` also retains the
prior fstab. Final module archive SHA256 is
`1d720ce99755c9626ed07775cdbad482c3593a9245b3339cc6cf1e538c8a092c`.

The next clean reboot confirmed:
- Combo Bluetooth setup and HCI initialization both returned **0**.
- Isolated vendor RX-enhance/WHISR transport activated for our board.
- N9 firmware **3.1.1**, build `20200604161656`, loaded successfully.
- Firmware eFuse calibration completed and stale MCU responses were purged.
- NetworkManager exposes `wlan0` as Wi-Fi, disconnected and ready for association.
- An active scan returned many access points on **both 2.4 GHz and 5 GHz**.
- Ethernet DHCP, display/input and the read-only FAT mount survived reboot;
  systemd's failed-unit list is empty.

This proves initialization and scanning, **not** authenticated association,
Wi-Fi DHCP, throughput or Bluetooth pairing. No nearby open network was joined,
and no Wi-Fi password was requested/read from unrelated files. Choose your own
network through the desktop NetworkManager menu. Alternatively, enter the
password interactively on the laptop (not in chat/history):

```sh
nmcli --ask device wifi connect 'YOUR_SSID' ifname wlan0
```

Keep Ethernet for recovery. After connection, verify `iw dev wlan0 link`,
`nmcli device show wlan0`, and a route explicitly using wlan0; a normal ping
could otherwise succeed through Ethernet and give false Wi-Fi acceptance.
Test 2.4/5 GHz switching, prolonged traffic and reboot reconnection before
enabling faster SDIO/CMD11 or changing the conservative power settings.

Trackpad tap-to-click is loaded, but libinput warns that this clickpad advertises
BTN_RIGHT. Physical movement, scrolling, left/right-click and typing while
touching the pad need user acceptance. Do not mask BTN_RIGHT with a guessed
quirk before identifying the physical button arrangement. GPU acceleration,
audio, battery/charging and lid/suspend are next bring-up topics, not implied
by working display/radio. The last audio inventory had no ALSA sound cards.

Final diagnostics at November 25, 15:30:59 CST verified Wi-Fi MAC
`a8:4f:a4:22:2d:e3`, Bluetooth MAC ending `e4`, and neither radio soft/hard
blocked. `iw` and `rfkill` are installed on the live USB and included in the
fresh userspace recipe. NTP was synchronized, systemd detected no container,
LightDM/UART getty were active, console-getty inactive and FAT read-only.
Evidence: `logs/live-20261125-input-network/wifi-final-regression.txt`.

An empty **system-scope** failed-unit list is not a clean application journal:
the current desktop journal still reports Bluetooth's optional SAP plugin,
missing optional `pam_lastlog.so`, and user-session D-Bus/PipeWire/WirePlumber
errors. These were inventoried, not silently fixed by altering authentication
or enabling unverified audio wiring. Audio and desktop session integration
need their own focused follow-up, together with physical trackpad acceptance.

At handoff the temporary port-2222 SSH listener was stopped (normal SSH
service/socket remain masked), and the UART logger disconnected locally with
`:quit`, without transmitting a key to the laptop. The serial bridge is free
for the user. A later diagnostic SSH session must recreate its `/run` listener
and verify the fresh host key through serial; do not disable host-key checks.
