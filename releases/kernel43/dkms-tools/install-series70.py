#!/usr/bin/env python3
"""Upgrade source-only DKMS policy to the 7.0 series, preserving installed binaries."""
from datetime import datetime
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'experiments/kernel-42/candidates/dkms-series-70-release'
RECORDS=json.loads((BASE/'packages.json').read_text())
BACKUPS=Path('/var/backups/mbp143-dkms-series70')
LIVE='7.0.14-mbp14342p1'
KERNELS=sorted(p.name.removeprefix('vmlinuz-') for p in Path('/boot').glob('vmlinuz-7.0*'))
MODULES=['apple-ibridge','apple-touchbar','snd-hda-codec-cs8409','brcmfmac','brcmfmac-wcc','brcmfmac-cyw','brcmfmac-bca','brcmutil']

def get(*args):return subprocess.check_output(list(map(str,args)),text=True).strip()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run(backup,*args):
    print('Running: '+' '.join(map(str,args[:3])),flush=True)
    p=subprocess.run(list(map(str,args)),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    with (backup/'commands.log').open('a') as f:f.write('COMMAND: '+' '.join(map(str,args))+'\n'+p.stdout+'\n')
    if p.returncode:raise RuntimeError('Command failed; see '+str(backup/'commands.log'))
    return p.stdout
def preserved():
    paths=list((ROOT/'state/kernel-42').glob('*.json'))+[Path(p) for p in [
        '/boot/grub/grub.cfg','/boot/grub/grubenv','/usr/local/share/mbp143-suspend-trial/modules.json',
        '/usr/local/libexec/mbp143-suspend-trial-check','/etc/systemd/sleep.conf.d/99-mbp143-disable-suspend.conf']]
    for k in KERNELS:paths+=list((Path('/lib/modules')/k).rglob('*.ko*'))
    return {str(p):sha(p) for p in paths}
def loaded():
    return {m:(Path('/sys/module')/m.replace('-','_')/'srcversion').read_text().strip() for m in MODULES
            if (Path('/sys/module')/m.replace('-','_')/'srcversion').exists()}

def rollback(backup):
    assert os.geteuid()==0 and backup.parent==BACKUPS
    backed_kernels={p.name.removeprefix('initrd.img-') for p in backup.glob('initrd.img-*')}
    assert set(KERNELS)==backed_kernels, 'Kernel targets changed after this backup; review/remove newer targets before baseline rollback.'
    with tarfile.open(backup/'trees.tar') as tar:tar.extractall('/',filter='fully_trusted')
    # Current revision's prerm retains unchanged source-version caches on upgrade.
    run(backup,'apt-get','-y','--allow-downgrades','--no-remove','--no-install-recommends','install',*sorted((backup/'packages').glob('*.deb')))
    with tarfile.open(backup/'trees.tar') as tar:tar.extractall('/',filter='fully_trusted')
    for k in KERNELS:
        shutil.copy2(backup/('initrd.img-'+k),'/boot/initrd.img-'+k)
        run(backup,'depmod','-a',k)
    expected=json.loads((backup/'before.json').read_text())
    assert preserved()==expected['preserved'] and loaded()==expected['loaded']
    print('Previous package/configuration/module/DKMS/image baseline restored.',flush=True)

def install():
    assert os.geteuid()==0 and os.uname().release==LIVE and not get('dpkg','--audit')
    assert not Path('/run/mbp143-suspend-trial-runtime.json').exists()
    assert (BASE/'validation.json').is_file()
    for r in RECORDS:
        assert sha(r['deb'])==r['sha256']
        assert get('dpkg-query','-W','-f=${Version}',r['package'])==r['dkms_version']+'-2'
    backup=BACKUPS/datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True,mode=0o700);backup.chmod(0o700);(backup/'packages').mkdir()
    before=dict(preserved=preserved(),loaded=loaded())
    (backup/'before.json').write_text(json.dumps(before,indent=2)+'\n')
    for r in RECORDS:
        old=ROOT/'experiments/kernel-42/candidates/dkms-migration-v3'/f"{r['package']}_{r['dkms_version']}-2_all.deb"
        shutil.copy2(old,backup/'packages'/old.name)
    for k in KERNELS:shutil.copy2('/boot/initrd.img-'+k,backup/('initrd.img-'+k))
    paths=[Path('/etc/dkms'),Path('/var/lib/dkms'),*[Path('/lib/modules')/k for k in KERNELS],
           Path('/etc/depmod.d/mbp143-dkms-official42.conf'),Path('/usr/lib/dracut/modules.d/92mbp143official42')]
    with tarfile.open(backup/'trees.tar','w') as tar:
        for p in paths:
            if p.exists():tar.add(p,arcname=str(p).lstrip('/'))
    print('Backup: '+str(backup),flush=True)
    # Revision -2 removes all builds on any upgrade, although C/source version
    # did not change. Preserve its maintscript, then bypass ONLY that upgrade
    # branch for this handoff. Revision -3 ships the permanent idempotent fix.
    for r in RECORDS:
        script=Path('/var/lib/dpkg/info')/(r['package']+'.prerm')
        text=script.read_text();assert 'remove|upgrade|deconfigure)' in text
        shutil.copy2(script,backup/(r['package']+'.prerm'))
        script.write_text(text.replace('remove|upgrade|deconfigure)','remove|deconfigure)'))
    try:
        for identity in ['mbp143-t1','mbp143-audio','mbp143-wifi','apple-ib-drv','mbp143-cs8409']:
            p=Path('/etc/dkms')/(identity+'--7.0.0-42-generic.conf')
            if p.exists():p.unlink()
        Path('/etc/depmod.d/mbp143-dkms-official42.conf').unlink()
        shutil.rmtree('/usr/lib/dracut/modules.d/92mbp143official42')
        run(backup,'apt-get','-y','--no-remove','--no-install-recommends','install',*[r['deb'] for r in RECORDS])
        # Exercise the same automatic entry point used by header installation.
        for k in KERNELS:run(backup,'/etc/kernel/header_postinst.d/dkms',k)
        for r in RECORDS:
            assert get('dpkg-query','-W','-f=${Version}',r['package'])==r['version']
            conf=Path('/usr/src')/(r['dkms_name']+'-'+r['dkms_version'])/'dkms.conf'
            assert 'BUILD_EXCLUSIVE_KERNEL="^7[.]0([.-]|$)"' in conf.read_text()
            for k in KERNELS:assert ': installed' in get('dkms','status','-m',r['dkms_name'],'-v',r['dkms_version'],'-k',k)
        for old in ['apple-ib-drv','mbp143-cs8409']:
            assert not get('dkms','status','-m',old)
            conf=Path('/etc/dkms')/(old+'.conf')
            assert 'AUTOINSTALL="no"' in conf.read_text() and "BUILD_EXCLUSIVE_KERNEL='^$'" in conf.read_text()
        images={}
        for k in KERNELS:
            run(backup,'depmod','-a',k)
            if k!=LIVE:run(backup,'update-initramfs','-u','-k',k)
            unpacked=backup/('image-'+k)
            run(backup,'unmkinitramfs','/boot/initrd.img-'+k,unpacked)
            images[k]={}
            for m in MODULES:
                path=Path(get('modinfo','-k',k,'-n',m));copies=list(unpacked.rglob(path.name))
                assert copies and all(sha(p)==sha(path) for p in copies),(k,m)
                images[k][m]=dict(path=str(path),sha256=sha(path))
        assert preserved()==before['preserved'] and loaded()==before['loaded']
        assert not get('dpkg','--audit')
        run(backup,'/usr/local/libexec/mbp143-suspend-trial-check')
        report=dict(backup=str(backup),packages=RECORDS,DKMS_status=get('dkms','status'),
            series='7.0',automatic_header_hooks_passed=KERNELS,images=images,
            legacy_registrations_absent_and_globally_excluded=True,
            existing_custom_and_official42_module_hashes_unchanged=True,loaded_unchanged=True,
            GRUB_readiness_policy_and_26_PM_reports_unchanged=True,
            boot_or_PM_test_performed=False,official43_installed=False)
        (backup/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True)
    except Exception:
        print('Upgrade failed; restoring previous configuration.',flush=True)
        rollback(backup)
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--install',action='store_true');m.add_argument('--rollback',type=Path)
    a=p.parse_args()
    if a.install:install()
    else:rollback(a.rollback.resolve())
