#!/usr/bin/env python3
import argparse
import datetime
import json
import os
from pathlib import Path
import select
import socket
import sys


def timestamp():
    return datetime.datetime.now().astimezone().isoformat(timespec="microseconds")


def main():
    parser = argparse.ArgumentParser(description="Logged, line-oriented TCP serial console")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--log-dir", type=Path, default=Path(__file__).resolve().parents[1] / "logs/live")
    parser.add_argument("--break-on", help="Send Ctrl-C once when this exact text appears in received output")
    args = parser.parse_args()
    args.log_dir.mkdir(parents=True, exist_ok=True)
    stem = datetime.datetime.now().astimezone().strftime("serial-%Y%m%dT%H%M%S-%f%z")
    prefix = args.log_dir / stem
    pending = bytearray()
    stdin_open = True
    break_pattern = args.break_on.encode() if args.break_on else None
    break_buffer = bytearray()

    with prefix.with_suffix(".jsonl").open("x", encoding="utf-8") as journal, \
            prefix.with_suffix(".rx.bin").open("xb") as received, \
            prefix.with_suffix(".tx.bin").open("xb") as transmitted:
        def record(direction, payload):
            entry = {"time": timestamp(), "direction": direction,
                     "hex": payload.hex(), "text": payload.decode("utf-8", errors="replace")}
            journal.write(json.dumps(entry, ensure_ascii=True) + "\n")
            journal.flush()
            if direction in ("RX", "TX"):
                output = received if direction == "RX" else transmitted
                output.write(payload)
                output.flush()

        record("LOCAL", f"Connecting to {args.host}:{args.port}".encode())
        with socket.create_connection((args.host, args.port), timeout=10) as connection:
            connection.settimeout(None)
            record("LOCAL", b"Connected; no bytes transmitted automatically")
            print(f"Connected to {args.host}:{args.port}; logs: {prefix}", flush=True)
            print("Enter sends CR; :break sends Ctrl-C; :quit disconnects locally.", flush=True)
            try:
                while True:
                    readers = [connection]
                    if stdin_open:
                        readers.append(sys.stdin.fileno())
                    readable, _, _ = select.select(readers, [], [])
                    if connection in readable:
                        payload = connection.recv(65536)
                        if not payload:
                            record("LOCAL", b"Remote connection closed")
                            print("\nRemote connection closed.", flush=True)
                            return
                        record("RX", payload)
                        if break_pattern:
                            break_buffer.extend(payload)
                            if break_pattern in break_buffer:
                                connection.sendall(b"\x03")
                                record("TX", b"\x03")
                                record("LOCAL", b"Automatic Ctrl-C on configured output pattern")
                                break_pattern = None
                            else:
                                break_buffer = break_buffer[-len(break_pattern):]
                        sys.stdout.buffer.write(payload)
                        sys.stdout.buffer.flush()
                    if stdin_open and sys.stdin.fileno() in readable:
                        payload = os.read(sys.stdin.fileno(), 4096)
                        if not payload:
                            stdin_open = False
                            record("LOCAL", b"stdin closed; continuing receive-only")
                            continue
                        pending.extend(payload)
                        while b"\n" in pending:
                            line, _, remainder = pending.partition(b"\n")
                            pending = bytearray(remainder)
                            line = bytes(line).rstrip(b"\r")
                            if line == b":quit":
                                record("LOCAL", b"User requested local disconnect")
                                return
                            outgoing = b"\x03" if line == b":break" else line + b"\r"
                            connection.sendall(outgoing)
                            record("TX", outgoing)
            except KeyboardInterrupt:
                record("LOCAL", b"Local KeyboardInterrupt; not sent to target")
                print("\nDisconnected locally.", flush=True)
            except OSError as error:
                record("LOCAL", str(error).encode())
                raise


if __name__ == "__main__":
    main()
