import hashlib,importlib.util,json,os,pathlib,subprocess,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parent
PRODUCT=ROOT.parents[1]/'r0013'
PS=ROOT.parents[1]/'runtime/pwsh7/pwsh'
TMP=ROOT/'probe-effects'; TMP.mkdir(exist_ok=True)
tempfile.tempdir=str(TMP)
env=dict(os.environ,HOME=str(ROOT/'pwsh-probe-home'),TMPDIR=str(ROOT/'pwsh-probe-tmp'))
for key in list(env):
 if key.lower()=='psmodulepath': del env[key]
report={'reviewer':'/root/r0013_review','scope':'actual-source parser, eligibility, and contained main consumers; PowerShell7/Linux is supplemental','results':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(PRODUCT/'install.ps1')
r=subprocess.run([str(PS),'-NoProfile','-File',str(ROOT/'parser-edge-probe.ps1'),'-SourceFile',str(PRODUCT/'install.ps1'),'-FixtureRoot',str(TMP/'ps-parsers')],env=env,text=True,capture_output=True,timeout=30)
(ROOT/'parser-edge-result.json').write_text(r.stdout)
(ROOT/'parser-edge-stderr.txt').write_text(r.stderr)
report['ps_parser_source_before']=before;report['ps_parser_source_after']=sha(PRODUCT/'install.ps1')
report['ps_parser_exit']=r.returncode
for name,payload in [('healthy-empty','{"addons":[]}'),('legacy-control','{"addons":[{"name":"Tabliss"}]}'),('malformed-unquoted','{addons:[]}'),('duplicate-inventory','{"addons":[{"name":"Tabliss"}],"addons":[]}')]:
 case=TMP/('ps-'+name);profile=case/'profiles/profile-0';profile.mkdir(parents=True)
 (profile/'extensions.json').write_text(payload);(case/'asset.xpi').write_bytes(b'contained fixture');(case/'preset.json').write_text('{}')
 source_before=sha(PRODUCT/'install.ps1')
 result=subprocess.run([str(PS),'-NoProfile','-File',str(ROOT/'actual-main-probe.ps1'),'-SourceFile',str(PRODUCT/'install.ps1'),'-Fixture',str(case)],env=env,text=True,capture_output=True,timeout=30)
 (case/'stdout.txt').write_text(result.stdout);(case/'stderr.txt').write_text(result.stderr)
 effects=(case/'effects.txt').read_text().splitlines() if (case/'effects.txt').exists() else []
 report['results'].append({'platform':'PowerShell7/Linux','case':name,'input':payload,'source_before':source_before,'source_after':sha(PRODUCT/'install.ps1'),'exit':result.returncode,'effects':effects,'stdout':str(case/'stdout.txt'),'stderr':str(case/'stderr.txt'),'profile_unchanged':(profile/'extensions.json').read_text()==payload})
sys.argv=['review-probe',str(PRODUCT/'install.sh')]
spec=importlib.util.spec_from_file_location('owned_entry_probe',PRODUCT/'tests/install-entry-bash.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
for name,payload in [('healthy-empty','{"addons":[]}'),('legacy-control','{"addons":[{"name":"Tabliss"}]}'),('duplicate-inventory','{"addons":[{"name":"Tabliss"}],"addons":[]}')]:
 case,subject,childenv=entry.fixture('bash-'+name,profiles='none',dry=False)
 profile=entry.browser_root(subject/'home','firefox')/'profile-0';profile.mkdir(parents=True);(profile/'extensions.json').write_text(payload)
 source_before=sha(PRODUCT/'install.sh')
 result,output,inputs=entry.run_pty(childenv,'all')
 (case/'stdout.txt').write_text(output)
 report['results'].append({'platform':'Bash/Linux','case':name,'input':payload,'source_before':source_before,'source_after':sha(PRODUCT/'install.sh'),'exit':result,'effects':entry.effect_lines(case),'output':str(case/'stdout.txt'),'inputs':inputs,'profile_unchanged':(profile/'extensions.json').read_text()==payload})
(ROOT/'additional-probes.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
