# Install: ZTE W600D SE USB preview

1. **Enable ADB on your own laptop.** In a Wi-Fi/account text field: `Alt` + hold `,` → Google Pinyin settings → Personal dictionary → Search → Settings → About tablet. Tap **Build number** seven times, then enable **USB debugging** in **Developer options**. Use Wi-Fi or a USB **Ethernet adapter** on a trusted LAN: `adb connect <laptop-ip>:5555`; approve the prompt. The USB cable is not the ADB transport on this firmware. See the [original notes](../bootloader/usb-uboot/README_人类写的.txt).
2. **Patch once.** If not USB-first, [back up and patch your own factory `uboot_a` over rooted ADB](FACTORY-UBOOT-PATCH.md). Confirm recovery before writing. Boot Android without USB and verify A is marked successful before repeated USB boots. Disable Android debugging when done.
3. **Write the USB.** Download `*.img.gz` and `GZIP-SHA256SUMS`. In the download directory, run `shasum -a 256 -c GZIP-SHA256SUMS` (or `sha256sum -c GZIP-SHA256SUMS`), then `gzip -dk *.img.gz`. Flash the extracted `.img` to the **whole USB drive** (not a partition; erases it). Use **8 GB or larger**. Plug it in and power on. First boot is designed to grow the USB root partition and leave the 512 MiB FAT partition unchanged. If using the zstd build instead, verify `SHA256SUMS` and run `zstd -d *.img.zst`.
4. **Optional internal slot A:** Not supported in this preview. `uboot_a` is firmware and `boot_a` is Android. Neither takes this USB image. Keep both Android slots intact for unplug-to-Android.
5. **Back to Android:** Shut down, unplug the USB, and power on. This is the intended fallback; verify it before relying on it.

Preview defaults: local `linux` autologin and passwordless `sudo`; SSH is masked and UART does not autologin as root. Set a password and disable local autologin/passwordless sudo before daily use.

[Build and validation](BUILD-CURRENT.md#compact-usb-preview) · [Recovery](RECOVERY.md) · [A/B retries](AB-BOOT-RETRIES.md)
