#!/usr/bin/env python3
"""R0013: real discovery, target records and contained complete Bash entry.

The failure mechanisms are false absence, dropped knowledge, suppressed peers,
delimiter-shifted records and effect dispatch of held/refused targets. Only
external effects are intercepted by the existing actual-entry fixture.
"""
import hashlib, importlib.util, json, os, pathlib, subprocess, sys, tempfile
from urllib.parse import unquote

SOURCE=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1]/'install.sh').resolve()
TEXT=SOURCE.read_text(encoding='utf-8')
DELIMITER="printf '\\nSalah Widget Installer\\n\\n'"
if TEXT.count(DELIMITER)!=1: raise RuntimeError('Installer helper/main boundary drift')
LIB=TEXT.split(DELIMITER)[0]
BASH=os.environ.get('SALAH_TEST_BASH','/bin/bash')
ROOT=pathlib.Path(tempfile.mkdtemp(prefix='salah-discovery-')).resolve()
os.chmod(ROOT,0o700)
(ROOT/'home').mkdir(mode=0o700); (ROOT/'tmp').mkdir(mode=0o700)
RESULTS=[]
SELECTED_CASES=set(json.loads(os.environ['SALAH_DISCOVERY_CASES'])) if os.environ.get('SALAH_DISCOVERY_CASES') else None
spec=importlib.util.spec_from_file_location('salah_entry_fixture',pathlib.Path(__file__).with_name('install-entry-bash.py'))
entry=importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)

def require(condition,message):
    if not condition: raise AssertionError(message)

def check(name,body):
    if SELECTED_CASES is not None and name not in SELECTED_CASES: return
    try: RESULTS.append(dict(case=name,pass_=True,observation=body()))
    except Exception as error: RESULTS.append(dict(case=name,pass_=False,error=str(error)))

def run(code,extra=None):
    env=dict(os.environ,HOME=str(ROOT/'home'),TMPDIR=str(ROOT/'tmp'),SALAH_INSTALL_SOURCE='github',DRY_RUN='0',NO_OPEN='0')
    env.pop('BASH_ENV',None); env.update(extra or {})
    return subprocess.run([BASH,'--noprofile','--norc','-c',LIB+'\n'+code],env=env,text=True,capture_output=True,timeout=15)

def profile(name,data):
    p=ROOT/name; p.mkdir(parents=True)
    if data=='directory': (p/'extensions.json').mkdir()
    elif isinstance(data,bytes): (p/'extensions.json').write_bytes(data)
    elif data is not None: (p/'extensions.json').write_text(data,encoding='utf-8')
    return p

def parser_case(name,data,want_status,want_reason,new='0',old='0',no_python=False):
    p=profile('parser-'+name,data)
    seam='command(){ if [ "$1" = -v ] && [ "${2:-}" = python3 ]; then return 1; fi; builtin command "$@"; }\n' if no_python else ''
    r=run(seam+'firefox_status "$PROFILE"\n',dict(PROFILE=str(p)))
    require(r.returncode==0,repr(dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)))
    rows=r.stdout.splitlines(); require(len(rows)==1,'Discovery emitted multiple records: '+repr(r.stdout))
    fields=rows[0].split('|')
    require(len(fields)==7,'Discovery knowledge/source fields absent or corrupted: '+repr(fields))
    require(fields[:2]==[new,old] and fields[3:5]==[want_status,want_reason],repr(fields))
    require(fields[6]==str(p/'extensions.json'),'Metadata source identity lost: '+repr(fields))
    require(fields[5]==('firefox-text-heuristic' if no_python else 'firefox-extensions-json'),'Wrong evidence class: '+repr(fields))
    if no_python: require('parser' in r.stderr.lower() or 'python' in r.stderr.lower(),'No parser-capability warning')
    if new=='1': require('TablissNG' in unquote(fields[2]),'New match lost')
    if old=='1': require('Tabliss' in unquote(fields[2]),'Legacy match lost')
    return dict(exit=r.returncode,status=fields[3],reason=fields[4],evidence=fields[5],source=fields[6],stderr=r.stderr)

