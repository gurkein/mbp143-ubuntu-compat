# Build and verify without installing

## Source release export

Export source from a committed Git snapshot rather than the working directory:

```sh
python3 scripts/make-source-archive.py --update-assets
```

The exporter uses `git archive`, excludes untracked/ignored local files and
refuses tracked local environment/credential paths. Keep `.envrc`, `.env*` and
`.direnv/` private. Commit intended source changes before generating a release.

## Build prerequisites

Use Python 3, a C compiler, make, binutils, kmod and the exact target headers.
The original kernel toolchain inventory is in `kernel/toolchain.txt`. Build in
fresh writable output directories; never run `make install`, driver reload or a
suspend command as part of these checks. All examples are run from the repo root.

## Driver modules

Extract the matching headers DEB to a temporary directory:

```sh
dpkg-deb -x dist/linux-headers-7.0.14-mbp14342p1_7.0.0-42.42+mbp143.1_amd64.deb /tmp/mbp143-headers
python3 scripts/build-drivers.py t1 --headers /tmp/mbp143-headers/usr/src/linux-headers-7.0.14-mbp14342p1 --output build/t1
```

Components: `t1`, `t1-baseline`, `t1-mode-result`, `audio`, `audio-baseline` and
`wifi`. Every output directory must be new. Sources are copied there before
compiling; published sources remain unchanged. The build verifies exact vermagic
and imported CRCs, including peer exports and common audio helper compatibility.
The report records hashes, source versions and signing state. It does not prove
that a module can load or that hardware will work.

Without signing arguments the output is unsigned. To sign your own rebuilt
modules provide both `--signing-key /private/path/key.pem` and
`--certificate /path/public-cert.x509`. The original host private key is not
included. New signatures differ from the released originals and require your
own trust/configuration decisions; no general Secure Boot support is claimed.

## Kernel

The source asset `kernel-source-7.0.14-mbp14342p1.tar.gz` contains the complete
patched kernel source, seven backports, the libc-package omission and public
Canonical certificate bundles. Do not apply those patches a second time.
The config is versioned in Git. An optional preparation-only check is:

```sh
tar -xzf dist/kernel-source-7.0.14-mbp14342p1.tar.gz -C /tmp
python3 scripts/build-kernel.py --source /tmp/linux-source-7.0.0 --output build/kernel --prepare-only
```

A full build omits `--prepare-only`; it is intentionally not run as part of this
publication task. The script builds DEBs without installing and uses a changed
`+local1` package version. It does not promise byte-identical outputs. Plan disk,
temperature and CPU limits before a long build: the original laptop needed CPU
quota and thermal stops. The historical build recipe is preserved under
`reference/maintenance/`; it is not a portable command to execute wholesale.

## Packaging

`packaging/templates/` preserves control scripts and selected non-binary data
from the exact seven DEBs. Hooks execute only when packages are installed or
removed. They are never executed by offline checks. The selected modules,
package relationships, sources and hashes are recorded in manifests. Rebuilt
payloads need new package versions; do not overwrite an original release asset.

Firmware and personalized NVRAM are not bundled. Wi-Fi 0.1-4 includes a dracut
hook that retains dynamically requested WCC/CYW/BCA helpers even when unloaded;
the helpers themselves come from the matching kernel image, not that override.
