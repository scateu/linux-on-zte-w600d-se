#!/usr/bin/env python3
import base64
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DTB = Path(sys.argv[1])


def value(path, property_name, kind="x"):
    result = subprocess.run(["fdtget", "-t", kind, str(DTB), path, property_name],
                            check=True, stdout=subprocess.PIPE, text=True)
    if kind == "s":
        return result.stdout.strip()
    return [int(number, 16) for number in result.stdout.split()]


def node(label):
    return value("/__symbols__", label, "s")


def handle(label):
    return value(node(label), "phandle")[0]


edid = base64.b64decode((ROOT / "panel-edid.base64").read_text())
assert len(edid) == 128 and sum(edid) % 256 == 0
assert edid[:8] == bytes.fromhex("00ffffffffffff00")
assert int.from_bytes(edid[54:56], "little") * 10000 == 141020000
assert value("/memory@0", "reg") == [0, 0x200000, 0, 0x8200000, 0, 0x9400000, 0, 0x76c00000]
assert value("/", "compatible", "s").split()[0] == "zte,w600d-se"
assert value(node("backlight"), "pwms") == [handle("pwm2"), 0, 25000, 0]
assert value(node("pwm2"), "reg") == [0, 0xfdd70020, 0, 0x10]
assert value(node("backlight"), "enable-gpios") == [handle("gpio2"), 27, 0]
assert value(node("vcc3v3_lcd_edp"), "gpio") == [handle("gpio2"), 29, 0]
assert value(node("edp_panel"), "enable-gpios") == [handle("gpio2"), 28, 0]
assert value(node("edp_panel"), "compatible", "s") == "edp-panel"
assert value(node("gpio3") + "/keyboard-power-hog", "gpios") == [3, 0]
assert value(node("edp_in_vp1"), "remote-endpoint") == [handle("vp1_out_edp")]
assert value(node("vp1_out_edp"), "remote-endpoint") == [handle("edp_in_vp1")]
assert value(node("vop"), "assigned-clock-rates") == [564080000, 141020000]
for property_name, provider in {
    "pmuio2-supply": "vcc3v3_pmu",
    "vccio1-supply": "vccio_acodec",
    "vccio3-supply": "vccio_sd",
    "vccio4-supply": "vcc_1v8",
    "vccio5-supply": "vcc_3v3",
    "vccio6-supply": "vcc_3v3",
    "vccio7-supply": "vcc_3v3",
}.items():
    assert value(node("pmu_io_domains"), property_name) == [handle(provider)]
assert value(node("vcc3v3_pmu"), "regulator-min-microvolt") == [3300000]
for label in ["sdhci", "sdmmc0", "sdmmc1"]:
    assert value(node(label), "status", "s") == "disabled"
for label in ["edp", "edp_phy", "pwm2", "vop", "vop_mmu", "usb_host0_xhci", "usb_host1_xhci"]:
    assert value(node(label), "status", "s") == "okay"
properties = subprocess.check_output(["fdtget", "-p", str(DTB), node("edp_phy")], text=True).splitlines()
assert "zte,edp-v12-v13" not in properties
image = DTB.parent / "Image"
with image.open("rb") as source:
    header = source.read(64)
assert header[56:60] == b"ARM\x64"
print("Validated 2 GB memory, native EDID, PWM2, panel GPIOs, keyboard power, VP1 graph, exact IO supplies and Android storage disabled")
