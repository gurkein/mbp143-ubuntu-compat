# Graphics, EFI selection and Boot Camp

The tested configuration combines kernel/drivers with an existing firmware and
desktop arrangement. Installing the six DEBs alone does not reproduce it.
This document describes the MacBookPro14,3 maintenance setup; no new firmware
write, GPU switch, reboot or hardware test was performed for publication.

## Intel preferred, Radeon available

The internal display and GNOME session use Intel HD 630 as the preferred GPU.
Radeon Pro 560 remains powered, bound to `amdgpu` and available to Mutter for
external display output. This is not a Radeon power-off configuration.

External 4K display output was verified through Radeon DP-3 at 3840×2160/60 Hz. An earlier
`mutter-device-ignore` rule hid Radeon from Mutter and prevented external output;
that rule must not be restored for the documented dual-display arrangement.
The historical display helper's `external` mode represents Intel preferred with
Radeon available. Its default `install` mode hides Radeon and is unsuitable for
this external-display setup. Stale udev tags also required cleanup in the
original maintenance work.

Native-PME boots with an external display attached sometimes left the internal
panel unavailable. Verified workaround: boot with external display detached,
then attach after login. A later lid close/open transition worked, but the
firmware/kernel/display initialization cause remains unisolated.

## Persistent GPU preference and the EFI helpers

The helper source is [mbp143-gpu-switch.c](../boot/efi/mbp143-gpu-switch.c).
It writes Apple's nonvolatile `gpu-power-prefs` variable under GUID
`fa4ce28d-b62f-4c99-9cc3-6815686e30f9`, then requests an immediate cold reboot.
The four-byte values in this implementation are:

| EFI application | Preference payload | Additional behavior |
|---|---|---|
| `mbp143-set-igd.efi` | `01 00 00 00` (Intel) | Cold reboot after a successful write |
| `mbp143-set-dis.efi` | `00 00 00 00` (Radeon) | Cold reboot after a successful write |
| `mbp143-windows-radeon.efi` | `00 00 00 00` (Radeon) | Select Windows via BootNext, then cold reboot |

The preference persists across reboots. Removing an EFI file or GRUB menu entry
does not undo it. These applications do not prompt for confirmation or validate
the machine model. Treat launching one as a firmware change and reboot action,
not as a harmless status check. No EFI executable is added to the release here.

## Why Windows uses the Radeon wrapper

In the original machine's Boot Camp tests, direct Windows boot was unreliable
while the persistent preference selected Intel. The working route uses a GRUB
entry to chainload `mbp143-windows-radeon.efi`. It locates a firmware boot option
containing the Microsoft loader path, sets the one-time UEFI `BootNext`, selects
Radeon and cold-reboots into the Windows firmware route.

This route is different from directly chainloading `bootmgfw.efi` from GRUB.
Preserve the dedicated wrapper when reproducing this machine's dual-boot setup;
do not silently restore a direct os-prober Windows entry under Intel preference.
The helper uses a loader-path byte search rather than a general device-path
parser; other firmware/partition layouts have not been qualified.

## Source-only build

The portable [Makefile](../boot/efi/Makefile) uses a source-relative path and
explicit output/include options. It has no install or firmware-operation target.
Build prerequisites are `gnu-efi`, GCC and `binutils-mingw-w64-x86-64`.

```sh
# Display the build commands without compiling or executing EFI applications:
make -n -f boot/efi/Makefile OUTPUT=/tmp/mbp143-efi-build

# Optional build only; does not install or launch the outputs:
make -f boot/efi/Makefile OUTPUT=/tmp/mbp143-efi-build
```

The C source is preserved byte-for-byte. Only Makefile paths/output handling
were adapted for publication. The adapted recipe was checked with `make -n`;
no new EFI binary was compiled, installed or executed during this update.
These EFI applications are not signed by this recipe; no Secure Boot support
is claimed.

## Installation and recovery boundaries

The original local installer is preserved as a
[historical text reference](../reference/maintenance/scripts/boot/apply-mbp143-intel-display-menu.sh.txt).
It contains an absolute maintenance source path and changes GRUB saved-entry,
timeout, automatic-save and os-prober settings. Those policies were not copied
into a new automatic installer. In particular, its numeric saved/next-entry
assignments must not overwrite the current named kernel/trial default.

Before adapting it to another installation, back up the ESP/EFI files, GRUB
configuration/environment and the current GPU preference. Identify the actual
ESP and firmware Windows option, and keep an accessible official Ubuntu kernel
and boot recovery path. Copying files, creating menu entries, launching a helper
and selecting a kernel default are distinct operations.

For recovery on the documented machine, the Radeon selector writes the Radeon
preference and cold-reboots; the Intel selector changes it back for the tested
Intel-preferred Linux arrangement. Choose deliberately with work saved and the
external display detached for the internal-panel workaround. Do not execute a
selector just to inspect state. A file-only rollback leaves the NVRAM preference
unchanged; restoring a prior preference is a separate firmware operation.

The firmware Option-key picker still labels the shared EFI volume Windows.
The earlier cosmetic label helper did not resolve that; it is not a required
compatibility fix. This publication performs none of these firmware operations.
