# Changelog

## Unreleased — experimental snapshot, 2026-11-04

- Removed once/repeat activation modes in T1 0.6 for both local and public use;
  retained transaction checks, with system policy controlling sleep availability.
- Redacted private setup details from prose/references and excluded old local
  Git history from the publication tree; source archives/manifests refreshed.

- Added Intel/Radeon EFI and Boot Camp documentation, original GPU-selector C
  source and a portable build-only Makefile; no firmware operation or EFI build.

- Collected seven kernel backports, exact configuration and selected drivers.
- Included automatic T1 0.6 package source, PR220 audio recovery/local error handling
  and BCM43602 D0 retention with the 0.1-4 dracut packaging repair.
- Added portable build-only tools, offline tests, manifests and scoped evidence.
- Documented five same-boot short normal-route S3 passes and later Wi-Fi,
  display, USB and battery limitations without claiming general qualification.
- Preserved seven original DEBs as release assets; excluded failed Wi-Fi
  packaging revisions, private keys and one-shot PM experiment runners.

## 2026-11-05 — Distribution licensing corrections

- Add dated source distribution notices; retain original per-file licenses.
- Clarify GPL coverage of source-generating recipes and combined C tests.
- Add full license texts, actual source copyright notices and source-release
  instructions to all seven DEBs as `+license1` revisions; update exact package
  dependencies. Executable payloads and signatures are unchanged.
- Publish source/asset mappings and offline checks for these corrections.
