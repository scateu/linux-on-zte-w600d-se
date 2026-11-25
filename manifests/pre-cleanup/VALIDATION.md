# Snapshot validation — November 25, 2026

Collection imported 340 source files from the local research and `trash`.
Original source directories and physical USB/eMMC contents were not changed.
The new consolidated guides and source/checksum maps are additional files.

Completed checks:

- SHA-256 verification of every file listed in `SHA256SUMS`, including the
  organized source recipe, reference files, logs, artifacts and new guides.
- All four copied tested outputs matched the original build's saved
  `artifacts/kernel-tested/SHA256SUMS`: Image, DTB, System.map and config.
- Python syntax parsing passed for the snapshot collector and seven active
  recipe Python scripts. No bytecode/cache files were generated.
- Bash syntax checks passed for 24 active recipe shell scripts.
- The copied kernel config passed the existing required-built-in validator.
- On `trash`, where dtc is installed, the existing board validator passed
  for the same SHA-256-identified final DTB: 2 GB RAM, native EDID, PWM2,
  panel GPIOs, keyboard power, VP1 graph, I/O supplies and disabled Android
  storage nodes. The host config validator passed too.

These checks validate the handoff and known build outputs; they do not replace
physical acceptance of trackpad, DHCP, full visible XFCE or Android fallback.
No kernel/rootfs rebuild, flash, live rootfs repair, reboot or physical-device
read-back was performed. Validation read only snapshot/host artifact files.

To verify the copy again from the snapshot root:

```sh
python3 tools/collect-snapshot.py verify
```

`SOURCE-MAP.json` records original paths, original digests and original sizes.
Only `docs/DIY-FROM-UPSTREAM.md` has deliberate path/config-location adjustments;
its unchanged source is retained in the archive. `SHA256SUMS` records the current
snapshot bytes, including that adjusted guide, and excludes itself.
