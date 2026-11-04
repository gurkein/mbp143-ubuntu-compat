# Scoped hardware evidence — 2026-11-04

This authored public summary selects facts from the private dated maintenance
records. Raw journals, network identifiers, mutable state and consumed experiment
tickets are excluded. It is not a replacement for the original evidence.

1. Five consecutive normal-logind/systemd/NetworkManager S3 cycles completed
   in one boot, approximately 45 seconds each. Per-cycle bound Wi-Fi traffic,
   fsync/read, counter progression and RTC/T1 restoration passed.
2. Every sleep/wake SOCW pair returned zero; fresh mode work/cache commit
   completed. Two xHCIs reinitialized each cycle; the targeted review found no
   dead-controller, brcmfmac bus/timeout, amdgpu resume or strict crash match.
3. Later user confirmation covered sound, microphone and general Touch Bar
   operation. Both USB Ethernet trees later passed 30/30 gateway/public-IP
   replies; one tree needed reconnect to regain its IPv4 default.
4. Two later personal lid cycles returned, one reportedly on battery, with less
   complete physical/dwell/function evidence than the attended series.
5. Network measurements describe short samples. Later variability has no
   established cause; no driver-level conclusion is drawn. Detailed scope is
   recorded in the compatibility document.


Private source records, identified by maintenance-relative paths:

- `results/2026-11-04/164749-T1-repeat-five-cycles-review/review.json`
- `results/2026-11-04/172355-repeat-five-both-USB-review/review.json`
- `results/2026-11-04/213133-T1-repeat-final-user-confirmation/review.json`
- `results/2026-11-04/220613-wifi-recurrent-disconnect/review.json`
- `results/2026-11-04/2201-battery-telemetry-review/SUMMARY.md`

The hashes and exact extraction checkpoint for this public summary are distinct
from raw private record hashes. Tests here add no new hardware acceptance claim.
