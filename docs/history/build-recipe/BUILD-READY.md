# Current build commands — includes DT symbols and SSH socket fix

This is the latest authoritative build entry point. Older START-HERE/README
commands are historical. Use **build-ready-image.sh**, not build-all.sh or
build-release.sh. They predate the explicit DTC_FLAGS=-@ requirement.

```sh
ssh trash
cd /home/k/codex-workdir-nov-24-2026
export ALL_PROXY=socks5://192.168.1.5:1080
export APT_PROXY=socks5h://192.168.1.5:1080
JOBS=24 bash scripts/build-ready-image.sh
```

If the initial kernel and Ubuntu userspace builds have already completed:

```sh
bash scripts/finalize-kernel-symbols.sh
bash scripts/build-desktop-rootfs.sh
bash scripts/assemble-image.sh
```

The final DTB must contain /__symbols__. Kernel CONFIG_OF_OVERLAY=y alone
did not cause this custom target to include symbols; pass DTC_FLAGS=-@
explicitly. The final board validator refuses a symbol-less or incorrectly
wired tree. The final Ubuntu exporter uses Dockerfile.final and verifies
both SSH service and socket are masked. It exports an ordinary bootable
Ubuntu filesystem, not a container-dependent laptop runtime.

See README.md for detailed architecture, image layout, development account,
safe USB flashing, hardware acceptance and Android fallback. See
FACTORY-UBOOT.md for per-machine original vendor U-Boot patch precautions.

Only these phases/inputs are supported for the release:

- scripts/prepare-sources.sh, scripts/build-userspace.sh
- scripts/build-kernel-v2.sh, scripts/finalize-kernel-symbols.sh
- scripts/build-desktop-rootfs.sh, scripts/assemble-image.sh
- scripts/validate-kernel-config.py, scripts/validate-board.py
- scripts/flash-usb.py, rootfs/Dockerfile.v2 (userspace stage only),
  rootfs/Dockerfile.final, rootfs/FIRST-STEPS.txt
- final validated v3 DTB; v1/v2 are compilation inputs, never hardware images.

Intermediate revisions were retained because the host refused existing-file
updates, not because multiple production bootflows are intended. The sole
target flow remains vendor eMMC U-Boot -> USB extlinux -> native Linux 7.3.6
-> USB Ubuntu XFCE. Shutdown/remove USB -> original Android.
