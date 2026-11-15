# Source-only DKMS driver migration

This retained maintenance reference includes dated and superseded deployment
paragraphs. Use the [current patch/package inventory](../../../docs/patches.md)
for the -43 release and seven DKMS families, including the i915 add-on.

Current policy supports automatic build/install throughout the **7.0** kernel
series (`^7[.]0([.-]|$)`). Matching kernel/header installation invokes Ubuntu's
standard DKMS hooks; no per-ABI permission is needed for -42, -43 or later 7.0
updates. Other series are excluded. Kernel patches and suspend qualification
remain separate from module compilation.

| Source package | DKMS identity | Modules |
|---|---|---|
| mbp143-t1-dkms 0.8-1 | mbp143-t1/0.8 | apple-ibridge, apple-touchbar |
| mbp143-audio-dkms 0.1-3 | mbp143-audio/0.1 | snd-hda-codec-cs8409 |
| mbp143-wifi-dkms 0.2-4 | mbp143-wifi/0.2 | brcmfmac, WCC, CYW, BCA |
| mbp143-sbs-dkms 0.1-1 | mbp143-sbs/0.1 | sbs |
| mbp143-thunderbolt-dkms 0.1-1 | mbp143-thunderbolt/0.1 | thunderbolt, thunderbolt_net |
| mbp143-amdgpu-dkms 0.3-1 | mbp143-amdgpu/0.3 | amdgpu |

DEBs contain `/usr/src` source trees and DKMS configuration, not precompiled
modules or signing keys. Corresponding standalone source tarballs are generated
beside the DEBs. The source manifests record all inputs. Existing driver C/header
inputs are retained; independent DKMS builds have matching source versions.
The audio build also compiles its common component helper to verify unchanged
export CRCs, but installs only the codec. Wi-Fi retains the kernel's `brcmutil`.

`AUTOINSTALL=yes` applies to 7.0. Package setup installs into existing matching
kernel images with headers and retains already-installed builds when only
packaging changes. Header hooks automatically handle future matching kernels.
Headers left behind after a kernel image was removed do not cause retroactive
installation during package setup. Source/API compatibility is checked on each
build; build success is not hardware or suspend certification.

Legacy `apple-ib-drv/0.1` and `mbp143-cs8409/0.1` registrations were retired from
official -42. Their source trees are retained for explicit rollback. Package-owned
`/etc/dkms/apple-ib-drv.conf` and `/etc/dkms/mbp143-cs8409.conf` set
`AUTOINSTALL=no` and an empty matching kernel regex, preventing duplicate
automatic installation even if the old identities are registered again.
Temporary per--42 overrides and its separate dracut/depmod rules are superseded
by series-wide package rules. Generic Wi-Fi dracut inclusion covers all eight
required modules for matching kernels. No PM/readiness protection is removed.

## Wi-Fi FEM source package — 2026-11-08

Wi-Fi 0.2-4 is installed using the unmodified Ubuntu dh-dkms 3.2.2 lifecycle
snippets (`debhelper/`). It calls the distribution's `common.postinst` and
removes the old source version in standard prerm before dpkg unpacks sources.
The predecessor's installed prerm was repaired to that same standard for this
transition. No temporary source retention or cache import is used. Signing
configuration is unchanged: custom kernel local certificate, official targets
normal default MOK. Different drivers need not share the same signing key.

The existing D0 quirk is retained and FEM v3 applies with fuzz=0. All source
manifest entries and all eight selected/image hashes pass on official -42/-43
and custom -42. Native all-headers policy also built the retained -31 header
target; no -31 image was installed. Loaded Wi-Fi remains old until normal boot.
No reload, reboot or PM test ran. Full custom -43 build remains stopped.

Build the one source-only package with:

```sh
python3 scripts/drivers/dkms/build-packages.py --role wifi --output <new-directory>
```

Final artifacts: `experiments/kernel-42/candidates/wifi-fem-dkms-standard/`.
Install through normal APT. The earlier `install-wifi-fem.py` custom import
workflow is retired; do not run it. After normal custom-kernel reboot use
`verify-installed.py --require-activated` and confirm Wi-Fi functionality.
[Verified deployment](../../../results/2026-11-08/wifi-standard-install/verification.json).

