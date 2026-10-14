"""Capture-process clock and bounded post-capture bridge acquisition.

Only root's later browser lease executes these acquisition helpers. Clock
receipts are saved separately from immutable raw frame/observer receipts.
"""
import asyncio
import hashlib
import json
import time
import uuid
from pathlib import Path


class CaptureClock:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=False)
        info = time.get_clock_info('perf_counter')
        if not info.monotonic or info.adjustable:
            raise ValueError('capture perf_counter must be monotonic and non-adjustable')
        self.clock = {'id':'capture:'+uuid.uuid4().hex,'kind':'python-monotonic','unit':'ms',
            'api':'time.perf_counter_ns','implementation':info.implementation,
            'resolutionMs':info.resolution*1000,'monotonic':info.monotonic,
            'adjustable':info.adjustable}
        self.samples = []
        self.counter = 0

    def now(self):
        return time.perf_counter_ns()/1000000

    def retain(self, label, value):
        self.counter += 1
        file = self.directory/(str(self.counter).zfill(4)+'-'+label+'.json')
        raw = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
        with file.open('xb') as stream:stream.write(raw)
        return {'file':str(file),'sha256':hashlib.sha256(raw).hexdigest()}

    def navigation(self):
        # Stamp at the original request boundary; defer receipt I/O until after capture.
        return {'kind':'navigation-request','clockId':self.clock['id'],'atMs':self.now()}

    def retain_navigation(self, event):
        return {**event,'artifact':self.retain('navigation',event)}

    async def browser_bridge(self, frame):
        before = self.now()
        sample = await frame.evaluate('''()=>{
          const atMs=performance.now(), clock=window.SalahStartupTiming?.snapshot().clock;
          return {atMs,clock};
        }''')
        after = self.now()
        if not isinstance(sample,dict) or not isinstance(sample.get('clock'),dict):
            return None
        row = {'kind':'bracketed-clock-sample','sampleId':uuid.uuid4().hex,
            'sourceClockId':sample['clock']['id'],'sourceKind':'window-performance',
            'targetClockId':self.clock['id'],'sourceAtMs':sample['atMs'],
            'targetBeforeMs':before,'targetAfterMs':after}
        row['artifact']=self.retain('browser-clock',{'sample':sample,**row})
        self.samples.append(row);return row

    async def driver_bridge(self, rpc_directory, timeout=3):
        rpc = Path(rpc_directory)
        request_id = uuid.uuid4().hex
        request = {'schema':'salah-capture-clock-request/1','requestId':request_id}
        before = self.now()
        temporary = rpc/(request_id+'.request.tmp')
        with temporary.open('x') as stream:
            json.dump(request,stream)
        temporary.rename(rpc/(request_id+'.request.json'))
        response = rpc/(request_id+'.response.json')
        deadline = time.perf_counter()+timeout
        while not response.is_file():
            if time.perf_counter()>=deadline:return None
            await asyncio.sleep(.01)
        raw = response.read_bytes();after = self.now()
        data = json.loads(raw)
        if data.get('schema')!='salah-capture-clock-response/1' or data.get('requestId')!=request_id:
            raise ValueError('clock response identity mismatch')
        row={'kind':'bracketed-clock-sample','sampleId':request_id,
            'sourceClockId':data['clock']['id'],'sourceKind':'node-hrtime',
            'targetClockId':self.clock['id'],'sourceAtMs':data['atMs'],
            'targetBeforeMs':before,'targetAfterMs':after}
        # Associate the actual retained RPC bytes after the unchanged bracket.
        request_file = rpc/(request_id+'.request.json')
        request_raw = request_file.read_bytes()
        if json.loads(request_raw) != request:
            raise ValueError('clock request raw field mismatch')
        request_artifact = {'file':str(request_file),'sha256':hashlib.sha256(request_raw).hexdigest()}
        response_artifact = {'file':str(response),'sha256':hashlib.sha256(raw).hexdigest()}
        row['artifact']=self.retain('driver-clock',{'request':request,'response':data,
            'requestArtifact':request_artifact,'responseArtifact':response_artifact,
            'responseSha256':hashlib.sha256(raw).hexdigest(),**row})
        self.samples.append(row);return row
