#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct


EXPECTED_SOURCE_SHA256 = "4578807d00d97eed27227955e10251ff195f2de38d3d3b783965dc2b5057aa8e"
DISPLAY_NODES = (
    "/syscon@fdcb0000/edp-phy",
    "/edp@fe0c0000",
    "/pwm@fdd70020",
    "/vcc3v3-lcd-edp",
    "/backlight",
    "/edp-panel",
    "/edp@fe0c0000/ports/port@0/endpoint@1",
    "/display-subsystem/route/route-edp",
)


def find_status_offsets(data):
    header = struct.unpack_from(">10I", data)
    position = header[2]
    structure_end = position + header[9]
    strings_offset = header[3]
    stack = []
    offsets = {}
    while position < structure_end:
        token, = struct.unpack_from(">I", data, position)
        position += 4
        if token == 1:
            name_end = data.index(b"\0", position, structure_end)
            stack.append(data[position:name_end].decode())
            position = (name_end + 4) & ~3
        elif token == 2:
            stack.pop()
        elif token == 3:
            length_offset = position
            length, name_offset = struct.unpack_from(">II", data, position)
            position += 8
            name_start = strings_offset + name_offset
            name_end = data.index(b"\0", name_start)
            name = data[name_start:name_end].decode()
            node_path = "/" + "/".join(stack[1:])
            if node_path in DISPLAY_NODES and name == "status":
                if length != 9 or data[position:position + length] != b"disabled\0":
                    raise ValueError(f"Unexpected original status for {node_path}")
                if node_path in offsets:
                    raise ValueError(f"Duplicate status for {node_path}")
                offsets[node_path] = length_offset
            position = (position + length + 3) & ~3
        elif token == 4:
            continue
        elif token == 9:
            break
        else:
            raise ValueError(f"Unexpected DT token {token}")
    if set(offsets) != set(DISPLAY_NODES):
        raise ValueError("The source does not contain all eight expected disabled nodes")
    return offsets


def main():
    parser = argparse.ArgumentParser(description="Prepare only the tested ZTE eDP status changes")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    source = args.source.read_bytes()
    source_sha256 = hashlib.sha256(source).hexdigest()
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError("Source DTB hash differs from the inspected USB snapshot")
    if args.output.exists() or args.manifest.exists():
        raise FileExistsError("Refusing to replace existing output or manifest")
    inventory_path = Path(__file__).resolve().parent.parent / "2026-11-24-Codex/dtb_inventory.py"
    module_spec = importlib.util.spec_from_file_location("dtb_inventory", inventory_path)
    inventory = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(inventory)
    original_tree = inventory.read_tree(source)
    if original_tree["/"]["model"] != b"ZTE W600D SE (PVT-CS)\0":
        raise ValueError("Unexpected board model")
    offsets = find_status_offsets(source)
    patched = bytearray(source)
    for node_path in DISPLAY_NODES:
        length_offset = offsets[node_path]
        struct.pack_into(">I", patched, length_offset, 5)
        patched[length_offset + 8:length_offset + 20] = b"okay\0\0\0\0" + struct.pack(">I", 4)
    patched_tree = inventory.read_tree(patched)
    expected_tree = {node_path: dict(properties) for node_path, properties in original_tree.items()}
    for node_path in DISPLAY_NODES:
        expected_tree[node_path]["status"] = b"okay\0"
    if patched_tree != expected_tree:
        raise ValueError("Patched tree differs beyond the eight intended status properties")
    if len(patched) != len(source) or patched[:40] != source[:40]:
        raise ValueError("Unexpected file-size or DT-header change")
    manifest = {
        "source": str(args.source),
        "source_sha256": source_sha256,
        "output": str(args.output),
        "output_sha256": hashlib.sha256(patched).hexdigest(),
        "size": len(patched),
        "status_length_offsets": offsets,
        "validation": "Exactly eight status changes; all other DT properties, header and size unchanged",
        "layout": "Each shorter status value is followed by one FDT_NOP token to preserve block offsets",
    }
    with args.output.open("xb") as output:
        output.write(patched)
    with args.manifest.open("x", encoding="utf-8") as output:
        output.write(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
