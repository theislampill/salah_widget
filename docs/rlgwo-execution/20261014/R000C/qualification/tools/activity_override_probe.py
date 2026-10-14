"""One diagnostic of Firefox's documented automation activity criterion.

Fresh isolated browser only. Preserve the reviewed twenty-second passive probe,
original readiness, source, reduced-motion input and native recorder. This does
not qualify the weather case or simulate foreground/desktop interaction.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys

probe = Path(__file__).with_name('visibility_probe.py')
assert hashlib.sha256(probe.read_bytes()).hexdigest() == '9d4b7cc44a888aed71224f7566763aeee36e0edccf48cefb09e5005716679e90'
sys.path.insert(0, str(Path.cwd() / 'tools/cp9'))
import browser_runtime

original_options = browser_runtime.browser_options
preference = {'layout.testing.top-level-always-active': True}


def diagnostic_options():
    family, options = original_options()
    assert family == 'firefox'
    assert 'firefox_user_prefs' not in options
    return family, {**options, 'firefox_user_prefs': preference.copy()}


browser_runtime.browser_options = diagnostic_options
out = Path(sys.argv[sys.argv.index('--out') + 1]).resolve()
runpy.run_path(str(probe), run_name='__main__')
(out / 'activity-override-binding.json').write_text(json.dumps({
    'schema': 'r000c-activity-override-diagnostic/v1',
    'diagnosticOnly': True,
    'preference': preference,
    'appliesTo': 'Only the fresh isolated Firefox launch options',
    'wrapperSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'probeSha256': hashlib.sha256(probe.read_bytes()).hexdigest(),
    'nativeLogging': 'timestamp,sync,PresShell:5,nsRefreshDriver:5',
    'criteria': ['Exact fixture URL logs native Activeness overridden by pref',
                 'Actual last-render summaries resume ordinary progression',
                 'Original native video contains a readable complete card'],
    'limitations': __doc__,
}, indent=2) + '\n', encoding='utf8')
