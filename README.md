# MacBookPro14,3 Ubuntu compatibility

Experimental Ubuntu 26.04.1 compatibility packages for the 15-inch 2017
MacBook Pro (MacBookPro14,3). The current host runs patched
`7.0.14-mbp14343p1`, based on Ubuntu `7.0.0-43.43`. The maintainer confirms
successful suspend/resume tests on this kernel.

[Download the -43 experimental release](https://github.com/gurkein/mbp143-ubuntu-compat/releases/tag/v0.2.0-experimental.1).

The new layout contains **eight DEBs**: kernel image, matching headers and six
source-only DKMS packages. Headers are required for DKMS compilation. The kernel
retains five PCI/ACPI patches; AMDGPU, Thunderbolt and SBS corrections are now
provided by DKMS, alongside T1/Touch Bar, CS8409 audio and BCM43602 Wi-Fi fixes.
DKMS packages target the 7.0 series and use the standard APT/DKMS lifecycle.
An optional **ninth DEB**, i915 0.1-1, was added on November 15 for the
external-attached boot fix, with its own source archive and `SHA256SUMS-i915`.

- [All applied patches: purpose and delivering package](docs/patches.md)
- [Package versions and -43 installation](releases/kernel43/README.md)
- [Exact package manifest](releases/kernel43/packages.json)
- [Compatibility and measured scope](docs/compatibility.md)
- [Known issues](docs/known-issues.md)
- [NVMe protection required for the documented suspend setup](docs/nvme-d3cold.md)
- [External-attached boot: i915 four-lane fix and availability](docs/i915-four-lanes.md)
- [Graphics, EFI and Boot Camp](docs/graphics-and-efi.md)
- [Credits](CREDITS.md) and [licensing](LICENSE.md)

The base release includes eight DEBs, six complete DKMS source archives, the complete
patched kernel source, a project source archive and SHA-256 metadata. Private
signing keys and personalized firmware/NVRAM are excluded.

The detailed historical five-cycle series used T1 0.5 on -42. The -43 result is
user-confirmed; cycle count, dwell and per-device coverage were not enumerated
in this update. On November 15, a separate i915 0.1-1 four-lane package passed
one external-display-attached reboot with both screens active on custom -43.
That package is now available as a separately checksummed release add-on. Repeated/cold boots,
official -43 runtime and new-i915 suspend remain unqualified. Long-duration
sleep and broad peripheral coverage retain their documented limits.

`v0.1.0-experimental.1` remains available as the historical -42 binary/source
snapshot. Existing `kernel/`, `drivers/`, build scripts and offline tests describe
that snapshot. Current -43 patches, configuration and package metadata live in
`releases/kernel43/`; complete current driver sources are accompanying release
assets. Imported work retains its authorship and per-file licenses.
