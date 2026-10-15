"""One-run loopback HTTP headers/body/Image holds. No native/browser claim by this module."""
import copy
import base64
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import runpy
import secrets
import threading
import time
from urllib.parse import parse_qs,urlsplit

N=runpy.run_path(str(Path(__file__).resolve().parent/'run_weather_native.py'))

class TransportServer(N['FixtureServer']):
    def __init__(self,root,spec,run):
        super().__init__(root);self.run=run;self.token=secrets.token_urlsafe(24);self.selected=copy.deepcopy(spec)
        self.selected['transport'].update(run=run,token=self.token);self.cases[self.selected['id']]=self.selected
        self.rows=[];self.documents={};self.counts={};self.lock=threading.RLock();self.stopping=threading.Event()
        original=self.server.RequestHandlerClass;parent=self
        class Handler(original):
            def do_GET(self):
                p=urlsplit(self.path)
                if p.path=='/transport' or p.path.startswith('/transport-tile/'):return parent.handle(self,p)
                return super().do_GET()
            def do_POST(self):
                if urlsplit(self.path).path!='/control/release':self.send_error(404);return
                try:
                    size=int(self.headers.get('Content-Length','0'))
                    if size<1 or size>4096:raise ValueError('body size')
                    data=json.loads(self.rfile.read(size))
                    if self.headers.get('X-Weather-Test-Token')!=parent.token or data.get('run')!=parent.run:raise ValueError('run token')
                    with parent.lock:
                        row=next((x for x in parent.rows if x['requestId']==data.get('requestId')and x['document']==data.get('document')),None)
                        if not row or not row['held']:raise ValueError('owned held request')
                        row['releasedAt']=time.monotonic();row['_release'].set()
                    body=b'{"released":true}';self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
                except (ValueError,TypeError,json.JSONDecodeError):self.send_error(403)
        self.server.RequestHandlerClass=Handler
    def target_kind(self):
        stage=self.selected['transport']['stage'];return 'weather' if stage.startswith('weather-')else'manifest' if stage.startswith('manifest-')else'image'
    def handle(self,handler,parts):
        try:
            if parts.path=='/transport':
                q=parse_qs(parts.query,strict_parsing=True)
                if set(q)!={'run','document','case','kind','clientNow'} or any(len(v)!=1 for v in q.values()):raise ValueError('query shape')
                run,document,case,kind,client=[q[k][0]for k in ('run','document','case','kind','clientNow')]
                if handler.headers.get('X-Weather-Test-Token')!=self.token or run!=self.run or case!=self.selected['id']or kind not in('weather','manifest'):raise ValueError('identity')
                client=int(client)
                if not re.fullmatch(r'[0-9a-f-]{36}',document)or client<0:raise ValueError('document/clock')
                with self.lock:self.documents[document]=client
            else:
                segments=parts.path.split('/')
                if len(segments)<9 or segments[2]!=self.token or segments[3]!=self.run or segments[4]not in self.documents or segments[5:7]!=['v2','radar']or not parts.path.endswith('/2/1_1.png'):raise ValueError('Image identity/path')
                document=segments[4];kind='image';client=self.documents[document]
            with self.lock:
                key=(document,kind);number=self.counts.get(key,0)+1;self.counts[key]=number
                held=kind==self.target_kind()and number in self.selected['transport'].get('heldNumbers',[1,2])
                row={'requestId':secrets.token_hex(12),'run':self.run,'document':document,'kind':kind,'number':number,
                  'arrivedAt':time.monotonic(),'clientNow':client,'held':held,'headersFlushedAt':None,'prefixBytes':0,'releasedAt':None,'finishedAt':None,'writeError':None,'_release':threading.Event()}
                self.rows.append(row)
            if kind=='image':body=self.tile;mime='image/png'
            elif kind=='weather':
                local=datetime.fromtimestamp((client+3*3600000)/1000,timezone.utc).isoformat(timespec='minutes')[:16]
                # Original healthy() current/hourly input, with captured Riyadh timestamps/units.
                current={'time':local,'interval':900,'weather_code':95,'temperature_2m':20,'apparent_temperature':19,
                         'relative_humidity_2m':90,'dew_point_2m':18,'wind_speed_10m':2,'wind_direction_10m':180,
                         'wind_gusts_10m':4,'cloud_cover':95,'precipitation':2,'is_day':0 if self.selected.get('night') else 1}
                # A04's synthetic first source quarter-hour is already aged.
                # It expires naturally while body2 is held. Actual successor
                # bodies retain the existing dispatch-clock timestamp producer.
                if (number==1 and self.selected['id'] in ('D-preserve-weather-body-night-reduced','D-preserve-weather-body-night-full')
                    and self.selected['transport'].get('expiryClock')=='real1x-source-TTL-boundary'):
                    current['time']='2026-09-07T21:30'
                later=datetime.fromtimestamp((client+4*3600000)/1000,timezone.utc).isoformat(timespec='minutes')[:16]
                hourly={'time':[local,later],'temperature_2m':[20,19],'weather_code':[95,3],
                        'wind_direction_10m':[180,180],'precipitation':[2,0]}
                payload={'timezone':'Asia/Riyadh','elevation':100,'current':current,'hourly':hourly,
                         'current_units':{'temperature_2m':'°C','precipitation':'mm'},
                         'hourly_units':{'temperature_2m':'°C','precipitation':'mm'}}
                # Preserve the original A04 warm-current/no-track input: it permits the
                # ordinary poll before natural source expiry. Healthy replacements include track.
                if number==1 and self.selected['transport'].get('gap')=='preservation':payload.pop('hourly')
                body=json.dumps(payload,allow_nan=False).encode();mime='application/json'
            else:
                second=client//1000
                host=self.origin+('/transport-tile/'+self.token+'/'+self.run+'/'+document if self.target_kind()=='image'else'/tile')
                body=json.dumps({'generated':second,'host':host,'radar':{'past':[{'time':second,'path':'/v2/radar/'+str(second)}]}},allow_nan=False).encode();mime='application/json'
            row['bodyBytes']=len(body);row['bodySha256']=N['sha'](body);row['bodyBase64']=base64.b64encode(body).decode()
            stage=self.selected['transport']['stage']
            headers_hold=held and stage.endswith('-headers')
            def await_release():
                while not row['_release'].wait(.1):
                    if self.stopping.is_set():return False
                return True
            if headers_hold and not await_release():return
            try:
                handler.send_response(200);handler.send_header('Content-Type',mime);handler.send_header('Content-Length',str(len(body)));handler.send_header('Cache-Control','no-store');handler.end_headers();handler.wfile.flush()
                row['headersFlushedAt']=time.monotonic()
                if held and not headers_hold:
                    prefix=body[:16];handler.wfile.write(prefix);handler.wfile.flush();row['prefixBytes']=len(prefix)
                    if not await_release():return
                    handler.wfile.write(body[len(prefix):])
                else:handler.wfile.write(body)
                handler.wfile.flush();row['finishedAt']=time.monotonic()
            except (BrokenPipeError,ConnectionResetError,OSError)as error:
                row['writeError']=type(error).__name__+': '+str(error);row['finishedAt']=time.monotonic()
        except (ValueError,KeyError):handler.send_error(403)
    def state(self):
        with self.lock:return [{k:v for k,v in x.items()if not k.startswith('_')}for x in self.rows]
    def __exit__(self,*args):
        self.stopping.set()
        for row in self.rows:row['_release'].set()
        super().__exit__(*args)
