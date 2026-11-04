#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify allowlisted imported inputs and optional release assets; no hardware I/O."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while data := stream.read(1024 * 1024):
            h.update(data)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--with-assets', action='store_true')
    a = p.parse_args()
    rows = json.loads((ROOT / 'manifests/inputs.json').read_text())['files']
    checked = 0
    for row in rows:
        if row['disposition'] == 'release asset' and not a.with_assets:
            continue
        path = ROOT / row['destination']
        if not path.is_file() or digest(path) != row['sha256']:
            raise RuntimeError('Missing or changed input: ' + row['destination'])
        checked += 1
    series = (ROOT / 'kernel/patches/series').read_text().splitlines()
    if len(series) != 7:
        raise RuntimeError('Expected seven kernel patches')
    for row in json.loads((ROOT / 'kernel/patches/manifest.json').read_text()):
        if digest(ROOT / 'kernel/patches' / row['file']) != row['sha256']:
            raise RuntimeError('Patch provenance hash mismatch')
    print(f'Verified {checked} imported inputs and seven patch provenance hashes.')

if __name__ == '__main__':
    main()
