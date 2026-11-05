# Source distribution for the binary packages

Every release containing these DEBs must provide both source archives alongside
them, with equivalent download access from the same release:

- `kernel-source-7.0.14-mbp14342p1.tar.gz`: complete patched kernel source,
  kernel license texts, public certificates and modified packaging recipe.
- `mbp143-ubuntu-compat-source.tar.gz`: selected T1/audio/Wi-Fi source snapshots,
  baseline sources, patches, exact kernel configuration, toolchain inventory,
  build tools, package control/install scripts, license texts and notices.

The pinned source commit and hashes are in `artifacts.json` and `SHA256SUMS`.
`manifests/packages.json` maps package names, versions and dependencies;
`manifests/licensing.json` maps original DEBs to corrected DEBs and records
payload equality. The build instructions are in `docs/building.md`.

The corrected DEBs use standard numeric Debian packaging revisions listed in
`manifests/packages.json`; functional driver versions remain unchanged. Documentation, module locations, kernel-specific DKMS policy
and package metadata changed; executable files and signed modules are preserved.
These publication packages were not installed or newly hardware-tested. The
kernel release and driver functional versions retain their existing scope.

Do not distribute only patches, upstream URLs or binary DEBs. Publish the two
complete source assets with the DEBs. This distribution uses the accompanying-
source route in GPLv2 section 3, rather than a three-year written source offer.
No original private signing key is required to compile a modified version;
builders can generate/use their own key as described in `docs/building.md`.

For a package built from source, choose a new version, preserve the notices and
provide corresponding sources/build/install scripts for that new binary.
Reproducible byte-identical signatures or hardware portability are not claimed.

License references: [GPLv2](https://spdx.org/licenses/GPL-2.0-only.html),
[Linux licensing rules](https://docs.kernel.org/process/license-rules.html),
[MIT](https://opensource.org/license/mit),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode.en).

The six-package layout carries one final driver module per role. Current
package metadata is in `package-layout.json`, relative to `manifests/` in the
source archive. Earlier release assets remain frozen and separately attributed.
