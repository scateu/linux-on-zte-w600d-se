# Hardware rootfs must not retain Docker runtime markers

The 2026-11-24 Ubuntu USB first boots with `Detected virtualization docker.`
because Docker export preserved `/.dockerenv`. The operating system is
actually running on the RK3568 laptop, not in a container. Systemd's extra
`console-getty.service` competes with the explicitly enabled ttyS2 serial
getty; other container-conditioned services may also behave incorrectly.

Strip runtime markers **after Docker export**, not only during Docker RUN.
The authoritative fresh-image entry remains:

```sh
cd /home/k/codex-workdir-nov-24-2026
JOBS=24 bash scripts/build-display-fixed-image.sh
```

It now applies both the Analogix lane fix and offline archive normalization
before image assembly. `normalize-container-markers.sh` removes only:

- `/.dockerenv`
- `/run/.containerenv`
- `/run/systemd/container`

The tar-stream filter preserves all other member metadata, numeric ownership,
modes, symlinks and hardlink targets; it does not re-extract/repack under
ordinary user ownership. It refuses an existing output archive and validates
that none of the marker paths survive. The shell wrapper retains the original
tar as `artifacts/ubuntu-w600d-rootfs.with-container-markers.tar` before
promoting the clean archive and regenerating its checksum.

This is a build-rootfs correction; it does not require a full USB flash for
the current laptop. On the live USB, after access is restored, inspect and
remove the Docker-created marker and stop/mask only the duplicate console
getty. Keep `serial-getty@ttyS2` and the physical tty1 login. Systemd's
already-selected container mode persists until the next boot, so a clean
reboot is needed to validate normal hardware service behavior.

The user confirmed Ctrl+Alt+F1 reaches the text console. They are asked to
run `sudo systemctl stop console-getty` there to recover UART access; normal
XFCE session completion remains a separate acceptance step.
