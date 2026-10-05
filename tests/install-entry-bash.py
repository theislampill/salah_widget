#!/usr/bin/env python3
"""Actual piped Bash entry, controlled terminal input and contained effect boundaries."""
import errno, hashlib, json, os, pathlib, pty, select, signal, stat, subprocess, sys, tempfile, time, zipfile

SOURCE=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1]/'install.sh').resolve()
ROOT=pathlib.Path(tempfile.mkdtemp(prefix='salah-entry-bash-'))
os.chmod(ROOT,0o700)
RESULTS=[]

def require(ok,message):
    if not ok: raise AssertionError(message)

def snapshot(root):
    rows=[]
    for p in sorted(root.rglob('*')):
        info=p.lstat(); digest=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() and not p.is_symlink() else ''
        rows.append((str(p.relative_to(root)),stat.S_IMODE(info.st_mode),digest,os.readlink(p) if p.is_symlink() else ''))
    return rows

def fixture(name, profiles='both',source='github',dry=True):
    root=ROOT/name; root.mkdir(mode=0o700)
    subject=root/'subject'; subject.mkdir(mode=0o700)
    home=subject/'home'; home.mkdir(mode=0o700)
    tmp=subject/'tmp'; tmp.mkdir(mode=0o700)
    chrome=home/'.config/google-chrome/Default'
    if profiles!='none': chrome.mkdir(parents=True)
    if profiles in ('legacy','mixed'): (chrome/'Extensions/hipekcciheckooncpjeljhnekcoolahp').mkdir(parents=True)
    if profiles=='installed': (chrome/'Extensions/dlaogejjiafeobgofajdlkkhjlignalk').mkdir(parents=True)
    if profiles in ('both','mixed'): (home/'.mozilla/firefox/fixture profile').mkdir(parents=True)
    if profiles=='three':
        (home/'.config/microsoft-edge/Default').mkdir(parents=True)
        (home/'.config/BraveSoftware/Brave-Browser/Default/Extensions/hipekcciheckooncpjeljhnekcoolahp').mkdir(parents=True)
    preset=root/'preset.json'; preset.write_text('{"input":"#local=1"}\n')
    asset=root/'asset.zip'
    with zipfile.ZipFile(asset,'w') as archive: archive.writestr('Nested Folder/manifest.json','{"manifest_version":3}')
    if name=='cached':
        old=tmp/'salah-widget-installer'; (old/'downloads/v-fixture/asset-unpacked').mkdir(parents=True)
        (old/'downloads/v-fixture/tabliss-chromium.zip').write_bytes(asset.read_bytes())
        (old/'downloads/v-fixture/tabliss-firefox-signed.xpi').write_bytes(asset.read_bytes())
        (old/'downloads/v-fixture/asset-unpacked/marker.txt').write_text('keep')
        (old/'presets').mkdir(); (old/'presets/salah-widget.tablissng.json').write_text('keep preset')
    envfile=root/'env.sh'
    envfile.write_text(r'''
record(){ printf '%s\n' "$*" >> "$EFFECT_LOG"; }
check_path(){ case "$1" in "$FIXTURE_ROOT"/*) ;; *) record "ESCAPE $1"; return 99 ;; esac; }
command(){
  if [ "$1" = -v ]; then case "${2:-}" in google-chrome|google-chrome-stable|chrome|microsoft-edge|microsoft-edge-stable|brave-browser|brave|chromium|chromium-browser|firefox|librewolf) return 1 ;; esac; fi
  builtin command "$@"
}
mkdir(){ for item in "$@"; do case "$item" in -*) ;; *) check_path "$item" || return ;; esac; done; record "mkdir $*"; builtin command mkdir "$@"; }
mktemp(){ for item in "$@"; do case "$item" in -*) ;; *) check_path "$item" || return ;; esac; done; record "mktemp $*"; builtin command mktemp "$@"; }
rm(){ for item in "$@"; do case "$item" in -*) ;; *) check_path "$item" || return ;; esac; done; record "remove $*"; builtin command rm "$@"; }
cp(){ for item in "$@"; do case "$item" in -*) ;; *) check_path "$item" || return ;; esac; done; record "copy $*"; builtin command cp "$@"; }
mv(){ for item in "$@"; do case "$item" in -*) ;; *) check_path "$item" || return ;; esac; done; record "move $*"; builtin command mv "$@"; }
curl(){
  record "download $*"
  local item previous='' url='' destination=''
  for item in "$@"; do
    [ "$previous" != -o ] || destination="$item"
    case "$item" in file://*) url="$item" ;; esac
    previous="$item"
  done
  case "$url" in "file://$FIXTURE_ROOT"/*) ;; *) record 'DENIED network'; return 99 ;; esac
  check_path "$destination" || return
  builtin command curl --proto '=file' "$@"
}
python3(){
  if [ "$#" = 3 ] && [ "$1" = - ] && [ "$2" = fixture/repo ]; then
    record "metadata $3"; cat >/dev/null
    [ "${FAIL_METADATA:-0}" != 1 ] || { record 'DENIED metadata fixture'; return 99; }
    case "$3" in chromium) printf 'v-fixture\ttabliss-chromium.zip\tfile://%s\n' "$ASSET_FIXTURE" ;; firefox) printf 'v-fixture\ttabliss-firefox-signed.xpi\tfile://%s\n' "$ASSET_FIXTURE" ;; *) return 99 ;; esac
  else builtin command python3 "$@"; fi
}
xclip(){ local text; text="$(cat)"; record "clipboard $text"; }
xdg-open(){ record "open $*"; }
unzip(){ record "extract $*"; return 99; }
''')
    env=dict(os.environ,HOME=str(home),TMPDIR=str(tmp),PATH='/usr/bin:/bin',BASH_ENV=str(envfile),EFFECT_LOG=str(root/'effects.log'),FIXTURE_ROOT=str(root),ASSET_FIXTURE=str(asset),INSTALL_SOURCE=str(SOURCE),TABLISSNG_REPO='fixture/repo',SALAH_WIDGET_PRESET_URL=preset.as_uri(),SALAH_WIDGET_HASH='lat=24.47&lon=39.61&method=4',SALAH_INSTALL_SOURCE=source,DRY_RUN='1' if dry else '0',NO_OPEN='0')
    return root,subject,env

