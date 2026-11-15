# Known issues

- **USB:** two downstream xHCIs reinitialize on each resume. Post-wake Ethernet
  works on both trees, but one tree needed saved-profile reconnect to regain an
  IPv4 default route. The maintainer reports successful sleep/wake with
  peripherals attached outside the controlled series; broader device combinations
  and native Thunderbolt coverage remain to be characterized.
- **Display:** the separate [i915 four-lane fix](i915-four-lanes.md) passed one
  external-attached normal reboot on custom -43 on 2026-11-15. It is not included
  in the eight-package release. Repeated/cold boots, official -43 runtime and PM
  remain unqualified. Without the fix, boot detached and attach after login;
  keep that recovery option and keep Radeon available to Mutter.
- **Battery:** an incorrect UPower full-capacity cache produced an erroneous
  percentage; restarting it corrected the value without a corresponding energy
  gain. A voltage dip remains unexplained. Successful wake is not battery
  qualification.
- **Sleep coverage:** five approximately 45-second AC/undocked cycles do not
  establish long-duration, docked or every-peripheral acceptance. Hibernation is
  outside this work. Firmware/T1/readiness errors must remain terminal.

No new hardware experiment is needed to reproduce the publication checks.

Additional network observations are recorded under [Wi-Fi test scope](compatibility.md#wi-fi-test-scope); no driver cause has been established.
