# Native-display U-Boot — November 25–26, 2026

## Status and scope

| Path tested | Result |
| --- | --- |
| Factory U-Boot → USB extlinux → Ubuntu | Working baseline; also recovered after the panic |
| Factory → USB native U-Boot, installed 677656-byte build | Warm restart and manual chainload: LCD showed the countdown, built-in Space stopped it, and the keyboard ran `version` |
| Native U-Boot → same Ubuntu, 677664-byte build with Smart0 origin corrected in RAM | Image and DTB loaded, but Linux panicked during display probe |
| Native U-Boot → Ubuntu, exact installed 677656-byte build | Not yet tested; it still uses the same display initialization sequence |
| Cold native chainload, repeated cold/warm Linux boots, no-USB Android acceptance | Not yet verified for this experiment |
| Replace eMMC `uboot_a` | Not built or tested; the USB binary is not a replacement image |

## Goal and exact bootflow

This is **goal #2**: the USB-loaded mainline U-Boot must initialize the display,
not merely inherit the vendor logo scanout. It is **not** a project to replace
factory SPL/DDR training or secure firmware.

```text
Rockchip BootROM
  -> factory loader/SPL: DDR and secure firmware
  -> original eMMC U-Boot, with the established USB-first bootcmd patch
  -> explicitly selected USB native-display script
  -> existing RAM-only ARM64 cache/MMU handoff shim
  -> patched mainline U-Boot: reset/power-cycle and initialize LCD pipeline
  -> visible ten-second autoboot countdown + internal USB keyboard shell
  -> USB extlinux.conf -> existing Image/DTB -> Ubuntu (handoff not yet validated)
```

Until acceptance, the default remains the already-working **factory U-Boot ->
USB extlinux -> Linux** route. The experiment does not install a root `boot.scr`,
rename extlinux.conf, alter Image/DTB/rootfs, issue an eMMC write or save an
environment. Removing USB therefore removes all experimental files; the physical
unplugged Android acceptance test remains a separate outstanding check.

Do not treat slot B as automatic recovery for an eMMC replacement. See
[W600D SE A/B boot retries](AB-BOOT-RETRIES.md) for the FIT fallback rules,
the Android success flag and the separate ZTE counter seen in serial logs.

The old typewriter is also patched mainline U-Boot, but its VOP2 takeover driver
only finds an already-enabled window and changes its framebuffer. Its CRTC,
eDP PHY, panel and backlight remain the factory's work. Neither that driver nor
the typewriter submodule is changed by this experiment.

## Upstream and native port

On November 25, 2026 the upstream GitHub mirror advertised HEAD
`9d67454e920b3908529c9fc642a8c911db040896`. The checked-out commit is dated
November 24, 2026 and merges `fsl-qoriq-for-2027-01-rc3`; its version base is
`2027.01-rc`. This is a pinned reproduction input, not an evergreen "latest".
The Rockchip video directory at this exact revision contains the older VOP
drivers and Analogix `rk_edp.c`, but no RK3568 VOP2 driver.

The experimental board port in `build/u-boot-native/` adds:

1. **Native VOP2:** wakes/unidles VO, enables display/PWM gates, sets VPLL to
   564 MHz and VP1 pixel clock to 141 MHz, pulses all six VOP2 resets,
   verifies no old window is enabled, resets/disables both inherited IOMMUs,
   creates an ARGB8888 Smart0 window, and programs VP1 timing/overlay/eDP mux.
2. **Naneng PHY:** reset, AUX power, explicit 1.62/2.7 Gb/s link rate, 1/2/4
   lanes, lane power masks, PLL-lock wait and per-lane swing/pre-emphasis.
   Both rate and voltage changes carry the full lane count, retaining the
   important Linux eDP-lane fix.
3. **Analogix RK3568:** external PHY integration, software clock-recovery and
   channel-equalization training, training-pattern cleanup, scrambling and
   enhanced framing, RGB 8-bit input, and positive stream-valid validation.
   No internal hardware trainer is asked to adjust an external PHY.
