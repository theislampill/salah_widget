#!/usr/bin/env python3
"""Source-bound Linux/Bash probes. All writes belong to a new disposable fixture."""
import hashlib, json, os, pathlib, re, subprocess, sys, tempfile, zipfile, stat

SOURCE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[1] / 'install.sh')
TEXT = SOURCE.read_text(encoding='utf-8')
LIB = TEXT[:TEXT.index("printf '\\nSalah Widget Installer\\n\\n'")]
ROOT = pathlib.Path(tempfile.mkdtemp(prefix='salah-install-tests-'))
os.chmod(ROOT, 0o700)
RESULTS = []

def function(name):
    start = r'^' + re.escape(name) + r'\(\) \{'
    match = re.search(start + r'[^\n]*\}\n', TEXT, re.M)
    if not match:
        match = re.search(start + r'\n.*?^\}\n', TEXT, re.M | re.S)
    if not match:
        raise RuntimeError('Missing production function: '+name)
    return match.group()

def run(code, extra=None):
    env = dict(os.environ, HOME=str(ROOT/'home'), TMPDIR=str(ROOT/'tmp'))
    env.update(extra or {})
    return subprocess.run(['bash','--noprofile','--norc','-c','set -Eeuo pipefail\n'+code], text=True, capture_output=True, env=env, timeout=20)

def check(name, body):
    try:
        body(); RESULTS.append(dict(case=name, pass_=True))
    except Exception as error:
        RESULTS.append(dict(case=name, pass_=False, error=str(error)))

def require(condition, message):
    if not condition:
        raise AssertionError(message)

(ROOT/'home').mkdir(mode=0o700); (ROOT/'tmp').mkdir(mode=0o700)

def cache_path():
    asset=ROOT/'asset.zip'
    with zipfile.ZipFile(asset,'w') as archive: archive.writestr('manifest.json','{"manifest_version":3}')
    fetches=ROOT/'fetches.txt'
    r=run(LIB+'''
initialize_staging
select_asset(){ printf 'v1\ttabliss chromium.zip\tfile://%s\n' "$ASSET"; }
curl(){ printf 'fetch\n' >> "$FETCHES"; command curl "$@"; }
first="$(download_tablissng_asset chromium)"
second="$(download_tablissng_asset chromium)"
[ -f "$first" ] && [ "$first" = "$second" ]
printf '%s\n%s\n' "$first" "$second"
''',dict(ASSET=str(asset),FETCHES=str(fetches)))
    require(r.returncode==0, repr(dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)))
    paths=r.stdout.splitlines()
    require(len(paths)==2 and paths[0]==paths[1] and paths[0].startswith(str(ROOT/'tmp')+'/salah-widget-download.'),r.stdout)
    require(fetches.read_text()=='fetch\n','Duplicate asset fetch')
    require('[OK] Already downloaded' in r.stderr,'Cache status missing from stderr')

def detector():
    code=function('detect_targets')+'''
CONFIGS=("c|Chrome|chromium|fixture|chrome|new|old|store|manager|newtab" "f|Firefox|firefox|fixture|firefox|| |store|manager|newtab")
find_exe(){ printf fixture; }
chromium_profiles(){ printf '/fixture/Profile One\n/fixture/مدينة'; }
firefox_profiles(){ printf '/fixture/fire fox\n'; }
firefox_status(){ printf '0|0|'; }
has_id_dir(){ return 1; }
add_target(){ printf '%s\n' "$5"; }
enable -n mapfile
detect_targets
'''
    r=run(code)
    require(r.returncode==0 and r.stdout=='/fixture/Profile One\n/fixture/مدينة\n/fixture/fire fox\n', repr(dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)))

def profile_producer():
    profile_root=ROOT/'profiles'; profile_root.mkdir()
    r=run(function('firefox_profiles')+'firefox_profiles "$DATA"\n',dict(DATA=str(profile_root)))
    require(r.returncode==0 and not r.stdout,'Profiles container emitted as a profile: '+r.stdout)
    one=profile_root/'Profile One مدينة'; one.mkdir()
    r=run(function('firefox_profiles')+'firefox_profiles "$DATA"\n',dict(DATA=str(profile_root)))
    require(r.returncode==0 and r.stdout==str(one)+'\n','Actual producer cardinality/path wrong: '+r.stdout)

