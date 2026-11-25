# Optional USB U-Boot and typewriter

This is the **two-U-Boot workflow**, separate from the current Ubuntu USB.
Run commands below from the repository root, unless a block says otherwise.
Use a separate typewriter stick: do not add these files to the working Linux
stick, where an extra boot.scr can change which boot path the factory scanner takes.

```text
Factory eMMC DDR/SPL/ATF/U-Boot, patched USB-first
  -> FAT32 USB /boot.scr (vendor-specific script)
  -> /u-boot-w600d.bin + /w600d-chain.bin loaded into RAM
  -> chain shim -> second U-Boot, running from RAM
  -> display/USB keyboard -> typewriter
```

The factory loader and Android stay on eMMC. The second U-Boot belongs on
USB as a normal file, **not in eMMC bootloader partitions or USB raw sectors**.
The current Linux stick instead goes directly from factory U-Boot to extlinux
and Linux; see `BOOTFLOW.md` and `FACTORY-UBOOT-PATCH.md`.

## Sources and ready-made files

Everything is in `../bootloader/usb-uboot/`, including the original Git history:

| Path within that repository | Purpose |
| --- | --- |
| `build.sh`, `patch-u-boot.sh` | Fetch, patch and build the second U-Boot |
| `patches_for_upstream/u-boot/` | Five board/display/keyboard/typewriter integration patches |
| `patches_for_upstream/typewriter/` | Typewriter changes |
| `chain/chain.S` | RAM-entry shim |
| `chain/boot.cmd`, `chain/boot-nc.cmd` | Human-readable vendor script sources |
| `chain/mkscr.py` | Required vendor-specific boot.scr generator |
| `typewriter/` | Complete application source, including required font/Wubi C data |
| `02_prebuilt_USB_uboot/` | Tested boot.scr, U-Boot binary, shim and SHA256SUMS |
| `howto-typewriter-uboot.md`, `PATCHING.md` | Original detailed instructions |

The original packaging expects `patches/u-boot/`, but the repository contains
`patches_for_upstream/u-boot/`. The local relative alias
`patches -> patches_for_upstream` fixes that path without editing the source.
If checking out the repository elsewhere, recreate that alias before building.

For ready-made files, verify `02_prebuilt_USB_uboot/SHA256SUMS` from that
directory, then copy **only boot.scr, u-boot-w600d.bin and w600d-chain.bin**
to the root of a mounted MBR/FAT32 USB first partition. Identify the mount
and disk first; this guide does not format or flash anything automatically.

## Build it on Linux

The recipe pins U-Boot commit
`709a97a05df66e394f40d249105d0baade46f107`; reproduce that input rather
than silently replacing it with another version. The recorded revision label
is 2027.01-rc1. Linux and macOS toolchain details are in the repository README.

```sh
sudo apt-get install git make gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu \
  bison flex libssl-dev device-tree-compiler python3
cd bootloader/usb-uboot
export ALL_PROXY=socks5://192.168.1.5:1080
./build.sh
```

`build.sh` applies the board patches, copies `typewriter/` into U-Boot,
builds `zte-w600d-chain-rk3568_defconfig`, builds the shim and writes
`out/stick/{boot.scr,u-boot-w600d.bin,w600d-chain.bin,SHA256SUMS}`.
Do not delete `font_data.c` or `wubi_embed.c`: the normal build needs them.

## Generate the right boot.scr

**Use `chain/mkscr.py`, not ordinary mkimage.** This factory U-Boot walks the
script length table until **0xffffffff**, whereas ordinary legacy-script
packaging uses zero. A conventional mkimage script was observed to execute
garbage on this vendor loader.

The current build actually uses **boot-nc.cmd**, not boot.cmd:

```sh
cd bootloader/usb-uboot
mkdir -p out/stick
python3 -I chain/mkscr.py chain/boot-nc.cmd out/stick/boot.scr
```

If you deliberately edit and select the commented boot.cmd instead:

```sh
python3 -I chain/mkscr.py chain/boot.cmd out/stick/boot.scr
```

The preserved prebuilt script's payload exactly matches boot-nc.cmd;
boot.cmd contains additional comments, so the two text sources are not
byte-identical. Regenerate the stick's SHA256SUMS after changing any file.
This boot.scr format is for the **factory vendor** U-Boot, not a generic script
to source in arbitrary mainline U-Boot.

## RAM layout and commands

- Load the second U-Boot at `0x00800000`. Keep its binary **under 4 MiB**:
  the factory script buffer is at `0x00c00000`.
- Load the shim at `0x10000000`.
- The script loads both files, runs **usb stop**, then **go 0x10000000**.
- Keep the known flat command form. Earlier top-level if/fi experiments in
  the factory bootcmd reset the board.

At the second U-Boot prompt:

```text
typewriter
typewriter usb 0:1 notes.txt
```

Ctrl+S saves, Ctrl+X exits, and Ctrl+Space switches Wubi/English.
After a failed RAM/Linux handoff, power off and remove USB to recover the
factory Android path; U-Boot cannot resume after it has transferred control.