Full-kernel series remain 0001–0008. Patch 0008 is ACPI SBS battery reporting;
PCI/ACPICA/PME/AMD/Thunderbolt changes remain in the full kernel. The FEM update
does not replace those changes or qualify official kernels for suspend.
See the [Wi-Fi candidate review](../../../docs/HARDWARE-COMPATIBILITY-ROADMAP.md#wi-fi-dkms-candidate-apple-bcm43602-fem-control-formerly-0009--2026-11-08).


## Standardized hardware delivery — 2026-11-08

The current six DEBs and source archives are in packages/mbp143-dkms-7.0/.
All identities use the 7.0 build policy. New SBS/Thunderbolt/AMDGPU packages use
Ubuntu dh-dkms lifecycle snippets and native builds. Their base is Ubuntu
7.0.0-43.43. AMDGPU adapts trace paths and older DRM interfaces. Thunderbolt
builds its core and network companion with a matching public header. Strict ABI
checks validate imports and all retained consumers of changed exports.

The orphan -31 headers/caches were removed after initial verification. Keep
headers aligned with installed images to avoid rebuilding obsolete targets.
After normal boot run verify-installed.py --require-activated and check
battery, graphics and Thunderbolt I/O. Module patches 6–8 have a retirement
checkpoint after activation before future kernel-source preparation.

## Preparation and checks

`build-packages.py --output <new-directory>` exports clean reviewed source and
creates three source-only DEBs and tarballs. Never overwrite a dated candidate.
`validate-builds.py` checks the initial isolated DKMS output, exact source inputs, source
versions, signatures, the T1 peer dependency and the APT replacement plan.
`verify-abi.py` runs inside each build and rejects imported-symbol/shared-helper
CRC mismatches. This checks module ABI, not hardware behavior.
For complete replacement stacks, paired exports come from the rebuilt modules;
kernel-retained helper exports must still match. This avoids incorrectly
rejecting a complete Wi-Fi core/vendor replacement while retaining the HDA
helper ABI protection. `test-abi-policy.py` verifies both cases and import errors.

The first isolated build is under
`experiments/kernel-42/candidates/dkms-migration-v1/isolated-dkms/`; final source
packages were under `experiments/kernel-42/candidates/dkms-migration-v3/`.
v2 added the portable original-module restoration hook used during disposable
installation testing. Its first live validation detected DKMS skipping matching
unversioned modules, and the transaction restored its baseline. v3 adds scoped
DKMS version overrides and standard batched initramfs triggers. C/header inputs
are identical across these candidates. Preserve the initial failed-attempt
backup as evidence; no driver was reloaded during that attempt or rollback.
Current series-wide DEBs/source archives and manifests are under
`experiments/kernel-42/candidates/dkms-series-70-release/`. C/header inputs and
DKMS source versions are unchanged; revision -3 changes packaging/build checks.

## Series-wide upgrade and rollback

`install-series70.py --install` is a baseline-specific transition from revision
-2, not a generic repeatable installer. It backs up source DEBs, configuration,
module/DKMS trees and images, preserves cached working builds during the old
prerm handoff, removes temporary target rules, then installs revision -3.
Future package-only upgrades retain unchanged DKMS-source-version builds.
Actual driver-source updates must use a new DKMS source version.

Use `sudo python3 scripts/drivers/dkms/install-series70.py --rollback <backup>`
before earlier official-target or full-migration rollback helpers. Source DEBs
include neither signing keys nor firmware blobs. The current custom-kernel
module hashes, loaded state and readiness manifest are preserved; a packaging
policy upgrade does not require a reboot to activate new driver code.
Kernel targets added after a policy backup must be reviewed before replaying
its baseline rollback; the helper checks this before making changes.

The official -43 image/headers 7.0.0-43.43 have now been installed and all three
current identities built/installed automatically by package hooks. No target
override or manual DKMS build/install was used. Eight selected/image hashes
and ABI/signature/dependency checks pass. The official kernels have not been
booted with these modules and the unchanged readiness helper rejects their PM
use. Source/build success does not establish full-kernel patch coverage.

## Historical first migration and rollback

The migration helper is specific to the recorded binary-package baseline.
Do not rerun its install path on an already migrated system.

```sh
sudo python3 scripts/drivers/dkms/migrate-installed.py --preflight
sudo python3 scripts/drivers/dkms/migrate-installed.py --install
```

It first tests DKMS install/uninstall using private disposable trees and verifies
that duplicate originals survive. The live migration preserves exact binary
DEBs, the complete custom-kernel module tree, legacy DKMS trees, readiness
manifest/helper and initramfs under `/var/backups/mbp143-dkms-migration/<timestamp>`.
Only the old custom-kernel T1 DKMS registration is retired. The official -42
module files, kernel image/headers, GRUB, keyboard maps, sleep policy and all
26 old PM reports are retained unchanged.

DKMS normally archives same-named originals. `restore-originals.py` copies
non-DKMS originals back to their paths after installation while retaining the
DKMS archive for uninstall. Active `/updates/dkms` belongs to the new modules.
The scoped signing configuration uses a root-only copy of the existing kernel
signing key. Private key contents are never included in source packages,
repository evidence or logs. Newly rebuilt vendor helpers are signed too.
`/usr/share/dkms/modules_to_force_install/<package>` requests version comparison
override only for each new DKMS identity, so even same-source unversioned modules
are actually installed. Build-exclusion, ABI validation and PM checks remain.
The package trigger refreshes initramfs after install, upgrade and removal.

After installation, eight selected/image hashes and the T1 dependency are
verified. The manifest records the installation boot ID; readiness refuses
suspend until a normal reboot. This distinguishes installed DKMS provenance
from matching source versions in modules loaded before migration. The same
driver source is not proof that the new build has been loaded.

```sh
sudo python3 scripts/drivers/dkms/migrate-installed.py --rollback /var/backups/mbp143-dkms-migration/<timestamp>
```

Use this rollback before older package-layout rollback helpers. It restores
binary packages, custom-kernel/legacy-DKMS trees, the old readiness helper and
manifest, and the verified image. No live unload/rebind, reboot, suspend or guard
reset occurs. Existing PM failure latches and consumed tickets must not be
removed to force a test. Normal reboot and interactive Fn/audio/Wi-Fi checks
remain separate activation steps; no PM transition is authorized by packaging.

## Read-only activation verification

```sh
sudo python3 scripts/drivers/dkms/verify-installed.py
# After a planned normal reboot:
sudo python3 scripts/drivers/dkms/verify-installed.py --require-activated
```

The verifier checks package/DKMS registration, all installed source-manifest
entries, selected source versions/signatures, T1 dependency/keyboard handlers,
boot provenance, normal-readiness result and dpkg audit. It performs no PM
operation or network reconfiguration. Confirm Fn/Touch Bar, speakers, microphone
and Wi-Fi interactively; source versions alone do not qualify these functions.

T1 0.8 adds narrow USB xremap identity matching alongside SPI support. All
three target builds/images pass. On November 10, normal-boot activation and
physical/xremap handler attachment were verified; the user reports no problems
with the installed DKMS set. Individual Fn combinations were not enumerated. The iBridge C source is unchanged.
