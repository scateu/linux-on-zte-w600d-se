# Tested artifacts and historical build records

`kernel-tested/` is a copy of `trash`'s corrected
`artifacts/kernel-edp-lanes-fix/`, not its stale canonical kernel output.
It contains Image, final v3 DTB under the installed filename, exact config,
System.map, and the saved build checksum list.

| File | Recorded SHA-256 |
| --- | --- |
| Image | `0b0c71f33eed1057e9857e65ff60b9fecb248d7ed394408af4c240fb64c8638d` |
| rk3568-zte-w600d-mainline.dtb | `4e7156892cfaa29da5d73b217d6e846c01af9b6e6d449323192463dc551e942d` |
| System.map-7.3.6-w600d-usb | `95bd2d3c69017ce811bc3cfebe745314f111155dea49951a9feb3c1a21460641` |
| config-7.3.6-w600d-usb | `13a567071ccd42b1dab2baa32cc58e7f9471f1ec19a19969b5e9fbdfc9bd597a` |

These identify the copied build outputs. They are not a claim of physical-USB
read-back verification. The Image is 43792896 bytes, from the kernel build
that produced the November 24 approximately 17:20 FAT file-only update.

The boot files alone are not a complete OS image. Matching modules and rootfs
remain on the host or can be rebuilt using the included recipe. A new build
can also have a different Image hash because of build timestamps/environment;
use its own generated checksums and verify actual hardware behavior.

`build-records/` preserves package versions, environment, partition metadata,
rootfs hash, and the **historical** original full-image hashes. Image was later
changed on the physical USB and the host rootfs tar was later normalized;
these facts must not be combined into a false claim that an old whole-disk
image already contains both fixes.

The old recipe packaging script/tarballs also predate some fixes. To distribute
the complete source handoff, archive this entire snapshot rather than using
that script's old hardcoded file list.
