#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify licensing scope, dated notices and optional release documentation."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

from license_notices import NOTICE, without_notice

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-assets', action='store_true')
    args = parser.parse_args()
    report = json.loads((ROOT / 'manifests/licensing.json').read_text())
    for row in report['source_annotations']:
        data = (ROOT / row['file']).read_bytes()
        assert NOTICE.encode() in data[:600], row['file']
        assert hashlib.sha256(data).hexdigest() == row['sha256'], row['file']
        assert hashlib.sha256(without_notice(data)).hexdigest() == row['original_sha256'], row['file']
    for name in report['combined_GPL_2_0_only']:
        assert 'SPDX-License-Identifier: GPL-2.0-only' in '\n'.join((ROOT / name).read_text().splitlines()[:3]), name
    packages = json.loads((ROOT / 'manifests/packages.json').read_text())
    versions = {row['Package']: row['Version'] for row in packages}
    assert len(packages) == 7
    revisions = json.loads((ROOT / 'manifests/package-revisions.json').read_text())
    for row in packages:
        assert row['Version'] == revisions[row['Package']]
        for name, version in versions.items():
            if name + ' (=' in row['Depends']:
                assert name + ' (= ' + version + ')' in row['Depends']
    assert 'Copyright (c) 2014 Broadcom Corporation' in (ROOT / 'SOURCE-NOTICES.txt').read_text()
    if args.with_assets:
        for row in packages:
            path = ROOT / 'dist' / row['file']
            assert digest(path) == row['sha256'], path.name
            # No package hooks are executed by dpkg-deb's tar listing/extraction.
            result = subprocess.run(['dpkg-deb', '--fsys-tarfile', str(path)],
                                    stdout=subprocess.PIPE, check=True)
            with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
                prefix = './usr/share/doc/' + row['Package'] + '/'
                for name in ['copyright', 'SOURCE-DISTRIBUTION.md', 'SOURCE-NOTICES.txt',
                             'LICENSES/GPL-2.0.txt', 'LICENSES/ISC.txt', 'LICENSES/MIT-project.txt',
                             'LICENSES/kernel/dual/CC-BY-4.0']:
                    assert archive.getmember(prefix + name).isfile(), name
                assert archive.extractfile(prefix + 'SOURCE-NOTICES.txt').read() == (ROOT / 'SOURCE-NOTICES.txt').read_bytes()
        archive = ROOT / 'dist/kernel-source-7.0.14-mbp14342p1.tar.gz'
        assert digest(archive) == report['kernel_source_archive']['sha256']
    print(f"Verified {len(report['source_annotations'])} dated source notices, GPL scope and seven package revisions"
          + (' with release assets.' if args.with_assets else '.'))

if __name__ == '__main__':
    main()
