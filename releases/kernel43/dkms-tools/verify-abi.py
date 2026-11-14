#!/usr/bin/env python3
"""Reject imported-symbol or shared-helper ABI drift before DKMS installs anything."""
import json
from pathlib import Path
import subprocess
import sys

arguments = sys.argv[1:]
strict_exports = '--strict-exports' in arguments
arguments = [argument for argument in arguments if argument != '--strict-exports']
headers, source = map(Path, arguments[:2])
replaced = {name.replace('-', '_') for name in arguments[2:]}
built = {p.stem.replace('-', '_') for p in source.rglob('*.ko')}
if not replaced <= built:
    raise RuntimeError('A declared replacement module was not built')
symbols = {}
providers = {}
for line in (headers / 'Module.symvers').read_text().splitlines():
    fields = line.split()
    if len(fields) >= 3:
        symbols[fields[1]] = int(fields[0], 16)
        providers[fields[1]] = Path(fields[2]).name.replace('-', '_')
local = {}
changed_exports = {}
for symvers in source.rglob('Module.symvers'):
    for line in symvers.read_text().splitlines():
        fields = line.split()
        if len(fields) >= 3:
            value = int(fields[0], 16)
            # A complete replacement stack supplies its own paired exports.
            # Helpers retained from the kernel (notably HDA) must stay identical.
            if fields[1] in symbols and symbols[fields[1]] != value:
                if providers[fields[1]] not in replaced:
                    raise RuntimeError('Shared helper ABI changed: ' + fields[1])
                changed_exports[fields[1]] = value
            local[fields[1]] = value
available = symbols | local
report = {}
for module in sorted(source.rglob('*.ko')):
    rows = subprocess.check_output(['modprobe', '--show-modversions', str(module)], text=True).splitlines()
    if not rows:
        raise RuntimeError('No symbol versions in ' + str(module))
    for row in rows:
        crc, symbol = row.split()
        if available.get(symbol) != int(crc, 16):
            raise RuntimeError('Imported ABI mismatch: ' + module.name + ': ' + symbol)
    report[str(module.relative_to(source))] = len(rows)
if not report:
    raise RuntimeError('No modules built')
retained_consumers = 0
if strict_exports and changed_exports:
    kernel = subprocess.check_output(['modinfo', '-F', 'vermagic', str(next(source.rglob('*.ko')))], text=True).split()[0]
    installed = Path('/lib/modules') / kernel
    dependencies = installed / 'modules.dep'
    if not dependencies.exists() and Path('/boot', 'vmlinuz-' + kernel).exists():
        raise RuntimeError('Cannot verify retained module consumers for ' + kernel)
    def module_name(path):
        return Path(path).name.split('.ko', 1)[0].replace('-', '_')
    for line in dependencies.read_text().splitlines() if dependencies.exists() else []:
        filename, dependency_list = line.split(':', 1)
        if module_name(filename) in replaced:
            continue
        if not any(module_name(dependency) in replaced for dependency in dependency_list.split()):
            continue
        rows = subprocess.check_output(['modprobe', '--show-modversions', str(installed / filename)], text=True).splitlines()
        retained_consumers += 1
        for row in rows:
            crc, symbol = row.split()
            if symbol in changed_exports and int(crc, 16) != changed_exports[symbol]:
                raise RuntimeError('Retained consumer requires a matching rebuild: ' + filename + ': ' + symbol)
print(json.dumps({'matching_import_CRCs': report, 'shared_exports_checked': len(local),
                  'changed_exports': len(changed_exports), 'retained_consumers_checked': retained_consumers}))
