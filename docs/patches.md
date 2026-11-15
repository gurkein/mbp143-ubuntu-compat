# Applied patches: purpose and delivering package

Reviewed 2026-11-15 for MacBookPro14,3 / Ubuntu 26.04.1 and
`v0.2.0-experimental.1`, including its November 15 i915 add-on.
This is the index of this project's changes over its Ubuntu/driver baselines;
it does not enumerate every patch already included by Ubuntu or upstream Linux.
Historical -42 sources remain for provenance and are distinguished below.

## Which package supplies which fix?

| Delivering DEB | Published version | Changes supplied |
|---|---|---|
| `linux-image-7.0.14-mbp14343p1` | `7.0.0-43.43+mbp143.1` | Built-in PCI/ACPI changes 0001–0005, with the project's kernel configuration/build packaging |
| `linux-headers-7.0.14-mbp14343p1` | `7.0.0-43.43+mbp143.1` | Matching interfaces required to compile DKMS modules; no separately activated hardware fix |
| `mbp143-t1-dkms` | `0.8-1` | iBridge and Touch Bar support, mode-result correction, ordered automatic S3 handling, Fn forwarding and xremap USB matching |
| `mbp143-audio-dkms` | `0.1-3` | CS8409 Apple audio support, PR220-derived codec recovery and local error propagation |
| `mbp143-wifi-dkms` | `0.2-4` | BCM43602 D0 workaround (0682) and Apple FEM control restoration v3 |
| `mbp143-amdgpu-dkms` | `0.3-1` | AMD VI VRAM initialization/reset correction (0006), plus external-build/API adaptations |
| `mbp143-thunderbolt-dkms` | `0.1-1` | Apple SXFP suspend ordering (0007), with matched core/network modules |
| `mbp143-sbs-dkms` | `0.1-1` | ACPI Smart Battery relative-capacity correction (0008) |
| `mbp143-i915-dkms` | `0.1-1` | Optional add-on: Intel port A four-lane workaround for external-display-attached boot |

The kernel contains **five built-in patches**, not the old eight-patch series.
Changes 0006–0008 are applied to DKMS source exports and delivered by their
module packages. T1, audio, Wi-Fi and i915 changes have their own histories and
are additional to that numbered series. There is no numbered kernel patch 0009
in the published series; the Wi-Fi FEM change is delivered by Wi-Fi DKMS.

[Installation and package list](../releases/kernel43/README.md) ·
[Exact published package metadata](../releases/kernel43/packages.json) ·
[Compatibility and acceptance limits](compatibility.md)

## Built into the custom kernel: 0001–0005

All five arrive with `linux-image-7.0.14-mbp14343p1`, based on Ubuntu
`7.0.0-43.43`. Installing a DKMS package on an official generic kernel does
not add these built-in PCI/ACPI changes to that kernel.

| Patch | Problem addressed | What changes |
|---|---|---|
| [0001 — PCI configuration accessibility](../releases/kernel43/patches/0001-pci-config-accessible.patch) | An unavailable PCI device can return all-one register values; treating those as real configuration can corrupt recovery state. | Adds an accessibility check using Command/Status registers and avoids saving configuration during reset preparation if the device is inaccessible. It is a prerequisite for 0002. |
| [0002 — Preserve saved PCI configuration](../releases/kernel43/patches/0002-pci-save-v3.patch) | Saving inaccessible PCI configuration can overwrite a previously valid snapshot with all-one values. | `pci_save_state()` keeps the existing snapshot and marks it saved rather than reading invalid configuration. |
| [0003 — Reject invalid PCI link status](../releases/kernel43/patches/0003-pci-link-v3.patch) | All-one link-status reads can look like an active link, causing reset/retrain code to accept a device that is unavailable. | Link-status waits return `-ENODEV` on inaccessible reads; readiness checks reject the invalid status before accepting link activity. |
| [0004 — ACPICA parent-derived PCI bus](../releases/kernel43/patches/0004-acpica-parent-bus.patch) | During D3cold-to-D0 restoration, a bridge's primary-bus register can still be zero; caching it can misaddress an ACPI PCI configuration region. | Keeps the bus number already obtained from the parent bridge instead of overwriting it with the not-yet-restored primary-bus register. |
| [0005 — Apple native PME ownership](../releases/kernel43/patches/0005-apple-native-pme.patch) | Apple's special `_OSC` path excludes native PCIe PME control, preventing the native PME route used by the documented suspend design. | Uses `calculate_control()` for the Apple path so the OS requests the controls supported by this kernel, including native PME. Boot arguments can still select a different route; the patch alone does not establish readiness. |

