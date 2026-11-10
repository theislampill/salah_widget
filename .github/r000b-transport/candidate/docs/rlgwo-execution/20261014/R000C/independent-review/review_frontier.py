"""Independent offline verification of existing R000C inputs and original evidence."""
from pathlib import Path
import hashlib, importlib.util, json, re, subprocess, sys
from urllib.parse import urlsplit, parse_qs

OUT=Path(__file__).resolve().parent
EV=OUT.parent
ROOT=EV.parent/'salah_widget'
FFMPEG=Path(r'C:\Users\theis\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe')
FFPROBE=FFMPEG.with_name('ffprobe.exe')
NODE=Path(r'C:\workspace\ai\cp9-integration-20261005\toolchain\node-v22.16.0-win-x64\node.exe')
def sha(x):return hashlib.sha256(x).hexdigest()
def read(p):return json.loads(p.read_bytes())
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def module(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def gitblob(commit,p):return subprocess.check_output(['git','--no-optional-locks','show',commit+':'+p],cwd=ROOT)

packet=read(ROOT/'tests/rlgwo/R000C-cases.json')
curr=read(EV/'currentness.json')
assessment=read(EV/'authority/accepted-assessment.json')
source={'schema':'r000c-independent-source-and-receipts/v1','acceptedRows':[],'tests':[],'mutants':[]}
assert curr['candidateBase']==packet['sourceCommit']=='7827099dff3c9bc5ecb1b7a67dc4c25414bcfb69'
for row in curr['acceptedRows']:
    claims=[]
    for s in row['spans']:
        text=gitblob(curr['acceptedCommit'],s['file']).decode().replace('\r\n','\n')
        a,b=s['originalLines'];fragment='\n'.join(text.splitlines()[a-1:b])
        assert sha(fragment.encode())==s['spanSha256'],(row['id'],s)
        actual=(ROOT/s['file']).read_text(encoding='utf8')
        assert actual.count(fragment)==1
        line=actual[:actual.index(fragment)].count('\n')+1
        assert line==s['currentStartLine']
        claims.append({'file':s['file'],'currentStartLine':line,'sha256':s['spanSha256'],'exactOccurrences':1})
    source['acceptedRows'].append({'id':row['id'],'verdict':'EXACT_ACCEPTED_SPANS_CURRENT','spans':claims})
assert len(source['acceptedRows'])==13
for t in curr['tests']:
    before=gitblob(curr['acceptedCommit'],t['path']);now=(ROOT/t['path']).read_bytes()
    assert now==before and sha(now)==t['currentSha256']==t['priorSha256']
    source['tests'].append({'file':t['path'],'sha256':sha(now),'originalBytesUnchanged':True})
runtime=module('runtime_identity',ROOT/'tools/cp9/runtime_identity.py').runtime_identity(ROOT)
assert runtime==packet['runtime']
source['runtime']={'fileCount':len(runtime['files']),'treeSha256':runtime['treeSha256'],'allPacketPinsMatch':True}
source['frozenV1Errors']=module('verify_v1',ROOT/'tools/verify_v1.py').verify(ROOT)
assert not source['frozenV1Errors']
for p,digest in packet['sourceFiles'].items():assert sha((ROOT/p).read_bytes())==digest,p
source['packetSourcePins']=packet['sourceFiles']
receipt=read(EV/'mutants/receipt.json')
original=(ROOT/'index.html').read_bytes()
assert sha(original)==receipt['sourceSha256']
assert sha((ROOT/'tests/r000c-weather.test.cjs').read_bytes())==receipt['oracleSha256']
for m in receipt['mutations']:
    before=m['before'].encode();after=m['after'].encode()
    assert original.count(before)==1
    data=(EV/'mutants'/(m['id']+'.html')).read_bytes()
    assert data==original.replace(before,after,1) and sha(data)==m['afterSha256']
    logs={}
    for key in ['original','mutant','positive']:
        p=EV/'mutants'/m[key]['log'];raw=p.read_bytes();assert sha(raw)==m[key]['sha256']
        text=raw.decode();logs[key]={'sha256':sha(raw),'pass':int(re.search(r'^# pass (\d+)',text,re.M)[1]),'fail':int(re.search(r'^# fail (\d+)',text,re.M)[1]),'failedTests':re.findall(r'^not ok \d+ - (.+)',text,re.M)}
        assert m[key]['environment']['SALAH_WEATHER_SOURCE'].replace('\\','/').endswith('/'+('index.html' if key=='original' else m['id']+'.html'))
        assert 'SyntaxError' not in text
        if key=='mutant':assert 'ERR_ASSERTION' in text and logs[key]['fail']>0
        else:assert logs[key]['fail']==0 and logs[key]['pass']>0
    assert logs['positive']['pass']==5
    source['mutants'].append({'id':m['id'],'exactSingleOriginalSourceMutation':True,'oracleUnchanged':True,'logs':logs,'verdict':'KILLED_BY_INTENDED_ASSERTION_WITH_FIVE_POSITIVES'})
source['retainedTestLogs']={}
for name in ['baseline-weather.tap','baseline-hotfix.tap','original-related-controls.tap','authored-weather.tap']:
    raw=(EV/name).read_bytes();text=raw.decode()
    source['retainedTestLogs'][name]={'sha256':sha(raw),**{key:int(re.search(r'^# '+key+r' (\d+)',text,re.M)[1]) for key in ['tests','pass','fail','todo']}}
source['docs']={p:sha((ROOT/p).read_bytes()) for p in ['README.md','DESIGN.md']}
for p,digest in read(EV/'docs-review.json')['files'].items():assert source['docs'][p]==digest
preserve=read(EV/'preservation-reuse.json');files=0
for control in preserve['controls']:
    for path,digest in control['files'].items():assert sha((ROOT/path).read_bytes())==digest,path;files+=1
    case=ROOT/control['path']/'case-input.json';binding=read(ROOT/control['path']/'document-hashes.json')
    html=subprocess.check_output([str(NODE),str(ROOT/'tests/rlgwo/prayer-browser-fixture.cjs'),str(ROOT/'index.html'),str(case)],cwd=ROOT)
    assert sha(html)==binding['observed'],control['path']
source['preservationReuse']={'controls':len(preserve['controls']),'originalFilesVerified':files,'originalObservedHtmlRegeneratedIdentically':True,'scope':preserve['R000CScope']}
dump(OUT/'source-and-receipts-check.json',source)

native={'schema':'r000c-independent-native-readback/v1','cases':[],'limits':'No browser or product execution. Raw receipts and all original media hashes reconciled. Visual review is separate; no metric-only continuity PASS.'}
paths=sorted((EV/'native/chromium').glob('*/receipt.json'))+[EV/'native/firefox-single-headed-pilot/R000C-invalid-precip/receipt.json']
for rp in paths:
    r=read(rp);case=read(rp.parent/'case-input.json');index=read(rp.parent/'pixel-review/index.json');lane=rp.parent.parent.name
    canonical=next(c for c in packet['cases'] if c['id']==case['id']);assert canonical==case
    assert r['status']=='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW' and all(r['checks'].values())
    assert r['fixture']['storageIsolated'] and r['fixture']['clockIsolated'] and r['fixture']['fetchIntercepted']
    assert r['fixture']['sourceSha256']==packet['sourceFiles']['index.html']
    weather=[q for q in r['fixture']['ledger'] if urlsplit(q['url']).hostname=='api.open-meteo.com']
    assert len(weather)==(2 if case.get('night') else 1)
    for q in weather:
        args=parse_qs(urlsplit(q['url']).query)
        assert args['latitude']==['24.47'] and args['longitude']==['39.61'] and args['timezone']==['Asia/Riyadh'] and args['temperature_unit']==['celsius']
        assert q['jsonReads']==1 and q['jsonSettled'] is True
    first=weather[0]['parsedBody']['current']
    if case['inputCase']=='12-absent-temp':assert 'temperature_2m' not in first
    else:assert first['temperature_2m']==case['temp']
    assert first['precipitation']==('Infinity' if case['precip'] is None else case['precip'])
    observations=[]
    for obs in r['observations']:
        s=obs['state'];recovered=obs['stage'].startswith('recovered');temp,amount=(20,2) if recovered else (case['temp'],case['precip'])
        assert s['raw']['temp']==s['cached']['w']['temp']==temp and s['raw']['precip']==s['cached']['w']['precip']==amount
        assert s['temperature']==('' if temp is None else str(temp)+'°')
        assert s['icon']=='⛈️' and s['fx']=='thunder' and s['qa']['weatherHeader']['rawCode']==95
        assert s['qa']['wxTruth']['lane']=='live' and s['qa']['wxTruth']['observedPresent'] is False
        assert 'current model estimate' in s['headerLabel'] and 'direct local observation unavailable' in s['headerLabel']
        wet=amount is not None and amount>0
        assert s['precip']==('on' if wet else 'off') and (s['visibleParticles']>0)==wet
        assert s['lightning']=='off' and not s['qa']['wxTruth']['visualPermissions']['lightning']
        assert s['qa']['wxTruth']['radarPrecipMm']==s['radar']['precipMm']==0 and not s['qa']['wxTruth']['radarConfirming']
        assert s['card']=={'width':325,'height':530} and s['footer']['top']>=0 and s['footer']['bottom']<=530.1
        assert s['motion']['reduced']==(case['motionPreference']=='reduce') and s['motion']['full']==case.get('fullMotion',False)
        if amount is None:assert s['raw']['admission']['precip']=='invalid measurement'
        mt=s['qa']['moonTruth']
        observations.append({'stage':obs['stage'],'hostMonotonic':obs['hostMonotonic'],'elapsedMs':s['elapsedMs'],'wallUtcMs':s['wallUtcMs'],'temp':temp,'precip':amount,'particles':s['visibleParticles'],'moon':{'visible':mt['calendarMoonVisible'],'fresh':mt['moonSkyFresh'],'phase':mt['phaseFraction'],'status':mt['surface']['status'],'quality':mt['surface']['quality']},'motion':s['motion']})
    assert all(x['action']=='consumer-read' for x in r['fixture']['weatherEvents'])
    if case.get('night'):
        assert weather[-1]['parsedBody']['current']['precipitation']==2
        assert weather[-1]['elapsedMs']-weather[0]['elapsedMs']>=60000
        a,z=observations[0],observations[-1]
        assert abs((z['wallUtcMs']-a['wallUtcMs'])-(z['elapsedMs']-a['elapsedMs']))<10
        assert z['elapsedMs']-a['elapsedMs']>=60000
        assert z['moon']['phase']==.5 and z['moon']['visible']
        starts={x['stage']:x for x in observations}
        assert starts['initial-30s']['hostMonotonic']-starts['initial']['hostMonotonic']>=30
        assert starts['recovered-30s']['hostMonotonic']-starts['recovered']['hostMonotonic']>=30
    video=rp.parent/r['video']['file'];assert sha(video.read_bytes())==r['video']['sha256']==index['videoSha256']
    assert sha(rp.read_bytes())==index['receiptSha256']
    probe=json.loads(subprocess.check_output([str(FFPROBE),'-v','error','-select_streams','v:0','-show_entries','stream=width,height:frame=best_effort_timestamp_time','-of','json',str(video)]))
    assert [probe['streams'][0]['width'],probe['streams'][0]['height']]==[390,600]
    proc=subprocess.Popen([str(FFMPEG),'-v','error','-i',str(video),'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    n=0
    while True:
        frame=proc.stdout.read(390*600*3)
        if not frame:break
        assert len(frame)==390*600*3 and sha(frame)==index['frames'][n]['decodedRgbSha256']
        assert index['frames'][n]['ptsSeconds']==float(probe['frames'][n]['best_effort_timestamp_time']);n+=1
    assert proc.wait()==0 and n==len(index['frames'])==len(probe['frames'])
    out=OUT/lane/case['id'];out.mkdir(parents=True,exist_ok=True)
    if case.get('night'):
        # Native-sized original temporal pixels, without interpolation or redrawing.
        for start,end,label in [(1,31,'initial'),(90,126,'recovery')]:
            cmd=[str(FFMPEG),'-v','error','-i',str(video),'-vf',f"select='between(t,{start},{end})*not(mod(n,50))',tile=5x4",'-frames:v','1','-fps_mode','passthrough',str(out/(label+'-native-sequence.png'))]
            subprocess.run(cmd,check=True)
    else:
        selected=index['frames'][-1]['ordinal']
        subprocess.run([str(FFMPEG),'-v','error','-i',str(video),'-vf',f'select=eq(n\\,{selected})','-frames:v','1','-fps_mode','passthrough',str(out/'last-original.png')],check=True)
    native['cases'].append({'lane':lane,'id':case['id'],'inputSha256':sha((rp.parent/'case-input.json').read_bytes()),'receiptSha256':sha(rp.read_bytes()),'indexSha256':sha((rp.parent/'pixel-review/index.json').read_bytes()),'video':r['video'],'frames':n,'durationPts':index['durationPts'],'allFrameHashesAndPtsMatch':True,'suspectCandidates':len([s for s in index['samples'] if s['suspect']]),'semanticChecks':'PASS','observations':observations,'weatherRequests':[{'elapsedMs':q['elapsedMs'],'sourceTime':q['parsedBody']['current']['time'],'precip':q['parsedBody']['current']['precipitation']} for q in weather]})
dump(OUT/'native-readback-check.json',native)
print(json.dumps({'acceptedRows':len(source['acceptedRows']),'originalTests':len(source['tests']),'mutants':len(source['mutants']),'runtime':source['runtime'],'preservation':source['preservationReuse'],'nativeCases':len(native['cases']),'framesVerified':sum(c['frames'] for c in native['cases']),'nativeSummary':[{k:c[k] for k in ['lane','id','frames','durationPts','suspectCandidates','semanticChecks']} for c in native['cases']]},indent=2))