def escaped_matches():
    name='TablissNG|line\n\r\x1b % مدينة'
    p=profile('escaped-matches',json.dumps({'addons':[{'name':name}]}))
    r=run('firefox_status "$PROFILE"\n',dict(PROFILE=str(p)))
    require(r.returncode==0 and len(r.stdout.splitlines())==1,repr(dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)))
    fields=r.stdout.rstrip('\n').split('|')
    require(len(fields)==7 and fields[3]=='known-new','Untrusted text shifted discovery fields: '+repr(fields))
    require(unquote(fields[2])==name,'Bounded match escaping lost original evidence')
    require('\x1b' not in r.stdout and '\r' not in r.stdout,'Control bytes escaped into terminal record')
    return dict(fields=len(fields),status=fields[3])

def target_rows(data_root,configs=None,extra=''):
    configs=configs or 'CONFIGS=("f|Firefox|firefox|$DATA|missing|| |store|manager|newtab")'
    code=configs+'\nfind_exe(){ return 1; }\n'+extra+'\ndetect_targets\nprintf "count=%s\\n" "$TARGET_COUNT"\nif [ "$TARGET_COUNT" -gt 0 ]; then printf "%s\\n" "${TARGETS[@]}"; fi\n'
    r=run(code,dict(DATA=str(data_root)))
    require(r.returncode==0,repr(dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)))
    lines=r.stdout.splitlines(); require(lines and lines[0].startswith('count='),repr(r.stdout))
    count=int(lines[0][6:]); rows=[line.split('|') for line in lines[1:]]
    require(count==len(rows),'Target cardinality inconsistent')
    for row in rows: require(len(row)==17,'Knowledge or target identity lost: '+repr(row))
    return rows,r

def builders():
    root=ROOT/'builder-firefox'; root.mkdir()
    for name,body in [('00-empty','{"addons":[]}'),('01-malformed','{"addons":['),('02-legacy','{"addons":[{"name":"Tabliss"}]}'),('03-new','{"addons":[{"name":"TablissNG"}]}'),('04-both','{"addons":[{"name":"TablissNG"},{"name":"Tabliss"}]}'),('05-shape','[]')]:
        p=root/name;p.mkdir();(p/'extensions.json').write_text(body)
    rows,r=target_rows(root)
    require([r[13] for r in rows]==['known-neither','unknown','known-legacy','known-new','known-both','unknown'],'Wrong builder knowledge: '+repr(rows))
    require([r[5] for r in rows]==[str(root/x) for x in ['00-empty','01-malformed','02-legacy','03-new','04-both','05-shape']],'Profile identity changed')
    require(all(row[16]==row[5]+'/extensions.json' and row[15]=='firefox-extensions-json' for row in rows),'Source identity not projected')
    return dict(count=len(rows),statuses=[r[13] for r in rows])

def detector_matrix(family):
    root=ROOT/('matrix-'+family); root.mkdir()
    cfg='CONFIGS=("b|Browser|'+family+'|$DATA|missing|new-id|old-id|store|manager|newtab")'
    rows,_=target_rows(root,configs=cfg)
    require(len(rows)==1 and rows[0][5]=='' and rows[0][13]=='unknown' and rows[0][14]=='no-profile','Empty installed browser was certified as an inventory')
    absent=ROOT/('absent-'+family); rows,_=target_rows(absent,configs=cfg); require(not rows,'Absent browser gained target')
    names=['Default','Profile One','Profile مدينة','Profile \\backslash'] if family=='chromium' else ['00.default','Profile One','مدينة','back\\slash']
    for index,name in enumerate(names):
        p=root/name;p.mkdir()
        if family=='firefox': (p/'extensions.json').write_text('{"addons":[]}')
        rows,_=target_rows(root,configs=cfg)
        require(len(rows)==index+1,'Wrong profile count: '+repr(rows))
        require({r[5] for r in rows}=={str(root/x) for x in names[:index+1]},'Profile path bytes changed')
        require(all(r[13]=='known-neither' for r in rows),'Supported empty profile not usable')
    rows,_=target_rows(root,configs=cfg+'; CONFIGS+=("z|Absent|'+family+'|$DATA/absent|missing|new-id|old-id|store|manager|newtab")')
    require(len(rows)==len(names),'Populated array leaked into next empty config')
    producer='firefox_profiles' if family=='firefox' else 'chromium_profiles'
    rows,_=target_rows(root,configs=cfg,extra=producer+'(){ printf "%s" "$DATA/'+names[0]+'"; }')
    require(len(rows)==1 and rows[0][5]==str(root/names[0]),'Unterminated last profile lost')
    return dict(family=family,cardinalities=[0,1,2,3,4],backslash=True,unterminated=True,reset=True)

