# Changing the factory power-on BMP

This is **optional cosmetic eMMC modification**, not a Linux display fix.
No logo partition was written during this cleanup. Commands here generate
files offline; the original detailed write/undo instructions are in
`../bootloader/usb-uboot/_RESEARCH/docs/HOWTO-change-logo.md`.

## Which picture is where?

The historical experiment changed **p17, the logo partition**, and changed
the observed China Mobile power-on picture. The RSCE `logo.bmp` and
`logo_kernel.bmp` show a different ZTE picture. RSCE `battery_*.bmp` files
are charging animation, not the proven source of that power-on logo.

Keep these distinct:

| Source | Purpose |
| --- | --- |
| eMMC p17 `logo` | Tested power-on logo location |
| p16 `baseparameter` | Vendor display-mode data |
| RSCE in Android boot image | Vendor display DTB and charging/resource pictures |
| Linux Image/DTB and eDP patches | Actual Linux scanout, unrelated to changing the logo BMP |

The vendor display setup still needs its original Android resources. Do not
erase boot_a, boot_b, baseparameter or any other Android partition to change
a picture or to use the removable Linux stick.

## Preserve this exact format

The backed-up logo partition is **32 MiB**, with two copies:

| Offset | BMP size | Format |
| --- | --- | --- |
| `0x000000` | 6,220,854 bytes | 1920 x 1080, 24-bit, uncompressed, 54-byte header |
| `0x5eee00` | 6,220,854 bytes | Same image, rounded to a 512-byte boundary |

Its header says positive height/bottom-up, but the tested pixel rows are
actually **top-down**. Keep the stock header unchanged, write row zero as the
top of the screen, replace both pixel copies, preserve padding and total
partition size. Do not substitute a resized/compressed BMP casually.

## Generate a replacement offline

Run from the consolidated root. Extraction verifies the original raw SHA256
before publishing the decompressed file; use a new output directory.

```sh
python3 tools/extract-backups.py /tmp/w600d-logo \
  --only w600d-backup/logo.img
python3 -I bootloader/usb-uboot/_RESEARCH/tools/make-logo.py \
  /tmp/w600d-logo/w600d-backup/logo.img \
  /tmp/w600d-logo/logo-linux.img 'W600D LINUX'
```

The generator edits both copies and also writes `logo-linux.img.bmp`.
Its built-in glyph set is small; the sample text above uses supported glyphs.
For a correct macOS preview:

```sh
sips -s format png -f vertical /tmp/w600d-logo/logo-linux.img.bmp \
  --out /tmp/w600d-logo/logo-linux.png
```

The obsolete generated 32 MiB example and its 6 MiB BMP preview were removed;
the original stock image, generator and detailed format analysis remain.
Saved charging BMPs/resource DTBs remain readable under
`../recovery/factory-backups/w600d-backup/resource_a/`.
`_RESEARCH/tools/rsce.py` can extract a restored resource.img or boot.img.

## If you later choose to install the logo

First back up **that laptop's own** logo partition and establish a recovery
route. Compare the generated file's size/hash and confirm the actual
`/dev/block/by-name/logo` mapping on that device. Only then follow the
historical Android-root write procedure, targeting **logo and nothing else**.
Undo uses that same laptop's original raw logo.img, not its .gz file.
Never pass a compressed backup to dd or a flashing utility.
Logo customization is not required for USB Linux or Android fallback.
