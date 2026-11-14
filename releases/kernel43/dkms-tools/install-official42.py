#!/usr/bin/env python3
"""Install reviewed DKMS sources for official -42 without touching the live kernel."""
from datetime import datetime
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[3]
TARGET = '7.0.0-42-generic'
LIVE = '7.0.14-mbp14342p1'
ROLES = [('mbp143-t1','0.7',['apple-ibridge','apple-touchbar']),
         ('mbp143-audio','0.1',['snd-hda-codec-cs8409']),
         ('mbp143-wifi','0.1',['brcmfmac','brcmfmac-wcc','brcmfmac-cyw','brcmfmac-bca'])]
OLD = [('apple-ib-drv','0.1'),('mbp143-cs8409','0.1')]
BACKUPS = Path('/var/backups/mbp143-dkms-official42')

def get(*args):
    return subprocess.check_output(list(map(str,args)),text=True).strip()

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def loaded():
    return {n:(Path('/sys/module')/n/'srcversion').read_text().strip()
            for n in ['apple_ibridge','apple_touchbar','snd_hda_codec_cs8409','brcmfmac','brcmfmac_wcc']}

def preserved():
    files=list((ROOT/'state/kernel-42').glob('*.json'))
    files+=list((Path('/lib/modules')/LIVE).rglob('*.ko*'))
    files+=[Path('/boot/initrd.img-'+LIVE),Path('/boot/vmlinuz-'+LIVE),
            Path('/boot/vmlinuz-'+TARGET),Path('/boot/grub/grub.cfg'),Path('/boot/grub/grubenv'),
            Path('/usr/local/share/mbp143-suspend-trial/modules.json'),
            Path('/usr/local/libexec/mbp143-suspend-trial-check'),
            Path('/etc/systemd/sleep.conf.d/99-mbp143-disable-suspend.conf')]
    return {str(p):sha(p) for p in files if p.is_file()}

