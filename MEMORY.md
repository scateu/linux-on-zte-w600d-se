# W600D SE handoff — November 26, 2026

## USB Ubuntu preview

- **Goal:** patch a matching factory laptop once, boot Ubuntu with its built-in display and keyboard when the USB is inserted, and boot stock Android when it is removed. The normal route is factory SPL → patched factory `uboot_a` → USB extlinux → Linux. There is no second U-Boot in the release image.
- **Image:** `preview-20261126-r2`, Ubuntu 24.04.5 ARM64/XFCE, Linux `7.3.6-w600d-usb-wifi`, v6 Wi-Fi/BT DTB. The 4 GiB raw MBR image has a 512 MiB FAT32 boot partition and an ext4 root designed to expand on first boot. Use an 8 GB or larger stick. Local `linux` autologin and passwordless sudo are enabled; SSH is masked and UART root autologin is removed.
- **Build host:** `trash`, `/home/k/codex-workdir-nov-24-2026/artifacts/releases/preview-20261126-r2/`. The recipe is [`build-usb-release.sh`](build/linux-7.3.6/scripts/build-usb-release.sh); see [build inputs and procedure](docs/BUILD-CURRENT.md#compact-usb-preview). The recipe emits raw and zstd images; gzip was prepared separately for distribution.
- **GitHub:** [draft prerelease](https://github.com/scateu/linux-on-zte-w600d-se/releases/tag/untagged-ff4914422110bbb7c087), not public. Uploaded the 459 MiB `.img.gz`, `GZIP-SHA256SUMS`, `usb-partitions.json`, and `rootfs-package-versions.txt`. All four GitHub asset sizes and SHA-256 digests matched local files. The gzip image SHA-256 is `dc7db43c40898914bb326dc648c6c093fbb5b31e11f32d31ce4e518c3f0a69c7`.
- **Git:** `91721cb` (`Prepare W600D removable Ubuntu USB preview`) is local on `main`, one commit ahead of `origin/main` at `d47ee6a`. Shell syntax and staged whitespace checks passed. Nothing was pushed. The draft targets `d47ee6a`, not the unpublished recipe; review the target before publishing.
- **Verified offline:** image checksums and both compression formats, MBR and both filesystems, boot files, and ARM64 package/service defaults. The ext4 root grew on an 8 GiB file copy without changing the FAT32 partition. No laptop or USB drive was flashed during release preparation.

## Next physical checks

1. Flash the verified gzip image to a spare **whole USB drive** following [the install guide](docs/INSTALL.md). Keep the currently working USB as a fallback. Cold-boot the preview and check the LCD, built-in keyboard, trackpad, and desktop.
2. Confirm live first-boot expansion with `journalctl -b -u w600d-grow-root.service` and `df -h /`. Then shut down, remove the USB, and cold-boot stock Android. Neither test has been done with this exact image.
3. On the older working USB, trackpad motion/click and USB Ethernet DHCP were verified; Wi-Fi scanned both bands and associated, but DHCP was slow. Revisit Wi-Fi DHCP after the preview boot checks. See [the previous live checkpoint](CURRENT.md).

## Bootloader boundaries

- [Factory patch guide](docs/FACTORY-UBOOT-PATCH.md): use the machine’s own backup and rooted ADB; verify Android slot A is marked successful after patching. The SPL is in the raw eMMC `idbloader` (header LBA 64; SPL LBA 176), not in either `uboot_*` partition. See [boot flow](docs/BOOTFLOW.md) and [A/B retry behavior](docs/AB-BOOT-RETRIES.md). Do not rely on B to rescue every failure in A. The USB image must never be written to `boot_a` or `uboot_a`.
- [Native U-Boot prototype](docs/NATIVE-UBOOT.md) is a separate manual USB chainload. After correcting the Smart0 origin, the internal countdown was readable and Space on the laptop keyboard stopped it. A RAM-only trial handing off to Linux hit a Rockchip IOMMU/display power-domain panic; the factory-to-USB Linux route recovered after a power cycle. Keep this prototype on USB and off the default boot path.
- Serial is `tcp://localhost:5000`; coordinate a single reader so another client does not consume the log. Reconfirm device paths and hardware state before any write.
