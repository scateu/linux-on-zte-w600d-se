#!/usr/bin/env python3
import pathlib
import subprocess
import sys


def main():
    output = pathlib.Path(sys.argv[1])
    config = (output / ".config").read_text()
    expected = {
        "CONFIG_TEXT_BASE": "0x00800000",
        "CONFIG_BAUDRATE": "115200",
        "CONFIG_BOOTDELAY": "10",
        "CONFIG_ENV_IS_NOWHERE": "y",
        "CONFIG_VIDEO_W600D_NATIVE": "y",
        "CONFIG_DISPLAY_ROCKCHIP_EDP": "y",
        "CONFIG_USB_KEYBOARD": "y",
        "CONFIG_USB_STORAGE": "y",
        "CONFIG_CMD_FS_GENERIC": "y",
        "CONFIG_BOOTMETH_EXTLINUX": "y",
    }
    for name, value in expected.items():
        if f"{name}={value}\n" not in config:
            raise SystemExit(f"Missing/incorrect {name}={value}")
    forbidden = (
        "CONFIG_MMC", "CONFIG_CMD_MMC", "CONFIG_ENV_IS_IN_MMC",
        "CONFIG_ENV_IS_IN_FAT", "CONFIG_ENV_IS_IN_SPI_FLASH",
        "CONFIG_FAT_WRITE", "CONFIG_EXT4_WRITE", "CONFIG_USB_GADGET",
        "CONFIG_BOOTMETH_SCRIPT", "CONFIG_VIDEO_ROCKCHIP_VOP2_TAKEOVER",
        "CONFIG_CMD_SF", "CONFIG_CMD_SAVEENV", "CONFIG_EFI_LOADER",
        "CONFIG_ARCH_FIXUP_FDT_MEMORY",
    )
    for name in forbidden:
        if f"{name}=y\n" in config:
            raise SystemExit(f"Unsafe/unwanted setting: {name}")
    binary = output / "u-boot.bin"
    if not 0 < binary.stat().st_size < 0x400000:
        raise SystemExit("Binary would overlap the factory script at 0x00c00000")
    dtb = output / "dts/dt.dtb"
    compatible = subprocess.check_output(
        ["fdtget", "-t", "s", str(dtb), "/display@fe040000", "compatible"],
        text=True,
    ).strip()
    if compatible != "zte,w600d-vop2-native":
        raise SystemExit(f"Wrong display binding: {compatible}")
    properties = subprocess.check_output(
        ["fdtget", "-p", str(dtb), "/display@fe040000"], text=True,
    ).splitlines()
    if "bootph-some-ram" not in properties:
        raise SystemExit("Native video must bind before relocation to reserve its framebuffer")
    for node in ("/usb@fcc00000", "/usb@fd000000"):
        status = subprocess.check_output(
            ["fdtget", "-t", "s", str(dtb), node, "status"], text=True,
        ).strip()
        if status != "okay":
            raise SystemExit(f"Boot USB and keyboard controllers must be enabled: {node}")
    mode = subprocess.check_output(
        ["fdtget", "-t", "s", str(dtb), "/usb@fcc00000", "dr_mode"], text=True,
    ).strip()
    if mode != "host":
        raise SystemExit("The external boot USB controller must use host mode")
    secure = subprocess.check_output(
        ["fdtget", "-t", "x", str(dtb), "/reserved-memory/optee@8400000", "reg"],
        text=True,
    ).strip()
    if secure != "0 8400000 0 1000000":
        raise SystemExit(f"Factory OP-TEE reservation missing or incorrect: {secure}")
    print(f"Build guards passed: USB-only, native driver, {binary.stat().st_size} bytes")


if __name__ == "__main__":
    main()