4. **KDC panel/backlight:** disable supply and enable GPIO for 500 ms; power
   them back on, wait 200 ms, and light the backlight only after video training.
5. **USB-only console/boot:** 115200 serial, `serial,usbkbd` input and
   `serial,vidconsole` output, ten-second countdown, extlinux boot, no eMMC,
   SPI-flash, persistent environment writer, FAT/ext4 writer or script bootmeth.
   Excluding the script bootmeth prevents the second U-Boot from chainloading
   itself again when it scans USB.

This deliberately narrow prototype uses some direct board-specific CRU/PMU
register operations because this upstream RK3568 clock driver lacks gate
callbacks. The VP1 divider is explicitly four; calling its generic DCLK setter
can select a different PLL multiple that is not our panel's verified mode.
DDR, PMIC rails, secure-world setup and foundational system clocks remain part
of the factory chainload baseline. Success would prove independent **display
initialization**, not independent power-on initialization of the entire SoC.

## Actual board, not the CloudBook panel

- W600D SE: RK3568, **2 GiB RAM**, panel KDC `KD140N1930A02`.
- EDID: 1920x1080; pixel clock 141.020 MHz; totals 2080x1130. The programmed
  clock is 141.000 MHz (0.014% lower), matching working Linux scanout.
- Horizontal front/sync/back: 48/32/80; vertical: 10/12/28; negative H/V sync.
- LCD supply GPIO2_D5; panel enable GPIO2_D4; backlight enable GPIO2_D3.
- Backlight PWM2m1 on GPIO0_B6, 25000 ns period.
- VOP2 `fe040000`, eDP `fe0c0000`, Naneng PHY `fdcb0000`; **VP1 -> eDP**.
- Internal USB keyboard `258a:0001`, GPIO3_A3 power, host xHCI at `fd000000`.
- Do not substitute CloudBook's BOE panel, PWM8 or 4 GiB memory assumptions.

Timing is decoded from `build/linux-7.3.6/panel-edid.base64`; its EDID checksum
is valid. PHY and VOP2 settings reference the already-working Linux source on
`trash`, including our four display patches and the pinned CloudBook reference.

## The supplied "factory" backup is partly patched

Input: `recovery/factory-backups/uboot-backup-20261106-v14/uboot_a.img.gz`.
Read-only inspection verifies decompressed size 4194304 and SHA256:

```text
8de8c9f8187a062128af68e6ae219a991ac67f8fb9e25b55f3fbc95c69ec65b0
```

Both FIT copies contain `U-Boot 2017.09 (May 29 2024 - 17:08:27 +0800)`.
Their U-Boot payload is 995144 bytes at FIT-relative `0xe00`, loaded at
`0x00a00000`. Both payload SHA256 properties match their data:

| FIT offset | Payload SHA256 | Default environment |
| --- | --- | --- |
| `0x0` | `115502cafacb4feee786eb17715d58bf2fb6e4ebeb3aa9ca276ba84e1abe9f5b` | **v14 debug USB bootcmd, bootdelay=3** |
| `0x200000` | `2ceaba1c8a8087d634d7cb95cb0193909cce4ee87d46fd0dd4987948f2371726` | Original Android bootcmd, bootdelay=0 |

The two copies are **not identical**. The filename means "backup made at v14",
not a wholly pristine image. Do not pass it to a pristine-input patcher or flash
it onto a different laptop. No RSA signature validity is inferred from matching
payload hashes. It is an offline reference/recovery artifact only.

The extracted scanner tries **extlinux before scripts for each boot prefix**.
The current USB has `/extlinux/extlinux.conf` at FAT root. A root boot.scr is
therefore not a reliable override while this root extlinux entry succeeds.
Manual selection is safer than changing scan order or factory defaults.

The backup also contains `vop2_initial` and the Analogix bandwidth/lane-count/
lane-training function-name strings. Presence of a string is not a complete
disassembly or proof of a particular register write.

