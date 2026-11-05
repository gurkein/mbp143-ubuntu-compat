# Source provenance

The extraction checkpoint and source-relative file/hash mapping are recorded in
`manifests/inputs.json`. New documentation supersedes stale status paragraphs
from candidate READMEs; original dated observations remain historical evidence.

## Kernel

- Ubuntu binary source package: `linux-source-7.0.0=7.0.0-42.42`.
- Original source-package SHA256:
  `3da06804a13cbc18974a61f78ff73dbbbfe476dc9b775e99102aee15aabe55a7`.
- Internal upstream version: `7.0.14`; release: `7.0.14-mbp14342p1`.
- Original DEB version: `7.0.0-42.42+mbp143.1`.
- Seven backports and their origins/adaptations/hashes:
  `kernel/patches/manifest.json`; order: `kernel/patches/series`.
- Additional kernel packaging modification:
  `kernel/packaging/0001-omit-libc-package.patch`.
- Configuration: `kernel/config/mbp14342p1.config`; public certificate bundles
  are retained separately and in the source archive. The original source key
  is intentionally unavailable; a full rebuild generates or uses another key.

The full source archive is the existing patched source tree, not an upstream
tarball misleadingly labeled as containing the modifications. The copied source
does not include the 32 GiB original kernel build directory.

## Drivers

- T1 `baseline/`: source copied for the original trial companion package.
- T1 `mode-result-0.1/`: historical source snapshot retained for patch provenance. It normalizes successful USB byte-count returns for the mode worker.
- T1 `automatic-0.6/`: current package build-source snapshot with dated distribution comments with tracing
  enabled. MacBookPro14,3 S3 handling is automatic; there are no once/repeat
  activation parameters. Read-only status/count remain. The aggregated
  baseline-to-package patch reconstructs the functional source; dated
  distribution comments are checked separately without changing upstream patches.
- Audio `baseline/` and `pr220-0.1/`: complete source-only copies of the baseline
  and PR220/local-error-handling candidate used for builds. A combined patch and
  separate imported/local patches are preserved.
- Wi-Fi `d0-0.1/`: complete selected brcm80211 build-source subtree, based on the
  target kernel plus only patch 0682. Vendor helpers remain kernel-supplied.

Revised package control files and original non-binary override data are preserved under
`packaging/templates/`; the earlier-release DEBs are hash-pinned inputs to the role-based package builder.
Original and revised hashes, dependency changes and payload comparisons are in
`manifests/licensing.json`; no executable payload was rebuilt. Scripts
under `reference/maintenance/` are text snapshots and retain original paths and
historical assertions. They are evidence of build/deployment steps, not portable
commands or the maintained status reference.

No byte-identical rebuild or general hardware portability is claimed. New
build-only tools operate on copied sources and explicit target headers. Their
isolated build/test results are recorded in `manifests/validation.json`.

## Graphics and EFI

`boot/efi/mbp143-gpu-switch.c` is an unchanged copy of the original local EFI
helper. The publication Makefile derives from the local recipe and changes
source/output path handling while retaining compiler/linker flags. The original
EFI/GRUB installer is a text reference because it embeds a host path and changes
boot defaults. The input manifest records original and adapted hashes. No
firmware change, EFI launch or new binary build was performed for publication.

The original seven-package publication was retired on 2026-11-06; its source
commit `b11abe0` and historical receipt remain. The current six-package release
uses the canonical `v0.1.0-experimental.1` tag. Current assembly accepts its DEBs
as hash-pinned inputs, avoiding any dependency on retired download endpoints.
