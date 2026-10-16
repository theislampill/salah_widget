from pathlib import Path
import ast,datetime,hashlib,json
O=Path(__file__).resolve().parent;A=O/'solar-probe-tools-r1';B=O/'solar-probe-tools-r2';assert not B.exists()
inputs={};sha=lambda b:hashlib.sha256(b).hexdigest()
for p in A.rglob('*'):
 if p.is_file() and p.suffix in ['.py','.js']:
  rel=p.relative_to(A);b=p.read_bytes();out=B/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b);inputs[str(rel)]=sha(b)
p=B/'tools/cp9/celestial_startup_check.py';s=p.read_text()
anchor=" if a.scene=='dawn':stamp='2026-09-25T10:40:00Z'"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n if a.solar_stamp:datetime.fromisoformat(a.solar_stamp.replace('Z','+00:00'));stamp=a.solar_stamp\n if a.solar_cloud is not None:cloud=a.solar_cloud;wx=0 if cloud==0 else 2")
s=s.replace("'weatherOverride':'day scene uses fixed code2/35percent low cloud'","'weatherOverride':{'code':wx,'lowCloudPercent':cloud,'clockAnchor':stamp}")
anchor=' asyncio.run(run(p.parse_args()))'
assert s.count(anchor)==1
s=s.replace(anchor," p.add_argument('--solar-stamp');p.add_argument('--solar-cloud',type=int,choices=[0,35])\n"+anchor)
ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')
wrapper=(O/'run_solar_probe.py').read_text().replace("R = O / 'solar-probe-tools-r1'","R = O / 'solar-probe-tools-r2'")
ast.parse(wrapper);(O/'run_solar_probe_r2.py').write_text(wrapper,encoding='utf-8',newline='\n')
record={'atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputPins':inputs,'harnessSha256':sha(p.read_bytes()),'wrapperSha256':sha((O/'run_solar_probe_r2.py').read_bytes()),'change':'Add explicit anchored sunrise/forenoon and clear/35percent cloud fixtures only; preserve first30s ordinary and15s diagnostic observation. No app CSS/runtime mutation.',
 'boundedCases':['Chromium r3 vs r4 sunrise clear,10s prayer hold','Firefox r4 sunrise clear,10s prayer hold','Firefox r4 forenoon35percent cloud'],
 'scope':'Native source-regression and owner Sun-strobe discriminator; no automatic retries, S1 or cost claim.'}
(B/'PREPARATION.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