def run_plain(env):
    return subprocess.run(['bash','--noprofile','--norc',str(SOURCE)],env=env,text=True,capture_output=True,start_new_session=True,timeout=20)

def run_pty(env,answer='all',eof=False):
    pid,fd=pty.fork()
    if pid==0:
        os.execvpe('bash',['bash','--noprofile','--norc','-c','cat "$INSTALL_SOURCE" | bash'],env)
    output=b''; menu=False; prompts=0; choices=0; status=None; deadline=time.monotonic()+20
    try:
        while time.monotonic()<deadline:
            if select.select([fd],[],[],0.05)[0]:
                try: data=os.read(fd,65536)
                except OSError as error:
                    if error.errno!=errno.EIO: raise
                    data=b''
                if data: output+=data
            decoded=output.decode('utf-8',errors='replace')
            if not menu and 'Select target numbers' in decoded:
                os.write(fd,b'\x04' if eof else (answer+'\n').encode()); menu=True
            count=decoded.count('Choose [1/2]')
            while choices<count: os.write(fd,b'1\n'); choices+=1
            count=decoded.count('Press Enter after the browser step')
            while prompts<count: os.write(fd,b'\n'); prompts+=1
            done,raw=os.waitpid(pid,os.WNOHANG)
            if done:
                status=os.waitstatus_to_exitcode(raw)
                # Drain the terminal so the final lifetime path is included.
                while select.select([fd],[],[],0.05)[0]:
                    try: data=os.read(fd,65536)
                    except OSError: break
                    if not data: break
                    output+=data
                break
        require(status is not None,'Owned PTY entry timed out: '+output.decode(errors='replace'))
        return status,output.decode('utf-8',errors='replace'),dict(menu=menu,confirmations=prompts,sourceChoices=choices)
    finally:
        if status is None:
            try: os.killpg(pid,signal.SIGKILL)
            except ProcessLookupError: pass
            os.waitpid(pid,0)
        os.close(fd)

def effect_lines(root):
    path=root/'effects.log'; return path.read_text().splitlines() if path.exists() else []

def preview(name,profiles='both',source='github',failure=False,invalid=False):
    root,subject,env=fixture(name,profiles,source)
    if name=='missing-preset': env['SALAH_WIDGET_PRESET_URL']=''  # explicitly empty override must remain empty
    if invalid: env['SALAH_INSTALL_SOURCE']='invalid'
    before=snapshot(subject); r=run_plain(env); after=snapshot(subject); effects=effect_lines(root)
    require(not effects and before==after,repr(dict(effects=effects,stdout=r.stdout,stderr=r.stderr)))
    require((r.returncode!=0)==failure,repr(dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)))
    if not failure:
        require('Preview only; no changes made' in r.stdout and 'Press Enter' not in r.stdout,'Bad preview completion/prompt')
        if source=='ask': require('Install source unresolved' in r.stdout,'Source choice fabricated')
        if profiles!='installed' and source=='github': require('release/version/path unresolved' in r.stdout,'Release/path fabricated')
        if name=='missing-preset': require('No preset URL configured' in r.stdout+r.stderr,'Empty preset override silently replaced')
    return dict(exit=r.returncode,effects=len(effects),snapshotUnchanged=before==after,fixture=str(root))

