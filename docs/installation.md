# Installation prerequisites and package order

Target only the documented MacBookPro14,3/Ubuntu/kernel combination. These are
experimental exact-kernel overrides, not a general Ubuntu driver installer.
The initial publication provides existing artifacts and manual review steps;
there is no automatic system/suspend activation script.

1. Keep a working official Ubuntu kernel and selectable GRUB fallback. Back up
   boot configuration, matching modules and initramfs, firmware/NVRAM settings
   and current power-policy files before making changes.
2. Verify release SHA256SUMS and review `manifests/packages.json`, source notices
   and known issues. Original modules are locally signed; they are not Canonical
   signed. Secure Boot support is not established.
3. Confirm the model, architecture, Ubuntu release, initramfs backend and available
   boot space. The verified packaging repair used dracut; do not assume an
   initramfs-tools host has equivalent helper inclusion.
4. Review a single APT simulation for the five runtime DEB paths. The sixth
   package, `linux-headers`, is optional for compiling modules. Only the five
   superseded compatibility packages should be removed during migration.
5. Runtime packages are `linux-image-7.0.14-mbp14342p1`, `mbp143-ibridge`,
   `mbp143-t1`, `mbp143-audio` and `mbp143-wifi`. Every driver depends on the
   exact kernel-image package; Touch Bar also depends on the matching iBridge
   package. Submit all five runtime paths and optional headers to APT in one
   reviewed transaction. No baseline, mode-result or phase-trace package is
   needed by this layout.
6. Before reboot, inspect module selection and the generated initramfs, including
   WCC/CYW/BCA/brcmutil and the intended T1 pair. Preserve original modules and
   kernel-scoped depmod overrides. Do not live-unload or rebind T1/audio/Wi-Fi.
7. Boot normally with the external monitor detached, verify loaded source
   versions and ordinary functions, then attach the monitor after login.

The maintenance setup also required model-specific NVRAM, protected NVMe D3cold,
`skip_acpi_power=1`, Intel-primary display configuration and exact-driver systemd
readiness/runtime restoration. DEBs alone do not install that complete policy.
Original local recipes are text references; review per-machine applicability,
country regulatory settings and private adapter address before adapting them.

The [graphics and EFI guide](graphics-and-efi.md) explains persistent GPU
selection, Intel-preferred/Radeon-visible operation and the Windows Radeon
wrapper. EFI file installation, launching a GPU selector and choosing a GRUB
kernel default are separate actions; the historical installer changes defaults
and must not be applied wholesale to the current named trial entry.

Sleep availability belongs to system policy. T1 0.6 performs its normal S3
handling automatically on the supported model and has no once/repeat activation
parameter. Remove old S3 activation options from the selected boot entry and
module configuration when migrating. Transaction state/error checks and system
readiness checks remain; no one-cycle user policy is implemented by the driver.
Do not run old maintenance experiment helpers or reset consumed tickets.

The release DEBs use numeric packaging revisions containing documentation-only changes. Install matching
revisions together; do not substitute original versions where an exact revised
dependency is declared. Kernel/module executable payloads remain unchanged.


## Migrating from the first prerelease

The new packages conflict with and replace the old trial-driver, mode-result,
phase-trace, audio-resume and Wi-Fi-D0 package names. APT removes those obsolete
packages in the same transaction. The four selected signed modules retain their
existing executable bytes; their package-owned paths now match their roles.

Existing custom readiness manifests must use the new module paths and the
verified hashes/source versions. Keep failure latches and consumed experiment
records intact. Use a normal reboot for activation when selected and loaded
modules differ; never live-unload these drivers. Rebuilding an initramfs is part
of package installation and does not establish suspend acceptance.

The driver packages pre-depend on the configured exact kernel image. iBridge
also owns `/etc/dkms/apple-ib-drv--7.0.14-mbp14342p1.conf`, which excludes the
older generic T1 DKMS source from this supplied kernel. This prevents DKMS from
archiving the package-owned modules when optional headers are configured later;
other kernels retain their normal DKMS behavior. The setting is removed when
the iBridge package is purged.
