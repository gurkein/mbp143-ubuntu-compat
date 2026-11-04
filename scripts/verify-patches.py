#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Replay published patches in temporary copies and compare complete file hashes."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def apply(folder, patch):
    result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)],
                            cwd=folder, check=True, text=True, capture_output=True)
    if 'fuzz' in (result.stdout + result.stderr).lower():
        raise RuntimeError('Unexpected fuzzy application')

def main():
    expected = json.loads((ROOT / 'manifests/kernel-patch-targets.json').read_text())
    with tempfile.TemporaryDirectory(prefix='mbp143-patches-') as tmp:
        folder = Path(tmp)
        shutil.copytree(ROOT / 'kernel/pristine', folder / 'kernel')
        for name in (ROOT / 'kernel/patches/series').read_text().splitlines():
            apply(folder / 'kernel', ROOT / 'kernel/patches' / name)
        for name, digest in expected.items():
            if hashlib.sha256((folder / 'kernel' / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError('Kernel patch output mismatch: ' + name)
        specs = [
            ('t1', 'drivers/t1/baseline', 'drivers/t1/patches/baseline-to-automatic-package.patch', 'drivers/t1/automatic-0.6'),
            ('audio', 'drivers/audio/baseline', 'drivers/audio/combined-kernel7.patch', 'drivers/audio/pr220-0.1'),
            ('wifi', 'drivers/wifi/baseline', 'drivers/wifi/0682-brcmfmac-bcm43602-keep-d0-on-suspend.patch', 'drivers/wifi/d0-0.1'),
        ]
        for component, base, patch, target in specs:
            dest = folder / component
            shutil.copytree(ROOT / base, dest)
            apply(dest, ROOT / patch)
            for path in dest.rglob('*'):
                if path.is_file() and path.read_bytes() != (ROOT / target / path.relative_to(dest)).read_bytes():
                    raise RuntimeError('Driver patch output mismatch: ' + str(path))
    print('Seven kernel patches and T1/audio/Wi-Fi patch reproduction passed with zero fuzz.')

if __name__ == '__main__':
    main()
