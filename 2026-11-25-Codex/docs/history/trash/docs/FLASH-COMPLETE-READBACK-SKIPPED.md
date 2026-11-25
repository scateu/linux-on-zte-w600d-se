# Current checkpoint: USB flashed, full read-back skipped

**Read this first.** This supersedes the pending-flush/verification state in
CURRENT.md and NEW-USB-RELEASE.md. Those files still document useful hardware,
build inputs and hashes, but their live checkpoints are historical. Existing-file
updates were denied again; this new Markdown preserves the correct final state.

## Completed write; explicitly unverified read-back

- The full `30943477760`-byte image was written to the authorized Kingston
  `/dev/sdb` on trash, serial `E0D55E625BE9F440F84702D0`.
- `dd conv=fsync` completed successfully before its read-only verification
  stage began at approximately 16:47:47 +08:00 on November 24, 2026.
- The USB was genuinely writing during the silent fsync period: measured
  physical counters advanced 141672 sectors in five seconds, about 14.5 MB/s.
  Buffered progress had reached EOF before the physical flash finished.
- Read-back subsequently ran at about 24.7 MB/s. At **16:50:50 +08:00**,
  it was stopped at the user's explicit request to skip verification.
- The selected container was checked to contain only a reader/hash pipeline,
  with no remaining disk writer, before stopping it. No new flash was started.
- **Full disk read-back SHA256 was NOT verified.** Source image SHA256 and
  pre-flash filesystem/boot-file checks passed; do not conflate these facts.
- The all-verified wrapper's nonzero exit is expected from intentional
  verification cancellation, not evidence that write/fsync failed. Do not
  reflash simply to make its wrapper return zero.
- Audit on trash: `logs/flash-readback-skipped-20261124.txt` and
  `logs/flash-kingston-20261124.log`. No `/dev/sda` or laptop eMMC was exposed.

The USB can now be removed from trash and moved to the laptop. Its host-side
cached partition view may retain the old layout until replug; the new image's
MBR defines 512 MiB FAT32 boot and 28997 MiB ext4 root. No more device reads
are needed or being requested after the user's verification waiver.

## New-drive bootflow and remaining physical acceptance

Patched **original eMMC vendor U-Boot -> new USB extlinux -> Linux
7.3.6-w600d-usb -> Ubuntu 24.04.5 ARM64 XFCE/systemd**. This new USB
contains no second U-Boot, boot.scr or raw Rockchip loader. Linux eMMC/SDMMC
nodes are disabled. No further eMMC flash or saveenv was performed.

The new kernel has **not yet booted on the laptop**. The old 5.10 white-screen
and physical-keyboard tests are hardware clues, not new-kernel acceptance.
Wi-Fi, Bluetooth, audio, battery, suspend and touchpad are not claimed working.

Next: keep the laptop powered off, insert the new USB in the known-working
boot port, restore `tcp://localhost:5000`, and tell the agent before powering
on. Old serial session 81726 is closed; establish one fresh logged client,
then power on and capture the first boot. Observe the internal display and
physical keyboard typing, then properly shut down, remove USB and observe
original Android on the next power-on. Never remove a running Linux rootfs.

Bring-up accounts remain deliberately permissive: `linux` desktop/tty1
autologin, UART root autologin and passwordless sudo. SSH service **and socket**
are masked. Harden password/sudo/autologin before daily use.

## Build and handoff files

Build host workdir: `/home/k/codex-workdir-nov-24-2026` on `trash`.
Current recipe: `linux-7.3.6-build/BUILD-VERIFIED.md`,
`scripts/build-verified-image.sh`, and `scripts/assemble-capacity-image.sh`.
Detailed board wiring, native panel clock/EDID, source/config/image checksums,
Docker special-file fixes and privilege scope: NEW-USB-RELEASE.md.
Per-factory-machine vendor bootcmd patch/recovery: FACTORY-UBOOT.md.

Raw image under server artifacts:
`w600d-ubuntu-xfce-7.3.6-20261124-usb-29510MiB.img`

Source-image SHA256 (not a completed disk read-back hash):
`ec9bd70d021c829a528e52e9f9642162932b528ffddf3d7ab696497e8e5926d2`

Its `.img.zst` distribution copy is about 432 MiB; a separate portable
6 GiB raw image is also retained. All source archives, package/config
manifests, checked rootfs and build logs remain on trash.

A fresh official-Ubuntu build of the corrected recipe is still running
under a separate `w600d-ubuntu-xfce-clean-check:24.04.5` tag. It first failed
during a transient proxy outage, then restarted with a 4.6 KB context after
the proxy returned. It does not write the USB or replace this release.
Resume/check exec session 74697 or `logs/build-userspace-v2.log` later.
The flashed release's dpkg audit and required-package/service checks passed.
