#!/usr/bin/env python3
"""Create source-only DKMS DEBs from the current, locally reviewed driver sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
KERNEL = '7.0.14-mbp14342p1'
KERNEL_PATTERN = '^7[.]0([.-]|$)'
FLAGS = '-DAPPLE_PINSENSE_FIXUP -DAPPLE_CODECS -DCONFIG_SND_HDA_RECONFIG=1 -Wno-unused-variable -Wno-unused-function -Wno-error -Wno-incompatible-pointer-types -Wno-discarded-qualifiers -Wno-implicit-function-declaration'
CANDIDATES = ROOT / 'experiments/kernel-42/candidates'
ROLES = {
    't1': {'name': 'mbp143-t1', 'version': '0.8', 'replaces': ['mbp143-ibridge', 'mbp143-t1'],
           'modules': [('apple-ibridge', 'source'), ('apple-touchbar', 'source')]},
    'audio': {'name': 'mbp143-audio', 'version': '0.1', 'replaces': ['mbp143-audio'],
              'modules': [('snd-hda-codec-cs8409', 'source/codecs/cirrus')]},
    'sbs': {'name': 'mbp143-sbs', 'version': '0.1', 'replaces': ['sbs-dkms'],
            'modules': [('sbs', 'source')]},
    'thunderbolt': {'name': 'mbp143-thunderbolt', 'version': '0.1', 'replaces': [],
                    'modules': [('thunderbolt', 'source/thunderbolt'), ('thunderbolt_net', 'source/net')]},
    'amdgpu': {'name': 'mbp143-amdgpu', 'version': '0.3', 'replaces': [],
               'modules': [('amdgpu', 'source/amdgpu')]},
    'wifi': {'name': 'mbp143-wifi', 'version': '0.2', 'replaces': ['mbp143-wifi'],
             'modules': [('brcmfmac', 'source/brcmfmac'), ('brcmfmac-wcc', 'source/brcmfmac/wcc'),
                         ('brcmfmac-cyw', 'source/brcmfmac/cyw'), ('brcmfmac-bca', 'source/brcmfmac/bca')]},
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, content, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(0o755 if executable else 0o644)

def copy_sources(source, dest):
    """Export source text only; never copy objects, VCS metadata or private keys."""
    for path in source.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(source)
        if any(part.startswith('.') for part in rel.parts):
            continue
        if path.suffix in ('.c', '.h') and not path.name.endswith('.mod.c') or path.name in ('Makefile', 'Kbuild', 'Kconfig', 'LICENSE'):
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)

def build(out, roles=None):
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for role, spec in ROLES.items():
        if roles and role not in roles:
            continue
        revision = '1' if role in ('t1', 'sbs', 'thunderbolt', 'amdgpu') else ('4' if role == 'wifi' else '3')
        name, version = spec['name'], spec['version']
        package = name + '-dkms'
        stage = out / (package + '-stage')
        src = stage / 'usr/src' / (name + '-' + version)
        source = src / 'source'
        source.mkdir(parents=True)
        if role in ('sbs', 'thunderbolt', 'amdgpu'):
            kernel_source = ROOT / 'experiments/kernel-43/linux-source-7.0.0'
            if role == 'sbs':
                for filename in ('sbs.c', 'sbshc.h'):
                    shutil.copyfile(kernel_source / 'drivers/acpi' / filename, source / filename)
                write(source / 'Makefile', 'obj-m := sbs.o\n')
                module_directory = 'source'
            elif role == 'thunderbolt':
                copy_sources(kernel_source / 'drivers/thunderbolt', source / 'thunderbolt')
                copy_sources(kernel_source / 'drivers/net/thunderbolt', source / 'net')
                write(source / 'Makefile',
                      'subdir-ccflags-y := -include $(abspath $(src))/include/linux/thunderbolt.h\n'
                      'obj-m := thunderbolt/ net/\n')
                public_header = source / 'include/linux/thunderbolt.h'
                public_header.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(kernel_source / 'include/linux/thunderbolt.h', public_header)
                module_directory = 'source'
            else:
                copy_sources(kernel_source / 'drivers/gpu/drm/amd', source)
                trace_header = source / 'amdgpu/amdgpu_trace.h'
                trace_header.write_text(trace_header.read_text().replace(
                    '#define TRACE_INCLUDE_PATH ../../drivers/gpu/drm/amd/amdgpu',
                    '#define TRACE_INCLUDE_PATH .'))
                makefile = source / 'amdgpu/Makefile'
                makefile.write_text(makefile.read_text() + '\n# Resolve trace headers during external module builds.\nccflags-y += -I$(src)\n')
                # DRM 7.0 headers contain both two- and three-argument iterator macros.
                # The underlying object accessor has the same interface in both.
                for filename in ('amdgpu_cs.c', 'amdgpu_eviction_fence.c'):
                    driver_file = source / 'amdgpu' / filename
                    contents = driver_file.read_text()
                    for context, variable in (('&p->exec', 'obj'), ('&p->exec', 'gobj'), ('exec', 'obj')):
                        old_iterator = f'drm_exec_for_each_locked_object({context}, {variable})'
                        portable_iterator = (
                            'for (unsigned long object_index = 0;\n'
                            f'\t     ({variable} = drm_exec_obj({context}, object_index));\n'
                            '\t     ++object_index)')
                        contents = contents.replace(old_iterator, portable_iterator)
                    driver_file.write_text(contents)
                fence_file = source / 'amdgpu/amdgpu_job.c'
                fence_text = fence_file.read_text().replace(
                    'dma_fence_was_initialized(', 'mbp143_dma_fence_was_initialized(')
                fence_text = fence_text.replace('#include "amdgpu_xgmi.h"',
                                                '#include "amdgpu_xgmi.h"' + '\n#ifdef MBP143_LEGACY_DMA_FENCE\n/* Older 7.0 fences retain their operations pointer after initialization. */\nstatic bool mbp143_dma_fence_was_initialized(struct dma_fence *fence)\n{\n\treturn fence && fence->ops;\n}\n#else\n#define mbp143_dma_fence_was_initialized dma_fence_was_initialized\n#endif\n')
                fence_file.write_text(fence_text)
                display_file = source / 'display/amdgpu_dm/amdgpu_dm.c'
                display_file.write_text(display_file.read_text().replace('\telse if (!IS_ERR_OR_NULL(panel_backlight_quirk) &&\n\t\t panel_backlight_quirk->force_pwm)\n\t\tcaps->aux_support = false;', '#ifdef MBP143_HAVE_PANEL_PWM_QUIRK\n\telse if (!IS_ERR_OR_NULL(panel_backlight_quirk) &&\n\t\t panel_backlight_quirk->force_pwm)\n\t\tcaps->aux_support = false;\n#endif'))
                module_directory = 'source/amdgpu'
            make = 'make -C /lib/modules/"$1"/build M="$PWD/' + module_directory + '" -j"$2" modules'
        elif role == 't1':
            copy_sources(CANDIDATES / 't1-keyboard-forwarding/package/source', source)
            patch = HERE / 'patches/t1-xremap-usb-identity.patch'
            subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)],
                           cwd=source, check=True)
            shutil.copyfile(patch, src / patch.name)
            make = 'make -C /lib/modules/"$1"/build M="$PWD/source" -j"$2" modules'
        elif role == 'audio':
            copy_sources(CANDIDATES / 'audio-pr220/source', source)
            make = 'make -C /lib/modules/"$1"/build M="$PWD/source" -j"$2" CFLAGS_MODULE=' + "'" + FLAGS + "' modules"
            shutil.copyfile(CANDIDATES / 'audio-pr220/LICENSE', src / 'LICENSE')
        else:
            copy_sources(CANDIDATES / 'connectivity-pr596/wifi-d0-only/source/drivers/net/wireless/broadcom/brcm80211', source)
            patch = HERE / 'patches/brcmfmac-apple-fem-control-v3.patch'
            # Apply to a fresh export; the reviewed D0 baseline remains immutable.
            for args in (['--dry-run'], []):
                subprocess.run(['patch', '--batch', '--fuzz=0', '-p6', *args,
                                '-i', str(patch)], cwd=source, check=True)
            subprocess.run(['patch', '--batch', '--fuzz=0', '-R', '--dry-run', '-p6',
                            '-i', str(patch)], cwd=source, check=True)
            shutil.copyfile(patch, src / patch.name)
            make = 'make -C /lib/modules/"$1"/build M="$PWD/source/brcmfmac" -j"$2" modules'
        new_driver = role in ('sbs', 'thunderbolt', 'amdgpu')
        helpers = ['verify-abi.py'] if new_driver else ['verify-abi.py', 'restore-originals.py']
        for helper in helpers:
            shutil.copyfile(HERE / helper, src / helper)
            (src / helper).chmod(0o755)
        if new_driver:
            patch_number = {'sbs': '0008', 'thunderbolt': '0007', 'amdgpu': '0006'}[role]
            manifest = json.loads((ROOT / 'experiments/kernel-43/patches/module-patches.json').read_text())
            patch_record = next(record for record in manifest if record['file'].startswith(patch_number))
            # Module fixes are applied only to DKMS exports, not the kernel tree.
            patch = ROOT / 'experiments/kernel-43/patches/dkms' / patch_record['file']
            assert sha(patch) == patch_record['applied_patch_sha256']
            prefix = {'sbs': 'drivers/acpi/', 'thunderbolt': 'drivers/',
                      'amdgpu': 'drivers/gpu/drm/amd/'}[role]
            strip = len(Path(prefix).parts) + 1
            subprocess.run(['patch', '--batch', '--fuzz=0', '-p' + str(strip),
                            '-i', str(patch)], cwd=source, check=True)
            for relative, digest in patch_record['resulting_files'].items():
                assert relative.startswith(prefix)
                assert sha(source / relative[len(prefix):]) == digest, relative
            write(src / 'source-origin.json', json.dumps(dict(
                ubuntu_source='7.0.0-43.43', module_patch=patch_record,
                target_series='7.0'), indent=2) + '\n')
        replacements = ' '.join(module for module, _ in spec['modules'])
        if new_driver:
            replacements += ' --strict-exports'
        write(src / 'build.sh', '#!/bin/sh\nset -eu\n' + make + '\npython3 ./verify-abi.py /lib/modules/"$1"/build "$PWD/source" ' + replacements + '\n', True)
        if role == 'amdgpu':
            build_text = (src / 'build.sh').read_text()
            probe = """amdgpu_compat_flags=""