Re-run the non-writing inspector:

```sh
python3 -I build/u-boot-native/inspect-factory.py \
  recovery/factory-backups/uboot-backup-20261106-v14/uboot_a.img.gz
```

## Rebuild on trash

Keep the new source apart from `/home/k/repo/uboot/` and the old typewriter.
On a fresh repository checkout, initialize the pinned shim dependency with
`git submodule update --init bootloader/usb-uboot`. The recorded submodule
revision is `c6283107a754a2baeb48843c11dc0640a77a0444`. The only files the
native build consumes from it are `chain/chain.S` and `chain/mkscr.py`.
Copy this small recipe plus the existing chain shim/script generator, retaining
repository-relative paths. One convenient layout is
`$WORK/recipe/build/u-boot-native/` and
`$WORK/recipe/bootloader/usb-uboot/chain/{chain.S,mkscr.py}`.

```sh
ssh trash
export ALL_PROXY=socks5://192.168.1.5:1080
cd /path/to/copied/repository
bash build/u-boot-native/build.sh
```

Default `WORK` is `/home/k/codex-workdir-nov-24-2026/uboot-native`; override it
for a fresh build directory. Dependencies are Git, GNU make, host GCC, Python 3,
`aarch64-linux-gnu-gcc/binutils`, bison, flex, OpenSSL development headers and
device-tree-compiler (`fdtget` included). The observed cross compiler is Ubuntu
GCC `14.2.0-19ubuntu2`. No kernel or rootfs rebuild is needed for this test.

The recipe fetches only the pinned revision into `src/u-boot`, checks its HEAD,
checks/applies all sorted recipe patches, copies the board overlay, builds only
`u-boot.bin`, validates configuration/DT/size, and builds the established shim.
It does **not** build/install an SPL replacement or flash any device.
If an older integration patch was applied in that isolated source, reverse
that exact old patch first; the recipe intentionally stops instead of resetting
or force-overwriting a mismatched checkout.

Outputs in `$WORK/artifacts/stick/` (sizes below are from the installed build):

| File | Use |
| --- | --- |
| `u-boot-w600d-native.bin` | 677656-byte U-Boot; loaded at `0x00800000` |
| `w600d-native-chain.bin` | 272-byte cache/MMU handoff shim; entered at `0x10000000`, jumps to `0x00800000` |
| `boot-native.scr` | Factory-only script loaded at `0x00c00000`; source is `boot-native.cmd` |
| `SHA256SUMS` | Verify all three payload files with `sha256sum -c SHA256SUMS` from this directory |

Save `$WORK/artifacts/UPSTREAM_REV`, `$WORK/logs/build.log`, the build
configuration in `$WORK/out/build/.config`, and the output hashes for each new
trial. Keep each tested artifact set together. The installed binary and
manifest hashes are recorded below; a regenerated script embeds its generation
time and therefore need not hash identically. The `<4 MiB` build guard prevents
overlap with the script in RAM; it does **not** validate an eMMC FIT image.

The factory script generator uses the nonstandard `0xffffffff` image-length
table terminator. Standard mkimage's zero-terminated script is **not** equivalent.
Do not ask the second mainline U-Boot to interpret this factory-format script.

## Manual RAM-only hardware test

### Live observations: November 25, 2026

- Isolated files were staged under `/native-uboot/` on the existing FAT boot
  partition. New-file hashes verified; existing extlinux/Image/v6 DTB hashes
  matched before/after. FAT was synced and remounted read-only. No default
  boot files or eMMC were modified.
- The first software reboot failed in the **existing Linux kernel**, before
  native U-Boot executed. Xorg hit a VOP2 register-read external abort;
  shutdown then faulted in `drm_atomic_helper_shutdown` and killed PID 1.
  Shutdown had already synced/remounted root read-only and detached filesystems.
  The user physically power-cycled instead. This shutdown bug is deferred.
