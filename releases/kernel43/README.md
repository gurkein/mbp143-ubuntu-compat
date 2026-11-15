# Patched -43 package layout

| Package | Version |
|---|---|
| `linux-headers-7.0.14-mbp14343p1` | `7.0.0-43.43+mbp143.1` |
| `linux-image-7.0.14-mbp14343p1` | `7.0.0-43.43+mbp143.1` |
| `mbp143-t1-dkms` | `0.8-1` |
| `mbp143-audio-dkms` | `0.1-3` |
| `mbp143-wifi-dkms` | `0.2-4` |
| `mbp143-sbs-dkms` | `0.1-1` |
| `mbp143-thunderbolt-dkms` | `0.1-1` |
| `mbp143-amdgpu-dkms` | `0.3-1` |

## Installation

Download the eight DEBs from the release into a dedicated directory, alongside
SHA256SUMS and the source archives. Verify checksums before installing.
Keep a working official Ubuntu kernel selectable for recovery.

```sh
sha256sum --ignore-missing -c SHA256SUMS
sudo apt install ./linux-image-7.0.14-mbp14343p1_7.0.0-43.43+mbp143.1_amd64.deb ./linux-headers-7.0.14-mbp14343p1_7.0.0-43.43+mbp143.1_amd64.deb ./mbp143-*-dkms_*_all.deb
```

APT runs standard DKMS hooks. Six driver packages contain source and build/install
hooks, rather than precompiled modules. The T1 package supplies both iBridge and
Touch Bar. AMDGPU, Thunderbolt and SBS replace kernel patches 6–8; only patches
1–5 are built into this kernel. Reboot normally to activate the new kernel and
modules. Check `uname -r`, `dkms status`, module selection and ordinary device
functions after login. Boot with external displays disconnected, then attach them.

The original host signs DKMS modules with its private kernel signing identity.
That key is not distributed. Configure your own local DKMS signing/trust policy
when required; these artifacts do not establish general Secure Boot support.
The kernel does not enable CONFIG_MODULE_SIG_FORCE.

## Additional system policy and display fix

For the documented suspend setup, [install and verify persistent NVMe D3cold
protection](../../docs/nvme-d3cold.md). It is required by the sleep readiness
check and is not supplied by these DEBs.

A subsequent [i915 four-lane workaround](../../docs/i915-four-lanes.md) passed
one external-display-attached reboot on custom -43. Its separate
`mbp143-i915-dkms 0.1-1` package is not included in this eight-package release;
see the linked scope and availability notes.

The packages do not install the complete host sleep/readiness, NVMe D3cold,
model-specific NVRAM, graphics/EFI or keyboard policy. Review the corresponding
project documentation before adapting those settings. Old maintenance runners,
private GRUB IDs and consumed experiment guards are not installation steps.

## Corresponding source and rebuilding

Each driver DEB is accompanied by its complete `*-dkms-source.tar.gz` archive;
the DEB itself also contains its /usr/src sources, hooks, license notices and
package control scripts. Install matching headers and use normal DKMS builds.
Keep source archives with binary redistribution.

The `kernel-source-7.0.14-mbp14343p1.tar.gz` asset includes the patched Ubuntu
source, modified Debian packaging scripts, exact .config and public Canonical
certificates. Patches are already applied. Build in a fresh output directory
using ordinary Kbuild `make O=/path/to/output olddefconfig` and
`make O=/path/to/output bindeb-pkg`, after copying .config into that directory.
Use your own signing key or Kbuild-generated identity and a new package revision.
Public certificates are under the source archive's debian directory; configuration
paths must resolve in your chosen output layout. No byte-identical signature or
binary reproducibility is claimed. The source is based on Ubuntu 7.0.0-43.43.

`dkms-tools/` preserves the maintenance packaging recipes for provenance. Their
host paths and source-root assumptions require adaptation; source archives and
standard DKMS are the installation route.

The current host's suspend/resume result is user-confirmed. Historical detailed
component checks and the 0.5 five-cycle series retain their earlier kernel scope.
