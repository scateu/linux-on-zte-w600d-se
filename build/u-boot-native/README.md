# Native-display USB U-Boot prototype

**Experimental, not yet a replacement for the working Linux USB bootflow.**
See the [native U-Boot guide](../../docs/NATIVE-UBOOT.md) for the complete
build, deployment, hardware tests, failure history, and recovery procedure.
The installed USB build passed the countdown and built-in keyboard test; the
direct Ubuntu handoff remains unverified. Do not flash the USB binary to eMMC.

- Upstream base: `9d67454e920b3908529c9fc642a8c911db040896`, fetched November 25, 2026.
- Build host: `trash`; isolated work: `/home/k/codex-workdir-nov-24-2026/uboot-native`.
- Build: `bash build/u-boot-native/build.sh` on a Linux cross-build host.
- Output: `$WORK/artifacts/stick/`; default WORK is the isolated directory above.
- Manual test only: use `/native-uboot/boot-native.scr`, **not** root `boot.scr`.
- Factory SPL/DDR/ATF/OP-TEE remain required. No replacement loader is built/flashed.

## Files

| Path | Purpose |
| --- | --- |
| `overlay/arch/arm/dts/` | Actual KDC panel timing, GPIO wiring, USB keyboard and native display nodes |
| `overlay/configs/` | 115200 UART, ten-second countdown, USB-only extlinux, no persistent environment writes |
| `overlay/drivers/video/rockchip/w600d_vop2.c` | VO wake, gates, PLL, VOP2 reset, IOMMU bypass, fresh Smart0/VP1 modeset |
| `overlay/drivers/video/rockchip/rk3568_edp_phy.c` | Naneng PHY reset/AUX, link-rate/lane-count/swing configuration |
| `overlay/drivers/video/rockchip/w600d_panel.c` | Supply/enable power cycle and delayed PWM backlight |
| `overlay/include/rockchip_edp_phy.h` | Complete configuration passed through U-Boot's generic PHY API |
| `patches/0001-native-display-integration.patch` | Analogix external-PHY integration, VPLL rate, opaque console colors and build wiring |
| `patches/0002-pll-fractional-rate-and-mode.patch` | Rockchip 64-bit PLL rate arithmetic and explicit fractional/integer mode |
| `boot-native.cmd` | Factory-only chainload script source; uses the established RAM shim |
| `validate-build.py` | Configuration, binary-size and compiled native-display DT guards |
| `inspect-factory.py` | Read-only inspection of this machine's compressed or raw two-FIT backup |
| `intercept-factory.py` | Bounded UART interception; physical listen-only or guarded restart of already read-only USB |

The register sequence and electrical settings reference the already-working
Linux `7.3.6` source and its eDP patches, not CloudBook's different BOE panel.
Upstream Analogix/U-Boot source is retained and patched; the old typewriter
submodule, editor, takeover driver and their pinned source are not changed.
This is a board-specific port on mainline, not a claim that unmodified upstream
already supports RK3568 laptop display.

Generated upstream checkout, outputs and logs stay out of Git. Keep the
recipe, board overlay, patches, and documentation in the repository.
