# Known issues

- **USB:** two downstream xHCIs reinitialize on each resume. Post-wake Ethernet
  works on both trees, but one tree needed saved-profile reconnect to regain an
  IPv4 default route. Native Thunderbolt and peripheral-present sleep are open.
- **Display:** booting with an external display attached can leave the internal
  panel unavailable. Verified workaround: boot with external display detached,
  then attach after login. Keep Radeon available to Mutter for external output.
- **Battery:** an incorrect UPower full-capacity cache produced an erroneous
  percentage; restarting it corrected the value without a corresponding energy
  gain. A voltage dip remains unexplained. Successful wake is not battery
  qualification.
- **Sleep coverage:** five approximately 45-second AC/undocked cycles do not
  establish long-duration, docked or every-peripheral acceptance. Hibernation is
  outside this work. Firmware/T1/readiness errors must remain terminal.

No new hardware experiment is needed to reproduce the publication checks.

Additional network observations are recorded under [Wi-Fi test scope](compatibility.md#wi-fi-test-scope); no driver cause has been established.
