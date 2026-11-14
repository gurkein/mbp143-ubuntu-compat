#!/usr/bin/env python3
"""Keep archived, non-DKMS original modules available at their original paths."""
from pathlib import Path
import shutil
import sys

module, kernel, arch, dkms_tree, install_tree = sys.argv[1:]
root = Path(install_tree) / kernel
archive = Path(dkms_tree) / module / 'original_module' / kernel / arch
for record in archive.rglob('*.origin'):
    target = Path(record.read_text().strip())
    if not target.is_relative_to(root) or '..' in target.parts:
        raise RuntimeError('Unsafe original-module path')
    # The active DKMS destination belongs exclusively to the new version.
    if target.is_relative_to(root / 'updates/dkms'):
        continue
    source = record.with_suffix('')
    if source.is_file():
        if target.exists():
            if source.read_bytes() != target.read_bytes():
                raise RuntimeError('Original-module collision: ' + str(target))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
