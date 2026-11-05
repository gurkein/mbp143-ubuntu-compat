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
4. Review a single APT simulation for the six runtime DEB paths. The seventh
   package, `linux-headers`, is optional for compiling modules. It should not
   remove unrelated packages, replace Docker CE or install unrelated kernels.
5. The runtime dependency chain is kernel image, trial drivers, T1 mode-result
   0.1-2, then T1 phase-trace 0.6-2 and audio
   0.1-2; Wi-Fi 0.1-5 depends on the
   exact kernel image. Submit the six runtime paths (and optional headers when
   needed) to APT in one reviewed transaction so it can resolve the relationships.
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

The layered T1 packages preserve the development dependency chain: the baseline
supplies initial modules, mode-result supplies the USB result correction, and
automatic T1 supplies the selected final pair with that correction included.
The depmod rules select the final pair; multiple copies do not mean multiple
Touch Bar drivers run simultaneously.
