# Third-party notices

Original authorship and per-file notices are preserved. See
[Credits](CREDITS.md) for Codex collaboration, upstream work and research links. This collection does
not imply endorsement by Apple, Canonical, Broadcom, AMD or upstream authors.

| Component | Origin and pinned version | License treatment |
|---|---|---|
| Ubuntu/Linux kernel | Ubuntu `linux-source-7.0.0` binary source package `7.0.0-42.42`, internal version 7.0.14 | Linux per-file SPDX and `LICENSES/kernel/`; kernel COPYING retained in the full source archive |
| Seven kernel backports | Original commits/mailing-list submissions listed in `kernel/patches/manifest.json` | Retain upstream authorship and applicable source licenses; local backports are identified |
| Apple iBridge/Touch Bar | Ronald Tschalär and later contributors; wrapper [AJ-dev-i60/t1-touchbar](https://github.com/AJ-dev-i60/t1-touchbar), commit `20d65c7b0fe6d05ea9734f869b27384a62de5109` | Driver files retain GPL-2.0 SPDX headers; wrapper MIT text is retained separately |
| MacBook CS8409 audio | [oliveira11670/snd_hda_macbookpro](https://codeberg.org/oliveira11670/snd_hda_macbookpro), baseline `53dd5fae334a101e8a940f1242bd6859dca14273`; derived from David Jo's driver and Linux audio sources | Preserve GPL and all per-file notices; local kernel-7 mapping and error-handling changes identified |
| Audio recovery | [davidjo PR220](https://github.com/davidjo/snd_hda_macbookpro/pull/220), commit `b8bc4d935335a9a5476c478d491adf9b18012f58` | Imported patch and local adaptation are separate files |
| BCM43602 D0 proposal | [Omarchy packages PR596](https://github.com/omacom/omarchy-pkgs/pull/596), pinned `1aac35af814bc9b3e0fa7669cdb9e42ebf277795`, only patch 0682 | Broadcom driver ISC and other per-file notices retained; other recipe patches are excluded |
| Package hooks and kernel build recipes | Original generated Debian/Linux hooks plus independent local packaging scripts | Generated upstream scripts retain origin; independent local scripts are MIT; no blanket relicensing |

The complete patched kernel source asset retains public self-test fixture keys
from the original distro source. These are byte-verified upstream test data,
not the host's private module-signing key. Public Canonical certificates are
included for source reconstruction; they do not mean this custom kernel was
signed by Canonical.

Firmware blobs, personalized NVRAM, system backups and network credentials are
excluded. Firmware/NVRAM acquisition and model-specific configuration remain
separate from the source licenses above.

The local GPU-selection EFI C helper and adapted build-only Makefile under
`boot/efi/` are independent project tools covered by MIT. They use gnu-efi
headers at build time; no header/library distribution or prebuilt EFI application
is added here. The original host installer is retained as a text reference.
