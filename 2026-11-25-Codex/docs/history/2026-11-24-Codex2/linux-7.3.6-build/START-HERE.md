# Authoritative release build entry point

Use this file for current commands. The older README explains the architecture
and factory/flash procedure, but its `build-all.sh` / rootfs-v2 commands are
superseded. Historical intermediate files are kept because existing-file
edits are denied by the host's access policy; do not boot intermediate DTBs.

## Build the final image on trash

```sh
ssh trash
cd /home/k/codex-workdir-nov-24-2026
export ALL_PROXY=socks5://192.168.1.5:1080
export APT_PROXY=socks5h://192.168.1.5:1080
JOBS=24 bash scripts/build-release.sh
```

For an already-built kernel/userspace, the remaining release phases are:

```sh
bash scripts/finalize-kernel.sh
bash scripts/build-desktop-rootfs.sh
bash scripts/assemble-image.sh
```

The final rootfs uses `rootfs/Dockerfile.final` after building the Ubuntu
userspace base. Both `ssh.service` and Ubuntu's socket-activated `ssh.socket`
are disabled and masked; masking only the service would be insufficient.
The normal XFCE desktop/tty1 auto-login account is linux; diagnostic serial
auto-login is root. See the README's security setup before daily use.

The shipped DTB is the validated v3 output. IO supply providers are checked
against the original compiled ZTE tree, not inferred from phandle numbers.
In particular pmuio2 is the original **3.3 V LDO6**, not 1.8 V. No v2 DTB was
sent to or booted on the laptop. Final checks also cover native EDID, PWM2,
GPIOs, memory, VP1 graph, disabled eMMC/SDMMC and the 141.02 MHz clock setup.

Image: `artifacts/w600d-ubuntu-xfce-7.3.6-20261124.img`, 6 GiB, for an 8 GB or
larger USB. A compressed `.img.zst` and SHA-256 file accompany it.

Build success is not hardware acceptance. Flash only the positively identified
new USB with `scripts/flash-usb.py`, then verify display/keyboard on the new
kernel, shut down, remove USB, and confirm original Android boot. Keep the old
known-working USB unchanged. No Linux eMMC write or USB flash is performed by
the release build script.
