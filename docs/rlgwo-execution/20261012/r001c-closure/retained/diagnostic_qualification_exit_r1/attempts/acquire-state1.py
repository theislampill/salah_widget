import sys, json, re, hashlib, pathlib, subprocess, datetime, shutil
sys.stdout.reconfigure(encoding='utf-8')
R=pathlib.Path(r'C:\Users\theis\Documents\Codex\salah-rlgwo-execution-20261009')
P=pathlib.Path(r'C:\Users\theis\Documents\Codex\celestial-startup-repair-20261008\planning-original-21e7a843\docs\rlgwo-execution\20261008')
C=pathlib.Path(r'C:\Users\theis\.codex\worktrees\pr43-review-revision\salah_widget')
O=R/'candidates/rlgwo-weather-info-01'
W=R/'workers/diagnostic_qualification_exit_r1'
REVIEWER='/root/diagnostic_qualification_exit'
assert W.is_dir() and not (W/'SEAL.json').exists()
verified={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def write(name,value):
 p=W/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def ref(p,expected=None,bytes_=None):
 p=pathlib.Path(p).resolve(); b=p.read_bytes(); h=sha(b)
 if expected: assert h==expected,(str(p),h,expected)
 if bytes_ is not None:assert len(b)==bytes_,(str(p),len(b),bytes_)
 v={'path':str(p),'bytes':len(b),'sha256':h}; verified[str(p)]=v; return v
def dependencies(v,base=None):
 if isinstance(v,dict):
  p=v.get('path') or v.get('file') or v.get('source')
  h=v.get('sha256') or v.get('rawResultSha256')
  if isinstance(p,str) and isinstance(h,str) and len(h)==64 and not p.startswith('http'):
   pp=pathlib.Path(p);pp=pp if pp.is_absolute() else ((base/pp) if base else None)
   if pp and pp.is_file():ref(pp,h,v.get('bytes'))
  for x in v.values():dependencies(x,base)
 elif isinstance(v,list):
  for x in v:dependencies(x,base)
def packet(root,expectedSeal=None):
 root=pathlib.Path(root); seal=ref(root/'SEAL.json',expectedSeal); man=ref(root/'MANIFEST.json'); sv=read(root/'SEAL.json');mv=read(root/'MANIFEST.json')
 assert sv.get('manifestSha256',sv.get('manifest',{}).get('sha256',man['sha256']))==man['sha256']
 files=mv['files'];rows=[]
 if isinstance(files,dict):
  for name,x in files.items():rows.append(ref(pathlib.Path(x.get('path',root/name)),x['sha256'],x.get('bytes')))
 else:
  for x in files:rows.append(ref(root/x['path'],x['sha256'],x.get('bytes')))
 return {'root':str(root),'seal':seal,'manifest':man,'membersVerified':len(rows)}
at=datetime.datetime.now(datetime.timezone.utc).isoformat()
assert sha((P/'CLOSURE_DAG.json').read_bytes())=='9ac372cfcce4df94ee0e678b907e66c131fe49f72cc55106143aa35dbdb0a6e7'
d=read(P/'CLOSURE_DAG.json');m=read(P/'metadata/R001C.json');a=read(R/'ACTIVE_LEDGER.json')
node=next(x for x in d['nodes'] if x['id']=='R001C-QUALIFY'); active=next(x for x in a['nodes'] if x['id']=='R001C-QUALIFY');preds=[x for x in a['nodes'] if x['id'] in ['R001C-DOCS','R001C-FORCE-FIXTURE','R001C-BROWSER','R001C-RENDER']]
assert len(preds)==4 and all(x['executionStatus']=='COMPLETE_EXIT_VERIFIED' for x in preds)
assert active['executionStatus']=='EXECUTING',active['executionStatus']
write('ORIGINAL_NODE.json',node);write('ACTIVE_NODE.acquired.json',active);write('PREDECESSORS.acquired.json',preds)
write('R001C_OBLIGATIONS.json',{'accepted':m['acceptedObligations'],'remaining':[{'id':o['id'],'parentText':o['parentText'],'acceptance':o['acceptance'],'children':[{'id':c['id'],'scope':c['scope']} for c in o.get('subObligations',[])]} for o in m['remainingObligations']],'documentationFacts':m['documentationFacts'],'reuseRules':m['reuseRules'],'closure':m['closure'],'nonGoals':m['nonGoals']})
for name,expected in [('AGENTS.md','f506acbba2b5b2ade773c251342b41523b6e94cd740ee51a38ba15316714b948'),('DESIGN.md','f517f7174f5f3214265ace51c74713f57e392bb22312c1c32658b3f0d8b0f16a'),('OPTICS.md','8abd464e3d6115c554b0b4b5af719fe56b7ff87bf0acd08392a60d2ac8e4c669'),('src/native/index.html','cbd5e37608dcb502b0824ea5c145cc9ba242d1970e512cd4f9572be414cd818b'),('index.html','c773af444ed1071f9ba6b62b8e635c8d38b1b7f73de995c781ed23c0d307499a'),('tests/rlgwo-docs-contract.cjs','8a3e35852b3647112addfe4254ed2d0149427cb1c8456503d780bb583c17905a'),('src/native/builder.html','66f1cd86cfb3d1e53b75c8840057564ccfa514a46cf1f13b6863673b0d83279e'),('config.js','91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81')]:
 ref(C/name,expected);q=W/'inputs/current'/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(C/name,q)
for name,expected in [('src/native/index.html','ec59b3ff64e06713d652af5b30f04a18fcde404b92b4595bc1cee96818a6ec65'),('index.html','14e1d92101dad56f1352a2b4a85a460067361ecdfca62093f9f9d1286b991fad')]:
 ref(O/name,expected);q=W/'inputs/historical-browser'/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/name,q)