def staging_canary():
    victim=ROOT/'victim'; victim.write_bytes(b'unchanged sentinel\n')
    old=ROOT/'tmp'/'salah-widget-installer'/'presets'; old.mkdir(parents=True)
    (old/'salah-widget.tablissng.json').symlink_to(victim)
    data=ROOT/'download.json'; data.write_text('{"input":"#local=1"}\n')
    r=run(LIB+'\ninitialize_staging\ndownload_preset\n',dict(SALAH_WIDGET_HASH='lat=24.47&lon=39.61&method=4',SALAH_WIDGET_PRESET_URL=data.as_uri()))
    require(r.returncode==0, r.stderr)
    require(victim.read_bytes()==b'unchanged sentinel\n', 'Victim changed: '+repr(victim.read_bytes()))
    dest=pathlib.Path(r.stdout.strip())
    require(dest.is_file() and json.loads(dest.read_text())['input']=='#lat=24.47&lon=39.61&method=4', 'Configured private output missing')
    require(str(dest).startswith(str(ROOT/'home')+'/salah-widget-install.'),'Preset not in retained bundle')
    require((old/'salah-widget.tablissng.json').is_symlink(),'Legacy symlink touched')
    require(stat.S_IMODE(dest.parents[1].stat().st_mode)==0o700,'Retained root not private')

def dry_helpers():
    helpers=''.join(function(n) for n in ('copy_text','expand_chromium_asset','download_preset','download_tablissng_asset','select_asset','install_tablissng','retain_asset','initialize_staging','cleanup_staging','show_import_instructions'))
    r=run('''
DRY_RUN=1
NO_OPEN=0
PLATFORM=mac
DOWNLOAD_ROOT=/fixture
PRESET_ROOT=/fixture
SALAH_WIDGET_PRESET_URL=https://example.invalid/preset
need_cmd(){ :; }
ok(){ :; }
warn(){ :; }
err(){ :; }
mkdir(){ printf 'EFFECT mkdir\n' >&2; }
rm(){ printf 'EFFECT remove\n' >&2; }
unzip(){ printf 'EFFECT extract\n' >&2; }
curl(){ printf 'EFFECT network\n' >&2; return 99; }
pbcopy(){ cat >/dev/null; printf 'EFFECT clipboard\n' >&2; }
find(){ printf '/fixture/unpacked/manifest.json\n'; }
select_asset(){ printf 'v1\tasset.zip\thttps://example.invalid/asset\n'; }
sanitize(){ printf '%s' "$1"; }
[(){ if test "$1" = -f; then return 0; else builtin [ "$@"; fi; }
'''+helpers+'''
copy_text fixture || :
expand_chromium_asset /fixture/asset.zip || :
download_preset || :
download_tablissng_asset chromium || :
select_asset chromium || :
install_tablissng chromium Fixture '' fixture://store fixture://manager || :
retain_asset /fixture/asset.zip || :
initialize_staging || :
cleanup_staging || :
show_import_instructions Fixture profile '' fixture://newtab /fixture/preset.json || :
''')
    require(r.returncode==0, r.stderr)
    require('EFFECT' not in r.stderr and not r.stdout, repr(dict(stdout=r.stdout,stderr=r.stderr)))

def parent_case(case):
    parent=ROOT/case; parent.mkdir(mode=0o700)
    if case=='writable-home': os.chmod(parent,0o770)
    if case=='symlink-home':
        link=ROOT/'home-link'; link.symlink_to(parent,target_is_directory=True); parent=link
    if case=='wrong-owner-home': parent=pathlib.Path('/tmp')
    before=set((ROOT/'tmp').iterdir())
    r=run(LIB+'\ninitialize_staging\n',dict(HOME=str(parent)))
    require(r.returncode!=0,'Unsafe home admitted: '+case)
    require(set((ROOT/'tmp').iterdir())==before,'Rejected home created scratch')