- The physical boot was intercepted in factory U-Boot 2017.09. The first
  `usb start` had a set-address error and found no storage; `usb reset`
  then found the Kingston DataTraveler as USB storage 0. Its serial number is
  `E0D55E625BE9F440F84702D0`. Submit serial load commands separately and await
  the prompt: queued input can be dropped while a synchronous USB load runs.
- Explicit loads reported 660160 bytes for the first native binary and
  272 bytes for the handoff shim. After `usb stop` and `go 0x10000000`, the
  native banner appeared, but `initr_dm()` stopped with a framebuffer-allocation
  error **before the display driver probed**. This is not a successful LCD test.
- Root cause: the native video node lacked `bootph-some-ram`, so it was absent
  during pre-relocation video reservation. The U-Boot-only DTS now supplies
  this tag, and the build validator checks it in the compiled DT.
- Pre-retest review also found the external `fcc00000` boot USB controller
  disabled in the prototype tree. Both xHCI controllers, both combo PHYs and
  the USB2 OTG PHY are now enabled as in the working Linux DTS; `fcc00000`
  explicitly uses host mode. The validator checks both controller statuses
  and external host mode; later tests read the Linux boot files from USB.
- The corrected build passes all guards: native binary 660184 bytes,
  SHA256 `5691fa2e5dfba0452c6f03cf75fc3d4f27ae421d6b5033026789185d9b781cd3`.
  The shim remains 272 bytes. The user power-cycled into unchanged Linux;
  root/boot device names, PARTUUIDs and Kingston serial were rechecked. The
  corrected isolated test files are now on the laptop USB and their hashes
  verify. Normal extlinux/Image/v6 DTB hashes also still verify. First-attempt
  files are backed up at
  `/root/w600d-debug-backups/20261125T170112-native-uboot-first/`.
- A guarded restart successfully avoided the existing Linux DRM shutdown
  panic: ordinary `sync`, SysRq `s`, SysRq `u`, verify USB root and FAT both
  read-only, then SysRq `b`. Only USB root/FAT were mounted block filesystems.
  `intercept-factory.py --restart-readonly --execute` independently rechecked
  both USB sources, PARTUUIDs and read-only mount options before sending `b`;
  it captured the factory prompt. **Never use `b` with writable filesystems**:
  it does not sync or unmount. This is a debug workaround, not a shutdown fix.
  Root remount-read-only is disruptive to running services: save all work first.
- Factory boot logs include its own `zte_retry` metadata rewrite. No explicit
  eMMC, factory bootloader or saved-environment write command was issued by
  this experiment; preserving the factory boot path does not prevent its
  normal internal bookkeeping.
- Serial evidence is under `logs/live-20261125-native-uboot/`, including
  `serial-20261125T164807-775574+0800.jsonl` for the physical boot and first
  native startup attempt. These logs are ignored build/debug artifacts.
- Second test used the factory-format `/native-uboot/boot-native.scr`: loads
  reported 660184/272 bytes, and mainline U-Boot passed the earlier reservation
  failure. Both boot USB and the SINO WEALTH internal keyboard enumerate.
  The countdown appears on UART, but the user reports **pure black LCD and
  no visible countdown**. No display success is claimed.
- New failure: panel power-off returned `-EALREADY` (`-114`) because U-Boot's
  fixed-regulator probe had already driven the supply GPIO low while its
  enable counter was zero. Treating this as fatal left the panel-enable GPIO
  claimed; later automatic reprobes then failed with `-EBUSY` (`-16`). The
  board panel driver now accepts only `-EALREADY` with matching actual GPIO
  readback, still requires the full 500 ms OFF interval, verifies ON readback,
  and releases its enable GPIO on failure. Unlike the generic "if allowed"
  helper, it does not silently accept `-EACCES`, `-EBUSY` or `-ENOSYS`.
  The third and fourth RAM tests passed this panel sequence.