def invalid_path():
    root=ROOT/'path-delimiter';root.mkdir();p=root/'Profile | injected';p.mkdir();(p/'extensions.json').write_text('{"addons":[]}')
    rows,r=target_rows(root)
    require(not rows and 'unsupported' in r.stderr.lower(),'Delimiter-corrupt profile was selectable: '+repr(rows))
    return dict(targets=0,diagnostic=r.stderr)

def newline_path(family):
    root=ROOT/('newline-'+family);root.mkdir()
    safe=root/('Profile safe' if family=='chromium' else 'safe');safe.mkdir()
    bad=root/(safe.name+'\n');bad.mkdir()
    if family=='firefox':
        (safe/'extensions.json').write_text('{"addons":[]}')
        (bad/'extensions.json').write_text('{"addons":[]}')
    configs='CONFIGS=("b|Browser|'+family+'|$DATA|missing|new-id|old-id|store|manager|newtab")'
    rows,r=target_rows(root,configs=configs)
    require(len(rows)==1 and rows[0][5]==str(safe),'Newline-containing identity became synthetic/duplicate targets: '+repr(rows))
    require('unsupported' in r.stderr.lower(),'Unsupported profile path was silently discarded')
    return dict(family=family,targets=len(rows),safePath=rows[0][5])

def whole_entry(name,bodies,selection='all',dry=False,eligible=0,held=0,refused=0,no_profile=False,no_python=False,chrome=False,selected_profile=None,selected_reason=None):
    root,subject,env=entry.fixture('r0013-'+name,profiles='none',dry=dry)
    if no_python: env['INSTALL_DISCOVERY_NO_PYTHON']='1'
    if chrome: (entry.browser_root(subject/'home','chrome')/'Default').mkdir(parents=True)
    profiles=entry.browser_root(subject/'home','firefox')
    if no_profile: profiles.mkdir(parents=True)
    for i,body in enumerate(bodies):
        p=profiles/('profile-'+str(i));p.mkdir(parents=True)
        if body=='directory': (p/'extensions.json').mkdir()
        elif body is not None: (p/'extensions.json').write_text(body,encoding='utf-8')
    before=entry.snapshot(subject); before_profiles=entry.snapshot(profiles) if profiles.exists() else []
    if dry:
        r=entry.run_plain(env);status=r.returncode;output=r.stdout+r.stderr;inputs={}
    else: status,output,inputs=entry.run_pty(env,selection)
    readiness=entry.require_ready(root,env,pipe=not dry)
    effects=entry.effect_lines(root)
    (root/'entry-output.txt').write_text(output)
    selected_identity=None
    if selected_profile is not None:
        selected_identity=next((line for line in output.splitlines() if line.startswith('['+selection+'] ')),None)
        require(selected_identity is not None and 'Firefox / profile-'+str(selected_profile)+' ' in selected_identity,'Explicit selection did not identify the intended fixture profile: '+repr(selected_identity))
        if selected_reason is not None:
            require('('+selected_reason+')' in selected_identity,'Explicit selection did not carry its intended metadata reason: '+repr(selected_identity))
    require((status==0)==(eligible>0),repr(dict(exit=status,effects=effects,output=output)))
    if dry or not eligible:
        require(not effects and before==entry.snapshot(subject),'Held/preview entry performed effects: '+repr(effects))
    else:
        require(any(x.startswith('download ') for x in effects),'Known target lost useful staging')
        require(sum(x=='open about:newtab' for x in effects)==eligible,'Wrong target reached actual manual handoff: '+repr(effects))
    require(before_profiles==(entry.snapshot(profiles) if profiles.exists() else []),'Browser profile mutated')
    require(str(held)+' held' in output and str(refused)+' refused' in output and str(eligible)+' eligible' in output,'Held/refused summary missing or false: '+output)
    if not eligible: require('Validated manual-install files retained' not in output,'No-eligible entry claimed staging')
    require('installation remains manual' in output or 'manual' in output.lower(),'Manual boundary missing')
    return dict(exit=status,effects=len(effects),eligible=eligible,held=held,refused=refused,snapshotUnchanged=before==entry.snapshot(subject),fixture=str(root),inputs=inputs,readiness=readiness,selectedIdentity=selected_identity)