def confinement(case):
    victim=ROOT/('guard-victim-'+case); victim.write_bytes(b'keep\n')
    data=ROOT/('guard-preset-'+case+'.json'); data.write_text('{"input":"#local=1"}\n')
    setup={
        'symlink': 'ln -s "$VICTIM" "$PRESET_ROOT/salah-widget.tablissng.json"\ndownload_preset',
        'symlink-parent': 'mv "$PRESET_ROOT" "$PRESET_ROOT-original"\nln -s "$OUTSIDE" "$PRESET_ROOT"\ndownload_preset',
        'prefix': 'guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$BUNDLE_ROOT-other/victim" file',
        'traversal': 'guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$BUNDLE_ROOT/../victim" file',
        'dot-leaf': 'select_asset(){ printf "..\\tasset.zip\\tfile://$VICTIM\\n"; }\ndownload_tablissng_asset chromium',
    }[case]
    outside=ROOT/('outside-'+case); outside.mkdir(mode=0o700)
    r=run(LIB+'\ninitialize_staging\n'+setup+'\n',dict(VICTIM=str(victim),OUTSIDE=str(outside),SALAH_WIDGET_PRESET_URL=data.as_uri()))
    require(r.returncode!=0,'Unsafe staged path admitted: '+case)
    require(victim.read_bytes()==b'keep\n','Outside sentinel changed')
    require(not list(outside.iterdir()),'Symlinked parent written')

def archive_case(case):
    before_bundles=set((ROOT/'home').glob('salah-widget-install.*'))
    source=ROOT/('archive-'+case+'.zip'); victim=ROOT/('zip-victim-'+case); victim.write_text('keep')
    if case=='malformed': source.write_bytes(b'not a zip')
    else:
        with zipfile.ZipFile(source,'w') as archive:
            archive.writestr('first-marker.txt','preflight must run first')
            if case=='safe': archive.writestr('Folder One/مدينة/manifest.json','{"manifest_version":3}')
            elif case=='traversal': archive.writestr('../victim','bad')
            elif case=='absolute': archive.writestr(str(victim),'bad')
            elif case=='backslash': archive.writestr('..\\victim','bad')
            elif case=='symlink':
                info=zipfile.ZipInfo('link'); info.create_system=3; info.external_attr=(stat.S_IFLNK|0o777)<<16
                archive.writestr(info,str(victim))
            elif case=='no-manifest': archive.writestr('readme.txt','no extension')
    r=run(LIB+'''
initialize_staging
cp "$ARCHIVE" "$DOWNLOAD_ROOT/fixture.zip"
expand_chromium_asset "$DOWNLOAD_ROOT/fixture.zip"
''',dict(ARCHIVE=str(source)))
    require(victim.read_text()=='keep','ZIP escaped to victim')
    if case=='safe':
        require(r.returncode==0,r.stderr)
        dest=pathlib.Path(r.stdout.strip()); require((dest/'manifest.json').is_file(),'Manifest path missing after exit')
        require(str(dest).startswith(str(ROOT/'home')+'/salah-widget-install.'),'Unpacked directory not retained')
        require('Folder One/مدينة' in str(dest),'Archive Unicode/spaces lost')
        restarted=subprocess.check_output(['python3','-c','import json,pathlib,sys; print(json.dumps(json.loads((pathlib.Path(sys.argv[1])/"manifest.json").read_text())))',str(dest)],text=True)
        require(json.loads(restarted)=={'manifest_version':3},'Fresh consumer could not read retained manifest')
    else:
        require(r.returncode!=0 and not r.stdout,'Unsafe/invalid archive returned artifact path')
        if case not in ('malformed','no-manifest'):
            # Preflight must reject before first-marker is extracted.
            new_bundles=set((ROOT/'home').glob('salah-widget-install.*'))-before_bundles
            require(not any(list(bundle.glob('fixture-unpacked.*/first-marker.txt')) for bundle in new_bundles),'Member written before unsafe-member validation')

def cleanup_identity():
    r=run(LIB+'''
initialize_staging
original="$WORK_ROOT"
mv "$WORK_ROOT" "$WORK_ROOT-original"
mkdir "$WORK_ROOT"
printf 'keep' > "$WORK_ROOT/canary"
cleanup_staging
printf '%s\n' "$original/canary"
''')
    require(r.returncode==0,r.stderr)
    require(pathlib.Path(r.stdout.strip()).read_text()=='keep','Changed scratch identity deleted')
    require('cleanup skipped' in r.stderr,'Changed identity not reported')

