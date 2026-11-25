# Reference material and provenance

`factory-device-tree/` contains selected original Android tree dumps from
`ref/backups/`. `original-backup-SHA256SUMS` is the original larger backup's
list, not a checksum command for this subset. Raw bootloader, misc, Android
and full eMMC images were not imported into this snapshot.

`upstream-linux-7.3.6/` contains the common RK3568 DTSI files as they existed
in the build host's pinned kernel source. Obtain the complete upstream source
for compilation; this is only a reading/provenance excerpt.

`download-metadata/` contains the November 24 kernel release JSON and publisher
checksum lists used by the build. A checksum against an HTTPS-downloaded list
was checked in the original build; this snapshot does not claim independent
PGP-signature verification. It does not re-determine the latest kernel version.

`u-boot-research/` preserves the previous research's own directory structure,
including historical two-U-Boot demo assets, keymaps, recovery/partition notes
and tools. These old boot scripts/binaries are not the new mainline USB layout
and must not be installed onto a new machine indiscriminately.

The CloudBook source/reference tree lives within the recipe at
`../build/linux-7.3.6/reference/cloudbook-mainline-6.12/` because the kernel
builder expects its Naneng PHY patch there. Its additional board DTS/patches
remain comparison material only.

For every copied file's original local or SSH path and original SHA-256,
consult `../manifests/SOURCE-MAP.json`. Current snapshot hashes, including
newly written consolidated documentation, are in `../manifests/SHA256SUMS`.