cmds=[]
for name,args in [('head',['git','-C',str(C),'rev-parse','HEAD']),('branch',['git','-C',str(C),'branch','--show-current']),('origin',['git','-C',str(C),'remote','get-url','origin']),('dirty',['git','-C',str(C),'status','--short'])]:
 z=subprocess.run(args,capture_output=True,check=False);assert z.returncode==0;write('git/'+name+'.json',{'argv':args,'exitCode':z.returncode,'stdout':z.stdout.decode('utf-8'),'stderr':z.stderr.decode('utf-8')});cmds.append({'name':name,'argv':args,'exitCode':z.returncode,'stdoutSha256':sha(z.stdout)})
assert read(W/'git/head.json')['stdout'].strip()=='50e46b7ecfde9c8bea9c0cf00b6017afaf27aab9'
packets=[]
for p,h in [('workers/diagnostic_release_exit_r1','8ca35cb543a75cb1dd9864f0650486e25c3538c8d3dd0db17ca15e635e604ec2'),('workers/diagnostic_a10_final_adopted_r1','5173787b5f0cb5c7d9b0b30059defa503efb5a3c95bf91f2414730501b7bbb78'),('workers/diagnostic_a10_final_consumer_r1','c3744624abd6b96d404c9691439261551f05f281669f79f31c5be50f51e2da7b'),('workers/final_force_fixture_binding_review_r1','7169cce0f2e191636480218f2a3fbb99e162454818bfd8fddf4c744385cdd66d')]:packets.append(packet(R/p,h))
canon={}
for p,h in [('integration/r001c-release-exit-join-r1/receipt.json','c5612f2bb2732f6ba7ca89d1217bd79f2cabf19c259f9db27be8042d9106378a'),('execution/R001C/release-review.json','b2d402855c0617669b06fba034cef5a104f89c565d45682f12ff8ee2546b81f6'),('evidence/R001C/rendered/results.json','84f522e004ace04b8db01a15c6918d56698ad153b3816f1bbd66455840eb867a'),('integration/r001c-render-exit-join-r1/receipt.json','269dd7aaeb57f0b666ecee86bcd0f2a9562db52965072e869c03cb7b31d0fb00'),('evidence/R001C/browser/results.json','2b68c079984551a39f5e3db9c363d57f17ce01a8423a0ca0f68c0f4921fe9f9d'),('evidence/R001C/browser/debug-motion.json','4a0d10415d7f90d835ab422484f4cd4d5b4e46a6053599398321adecdca6f4ab'),('evidence/R001C/browser/reduced-motion.json','df8cf5f7a3939dc7ebf8ebc63aa268449f92b4ef365b0060b5957a4067023ee5'),('integration/reviewed-test-joins-r1/receipt.json','4c4f0ef47dd43de3ea4166968d0b782b5c2eb2d157bc8c2ad51a62638784bb4e'),('integration/reviewed-test-joins-r1/force-current-scope.stdout','6cf400b349b0bfaf9c2b412df529bf3915672828e2adf691837c2d014819f546')]:canon[p]=ref(R/p,h)
canon['evidence/R001C/browser/node-exit-join-r2/receipt.json']=ref(R/'evidence/R001C/browser/node-exit-join-r2/receipt.json')
reuse=read(R/'workers/diagnostic_release_exit_r1/REUSE_READBACK.json')
for x in reuse['exactReferencesVerified']:ref(x['path'],x['sha256'],x.get('bytes'))
for p in ['evidence/R001C/rendered/results.json','workers/diagnostic_release_exit_r1/REUSE_READBACK.json','workers/diagnostic_release_exit_r1/ADVERSE_AND_BOUNDARY_REVIEW.json','workers/diagnostic_a10_final_adopted_r1/FINAL_ROW_MAP.json','workers/diagnostic_a10_final_adopted_r1/FINAL_A10_CERTIFICATE.json']:
 dependencies(read(R/p),R/pathlib.Path(p).parent)
