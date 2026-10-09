"""Primary-only bounded browser follow-up. Prepared by C; never executed by C.

Extends tests/widget-fixture.html with declared transport cases. Actual delivered
scripts, native HTTP assets, fetchWeather/fetchRadar, Image, canvas, render and QA
execute. Fixed fixture clock/storage/provider data are disclosed; no live-provider
or normal-live M0 claim. Fresh disposable profiles, no persistent browser state.
"""
import argparse, functools, hashlib, http.server, json, os, struct, sys, threading, traceback, zlib
from pathlib import Path
from urllib.parse import urlencode, urlsplit, unquote

BASE=Path(__file__).resolve().parent
EXPECTED_INDEX='ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee'
EXPECTED_RUNTIME='f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'
CASES={
 '12-null-temp':(12,24.47,39.61,None,2),
 '12-zero-temp':(12,24.47,39.61,0,2),
 '12-invalid-precip':(12,24.47,39.61,20,None),
 '12-wet':(12,24.47,39.61,20,2),
 '14-dry':(14,24.47,39.61,20,0),
 '14-wet':(14,24.47,39.61,20,2),
 '30-equator':(30,0,30,20,2),
 '30-meridian':(30,30,0,20,2),
 '30-origin':(30,0,0,20,2),
}
TILES={'30-equator':(37,32),'30-meridian':(32,26),'30-origin':(32,32)}
def sha(data):return hashlib.sha256(data).hexdigest()
def png_rgba(rgba):
 def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
 raw=(b'\0'+bytes(rgba)*256)*256
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',256,256,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def write_json(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def run(a):
 root=a.root.resolve();out=a.out.resolve()
 if BASE not in out.parents:raise ValueError('Output must stay within workers/C')
 if sha((root/'index.html').read_bytes())!=EXPECTED_INDEX:raise ValueError('Delivered source is not pinned audit target')
 sys.path.insert(0,str(root/'tools/cp9'))
 from browser_runtime import launch_browser,browser_identity
 from runtime_identity import runtime_identity
 from playwright.sync_api import sync_playwright
 before=runtime_identity(root)
 if before['treeSha256']!=EXPECTED_RUNTIME:raise ValueError('Runtime target changed')
 prepared=json.loads((BASE/'browser-fixture-preparation.json').read_text(encoding='utf-8'))
 wrapper=BASE/'browser-fixtures/widget-fixture.html'
 if sha(wrapper.read_bytes())!=prepared['preparedFixtureSha256']:raise ValueError('Prepared fixture changed')
 out.mkdir(parents=True,exist_ok=True);requests=[];tile=png_rgba([130,123,105,73])
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   path=unquote(urlsplit(self.path).path);requests.append(path)
   if path=='/fixture.html':data=wrapper.read_bytes();mime='text/html; charset=utf-8'
   elif path.startswith('/tile/v2/radar/') and path.endswith('/2/1_1.png'):data=tile;mime='image/png'
   elif path.startswith('/product/'):
    relative=path[len('/product/'):];target=(root/relative).resolve()
    if root not in target.parents:self.send_error(400,'Path outside target');return
    if not target.is_file():self.send_error(404);return
    data=target.read_bytes();mime=self.guess_type(str(target))
   elif path=='/favicon.ico':self.send_response(204);self.end_headers();return
   else:self.send_error(404);return
   self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
 threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:'+str(server.server_port)
 report={'status':'RUNNING','target':'18ff14860ff41c084b1db5f396bb62aa9c22b1be','runtime':before,'preparation':prepared,
  'harnessSha256':sha(Path(__file__).read_bytes()),'browserExecutionBy':'primary if executed; C prepared only',
  'scope':__doc__,'tile':{'rgba':[130,123,105,73],'sha256':sha(tile),'semantics':'historically preserved scheme2 0dBZ test row; not a provider observation'},'cases':[]}
 write_json(out/'results.json',report)
 try:
  os.environ['SALAH_BROWSER']=a.browser
  with sync_playwright() as pw:
   browser=launch_browser(pw);report['browser']=browser_identity(browser)
   try:
    for number,(name,(issue,lat,lon,temp,precip)) in enumerate(CASES.items(),1):
     if issue!=a.issue:continue
     case_out=out/name;case_out.mkdir(exist_ok=True)
     context=browser.new_context(viewport={'width':390,'height':600},reduced_motion='no-preference',timezone_id='Asia/Riyadh')
     page=context.new_page();errors=[];image_requests=[]
     page.on('pageerror',lambda e:errors.append(str(e)))
     page.on('request',lambda r:image_requests.append(r.url) if '/tile/' in r.url else None)
     config={'lat':lat,'lon':lon,'tz':'Asia/Riyadh','label':'Public coordinate fixture','method':4,'school':0,'units':'c','local':1,'seed':1}
     url=origin+'/fixture.html?'+urlencode({'case':name,'attempt':number,'run':'C-audit-primary-only','mode':'healthy'})+'#'+urlencode(config)
     row={'id':name,'issue':issue,'coordinates':[lat,lon],'expected':{'temperature':temp,'normalizedPrecip':precip,'rain':precip is not None and precip>0,'lightning':False},'url':url}
     try:
      page.goto(url,wait_until='domcontentloaded')
      page.wait_for_function("window.__widgetFixture?.state==='ready'||window.__widgetFixture?.state==='error'",timeout=45000)
      if page.evaluate('__widgetFixture.state')!='ready':raise AssertionError(page.evaluate('__widgetFixture.error'))
      # Read-only bridge; no installModel/installSynthetic/advanceClock helpers called.
      page.wait_for_function("()=>{const f=window.__widgetFixture,b=window.__smokeWeather;if(f?.state!=='ready'||!b)return false;const s=b.read(b.identity());return s.qa.cache.prayerLoaded&&s.modelEligible&&!s.wxBusy&&!s.radarBusy&&s.radar?.sample&&s.qa.weatherHeader?.rawCode===95;}",timeout=45000)
      wet=precip is not None and precip>0
      page.wait_for_function("wet=>{const b=__smokeWeather,s=b.read(b.identity());return wet?(s.precip==='on'&&s.visibleParticles>0):(s.precip==='off'&&s.visibleParticles===0);}",arg=wet,timeout=10000)
      snapshot=page.evaluate('()=>__smokeWeather.read(__smokeWeather.identity())')
      fixture=page.evaluate('__widgetFixture')
      wanted_tiles=TILES.get(name,(39,27))
      checks={
       'exactSource':fixture['sourceSha256']==EXPECTED_INDEX,
       'sourceOwnedHooks':fixture['storageIsolated'] and fixture['clockFixed'] and fixture['fetchIntercepted'],
       'actualWeatherAndManifestBodiesConsumed':all(any(x['jsonReads']==1 and x['result']=='json-consumed' and endpoint in x['url'] for x in fixture['ledger']) for endpoint in ['api.open-meteo.com/v1/forecast','api.rainviewer.com/public/weather-maps.json']),
       'rawNormalizedTemp':snapshot['raw']['temp']==temp,
       'cachedNormalizedTemp':snapshot['cached']['w']['temp']==temp,
       'headerTemp':snapshot['temperature']==('' if temp is None else str(temp)+'°'),
       'normalizedPrecip':snapshot['raw']['precip']==precip,
       'conditionRetainedAsModel':snapshot['icon']=='⛈️' and snapshot['fx']=='thunder' and snapshot['qa']['weatherHeader']['rawCode']==95,
       'modelDisclosure':'current model estimate' in snapshot['headerLabel'] and 'direct local observation unavailable' in snapshot['headerLabel'],
       'actualParticles':snapshot['visibleParticles']>0 if wet else snapshot['visibleParticles']==0,
       'effectDataset':snapshot['precip']==('on' if wet else 'off'),
       'noLightning':snapshot['lightning']=='off' and not snapshot['qa']['wxTruth']['visualPermissions']['lightning'],
       'notObserved':snapshot['qa']['wxTruth']['observedPresent'] is False,
       'actualReadable0dBZImage':snapshot['radar']['sample']['returnCount']>0 and any('/256/6/'+str(wanted_tiles[0])+'/'+str(wanted_tiles[1])+'/2/1_1.png' in x for x in image_requests),
       'radarContributesNoMm':snapshot['qa']['wxTruth']['radarPrecipMm']==0 and snapshot['radar']['precipMm']==0 and snapshot['qa']['wxTruth']['radarConfirming'] is False,
       'cardGeometry':snapshot['card']=={'width':325,'height':530},
       'footerFits':snapshot['footer']['top']>=0 and snapshot['footer']['bottom']<=530.1,
       'noPageError':not errors,
      }
      if name=='14-dry':checks['gateDowngradeDespite0dBZ']=snapshot['qa']['wxTruth']['modelCondition']=='overcast'
      if name=='12-invalid-precip':checks['malformedAmountReason']=snapshot['raw']['admission'].get('precip')=='invalid measurement' and bool(snapshot['qa']['wxTruth']['visualPermissions'].get('quantitativeSupport'))
      try:
       page.evaluate("()=>{const b=__smokeWeather;return b.read({...b.identity(),attempt:-1});}")
       checks['wrongOwnerRejected']=False
      except Exception:checks['wrongOwnerRejected']=True
      # Pictures decide art/readability; these geometry checks do not decide pixels.
      page.locator('.c').screenshot(path=str(case_out/'card.png'))
      page.locator('.h').screenshot(path=str(case_out/'header.png'))
      page.locator('.d').screenshot(path=str(case_out/'footer.png'))
      row.update(checks=checks,state=snapshot,fixture=fixture,imageRequests=image_requests,pageErrors=errors,status='PASS' if all(checks.values()) else 'FAIL',primaryVisualReview='REQUIRED; C has not seen these unexecuted pixels')
     except Exception:row.update(status='FAIL',exception=traceback.format_exc(),pageErrors=errors)
     finally:context.close()
     report['cases'].append(row);write_json(case_out/'receipt.json',row);write_json(out/'results.json',report)
   finally:browser.close()
 except Exception:report.update(status='FAIL',exception=traceback.format_exc())
 finally:server.shutdown()
 after=runtime_identity(root);report['runtimeUnchanged']=after==before
 report['status']='PASS' if report['cases'] and all(c['status']=='PASS' for c in report['cases']) and report['runtimeUnchanged'] and 'exception' not in report else 'FAIL'
 report['limitations']='No live-provider/coverage guarantee, all-phase Moon opacity, normal1x M0, font appearance or overall issue closure inferred. Fixed-source inspection and primary visual review/reconciliation still required.'
 write_json(out/'results.json',report)
 print(json.dumps({'status':report['status'],'cases':len(report['cases']),'failed':[c['id'] for c in report['cases'] if c['status']!='PASS']},indent=2))
 return report['status']=='PASS'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--issue',type=int,choices=[12,14,30],required=True);p.add_argument('--browser',choices=['chromium','firefox'],default='chromium');args=p.parse_args();raise SystemExit(0 if run(args) else 1)
