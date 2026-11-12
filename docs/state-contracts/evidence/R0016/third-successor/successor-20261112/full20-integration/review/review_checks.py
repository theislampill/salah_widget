"""Focused immutable packet checks and inert receipt edge probes. No native imports."""
import ast, collections, hashlib, json, math, pathlib, re, stat, tempfile
HERE=pathlib.Path(__file__).resolve().parent
PACKET=HERE.parent/'full20_integration'
results=[]
def check(name,condition):
    assert condition,name
    results.append(dict(check=name,pass_=True))
def require(value,reason):
    if not value: raise ValueError(reason)
def sha(raw): return hashlib.sha256(raw).hexdigest()
manifest_raw=(PACKET/'MANIFEST.json').read_bytes()
check('exact assigned manifest',sha(manifest_raw)=='dfa649b4f98cd43dae72aed81729a59919bbaa15480973208ce38c3e4b6578b4')
manifest=json.loads(manifest_raw)
for item in manifest['files']:
    raw=(PACKET/item['path']).read_bytes()
    check('packet file '+item['path'],len(raw)==item['bytes'] and sha(raw)==item['sha256'])
roles=('tests/install-entry-native-composition.py','tools/qualification/installer_preview_windows_full_entry.py')
trees={}
for role,allowed in zip(roles,({'_case_impl'},{'validate_case_headers','validate_report'})):
    old=ast.parse((PACKET/'baseline'/role).read_bytes());new=ast.parse((PACKET/'candidate'/role).read_bytes())
    trees[role]=new
    functions=lambda t:{n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
    a,b=functions(old),functions(new)
    check('all original functions retained '+role,set(a)<=set(b))
    for name,node in a.items():
        if name not in allowed: check('unchanged comparator/helper '+name,ast.dump(node)==ast.dump(b[name]))
    requires=lambda t:collections.Counter(ast.dump(n) for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require')
    check('all original require calls retained '+role,not(requires(old)-requires(new)))

# Only inert definitions and literal JSON_LIMIT are loaded. The native harness is never imported.
outer=trees[roles[1]]
names={'checked_path','file_fact','verify_fact','parse_json','read_json_array','bind_preparation_receipt','selected_pure_receiver'}
ns=dict(require=require,Path=pathlib.Path,stat=stat,json=json,hashlib=hashlib,re=re,ast=ast,math=math,JSON_LIMIT=64*1024*1024,Rejected=ValueError)
exec(compile(ast.Module(body=[n for n in outer.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'candidate-outer-inert','exec'),ns)
with tempfile.TemporaryDirectory(dir=HERE,prefix='probe-') as tmp:
    case=pathlib.Path(tmp);capture=case/'entry-profile-window';capture.mkdir()
    receipt=dict(environment=dict(INSTALL_READY_NONCE='a'*32),nonce='a'*32,pid=1234,ready=False,before=[],after=[])
    for stream in ('stdout','stderr'):
        path=capture/(stream+'.raw');path.write_bytes(b'');receipt[stream]=ns['file_fact'](path,case)
    for field,filename in (('before','profile-before-launch.json'),('after','profile-after-exit.json')):
        (capture/filename).write_text('[]')
    facts=[]
    check('early refusal binds raw streams and before/after without invented ready or ACK',ns['bind_preparation_receipt'](receipt,case,capture,facts)=='a'*32 and len(facts)==4)
    startup=case/'host-only-control';startup.mkdir()
    try:ns['bind_preparation_receipt'](receipt,case,startup,[])
    except ValueError as error:check('source-free baseline cannot use early refusal exception',str(error)=='Source-free preparation readiness is missing')
    else:raise AssertionError('source-free missing ready accepted')
    (capture/'profile-before-launch.json').write_text('[{"key":1,"key":2}]')
    try:ns['bind_preparation_receipt'](receipt,case,capture,[])
    except ValueError as error:check('duplicate members in original raw profile rejected',str(error)=='Duplicate JSON member')
    else:raise AssertionError('duplicate profile accepted')

# Use the production outer loader and its incrementally populated binding dictionary,
# rather than the author's one-namespace test helper, to resolve the added pure functions.
harness=PACKET/'candidate'/roles[0]
bindings=dict(SCENARIOS=('positive','no-open','github'),hashlib=hashlib,json=json,re=re,composition=object())
loaded={}
for name in ('digest','warm_control_body','receive_cache_bytes','parse_warm_context','receive_warm_context','require_scoped_preparation_environment','require_normal_preparation'):
    loaded[name]=ns['selected_pure_receiver'](harness,name,sha(harness.read_bytes()),bindings)
    bindings[name]=loaded[name]
check('production selected-function loader resolves helper chain',loaded['receive_cache_bytes'](b'abc',[dict(role='analysisCache',path='.',kind='file',bytes=3,sha256=sha(b'abc'))])['bytes']==3)
for case_name in ('c10','c11'):
    fixture=PACKET/'fixtures/native-43216080799'
    report=json.loads((fixture/'entry-composition-report.json').read_bytes())
    scenario='positive' if case_name=='c10' else 'no-open'
    observation=next(row['observation'] for row in report['results'] if row['case']==scenario)
    raw=(fixture/case_name/'host-only-control/stdout.raw').read_bytes()
    journal=json.loads((fixture/case_name/'warm-json-assembly-binding.json').read_bytes())
    context=loaded['receive_warm_context'](raw,observation['hostOnlyBaseline'],journal['comparisons'][0])
    check('production loader accepts original runtime-expanded PSModulePath '+case_name,context['moduleSearchPath']!=observation['hostOnlyBaseline']['environment']['PSModulePath'])
out=dict(status='PASS',checkCount=len(results),checks=results,nativeExecuted=False,nativeHarnessImported=False,writeScope=str(HERE))
(HERE/'checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(status='PASS',checkCount=len(results))))
