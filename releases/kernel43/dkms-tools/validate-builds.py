#!/usr/bin/env python3
"""Validate source-only packages and isolated DKMS outputs against current modules."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

def get(*args):
    return subprocess.check_output([str(a) for a in args], text=True).strip()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate(packages, tree, output):
    kernel = '7.0.14-mbp14342p1'
    records = json.loads((packages / 'packages.json').read_text())
    modules = {}
    for record in records:
        assert sha(record['deb']) == record['sha256']
        src = Path(record['source'])
        for rel, digest in json.loads((src / 'source-manifest.json').read_text()).items():
            assert sha(src / rel) == digest
        # The first isolated build and final source export must have identical C/header inputs.
        original = Path(get('readlink', '-f', tree / record['dkms_name'] / record['dkms_version'] / 'source'))
        for path in (src / 'source').rglob('*'):
            if path.is_file():
                assert sha(path) == sha(original / path.relative_to(src)), path
        payload = get('dpkg-deb', '-c', record['deb'])
        assert '.ko' not in payload and '.pem' not in payload and '.key' not in payload
        assert get('dpkg-deb', '-f', record['deb'], 'Architecture') == 'all'
        stage = src.parents[2]
        assert (stage / 'usr/share/dkms/modules_to_force_install' / record['package']).read_text().strip() == record['dkms_name'] + '_version-override'
        assert (stage / 'DEBIAN/triggers').read_text().strip() == 'activate-noawait update-initramfs'
        for module in record['modules']:
            binary = tree / record['dkms_name'] / record['dkms_version'] / kernel / 'x86_64/module' / (module + '.ko')
            fields = {field: get('modinfo', '-F', field, binary) for field in ['srcversion', 'vermagic', 'sig_key', 'depends']}
            assert fields['vermagic'].split()[0] == kernel
            assert fields['srcversion'] == get('modinfo', '-F', 'srcversion', module)
            assert fields['sig_key'] == get('modinfo', '-F', 'sig_key', 'apple-ibridge')
            modules[module] = dict(path=str(binary), sha256=sha(binary), **fields)
    assert 'apple-ibridge' in modules['apple-touchbar']['depends'].split(',')
    actions = get('apt-get', '-s', '--no-install-recommends', 'install', *[r['deb'] for r in records])
    installed = {line.split()[1] for line in actions.splitlines() if line.startswith('Inst ')}
    removed = {line.split()[1] for line in actions.splitlines() if line.startswith('Remv ')}
    assert installed == {r['package'] for r in records}, installed
    assert removed == {'mbp143-ibridge', 'mbp143-t1', 'mbp143-audio', 'mbp143-wifi'}, removed
    report = dict(source_only_packages=records, modules=modules,
                  APT_simulation=actions, kernel=kernel, installed=False, loaded=False,
                  qualification='isolated DKMS build; no hardware acceptance inferred')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(packages=len(records), modules=len(modules), validation=str(output))))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packages', type=Path, required=True)
    parser.add_argument('--build-tree', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    validate(args.packages.resolve(), args.build_tree.resolve(), args.output.resolve())