write('INPUT_PACKET_READBACK.json',{'atUtc':at,'packets':packets,'canonical':canon,'referencesVerified':list(verified.values()),'commands':cmds,'nativeBrowserBuildVmExecuted':False,'canonicalWritten':False})
write('COLD_ADMISSION.json',{'schema':'r001c-qualification-cold-admission/1','atUtc':at,'node':node['id'],'reviewer':REVIEWER,'authority':'Parent /root exact dispatch and actual assignment reconciliation at 2026-10-09T22:47:37UTC; original F-E cold-read readiness preserved. This authorises only private independent read-only reconciliation.','objective':node['scope'],'literalEntryCriteria':node['entryCriteria'],'literalExitCriteria':node['exitCriteria'],'predecessors':[{'id':x['id'],'executionStatus':x['executionStatus']} for x in preds],'entryDisposition':'ADMITTED_FOR_PRIVATE_READ_ONLY_RECONCILIATION','differentFromAuthorsAndIntegrator':True,'rootSoleCanonicalIntegrator':True,'resource':'independent-read-only-review; no heavy-browser lease acquired or changed','independentOfInstallerApplePlatform':True,'doneWhen':'Return exact proposed own outputs or precise missing input; verify and seal private members; stop without self-awarded node credit.','rollback':'Private additive packet only. Root may decline it; no shared effect needs compensation.','assumptions':['Accepted source/browser/render runs are consumed without replay.','A11/public delivery and issue closure are downstream; M0/actual parent/optical physics remain separate bounded limits.'],'nodeCredit':0,'parentIssueCredit':0,'externalEffects':[]})
print(json.dumps({'acquired':True,'privateRoot':str(W),'verifiedReferences':len(verified),'packets':len(packets),'head':read(W/'git/head.json')['stdout'].strip(),'ownState':active['executionStatus'],'predecessorsComplete':len(preds)}))
