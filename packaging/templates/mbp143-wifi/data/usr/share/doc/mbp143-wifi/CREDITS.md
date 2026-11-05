# Credits and collaboration

## Developed with Codex

This project was developed collaboratively by [gurkein](https://github.com/gurkein)
and [OpenAI Codex](https://openai.com/codex/). Codex assisted with source research,
patch analysis and adaptation, local driver changes, build and packaging tools,
offline tests, debugging, documentation and preparation of this repository.

The maintainer directed the work, supplied machine context, performed physical
interactions and reported user-observed hardware behavior. Recorded automated
checks and human observations retain their individual scope. In particular,
earlier 0.5 hardware results are distinguished from the documented 0.6 changes.

## Driver and configuration foundations

| Source | Contribution used here |
|---|---|
| Ronald Tschalär and subsequent iBridge/Touch Bar contributors; [AJ-dev-i60/t1-touchbar](https://github.com/AJ-dev-i60/t1-touchbar) | T1 driver and packaging baseline; pinned wrapper commit `20d65c7b0fe6d05ea9734f869b27384a62de5109` |
| [davidjo/snd_hda_macbookpro](https://github.com/davidjo/snd_hda_macbookpro) and [oliveira11670 kernel-7 fork](https://codeberg.org/oliveira11670/snd_hda_macbookpro) | MacBook CS8409 audio sources; selected fork commit `53dd5fae334a101e8a940f1242bd6859dca14273` |
| Francisco Beltran Millalen, [audio PR220](https://github.com/davidjo/snd_hda_macbookpro/pull/220) | Resume codec-recovery proposal, pinned `b8bc4d935335a9a5476c478d491adf9b18012f58`, with separate local error-handling changes |
| [Omarchy packages PR596](https://github.com/omacom/omarchy-pkgs/pull/596) | Source of the selected BCM43602 D0 patch, pinned `1aac35af814bc9b3e0fa7669cdb9e42ebf277795`; only patch 0682 is used |
| [animatek/macbook-bcm43602-linux](https://github.com/animatek/macbook-bcm43602-linux) | Model-specific NVRAM/configuration reference used by the historical setup recipe |

## Kernel backports

Thanks to the Linux, Ubuntu, ACPICA, PCI, AMDGPU and Thunderbolt contributors
and the authors/reviewers of these changes. The source links and adaptations
below are recorded in the [patch manifest](kernel/patches/manifest.json).

| Area | Original source |
|---|---|
| PCI configuration accessibility | [0001-pci-config-accessible.patch](https://github.com/torvalds/linux/commit/e18d1abc3bff0a24a5299f3c150ab9546e9439aa) |
| PCI saved-configuration preservation | [0002-pci-save-v3.patch](https://lists.openwall.net/linux-kernel/2026/10/19/3216) |
| PCI link-state validity | [0003-pci-link-v3.patch](https://lists.openwall.net/linux-kernel/2026/10/19/3211) |
| ACPICA parent-derived PCI bus | [0004-acpica-parent-bus.patch](https://github.com/open-acpica/acpica/pull/1236) |
| Apple native PME | [0005-apple-native-pme.patch](https://lore.landau.one/lkml/20260924132859.24751-1-fbeltranmillalen%40gmail.com/) |
| AMD VI VRAM initialization | [0006-amdgpu-vi-vram.patch](https://www.mail-archive.com/amd-gfx%40lists.freedesktop.org/msg153399.html) |
| Thunderbolt SXFP ordering | [0007-thunderbolt-sxfp-v3.patch](https://lkml.rescloud.iu.edu/hypermail/linux/kernel/2610.2/13908.html) |

## Community investigation references

- [Standard Agents T1Bridge](https://github.com/standardagents/t1bridge): separate experimental T1/Touch ID work and model-specific enrollment reports; consulted as a research reference.

- [Dunedan: Linux on 2016/2017 MacBook Pro](https://github.com/Dunedan/mbp-2016-linux): family compatibility history and investigation links.
- [Gavin McLelland: MacBookPro14,3 notes](https://github.com/gavinmclelland/omarchy-macbookpro14-3) and [suspend discussion](https://github.com/gavinmclelland/omarchy-macbookpro14-3/issues/12): model-specific configuration and experience reports.
- [nohzafk: T1 MacBook Pro notes](https://github.com/nohzafk/omarchy-macbookpro-t1): additional T1 investigation context, with model differences retained.
- [mythopoeic: MacBookPro14,3 Ubuntu notes](https://github.com/mythopoeic/macbookpro14-3-linux): model-specific enablement research and findings.

Imported code remains attributed to its original authors under its applicable
licenses. Local adaptations and source pins are documented in
[source provenance](docs/source-provenance.md) and
[third-party notices](THIRD_PARTY_NOTICES.md). Community reports retain their
original hardware/kernel/test limits; this project records its own evidence
separately.
