#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify the six-role dependency graph and optional package module selection."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
KERNEL = '7.0.14-mbp14342p1'

def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True).strip()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-assets', action='store_true')
    args = parser.parse_args()
    layout = json.loads((ROOT / 'manifests/package-layout.json').read_text())
    rows = json.loads((ROOT / 'manifests/packages.json').read_text())
    expected = {'linux-image-' + KERNEL, 'linux-headers-' + KERNEL,
                'mbp143-ibridge', 'mbp143-t1', 'mbp143-audio', 'mbp143-wifi'}
    assert len(rows) == 6 and {r['Package'] for r in rows} == expected
    by_name = {r['Package']: r for r in rows}
    legacy = set(layout['legacy_packages'])
    conflicts = set()
    for row in rows:
        assert not any(name in row['Depends'] for name in legacy)
        conflicts.update(filter(None, row.get('Conflicts', '').split(', ')))
        if row['Package'].startswith('mbp143-'):
            assert 'linux-image-' + KERNEL + ' (= ' + by_name['linux-image-' + KERNEL]['Version'] + ')' in row['Depends']
            assert row['Pre-Depends'] == 'linux-image-' + KERNEL + ' (= ' + by_name['linux-image-' + KERNEL]['Version'] + ')'
    assert conflicts == legacy
    assert 'mbp143-ibridge (= ' + by_name['mbp143-ibridge']['Version'] + ')' in by_name['mbp143-t1']['Depends']
    guard = ROOT / ('packaging/templates/mbp143-ibridge/data/etc/dkms/apple-ib-drv--' + KERNEL + '.conf')
    assert "BUILD_EXCLUSIVE_KERNEL='^$'" in guard.read_text()
    assert '/etc/dkms/' + guard.name in (ROOT / 'packaging/templates/mbp143-ibridge/DEBIAN/conffiles').read_text()
    role_modules = {'mbp143-ibridge': 'apple-ibridge', 'mbp143-t1': 'apple-touchbar',
                    'mbp143-audio': 'snd-hda-codec-cs8409', 'mbp143-wifi': 'brcmfmac'}
    payload = json.loads((ROOT / 'manifests/package-layout-validation.json').read_text())
    assert payload['bridge_before_touchbar']
    if args.with_assets:
        with tempfile.TemporaryDirectory(prefix='mbp143-selection-') as temporary:
            folder = Path(temporary)
            for row in rows:
                path = ROOT / 'dist' / row['file']
                if row['Package'].startswith('linux-headers-'):
                    continue
                subprocess.run(['dpkg-deb', '--extract', str(path), str(folder)], check=True)
            # A registered DKMS source may provide duplicate basenames. Verify
            # that exact-kernel role overrides win independently of copy order.
            duplicates = folder / 'lib/modules' / KERNEL / 'updates/dkms'
            duplicates.mkdir(parents=True, exist_ok=True)
            for name, module in role_modules.items():
                source = folder / f'lib/modules/{KERNEL}/updates/{name}/{module}.ko'
                shutil.copy2(source, duplicates / source.name)
            subprocess.run(['depmod', '-b', str(folder), '-C', str(folder / 'usr/lib/depmod.d'), '-a', KERNEL], check=True)
            for name, module in role_modules.items():
                selected = Path(run('modinfo', '-b', folder, '-k', KERNEL, '-n', module))
                expected_path = f'lib/modules/{KERNEL}/updates/{name}/{module}.ko'
                assert selected.relative_to(folder).as_posix() == expected_path
                row = next(r for r in json.loads((ROOT / 'manifests/licensing.json').read_text())['packages'] if r['Package'] == name)
                assert hashlib.sha256(selected.read_bytes()).hexdigest() == row['modules'][0]['sha256']
            dependencies = run('modprobe', '-d', folder, '-S', KERNEL, '--show-depends', 'apple-touchbar')
            assert dependencies.index('updates/mbp143-ibridge/') < dependencies.index('updates/mbp143-t1/')
    print('Six-package graph verified: five runtime roles, optional headers, exact bridge and kernel dependencies.'
          + (' Temporary depmod selection and module hashes passed.' if args.with_assets else ''))

if __name__ == '__main__':
    main()
