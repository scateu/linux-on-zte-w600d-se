# Current W600D SE Linux recipe

This is the retained Linux **7.3.6-w600d-usb-wifi** / Ubuntu ARM64 recipe, including
the final eDP PHY lane fix, I2C4 touchpad and v6 MT7663S radio wiring. Start with the root's
`docs/BUILD-CURRENT.md`, `docs/DIY-FROM-UPSTREAM.md` and `CURRENT.md`.
The version is a tested reproduction input, not a claim about today's latest
upstream release. Trackpad motion/left-click and managed Ethernet DHCP are now
recorded; complete desktop/right-click and Android fallback acceptance remain
unfinished. Live SDIO enumeration identifies the same MediaTek MT7663S pair
as CloudBook; the factory Unisoc platform nodes were misleading.

From a fresh Linux/Docker build directory containing this recipe:

```sh
export ALL_PROXY=socks5://192.168.1.5:1080
bash scripts/build-wifi-image.sh
```

The wrapper prepares sources, builds Ubuntu userspace and the patched kernel,
applies the eDP lane fix and board-adapted radio patches, fetches pinned
MediaTek firmware, finalizes artifacts, builds XFCE, strips exported
container markers and assembles a regular disk-image file. It does not flash
a device. Detailed prerequisites, working-directory setup, exact config,
output names, and safe USB file-only updates are in docs/BUILD-CURRENT.md.
The original display-only wrapper remains available. The new full Wi-Fi image
wrapper is syntax-checked; it is not yet an end-to-end flashed-image result.

## Retained inputs

- Complete rk3568-zte-w600d-mainline DTS include chain, final extlinux.conf, native
  panel EDID and config/config-7.3.6-w600d-usb.
- Naneng eDP PHY patch in reference/cloudbook-mainline-6.12/patches/0009-*.patch
  and patches/0002 through 0004 for Analogix, VPLL and PHY lanes.
- CloudBook radio patches 0005/0011/0012/0013, our 0005b lifecycle adaptation,
  and 0005c activating that isolated driver for the actual `zte,w600d-se` board.
- Current userspace/rootfs definitions: Dockerfile.v3, Dockerfile.final,
  Dockerfile.mtools, FIRST-STEPS.txt and rootfs/overlay/.
- Current build, validation, assembly and narrowly scoped USB-update scripts.

The full original comparison Git repository is now inside
reference/cloudbook-air-mainline-linux/. The relative alias
reference/cloudbook-mainline-6.12 points to its mainline-6.12 subtree, so the
recipe remains self-contained. Preserve aliases when copying or archiving it.

Superseded build wrappers and Dockerfiles were removed. The pre-consolidation
README, START-HERE, BUILD-READY and FACTORY-UBOOT documents moved to
docs/history/build-recipe/ in the consolidated root. They are historical, not
the current build entry point. The cleanup audit records the removed files.

Current bootflow is factory eMMC U-Boot -> USB extlinux -> Linux. Do not add
typewriter boot.scr, a chain shim or another U-Boot to this Linux stick.