def terminal(name,answer='all',profiles='both',source='github',failure=False,eof=False,no_terminal=False,no_open=False,failed_release=False):
    root,subject,env=fixture(name,profiles,source,dry=False)
    if no_open: env['NO_OPEN']='1'
    if failed_release: env['FAIL_METADATA']='1'
    before=snapshot(subject)
    if no_terminal:
        r=run_plain(env); status=r.returncode; output=r.stdout+r.stderr; inputs={}
    else: status,output,inputs=run_pty(env,answer,eof)
    effects=effect_lines(root)
    if failure:
        require(status!=0 and not effects and before==snapshot(subject),repr(dict(exit=status,effects=effects,output=output)))
        require('Validated manual-install files retained' not in output,'False staged completion')
    else:
        require(status==0,repr(dict(exit=status,effects=effects,output=output)))
        require(any(e.startswith('download ') for e in effects) and any(e.startswith('clipboard ') for e in effects),'Normal external callers not reached')
        if source=='github': require(any(e.startswith('metadata ') for e in effects),'Release lookup caller not reached')
        require(any(e.startswith('mktemp ') for e in effects) and any(e.startswith('remove ') for e in effects),'Private staging/cleanup not reached')
        require('Keep this directory while the unpacked extension is installed.' in output if source=='github' and not failed_release else True,'Unpacked lifetime warning missing')
        if no_open: require(not any(e.startswith('open ') for e in effects),'NO_OPEN opened a page')
        bundles=list((subject/'home').glob('salah-widget-install.*')); require(len(bundles)==1,'One bundle per attempt violated')
        preset=bundles[0]/'presets/salah-widget.tablissng.json'
        require(preset.is_file() and json.loads(preset.read_text())['input']=='#lat=24.47&lon=39.61&method=4','Configured retained preset missing')
        require(not list((subject/'tmp').glob('salah-widget-download.*')),'Owned scratch not cleaned')
        if answer=='1,1,3':
            require(sum(e.startswith('metadata ') for e in effects)==1,'Deduplicated selection reached wrong targets')
            require('Refusing to touch this browser/profile' in output,'Legacy target not refused')
        if profiles=='both' and source=='github' and not failed_release:
            require(any(bundles[0].glob('*.xpi')),'Firefox manual asset not retained')
            require(any(bundles[0].glob('*/Nested Folder/manifest.json')),'Chromium unpacked path not retained')
            require(inputs.get('confirmations')==2,'Both later human confirmations not read from PTY')
        if source=='store' or failed_release:
            require(inputs.get('confirmations')==2,'Store/fallback confirmations not read from PTY')
            require(sum(e.startswith('download ') for e in effects)==1,'Store/fallback downloaded an extension')
            require(not list(bundles[0].glob('*.xpi')) and not list(bundles[0].glob('*unpacked*')),'Fallback invented manual extension assets')
        if failed_release: require('GitHub release download failed; falling back to store page.' in output,'Actual metadata failure branch not reached')
    (root/'entry-output.txt').write_text(output)
    return dict(exit=status,effects=len(effects),inputs=inputs,fixture=str(root))

def check(name,body):
    try: RESULTS.append(dict(case=name,pass_=True,observation=body()))
    except Exception as error: RESULTS.append(dict(case=name,pass_=False,error=str(error)))

for name in ('github','cached','store','ask','installed','mixed','missing-preset'):
    check('offline '+name,lambda name=name:preview(name,profiles=name if name in ('installed','mixed') else 'both',source=name if name in ('store','ask') else 'github'))
check('offline legacy-only',lambda:preview('legacy',profiles='legacy',failure=True))
check('offline zero targets',lambda:preview('none',profiles='none',failure=True))
check('offline malformed option',lambda:preview('invalid',invalid=True,failure=True))
check('pipe actual PTY all and later confirmations',lambda:terminal('normal'))
check('pipe empty answer defaults all',lambda:terminal('empty',answer=''))
check('pipe explicit indices',lambda:terminal('indices',answer='1,2'))
check('pipe deduplicate and refuse legacy',lambda:terminal('dedup',answer='1,1,3',profiles='three'))
check('pipe source ask and confirmations',lambda:terminal('source-ask',source='ask'))
check('pipe store confirmation input',lambda:terminal('normal-store',source='store'))
check('pipe metadata-failure fallback input',lambda:terminal('metadata-fallback',failed_release=True))
check('NO_OPEN retains normal effects',lambda:terminal('no-open',no_open=True))
check('no controlling terminal before effects',lambda:terminal('no-terminal',failure=True,no_terminal=True))
check('PTY EOF before effects',lambda:terminal('eof',failure=True,eof=True))
check('PTY invalid token before effects',lambda:terminal('bad-token',answer='1,bad',failure=True))
check('PTY unknown index before effects',lambda:terminal('unknown',answer='999',failure=True))
check('PTY legacy-only before effects',lambda:terminal('legacy-terminal',profiles='legacy',failure=True))
print(json.dumps(dict(host=subprocess.check_output(['bash','--version'],text=True).splitlines()[0],uid=os.getuid(),source=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),fixture=str(ROOT),results=RESULTS),ensure_ascii=False,indent=2))
sys.exit(1 if any(not r['pass_'] for r in RESULTS) else 0)
