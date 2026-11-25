# USB persistence preparation — November 24, 2026, +08:00

## Authorization and actual status

The user explicitly requested: "please write changes to usb drive" after
confirming the successful RAM-only white-screen test.

**No USB write, writable remount, boot-file replacement or reboot has been
performed during this persistence attempt.** Serial must be reliable before
backups and disk writes can be verified. This file supersedes the serial-session
identifiers in `CURRENT.md` and `display-success.md`; their display success and
board-wiring findings remain valid.

The user most recently confirmed that the laptop is still powered on with a
white screen. Last readable mount evidence showed USB root ext4 read-only.
Do not exit the PID-1 shell, reboot, or unplug its USB root drive to work around
the serial problem. eMMC/GPT/misc/slot writes and `saveenv` remain out of scope.

## Serial issue and current connection state

At 11:50, host `lsof` showed two clients connected to `localhost:5000`: the
existing Python logger and a separate `nc` process. RX text was being split.
The user acknowledged the competing connection and subsequently closed it;
`lsof` then confirmed only the logger remained.

The old logger was disconnected locally with `:quit`, followed by local Ctrl-C
only after its Python process had exited to terminate the remaining producer
pipeline. No target reboot was sent. Reconnected logger session `26723` produced
garbled bytes and later a prompt, but readable echo responses could not be
verified. A transmitted XON and target Ctrl-C did not establish a working shell.

That logger was also disconnected locally. A sole-client, 15-second diagnostic
then sent exactly XON followed by CR/LF, `echo SERIAL_CRLF_OK`, and CR/LF.
It received no bytes and closed its socket. **There is no active logger session
at this checkpoint.** Sessions `83306`, `26723` and `94753` have ended.

New evidence:

- `logs/serial-20261124T115429-417313+0800`: reconnect and garbled/stalled replies.
- `logs/serial-crlf-20261124T120208+0800`: CR/LF diagnostic with no RX bytes.
- Earlier `logs/serial-20261124T113221-669340+0800` still contains the successful
  display test and the beginning of the read-only persistence preflight.

The user was asked to restore/restart the serial bridge at 115200 baud while
leaving the laptop powered on. The actual cause is not established; 115200 is
the baud specified by the observed Linux ttyS2 console arguments, not proof that
a baud mismatch is the only issue. Reconnect exactly one logger and require a
readable command echo, shell response and mount listing before disk operations.

## Prepared and validated host artifact

`prepare_persistent_display.py` prepares only the eight tested DT status changes
from the inspected original USB snapshot. It refuses a different source hash or
existing output path. It reuses the earlier `dtb_inventory.py` for validation.

Generated files:

- `rk3568-laptop-zte-edp-20261124.dtb`, 165657 bytes.
- `persistent-display-manifest.json`, including source/output hashes and offsets.

```text
Source SHA256:
4578807d00d97eed27227955e10251ff195f2de38d3d3b783965dc2b5057aa8e

Prepared DTB SHA256:
ae39fab24eba06fcee147abcf76e7ba3f374bcf874b3fc123d54b09c83fdb7d0

Snapshot extlinux.conf SHA256:
5ef3b7c8b83a42b9d4011cff4a43a31da5984110068672edda63fde1e21559bb
```

Validation proved that the parsed trees differ only in those eight `status`
properties, from `disabled` to `okay`; all other properties, file size and the
40-byte DT header are unchanged. Each shorter property occupies its original
space by adding a standard FDT_NOP token after its padded value. VP0 input,
PWM2 phandle/pinmux, GPIOs, graph links and panel timing properties are unchanged.
This is an offline parser validation, not a new hardware boot of this artifact.

## Pending installation plan

1. Restore reliable sole-client serial; confirm PID 1 and root/mount state.
2. Mount the verified USB boot partition `/dev/sda1` read-only at an existing,
   unused directory such as `/media`; confirm partition start 2048 and size
   1048576 sectors. Do not confuse it with ext4 USB root `/dev/sda2` or eMMC.
3. Read/hash the actual `/boot/rk3568-laptop-zte.dtb` and `/extlinux/extlinux.conf`
   on that FAT partition. Compare with the snapshot; adapt rather than overwrite
   blindly if live configuration differs. The binary patch requires an exact
   source DTB hash match.
4. Remount only the FAT boot partition writable. Back up the live original DTB
   and extlinux.conf before changing any boot selection; sync the backups.
5. Install the prepared DTB under the new filename, leaving the original DTB
   untouched. If generating it on target with Perl, use the manifest offsets
   and require the prepared checksum before activation.
6. Stage an extlinux configuration selecting the new DTB for the existing default
   entry, retaining the original entry/DTB as a rollback choice. Preserve existing
   kernel/root/init arguments unless a further change is intentionally reviewed.
7. Publish the new DTB before switching the configuration, sync, verify hashes and
   contents by readback, then unmount/remount boot FAT read-only. Keep root ext4
   read-only throughout this operation. Do not reboot without a deliberate test.
8. Record the actual backup locations, installed hashes and final configuration
   in a new completion note; do not label this pending file as a completed write.

Persisting eDP enablement does not add missing framebuffer-console support. The
manual `fb0/pan` handover documented in `display-success.md` may still be needed
for fbdev diagnostics after boot. Do not claim an automatic local text shell or
install a different init program as part of this minimal DT persistence change.
