#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build copied driver sources against explicit headers; never install or reload."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
KVER = '7.0.14-mbp14342p1'
FLAGS = '-DAPPLE_PINSENSE_FIXUP -DAPPLE_CODECS -DCONFIG_SND_HDA_RECONFIG=1 -Wno-unused-variable -Wno-unused-function -Wno-error -Wno-incompatible-pointer-types -Wno-discarded-qualifiers -Wno-implicit-function-declaration'
COMPONENTS = {
    't1': ('drivers/t1/automatic-0.6', '.', ['apple-ibridge.ko', 'apple-touchbar.ko']),
    't1-baseline': ('drivers/t1/baseline', '.', ['apple-ibridge.ko', 'apple-touchbar.ko']),
    't1-mode-result': ('drivers/t1/mode-result-0.1', '.', ['apple-touchbar.ko']),
    'audio': ('drivers/audio/pr220-0.1', '.', ['codecs/cirrus/snd-hda-codec-cs8409.ko']),
    'audio-baseline': ('drivers/audio/baseline', '.', ['codecs/cirrus/snd-hda-codec-cs8409.ko']),
    'wifi': ('drivers/wifi/d0-0.1', 'drivers/net/wireless/broadcom/brcm80211/brcmfmac', ['brcmfmac.ko']),
}

def run(*args):
    return subprocess.check_output([str(x) for x in args], text=True).strip()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('component', choices=COMPONENTS)
    p.add_argument('--headers', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=2)
    p.add_argument('--signing-key', type=Path)
    p.add_argument('--certificate', type=Path)
    a = p.parse_args()
    if a.jobs < 1 or bool(a.signing_key) != bool(a.certificate):
        p.error('Use positive jobs and provide both signing key and certificate, or neither.')
    headers = a.headers.resolve(strict=True)
    if (headers / 'include/config/kernel.release').read_text().strip() != KVER:
        p.error('Headers do not match the exact target release.')
    out = a.output.resolve()
    # Never build in the published source tree or overwrite an earlier result.
    if out == ROOT or ROOT.is_relative_to(out):
        p.error('Output must not contain the publication repository.')
    out.mkdir(parents=True, exist_ok=False)
    relative, module_subdir, expected = COMPONENTS[a.component]
    shutil.copytree(ROOT / relative, out / 'source')
    module_dir = out / 'source' / module_subdir
    cmd = ['make', '-C', str(headers), 'M=' + str(module_dir), f'-j{a.jobs}']
    if a.component.startswith('audio'):
        cmd.append('CFLAGS_MODULE=' + FLAGS)
    cmd.append('modules')
    env = dict(os.environ, KBUILD_BUILD_USER='mbp143-builder', KBUILD_BUILD_HOST='local')
    with (out / 'build.log').open('w') as log:
        subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    exports = {}
    for path in [headers / 'Module.symvers', module_dir / 'Module.symvers']:
        for line in path.read_text().splitlines():
            row = line.split()
            if len(row) >= 3:
                crc = int(row[0], 16)
                if path.parent == headers:
                    exports[row[1]] = crc
                elif row[1] in exports and exports[row[1]] != crc:
                    raise RuntimeError('Changed kernel export ABI: ' + row[1])
                else:
                    exports[row[1]] = crc
    modules = []
    (out / 'modules').mkdir()
    for name in expected:
        original = module_dir / name
        target = out / 'modules' / original.name
        shutil.copyfile(original, target)
        subprocess.run(['strip', '--strip-debug', str(target)], check=True)
        if a.signing_key:
            subprocess.run([str(headers / 'scripts/sign-file'), 'sha512',
                            str(a.signing_key.resolve()), str(a.certificate.resolve()), str(target)], check=True)
        magic = run('modinfo', '-F', 'vermagic', target)
        if magic.split()[0] != KVER:
            raise RuntimeError('Wrong vermagic: ' + magic)
        imports = run('modprobe', '--show-modversions', target).splitlines()
        if not imports:
            raise RuntimeError('No import CRCs found')
        for row in imports:
            crc, symbol = row.split()
            if exports.get(symbol) != int(crc, 16):
                raise RuntimeError('Import ABI mismatch: ' + symbol)
        modules.append(dict(file=target.name, sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                            vermagic=magic, srcversion=run('modinfo', '-F', 'srcversion', target),
                            signer=run('modinfo', '-F', 'signer', target), matching_import_crcs=len(imports)))
    report = dict(component=a.component, kernel=KVER, signed=bool(a.signing_key), modules=modules,
                  built_only=True, installed=False, hardware_tested=False)
    (out / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