Original sources, adaptation notes, application order and hashes are in the
[current kernel manifest](../releases/kernel43/patches/manifest.json) and
[series](../releases/kernel43/patches/series). These are backports/local
adaptations of the linked Linux/ACPICA work, not claims of original authorship.

## Delivered through DKMS: 0006–0008

| Patch and delivering package | Problem addressed | What changes and what remains open |
|---|---|---|
| [0006 — AMD VI VRAM](../releases/kernel43/patches/dkms/0006-amdgpu-vi-vram.patch), `mbp143-amdgpu-dkms 0.3-1` (`amdgpu`) | Apple switchable AMD GPUs can need a reset when firmware leaves the VRAM base uninitialized. | Adds an Apple-subsystem/zero-VRAM-base condition to the existing VI reset predicate, preserving Ubuntu -43 reset quirks. This is not a Radeon power-off fix; Radeon remains available for external displays. General boot evidence does not qualify every GPU resume/stress route. |
| [0007 — Thunderbolt SXFP](../releases/kernel43/patches/dkms/0007-thunderbolt-sxfp-v3.patch), `mbp143-thunderbolt-dkms 0.1-1` (`thunderbolt`, `thunderbolt_net`) | Apple's Thunderbolt firmware power-down sequence needs coordination while the software connection manager can still access the switch. | Adds an Alpine Ridge pre-suspend-noirq callback. On the applicable Apple/firmware-suspend path, clears switch CS_20 bit 26 before calling `SXFP(0)`; skips ICM-managed switches and absent firmware methods. This does not establish native Thunderbolt networking or docked-suspend acceptance. |
| [0008 — SBS relative capacity](../releases/kernel43/patches/dkms/0008-acpi-sbs-relative-capacity.patch), `mbp143-sbs-dkms 0.1-1` (`sbs`) | Battery percentage can use the wrong Smart Battery register when absolute state of charge is read as relative state of charge. | Changes the capacity command from `0x0e` to relative-state-of-charge `0x0d`. It does not repair a stale UPower cache, explain voltage anomalies or qualify battery health. |

The [module patch manifest](../releases/kernel43/patches/module-patches.json)
records upstream links, local backports and hashes. SBS attribution includes
Itay Shem-tov; AMD and Thunderbolt notices remain with their original sources.
The module source baselines are Ubuntu `7.0.0-43.43`.

## T1 / Touch Bar: `mbp143-t1-dkms 0.8-1`

