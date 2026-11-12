"""Independent bounded rereview of concrete parser findings; no product writes."""
import hashlib,importlib.util,json,os,pathlib,subprocess,sys,tempfile
REPORT=pathlib.Path(__file__).resolve().parent
REPO=REPORT.parents[1]/'r0013'
PS=REPORT.parents[1]/'runtime/pwsh7/pwsh'
OWN=REPORT/'rereview-fixtures'; OWN.mkdir(exist_ok=True)
for n in ['home','tmp']: (OWN/n).mkdir(exist_ok=True)
env=dict(os.environ,HOME=str(OWN/'home'),TMPDIR=str(OWN/'tmp'))
for key in list(env):
 if key.lower()=='psmodulepath': del env[key]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
source_before={n:sha(REPO/n) for n in ['install.sh','install.ps1']}
assert source_before=={'install.sh':'609ecb0bb6924eccee5c311b77f0d513f0e78c3462c7fa5b15b1fd38694a5b22','install.ps1':'a67ac0c6190b3027a4ca31a1703df76b66558582e29b583bd15afe3da17bb7a4'}
results=[]
def ps_run(script,args,label):
 r=subprocess.run([str(PS),'-NoProfile','-File',str(REPORT/script)]+args,env=env,text=True,capture_output=True,timeout=40)
 (REPORT/(label+'.json')).write_text(r.stdout)
 (REPORT/(label+'.stderr.txt')).write_text(r.stderr)
 assert r.returncode==0,(label,r.returncode,r.stdout,r.stderr)
 return json.loads(r.stdout)
# Standard-library parser is the independent grammar oracle. Only ASCII folding
# is used in duplicate cases, matching the candidate's PS property-key policy.
def keys(pairs):
 result={}
 for k,v in pairs:
  norm=k.lower()
  if norm in result: raise ValueError('duplicate')
  result[norm]=v
 return result
def constant(v): raise ValueError(v)
def expected(text):
 try: json.loads(text,object_pairs_hook=keys,parse_constant=constant); return True
 except (ValueError,TypeError): return False
values=[None,True,False,0,-1,1.25,'', 'quote" backslash\\ slash/ newline\n Arabic م',[],{},[{},[],[1,2],{'a':True}],{'a':{'a':1},'b':{'a':2}}, {'addons':[]}, {'addons':[{'id':'other','name':'Ordinary','defaultLocale':{'name':'Localized'}}]}]
texts=[json.dumps(v,ensure_ascii=True,separators=(',',':')) for v in values]
texts += [' \t\n'+t+'\r ' for t in texts[-6:]]
texts += [r'{"same":1,"nested":{"same":2}}',r'{"a\u0062":1,"cd":2}',r'{"x":[0,-0,10,-10,0.1,1E2,1e+2,1e-2,true,false,null]}',r'{"\"":1,"\\":2,"\/":3,"\b":4,"\f":5,"\n":6,"\r":7,"\t":8}',r'{"addons":[],"other":[[[[{}]]]]}']
texts += ['', ' ', '{','[','}',']',':',',','tru','TRUE','nul','nullnull','0 0','{}[]','[1,]','[1,,2]','[,1]','[1 2]','[1}','{"a":1,}','{,"a":1}','{"a":}','{"a" 1}','{"a":1 "b":2}','{"a":1,,"b":2}','{"a":1]','{"a":{}}}','{"a":[]]','{"a":1}/*x*/','{/*x*/"a":1}',"{'a':1}",'{a:1}','{"a":+1}','{"a":01}','{"a":-01}','{"a":.1}','{"a":1.}','{"a":1e}','{"a":1e+}','{"a":--1}','{"a":NaN}','{"a":Infinity}',r'{"a":"\v"}',r'{"a":"\x01"}',r'{"a":"\u01"}',r'{"a":"\uZZZZ"}','{"a":"line\nbreak"}','\ufeff{}','\v{}','{"a":1,"a":2}',r'{"na\u006de":1,"name":2}','{"a":1,"A":2}',r'{"a\nb":1,"a\u000ab":2}',r'{"a\\b":1,"a\u005cb":2}',r'{"a\/b":1,"a/b":2}',r'{"a":{"x":1,"x":2}}']
corpus=[{'name':'grammar-'+str(i),'text':t,'expected':expected(t)} for i,t in enumerate(texts)]
(REPORT/'strict-grammar-corpus.json').write_text(json.dumps(corpus,indent=2)+'\n')
grammar=ps_run('strict-grammar-probe.ps1',['-SourceFile',str(REPO/'install.ps1'),'-Corpus',str(REPORT/'strict-grammar-corpus.json')],'strict-grammar-result')
assert all(r['pass'] for r in grammar['results']),[r for r in grammar['results'] if not r['pass']]
results.append({'case':'actual strict helper vs independent grammar corpus','pass':True,'count':len(corpus),'valid':sum(r['expected'] for r in corpus),'invalid':sum(not r['expected'] for r in corpus),'receipt':str(REPORT/'strict-grammar-result.json')})
parser=ps_run('parser-edge-probe.ps1',['-SourceFile',str(REPO/'install.ps1'),'-FixtureRoot',str(OWN/'ps-parsers')],'parser-edge-repaired')
for row in parser['results']:
 wanted='eligible-known' if row['case'] in ['healthy-empty','unsupported-version'] else 'unknown-held'
 assert row['eligible']==wanted,row
