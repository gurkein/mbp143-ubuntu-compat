#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Repack seven allowlisted DEBs with license documentation; never install them."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()

def payload(folder):
    result = {}
    for p in sorted(folder.rglob('*')):
        rel = p.relative_to(folder).as_posix()
        if rel == 'DEBIAN' or rel.startswith(('DEBIAN/', 'usr/share/doc/')):
            continue
        if p.is_symlink():
            result[rel] = ['link', p.readlink().as_posix()]
        elif p.is_file():
            result[rel] = ['file', p.stat().st_mode & 0o7777, digest(p)]
        elif p.is_dir():
            result[rel] = ['directory', p.stat().st_mode & 0o7777]
        else:
            raise RuntimeError('Unsupported package member: ' + rel)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-directory', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True,
                        help='A new directory, distinct from the original assets')
    args = parser.parse_args()
    originals = json.loads((ROOT / 'manifests/original-packages.json').read_text())
    versions = json.loads((ROOT / 'manifests/package-revisions.json').read_text())
    # Check every input before creating output or unpacking anything.
    for row in originals:
        if digest(args.input_directory / row['file']) != row['sha256']:
            raise RuntimeError('Original package hash mismatch: ' + row['file'])
    args.output_directory.mkdir(parents=True, exist_ok=False)
    reports = []
    for row in originals:
        package = row['Package']
        with tempfile.TemporaryDirectory(prefix='license-repack-') as temporary:
            work = Path(temporary)
            original = args.input_directory / row['file']
            before, after = work / 'before', work / 'after'
            subprocess.run(['dpkg-deb', '--raw-extract', str(original), str(before)], check=True)
            shutil.copytree(before, after, symlinks=True)
            control = after / 'DEBIAN/control'
            text = control.read_text().replace('Version: ' + row['Version'] + '\n',
                                               'Version: ' + versions[package] + '\n')
            for dependency in originals:
                old = dependency['Package'] + ' (= ' + dependency['Version'] + ')'
                new = dependency['Package'] + ' (= ' + versions[dependency['Package']] + ')'
                text = text.replace(old, new)
            control.write_text(text)
            doc = after / 'usr/share/doc' / package
            if doc.is_symlink():
                raise RuntimeError('Refuse symlinked documentation directory')
            doc.mkdir(parents=True, exist_ok=True)
            copyright_file = doc / 'copyright'
            if copyright_file.exists():
                copyright_file.rename(doc / 'copyright.upstream')
            copyright_file.write_text('''Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: mbp143-ubuntu-compat selected compatibility bundle
Source: https://github.com/gurkein/mbp143-ubuntu-compat
Comment: Documentation-only packaging revision, prepared 2026-11-05.
 Complete corresponding source must accompany the DEBs in the same release.
 See SOURCE-DISTRIBUTION.md and SOURCE-NOTICES.txt for source and copyright mapping.

Files: *
Copyright: Original per-file holders listed in SOURCE-NOTICES.txt and the sources
License: multiple-per-file
 Linux as a whole is GPL-2.0-only with the syscall exception for relevant UAPI
 headers. T1/audio retain their GPL and individual file terms; Broadcom files
 retain ISC and individual file terms. No blanket relicensing is applied.
 Full license texts are supplied in LICENSES/. See THIRD_PARTY_NOTICES.md.

Files: independent project tools and independently authored packaging hooks
Copyright: 2026 mbp143-ubuntu-compat contributors
License: MIT
 See LICENSES/MIT-project.txt.

Files: newly authored project documentation
Copyright: 2026 mbp143-ubuntu-compat contributors
License: CC-BY-4.0
 See LICENSES/kernel/dual/CC-BY-4.0 and LICENSE.md.
''')
            for name in ['LICENSE.md', 'THIRD_PARTY_NOTICES.md', 'CREDITS.md', 'SOURCE-NOTICES.txt']:
                shutil.copyfile(ROOT / name, doc / name)
            shutil.copyfile(ROOT / 'docs/source-distribution.md', doc / 'SOURCE-DISTRIBUTION.md')
            shutil.copytree(ROOT / 'LICENSES', doc / 'LICENSES')
            if (after / 'DEBIAN/md5sums').exists():
                sums = []
                for p in sorted(after.rglob('*')):
                    if p.is_file() and not p.is_symlink() and 'DEBIAN' not in p.relative_to(after).parts:
                        sums.append(hashlib.md5(p.read_bytes()).hexdigest() + '  ' + p.relative_to(after).as_posix())
                (after / 'DEBIAN/md5sums').write_text('\n'.join(sums) + '\n')
            # Installed-Size includes added license documentation.
            import re
            size = sum(p.stat().st_size for p in after.rglob('*') if p.is_file() and not p.is_symlink()
                       and 'DEBIAN' not in p.relative_to(after).parts)
            text = control.read_text()
            text = re.sub(r'^Installed-Size:.*$', 'Installed-Size: ' + str((size + 1023)//1024), text, flags=re.M)
            control.write_text(text)
            for hook in (before / 'DEBIAN').iterdir():
                if hook.is_file() and hook.name not in {'control', 'md5sums'}:
                    assert hook.read_bytes() == (after / 'DEBIAN' / hook.name).read_bytes(), hook.name
            old_payload = payload(before)
            assert old_payload == payload(after), package
            filename = f"{package}_{versions[package]}_{row['Architecture']}.deb"
            target = args.output_directory / filename
            subprocess.run(['dpkg-deb', '--root-owner-group', '-Zzstd', '-z10', '--build', str(after), str(target)], check=True)
            verify = work / 'verify'
            subprocess.run(['dpkg-deb', '--raw-extract', str(target), str(verify)], check=True)
            assert old_payload == payload(verify), package
            fields = dict(line.split(': ', 1) for line in (verify / 'DEBIAN/control').read_text().splitlines()
                          if ': ' in line and not line[0].isspace())
            for required in ['copyright', 'SOURCE-NOTICES.txt', 'SOURCE-DISTRIBUTION.md',
                             'LICENSES/GPL-2.0.txt', 'LICENSES/ISC.txt']:
                assert (verify / 'usr/share/doc' / package / required).is_file(), required
            reports.append(dict(file=filename, sha256=digest(target), bytes=target.stat().st_size,
                **{key: fields.get(key, '') for key in ['Package', 'Version', 'Architecture', 'Depends']},
                original_file=row['file'], original_sha256=row['sha256'],
                non_documentation_payload_unchanged=True, hooks_unchanged=True,
                verified_payload_entries=len(old_payload)))
            print('Verified unchanged executable/data payload:', package, flush=True)
    (args.output_directory / 'repack-report.json').write_text(json.dumps(reports, indent=2) + '\n')

if __name__ == '__main__':
    main()
