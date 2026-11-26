#!/usr/bin/env python3
import argparse
import datetime
import json
import pathlib
import re
import socket
import sys
import time


def main():
    parser = argparse.ArgumentParser(description="Interrupt factory U-Boot after a safe reboot or physical power-cycle")
    parser.add_argument("--execute", action="store_true")
    restart = parser.add_mutually_exclusive_group()
    restart.add_argument("--power-cycle", action="store_true",
                         help="Listen only: do not send a Linux reboot command")
    restart.add_argument("--restart-readonly", action="store_true",
                         help="Restart only after verifying USB root and boot are already read-only")
    parser.add_argument("--timeout", default=90, type=float)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000, type=int)
    parser.add_argument("--log-dir", default="logs/live-20261125-native-uboot", type=pathlib.Path)
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("No action: use --execute only after saving work and authorizing reboot")
    if args.timeout <= 0:
        raise SystemExit("Timeout must be positive")
    args.log_dir.mkdir(parents=True, exist_ok=True)
    stem = datetime.datetime.now().astimezone().strftime("intercept-%Y%m%dT%H%M%S-%f%z")
    journal_path = args.log_dir / f"{stem}.jsonl"
    with journal_path.open("x") as journal, socket.create_connection(
            (args.host, args.port), timeout=10) as connection:
        connection.settimeout(0.05)

        def record(direction, data):
            journal.write(json.dumps({
                "time": datetime.datetime.now().astimezone().isoformat(),
                "direction": direction,
                "hex": data.hex(),
                "text": data.decode("utf-8", errors="replace"),
            }) + "\n")
            journal.flush()

        def send(data):
            connection.sendall(data)
            record("TX", data)

        def receive():
            try:
                data = connection.recv(65536)
            except socket.timeout:
                return b""
            if not data:
                raise SystemExit("Serial bridge disconnected; no further commands sent")
            record("RX", data)
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
            return data

        received = bytearray()
        if args.power_cycle:
            print("Listening for physical power-cycle; no reboot command sent", flush=True)
        else:
            send(b"\r")
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                received.extend(receive())
                if re.search(rb"root@w600d-linux:[^\r\n]*#", received):
                    break
            else:
                raise SystemExit("Expected Linux root prompt not found; refusing to reboot")
            if args.restart_readonly:
                guard = (
                    b"if test \"$(findmnt -n -o SOURCE /)\" = /dev/sda2 "
                    b"&& test \"$(findmnt -n -o SOURCE /media/boot)\" = /dev/sda1 "
                    b"&& test \"$(blkid -s PARTUUID -o value /dev/sda2)\" = 24c0d202-02 "
                    b"&& test \"$(blkid -s PARTUUID -o value /dev/sda1)\" = 24c0d202-01 "
                    b"&& findmnt -rn -o OPTIONS / | grep -Eq '(^|,)ro(,|$)' "
                    b"&& findmnt -rn -o OPTIONS /media/boot | grep -Eq '(^|,)ro(,|$)' "
                    b"&& test -w /proc/sysrq-trigger; then "
                    b"echo W600D_RO_GUARD_OK; else echo W600D_RO_GUARD_FAILED; fi\r"
                )
                send(guard)
                received.clear()
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    received.extend(receive())
                    if re.search(rb"(?:^|[\r\n])W600D_RO_GUARD_OK[\r\n]", received):
                        break
                    if re.search(rb"(?:^|[\r\n])W600D_RO_GUARD_FAILED[\r\n]", received):
                        raise SystemExit("USB read-only guard failed; refusing to restart")
                else:
                    raise SystemExit("USB read-only guard not confirmed; refusing to restart")
                send(b"printf b > /proc/sysrq-trigger\r")
            else:
                send(b"sync; systemctl reboot\r")
            received.clear()
        deadline = time.monotonic() + args.timeout
        factory_seen = False
        next_interrupt = 0.0
        while time.monotonic() < deadline:
            received.extend(receive())
            if b"U-Boot 2017.09" in received:
                factory_seen = True
            if factory_seen and b"=>" in received:
                print(f"\nFactory shell intercepted. Journal: {journal_path}", flush=True)
                return
            now = time.monotonic()
            if factory_seen and now >= next_interrupt:
                send(b"\x03")
                next_interrupt = now + 0.05
        raise SystemExit("Factory prompt not captured; no boot-file/environment writes attempted")


if __name__ == "__main__":
    main()