- Handoff review found native `bdinfo` describes a single bank from `0x200000`
  to 2 GiB. With `CONFIG_ARCH_FIXUP_FDT_MEMORY=y`, U-Boot would overwrite the
  known-working Linux DTB's two banks that exclude factory OP-TEE at
  `[0x08400000, 0x09400000)`. Do **not** auto-boot that intermediate prototype.
  The next build reserves this 16 MiB region in its own control DT for LMB,
  and disables the memory-bank rewrite so Linux keeps its existing safe banks.
  Build guards require both. For recovery through the already-running older
  prototype, manually load Image/DTB at safe addresses, add this region with
  `fdt rsvmem add 0x08400000 0x01000000`, verify it, and only then `booti`.
- Recovery load then revealed `CONFIG_USB_STORAGE` was disabled: the USB tree
  listed mass-storage class, but no block device existed; `fatload` failed and
  `usb storage` was unavailable. The next defconfig explicitly enables USB
  storage and the generic filesystem read command; build guards require them.
  The unsafe-memory/absent-storage intermediate binary is not suitable for
  automatic Linux boot. Use its `reset` to return to unchanged factory -> USB
  Linux, then update only `/native-uboot/` with the guarded corrected build.
- Native `reset` successfully returned to the normal factory -> USB Linux
  path, and the user confirmed Linux booted. The next build combines panel
  handling, USB storage and secure-memory corrections: 677520 bytes, SHA256
  `a2fde01a6a5d9bfb7340aaa329333c1278efa1432f58f92b66574249d37c74eb`.
  Expanded build guards pass. This third build passed the panel sequence and
  booted Ubuntu automatically through the existing extlinux entry. Native
  display initialization stopped before VOP2 reset with `-ERANGE` (`-34`):
  VPLL/DCLK/ACLK read 564/141/300 MHz rather than the requested fractional
  564.080/141.020 MHz pair.
- The fourth build (677632 bytes) added 64-bit PLL rate math and explicit
  DSMPD mode programming. The same rate check failed; VPLL registers showed
  `con0=0000202f con1=00000441 con2=00000000 mode=00001455`. A single diagnostic
  write of `0x1b4e8` to `0xfdd200a8` read back as zero. Why the fractional
  field stayed zero is unproven. UART Ctrl-C held the countdown; `boot`
  reached Ubuntu. Capture: `serial-20261125T173752-945205+0800.jsonl`.

### November 26: integer-clock trial

- The new build requests and checks 564/141/300 MHz exactly, using the
  VPLL/DCLK pair already measured with working Linux scanout. Panel timing
  and Linux files are unchanged. Binary SHA256:
  `a201d4630ae27f47f6d8e09407c814c9baed5c300c53db86e63ae37cbdf11f94`.
- Updated only the four files under FAT `/native-uboot/`. Their checksums
  and the original extlinux/Image/v6 DTB hashes all verified after sync and
  remount read-only. Rollback:
  `/root/w600d-debug-backups/20261126T090143-native-uboot-pre-integer/`.
- The guarded warm restart reentered factory U-Boot. Its first `usb start`
  found zero storage devices; `usb reset` found the boot drive. The manually
  sourced script loaded the 677664-byte native binary and the 272-byte shim.
- The native probe passed the clock check, reset VOP2 with inherited window
  mask `00`, discarded the previous PHY link, and trained 2 lanes at 2.7 Gb/s
  with enhanced framing. It enabled the backlight and reported a fresh VP1
  frame on the new Smart0 framebuffer at `0x7d700000`. The current shell is
  held by UART Ctrl-C; `coninfo` confirms `vidconsole` output and `usbkbd`
  input. Initially the user saw white dots forming diagonal slash marks that
  changed with typing. UART echoed `ccxccccxxxxxzxzxzxzxzxzxz` without serial
  TX, confirming that the built-in keyboard reaches the native shell.
