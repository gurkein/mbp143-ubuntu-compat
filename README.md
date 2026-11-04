# MacBookPro14,3 Ubuntu compatibility

An experimental compatibility bundle for the 15-inch 2017 MacBook Pro
(`MacBookPro14,3`) on Ubuntu 26.04.1, scoped to `7.0.14-mbp14342p1`.

It brings together seven kernel backports, automatic T1/Touch Bar S3 handling,
CS8409 audio recovery, BCM43602 D0 retention, and the source/build information
behind seven locally verified DEBs. Imported work retains its authorship and
licenses. This is an independent community project.

With the earlier T1 0.5 driver, five short, undocked, AC-powered S3 cycles passed consecutively in one boot
through logind/systemd/NetworkManager. Speakers, microphone and Touch Bar were
subsequently user-confirmed; USB Ethernet traffic passed on both downstream
trees. This establishes a specific tested 0.5 configuration on one machine. The current
0.6 candidate removes activation modes and is installed pending a normal reboot;
its hardware behavior has not yet been tested.

Known limits include xHCI reinitialization on wake, external-display-at-boot
initialization and battery telemetry. Long-duration and docked suspend and broad
peripheral coverage remain open. Detailed observations are documented with their
measured scope; unresolved causes are not attributed to individual drivers.

- [Compatibility and measured scope](docs/compatibility.md)
- [Known issues and test coverage](docs/known-issues.md)
- [Intel/Radeon, EFI selection and Boot Camp](docs/graphics-and-efi.md)
- [Building from source](docs/building.md)
- [Installation prerequisites and order](docs/installation.md)
- [Recovery and rollback](docs/rollback.md)
- [Source provenance and local changes](docs/source-provenance.md)
- [Publication status and remaining checks](docs/publication-status.md)
- [Credits and collaboration with Codex](CREDITS.md)
- [Licensing and third-party notices](THIRD_PARTY_NOTICES.md)

## Repository and release contents

`kernel/` contains the patch series, configuration and public certificates.
`drivers/` contains complete selected driver sources, including the exact
T1 0.6 package source with tracing enabled. `scripts/` contains portable build
and verification tools. `reference/maintenance/` preserves original local
recipes as text, with their host-specific assumptions clearly separated.
`boot/efi/` contains the original GPU-selector C source and a build-only recipe;
the graphics/EFI guide explains its persistent effects and recovery boundaries.

Release assets in `dist/` are intentionally excluded from Git: seven selected
DEBs, complete patched kernel source, a project-source archive, and checksums.
Package names/versions/dependencies are in [the manifest](manifests/packages.json).
These are the selected final artifacts from the current engineering work;
they are not labeled as generally stable packages.

## Offline checks

These checks compile mocked C tests or use ordinary temporary files. They do
not load modules, change boot policy or suspend the computer.

```sh
python3 scripts/verify-files.py
python3 scripts/verify-patches.py
python3 tests/offline/test-t1-s3-automatic-offline.py
python3 tests/offline/test-audio-pr220-offline.py
python3 tests/policy/test-suspend-check-offline.py
```

Original independent tools are MIT-licensed; new documentation is CC BY 4.0.
Driver sources and imported patches retain their per-file licenses; see
[LICENSE.md](LICENSE.md). No private module-signing key is included.
