#!/usr/bin/env python3
"""Compile the proposed hardware DKMS sources against installed kernel headers."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--packages', type=Path, required=True)
parser.add_argument('--role', action='append')
parser.add_argument('--kernel', action='append', required=True)
arguments = parser.parse_args()
base = arguments.packages.resolve()
records = json.loads((base / 'packages.json').read_text())
report = {'completed': [], 'failed': [], 'running': None}
label = '-'.join(arguments.role or ['all'])
status = base / ('build-validation-' + label + '.json')
for record in records:
    if arguments.role and record['role'] not in arguments.role:
        continue
    for kernel in arguments.kernel:
        work = base / 'validation' / record['role'] / kernel
        shutil.copytree(record['source'], work)
        report['running'] = {'role': record['role'], 'kernel': kernel}
        status.write_text(json.dumps(report, indent=2) + '\n')
        print('Building ' + record['role'] + ' for ' + kernel, flush=True)
        with (work / 'build.log').open('w') as log:
            process = subprocess.run(['sh', './build.sh', kernel, str(os.cpu_count() or 1)],
                                     cwd=work, stdout=log, stderr=subprocess.STDOUT)
        result = {'role': record['role'], 'kernel': kernel, 'log': str(work / 'build.log')}
        if process.returncode:
            result['exit_code'] = process.returncode
            report['failed'].append(result)
            print('FAILED ' + record['role'] + ' for ' + kernel, flush=True)
        else:
            result['modules'] = {}
            for module in record['modules']:
                binary = next(work.rglob(module + '.ko'))
                result['modules'][module] = {
                    'srcversion': subprocess.check_output(['modinfo', '-F', 'srcversion', str(binary)], text=True).strip(),
                    'vermagic': subprocess.check_output(['modinfo', '-F', 'vermagic', str(binary)], text=True).strip(),
                }
            report['completed'].append(result)
            print('PASSED ' + record['role'] + ' for ' + kernel, flush=True)
        report['running'] = None
        status.write_text(json.dumps(report, indent=2) + '\n')
raise SystemExit(bool(report['failed']))