- `bdinfo` and Smart0 both report `0x7d700000`; Smart0 `YRGB_VIR=0x780`
  gives 1920 four-byte words per line, matching 1920x1080x32 console RAM.
  Smart0 destination initially read `0x00280070` (includes porches); the
  Linux atomic update uses destination coordinates without porches. Changed
  only Smart0 destination to `(0,0)` and latched VP1 via `CFG_DONE` in RAM.
  Readback confirmed zero and the user confirmed normal LCD output. The
  built-in keyboard ran `help` and returned to the prompt, verified on UART
  with no agent TX. No USB or eMMC files changed during that test.
- The recipe now sets the fullscreen Smart0 origin to `(0,0)` and keeps the
  porches in the VP1 timing registers. The corrected 677656-byte binary built
  on `trash`; configuration, compiled-DT, size and artifact checksum guards
  passed. Output is in `$WORK/artifacts/stick/`. Binary SHA256:
  `a9bab7e993562f5f28eff1529cae5d61f539633aed81c620d23f892bb958f461`.
  Manifest SHA256:
  `40a506a28794f7e6b075c5c293f7dbedbcc735bc9170e8655f69730069b104eb`.
  The initial hardware test changed only the live register.
- RAM-only display-fix capture: `serial-20261126T091138-636480+0800.jsonl`.
- In the same capture, `boot` with the RAM-only origin fix and native scanout
  active loaded the existing Ubuntu extlinux entry, Image and v6 DTB. At 5.2 s
  Linux reported `failed to set idle on domain 'vo', val=0`, then took a
  synchronous external abort in `rk_iommu_enable_stall` during Rockchip DRM
  probe and panicked before userspace. This confirms a failed warm display
  handoff, not its root cause. Earlier builds that stopped before the VOP2
  reset had reached Ubuntu. No USB or eMMC writes were made in this attempt.
  Use a power-cycle into the unchanged factory -> USB Ubuntu route to recover;
  test the corrected native binary's countdown separately from Linux handoff.
- The user power-cycled and confirmed normal Ubuntu boot. On the verified
  Kingston USB (`24c0d202-01` FAT, `24c0d202-02` root), updated only the
  `/native-uboot/` binary, script and manifest. The new script has the same
  payload and differs only in its mkimage timestamp and header CRC; the
  272-byte shim is byte-identical and was not replaced. The installed manifest
  and normal extlinux/Image/v6 DTB hashes verified after remounting FAT
  read-only. Rollback: restore the native directory from
  `/root/w600d-debug-backups/20261126T093341-native-uboot-pre-origin/`.
- Synced and verified both USB mounts read-only before the guarded reboot.
  `intercept-20261126T093519-719234+0800.jsonl` records the factory prompt.
  The factory firmware itself logged `rewrite zte_retry 2.` during normal
  initialization; no eMMC write command or `saveenv` was issued by the test.
- The installed binary passed a separate countdown test after that warm
  restart. `usb reset` recovered the stick after `usb start` initially found
  no storage. The script loaded 677656 bytes, then native U-Boot reported a
  fresh VP1 frame and successful two-lane eDP training. The user saw the
  countdown on the LCD, stopped it with the built-in Space key, and ran
  `version` at `=>`. In `serial-20261126T093556-443105+0800.jsonl`, the last
  TX is `source 0x00c00000`; UART did not interrupt the countdown or enter
  the command. Left the machine at the native prompt. Direct Linux handoff,
  repeated cold boots and USB-unplugged Android remain unvalidated.

### Procedure

1. Confirm the USB identity and power-cycle recovery readiness. The test stick
   has FAT `PARTUUID=24c0d202-01` and root `PARTUUID=24c0d202-02`; verify the
   actual device with `lsblk` rather than assuming a `/dev/sdX` name. Back up
   the existing FAT `/native-uboot/` directory, then copy only the three
   payload files and `SHA256SUMS` there. Leave `/extlinux/extlinux.conf`,
   the kernel and Linux DTB alone. Sync, remount FAT read-only, and verify
   the new small-file hashes and the unchanged extlinux/Image/DTB hashes.
   No full-disk write or read-back is needed.
