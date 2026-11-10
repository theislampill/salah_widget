from pathlib import Path
import datetime,hashlib,json,re,subprocess

root=Path('/workspace/scratch/15b8fb6ac4c2/r000b-work')
review=Path('/workspace/scratch/d9a9ea2be931/recovery')
preserved=Path('/tmp/r000b-successor-build-preserved')
commit='d124f050ec68fa8608022b1ed5fead426d42dcb9'
old_prefix='docs/state-contracts/evidence/R000B/20261110-native-preparation/evidence/native-manifests-v2/'
def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def file_hash(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()
def identity(path):return {'bytes':path.stat().st_size,'sha256':file_hash(path)}
def git_blob(path):
    size=path.stat().st_size;digest=hashlib.sha1(f'blob {size}\0'.encode())
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()
def check(value,message):
    if not value:raise AssertionError(message)
manifest_path=review/'r000b-native-candidate-f02.json'
inventory_path=review/'r000b-native-candidate-f02-runtime-inventory.json'
expected=json.loads(manifest_path.read_text());inventory=json.loads(inventory_path.read_text())
old_manifest_bytes=git('show',f'{commit}:docs/state-contracts/r000b-native-candidate.json')
old_manifest=json.loads(old_manifest_bytes)
old_archive_manifest_bytes=git('show',commit+':'+old_prefix+'r000b-native-candidate.json')
old_inventory_bytes=git('show',commit+':'+old_prefix+'r000b-native-candidate-runtime-inventory.json')
old_inventory=json.loads(old_inventory_bytes)
check(old_manifest_bytes==old_archive_manifest_bytes,'committed current and archived-v2 manifests disagree')
paths=[root/n for n in ['index.html','offline.html','config.js','builder.html']]
paths.extend(p for p in (root/'real-sky').rglob('*') if p.is_file())
paths.extend(p for p in (root/'moon').rglob('*') if p.is_file() and p.relative_to(root/'moon').parts[0] not in {'src','tests'})
check(len(paths)==len(set(paths)),'duplicate runtime inventory path')
actual_files={p.relative_to(root).as_posix():identity(p) for p in sorted(paths)}
canonical=''.join(f"{v['sha256']}  {p}\n" for p,v in sorted(actual_files.items()))
actual_tree=sha_bytes(canonical.encode())
check(len(actual_files)==142,'runtime inventory count drift')
check(actual_files==inventory['files'],'fresh runtime file inventory differs')
check(actual_tree==inventory['treeSha256']==expected['runtimeTreeSha256'],'runtime tree digest differs')
check(set(actual_files)==set(old_inventory['files']),'runtime path set changed')
changed_runtime={p:{'old':old_inventory['files'][p],'new':v} for p,v in actual_files.items() if v!=old_inventory['files'][p]}
check(set(changed_runtime)=={'index.html','offline.html','moon/BUILD.json'},'unexpected runtime leaf changed')

source_checks={};fixture_checks={}
for section,target in [('authoredSources',source_checks),('fixtureSources',fixture_checks)]:
    for path,record in expected[section].items():
        actual=identity(root/path);check(actual==record,'manifest input mismatch: '+path)
        target[path]={'actual':actual,'changed_from_old':record!=old_manifest[section][path]}
check([p for p,v in source_checks.items() if v['changed_from_old']]==['src/native/index.html'],'unexpected authored rebind')
check(not any(v['changed_from_old'] for v in fixture_checks.values()),'fixture/helper changed in rebind')
check(source_checks['src/native/index.html']['actual']['sha256']=='fe0ec24a6f26839ec6439c172a3b098bebd03388b3f7b0385cead0febecf4327','not reviewed F02 source')
check(file_hash(root/'tests/weather-no-timetable-handoff.test.cjs')=='f1669a82fa40691e0179372b282a41a9e369147887cec8f89c6f88ad58b23110','F02 tests drifted')

index=(root/'index.html').read_bytes();html=index.decode()
scripts=[{'index':i,'attributes':m[1],'sha256':sha_bytes(m[2].encode()),'characters':len(m[2].encode('utf-16-le'))//2}
         for i,m in enumerate(re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script>',html,re.I))]
check(scripts==expected['scriptBodies'],'script body manifest mismatch')
check(sha_bytes(index)==expected['indexSha256'],'index manifest mismatch')
changed_scripts=[{'index':i,'old':old,'new':new} for i,(old,new) in enumerate(zip(old_manifest['scriptBodies'],scripts)) if old!=new]
check(len(scripts)==6 and [x['index'] for x in changed_scripts]==[3],'unexpected generated script changes')

outputs=json.loads((review/'build-successor/outputs.json').read_text())
copy_receipt=json.loads((review/'generated-copy-preflight.json').read_text())
preservation=json.loads((preserved/'preservation.json').read_text())
check(copy_receipt['expectedHead']==commit,'copy expected HEAD mismatch')
check(copy_receipt['sourceSha256']==source_checks['src/native/index.html']['actual']['sha256'],'copy source mismatch')
check(copy_receipt['outputs']==outputs,'copy/build output receipts differ')
copied={}
for path,record in outputs.items():
    actual={**identity(root/path),'gitBlob':git_blob(root/path)}
    check(actual==record,'current output differs from build receipt: '+path)
    old=git('show',commit+':'+path)
    check(sha_bytes(old)==copy_receipt['preimages'][path],'copy preimage mismatch: '+path)
    has_preserved=(preserved/path).is_file()
    if has_preserved:
        check(identity(preserved/path)==identity(root/path),'preserved output differs: '+path)
    copied[path]={'actual':actual,'preserved_copy_matches':has_preserved,'old_sha256':sha_bytes(old),'changed':sha_bytes(old)!=actual['sha256']}
for path,digest in preservation['files'].items():
    check(file_hash(preserved/path)==digest==file_hash(root/path),'dirty build preservation mismatch: '+path)
check(set(preservation['files'])=={'src/native/index.html','index.html','offline.html','moon/BUILD.json'},'preserved dirty file set differs')
check(preservation['head']==commit,'preservation HEAD mismatch')

old_source=git('show',commit+':src/native/index.html')
new_source=(root/'src/native/index.html').read_bytes()
start=b'function cloudAuthorityMatches('
end=b'function rememberWeatherEffects('
def block(source):
    check(source.count(start)==1 and source.count(end)==1,'ambiguous F02 block')
    return source[source.index(start):source.index(end,source.index(start))]
old_block,new_block=block(old_source),block(new_source)
check(new_source.replace(new_block,old_block,1)==old_source,'source changes outside frozen F02 block')
parity={}
for path in ['index.html','offline.html']:
    current=(root/path).read_bytes();old=git('show',commit+':'+path)
    check(current.count(new_block)==1 and old.count(old_block)==1,'generated F02 owner ambiguous: '+path)
    check(current.replace(new_block,old_block,1)==old,'generated bytes changed outside exact F02 source block: '+path)
    parity[path]={'new_block_occurrences':1,'all_other_bytes_equal_committed_preimage':True}
old_moon=json.loads(git('show',commit+':moon/BUILD.json'));new_moon=json.loads((root/'moon/BUILD.json').read_text())
old_moon['source']['src/native/index.html']=sha_bytes(new_source)
check(old_moon==new_moon,'moon BUILD changed beyond authored-source hash')

commands=json.loads((review/'build-successor/commands.json').read_text());command_checks=[]
for row in commands:
    log=review/'build-successor'/(row['name']+'.log')
    check(file_hash(log)==row['log_sha256'],'build log digest mismatch: '+row['name'])
    check(row['exit']==0,'build command nonzero: '+row['name'])
    command_checks.append({**row,'verified_log_bytes':log.stat().st_size})
protected=subprocess.run(['git','-C',str(root),'diff','--exit-code',commit,'--','v1','vendor','real-sky/native-sky.js','tools/build_native.py','tools/build_moon.py'],capture_output=True)
check(protected.returncode==0,'protected/builder/native bundle differs from committed preimage')
untracked=git('ls-files','--others','--exclude-standard','--','v1','vendor').decode()
check(not untracked,'untracked protected files present')

results=json.loads((review/'generated-cohorts/results.json').read_text());cohort_checks=[]
for row in results:
    log=review/'generated-cohorts'/row['log'];data=log.read_bytes();text=data.decode()
    check(sha_bytes(data)==row['log_sha256'],'cohort log digest mismatch: '+row['path'])
    check(row['exit']==0,'cohort nonzero: '+row['path'])
    counts=row['counts']
    if counts:
        observed={name:int(re.search(r'^# '+name+r' (\d+)$',text,re.M)[1]) for name in ['tests','pass','fail','skipped','todo']}
        check(observed==counts,'cohort TAP summary mismatch: '+row['path'])
    else:
        if text.lstrip().startswith('{'):
            full=json.loads(text)
            check(full.get('allPassed') is True,'whole case receipt is not all passed: '+row['path'])
            check(full.get('cases') and all(case.get('passed') is True for case in full['cases']),'named case failure: '+row['path'])
            observed={'format':'named-case-json','pass':len(full['cases']),'fail':0,'cases':[case['case'] for case in full['cases']]}
        else:
            observations=[json.loads(line) for line in text.splitlines() if line.startswith('{')]
            observed=observations[-1] if observations else None
            check(observed is not None,'case receipt absent: '+row['path'])
            check(observed.get('fail')==0,'case receipt failures: '+row['path'])
    cohort_checks.append({'path':row['path'],'log_sha256':row['log_sha256'],'exit':row['exit'],'summary':observed,
                          'printed_generated_source_digest':expected['indexSha256'] in text})

status=git('status','--short').decode();head=git('rev-parse','HEAD').decode().strip();tree=git('rev-parse','HEAD^{tree}').decode().strip()
check(head==commit,'HEAD changed during review')
result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':head,'tree':tree,'status':status,
        'expected_manifest_sha256':file_hash(manifest_path),'expected_inventory_sha256':file_hash(inventory_path),
        'old_committed_manifest_sha256':sha_bytes(old_manifest_bytes),'old_committed_archived_manifest_sha256':sha_bytes(old_archive_manifest_bytes),
        'old_committed_inventory_sha256':sha_bytes(old_inventory_bytes),'old_runtime_tree':old_inventory['treeSha256'],'runtime_tree':actual_tree,
        'runtime_files':len(actual_files),'changed_runtime':changed_runtime,'source_checks':source_checks,'fixture_checks':fixture_checks,
        'script_count':len(scripts),'changed_scripts':changed_scripts,'output_checks':copied,'canonical_commands':command_checks,
        'preserved_dirty_build_files':preservation,'exact_source_propagation':parity,'moon_build_only_source_digest_changed':True,
        'protected_check':{'exit':protected.returncode,'stdout':protected.stdout.decode(),'stderr':protected.stderr.decode(),'untracked':untracked},
        'cohort_receipt_checks':cohort_checks,'old_manifest_matches_new_runtime':old_manifest['runtimeTreeSha256']==actual_tree,
        'limits':'Read-only identity/receipt inspection. No rebuild, broad test replay, browser, native pixels, delivery or whole-contract acceptance.'}
(review/'source-f02-output-identities.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['source_checks','fixture_checks','cohort_receipt_checks','preserved_dirty_build_files']},indent=2))
