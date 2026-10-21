"""One original twilight observation followed by explicit lunar-layer controls."""
from pathlib import Path
import ast,shutil
O=Path(__file__).resolve().parent;H=O/'twilight-tools-r131';assert not H.exists()
shutil.copytree(O/'visual-tools-r126',H,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy2(O/'twilight_moon_r131.js',H/'tools/cp9/celestial_layer_controls.js')
s=(O/'run_visual_parent_r125_r126.py').read_text(encoding='utf-8').replace('integrated-r30-owner-callbacks','integrated-r31-file-transport').replace('visual-parent-r125-r126','twilight-r131').replace('3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821','1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b')
lines=[]
for line in s.splitlines(keepends=True):
 if line.startswith("  ('"):
  if "('chromium-twilight'" not in line:continue
  line="  ('chromium-twilight','chromium','twilight','direct',1,'cold','twilight-tools-r131')]:\n"
 if line.startswith(" result.append({'name':'firefox-parent'"):continue
 lines.append(line)
s=''.join(lines)
s=s.replace("'--persistent-profile','--video','--video-only','--compositor-marker'","'--persistent-profile','--video-only','--compositor-marker','--layers'")
s=s.replace("paths=[Path(__file__),", "paths=[Path(__file__),O/'prepare_twilight_r131.py',O/'twilight_moon_r131.js',")
s=s.replace("O/'visual-tools-r126',O/'visual-tools-r126-exact'", "O/'twilight-tools-r131',O/'visual-tools-r126-exact'")
s=s.replace("'No repeats remain; each named case once.","'Authorized successor; one twilight lunar layer discriminator.")
s=s.replace("'Five missing ordinary conditions and two actual-parent sequences with one Ccloud overlap; r119 source unchanged. Twilight10:58Z source arithmetic gives UI solar elevation -6.139996 degrees and moonShow0.627999; actual returned state/pixels still required; no natural whole-day claim.'", "'Same exact twilight condition. Ordinary original pixels precede labelled detail-layer and detail-and-SVG-Moon hidden controls (mask and composed native sky unchanged). Original canvas buffers and current physical/presentation state retained. No retuned opacity, H1/V5, geometry or clock; no continuity inference across unobserved intervals.'")
ast.parse(s);(O/'run_twilight_r131.py').write_text(s,encoding='utf-8',newline='\n')
print('Bounded twilight lunar discriminator prepared, not run')