results.append({'case':'original PS actual-parser adverse cases repaired','pass':True,'count':len(parser['results']),'receipt':str(REPORT/'parser-edge-repaired.json')})
# Same exact actual main body used for the original independent RED evidence.
for name,payload in [('healthy-empty','{"addons":[]}'),('legacy-control','{"addons":[{"name":"Tabliss"}]}'),('malformed-unquoted','{addons:[]}'),('duplicate-inventory','{"addons":[{"name":"Tabliss"}],"addons":[]}')]:
 case=OWN/('ps-'+name); profile=case/'profiles/profile-0';profile.mkdir(parents=True)
 (profile/'extensions.json').write_text(payload);(case/'asset.xpi').write_bytes(b'fixture');(case/'preset.json').write_text('{}')
 r=subprocess.run([str(PS),'-NoProfile','-File',str(REPORT/'actual-main-probe.ps1'),'-SourceFile',str(REPO/'install.ps1'),'-Fixture',str(case)],env=env,text=True,capture_output=True,timeout=40)
 (case/'stdout.txt').write_text(r.stdout);(case/'stderr.txt').write_text(r.stderr)
 effects=(case/'effects.txt').read_text().splitlines() if (case/'effects.txt').exists() else []
 action=[e for e in effects if e!='prompt']
 ok=(r.returncode==0 and 'stage' in action and 'open:about:newtab' in action) if name=='healthy-empty' else (r.returncode!=0 and not action)
 assert ok,(name,r.returncode,effects,r.stderr)
 assert (profile/'extensions.json').read_text()==payload
 results.append({'case':'PS actual main '+name,'pass':ok,'exit':r.returncode,'effects':effects,'profileUnchanged':True,'fixture':str(case)})
# Bash uses the actual complete-file PTY harness. Trusted /tmp parent is required
# by the source; using /workspace's mode0777 ancestor is not a valid positive.
tempfile.tempdir='/tmp'
sys.argv=['review',str(REPO/'install.sh')]
spec=importlib.util.spec_from_file_location('rereview_entry',REPO/'tests/install-entry-bash.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
for name,payload in [('healthy-empty','{"addons":[]}'),('legacy-control','{"addons":[{"name":"Tabliss"}]}'),('duplicate-inventory','{"addons":[{"name":"Tabliss"}],"addons":[]}')]:
 root,subject,child=entry.fixture('independent-repaired-'+name,profiles='none',dry=False)
 profile=entry.browser_root(subject/'home','firefox')/'profile-0';profile.mkdir(parents=True);(profile/'extensions.json').write_text(payload)
 before=entry.snapshot(subject)
 code,output,inputs=entry.run_pty(child,'all');ready=entry.require_ready(root,child,pipe=True)
 effects=entry.effect_lines(root);(root/'entry-output.txt').write_text(output)
 ok=(code==0 and 'open about:newtab' in effects) if name=='healthy-empty' else (code!=0 and not effects and before==entry.snapshot(subject))
 assert ok,(name,code,effects,output)
 assert (profile/'extensions.json').read_text()==payload
 results.append({'case':'Bash actual full-file '+name,'pass':ok,'exit':code,'effects':effects,'profileUnchanged':True,'snapshotUnchanged':before==entry.snapshot(subject),'readiness':ready,'fixture':str(root)})
after={n:sha(REPO/n) for n in source_before};assert before is not None and after==source_before
report={'reviewer':'/root/r0013_review','scope':'bounded independent repair discrimination; Linux hosts only, not native Apple or Windows qualification','sourcesBefore':source_before,'sourcesAfter':after,'results':results}
(REPORT/'independent-rereview.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'results':len(results),'pass':all(r['pass'] for r in results),'grammarCases':len(corpus),'sourcesUnchanged':after==source_before}))
