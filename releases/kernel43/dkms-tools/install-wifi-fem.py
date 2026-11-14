#!/usr/bin/env python3
"""Deploy the reviewed Wi-Fi FEM source package with rollback and boot gating."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'experiments/kernel-42/candidates/wifi-fem-dkms-0.2-v3'
BUILDS = ROOT / 'experiments/kernel-42/candidates/wifi-fem-dkms-0.2-v2'
OLD = ROOT / 'experiments/kernel-42/candidates/dkms-series-70-release/mbp143-wifi-dkms_0.1-3_all.deb'
BACKUPS = Path('/var/backups/mbp143-wifi-fem-dkms')
LIVE = '7.0.14-mbp14342p1'
MANIFEST = Path('/usr/local/share/mbp143-suspend-trial/modules.json')
WIFI = ['brcmfmac', 'brcmfmac-wcc', 'brcmfmac-cyw', 'brcmfmac-bca']
ALL = ['apple-ibridge', 'apple-touchbar', 'snd-hda-codec-cs8409', *WIFI, 'brcmutil']

def get(*args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def kernels():
    return sorted(p.name.removeprefix('vmlinuz-') for p in Path('/boot').glob('vmlinuz-7.0*'))

def loaded():
    return {n: (Path('/sys/module') / n.replace('-', '_') / 'srcversion').read_text().strip()
            for n in ALL if (Path('/sys/module') / n.replace('-', '_') / 'srcversion').exists()}

def preserved():
    paths = list((ROOT / 'state/kernel-42').glob('*.json')) + [Path(p) for p in [
        '/boot/grub/grub.cfg', '/boot/grub/grubenv', '/usr/local/libexec/mbp143-suspend-trial-check',
        '/etc/systemd/sleep.conf.d/99-mbp143-disable-suspend.conf']]
    for k in kernels():
        paths += [Path(get('modinfo', '-k', k, '-n', n)) for n in ALL if n not in WIFI]
    return {str(p): sha(p) for p in paths}

def temperature():
    values = [int(p.read_text()) / 1000 for p in Path('/sys/devices/platform').glob('coretemp.*/hwmon/hwmon*/temp*_input')]
    assert values, 'CPU temperature is unavailable'
    return max(values)

def command(backup, *args):
    print('Running: ' + ' '.join(map(str, args[:4])), flush=True)
    with (backup / 'commands.log').open('a') as log:
        log.write('COMMAND: ' + ' '.join(map(str, args)) + '\n'); log.flush()
        proc = subprocess.Popen(list(map(str, args)), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        paused = False
        try:
            while proc.poll() is None:
                temp = temperature()
                if temp >= 99:
                    raise RuntimeError('99 C terminal guard reached')
                if temp >= 85 and not paused:
                    os.killpg(proc.pid, signal.SIGSTOP); paused = True
                    print('Cooling pause at ' + str(temp) + ' C', flush=True)
                elif temp <= 75 and paused:
                    os.killpg(proc.pid, signal.SIGCONT); paused = False
                    print('Resumed at ' + str(temp) + ' C', flush=True)
                time.sleep(1)
            if proc.returncode:
                raise RuntimeError('Command failed; see ' + str(backup / 'commands.log'))
        except BaseException:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGCONT)
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=30)
            raise

def restore(backup):
    assert backup.parent == BACKUPS
    before = json.loads((backup / 'before.json').read_text())
    assert kernels() == before['kernels'], 'Kernel targets changed; review rollback first'
    if get('dkms', 'status', '-m', 'mbp143-wifi', '-v', '0.2'):
        command(backup, 'dkms', 'remove', '-m', 'mbp143-wifi', '-v', '0.2', '--all')
    with tarfile.open(backup / 'trees.tar') as tar:
        tar.extractall('/', filter='fully_trusted')
    if get('dpkg-query', '-W', '-f=${Status} ${Version}', 'mbp143-wifi-dkms') != 'install ok installed 0.1-3':
        command(backup, 'apt-get', '-y', '--allow-downgrades', '--no-remove', '--no-install-recommends',
                'install', backup / OLD.name)
    with tarfile.open(backup / 'trees.tar') as tar:
        tar.extractall('/', filter='fully_trusted')
    for k in kernels():
        shutil.copy2(backup / ('initrd.img-' + k), '/boot/initrd.img-' + k)
        command(backup, 'depmod', '-a', k)
    assert get('dpkg-query', '-W', '-f=${Version}', 'mbp143-wifi-dkms') == '0.1-3'
    assert preserved() == before['preserved'] and loaded() == before['loaded']
    assert sha(MANIFEST) == before['manifest_sha256']
    for path, digest in before['wifi_files'].items():
        assert sha(path) == digest, path
    print('Wi-Fi package/module/image/readiness baseline restored.', flush=True)

def import_validated_builds(backup):
    """Sign checked isolated outputs and import via DKMS's supported tar format."""
    signing = Path('/etc/dkms/framework.conf.d/mbp143-dkms-signing.conf')
    text = signing.read_text()
    assert 'mbp143-wifi:7.0.14-mbp14342p1' in text
    signing.write_text(text.replace('mbp143-wifi:7.0.14-mbp14342p1',
        'mbp143-wifi:7.0.14-mbp14342p1|mbp143-wifi:7.0.0-42-generic'))
    payload = backup / 'validated-dkms-payload'
    payload.mkdir()
    source = BASE / 'mbp143-wifi-dkms-stage/usr/src/mbp143-wifi-0.2'
    for rel, digest in json.loads((source / 'source-manifest.json').read_text()).items():
        assert sha(source / rel) == digest, rel
    shutil.copytree(source, payload / 'dkms_source_tree')
    for record in json.loads((BUILDS / 'validation.json').read_text()):
        k = record['kernel']
        work = BUILDS / 'validation' / k
        assert all(sha(next((work / 'source').rglob(name))) == digest for name, digest in record['modules'].items())
        command(backup, 'python3', source / 'verify-abi.py', Path('/lib/modules') / k / 'build', work / 'source', *WIFI)
        cache = payload / 'dkms_main_tree' / k / 'x86_64'
        (cache / 'module').mkdir(parents=True); (cache / 'log').mkdir()
        shutil.copy2(work / 'build.log', cache / 'log/make.log')
        compress = get('modinfo', '-k', k, '-n', 'brcmfmac').endswith('.zst')
        for name, digest in record['modules'].items():
            original = next((work / 'source').rglob(name))
            target = cache / 'module' / name
            shutil.copy2(original, target)
            command(backup, 'strip', '-g', target)
            expected_key = get('modinfo', '-k', k, '-F', 'sig_key', 'apple-ibridge')
            if expected_key == get('modinfo', '-k', LIVE, '-F', 'sig_key', 'apple-ibridge'):
                key = '/var/lib/mbp143-dkms-signing/key.pem'
                certificate = '/var/lib/mbp143-dkms-signing/certificate.der'
            else:
                key = '/var/lib/shim-signed/mok/MOK.priv'
                certificate = '/var/lib/shim-signed/mok/MOK.der'
            command(backup, 'kmodsign', 'sha512', key, certificate, target)
            assert get('modinfo', '-F', 'sig_key', target) == expected_key, (k, 'signing identity')
            assert get('modinfo', '-F', 'srcversion', target) == get('modinfo', '-F', 'srcversion', original)
            assert get('modinfo', '-F', 'vermagic', target).split()[0] == k
            if compress:
                command(backup, 'zstd', '-q', '--rm', target)
    archive = backup / 'validated-signed-0.2.dkms.tar.gz'
    first, *remaining = kernels()
    # DKMS 3.2.2 declares readonly loop variables in multi-target ldtarball.
    # Import one target, then populate the same verified cache layout for others.
    # This path is validated in a disposable DKMS tree before live use.
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(payload / 'dkms_source_tree', arcname='dkms_source_tree')
        tar.add(payload / 'dkms_main_tree' / first, arcname='dkms_main_tree/' + first)
    command(backup, 'dkms', 'ldtarball', archive)
    for k in remaining:
        shutil.copytree(payload / 'dkms_main_tree' / k, Path('/var/lib/dkms/mbp143-wifi/0.2') / k)
    for k in kernels():
        assert ': built' in get('dkms', 'status', '-m', 'mbp143-wifi', '-v', '0.2', '-k', k)
    targets = [item for k in kernels() for item in ['-k', k]]
    command(backup, 'dkms', 'mktarball', '-m', 'mbp143-wifi', '-v', '0.2', *targets,
            '--archive', backup / 'verified-built-cache.dkms.tar.gz')

