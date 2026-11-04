# Experimental compatibility snapshot

Proposed tag: `v0.1.0-experimental.1` (not yet created).

For MacBookPro14,3 on Ubuntu 26.04.1 with exact kernel
`7.0.14-mbp14342p1`. Includes seven kernel backports, automatic T1 0.6,
PR220-derived audio recovery and BCM43602 D0 packaging 0.1-4.

The earlier 0.5 revision passed five consecutive approximately 45-second normal-route S3 cycles in one
boot on AC without external devices. Sound, microphone and Touch Bar were
subsequently user-confirmed; Ethernet traffic passed on both USB trees after
wake. Wider sleep conditions remain unqualified.

Later Wi-Fi disconnects/packet loss, repeated xHCI reinitialization, the
external-display-at-boot workaround and unresolved battery telemetry are
documented limitations. No further disconnect was reported after choosing
2.4 GHz; access point/environment/client/driver attribution remains unisolated.

Assets: seven selected DEBs, complete patched kernel source, project-source
archive, artifact manifest and SHA256SUMS. Original signatures are local build
signatures; no general Secure Boot support or signed release manifest is claimed.
The existing binaries retain some original local build-path metadata.

Read installation/rollback notes before use. These packages are an experimental
snapshot, and DEBs alone do not install the complete tested boot/power policy.

Current 0.6 removes driver activation modes; source/ABI tests pass, normal-boot
activation and hardware acceptance are pending. System policy controls suspend.
