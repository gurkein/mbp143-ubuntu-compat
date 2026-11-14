#!/usr/bin/env python3
"""Migrate the current driver packages to source-only DKMS with a sealed rollback."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[3]
K = '7.0.14-mbp14342p1'
BASE = ROOT / 'experiments/kernel-42/candidates/dkms-migration-v3'
RECORDS = json.loads((BASE / 'packages.json').read_text())
MANIFEST = Path('/usr/local/share/mbp143-suspend-trial/modules.json')
HELPER = Path('/usr/local/libexec/mbp143-suspend-trial-check')
INITRD = Path('/boot/initrd.img-' + K)
SIGNING = Path('/etc/dkms/framework.conf.d/mbp143-dkms-signing.conf')
BACKUPS = Path('/var/backups/mbp143-dkms-migration')
OLD = {
    'mbp143-ibridge': ('0.7-3', 'local-final-t1'),
    'mbp143-t1': ('0.7-3', 'local-final-t1'),
    'mbp143-audio': ('0.1-2', 'local-profile'),
    'mbp143-wifi': ('0.1-2', 'local-profile'),
}
CORE = ['apple-ibridge', 'apple-touchbar', 'snd-hda-codec-cs8409', 'brcmfmac']
ALL = CORE + ['brcmfmac-wcc', 'brcmfmac-cyw', 'brcmfmac-bca', 'brcmutil']

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def get(*args):
    return subprocess.check_output([str(a) for a in args], text=True).strip()

def command(backup, *args, allow_failure=False):
    process = subprocess.run([str(a) for a in args], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with (backup / 'commands.log').open('a') as log:
        log.write('COMMAND: ' + ' '.join(map(str, args)) + '\n' + process.stdout + '\n')
    if process.returncode and not allow_failure:
        raise RuntimeError('Command failed; see ' + str(backup / 'commands.log'))
    return process

def loaded():
    return {name: (Path('/sys/module') / name.replace('-', '_') / 'srcversion').read_text().strip()
            for name in ALL if (Path('/sys/module') / name.replace('-', '_') / 'srcversion').exists()}

def immutable():
    paths = list((ROOT / 'state/kernel-42').glob('*.json')) + [
        Path('/boot/grub/grub.cfg'), Path('/boot/grub/grubenv'),
        Path('/etc/grub.d/48_mbp143_s3_automatic'),
        Path('/etc/systemd/sleep.conf.d/99-mbp143-disable-suspend.conf'),
        Path('/home/gurkan/.config/gnome-macos-remap/config.yml'),
        Path('/home/gurkan/.config/systemd/user/gnome-macos-remap.service')]
    paths += list(Path('/lib/modules/7.0.0-42-generic').rglob('*.ko*'))
    return {str(p): sha(p) for p in paths if p.is_file()}

def package_plan(text):
    assert {l.split()[1] for l in text.splitlines() if l.startswith('Inst ')} == {r['package'] for r in RECORDS}
    assert {l.split()[1] for l in text.splitlines() if l.startswith('Remv ')} == set(OLD)

def preflight():
    assert os.geteuid() == 0 and os.uname().release == K
    assert not get('dpkg', '--audit')
    assert not Path('/run/mbp143-suspend-trial-runtime.json').exists()
    assert not Path('/run/mbp143-suspend-trial-failed.json').exists()
    assert not SIGNING.exists()
    assert (BASE / 'validation.json').is_file()
    for record in RECORDS:
        assert sha(record['deb']) == record['sha256']
    for name, (version, _) in OLD.items():
        assert get('dpkg-query', '-W', '-f=${Version}', name) == version
    manifest = json.loads(MANIFEST.read_text())
    assert manifest['profile'] == 'automatic'
    for name, record in manifest['modules'].items():
        assert sha(get('modinfo', '-n', name)) == record['sha256']
        assert loaded()[name] == record['srcversion']
    assert sha(HELPER) != sha(ROOT / 'scripts/power/mbp143-suspend-check.py')  # new boot-provenance guard
    plan = get('apt-get', '-s', '--no-install-recommends', 'install', *[r['deb'] for r in RECORDS])
    package_plan(plan)
    return dict(kernel=K, loaded=loaded(), old_manifest=manifest, preserved=immutable(), apt_plan=plan,
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                signature_keys={name: get('modinfo', '-F', 'sig_key', name) for name in ALL})

def sandbox(backup):
    """Exercise DKMS install/uninstall and collision restoration away from the host."""
    root = backup / 'sandbox'
    tree, sources, install = root / 'dkms', root / 'src', root / 'modules'
    for p in [tree, sources, install / K]: p.mkdir(parents=True, exist_ok=True)
    # Copy the final package sources and independently verified build outputs.
    built = ROOT / 'experiments/kernel-42/candidates/dkms-migration-v1/isolated-dkms'
    originals = {}
    for record in RECORDS:
        name, version = record['dkms_name'], record['dkms_version']
        shutil.copytree(record['source'], sources / (name + '-' + version))
        command(backup, 'dkms', 'add', '-m', name, '-v', version, '--dkmstree', tree, '--sourcetree', sources)
        shutil.copytree(built / name / version / K, tree / name / version / K)
        for module in record['modules']:
            original = Path(get('modinfo', '-n', module))
            for directory in ['kernel/test', 'updates/old-test']:
                target = install / K / directory / original.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, target)
                originals[str(target)] = sha(target)
    for name in ['modules.order', 'modules.builtin', 'modules.builtin.modinfo']:
        shutil.copy2(Path('/lib/modules') / K / name, install / K / name)
    for record in RECORDS:
        command(backup, 'dkms', 'install', '-m', record['dkms_name'], '-v', record['dkms_version'],
                '-k', K, '--dkmstree', tree, '--sourcetree', sources, '--installtree', install,
                '--force-version-override')
    assert all(Path(p).exists() and sha(p) == h for p, h in originals.items())
    for record in reversed(RECORDS):
        command(backup, 'dkms', 'remove', '-m', record['dkms_name'], '-v', record['dkms_version'],
                '-k', K, '--dkmstree', tree, '--sourcetree', sources, '--installtree', install)
    assert all(Path(p).exists() and sha(p) == h for p, h in originals.items())
    (backup / 'sandbox-validation.json').write_text(json.dumps(dict(
        passed=True, original_copies_preserved=len(originals), host_modules_modified=False))+'\n')

def restore(backup):
    assert backup.parent == BACKUPS and os.geteuid() == 0
    assert not Path('/run/mbp143-suspend-trial-runtime.json').exists()
    before_loaded = loaded()
    # Package removal invokes DKMS remove and restores all tracked originals.
    packages = []
    for record in RECORDS:
        status = subprocess.run(['dpkg-query', '-W', '-f=${Status}', record['package']], capture_output=True, text=True)
        if status.returncode == 0 and status.stdout.strip() not in ['deinstall ok config-files', 'unknown ok not-installed']:
            packages.append(record['package'])
    if packages:
        command(backup, 'apt-get', '-y', '--no-install-recommends', 'remove', *packages)
    files = sorted((backup / 'packages').glob('*.deb'))
    command(backup, 'apt-get', '-y', '--no-remove', '--no-install-recommends', 'install', *files)
    for r in RECORDS:
        command(backup, 'dkms', 'remove', '-m', r['dkms_name'], '-v', r['dkms_version'], '--all', allow_failure=True)
    with tarfile.open(backup / 'module-and-dkms-trees.tar') as tar:
        tar.extractall('/', filter='fully_trusted')
    for src, dst in [('modules.json', MANIFEST), ('suspend-check', HELPER), (INITRD.name, INITRD)]:
        shutil.copy2(backup / src, dst)
    if SIGNING.exists(): SIGNING.unlink()
    command(backup, 'depmod', '-a', K)
    before = json.loads((backup / 'before.json').read_text())
    assert all(sha(get('modinfo', '-n', name)) == record['sha256'] for name, record in before['old_manifest']['modules'].items())
    assert loaded() == before_loaded
    assert immutable() == before['preserved']
    print('Restored binary packages, module/DKMS trees, readiness and initramfs; no live reload.')

def install():
    before = preflight()
    backup = BACKUPS / datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True, mode=0o700)
    backup.chmod(0o700)
    (backup / 'before.json').write_text(json.dumps(before, indent=2)+'\n')
    (backup / 'packages').mkdir()
    for name, (version, folder) in OLD.items():
        package = ROOT / 'experiments/kernel-42/candidates/package-layout' / folder / f'{name}_{version}_amd64.deb'
        assert get('dpkg-deb', '-f', package, 'Version') == version
        shutil.copy2(package, backup / 'packages' / package.name)
    for src, dst in [(MANIFEST, 'modules.json'), (HELPER, 'suspend-check'), (INITRD, INITRD.name)]:
        shutil.copy2(src, backup / dst)
    with tarfile.open(backup / 'module-and-dkms-trees.tar', 'w') as tar:
        for path in [Path('/lib/modules') / K, Path('/var/lib/dkms/apple-ib-drv'), Path('/var/lib/dkms/mbp143-cs8409')]:
            tar.add(path, arcname=str(path).lstrip('/'), recursive=True)
    print('Backup:', backup, flush=True)
    sandbox(backup)
    assert immutable() == before['preserved'] and loaded() == before['loaded']
    print('Disposable DKMS install/uninstall and original-module restoration passed.', flush=True)
    try:
        signing_dir = Path('/var/lib/mbp143-dkms-signing')
        assert not signing_dir.is_symlink()
        signing_dir.mkdir(mode=0o700, exist_ok=True)
        assert signing_dir.stat().st_uid == 0 and signing_dir.stat().st_mode & 0o777 == 0o700
        for src, name, mode in [('signing_key.pem', 'key.pem', 0o600), ('signing_key.x509', 'certificate.der', 0o644)]:
            original_key_file = ROOT / 'experiments/kernel-42/build/certs' / src
            if (signing_dir / name).exists():
                assert (signing_dir / name).read_bytes() == original_key_file.read_bytes()
            shutil.copyfile(original_key_file, signing_dir / name)
            (signing_dir / name).chmod(mode)
        SIGNING.write_text('''# Preserve the target kernel's trusted signing identity for these local DKMS modules.
case "${module:-}:${kernelver:-}" in
  mbp143-t1:7.0.14-mbp14342p1|mbp143-audio:7.0.14-mbp14342p1|mbp143-wifi:7.0.14-mbp14342p1)
    mok_signing_key=/var/lib/mbp143-dkms-signing/key.pem
    mok_certificate=/var/lib/mbp143-dkms-signing/certificate.der
    ;;
esac
''')
        SIGNING.chmod(0o644)
        # Retire only the old DKMS registration on this exact custom kernel.
        # Its installed official-kernel fallback is never removed or rebuilt.
        command(backup, 'dkms', 'remove', '-m', 'apple-ib-drv', '-v', '0.1', '-k', K)
        command(backup, 'apt-get', '-y', '--no-install-recommends', 'install', *[r['deb'] for r in RECORDS])
        command(backup, 'depmod', '-a', K)
        manifest = before['old_manifest']
        manifest['activation_required_after_boot_id'] = before['boot_id']
        selected = {}
        for name in ALL:
            path = Path(get('modinfo', '-n', name))
            source = get('modinfo', '-F', 'srcversion', path)
            assert source == before['loaded'].get(name, get('modinfo', '-F', 'srcversion', name))
            expected_key = before['signature_keys']['apple-ibridge'] if name != 'brcmutil' else before['signature_keys'][name]
            assert get('modinfo', '-F', 'sig_key', path) == expected_key
            if name != 'brcmutil': assert '/updates/dkms/' in str(path), path
            selected[name] = dict(path=str(path), sha256=sha(path), srcversion=source,
                                  sig_key=get('modinfo', '-F', 'sig_key', path))
            if name in CORE:
                manifest['modules'][name] = {key: selected[name][key] for key in ['path', 'sha256', 'srcversion']}
        MANIFEST.write_text(json.dumps(manifest, indent=2)+'\n')
        shutil.copy2(ROOT / 'scripts/power/mbp143-suspend-check.py', HELPER)
        HELPER.chmod(0o755)
        command(backup, 'update-initramfs', '-u', '-k', K)
        unpacked = backup / 'initramfs-verification'
        command(backup, 'unmkinitramfs', INITRD, unpacked)
        for name, record in selected.items():
            copies = list(unpacked.rglob(Path(record['path']).name))
            assert copies and all(sha(p) == record['sha256'] for p in copies), name
        assert any('updates/dkms/apple-ibridge.ko' in line
                   for f in unpacked.rglob('modules.dep') for line in f.read_text().splitlines()
                   if line.startswith('updates/dkms/apple-touchbar.ko:'))
        assert not get('dpkg', '--audit')
        assert immutable() == before['preserved']
        assert loaded() == before['loaded']
        check = command(backup, HELPER, allow_failure=True)
        assert check.returncode != 0 and 'normal reboot' in check.stdout
        report = dict(backup=str(backup), kernel=K, selected=selected, loaded_unchanged=True,
                      old_state_reports_unchanged=26, fallback_modules_unchanged=True,
                      GRUB_keyboard_sleep_policy_unchanged=True, initramfs_verified=True,
                      activation='normal reboot pending; no live reload or PM transition',
                      readiness=check.stdout, packages=RECORDS, dkms_status=get('dkms', 'status'))
        (backup / 'installation.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report, indent=2), flush=True)
    except Exception:
        print('Installation failed; restoring the sealed baseline.', flush=True)
        restore(backup)
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight', action='store_true')
    mode.add_argument('--install', action='store_true')
    mode.add_argument('--rollback', type=Path)
    args = parser.parse_args()
    if args.install: install()
    elif args.rollback: restore(args.rollback.resolve())
    else:
        result = preflight()
        print(json.dumps(dict(ready=True, kernel=result['kernel'], loaded=result['loaded'], APT=result['apt_plan']), indent=2))
