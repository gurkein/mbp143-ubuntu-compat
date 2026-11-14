#!/usr/bin/env python3
"""Install official -43 and verify existing/new DKMS builds without boot or PM."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
TARGET = '7.0.0-43-generic'
CURRENT = '7.0.14-mbp14342p1'
VERSION = '7.0.0-43.43'
ROLES = [('mbp143-t1', '0.7', ['apple-ibridge', 'apple-touchbar']),
         ('mbp143-audio', '0.1', ['snd-hda-codec-cs8409']),
         ('mbp143-wifi', '0.1', ['brcmfmac', 'brcmfmac-wcc', 'brcmfmac-cyw', 'brcmfmac-bca'])]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def get(*args):
    return subprocess.check_output([str(a) for a in args], text=True).strip()

def preserve():
    files = list((ROOT/'state/kernel-42').glob('*.json'))
    files += [Path('/boot/grub/grubenv'), Path('/usr/local/share/mbp143-suspend-trial/modules.json'),
              Path('/usr/local/libexec/mbp143-suspend-trial-check'),
              Path('/etc/systemd/sleep.conf.d/99-mbp143-disable-suspend.conf')]
    for kernel in [CURRENT, '7.0.0-42-generic']:
        files += list((Path('/lib/modules')/kernel).rglob('*.ko*'))
        files += [Path('/boot/vmlinuz-'+kernel), Path('/boot/initrd.img-'+kernel)]
    return {str(p): sha(p) for p in files if p.is_file()}

def main():
    assert os.geteuid()==0 and os.uname().release==CURRENT
    assert not get('dpkg','--audit')
    assert not Path('/run/mbp143-suspend-trial-runtime.json').exists()
    stamp=datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')
    backup=Path('/var/backups/mbp143-official43')/stamp
    backup.mkdir(parents=True,mode=0o700); backup.chmod(0o700)
    def run(*args):
        print('Running: '+' '.join(map(str,args[:3])),flush=True)
        p=subprocess.run([str(a) for a in args],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        with (backup/'commands.log').open('a') as log:
            log.write('COMMAND: '+' '.join(map(str,args))+'\n'+p.stdout+'\n')
        if p.returncode: raise RuntimeError('Command failed; see '+str(backup/'commands.log'))
        return p.stdout
    before=preserve()
    loaded={n:(Path('/sys/module')/n/'srcversion').read_text().strip()
            for n in ['apple_ibridge','apple_touchbar','snd_hda_codec_cs8409','brcmfmac']}
    for p in [Path('/boot/grub/grub.cfg'),Path('/boot/grub/grubenv'),
              Path('/boot/initrd.img-'+CURRENT),Path('/boot/initrd.img-7.0.0-42-generic')]:
        shutil.copy2(p,backup/p.name)
    (backup/'before.json').write_text(json.dumps(dict(preserved=before,loaded=loaded),indent=2)+'\n')
    print('Backup: '+str(backup),flush=True)
    packages=['linux-image-'+TARGET+'='+VERSION,'linux-headers-'+TARGET+'='+VERSION]
    plan=run('apt-get','-s','--no-remove','--no-install-recommends','install',*packages)
    assert not any(l.startswith('Remv ') for l in plan.splitlines())
    allowed={'linux-image-'+TARGET,'linux-headers-'+TARGET,'linux-headers-7.0.0-43',
             'linux-modules-'+TARGET,'linux-main-modules-zfs-'+TARGET,
             'linux-main-modules-v4l2loopback-'+TARGET,'bpftool','linux-libc-dev','linux-perf','linux-tools-common'}
    assert {l.split()[1] for l in plan.splitlines() if l.startswith('Inst ')} <= allowed
    run('apt-get','-y','--no-remove','--no-install-recommends','install',*packages)
    for p in ['linux-image-'+TARGET,'linux-headers-'+TARGET]:
        assert get('dpkg-query','-W','-f=${Version}',p)==VERSION
    automatic=get('dkms','status','-k',TARGET)
    assert all(name+'/'+version in automatic for name,version,_ in ROLES)
    assert automatic.count(': installed')==3,automatic
    assert 'apple-ib-drv' not in automatic and 'mbp143-cs8409' not in automatic
    builds={}
    for name,version,modules in ROLES:
        # Kernel/header package hooks must have built/installed all three
        # without CLI allowlist/signing overrides or manual DKMS installation.
        folder=Path('/var/lib/dkms')/name/version/TARGET/'x86_64'
        log=(folder/'log/make.log').read_text()
        assert 'matching_import_CRCs' in log and 'exit code: 0' in log
        builds[name]={'status':get('dkms','status','-m',name,'-v',version,'-k',TARGET),'modules':{}}
        assert ': installed' in builds[name]['status']
        for module in modules:
            matches=list((folder/'module').glob(module+'.ko*'));assert len(matches)==1
            binary=matches[0]
            fields={field:get('modinfo','-F',field,binary) for field in ['vermagic','srcversion','sig_key','depends']}
            assert fields['vermagic'].split()[0]==TARGET and fields['sig_key']
            builds[name]['modules'][module]=dict(path=str(binary),sha256=sha(binary),**fields)
    assert 'apple-ibridge' in builds['mbp143-t1']['modules']['apple-touchbar']['depends'].split(',')
    unpacked=backup/'image-verification'
    run('unmkinitramfs','/boot/initrd.img-'+TARGET,unpacked)
    image_modules={}
    for module in [m for _,_,names in ROLES for m in names]+['brcmutil']:
        selected=Path(get('modinfo','-k',TARGET,'-n',module))
        if module!='brcmutil':assert '/updates/dkms/' in str(selected)
        copies=list(unpacked.rglob(selected.name))
        assert copies and all(sha(p)==sha(selected) for p in copies),module
        image_modules[module]=dict(path=str(selected),sha256=sha(selected))
    assert not get('dpkg','--audit')
    assert preserve()==before, 'Existing kernels, image, policy, default or old reports changed'
    assert all((Path('/sys/module')/n/'srcversion').read_text().strip()==v for n,v in loaded.items())
    report=dict(backup=str(backup),target=TARGET,package_version=VERSION,
        installed_packages=packages,DKMS_installed_automatically=automatic,current_DKMS_builds=builds,
        image_modules=image_modules,eight_image_hashes_verified=True,
        current_kernel_unchanged=True,custom_and_official42_modules_images_unchanged=True,
        saved_entry_unchanged=True,old_PM_reports_unchanged=True,
        new_DKMS_target_allowlist_unchanged=True,
        scope='Official kernel installed; current three DKMS sources built and installed automatically by kernel/header package hooks; no per-ABI override.',
        booted=False,PM_test_performed=False,GRUB_configuration_regenerated_by_kernel_package=True)
    (backup/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
