"""Exercise the actual runner under Windows' copied uppercase environment."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import traceback
from unittest.mock import patch

source, phase, destination = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
spec = importlib.util.spec_from_file_location('actual_runner', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fixture = Path(tempfile.mkdtemp(prefix='r15-diagnostic-env-'))
out = fixture / 'output'
calls = []
def no_process(command, **kwargs):
    calls.append(command)
    assert kwargs['env']['POWERSHELL_TELEMETRY_OPTOUT'] == '1'
    assert kwargs['env']['DOTNET_CLI_TELEMETRY_OPTOUT'] == '1'
    assert kwargs['env']['POWERSHELL_UPDATECHECK'] == 'Off'
    raise OSError('controlled launch refusal; no process started')
error, code, stdout = None, None, io.StringIO()
with patch.dict(os.environ, {'SYSTEMROOT': 'C:\\Windows', 'INSTALL_TEST_PS7': 'C:\\owned-runtime\\pwsh.exe'}, clear=True), patch.object(module.platform, 'system', return_value='Windows'), patch.object(module.platform, 'platform', return_value='Windows-host-identity-intercepted-for-control'), patch.object(module.subprocess, 'run', side_effect=no_process), patch.object(sys, 'argv', [str(source), '--output', str(out)]), contextlib.redirect_stdout(stdout):
    try:
        code = module.main()
    except Exception:
        error = traceback.format_exc()
receipt = json.loads((out / 'result.json').read_text()) if (out / 'result.json').exists() else None
green = code == 1 and error is None and len(calls) == 6 and receipt['complete'] is True and all(r['acquisitionError'] and r['status'] == 'captured' for r in receipt['commands'])
red = code is None and len(calls) == 0 and error is not None and "KeyError: 'SystemRoot'" in error and receipt is None
result = {'schema': 'r0015-diagnostic-uppercase-environment.v1', 'phase': phase, 'runner_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'fixture': str(fixture), 'real_processes': 0, 'attempted_intercepted_launches': len(calls), 'return_code': code, 'error': error, 'native_windows': False, 'installer_qualification': False, 'expected_observation': red if phase == 'red' else green, 'receipt': receipt}
destination.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('receipt', 'error')}))
assert result['expected_observation']
