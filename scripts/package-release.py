#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the six-package layout from hash-pinned binaries without installation."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = '7.0.14-mbp14342p1'

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()

def run(*args):
    return subprocess.check_output([str(x) for x in args], text=True).strip()

def data_files(folder):
    result = {}
    for p in sorted(folder.rglob('*')):
        name = p.relative_to(folder).as_posix()
        if name.startswith(('DEBIAN/', 'usr/share/doc/')) or name == 'DEBIAN':
            continue
        if p.is_symlink():
            result[name] = ['symlink', p.readlink().as_posix()]
        elif p.is_file():
            result[name] = ['file', p.stat().st_mode & 0o7777, digest(p)]
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-directory', type=Path, required=True)
    p.add_argument('--output-directory', type=Path, required=True, help='New empty output directory')
    p.add_argument('--t1-input', type=Path, help='Explicit local T1 binary override; not a public release')
    p.add_argument('--t1-sha256')
    p.add_argument('--t1-version')
    p.add_argument('--t1-source', type=Path, help='Corresponding local source for an override')
    p.add_argument('--local-kernel-version', help='Keep an already configured local kernel package revision; build four driver packages only')
    p.add_argument('--modules-only', action='store_true', help='Assemble just the four module roles')
    p.add_argument('--t1-only', action='store_true', help='Assemble only the bridge and Touch Bar roles')
    args = p.parse_args()
    override = any([args.t1_input, args.t1_sha256, args.t1_version, args.t1_source])
    if override and not all([args.t1_input, args.t1_sha256, args.t1_version, args.t1_source]):
        p.error('A local override requires binary, hash, version and corresponding-source directory')
    layout = json.loads((ROOT / 'manifests/package-layout.json').read_text())
    if args.local_kernel_version and not override:
        p.error('A local kernel profile requires an explicit local T1 input')
    selected = [r for r in layout['packages'] if (not args.modules_only or r['kind'] == 'module')
                and (not args.t1_only or r['Package'] in ['mbp143-ibridge', 'mbp143-t1'])
                and (not override or (r['kind'] == 'module' if args.local_kernel_version else r['Package'] in ['mbp143-ibridge', 'mbp143-t1']))]
    inputs = {}
    for row in selected:
        is_t1 = row['Package'] in ['mbp143-ibridge', 'mbp143-t1']
        original = args.t1_input if override and is_t1 else args.input_directory / row['input_file']
        expected = args.t1_sha256 if override and is_t1 else row['input_sha256']
        if digest(original) != expected:
            raise RuntimeError('Input hash mismatch: ' + original.name)
        inputs[row['Package']] = original.resolve()
    args.output_directory.mkdir(parents=True, exist_ok=False)
    report = []
    for row in selected:
        name = row['Package']
        is_t1 = name in ['mbp143-ibridge', 'mbp143-t1']
        version = args.t1_version if override and is_t1 else ('0.1-2' if args.local_kernel_version else row['Version'])
        depends = row['Depends']
        if override and is_t1:
            depends = depends.replace('mbp143-ibridge (= 0.6-1)', 'mbp143-ibridge (= ' + version + ')')
        if args.local_kernel_version:
            depends = depends.replace('7.0.0-42.42+mbp143.3', args.local_kernel_version)
        predepends = 'linux-image-' + KERNEL + ' (= ' + (args.local_kernel_version or '7.0.0-42.42+mbp143.3') + ')'
        with tempfile.TemporaryDirectory(prefix='mbp143-package-') as temporary:
            base = Path(temporary)
            before, stage = base / 'before', base / 'stage'
            subprocess.run(['dpkg-deb', '--raw-extract', str(inputs[name]), str(before)], check=True)
            if row['kind'] == 'kernel':
                shutil.copytree(before, stage, symlinks=True)
                # Preserve original hooks and non-documentation payload exactly.
                text = (stage / 'DEBIAN/control').read_text()
                text = re.sub(r'^Version:.*$', 'Version: ' + version, text, flags=re.M)
                (stage / 'DEBIAN/control').write_text(text)
                shutil.rmtree(stage / 'usr/share/doc' / name)
            else:
                (stage / 'DEBIAN').mkdir(parents=True)
                control = ['Package: ' + name, 'Version: ' + version, 'Architecture: amd64',
                           'Maintainer: mbp143-ubuntu-compat contributors <6039975+gurkein@users.noreply.github.com>',
                           'Section: kernel', 'Priority: optional', 'Depends: ' + depends, 'Pre-Depends: ' + predepends,
                           'Conflicts: ' + ', '.join(row['legacy_conflicts']),
                           'Replaces: ' + ', '.join(row['legacy_conflicts']),
                           'Description: ' + row['description'],
                           ' Exact-kernel signed module; no live reload, boot-policy or PM operation.']
                (stage / 'DEBIAN/control').write_text('\n'.join(control) + '\n')
                source = before / row['input_module']
                if override and is_t1:
                    # Local historical T1 inputs can use an older package path.
                    matches = list(before.rglob(row['module'] + '.ko'))
                    if len(matches) != 1:
                        raise RuntimeError('Expected one source module for ' + row['module'])
                    source = matches[0]
                target = stage / row['module_path']
                target.parent.mkdir(parents=True)
                shutil.copy2(source, target)
                assert digest(source) == digest(target)
                config = stage / 'usr/lib/depmod.d' / (name + '-' + KERNEL + '.conf')
                config.parent.mkdir(parents=True, exist_ok=True)
                escaped = KERNEL.replace('.', '[.]')
                config.write_text('# Exact-kernel selected driver.\noverride ' + row['module'] +
                                  ' ^' + escaped + '$ updates/' + name + '\n')
                # Existing installed hooks use only depmod and initramfs regeneration.
                hook = ('#!/bin/sh\nset -e\ncase "$1" in\n'
                        '  configure|remove|purge)\n'
                        f'    if [ -d /lib/modules/{KERNEL} ]; then\n'
                        f'      depmod -a {KERNEL}\n'
                        f'      if [ -e /boot/vmlinuz-{KERNEL} ]; then\n'
                        f'        update-initramfs -u -k {KERNEL}\n'
                        '      fi\n    fi\n    ;;\nesac\nexit 0\n')
                for phase in ['postinst', 'postrm']:
                    f = stage / 'DEBIAN' / phase
                    f.write_text(hook)
                    f.chmod(0o755)
                if name == 'mbp143-ibridge':
                    # DKMS otherwise moves same-named packaged modules into its
                    # original_module backup when headers are configured later.
                    guard = stage / ('etc/dkms/apple-ib-drv--' + KERNEL + '.conf')
                    guard.parent.mkdir(parents=True)
                    guard.write_text('# This exact kernel uses the signed mbp143-ibridge/mbp143-t1 pair.\n'
                                     '# Other kernels retain their normal DKMS behavior.\n'
                                     "BUILD_EXCLUSIVE_KERNEL='^$'\n")
                    (stage / 'DEBIAN/conffiles').write_text('/' + guard.relative_to(stage).as_posix() + '\n')
                if name == 'mbp143-wifi':
                    f = stage / 'usr/lib/dracut/modules.d/91mbp143wifi/module-setup.sh'
                    f.parent.mkdir(parents=True)
                    f.write_text('''#!/bin/bash
# Preserve dynamically requested vendor modules in host-only images.
check() {
    [[ "$kernel" == "7.0.14-mbp14342p1" ]] || return 1
    [[ -f /lib/modules/7.0.14-mbp14342p1/updates/mbp143-wifi/brcmfmac.ko ]] || return 1
    return 0
}
installkernel() {
    hostonly='' instmods -c brcmfmac-wcc brcmfmac-cyw brcmfmac-bca
}
''')
                    f.chmod(0o755)
            docs = stage / 'usr/share/doc' / name
            docs.mkdir(parents=True, exist_ok=True)
            for f in ['LICENSE.md', 'THIRD_PARTY_NOTICES.md', 'CREDITS.md', 'SOURCE-NOTICES.txt']:
                shutil.copy2(ROOT / f, docs / f)
            shutil.copy2(ROOT / 'docs/source-distribution.md', docs / 'SOURCE-DISTRIBUTION.md')
            shutil.copytree(ROOT / 'LICENSES', docs / 'LICENSES')
            (docs / 'copyright').write_text('''Source: https://github.com/gurkein/mbp143-ubuntu-compat
Copyright: original per-file holders in SOURCE-NOTICES.txt and corresponding sources.
License: imported kernel/driver per-file terms; independent project tools MIT;
 new documentation CC BY 4.0. Complete license texts accompany this notice.
Changes: six-package layout prepared 2026-11-05; signed executable bytes preserved.
See THIRD_PARTY_NOTICES.md and SOURCE-DISTRIBUTION.md.
''')
            if override and is_t1:
                destination = docs / 'local-corresponding-source'
                destination.mkdir()
                for f in args.t1_source.iterdir():
                    if f.is_file() and (f.suffix in {'.c', '.h'} or f.name in {'Makefile', 'LICENSE'}):
                        shutil.copy2(f, destination / f.name)
                assert (destination / 'apple-touchbar.c').exists()
            # Refresh checksums and size for the final staged package.
            checksums = []
            total = 0
            for f in sorted(stage.rglob('*')):
                rel = f.relative_to(stage)
                if f.is_file() and not f.is_symlink() and rel.parts[0] != 'DEBIAN':
                    total += f.stat().st_size
                    checksums.append(hashlib.md5(f.read_bytes()).hexdigest() + '  ' + rel.as_posix())
            (stage / 'DEBIAN/md5sums').write_text('\n'.join(checksums) + '\n')
            control = stage / 'DEBIAN/control'
            text = re.sub(r'^Installed-Size:.*\n', '', control.read_text(), flags=re.M)
            control.write_text(text + 'Installed-Size: ' + str((total + 1023)//1024) + '\n')
            target = args.output_directory / f'{name}_{version}_amd64.deb'
            subprocess.run(['dpkg-deb', '--root-owner-group', '-Zzstd', '-z10', '--build', str(stage), str(target)], check=True)
            verify = base / 'verify'
            subprocess.run(['dpkg-deb', '--raw-extract', str(target), str(verify)], check=True)
            modules = []
            if row['kind'] == 'kernel':
                assert data_files(before) == data_files(verify)
                for phase in ['postinst', 'postrm', 'preinst', 'prerm']:
                    f = before / 'DEBIAN' / phase
                    if f.exists():
                        assert f.read_bytes() == (verify / 'DEBIAN' / phase).read_bytes()
            else:
                module = verify / row['module_path']
                assert digest(module) == digest(before / row['input_module'])
                assert len(list(verify.rglob('*.ko'))) == 1
                assert run('modinfo', '-F', 'vermagic', module).split()[0] == KERNEL
                assert run('modinfo', '-F', 'sig_key', module)
                modules.append(dict(module=row['module'], path=row['module_path'], sha256=digest(module),
                                    srcversion=run('modinfo', '-F', 'srcversion', module),
                                    sig_key=run('modinfo', '-F', 'sig_key', module)))
            report.append(dict(Package=name, Version=version, Architecture='amd64', Depends=depends,
                               **{'Pre-Depends': predepends if row['kind'] == 'module' else ''},
                               Conflicts=', '.join(row.get('legacy_conflicts', [])),
                               file=target.name, bytes=target.stat().st_size, sha256=digest(target),
                               input_file=inputs[name].name, input_sha256=digest(inputs[name]),
                               modules=modules, executable_payload_preserved=True,
                               local_T1_override=bool(override and is_t1)))
            print('Verified package:', name, version, flush=True)
    (args.output_directory / 'package-report.json').write_text(json.dumps(report, indent=2) + '\n')

if __name__ == '__main__':
    main()