def repeated_roots():
    roots=[]
    for _ in range(2):
        r=run(LIB+'\ninitialize_staging\nprintf "%s\\n%s\\n" "$WORK_ROOT" "$BUNDLE_ROOT"\n')
        require(r.returncode==0,r.stderr); pair=r.stdout.splitlines(); require(len(pair)==2,r.stdout)
        require(not pathlib.Path(pair[0]).exists() and pathlib.Path(pair[1]).is_dir(),'Scratch/retained lifetime wrong')
        roots.append(pair)
    require(roots[0][0]!=roots[1][0] and roots[0][1]!=roots[1][1],'Cross-run roots reused')

def temp_parent_case(case):
    parent=ROOT/case; parent.mkdir(mode=0o700)
    if case=='writable-tmp': os.chmod(parent,0o777)
    else:
        link=ROOT/'tmp-link'; link.symlink_to(parent,target_is_directory=True); parent=link
    before=set((ROOT/'home').iterdir())
    r=run(LIB+'\ninitialize_staging\n',dict(TMPDIR=str(parent)))
    require(r.returncode!=0 and before==set((ROOT/'home').iterdir()),'Untrusted temporary parent admitted')

def retained_boundary(case):
    before_scratch=set((ROOT/'tmp').glob('salah-widget-download.*'))
    home=ROOT/('boundary-home-'+case); home.mkdir(mode=0o700)
    data=ROOT/('boundary-'+case+'.json'); data.write_text('not JSON' if case=='preset-failure' else '{"input":"#local=1"}')
    code=LIB+'\ninitialize_staging\ndownload_preset\n'
    env=dict(os.environ,HOME=str(home),TMPDIR=str(ROOT/'tmp'),SALAH_WIDGET_PRESET_URL=data.as_uri())
    if case=='interrupt': code+='kill -TERM $$\n'
    r=subprocess.run(['bash','--noprofile','--norc','-c','set -Eeuo pipefail\n'+code],env=env,text=True,capture_output=True,timeout=20)
    if case=='interrupt':
        require(r.returncode==143 and pathlib.Path(r.stdout.strip()).is_file(),'TERM trap deleted retained preset or failed to terminate')
        require('Partial bundle retained' in r.stderr,'Interrupted retained state not reported')
    else:
        require(r.returncode!=0 and not r.stdout and 'Partial bundle retained' in r.stderr,'Failed preset became an artifact/success')
    bundles=list(home.glob('salah-widget-install.*')); require(len(bundles)==1 and bundles[0].is_dir(),'Partial bundle removed')
    require(set((ROOT/'tmp').glob('salah-widget-download.*'))==before_scratch,'Scratch remained after failure/interrupt')

check('cached stdout is one path', cache_path)
check('detector supports missing mapfile and Unicode paths', detector)
check('actual Firefox producer zero/one profiles', profile_producer)
check('legacy symlink canary + configured preset positive', staging_canary)
check('dry helpers produce no effect or artifact path', dry_helpers)
for case in ('writable-home','symlink-home','wrong-owner-home'): check('parent refuses '+case,lambda case=case:parent_case(case))
for case in ('writable-tmp','symlink-tmp'): check('parent refuses '+case,lambda case=case:temp_parent_case(case))
for case in ('symlink','symlink-parent','prefix','traversal','dot-leaf'): check('write confinement '+case,lambda case=case:confinement(case))
for case in ('traversal','absolute','backslash','symlink','malformed','no-manifest','safe'): check('archive '+case,lambda case=case:archive_case(case))
check('scratch cleanup refuses changed identity',cleanup_identity)
check('cross-run freshness and retained lifetime',repeated_roots)
for case in ('preset-failure','interrupt'): check('retained boundary '+case,lambda case=case:retained_boundary(case))
print(json.dumps(dict(host=subprocess.check_output(['bash','--version'],text=True).splitlines()[0], uid=os.getuid(), fixture=str(ROOT), source=hashlib.sha256(SOURCE.read_bytes()).hexdigest(), results=RESULTS),ensure_ascii=False,indent=2))
sys.exit(1 if any(not r['pass_'] for r in RESULTS) else 0)
