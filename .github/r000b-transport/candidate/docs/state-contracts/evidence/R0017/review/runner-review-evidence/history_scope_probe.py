"""One missing-history boundary probe; no inherited command is launched."""
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch
import uuid

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
path = here / 'inputs/tools/cp9/run_native_regressions.py'
spec = importlib.util.spec_from_file_location('history_scope_review', path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
root = Path('/workspace/scratch/7a8daf93afaa/r0017-explicit-work')
selected = runner.build_plan(root, selected=['r0021-reveal'])[0]
out = here / ('history-scope-' + uuid.uuid4().hex[:12])
out.mkdir()
with patch.object(runner, 'history_input', side_effect=lambda _, locator: {
        'locator': locator, 'available': False, 'blob': None,
        'reason': 'controlled absent exact object; not a claim about live availability'}), \
        patch.object(runner.subprocess, 'run', side_effect=AssertionError('no suite launch authorized')) as child:
    row = runner.execute_command(root, out, selected, timeout=1)
    observed = {'selectedCommand': selected[0], 'observed': row, 'childCalls': child.call_count,
                'scope': 'Only exact historical availability was changed in a controlled double; current source files were read without modification.'}
(out / 'observation.json').write_text(json.dumps(observed, indent=2) + '\n')
print(json.dumps({'receipt': str(out), **observed}, indent=2))