One package supplies both `apple-ibridge` and `apple-touchbar`. The base driver
comes from Ronald Tschalär and subsequent contributors, through the
[AJ-dev-i60 wrapper](https://github.com/AJ-dev-i60/t1-touchbar), pinned at
`20d65c7b0fe6d05ea9734f869b27384a62de5109`.

| Included change | Problem addressed | Implementation |
|---|---|---|
| Mode-result normalization | A successful USB output transfer returns a positive byte count, which the worker could interpret as failure. | Normalizes the expected one-byte mode write to zero, rejects other nonnegative byte counts as `-EIO`, and preserves actual errors so the worker commits only a successful mode change. [Historical isolated patch](../drivers/t1/patches/mode-result.patch). |
| Ordered S3 firmware transaction | The existing firmware notification route and asynchronous Touch Bar I/O need ordering around real deep S3 transitions. | Coordinates `SOCW(0)` sleep and `SOCW(1)` return with the real S3 target and a paired cleanup path. Serializes mode/display USB I/O, invalidates stale cached state after return, and requires successful refresh before recording completion. |
| Failure handling and automatic subsequent cycles | A failed or incomplete transaction must not be silently treated as a successful reusable cycle. | Retains terminal failure state, firmware-return/refresh checks and read-only `s3_status` / `s3_completed`. Automatic model-specific handling replaces the historical once/repeat activation parameters; system policy still decides whether sleep is allowed. |
| Remapped-keyboard Fn forwarding (0.7) | After a remapper grabs keyboard input, rejecting the forwarded device prevents Touch Bar Fn changes. A single shared Fn flag also mishandles multiple input sources. | Accepts the applicable forwarded keyboard and tracks Fn state per attached keyboard, aggregating pressed state and clearing it on detach. Existing macOS-style mappings are preserved. |
| USB xremap identity (0.8) | A forwarded xremap keyboard can use USB identity rather than SPI, so SPI-only matching misses it. | Adds narrow matching for USB `1234:5678`, `KEY_FN` capability and the name `xremap` or `xremap pid=…`, alongside existing SPI/internal Apple USB paths. [Exact patch](../releases/kernel43/dkms-tools/patches/t1-xremap-usb-identity.patch). |

The [baseline-to-automatic patch](../drivers/t1/patches/baseline-to-automatic-package.patch)
is the historical 0.6 reconstruction, not the complete current 0.8 diff.
The complete 0.8 source archive in the release is authoritative for all rows.
The driver does not add Touch ID enrollment or PAM authentication. Historical
five-cycle acceptance was on 0.5; later versions and kernel stacks retain their
own scoped observations in the compatibility guide.

## Audio: `mbp143-audio-dkms 0.1-3`

The package installs `snd-hda-codec-cs8409`, using the kernel-7 Apple codec
baseline from the [oliveira11670 fork](https://codeberg.org/oliveira11670/snd_hda_macbookpro)
(commit `53dd5fae334a101e8a940f1242bd6859dca14273`), derived from David Jo's work.
This provides model-specific codec, amplifier and audio routing support beyond
the stock codec path. The added recovery changes are:

| Patch | Problem addressed | Implementation |
|---|---|---|
| [PR220-derived recovery](../drivers/audio/upstream-220-kernel7.patch) | After codec power loss, amplifiers/CS42L83 can remain reset while ordinary cached register restoration leaves sound unavailable. | Detects lost setup using the actual codec GPIO state, clears stale driver setup state and reruns boot programming through the init/resume path. Source: Francisco Beltran Millalen's [PR220](https://github.com/davidjo/snd_hda_macbookpro/pull/220), commit `b8bc4d935335a9a5476c478d491adf9b18012f58`. |
| [Local error propagation](../drivers/audio/error-propagation.patch) | Recovery could log a failed programming step but still return success, or leave unsolicited event dispatch blocked. | Returns setup/init errors, reports still-unprogrammed hardware as `-EIO`, always releases the event block, and propagates codec-init failure before resume regmap synchronization. |

[Combined historical diff](../drivers/audio/combined-kernel7.patch).
The package also builds the common audio component for ABI comparison while
installing only the codec module; it does not silently replace the complete HDA
stack. Working speakers/microphone do not qualify every output route.

## Wi-Fi: `mbp143-wifi-dkms 0.2-4`

| Patch | Problem addressed | Implementation |
|---|---|---|
| [0682 — Keep BCM43602 in D0](../drivers/wifi/0682-brcmfmac-bcm43602-keep-d0-on-suspend.patch) | The selected MacBookPro14,3 BCM43602 suspend route needs to avoid the PCI sleep transition that loses device state. | Calls `pci_save_state()` in the driver's D3-entry callback for `14e4:43ba`, subsystem `106b:0173`; the resulting `state_saved` state skips the PCI prepare-to-sleep power transition. Taken from [Omarchy PR596](https://github.com/omacom/omarchy-pkgs/pull/596), pinned `1aac35af814bc9b3e0fa7669cdb9e42ebf277795`; other recipe patches were not imported. |
| [Apple FEM control restoration v3](../releases/kernel43/dkms-tools/patches/brcmfmac-apple-fem-control-v3.patch) | After a chip power-on reset, supported Apple BCM43602 boards can lose the discrete front-end-module pin mode needed for 5 GHz association. | Restores ChipCommon chipcontrol bit 4 before firmware download, only if clear and on the listed Apple subsystem IDs (`0157`, `015a`, `0173`). This is Sergey Armodin's v3 proposal; the full attribution/source URL is retained in the patch. |

Both changes coexist: FEM restoration does not replace the D0 workaround.
The package builds/installs `brcmfmac` with matching WCC/CYW/BCA vendor modules;
`brcmutil` remains kernel-owned. Model-specific NVRAM is separate and is not
shipped by the DEB. Neither change establishes a cause for all observed
connection loss or packet loss; long-term stability remains unqualified.
The upstream FEM description's tests are not additional tests by this project.

## Intel display: `mbp143-i915-dkms 0.1-1`

This optional ninth DEB supplies `i915` from Ubuntu `7.0.0-43.43` with a local
adaptation of [Theo Andersen Carton's MacBookPro11,5 v3 proposal](https://www.mail-archive.com/intel-gfx@lists.freedesktop.org/msg385041.html).
The patch is included as `i915-mbp143-four-lanes.patch` in the
[complete i915 source archive](https://github.com/gurkein/mbp143-ubuntu-compat/releases/download/v0.2.0-experimental.1/mbp143-i915-0.1-dkms-source.tar.gz).

The failure was an internal panel with no usable modes when booting with an
external display connected: the Intel link ceiling was two lanes at 324000.
The quirk selects the normal four-lane path only for exact Apple Inc. /
MacBookPro14,3 DMI, Kaby Lake and port A. VBT/sink limits, normal link training,
rate selection and gmux ownership remain in force.

One external-attached reboot on custom -43 passed with four lanes and both
native-resolution screens active. Repeated/cold boots, official -43 runtime
and suspend with the new i915 remain unqualified. See
[downloads, full explanation and recovery](i915-four-lanes.md).

## Build and packaging adaptations

These changes make the patches deliverable; they are not additional claims
that a hardware defect is fixed.

| Delivered by | Adaptation and purpose |
|---|---|
| Custom kernel image/headers and source archive | Matching custom release/configuration and Debian packaging. The source recipe omits building the unrelated libc development package; the [historical packaging patch](../kernel/packaging/0001-omit-libc-package.patch) records that packaging change. Header packages supply the matching DKMS build interface. |
| All seven DKMS packages | Source-only `/usr/src` delivery, normal APT/dh-dkms lifecycle, 7.0-series x86-64 build policy, depmod selection, ABI checks and initramfs handling. Future 7.0 builds are attempts subject to API/ABI checks, not guarantees for every kernel. Signing uses the recipient's local policy; no private key is supplied. |
| T1/audio packages | Exclude obsolete generic T1/audio DKMS identities from automatic installation, avoiding competing copies. This is package selection policy, not another firmware/PM fix. |
| Wi-Fi package | Include the matching core/vendor modules in dracut initramfs generation so early boot does not silently use an incomplete/original set. Standard dh-dkms lifecycle replaces the retired custom cache-import workflow. |
| AMDGPU package | Adapt trace-header lookup for an external build; use `drm_exec_obj()` iteration across header macro variants; select a legacy fence-initialization helper and guard the optional panel `force_pwm` field when required by target headers. These preserve intended operations across supported 7.0 interfaces. |
| Thunderbolt package | Build core and network modules together with their matching public header, checking changed exports and consumers to avoid a mismatched pair. |
| Audio package | Adapt the existing Apple codec sources to the kernel-7 layout/build and validate compatibility with retained common-helper exports. |
| i915 package | Adapt four trace-header include paths for external compilation, include the unchanged neighboring `intel_ips.h`, and leave `kvmgt` kernel-owned while checking retained-consumer/export ABI. |

Source archives and their `source-manifest.json` / `source-origin.json` records,
where supplied, are authoritative for the exact published inputs. Some embedded
preparation-time status strings are historical; current acceptance is in the
dated compatibility/display guides. Packaging reference recipes retain historical
paths and are not generic installation commands.

## Required or related settings that are not driver patches

| Setting or helper | Delivery and purpose |
|---|---|
| Internal NVMe D3cold protection | **Not installed by any driver DEB.** The [NVMe guide](nvme-d3cold.md) installs the helper/service that keeps `d3cold_allowed=0`, required by the documented suspend readiness policy. |
| T1 `skip_acpi_power=1`, native PME route, sleep readiness/runtime restoration | Host boot/module/systemd policy, not a switch automatically enabled by installing the T1 DEB. Driver transaction checks do not replace host readiness checks. Preserve failure latches and do not replay old experiment tickets. |
| Wi-Fi model-specific NVRAM | Separate firmware/configuration prerequisite; private personalized data and firmware are excluded from the DEBs. |
| Intel preference, Radeon visible to Mutter, Windows Radeon wrapper | Separate [graphics/EFI configuration](graphics-and-efi.md), not installed by the i915/AMDGPU DEBs. The wrapper switches firmware preference for Windows; it is not a kernel patch. |
| Keyboard mappings and desktop preferences | Separate user configuration. T1 input matching does not install xremap or change its key mappings. |
| UPower cache correction | A historical userspace cache recovery, not a fix delivered by the SBS patch. Voltage/battery-health questions remain separate. |

## Historical layout and verification limits

The retained `kernel/`, `drivers/` and older provenance/release notes describe
the -42 publication, whose kernel contained seven backports and whose driver
packages were later reorganized. The later eight-patch intermediate kernel
layout is also superseded: current -43 has only 0001–0005 built in, with
0006–0008 supplied by DKMS. Do not reapply module patches to the current kernel
source or install old intermediate mode-result/phase-trace packages to obtain
fixes already included in T1 0.8.

The original -43 release assets remain unchanged; i915 is a later add-on with
`SHA256SUMS-i915`. Installing a package, compiling it successfully, selecting
its module and actually loading it are distinct checks. Functional device and
suspend acceptance require their own observations. This inventory does not
schedule hardware tests or establish general suspend safety.

For authorship and licensing, see [credits](../CREDITS.md),
[third-party notices](../THIRD_PARTY_NOTICES.md) and the original per-file notices.
