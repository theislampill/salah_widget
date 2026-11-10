"""Independent offline readback of the existing Firefox day/night evidence.

Does not execute product code, start browsers, or modify acquired evidence.
"""
from pathlib import Path
import hashlib, json, subprocess, sys
from urllib.parse import urlsplit, parse_qs

OUT=Path(__file__).resolve().parent
EV=OUT.parent
ROOT=EV.parent/'salah_widget'
FFMPEG=Path(r'C:\Users\theis\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe')
FFPROBE=FFMPEG.with_name('ffprobe.exe')
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_bytes())
def dump(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')

group=sys.argv[1]
assert group in ['day','night','boundary-pilot','boundary-preferences']
packet=read(ROOT/'tests/rlgwo/R000C-cases.json')
for path,digest in packet['sourceFiles'].items():assert sha((ROOT/path).read_bytes())==digest,path
paths=(sorted((EV/'native/firefox-day-remaining').glob('*/receipt.json'))+[EV/'native/firefox-day/R000C-invalid-precip/receipt.json']) if group=='day' else sorted((EV/('native/firefox-'+group if group.startswith('boundary-') else 'native/firefox-night')).glob('*/receipt.json'))
assert len(paths)=={'day':6,'night':3,'boundary-pilot':1,'boundary-preferences':2}[group]
report={'schema':'r000c-independent-firefox-readback/v1','group':group,'cases':[],'scope':'Original raw semantics and complete original frame inventory; visual review is recorded separately. No continuous-watch PASS is inferred from later readable state crops.'}
for rp in paths:
    r=read(rp);case=read(rp.parent/'case-input.json');ip=rp.parent/'pixel-review/index.json';index=read(ip)
    assert case==next(c for c in packet['cases'] if c['id']==case['id'])
    if group.startswith('boundary-'):
        assert case['id'] in (['R000C-night-default'] if group=='boundary-pilot' else ['R000C-night-reduced','R000C-night-full'])
        assert r['observerMode']=='full-diagnostic-boundaries-passive-recovery'
        assert [o['stage'] for o in r['observations']]==['initial','initial-30s','recovered','recovered-30s']
        assert [w['stage'] for w in r['watches']]==['initial','recovered']
        assert all(w['requiredSeconds']==30 and w['endHostMonotonic']-w['startHostMonotonic']>=30 for w in r['watches'])
    assert r['status']=='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW' and all(r['checks'].values()) and not r['pageErrors']
    assert r['browser']['family']=='firefox' and r['browser']['headless']
    assert sha(Path(r['browser']['executable']).read_bytes())==r['browser']['executableSha256']
    assert r['fixture']['sourceSha256']==packet['sourceFiles']['index.html']
    assert r['fixture']['storageIsolated'] and r['fixture']['clockIsolated'] and r['fixture']['fetchIntercepted']
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
    out=OUT/rp.parent.parent.name/case['id'];out.mkdir(parents=True,exist_ok=True)
    extracted=[]
    targets=([250,750,2250,2500,2750,3000,n-1] if case.get('night') else [n-1])
    for ordinal in targets:
        assert ordinal<n
        dest=out/f'original-{ordinal:05d}.png'
        subprocess.run([str(FFMPEG),'-v','error','-i',str(video),'-vf',f'select=eq(n\\,{ordinal})','-frames:v','1','-fps_mode','passthrough',str(dest)],check=True)
        extracted.append({'path':str(dest.relative_to(OUT)),'sha256':sha(dest.read_bytes()),'ordinal':ordinal,'ptsSeconds':index['frames'][ordinal]['ptsSeconds'],'decodedRgbSha256':index['frames'][ordinal]['decodedRgbSha256']})
    suspects=[s for s in index['samples'] if s['suspect']]
    report['cases'].append({'id':case['id'],'lane':rp.parent.parent.name,'browser':r['browser'],'inputSha256':sha((rp.parent/'case-input.json').read_bytes()),'receiptSha256':sha(rp.read_bytes()),'indexSha256':sha(ip.read_bytes()),'video':r['video'],'frames':n,'durationPts':index['durationPts'],'allFrameHashesAndPtsMatch':True,'suspectCandidates':len(suspects),'lastSuspectPts':max([s['ptsSeconds'] for s in suspects],default=None),'semanticChecks':'PASS','observations':observations,'watches':r.get('watches'),'weatherRequests':[{'elapsedMs':q['elapsedMs'],'sourceTime':q['parsedBody']['current']['time'],'precip':q['parsedBody']['current']['precipitation']} for q in weather],'independentExtractions':extracted})
dump(OUT/f'firefox-{group}-readback-check.json',report)
print(json.dumps({'group':group,'framesVerified':sum(c['frames'] for c in report['cases']),'cases':[{k:c[k] for k in ['id','frames','durationPts','suspectCandidates','lastSuspectPts','semanticChecks']} for c in report['cases']]},indent=2))
