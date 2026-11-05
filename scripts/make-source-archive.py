#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Export a committed source snapshot, excluding untracked local credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while data := stream.read(1024 * 1024):
            h.update(data)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ref', default='HEAD')
    p.add_argument('--output', type=Path, default=ROOT / 'dist/mbp143-ubuntu-compat-source.tar.gz')
    p.add_argument('--update-assets', action='store_true')
    a = p.parse_args()
    commit = git('rev-parse', '--verify', '--end-of-options', a.ref + '^{commit}')
    paths = subprocess.check_output(['git', 'ls-tree', '-rz', '--name-only', commit], cwd=ROOT).decode().split('\0')
    for name in filter(None, paths):
        path = Path(name)
        if any(part.startswith('.env') or part == '.direnv' for part in path.parts) or path.name == 'signing_key.pem' or path.suffix in {'.key', '.p12', '.pfx'}:
            raise RuntimeError('Local credential path is tracked; refuse to export: ' + name)
    output = a.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='source-export-', dir=output.parent) as tmp:
        temporary = Path(tmp) / 'source.tar.gz'
        subprocess.run(['git', 'archive', '--format=tar.gz', '--prefix=mbp143-ubuntu-compat/',
                        '--output=' + str(temporary), commit], cwd=ROOT, check=True)
        os.replace(temporary, output)
    if a.update_assets:
        manifest = output.parent / 'artifacts.json'
        record = json.loads(manifest.read_text())
        matches = [row for row in record['assets'] if row['file'] == output.name]
        if len(matches) != 1:
            raise RuntimeError('Expected exactly one matching source asset')
        matches[0].update(bytes=output.stat().st_size, sha256=digest(output))
        record['source_git_commit'] = commit
        manifest.write_text(json.dumps(record, indent=2) + '\n')
        sums = [row['sha256'] + '  ' + row['file'] for row in record['assets']]
        sums.append(digest(manifest) + '  ' + manifest.name)
        (output.parent / 'SHA256SUMS').write_text('\n'.join(sums) + '\n')
    print('Exported committed source:', commit[:7])
    print('Local untracked/ignored files are excluded.')

if __name__ == '__main__':
    main()
