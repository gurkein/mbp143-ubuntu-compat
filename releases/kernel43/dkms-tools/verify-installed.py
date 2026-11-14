#!/usr/bin/env python3
"""Read-only verification of selected DKMS packages, source and boot activation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
KERNEL = '7.0.14-mbp14342p1'
BASE = ROOT / 'experiments/kernel-42/candidates/dkms-migration-v3'

def get(*args):
    return subprocess.check_output([str(a) for a in args], text=True).strip()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-activated', action='store_true')
    args = parser.parse_args()
    assert os.geteuid() == 0 and os.uname().release == KERNEL
    manifest = json.loads(Path('/usr/local/share/mbp143-suspend-trial/modules.json').read_text())
    base = ROOT / 'experiments/kernel-42/candidates/dkms-series-70-release' if get('dpkg-query', '-W', '-f=${Version}', 'mbp143-t1-dkms') in ('0.7-3', '0.8-1') else BASE
    packages = json.loads((base / 'packages.json').read_text())
    expected = json.loads((base / 'validation.json').read_text())['modules']
    boot_changed = manifest.get('activation_required_after_boot_id') != Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    wifi_version = get('dpkg-query', '-W', '-f=${Version}', 'mbp143-wifi-dkms')
    if wifi_version in ['0.2-1', '0.2-2', '0.2-3', '0.2-4']:
        wifi_base = ROOT / 'experiments/kernel-42/candidates/wifi-fem-dkms-0.2-v2'
        package_base = {'0.2-1': wifi_base, '0.2-2': ROOT / 'experiments/kernel-42/candidates/wifi-fem-dkms-0.2-v3', '0.2-3': ROOT / 'experiments/kernel-42/candidates/wifi-fem-dkms-0.2-v4', '0.2-4': ROOT / 'experiments/kernel-42/candidates/wifi-fem-dkms-standard'}[wifi_version]
        wifi = json.loads((package_base / 'packages.json').read_text())[0]
        packages = [wifi if r['role'] == 'wifi' else r for r in packages]
        for name in wifi['modules']:
            binary = next((wifi_base / 'validation' / KERNEL / 'source').rglob(name + '.ko'))
            expected[name] = dict(srcversion=get('modinfo', '-F', 'srcversion', binary),
                                  sig_key=expected['apple-ibridge']['sig_key'])
    if get('dpkg-query', '-W', '-f=${Version}', 'mbp143-t1-dkms') == '0.8-1':
        t1 = json.loads((ROOT / 'results/2026-11-09/t1-xremap-usb/verification.json').read_text())
        packages = [t1['package'] if r['role'] == 't1' else r for r in packages]
        for name in t1['package']['modules']:
            expected[name] = t1['images'][KERNEL][name]
    sbs_status = subprocess.run(['dpkg-query', '-W', '-f=${Status} ${Version}', 'sbs-dkms'], capture_output=True, text=True)
    if sbs_status.returncode == 0 and sbs_status.stdout == 'install ok installed 0.1-1':
        sbs_base = ROOT / 'experiments/kernel-42/candidates/sbs-dkms'
        packages.append(dict(package='sbs-dkms', version='0.1-1', dkms_name='sbs', dkms_version='0.1',
                             source=str(sbs_base / 'package/usr/src/sbs-0.1'), modules=['sbs']))
        expected['sbs'] = dict(srcversion=get('modinfo', '-F', 'srcversion', sbs_base / 'build-check/sbs.ko'),
                               sig_key=expected['apple-ibridge']['sig_key'])
    hardware_modules = set()
    hardware_boot_changed = True
    hardware_path = ROOT / 'results/2026-11-08/hardware-dkms-70/current.json'
    if not hardware_path.exists():
        hardware_path = hardware_path.with_name('verification.json')
    if hardware_path.exists():
        hardware = json.loads(hardware_path.read_text())
        hardware_boot_changed = hardware['installed_boot_id'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        for record in hardware['packages']:
            packages.append(record)
            for name in record['modules']:
                hardware_modules.add(name)
                expected[name] = hardware['images'][KERNEL][name]
    modules, statuses = {}, {}
    for record in packages:
        assert get('dpkg-query', '-W', '-f=${Version}', record['package']) == record['version']
        status = get('dkms', 'status', '-m', record['dkms_name'], '-v', record['dkms_version'], '-k', KERNEL)
        assert ': installed' in status, status
        statuses[record['package']] = status
        source = Path('/usr/src') / (record['dkms_name'] + '-' + record['dkms_version'])
        original = Path(record['source'])
        for rel, digest in json.loads((original / 'source-manifest.json').read_text()).items():
            assert sha(source / rel) == digest, rel
        for name in record['modules']:
            path = Path(get('modinfo', '-n', name))
            assert '/updates/dkms/' in str(path)
            assert get('modinfo', '-F', 'vermagic', path).split()[0] == KERNEL
            assert get('modinfo', '-F', 'srcversion', path) == expected[name]['srcversion']
            assert get('modinfo', '-F', 'sig_key', path) == expected[name]['sig_key']
            if name in hardware_modules:
                assert sha(path) == expected[name]['sha256'], name
            if name in manifest['modules']:
                assert str(path) == manifest['modules'][name]['path']
                assert sha(path) == manifest['modules'][name]['sha256']
            loaded = Path('/sys/module') / name.replace('-', '_') / 'srcversion'
            loaded_matches = loaded.exists() and loaded.read_text().strip() == expected[name]['srcversion']
            if loaded.exists():
                activation_changed = hardware_boot_changed if name in hardware_modules else boot_changed
                assert loaded_matches or (not activation_changed and not args.require_activated), name
            modules[name] = dict(path=str(path), sha256=sha(path), source_matches=True,
                                 loaded=loaded.exists(), loaded_source_matches=loaded_matches, trusted_signature_matches=True)
    assert 'apple-ibridge' in get('modinfo', '-F', 'depends', 'apple-touchbar').split(',')
    assert Path('/sys/module/apple_ibridge/holders/apple_touchbar').exists()
    params = Path('/sys/module/apple_ibridge/parameters')
    assert (params / 'skip_acpi_power').read_text().strip() == '1'
    assert not (params / 's3_notify_once').exists() and not (params / 's3_notify_repeat').exists()
    boot_changed = manifest.get('activation_required_after_boot_id') != Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    keyboards = []
    for block in Path('/proc/bus/input/devices').read_text().split('\n\n'):
        name = re.search(r'N: Name="([^"]+)"', block)
        if name and (name[1] == 'Apple SPI Keyboard' or name[1].startswith('xremap')):
            keyboards.append(dict(name=name[1], handler_attached=bool(re.search(r'H: Handlers=.*\btbkbd\b', block))))
    assert keyboards
    if boot_changed or args.require_activated:
        assert all(k['handler_attached'] for k in keyboards)
    readiness = subprocess.run(['/usr/local/libexec/mbp143-suspend-trial-check'], capture_output=True, text=True)
    readiness_text = readiness.stdout + readiness.stderr
    if args.require_activated:
        assert boot_changed and hardware_boot_changed, 'A normal reboot is still required'
        for name in hardware_modules - {'thunderbolt_net'}:
            assert modules[name]['loaded_source_matches'], name
        assert readiness.returncode == 0, readiness.stdout + readiness.stderr
    elif not boot_changed:
        assert readiness.returncode != 0 and 'normal reboot' in readiness_text
    assert not get('dpkg', '--audit')
    print(json.dumps(dict(kernel=KERNEL, packages=statuses, modules=modules,
        new_build_activation='normal boot verified' if boot_changed and hardware_boot_changed else 'normal reboot pending',
        keyboard_handlers=keyboards, S3_status=(params/'s3_status').read_text().strip(),
        S3_completed=(params/'s3_completed').read_text().strip(),
        readiness_exit_code=readiness.returncode, readiness=readiness_text,
        interactive_checks='Confirm Fn, Touch Bar, speakers, microphone and Wi-Fi; not inferred from source versions.',
        PM_transition_performed=False, hardware_writes=False), indent=2))

if __name__ == '__main__':
    main()
