# Compatibility and acceptance scope

Evidence dates: detailed component matrix and controlled cycle data below are
from 2026-11-04. On 2026-11-14, the maintainer confirmed the current machine is
running patched `7.0.14-mbp14343p1` (`7.0.0-43.43+mbp143.1`) and reported that
it passed suspend/resume tests. The conditions and component checks for those
tests were not enumerated here. Host model: MacBookPro14,3, Intel i7-7820HQ,
Intel HD 630 plus Radeon Pro 560, BCM43602, Cirrus CS8409 and Apple T1. Ubuntu
26.04.1, GNOME/Wayland.

| Component | Observed result | Qualification limit |
|---|---|---|
| Internal display/input | Internal panel 2880×1800/~60 Hz after one external-attached reboot with i915 0.1-1 on custom -43 | November 15 display result; input retains earlier scope. Repeated/cold boots, official -43 runtime and new-i915 PM unqualified |
| Windows Boot Camp | Working through the Radeon EFI wrapper in the maintenance setup | Direct Windows boot under persistent Intel preference was unreliable; see the graphics/EFI guide |
| External display | 3840×2160/60 Hz through Radeon alongside the internal panel after one attached reboot with i915 0.1-1 | November 15 custom -43 only; keep detached boot for recovery. No new lid/hotplug or suspend acceptance |
| Touch Bar | 0.6 uses automatic S3 handling; five-cycle hardware evidence was recorded on 0.5 | Firmware return/cache refresh and transaction-error checks retained; version changes and 0.6 source/ABI checks are described in the release notes |
| Touch ID | Not working / unsupported in this bundle | [T1Bridge reports enrollment on MacBookPro14,3](https://github.com/standardagents/t1bridge#supported-hardware); this is a separate experimental stack, not integrated or validated with this Ubuntu bundle |
| Speakers/microphone | PR220 0.1-1; user-confirmed after the five-cycle series | No new audio recording collected during that final confirmation |
| Headphones/USB-C audio | Earlier working evidence | Not comprehensively retested after the current repeat series |
| Wi-Fi | Association and short traffic checks completed | Sustained behavior and controlled band/environment comparisons remain unqualified; see test scope below |
| Bluetooth | Normal-boot working evidence | Broad post-resume pairing/reconnection not qualified |
| Camera | Normal-boot decoded 1280×720 MJPEG at 30 fps | No broad repeat-resume camera coverage |
| USB Ethernet | Post-series I/O passed on both distinct downstream trees at 1 Gbit/s | Adapter absent during sleeps; one missing IPv4 default recovered by saved-profile reconnect |
| Thunderbolt/xHCI | Two xHCIs reinitialize per cycle; later USB traffic passed | Native Thunderbolt/docked/broader protocols not qualified |
| NVMe | Boot and per-cycle file fsync/read passed in the historical 0.5 series | [Install/preserve D3cold protection](nvme-d3cold.md); the 2026-11-14 -43 report does not enumerate storage checks |
| Battery reporting | UPower capacity-cache error corrected by restart; voltage dip unresolved | Percentage and battery behavior need separate qualification |
| Patched kernel -43 | Current kernel per maintainer confirmation; suspend/resume tests reported as passed | Test count, dwell, power route and individual device coverage were not specified in this update; official generic -43 is a separate kernel configuration |

The display rows include the 2026-11-15 i915 follow-up; other historical rows
retain their original scope. See [the four-lane fix](i915-four-lanes.md) and
[required NVMe suspend protection](nvme-d3cold.md). The i915 package is a
separate maintenance addition, absent from the eight-package release.

## Historical 0.5 five-cycle series

Normal logind/systemd/NetworkManager sleep preparation and wake were observed
in the same boot, with no reboot, live reload or counter reset. Lid was open,
AC connected and external peripherals absent during this attended series.

| Cycle | Inferred S3 seconds | Wi-Fi gateway / public-IP replies | File fsync/read | RTC/T1 restoration |
|---|---:|---|---|---|
| 1 | 45.408 | 3/3 and 3/3 | Pass | Pass |
| 2 | 44.539 | 3/3 and 3/3 | Pass | Pass |
| 3 | 44.563 | 3/3 and 3/3 | Pass | Pass |
| 4 | 45.486 | 3/3 and 3/3 | Pass | Pass |
| 5 | 45.399 | 3/3 and 3/3 | Pass | Pass |

Five sleep/wake SOCW pairs returned status zero. The five-cycle review matched
no dead-controller, brcmfmac bus/timeout, amdgpu firmware/resume or strict crash
error; it did count ten xHCI reinitializations. Driver status=4/completed=5
followed the series. Requested sound/microphone/Touch Bar checks were later
user-confirmed, and both USB trees passed bound gateway/public-IP pings 30/30.

Two subsequent personal lid-close returns were reported, including one on
battery; exact dwell/peripheral conditions and complete individual function
checks were not recorded. These are distinct from the five controlled cycles.
Current lid/nearby-device observations must not be assumed for earlier tests.

Failed earlier experiments are retained as negative findings in the private
maintenance record. Their one-shot tickets are consumed. No public instruction
in this project resets those tickets or authorizes another hardware experiment.

## Wi-Fi test scope

Short interface-bound traffic checks passed in the historical 0.5 cycle series.
Separate later connection/traffic observations varied, including disconnects and
packet loss; a later 2.4 GHz observation reported no further disconnection. These
are limited samples with no established cause or controlled AP/radio/client
comparison. They support neither a general stability claim nor attribution to
the driver. Further characterization is separate from this release snapshot.

## Touch ID development

Touch ID does not work with the stack provided by this bundle. The separate
[T1Bridge project](https://github.com/standardagents/t1bridge#supported-hardware)
reports fingerprint enrollment on MacBookPro14,3. Its published packages target
Arch-based systems, and that report does not establish support in this Ubuntu
configuration. It is a development reference, not a bundled feature.