EMPTY='{"addons":[]}'
OLD='{"addons":[{"name":"Tabliss"}]}'
NEW='{"addons":[{"name":"TablissNG"}]}'
BOTH='{"addons":[{"name":"TablissNG"},{"name":"Tabliss"}]}'
def retained_positive_control():
    for name,data,want in [('new',NEW,['1','0']),('legacy',OLD,['0','1']),('both',BOTH,['1','1'])]:
        p=profile('retained-'+name,data);r=run('firefox_status "$PROFILE"\n',dict(PROFILE=str(p)))
        require(r.returncode==0 and r.stdout.split('|')[:2]==want,'Known positive failed: '+repr(dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)))
    return dict(positives=3)
check('retained actual parser positives are useful',retained_positive_control)
check('healthy complete entry interception control',lambda:entry.terminal('r0013-healthy-entry-control'))
for name,data,status,reason,new,old in [
    ('empty',EMPTY,'known-neither','supported-metadata','0','0'),
    ('malformed','{"addons":[','unknown','metadata-malformed','0','0'),
    ('missing',None,'unknown','metadata-absent','0','0'),
    ('unreadable','directory','unknown','metadata-unreadable','0','0'),
    ('invalid-encoding',b'\xff{','unknown','metadata-encoding','0','0'),
    ('legacy',OLD,'known-legacy','supported-metadata','0','1'),
    ('new',NEW,'known-new','supported-metadata','1','0'),
    ('both',BOTH,'known-both','supported-metadata','1','1'),
]: check('actual parser '+name,lambda n=name,d=data,s=status,r=reason,a=new,b=old:parser_case(n,d,s,r,a,b))
for name,data in [('root-array','[]'),('root-null','null'),('missing-addons','{}'),('addons-object','{"addons":{}}'),('addons-null','{"addons":null}'),('addon-scalar','{"addons":[1]}'),('locale-scalar','{"addons":[{"defaultLocale":2}]}'),('name-object','{"addons":[{"name":{}}]}')]:
    check('unsupported shape '+name,lambda n=name,d=data:parser_case(n,d,'unknown','metadata-unsupported'))
for name,addon in [('empty-object',{}),('unrelated-keys',{'version':'1'}),('null-identities',{'id':None,'name':None,'defaultLocale':{'name':None}}),('empty-identities',{'id':'','name':'','defaultLocale':{'name':''}}),('whitespace-identities',{'id':'  ','name':'\t','defaultLocale':{'name':'\n'}})]:
    check('insufficient identity '+name,lambda n=name,a=addon:parser_case(n,json.dumps({'addons':[a]}),'unknown','metadata-unsupported'))
for name,addon in [('id-only',{'id':'ordinary@example.invalid'}),('name-only',{'name':'Ordinary extension'}),('locale-name-only',{'defaultLocale':{'name':'Ordinary extension'}})]:
    check('supported identity '+name,lambda n=name,a=addon:parser_case(n,json.dumps({'addons':[a]}),'known-neither','supported-metadata'))