def install():
    assert os.uname().release == LIVE and not get('dpkg', '--audit')
    assert not json.loads((ROOT / 'experiments/kernel-43/logs/status.json').read_text())['running']
    assert not Path('/run/mbp143-suspend-trial-runtime.json').exists()
    assert temperature() < 80, 'Cool the CPU before installation'
    assert shutil.disk_usage('/').free > 15 * 1024**3
    assert get('dpkg-query', '-W', '-f=${Version}', 'mbp143-wifi-dkms') == '0.1-3'
    records = json.loads((BASE / 'packages.json').read_text()); assert len(records) == 1
    record = records[0]; assert sha(record['deb']) == record['sha256']
    validation = json.loads((BUILDS / 'validation.json').read_text())
    assert {r['kernel'] for r in validation} == set(kernels())
    assert all(r['abi_check'] == 'passed' and len(r['modules']) == 4 for r in validation)
    original_manifest = json.loads(MANIFEST.read_text())
    assert original_manifest['profile'] == 'automatic'
    for name, value in original_manifest['modules'].items():
        assert sha(get('modinfo', '-n', name)) == value['sha256']
        assert loaded()[name] == value['srcversion']
    backup = BACKUPS / datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True, mode=0o700); backup.chmod(0o700)
    before = dict(kernels=kernels(), preserved=preserved(), loaded=loaded(),
                  manifest_sha256=sha(MANIFEST), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                  wifi_files={get('modinfo', '-k', k, '-n', n): sha(get('modinfo', '-k', k, '-n', n)) for k in kernels() for n in WIFI})
    (backup / 'before.json').write_text(json.dumps(before, indent=2) + '\n')
    shutil.copy2(OLD, backup / OLD.name)
    for k in kernels():
        shutil.copy2('/boot/initrd.img-' + k, backup / ('initrd.img-' + k))
    with tarfile.open(backup / 'trees.tar', 'w') as tar:
        for path in [Path('/usr/src/mbp143-wifi-0.1'), Path('/var/lib/dkms/mbp143-wifi'), MANIFEST,
                     Path('/etc/dkms/framework.conf.d/mbp143-dkms-signing.conf'),
                     *[Path('/lib/modules') / k for k in kernels()]]:
            tar.add(path, arcname=str(path).lstrip('/'))
    print('Backup: ' + str(backup), flush=True)
    try:
        import_validated_builds(backup)
        command(backup, 'apt-get', '-y', '--no-remove', '--no-install-recommends', 'install', record['deb'])
        assert not get('dkms', 'status', '-m', 'mbp143-wifi', '-v', '0.1')
        assert get('dpkg-query', '-W', '-f=${Version}', 'mbp143-wifi-dkms') == record['version']
        source = Path('/usr/src/mbp143-wifi-0.2')
        for rel, digest in json.loads((Path(record['source']) / 'source-manifest.json').read_text()).items():
            assert sha(source / rel) == digest, rel
        images = {}
        for k in kernels():
            assert ': installed' in get('dkms', 'status', '-m', 'mbp143-wifi', '-v', '0.2', '-k', k)
            command(backup, 'depmod', '-a', k)
            if k != LIVE:  # The completed package trigger already refreshed LIVE.
                command(backup, 'update-initramfs', '-u', '-k', k)
            image = backup / ('image-' + k)
            command(backup, 'unmkinitramfs', '/boot/initrd.img-' + k, image)
            images[k] = {}
            expected_src = get('modinfo', '-F', 'srcversion', BUILDS / 'validation' / k / 'source/brcmfmac/brcmfmac.ko')
            assert get('modinfo', '-k', k, '-F', 'srcversion', 'brcmfmac') == expected_src
            for n in ALL:
                path = Path(get('modinfo', '-k', k, '-n', n))
                copies = list(image.rglob(path.name))
                assert copies and all(sha(p) == sha(path) for p in copies), (k, n)
                assert get('modinfo', '-F', 'vermagic', path).split()[0] == k
                if n in WIFI:
                    assert '/updates/dkms/' in str(path)
                    assert get('modinfo', '-F', 'sig_key', path) == get('modinfo', '-k', k, '-F', 'sig_key', 'apple-ibridge')
                images[k][n] = dict(path=str(path), sha256=sha(path), srcversion=get('modinfo', '-F', 'srcversion', path))
        manifest = original_manifest
        manifest['activation_required_after_boot_id'] = before['boot_id']
        for name in WIFI:
            if name in manifest['modules']:
                manifest['modules'][name] = images[LIVE][name]
        MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n')
        assert preserved() == before['preserved'] and loaded() == before['loaded']
        assert not get('dpkg', '--audit')
        readiness = subprocess.run(['/usr/local/libexec/mbp143-suspend-trial-check'], capture_output=True, text=True)
        assert readiness.returncode != 0 and 'normal reboot' in readiness.stdout + readiness.stderr
        report = dict(backup=str(backup), package=record, final_version=record['version'], images=images, loaded_unchanged=True,
                      preserved_state_unchanged=True, DKMS_status=get('dkms', 'status'),
                      readiness=readiness.stdout + readiness.stderr, activation='normal reboot required',
                      validated_modules_imported_via_DKMS=True, signing_scope='existing per-target identities; custom and official -42 local key, other targets default MOK',
                      PM_or_reload_or_reboot_performed=False)
        (backup / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        public = ROOT / 'results/2026-11-08' / (backup.name + '-wifi-fem-install')
        public.mkdir(parents=True); (public / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print('VERIFIED: ' + str(public / 'verification.json'), flush=True)
    except Exception as exc:
        print('Installation failed: ' + repr(exc) + '; restoring Wi-Fi baseline.', flush=True)
        restore(backup)
        raise

if __name__ == '__main__':
    raise SystemExit('Retired custom workflow. Use the standard APT Wi-Fi DKMS package; see README.md.')
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--install', action='store_true'); mode.add_argument('--rollback', type=Path)
    args = parser.parse_args()
    assert os.geteuid() == 0
    if args.install: install()
    else: restore(args.rollback.resolve())
