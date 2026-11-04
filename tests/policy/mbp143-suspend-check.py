#!/usr/bin/python3
"""Check the exact automatic T1 S3 driver and preserve T1 runtime policy."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

MANIFEST = Path('/usr/local/share/mbp143-suspend-trial/modules.json')
MARKER = Path('/run/mbp143-suspend-trial-runtime.json')
FAILED = Path('/run/mbp143-suspend-trial-failed.json')
SYS_ROOT = Path('/sys/devices')

def read(path):
    return Path(path).read_text().strip()

def collect_snapshot():
    expected = json.loads(MANIFEST.read_text())
    matches = []
    for name, record in expected['modules'].items():
        selected = subprocess.check_output(['modinfo', '-n', name], text=True).strip()
        loaded = Path('/sys/module') / name.replace('-', '_') / 'srcversion'
        matches.append(selected == record['path'] and
                       hashlib.sha256(Path(selected).read_bytes()).hexdigest() == record['sha256'] and
                       read(loaded) == record['srcversion'])
    journal = subprocess.run(['journalctl', '-b', '-k', '--no-pager', '-o', 'json'],
                             capture_output=True, text=True, timeout=20)
    nvme = [p for p in Path('/sys/bus/pci/drivers/nvme').glob('*:*') if p.is_symlink()]
    messages = [r.get('MESSAGE','') for line in journal.stdout.splitlines()
                if isinstance((r := json.loads(line)).get('MESSAGE'),str)]
    hard_error = any(re.search(r'(?:BUG:|Oops:|Kernel panic|general protection fault|watchdog:.*lockup|HC died|host controller not responding|HC halt failed)',msg)
                     or re.search(r'brcmfmac.*(?:flow.?ring.*timeout|bus is down|bus down|MMIO read failed|Dongle setup failed)',msg,re.I)
                     or re.search(r'amdgpu.*(?:failed.*resume|resume.*failed)',msg,re.I)
                     for msg in messages)
    parameters = Path('/sys/module/apple_ibridge/parameters')
    status_path = parameters / 's3_status'
    return {
        'profile': expected.get('profile'),
        'legacy_parameters_absent': not any((parameters / name).exists() for name in ['s3_notify_once','s3_notify_repeat']),
        's3_status': int(read(status_path)) if status_path.exists() else None,
        'runtime_state_clear': not MARKER.exists() and not FAILED.exists(),
        'kernel_hard_errors': hard_error,
        'kernel': os.uname().release,
        'model': read('/sys/class/dmi/id/product_name'),
        'module_matches': len(matches) == 4 and all(matches),
        'WCC_loaded': Path('/sys/module/brcmfmac_wcc').exists(),
        'T1_skip_guard': read('/sys/module/apple_ibridge/parameters/skip_acpi_power'),
        'pm_test_none': '[none]' in read('/sys/power/pm_test'),
        'deep_available': 'deep' in read('/sys/power/mem_sleep').split() or
                          '[deep]' in read('/sys/power/mem_sleep').split(),
        'native_PME': 'pcie_ports=compat' not in read('/proc/cmdline').split(),
        'NVMe_guard': bool(nvme) and all(read(p/'d3cold_allowed') == '0' for p in nvme),
        'journal_complete': journal.returncode == 0 and not journal.stderr.strip(),
    }

def refusal_reasons(s):
    reasons = []
    if s['kernel'] != '7.0.14-mbp14342p1' or s['model'] != 'MacBookPro14,3':
        reasons.append('kernel/model differs from the selected trial')
    for key in ['module_matches', 'WCC_loaded', 'pm_test_none', 'deep_available',
                'native_PME', 'NVMe_guard', 'journal_complete', 'runtime_state_clear']:
        if not s[key]:
            reasons.append(key + ' check failed')
    if s['T1_skip_guard'] != '1':
        reasons.append('T1 skip guard differs')
    if s['kernel_hard_errors']:
        reasons.append('kernel reports a destructive error; review before further suspend')
    if s['profile'] != 'automatic':
        reasons.append('readiness manifest does not describe the automatic driver')
    if not s['legacy_parameters_absent']:
        reasons.append('legacy driver activation parameters remain loaded')
    if s['s3_status'] not in [0, 4]:
        reasons.append('S3 transaction is pending or failed; review driver status')
    return reasons

def find_t1_control():
    devices = [p for p in Path('/sys/bus/usb/devices').iterdir()
               if (p/'idVendor').exists() and read(p/'idVendor') == '05ac'
               and read(p/'idProduct') == '8600']
    if len(devices) != 1:
        raise RuntimeError('Expected one internal T1 device')
    return (devices[0]/'power/control').resolve()

def prepare_control(control, profile='automatic'):
    old = read(control)
    if old not in ['on', 'auto']:
        raise RuntimeError('Unexpected T1 runtime policy')
    # An interrupted preparation remains visible and prevents accidental reuse.
    fd = os.open(MARKER, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump({'control': str(control), 'old': old, 'profile': profile}, f)
        f.flush()
        os.fsync(f.fileno())
    control.write_text('on\n')
    if read(control) != 'on':
        raise RuntimeError('Could not pin T1 active')

def cleanup_control():
    if not MARKER.exists():
        return
    saved = json.loads(MARKER.read_text())
    control = Path(saved['control'])
    if not control.is_relative_to(SYS_ROOT) or control.name != 'control' or saved['old'] not in ['on', 'auto']:
        raise RuntimeError('Invalid runtime restoration record')
    if os.environ.get('SERVICE_RESULT','success') != 'success':
        # A normal systemd sleep failure must not silently permit another cycle.
        # This is a boot-local failure latch, separate from historical PM guards.
        if not FAILED.exists():
            fd = os.open(FAILED, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'w') as f:
                json.dump({'service_result': os.environ['SERVICE_RESULT']}, f)
                f.flush()
                os.fsync(f.fileno())
    control.write_text(saved['old'] + '\n')
    if read(control) != saved['old']:
        raise RuntimeError('T1 runtime restoration failed')
    MARKER.unlink()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--cleanup', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise RuntimeError('Root visibility is required')
    if args.cleanup:
        cleanup_control()
        return 0
    snapshot = collect_snapshot()
    reasons = refusal_reasons(snapshot)
    if reasons:
        print('Suspend readiness blocked: ' + '; '.join(reasons), file=sys.stderr)
        return 1
    if args.prepare:
        prepare_control(find_t1_control(), snapshot['profile'])
    print('Exact automatic S3 readiness checks passed; profile=' + snapshot['profile'])
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print('Suspend readiness blocked: ' + type(error).__name__, file=sys.stderr)
        raise SystemExit(1)