2. Keep the logged serial console connected to `tcp://localhost:5000`, 115200.
   Save work, safely reboot, and interrupt **factory** U-Boot over UART. Do not
   use saveenv or write eMMC. Short serial command lines avoid PTY canonical
   input limits; a single pasted line over 1024 bytes can be silently truncated.
   For a physical power-cycle, disconnect other serial clients and start
   `python3 build/u-boot-native/intercept-factory.py --power-cycle --execute
   --timeout 180` before applying power. It sends Ctrl-C only after the factory
   banner, issues no Linux reboot, and exits once the factory prompt is captured.
   Then reconnect with `python3 tools/serial_console.py --log-dir
   logs/live-20261125-native-uboot` for manual commands. Use only one client
   on the serial TCP stream; no `--break-on` or UART input during the physical
   keyboard acceptance test. Prefer the physical power-cycle path after a safe
   shutdown while the existing Linux DRM shutdown panic is unresolved.
3. In the factory shell, use USB device/partition discovered on that boot:

   ```text
   usb start
   load usb 0:1 0x00c00000 /native-uboot/boot-native.scr
   source 0x00c00000
   ```

   If `usb start` reports zero storage devices, use `usb reset` and wait for
   the expected drive to enumerate before loading the script.

   For a script-free equivalent:

   ```text
   load usb 0:1 0x00800000 /native-uboot/u-boot-w600d-native.bin
   load usb 0:1 0x10000000 /native-uboot/w600d-native-chain.bin
   usb stop
   go 0x10000000
   ```

   Proceed to `go` only after both load commands report the expected byte
   counts. The 4 MiB binary guard protects the factory script at `0x00c00000`.
4. The new U-Boot must show the panel OFF/ON sequence, an empty inherited-window
   mask after reset, Naneng PLL lock, successful software training and a **fresh**
   VP1 frame. A still-visible factory logo alone is not success.
5. User acceptance: visible countdown; Space on the built-in keyboard stops
   it; type `version` and confirm readable LCD output. `usb tree` and
   `coninfo` are useful diagnostics if input or output fails. Serial input
   remains the fallback, not evidence of a physical keypress. Use `reset` to
   return through factory U-Boot to normal Ubuntu; use a power cycle if reset
   does not recover. Treat direct `boot` as a separate, logged hardware test.
6. On a hang, power off and reboot with the unchanged Linux USB normally, or
   remove USB for the factory Android route. Nothing is installed as the default
   by this test; a failed RAM handoff cannot return to the old U-Boot instance.

Do not make the native route default until cold-display, keyboard interruption,
Ubuntu handoff, repeated cold boots and unplugged Android have been accepted.

To roll back just the experiment, restore `/native-uboot/` from the saved
`/root/w600d-debug-backups/20261126T093341-native-uboot-pre-origin/` copy (or
leave it unused). The default boot path does not read that directory. Do not
restore a whole USB image or write eMMC for this rollback.

## Ubuntu panic: evidence and next experiment

With native scanout running, the preceding 677664-byte build with the Smart0
origin corrected **in RAM** loaded the unchanged Ubuntu Image and v6 board
DTB. At approximately 5.2 seconds, Linux reported that display power domain
`vo` failed to exit idle (`val=0`). A synchronous external abort followed in
`rk_iommu_enable_stall` during `rockchip_drm_init`, before userspace. The same
Linux files booted via factory U-Boot after a power cycle. Earlier native
builds that stopped before VOP2 reset also reached Ubuntu. The leading
hypothesis is that native initialization leaves VO/VOP2, its clocks, or its
IOMMUs in a state Linux cannot take over. The exact offending state is unknown.
This is not evidence that changing the Smart0 origin caused the panic. It is
also separate from the pre-existing Linux DRM **shutdown** panic on reboot.

The board driver `w600d_vop2.c` powers/unidles VO, enables clocks, and resets
and programs the display path and IOMMUs. It has no `.remove` callback. That
is a lead, not a confirmed cause or fix. Verify which cleanup hooks `boot`
and `booti` actually invoke before relying on a removal hook. Turning off the
backlight alone leaves the scanout, clocks, and IOMMU state unchanged.