check('partial metadata preserves conservative legacy hint',lambda:parser_case('partial-legacy',json.dumps({'addons':[{'name':'Tabliss'},{}]}),'unknown','metadata-unsupported','0','1'))
for name,data in [
    ('trailing-comma','{"addons":[],}'),('trailing-comment','{"addons":[]} /* comment */'),
    ('internal-comment','{/* comment */ "addons":[]}'),('single-quotes',"{'addons':[]}"),('bare-key','{addons:[]}'),
    ('duplicate-addons','{"addons":[{"name":"Tabliss"}],"addons":[]}'),
    ('duplicate-name','{"addons":[{"name":"Tabliss","name":"Ordinary extension"}]}'),
    ('escaped-duplicate-name','{"addons":[{"name":"Tabliss","na\\u006de":"Ordinary extension"}]}'),
    ('duplicate-locale-name','{"addons":[{"defaultLocale":{"name":"Tabliss","name":"Ordinary extension"}}]}'),
    ('non-json-NaN','{"addons":[],"other":NaN}'),('non-json-Infinity','{"addons":[],"other":Infinity}'),
    ('empty-document',''),('array-trailing-comma','{"addons":[],"other":[1,]}'),
    ('leading-zero','{"addons":[],"n":01}'),('leading-plus','{"addons":[],"n":+1}'),
    ('leading-dot','{"addons":[],"n":.1}'),('trailing-dot','{"addons":[],"n":1.}'),('missing-exponent','{"addons":[],"n":1e}'),
    ('missing-comma','{"addons":[],"other":{"a":1 "b":2}}'),('multiple-roots','{"addons":[]}{}'),
    ('invalid-string-escape',r'{"addons":[],"s":"\x31"}'),('short-unicode-escape',r'{"addons":[],"s":"\u12"}')
]: check('strict JSON '+name,lambda n=name,d=data:parser_case(n,d,'unknown','metadata-malformed'))
check('strict JSON complex valid control',lambda:parser_case('complex-valid',r'{"addons":[],"other":{"same":1,"array":[0,-1,1.5,1e+2,true,false,null,{},[]],"text":"quote\" slash\/ backslash\\ line\n unicode\u0645"},"another":{"same":2}}','known-neither','supported-metadata'))
for name,data,new,old in [('empty',EMPTY,'0','0'),('malformed','{"addons":[','0','0'),('new',NEW,'1','0'),('legacy',OLD,'0','1'),('both',BOTH,'1','1')]:
    check('no Python '+name,lambda n=name,d=data,a=new,b=old:parser_case('no-python-'+n,d,'unknown','parser-unavailable',a,b,True))
check('metadata delimiters retain one truthful record',escaped_matches)
check('actual target builder keeps states and source identity',builders)
for family in ('chromium','firefox'): check('complete native detector matrix '+family,lambda f=family:detector_matrix(f))
check('delimiter-corrupt profile cannot be selected',invalid_path)
for family in ('chromium','firefox'): check('newline profile cannot alias a safe target '+family,lambda f=family:newline_path(f))
check('actual all mixed selection keeps useful known peer',lambda:whole_entry('mixed-all',[EMPTY,'{"addons":[',OLD],eligible=1,held=1,refused=1))
check('actual explicit known target stays useful',lambda:whole_entry('explicit-known',[EMPTY,'{"addons":[',OLD],selection='1',eligible=1,selected_profile=0))
check('actual explicit unknown refuses before staging',lambda:whole_entry('explicit-unknown',[EMPTY,'{"addons":[',OLD],selection='2',held=1,selected_profile=1,selected_reason='metadata-malformed'))
check('actual unknown only refuses before staging',lambda:whole_entry('unknown-only',['{"addons":['],held=1))
check('actual known both refuses before staging',lambda:whole_entry('known-both',[BOTH],refused=1))
check('actual missing metadata is held',lambda:whole_entry('metadata-absent',[None],held=1))
check('actual no profile is held',lambda:whole_entry('no-profile',[],held=1,no_profile=True))
check('actual wrong shape preserves independent peer',lambda:whole_entry('wrong-shape-peer',[EMPTY,'[]'],eligible=1,held=1))
check('preview mixed keeps knowledge without effects',lambda:whole_entry('preview-mixed',[EMPTY,'{"addons":[',OLD],dry=True,eligible=1,held=1,refused=1))
check('preview unknown only has no success or effects',lambda:whole_entry('preview-unknown',['{"addons":['],dry=True,held=1))
check('no Python mixed preview keeps independent Chromium peer',lambda:whole_entry('no-python-peer',[EMPTY,NEW,BOTH],dry=True,eligible=1,held=2,refused=1,no_python=True,chrome=True))
check('actual existing new target remains useful with unknown peer',lambda:whole_entry('new-unknown-peer',[NEW,'[]'],eligible=1,held=1))
check('actual insufficient identity held with known peer',lambda:whole_entry('insufficient-peer',[EMPTY,'{"addons":[{}]}'],eligible=1,held=1))
check('actual duplicate keys cannot hide legacy from selection',lambda:whole_entry('duplicate-peer',[EMPTY,'{"addons":[{"name":"Tabliss"}],"addons":[]}'],eligible=1,held=1))
print(json.dumps(dict(host=subprocess.check_output([BASH,'--version'],text=True).splitlines()[0],platform=sys.platform,uid=os.getuid(),source=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),fixture=str(ROOT),results=RESULTS),ensure_ascii=False,indent=2))
sys.exit(1 if any(not row['pass_'] for row in RESULTS) else 0)
