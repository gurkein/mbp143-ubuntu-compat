#!/usr/bin/env python3
"""Test policy refusals and runtime restoration with ordinary temporary files."""
from pathlib import Path
from unittest.mock import patch
import importlib.util
import tempfile

spec = importlib.util.spec_from_file_location('trial', Path(__file__).with_name('mbp143-suspend-check.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
good = dict(profile='automatic',legacy_parameters_absent=True,s3_status=0,runtime_state_clear=True,kernel_hard_errors=False,kernel='7.0.14-mbp14342p1', model='MacBookPro14,3', module_matches=True,
            WCC_loaded=True, pm_test_none=True, deep_available=True, native_PME=True,
            NVMe_guard=True, journal_complete=True, T1_skip_guard='1')
assert not m.refusal_reasons(good)
assert not m.refusal_reasons(dict(good,s3_status=4))
for key, value in [('kernel','7.0.0-42-generic'),('model','other'),('module_matches',False),
                   ('WCC_loaded',False),('pm_test_none',False),('deep_available',False),
                   ('native_PME',False),('NVMe_guard',False),('journal_complete',False),
                   ('T1_skip_guard','0'),('runtime_state_clear',False),('kernel_hard_errors',True),
                   ('profile','repeat'),('legacy_parameters_absent',False),('s3_status',None),
                   ('s3_status',1),('s3_status',2),('s3_status',3)]:
    assert m.refusal_reasons(dict(good, **{key: value})), key
with tempfile.TemporaryDirectory(prefix='suspend-policy-offline-', dir='/tmp') as tmp:
    root = Path(tmp)
    for old in ['auto', 'on']:
        control = root/'device/power/control'
        control.parent.mkdir(parents=True, exist_ok=True)
        control.write_text(old)
        with patch.object(m, 'MARKER', root/'runtime.json'), patch.object(m, 'SYS_ROOT', root):
            m.prepare_control(control)
            assert control.read_text().strip() == 'on'
            try:
                m.prepare_control(control)
            except FileExistsError:
                pass
            else:
                raise AssertionError('Overwrote an interrupted preparation')
            m.cleanup_control()
            assert control.read_text().strip() == old and not m.MARKER.exists()
            m.cleanup_control()
    with patch.object(m,'MARKER',root/'runtime.json'),patch.object(m,'FAILED',root/'failed.json'),patch.object(m,'SYS_ROOT',root),patch.dict(m.os.environ,{'SERVICE_RESULT':'exit-code'}):
        control.write_text('auto')
        m.prepare_control(control)
        m.cleanup_control()
        assert control.read_text().strip()=='auto' and not m.MARKER.exists() and m.FAILED.exists()
print('Passed automatic readiness and failure cases, exclusive preparation, auto/on restoration and systemd failure latch.')
print('All controls were ordinary temporary files; no host PM operation occurred.')