def command(backup,*args,allow_failure=False):
    print('Running: '+' '.join(map(str,args[:3])),flush=True)
    p=subprocess.run(list(map(str,args)),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    with (backup/'commands.log').open('a') as log:
        log.write('COMMAND: '+' '.join(map(str,args))+'\n'+p.stdout+'\n')
    if p.returncode and not allow_failure:raise RuntimeError('Command failed; see '+str(backup/'commands.log'))
    return p

def restore(backup):
    assert os.geteuid()==0 and backup.parent==BACKUPS
    before=json.loads((backup/'before.json').read_text())
    current_loaded=loaded()
    for name,version,_ in reversed(ROLES):
        status=get('dkms','status','-m',name,'-v',version,'-k',TARGET)
        if status:command(backup,'dkms','remove','-m',name,'-v',version,'-k',TARGET)
    for path in before['created_files']:
        p=Path(path)
        if p.exists():p.unlink()
    with tarfile.open(backup/'official42-and-legacy-dkms.tar') as tar:
        tar.extractall('/',filter='fully_trusted')
    shutil.copy2(backup/('initrd.img-'+TARGET),Path('/boot/initrd.img-'+TARGET))
    command(backup,'depmod','-a',TARGET)
    for name,record in before['selected'].items():
        assert sha(get('modinfo','-k',TARGET,'-n',name))==record['sha256']
    assert preserved()==before['preserved'] and loaded()==current_loaded
    print('Official -42 legacy module tree/DKMS registrations/image restored; live kernel unchanged.',flush=True)

def install():
    assert os.geteuid()==0 and os.uname().release==LIVE
    assert not get('dpkg','--audit')
    assert not Path('/run/mbp143-suspend-trial-runtime.json').exists()
    assert get('dpkg-query','-W','-f=${Version}','linux-image-'+TARGET)=='7.0.0-42.42'
    assert get('dpkg-query','-W','-f=${Version}','linux-headers-'+TARGET)=='7.0.0-42.42'
    stamp=datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')
    backup=BACKUPS/stamp;backup.mkdir(parents=True,mode=0o700);backup.chmod(0o700)
    files=[Path('/etc/dkms')/(name+'--'+TARGET+'.conf') for name,_,_ in ROLES]
    files += [Path('/etc/dkms')/(name+'--'+TARGET+'.conf') for name,_ in OLD]
    depmod=Path('/etc/depmod.d/mbp143-dkms-official42.conf')
    dracut=Path('/usr/lib/dracut/modules.d/92mbp143official42/module-setup.sh')
    files += [depmod,dracut]
    assert all(not p.exists() for p in files)
    before=dict(preserved=preserved(),loaded=loaded(),created_files=list(map(str,files)),selected={})
    for name in ['apple-ibridge','apple-touchbar','snd-hda-codec-cs8409','brcmfmac']:
        path=Path(get('modinfo','-k',TARGET,'-n',name))
        before['selected'][name]=dict(path=str(path),sha256=sha(path))
    (backup/'before.json').write_text(json.dumps(before,indent=2)+'\n')
    shutil.copy2('/boot/initrd.img-'+TARGET,backup/('initrd.img-'+TARGET))
    with tarfile.open(backup/'official42-and-legacy-dkms.tar','w') as tar:
        for path in [Path('/lib/modules')/TARGET,*[Path('/var/lib/dkms')/name for name,_ in OLD]]:
            tar.add(path,arcname=str(path).lstrip('/'))
    print('Backup: '+str(backup),flush=True)
    builds={}
    # Build/ABI-check all candidates before retiring the existing official drivers.
    for name,version,names in ROLES:
        command(backup,'dkms','build','-m',name,'-v',version,'-k',TARGET,'-j','2',
                '--directive','BUILD_EXCLUSIVE_KERNEL=^7[.]0[.]0-42-generic$',
                '--directive','mok_signing_key=/var/lib/mbp143-dkms-signing/key.pem',
                '--directive','mok_certificate=/var/lib/mbp143-dkms-signing/certificate.der')
        base=Path('/var/lib/dkms')/name/version/TARGET/'x86_64'
        log=(base/'log/make.log').read_text()
        assert 'matching_import_CRCs' in log and 'exit code: 0' in log
        builds[name]={}
        for module in names:
            binaries=list((base/'module').glob(module+'.ko*'));assert len(binaries)==1
            binary=binaries[0]
            info={f:get('modinfo','-F',f,binary) for f in ['vermagic','srcversion','sig_key','depends']}
            assert info['vermagic'].split()[0]==TARGET and info['sig_key']
            builds[name][module]=dict(path=str(binary),sha256=sha(binary),**info)
    assert preserved()==before['preserved'] and loaded()==before['loaded']
    print('All seven official -42 DKMS modules passed build, ABI and signature checks.',flush=True)
    try:
        for name,_,_ in ROLES:
            Path('/etc/dkms',name+'--'+TARGET+'.conf').write_text(
                '# Qualified module build target only; official-kernel suspend is not qualified.\n'
                'BUILD_EXCLUSIVE_KERNEL="^7[.]0[.]0-42-generic$"\n')
        for name,_ in OLD:
            Path('/etc/dkms',name+'--'+TARGET+'.conf').write_text(
                '# Current mbp143 DKMS sources own this target; preserve legacy sources for rollback.\n'
                "BUILD_EXCLUSIVE_KERNEL='^$'\n")
        depmod.parent.mkdir(parents=True,exist_ok=True)
        depmod.write_text(''.join('override '+m+' ^7[.]0[.]0-42-generic$ updates/dkms\n'
                                 for _,_,names in ROLES for m in names))
        dracut.parent.mkdir(parents=True,exist_ok=False)
        dracut.write_text('''#!/bin/bash
check() {
    [[ "$kernel" == "7.0.0-42-generic" ]] || return 1
    return 0
}
installkernel() {
    hostonly='' instmods -c apple-ibridge apple-touchbar snd-hda-codec-cs8409 brcmfmac brcmfmac-wcc brcmfmac-cyw brcmfmac-bca brcmutil
}
''');dracut.chmod(0o755)
        for name,version in OLD:
            command(backup,'dkms','remove','-m',name,'-v',version,'-k',TARGET)
        selected={}
        for name,version,names in ROLES:
            command(backup,'dkms','install','-m',name,'-v',version,'-k',TARGET)
            assert ': installed' in get('dkms','status','-m',name,'-v',version,'-k',TARGET)
            for module in names:
                path=Path(get('modinfo','-k',TARGET,'-n',module));expected=builds[name][module]
                assert '/updates/dkms/' in str(path) and sha(path)==expected['sha256']
                selected[module]=dict(path=str(path),sha256=sha(path),srcversion=expected['srcversion'])
        command(backup,'depmod','-a',TARGET)
        command(backup,'update-initramfs','-u','-k',TARGET)
        unpacked=backup/'image-verification'
        command(backup,'unmkinitramfs','/boot/initrd.img-'+TARGET,unpacked)
        util=Path(get('modinfo','-k',TARGET,'-n','brcmutil'))
        selected['brcmutil']=dict(path=str(util),sha256=sha(util))
        for module,record in selected.items():
            copies=list(unpacked.rglob(Path(record['path']).name))
            assert copies and all(sha(p)==record['sha256'] for p in copies),module
        assert any('updates/dkms/apple-ibridge.ko' in line
                   for f in unpacked.rglob('modules.dep') for line in f.read_text().splitlines()
                   if line.startswith('updates/dkms/apple-touchbar.ko'))
        assert preserved()==before['preserved'] and loaded()==before['loaded']
        assert not get('dpkg','--audit')
        report=dict(backup=str(backup),target=TARGET,builds=builds,selected=selected,
            DKMS_status=get('dkms','status'),eight_image_hashes_verified=True,
            running_kernel_and_modules_unchanged=True,GRUB_and_default_unchanged=True,
            current_initramfs_and_readiness_unchanged=True,old_PM_reports_unchanged=True,
            installed_source_package_versions_unchanged=True,no_APT_action=True,
            official43_installed=False,booted=False,suspend_qualified=False,
            scope='Current DKMS installed for official -42; build/image verification only; no live reload, reboot or PM test.')
        (backup/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True)
    except Exception:
        print('Restoring official -42 baseline after verification failure.',flush=True)
        restore(backup)
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--install',action='store_true');mode.add_argument('--rollback',type=Path)
    args=p.parse_args()
    if args.install:install()
    else:restore(args.rollback.resolve())
