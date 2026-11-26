# W600D SE: A/B boot slots and retries

Scope: the factory RK3568 SPL and vendor U-Boot on this laptop. The native
U-Boot prototype has only run as a USB chainload, not from `uboot_a` or `uboot_b`.
This investigation used saved firmware, `misc` backups and serial logs only.

## What selects the slot

`BootROM -> factory SPL -> uboot_a or uboot_b -> USB boot or Android`.
`uboot_a`/`uboot_b` contain bootloader FITs; `boot_a`/`boot_b` contain Android
kernel/ramdisk images. Factory SPL selects the highest-priority bootable slot
from `misc`. A slot is bootable if its priority is nonzero and it is either
marked successful or has tries remaining. A wins a priority tie. If neither
slot is bootable, this SPL has a separate `lastboot` path; that is not a
guarantee of recovery.

`misc` is partition 6 (4 MiB). Offsets below are relative to `misc`:

| Offset | Data | Effect |
| --- | --- | --- |
| `0x800` | 32-byte `\0AB0` record, with CRC32 | Per-slot priority, `tries_remaining`, `successful_boot`; used for A/B selection. |
| `0xc00` | ZTE `STRS` record | Separate `retry`, `boot_times` and `change_times` bookkeeping. |
| `0x4000` | Recovery command in the saved images | Separate from slot success; not a flag to clear for USB boot. |

The November 5 and November 6 backups both have A `(15, 0, 1)` and B
`(14, 0, 1)` at `0x800`, with valid CRCs. Their `STRS` tuples
`(retry, boot_times, change_times)` differ: `(5, 63, 0)` and `(5, 139, 5)`.
Those are historical snapshots, not a fresh device read.

## What if `uboot_a` is bad?

- **First FIT rejected:** SPL tries the second copy in **the same partition**,
  at `0x200000`. The USB-first patch leaves that copy stock. This is not a
  switch to `uboot_b`.
- **Both FITs rejected:** SPL calls its A/B decrement path, then returns a
  load error. It only decrements when `successful_boot=0` and tries remain.
  A trial A can exhaust its tries and allow a bootable B to be selected on a
  later attempt. An already confirmed A does not lose its status just because
  its FITs fail to load. Do not count on B or on automatic resets in that case.
- **FIT loads, then hangs:** SPL has already handed off and spends no try. A
  replacement that hangs before the vendor bookkeeping, or does not implement
  it, can be selected again indefinitely. Past fallback tests used factory
  U-Boot with a broken `bootcmd` after explicitly making A a trial slot; the
  factory U-Boot got far enough to decrement its tries. That does not test
  recovery from a loadable mainline replacement.

## What if Ubuntu boots but never marks the slot successful?

- **Confirmed A (`successful_boot=1`):** ordinary A/B tries do not run down.
  USB Ubuntu does not need to write a per-boot success flag to keep using A.
- **Trial A (`successful_boot=0`):** factory U-Boot spends a try during late
  init, before `bootcmd`, even if USB Ubuntu reaches the desktop or the user
  stops at the U-Boot prompt. Ubuntu does not mark the slot successful. Once
  the tries are exhausted, a later selection can use B instead; B may boot
  stock Android rather than taking the patched A USB path.
- **ZTE retry is independent:** when both slots are bootable, the analyzed
  vendor routine runs this bookkeeping once per U-Boot session, even with A
  already confirmed. When it decrements `retry` from 1 to 0, it logs
  `need reset zte_retry and switch A/B slot`, resets `retry` to 5, increments
  `change_times`, and writes the `STRS` data. Despite the message, this branch
  does not change either A/B priority, clear success or toggle the selected
  slot. The November 25 serial capture shows the message at `boot_times=425`,
  `change_times=15`, then `retry=5`, `boot_times=426`, `change_times=16` on
  the next boot. Both boots selected `_a`, `successful=1`, `tries-remain=0`.

CloudBook Air is a useful contrast: its guide keeps factory U-Boot, replaces
**`boot_a`**, and reports two A/B decrements per cold boot on that model. Its
trial-slot script later marks A successful to keep booting eMMC Linux. That
is not this board’s SPL behavior or an instruction to write its `misc` here.

## Evidence and recommendation

- Factory SPL: slot selection at `0x4110`, FIT failure call at `0x324c`,
  decrement function at `0x42cc` (guard at `0x4354–0x4374`). See the [original
  disassembly notes](../bootloader/usb-uboot/_RESEARCH/docs/ab-tries.md) for
  extraction details; the earlier unconditional corruption fallback claim
  omits the `successful_boot` guard.
- Factory U-Boot: late init at `0xa03d80`, A/B decrement at `0xa249c0`,
  `STRS` at `0xa90944`, expiry branch at `0xa90a38–0xa90a60`, separate
  `misc` write routine at `0xa903d8`. The analyzed retry routines match
  between the original and November 6 v14 saved `uboot_a` payloads.
- Serial capture: `logs/live-20261125-input-network/serial-20261125T121618-398018+0800.jsonl`.
- Comparison source: `build/linux-7.3.6/reference/cloudbook-air-mainline-linux/docs/FLASHING_GUIDE.md`,
  section 6.3, and `switch_ab_slot.py` in the same reference checkout.

Keep the native experiment on USB. Leave `misc` and B alone for USB boot on
a confirmed slot. Before any eMMC bootloader replacement, verify an independent
recovery path (for example Rockchip MaskROM with this machine’s own backups);
stock `uboot_b` alone is not a recovery guarantee.
