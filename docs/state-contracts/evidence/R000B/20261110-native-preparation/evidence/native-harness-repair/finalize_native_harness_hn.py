from pathlib import Path
import hashlib
import sys

base = Path('/workspace/scratch/15b8fb6ac4c2/r000b-work')
if sys.argv[1] == 'fixture':
    path = base / 'tests/rlgwo/r000b-no-timetable-fixture.html'
    expected = 'd142fcf74612e82003a365d84d7316773f008a74a72f5da82b056b9dac50edef'
    old = '        const matrix=new DOMMatrixReadOnly(style.transform==="none"?undefined:style.transform);'
    new = '        // R000B_HN_GEOMETRY_CONSTRUCTOR_V2_1\n        const matrix=style.transform==="none"?new DOMMatrixReadOnly():new DOMMatrixReadOnly(style.transform);'
elif sys.argv[1] == 'driver':
    path = base / 'tools/qa/run_r000b_withdrawal.py'
    expected = '82b65b459dd1122fd13a8d204c16192b88cde740541f1e540a29bfd40bfc5144'
    old = "        row['checks']['noErrors'] = not row['pageErrors']"
    new = "        # R000B_HN_ERROR_CHANNELS_V2_1\n        row['checks']['noErrorsInObservedBrowserFixtureAndTeardownChannels'] = not row['pageErrors']"
else:
    raise ValueError('Expected fixture or driver')
assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
text = path.read_text(); assert text.count(old) == 1
path.write_text(text.replace(old, new))
print(hashlib.sha256(path.read_bytes()).hexdigest(), path)
