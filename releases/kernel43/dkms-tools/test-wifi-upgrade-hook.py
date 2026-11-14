#!/usr/bin/env python3
"""Check staged Wi-Fi upgrade ordering without changing host DKMS state."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

hook = Path(sys.argv[1]).read_text()
for fail in (False, True):
    with tempfile.TemporaryDirectory(prefix='wifi-hook-') as temp:
        root = Path(temp)
        for kernel in ('7.0.0-42-generic', '7.0.0-43-generic', '7.1.0-generic'):
            (root / f'lib/modules/{kernel}/build/include').mkdir(parents=True)
            (root / 'boot').mkdir(exist_ok=True)
            (root / f'boot/vmlinuz-{kernel}').touch()
        old = root / 'var/lib/dkms/mbp143-wifi/0.1'
        old.mkdir(parents=True)
        source = root / 'usr/src/mbp143-wifi-0.1'
        source.mkdir(parents=True)
        (source / 'dkms.conf').write_text('PACKAGE_VERSION=0.1\n')
        old_link = old / 'source'
        old_link.symlink_to(source)
        shutil.copytree(source, old / 'source-retained')  # Clean up revision-2 leftovers too.
        def translated(text):
            for prefix in ('/lib/modules/', '/boot/', '/var/lib/dkms/', '/usr/src/', '/var/lib/mbp143-dkms-upgrade/'):
                text = text.replace(prefix, str(root) + prefix)
            return text
        if len(sys.argv) > 2:
            preinst = root / 'preinst'
            preinst.write_text(translated(Path(sys.argv[2]).read_text()))
            subprocess.run(['sh', str(preinst), 'upgrade'], check=True)
            shutil.rmtree(source)  # dpkg removes predecessor-owned /usr/src files.
            assert not (old / 'source-retained').exists()
            assert (old_link / 'dkms.conf').read_text() == 'PACKAGE_VERSION=0.1\n'
        script = root / 'postinst'
        script.write_text(translated(hook))
        mock = root / 'dkms'
        mock.write_text('''#!/bin/sh
printf '%s\\n' "$*" >> "$HOOK_LOG"
if [ "$1" = remove ]; then test -r "$OLD_SOURCE/dkms.conf" || exit 8; fi
if [ "${FAIL_BUILD:-}" = yes ] && [ "$1" = build ]; then exit 7; fi
''')
        mock.chmod(0o755)
        env = os.environ | {'PATH': str(root) + ':' + os.environ['PATH'], 'HOOK_LOG': str(root / 'calls'),
                            'OLD_SOURCE': str(old_link), 'FAIL_BUILD': 'yes' if fail else 'no'}
        result = subprocess.run(['sh', str(script), 'configure'], env=env)
        calls = (root / 'calls').read_text().splitlines()
        assert not any('7.1.0' in call for call in calls)
        if fail:
            assert result.returncode == 7
            assert not any(call.startswith(('remove ', 'install ')) for call in calls)
            assert (old_link / 'dkms.conf').is_file()
        else:
            assert result.returncode == 0
            remove = next(i for i, call in enumerate(calls) if call.startswith('remove '))
            assert len([call for call in calls[:remove] if call.startswith('build ')]) == 2
            assert len([call for call in calls[remove + 1:] if call.startswith('install ')]) == 2
            assert not (root / 'var/lib/mbp143-dkms-upgrade/mbp143-wifi-0.1').exists()
print('Source retention, legacy-cache cleanup, upgrade ordering and failed-build retention passed.')