For the next trial, work only with the isolated USB files. Keep the same USB,
extlinux entry, Image and DTB. Match the reboot type between native trials;
record the binary hash, cold/warm start, whether the LCD trained, and serial
log for each run:

1. **Factory control:** Boot Ubuntu via factory U-Boot. Capture a successful
   boot and, where safely observable, the VO idle status, VOP2 clock/reset
   state and IOMMU state for comparison. Do not read registers in an unpowered
   domain.
2. **Native, active scanout:** Try `boot` from the exact installed binary with
   scanout active to establish whether the prior panic reproduces on it.
3. **Native, quiesced scanout:** Test a USB-only variant that preserves the
   countdown but quiesces the display path before Linux. Compare power-domain
   idle acknowledgements and DRM/IOMMU probe output with the first two runs.
   Change only the display handoff initially, not the Linux files or memory
   map. Confirm a working Ubuntu graphics session and keyboard, not merely
   that the kernel loaded.

### Serial evidence index

The local captures below are in `logs/live-20261125-native-uboot/` and ignored
by Git. Preserve them separately if moving the project. JSONL records
distinguish RX from TX; `jq -j 'select(.direction == "RX") | .text' < capture.jsonl`
joins the original received chunks. The `.rx.bin` and `.tx.bin` files also
preserve the raw streams.

| Capture | What it shows |
| --- | --- |
| `serial-20261125T164807-775574+0800.jsonl` | First native startup: pre-relocation framebuffer allocation failure |
| `serial-20261125T173752-945205+0800.jsonl` | Fractional clock check failed before VOP2 reset; Ubuntu still booted |
| `serial-20261126T091138-636480+0800.jsonl` | Integer clock, RAM-only origin correction, then VO idle timeout and IOMMU abort |
| `intercept-20261126T093519-719234+0800.jsonl` | Warm restart into factory prompt; stock `zte_retry` bookkeeping |
| `serial-20261126T093556-443105+0800.jsonl` | Installed 677656-byte binary: LCD countdown and keyboard test; last UART TX was `source 0x00c00000` |

## Before considering an eMMC `uboot_a` replacement

**Do not write any of the USB artifacts to `uboot_a`.** The test binary is
built for a factory-U-Boot-to-RAM shim, with `bootflow scan -b usb`, no MMC
support and no Android fallback. It depends on factory SPL, DDR init, ATF and
OP-TEE. `uboot_a` is a 4 MiB partition starting at sector 16384 (512-byte
sectors); the supplied backup has two factory FIT copies at partition-relative
offsets `0` and `0x200000`. A raw binary fitting in RAM says nothing about
the factory loader requirements for FIT, entry point, or verification.
`uboot_b` has a different factory build; do not assume automatic failover.

Keep the known-good factory path until these gates pass:

1. Prove repeatable **USB-only** cold and warm boots from the native countdown
   to working Ubuntu display and input, without a handoff panic. Also power on
   without USB and verify original Android via factory U-Boot as a baseline.
2. Build an eMMC candidate as a separate target. Verify the actual SPL/ATF/
   OP-TEE entry and memory contract, FIT copy layout, image loading and any
   required authentication. Preserve the factory secure firmware and USB-first
   selection with Android fallback. Matching FIT hashes do not prove boot-time
   authentication passes.
3. Verify machine-specific backups and a recovery method that works even if
   `uboot_a` cannot boot. Only then plan a separately approved eMMC trial.
   Acceptance on the replacement must cover both USB Ubuntu and no-USB
   original Android, without modifying Android partitions.

See [Partitions and hardware](PARTITIONS-AND-HARDWARE.md),
[Factory bootcmd patch](FACTORY-UBOOT-PATCH.md), and [Recovery](RECOVERY.md).
No eMMC replacement was attempted. Slow Wi-Fi DHCP remains out of scope.
