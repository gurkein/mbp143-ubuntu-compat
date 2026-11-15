# NVMe D3cold protection for suspend

The documented MacBookPro14,3 suspend setup requires the internal NVMe
controller's `d3cold_allowed` value to be `0`. The driver DEBs do not install
this policy. Driver installation alone does not require this helper, but
reproducing the documented suspend setup does. The readiness check refuses
sleep if this protection is missing; protection alone does not qualify suspend.

## Install the persistent protection

From a checked-out copy of this repository, review
[`apply-mbp143-nvme-suspend-fix.sh`](../scripts/power/apply-mbp143-nvme-suspend-fix.sh)
before running it. It checks exact MacBookPro14,3 DMI, PCI address
`0000:02:00.0`, NVMe class, Samsung controller ID `144d:a804` and the `nvme`
driver. Do not bypass these checks for a different controller or model.

```sh
sudo bash scripts/power/apply-mbp143-nvme-suspend-fix.sh install
```

This installs `/usr/local/libexec/mbp143-nvme-no-d3cold` and
`/etc/systemd/system/mbp143-nvme-no-d3cold.service`, then enables and starts
the service. It immediately writes `0` to the controller's `d3cold_allowed`
attribute and reapplies it at each boot. It does not rebuild a kernel, change
GRUB, reload drivers, reboot or request sleep. Existing helper/unit files are
backed up under `/var/backups/mbp143-nvme-suspend-fix/` before replacement.
These two files are managed by the script, not by dpkg/APT.

## Verify without sleeping

```sh
systemctl is-enabled mbp143-nvme-no-d3cold.service
systemctl status --no-pager mbp143-nvme-no-d3cold.service
cat /sys/bus/pci/devices/0000:02:00.0/d3cold_allowed
```

Expect `enabled`, a successful `active (exited)` oneshot service and `0`.
The helper applies the setting and exits; it is not a resident process.
Repeat these read-only checks after your next planned normal boot to confirm
persistence. No suspend test is part of this installation.

On 2026-11-15 the maintenance machine's service was enabled and had succeeded
in the current boot; the live NVMe attribute was `0`.

## Removal

Keep this protection while using the documented suspend setup. If deliberately
retiring that setup, disable suspend first and review the script's `rollback`
action: it disables the service, restores previously backed-up helper/unit files
(or removes them if absent originally), and sets `d3cold_allowed` back to `1`.
Do not use rollback merely to diagnose a readiness refusal.
