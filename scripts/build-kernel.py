#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build an already-patched kernel in a new output directory, without installing."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True, help='Unpacked kernel-source archive')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=2)
    p.add_argument('--prepare-only', action='store_true')
    a = p.parse_args()
    if a.jobs < 1:
        p.error('jobs must be positive')
    source = a.source.resolve(strict=True)
    output = a.output.resolve()
    if output == source or source.is_relative_to(output) or output.is_relative_to(source):
        p.error('Use a new output directory outside the source tree.')
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(ROOT / 'kernel/config/mbp14342p1.config', output / '.config')
    (output / 'debian').mkdir()
    for certificate in (ROOT / 'kernel/public-certificates').glob('*.pem'):
        shutil.copyfile(certificate, output / 'debian' / certificate.name)
    env = dict(os.environ, KBUILD_BUILD_USER='mbp143-builder', KBUILD_BUILD_HOST='local',
               KDEB_SOURCENAME='linux-mbp143', KDEB_PKGVERSION='7.0.0-42.42+mbp143.1+local1',
               KDEB_CHANGELOG_DIST='resolute', DEBFULLNAME='Local MacBook Trial Builder',
               DEBEMAIL='builder@localhost',
               DEB_BUILD_PROFILES='pkg.linux-mbp143.nokerneldbg pkg.linux-mbp143.nokernellibc')
    common = ['make', '-C', str(source), 'O=' + str(output), 'AWK=mawk']
    subprocess.run(common + ['olddefconfig'], env=env, check=True)
    release = subprocess.check_output(common + ['-s', 'kernelrelease'], env=env, text=True).strip()
    if release != '7.0.14-mbp14342p1':
        raise RuntimeError('Unexpected target kernel release: ' + release)
    if not a.prepare_only:
        subprocess.run(common + [f'-j{a.jobs}', 'bindeb-pkg'], env=env, check=True)
    print('Prepared' if a.prepare_only else 'Built', release, 'without installation.')

if __name__ == '__main__':
    main()