if ! grep -q dma_fence_was_initialized /lib/modules/"$1"/build/include/linux/dma-fence.h; then
    amdgpu_compat_flags="-DMBP143_LEGACY_DMA_FENCE"
fi
if grep -Eq 'bool[[:space:]]+force_pwm;' /lib/modules/"$1"/build/include/drm/drm_utils.h; then
    amdgpu_compat_flags="$amdgpu_compat_flags -DMBP143_HAVE_PANEL_PWM_QUIRK"
fi
"""
            build_text = build_text.replace('set -eu\n', 'set -eu\n' + probe, 1)
            build_text = build_text.replace('-j"$2" modules', '-j"$2" CFLAGS_MODULE="$amdgpu_compat_flags" modules', 1)
            write(src / 'build.sh', build_text, True)
        config = f'''PACKAGE_NAME="{name}"
PACKAGE_VERSION="{version}"
AUTOINSTALL="yes"
# Automatically build/install for the 7.0 API series; hardware PM qualification is separate.
BUILD_EXCLUSIVE_KERNEL="{KERNEL_PATTERN}"
BUILD_EXCLUSIVE_ARCH="^x86_64$"
MAKE[0]="./build.sh ${{kernelver}} ${{parallel_jobs}}"
{'' if new_driver else 'POST_INSTALL="restore-originals.py ' + name + ' ${kernelver} ${arch} ${dkms_tree} ${install_tree}"' }
'''
        for i, (module, location) in enumerate(spec['modules']):
            config += f'BUILT_MODULE_NAME[{i}]="{module}"\nBUILT_MODULE_LOCATION[{i}]="{location}"\nDEST_MODULE_LOCATION[{i}]="/updates/dkms"\n'
        write(src / 'dkms.conf', config)
        old = ', '.join(spec['replaces'])
        write(stage / 'DEBIAN/control', f'''Package: {package}
Version: {version}-{revision}
Architecture: all
Maintainer: Local MacBook Compatibility Maintainer <builder@localhost>
Section: kernel
Priority: optional
Depends: dkms (>= 3.0), build-essential, python3, kmod, linux-initramfs-tool
{('Conflicts: ' + old + chr(10) + 'Replaces: ' + old + chr(10)) if old else ''}Description: Source-only MacBookPro14,3 {role} DKMS driver
 Reviewed local sources rebuilt by DKMS for the qualified target kernel.
 No precompiled modules, firmware blobs or private signing keys are included.
 Kernel PCI/ACPI patches remain separate requirements.
''')
        write(stage / 'DEBIAN/postinst', f'''#!/bin/sh
set -eu
if [ "$1" = configure ]; then
    # Metadata-only upgrades retain valid builds for the unchanged DKMS source version.
    if [ ! -L /var/lib/dkms/{name}/{version}/source ]; then
        dkms add -m {name} -v {version}
    fi
    for headers in /lib/modules/*/build; do
        [ -d "$headers/include" ] || continue
        kernel=$(basename "$(dirname "$headers")")
        case "$kernel" in 7.0|7.0.*|7.0-*) ;; *) continue ;; esac
        [ -e "/boot/vmlinuz-$kernel" ] || continue
        dkms install -m {name} -v {version} -k "$kernel" -j 2
    done
fi
''', True)
        write(stage / 'DEBIAN/prerm', f'''#!/bin/sh
set -eu
case "$1" in
  remove|deconfigure)
    if [ -d /var/lib/dkms/{name}/{version} ]; then
      dkms remove -m {name} -v {version} --all
    fi
    ;;
esac
''', True)
        if role in ('t1', 'wifi', 'sbs', 'thunderbolt', 'amdgpu'):
            # Exact Ubuntu dh-dkms 3.2.2 lifecycle templates; no source retention/import.
            for hook in ['postinst', 'prerm']:
                template = (HERE / 'debhelper' / (hook + '-dkms.in')).read_text()
                template = template.replace('#MODULE_NAME#', name).replace('#MODULE_VERSION#', version)
                write(stage / 'DEBIAN' / hook, '#!/bin/sh\nset -e\n' + template, True)
        # Claim matching-source originals too: rebuilding the same source for
        # DKMS must not silently keep an old binary at an unrelated path.
        write(stage / f'usr/share/dkms/modules_to_force_install/{package}', name + '_version-override\n')
        # Standard dpkg trigger batches initramfs refreshes for install/removal.
        write(stage / 'DEBIAN/triggers', 'activate-noawait update-initramfs\n')
        # Disable legacy identities globally so header hooks never race current sources.
        if role == 't1':
            write(stage / 'etc/dkms/apple-ib-drv.conf', "# Superseded by mbp143-t1; keep source only for explicit rollback.\nAUTOINSTALL=\"no\"\nBUILD_EXCLUSIVE_KERNEL='^$'\n")
        if role == 'audio':
            write(stage / 'etc/dkms/mbp143-cs8409.conf', "# Superseded by mbp143-audio; keep source only for explicit rollback.\nAUTOINSTALL=\"no\"\nBUILD_EXCLUSIVE_KERNEL='^$'\n")
        depmod = ''.join(f'override {module} {KERNEL_PATTERN} updates/dkms\n' for module, _ in spec['modules'])
        write(stage / f'usr/lib/depmod.d/{package}.conf', '# Prefer current DKMS modules throughout the 7.0 series.\n' + depmod)
        if role == 'wifi':
            write(stage / 'usr/lib/dracut/modules.d/91mbp143wifi/module-setup.sh', '''#!/bin/bash
check() {
    [[ "$kernel" =~ ^7[.]0([.-]|$) ]] || return 1
    compgen -G "/lib/modules/$kernel/updates/dkms/brcmfmac.ko*" >/dev/null || return 1
    return 0
}
installkernel() {
    hostonly='' instmods -c apple-ibridge apple-touchbar snd-hda-codec-cs8409 brcmfmac brcmfmac-wcc brcmfmac-cyw brcmfmac-bca brcmutil
}
''', True)
        if role in ('sbs', 'thunderbolt', 'amdgpu'):
            write(stage / f'etc/dkms/framework.conf.d/{name}-signing.conf', f'''# Match the existing custom kernel's signing identity.
case "${{module:-}}:${{kernelver:-}}" in
  {name}:{KERNEL})
    mok_signing_key=/var/lib/mbp143-dkms-signing/key.pem
    mok_certificate=/var/lib/mbp143-dkms-signing/certificate.der
    ;;
esac
''')
        doc = stage / 'usr/share/doc' / package
        doc.mkdir(parents=True)
        olddoc = Path('/usr/share/doc') / (spec['replaces'][0] if spec['replaces'] else package)
        if not olddoc.exists():
            olddoc = Path('/usr/share/doc') / package
        for p in olddoc.iterdir() if olddoc.exists() else []:
            if p.name != 'local-corresponding-source':
                if p.is_dir(): shutil.copytree(p, doc / p.name)
                else: shutil.copyfile(p, doc / p.name)
        write(doc / 'DKMS-MIGRATION.md', f'''# Source-only DKMS migration

Role: {role}; DKMS identity: {name}/{version}.
Source baseline: {'Ubuntu 7.0.0-43.43 with the reviewed local module patch' if role in ('sbs', 'thunderbolt', 'amdgpu') else 'existing locally reviewed driver sources'}. Hardware verification follows normal reboot.
AUTOINSTALL is enabled for the complete 7.0 API series. New matching kernel/headers
invoke the standard DKMS kernel hooks automatically. ABI checks reject incompatible
builds; a successful build is not boot, full-kernel-patch or suspend qualification.
Legacy T1/audio identities are globally excluded from autoinstall; their source
trees remain available for an explicit backed-up rollback.
No live driver reload or power transition is performed by these packages.
T1 still requires its matching bridge; audio shared-helper CRCs are checked;
Wi-Fi rebuilds its dynamically requested vendor helpers. Kernel patches are separate.
''')
        if role in ('sbs', 'thunderbolt', 'amdgpu'):
            shutil.copyfile('/usr/share/common-licenses/GPL-2', doc / 'copyright')
        provenance = {str(p.relative_to(src)): sha(p) for p in sorted(src.rglob('*')) if p.is_file()}
        write(src / 'source-manifest.json', json.dumps(provenance, indent=2) + '\n')
        deb = out / f'{package}_{version}-{revision}_all.deb'
        subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage), str(deb)], check=True)
        # Source tarball is also usable independently of the Debian wrapper.
        archive = out / f'{name}-{version}-dkms-source.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            tar.add(src, arcname=src.name)
        for hook in ['preinst', 'postinst', 'prerm']:
            if not (stage / 'DEBIAN' / hook).exists():
                continue
            subprocess.run(['sh', '-n', str(stage / 'DEBIAN' / hook)], check=True)
        subprocess.run(['bash', '-n', str(src / 'dkms.conf')], check=True)
        assert not any(p.suffix in ('.ko', '.o', '.pem', '.key') or p.name.endswith('.mod.c') for p in stage.rglob('*'))
        records.append(dict(role=role, package=package, version=version+'-'+revision, dkms_name=name,
                            dkms_version=version, deb=str(deb), sha256=sha(deb),
                            source=str(src), source_archive=str(archive), source_archive_sha256=sha(archive),
                            modules=[m for m, _ in spec['modules']], source_only=True))
    write(out / 'packages.json', json.dumps(records, indent=2)+'\n')
    print(out / 'packages.json')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--role', choices=ROLES, action='append', help='Build only selected roles')
    args = parser.parse_args()
    build(args.output.resolve(), args.role)
