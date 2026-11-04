# Recovery and rollback

Keep a selectable official Ubuntu kernel and an independent backup before
installation. Do not rely solely on a custom kernel entry if display or input
fails. Detach the external display for the verified internal-panel boot workaround.

For a driver/policy rollback, first choose the reviewed official fallback kernel and restore the matched
prior driver/boot configuration. With 0.6, the ordinary native-PME entry also
uses automatic driver behavior; changing to it alone does not disable S3 work. Restore the corresponding backed-up policy/modules/initramfs
as a matched set and regenerate boot metadata before a planned normal reboot.
No live driver reload is part of this recovery path.

GPU selection is also persistent firmware state. Removing the EFI helpers or
their GRUB entries does not restore `gpu-power-prefs`. See the
[graphics and EFI recovery boundaries](graphics-and-efi.md#installation-and-recovery-boundaries)
before changing the display/Boot Camp configuration.

T1 overrides form a dependency chain. Do not remove a required baseline while
leaving a dependent package installed. The maintenance environment's known
signed 0.5 rollback is separate from the selected seven-DEB release set; other
users must keep their own original package/module/policy backup. A backup path
from the author's machine is not a usable recovery resource for another host.

Inspect an APT removal/downgrade simulation for only the intended overrides,
verify fallback module selection with depmod, and inspect the regenerated
initramfs. Then reboot normally and verify ordinary functions. Do not reset a
failure latch, ticket or driver counter to force another attempt after failure.

The preserved local rollback recipes under `reference/maintenance/` describe
the original installation and are not portable recovery automation. No backup
image, private key, personalized NVRAM or machine credential is published.
