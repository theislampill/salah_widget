"""Finish only three missing Firefox observations using the corrected sidecar owner."""
from pathlib import Path
import ast
O=Path(__file__).resolve().parent
s=(O/'run_visual_parent_r125_r126.py').read_text(encoding='utf-8')
s=s.replace('integrated-r30-owner-callbacks','integrated-r31-file-transport').replace('visual-parent-r125-r126','visual-r130').replace('3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821','1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b').replace('capture-driver/','capture-driver-r130/')
s=''.join(line for line in s.splitlines(keepends=True) if not line.startswith("  ('chromium-") and not line.startswith(" result.append({'name':'firefox-parent'"))
s=s.replace("paths=[Path(__file__),", "paths=[Path(__file__),O/'prepare_source_recorder_r130.py',O/'source_recorder_r130.test.cjs',O/'intake/source-recorder-r130.json',O/'intake/source-recorder-r130-tests.txt',O/'prepare_visual_r130.py',")
s=s.replace("'No repeats remain; each named case once.","'Authorized successor; one corrected source-sidecar sequence per missing Firefox condition.")
s=s.replace("'Five missing ordinary conditions and two actual-parent sequences with one Ccloud overlap; r119 source unchanged. Twilight10:58Z source arithmetic gives UI solar elevation -6.139996 degrees and moonShow0.627999; actual returned state/pixels still required; no natural whole-day claim.'","'Firefox exact clear, cloud, twilight only. Original source timestamps/JPEG bytes preserved; no interpolation or inference across gaps. Old acquisition failure remains retained. Actual returned astronomy and original pixels govern.'")
ast.parse(s);(O/'run_visual_r130.py').write_text(s,encoding='utf-8',newline='\n')
print('Three missing visual cases prepared; no native run')
