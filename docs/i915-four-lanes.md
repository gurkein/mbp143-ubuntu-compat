# External-display-attached boot: Intel four-lane workaround

## Result — 2026-11-15

On MacBookPro14,3, booting with an external display attached could leave the
internal panel without usable modes. A new source-only package,
`mbp143-i915-dkms 0.1-1` (DKMS `mbp143-i915/0.1`), applies an Intel port A
four-lane workaround. After installation and a normal reboot with the external
display attached, the maintainer confirmed that the problem was fixed.

| Check | Before | After the reboot |
|---|---|---|
| Kernel | Patched `7.0.14-mbp14343p1` | Same kernel |
| Internal panel | No usable modes | 2880×1800 at approximately 60 Hz |
| Intel maximum lanes | 2 | 4 |
| Intel maximum link rate | 324000 | 324000 |
| Active Intel link | No active CRTC | Four lanes, port clock 324000, 30 bpp |
| External Radeon display | 3840×2160 at 60 Hz | Same, alongside the internal panel |

The loaded i915 GNU build ID and source version matched the selected signed
DKMS module, and selected/initramfs module hashes matched installation records.
This is one successful external-attached normal reboot with the lid open.
Repeated warm/cold boots, further lid/hotplug checks, official-kernel runtime
and suspend with this i915 have not been qualified. Earlier suspend results
do not establish acceptance for the new display stack.

## Scope and provenance

The patch adapts [Theo Andersen Carton's MacBookPro11,5 v3 proposal](https://www.mail-archive.com/intel-gfx@lists.freedesktop.org/msg385041.html)
to exact Apple Inc. / MacBookPro14,3 DMI, Kaby Lake and port A. It enables the
normal i915 four-lane path while preserving VBT/sink limits, link-rate selection,
link training and gmux ownership. The original firmware register value was not
captured before modification; the exact origin of the two-lane ceiling remains
unproven. Radeon must remain available to Mutter for external output.

The package uses Ubuntu `7.0.0-43.43` i915 sources. Full compilation/modpost and
ABI checks passed against custom `7.0.14-mbp14343p1` and official
`7.0.0-43-generic`: 1,254 imports checked and 47 exports with no changed CRCs
on each target. Build success on official -43 does not establish runtime success.

## Package availability and installation boundaries

Published on 2026-11-15 as an optional ninth DEB in
[`v0.2.0-experimental.1`](https://github.com/gurkein/mbp143-ubuntu-compat/releases/tag/v0.2.0-experimental.1),
alongside its complete source archive and a separate checksum file:

- [mbp143-i915-dkms_0.1-1_all.deb](https://github.com/gurkein/mbp143-ubuntu-compat/releases/download/v0.2.0-experimental.1/mbp143-i915-dkms_0.1-1_all.deb)
- [Complete DKMS source](https://github.com/gurkein/mbp143-ubuntu-compat/releases/download/v0.2.0-experimental.1/mbp143-i915-0.1-dkms-source.tar.gz)
- [SHA256SUMS-i915](https://github.com/gurkein/mbp143-ubuntu-compat/releases/download/v0.2.0-experimental.1/SHA256SUMS-i915)

The original eight-package assets and their `SHA256SUMS` remain unchanged.
The i915 add-on is verified separately; downloading only the original eight
DEBs does not install this fix. From a directory containing the add-on DEB,
source archive and checksum file, after reviewing the recovery/signing notes:

```sh
sha256sum -c SHA256SUMS-i915
sudo apt install --simulate ./mbp143-i915-dkms_0.1-1_all.deb
sudo apt install ./mbp143-i915-dkms_0.1-1_all.deb
```

Matching kernel headers, DKMS build dependencies and disk space are required.
The package compiles i915 locally; allow compilation time and monitor ordinary
system thermal management. No exact duration is promised. Retain the source
archive and upstream license notices with redistribution.

The separately built package uses standard APT/dh-dkms hooks, local signing
policy, depmod and initramfs handling. It ships no private keys or precompiled
modules. Its 7.0-series autoinstall scope also replaces i915 on matching official
kernels: an official kernel menu entry is not an untouched original-i915 fallback
after installation. Preserve original modules and initramfs for recovery.

Activation requires a planned normal reboot and verification of selected,
initramfs and actually loaded i915, followed by checking both physical displays.
The maintenance installation needed an explicit standard initramfs refresh for
official -43 after the trigger refreshed only custom -43; verify every retained
target rather than assuming all images were updated. No live i915 unload, mux
switch, EDID override or forced link-rate command belongs to this fix.

Rollback uses normal APT removal of `mbp143-i915-dkms`, restoration/verification
of original module selection and regenerated initramfs for each retained target,
then a planned normal reboot. Keep a matched original-module/image backup in
case standard restoration fails. Booting with the external display disconnected
and attaching after login remains a recovery option for an affected machine.
