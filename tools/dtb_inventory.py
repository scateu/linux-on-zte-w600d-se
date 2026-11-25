#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import struct


def read_tree(data):
    if len(data) < 40:
        raise ValueError("Truncated DTB header")
    magic, total_size, structure_offset, strings_offset, _, version, _, _, strings_size, structure_size = struct.unpack_from(">10I", data)
    if magic != 0xD00DFEED or version != 17 or total_size > len(data):
        raise ValueError("Expected a complete version-17 flattened device tree")
    structure_end = structure_offset + structure_size
    strings_end = strings_offset + strings_size
    if structure_end > total_size or strings_end > total_size:
        raise ValueError("DTB blocks extend beyond the declared size")
    position = structure_offset
    stack = []
    nodes = {}
    while position + 4 <= structure_end:
        token, = struct.unpack_from(">I", data, position)
        position += 4
        if token == 1:
            end = data.index(b"\0", position, structure_end)
            stack.append(data[position:end].decode())
            nodes["/" + "/".join(stack[1:])] = {}
            position = (end + 4) & ~3
        elif token == 2:
            if not stack:
                raise ValueError("Unbalanced END_NODE")
            stack.pop()
        elif token == 3:
            if not stack or position + 8 > structure_end:
                raise ValueError("Invalid property header")
            length, name_offset = struct.unpack_from(">II", data, position)
            position += 8
            if position + length > structure_end or name_offset >= strings_size:
                raise ValueError("Invalid property data or name offset")
            start = strings_offset + name_offset
            end = data.index(b"\0", start, strings_end)
            name = data[start:end].decode()
            value = data[position:position + length]
            nodes["/" + "/".join(stack[1:])][name] = value
            position = (position + length + 3) & ~3
        elif token == 4:
            continue
        elif token == 9:
            if stack:
                raise ValueError("Unclosed node at END")
            return nodes
        else:
            raise ValueError(f"Unexpected DTB token {token}")
    raise ValueError("Missing END token")


def describe(value):
    result = {"hex": value.hex(" ")}
    if value and value.endswith(b"\0") and all(byte == 0 or 32 <= byte < 127 for byte in value):
        result["strings"] = value[:-1].decode("ascii").split("\0")
    elif len(value) % 4 == 0:
        result["cells"] = [f"0x{cell[0]:x}" for cell in struct.iter_unpack(">I", value)]
    return result


def main():
    parser = argparse.ArgumentParser(description="Read-only DTB inventory without dtc/libfdt")
    parser.add_argument("dtb", type=Path)
    parser.add_argument("--match", action="append", default=[], help="Include paths containing this text; repeatable")
    args = parser.parse_args()
    nodes = read_tree(args.dtb.read_bytes())
    result = {path: {name: describe(value) for name, value in properties.items()}
              for path, properties in nodes.items()
              if not args.match or any(fragment in path for fragment in args.match)}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
