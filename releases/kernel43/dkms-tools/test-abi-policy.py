#!/usr/bin/env python3
"""Check replacement-stack versus retained-helper ABI rules without kernel I/O."""
from pathlib import Path
import runpy
import sys
import tempfile
from unittest.mock import patch

script=Path(__file__).with_name('verify-abi.py')
with tempfile.TemporaryDirectory(prefix='dkms-abi-policy-') as tmp:
    root=Path(tmp);headers=root/'headers';source=root/'source'
    headers.mkdir();source.mkdir()
    (source/'brcmfmac.ko').touch()
    (headers/'Module.symvers').write_text('0x1\tpeer\tkernel/brcmfmac\tEXPORT_SYMBOL_GPL\n')
    (source/'Module.symvers').write_text('0x2\tpeer\tsource/brcmfmac\tEXPORT_SYMBOL_GPL\n')
    def check(replacements,crc,passed):
        try:
            with patch.object(sys,'argv',[str(script),str(headers),str(source),*replacements]),patch('subprocess.check_output',return_value=crc+' peer\n'):
                runpy.run_path(str(script),run_name='__main__')
        except RuntimeError:
            assert not passed
        else:assert passed
    check([], '0x2',False)
    check(['brcmfmac'],'0x2',True)
    check(['brcmfmac'],'0x3',False)
    check(['missing-module'],'0x2',False)
    # Even when the codec is replaced, a retained HDA helper must match.
    (headers/'Module.symvers').write_text('0x1\tpeer\tkernel/snd-hda-scodec-component\tEXPORT_SYMBOL_GPL\n')
    check(['brcmfmac'],'0x2',False)
print('Passed complete-stack replacement, retained-helper refusal, missing build and imported-CRC mismatch checks.')
