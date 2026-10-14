"""Disposable existing-driver copy retaining raw frames and monotonic receipts.

Never modifies the installed driver. Native source timestamps stay raw; callback
receipts are pixel-visible upper bounds, not physical presentation timestamps.
"""
import argparse,hashlib,json,shutil
from pathlib import Path

PATCH = r"""        if (process.env.SALAH_CAPTURE_NATIVE_FRAMES === '1') {
          const fs = require('node:fs'), path = require('node:path');
          const symbol = Symbol.for('salah.capture.monotonic/1');
          const clock = globalThis[symbol] ||= (() => {
            const value = {id: 'driver:' + process.pid + ':' + require('node:crypto').randomUUID(),
              kind: 'node-hrtime', unit: 'ms'};
            const rpc = process.env.SALAH_CAPTURE_CLOCK_RPC;
            if (rpc) {
              const watcher = fs.watch(rpc, {persistent:false}, (_event, file) => {
                file = String(file || '');
                if (!/^[0-9a-f]{32}\.request\.json$/.test(file)) return;
                try {
                  const request = JSON.parse(fs.readFileSync(path.join(rpc,file),'utf8'));
                  if (request.schema !== 'salah-capture-clock-request/1' || file !== request.requestId+'.request.json') return;
                  const response = {schema:'salah-capture-clock-response/1', requestId:request.requestId,
                    clock:value, atMs:Number(process.hrtime.bigint())/1e6};
                  const temporary = path.join(rpc,request.requestId+'.response.tmp');
                  const destination = path.join(rpc,request.requestId+'.response.json');
                  if (fs.existsSync(destination)) return;
                  fs.writeFileSync(temporary,JSON.stringify(response),{flag:'wx'});
                  fs.renameSync(temporary,destination);
                } catch { /* Failed clock acquisition stays UNKNOWN, never a guessed bridge. */ }
              });
              watcher.unref();
            }
            return value;
          })();
          const atMs = Number(process.hrtime.bigint())/1e6;
          const seq = this._salahSeq = (this._salahSeq || 0) + 1;
          const folder = this._outputFile + '.frames', file = String(seq).padStart(6,'0') + '.jpeg';
          const eventId = this._outputFile + ':source:' + seq;
          const record = {seq, sourceTimeSeconds:timestamp, receiptUtcMs:Date.now(),
            receiptMonotonicMs:atMs, receiptClock:clock, sourceEventId:eventId,
            presentedReceiptEventId:this._outputFile + ':pixel-receipt:' + seq,
            file, bytes:frame.length};
          if (seq === 1) fs.mkdirSync(folder, {recursive:true});
          fs.appendFileSync(this._outputFile + '.frames.jsonl',JSON.stringify(record) + '\n');
          fs.writeFileSync(path.join(folder,file),frame);
        }
"""


ORIGINAL_BUNDLE_SHA256 = 'f74353fcb8e406756a70a6af0dfc4a5069acd577e35ec9d923ccf36ac009c2f5'


PHASE_HANDLER = r"""      _onScreencastFrame(payload) {
        const salahHandlerEnteredMs = process.env.SALAH_CAPTURE_PHASE_OBSERVATION === '1' ? Number(process.hrtime.bigint())/1e6 : null;
        const buffer = Buffer.from(payload.data, "base64");
        const frameSwapWallTime = payload.metadata.timestamp ? payload.metadata.timestamp * 1e3 : Date.now();
        const viewportWidth = payload.metadata.deviceWidth, viewportHeight = payload.metadata.deviceHeight;
        const salahCapturePhase = salahHandlerEnteredMs === null ? undefined : (() => {
          const descriptor = Object.getOwnPropertyDescriptor(payload.metadata, 'timestamp');
          const inspectable = descriptor ? Object.prototype.hasOwnProperty.call(descriptor, 'value') : !('timestamp' in payload.metadata);
          const value = inspectable && descriptor ? descriptor.value : undefined;
          const handlerSeq = this._salahCaptureHandlerSeq = (this._salahCaptureHandlerSeq || 0) + 1;
          return {schema:'salah-capture-phase-record/1', token:this._page.guid+':capture-handler:'+handlerSeq,
            pageId:this._page.guid, protocolSessionId:payload.sessionId, handlerSeq,
            eventHandlerEnteredMs:salahHandlerEnteredMs,
            metadata:{deviceWidth:viewportWidth,deviceHeight:viewportHeight,timestampHasOwn:!!descriptor,
              timestampInspectable:inspectable,timestampType:inspectable?typeof value:'unavailable',
              timestampValue:value === undefined ? null : typeof value === 'number' && !Number.isFinite(value) ? String(value) : value,
              timestampEncoding:!inspectable?'unavailable':value === undefined?'undefined':typeof value === 'number' && !Number.isFinite(value)?'nonfinite-number':'json',
              timestampNegativeZero:Object.is(value,-0)},
            timestampBranch:inspectable?(value?'protocol-timestamp':'driver-Date.now-fallback'):'UNKNOWN_PROVENANCE',
            selectedFrameSwapWallTime:frameSwapWallTime};
        })();
        this._page.screencast.onScreencastFrame({
          buffer, frameSwapWallTime, viewportWidth, viewportHeight, salahCapturePhase
        }, () => {
          if (salahCapturePhase) salahCapturePhase.ackInvokedMs = Number(process.hrtime.bigint())/1e6;
          this._client._sendMayFail("Page.screencastFrameAck", { sessionId: payload.sessionId });
          if (salahCapturePhase) salahCapturePhase.ackCallReturnedMs = Number(process.hrtime.bigint())/1e6;
        });
      }
"""
PHASE_RECORDER_BIND = r"""          const phase = process.env.SALAH_CAPTURE_PHASE_OBSERVATION === '1' && capturePhase ? {handler:capturePhase} : undefined;
          if (phase) {
            phase.recorderEnteredMs = atMs;
            phase.receiptClock = clock;
            phase.outputFile = this._outputFile;
            phase.rawReceiptPath = this._outputFile + '.frames.jsonl';
            phase.pixelPath = path.join(folder,file);
            phase.originalReceipt = record;
            phase.forwardedSourceTimeSeconds = timestamp;
            const phases = this._salahCapturePhases ||= [];
            if (phases.length < 8192) phases.push(phase);
            else this._salahCapturePhaseOverflow = (this._salahCapturePhaseOverflow || 0) + 1;
            phase.rawPersistenceStartedMs = Number(process.hrtime.bigint())/1e6;
          }
"""
PHASE_AFTER_APPEND = r"""          if (phase) phase.rawReceiptAppendFinishedMs = Number(process.hrtime.bigint())/1e6;
"""
PHASE_AFTER_PIXEL = r"""          if (phase) phase.rawPixelWriteFinishedMs = Number(process.hrtime.bigint())/1e6;
"""
PHASE_FLUSH = r"""      _salahFlushCapturePhases() {
        if (this._salahCapturePhaseFlushed) return;
        const records = (this._salahCapturePhases || []).map(({handler,...owned}) => ({...handler,...owned})), overflow = this._salahCapturePhaseOverflow || 0;
        const required = ['eventHandlerEnteredMs','recorderEnteredMs','rawPersistenceStartedMs',
          'rawReceiptAppendFinishedMs','rawPixelWriteFinishedMs','ackInvokedMs','ackCallReturnedMs'];
        const incomplete = records.filter(r => !r.metadata.timestampInspectable || !r.pageId || !r.receiptClock ||
          required.some(k => typeof r[k] !== 'number' || !Number.isFinite(r[k]))).map(r => r.token);
        const data = {schema:'salah-capture-phase-observation/1', outputFile:this._outputFile,
          clock:globalThis[Symbol.for('salah.capture.monotonic/1')] || null, maximumRecords:8192,
          records, overflow, incompleteTokens:incomplete, complete:records.length > 0 && overflow === 0 && incomplete.length === 0,
          sourceLabelsAreEndpoints:false, physicalDisplayProof:false, ackTransportCompletionProof:false,
          flushBoundary:'after existing videoRecorder._stop and artifact.reportFinished'};
        require('node:fs').writeFileSync(this._outputFile + '.capture-phases.json', JSON.stringify(data,null,2)+'\n', {encoding:'utf8',flag:'wx'});
        this._salahCapturePhaseFlushed = true;
      }
"""

def observe_bundle(text):
 anchors={
  'handler':('      _onScreencastFrame(payload) {\n','      async _updateGeolocation('),
  'client':'onFrame: (frame) => this._videoRecorder.writeFrame(frame.buffer, frame.frameSwapWallTime / 1e3),',
  'recorder':'      writeFrame(frame, timestamp) {\n',
  'persistence':'          if (seq === 1) fs.mkdirSync(folder, {recursive:true});\n',
  'append':"          fs.appendFileSync(this._outputFile + '.frames.jsonl',JSON.stringify(record) + '\\n');\n",
  'pixel':'          fs.writeFileSync(path.join(folder,file),frame);\n',
  'flush':'      _writeFrame(frame, timestamp) {\n',
  'stop':'        await videoRecorder._stop();\n        await artifact.reportFinished();\n'
 }
 for key,value in anchors.items():
  for literal in value if isinstance(value,tuple) else [value]:
   if text.count(literal)!=1:raise ValueError('Unsupported phase-observer anchor: '+key)
 start=text.index(anchors['handler'][0]);end=text.index(anchors['handler'][1],start)
 text=text[:start]+PHASE_HANDLER+text[end:]
 text=text.replace(anchors['client'],anchors['client'].replace('/ 1e3)', '/ 1e3, frame.salahCapturePhase)'))
 text=text.replace(anchors['recorder'],'      writeFrame(frame, timestamp, capturePhase) {\n')
 text=text.replace(anchors['persistence'],PHASE_RECORDER_BIND+anchors['persistence'])
 text=text.replace(anchors['append'],anchors['append']+PHASE_AFTER_APPEND)
 text=text.replace(anchors['pixel'],anchors['pixel']+PHASE_AFTER_PIXEL)
 text=text.replace(anchors['flush'],PHASE_FLUSH+anchors['flush'])
 text=text.replace(anchors['stop'],anchors['stop']+"        if (process.env.SALAH_CAPTURE_PHASE_OBSERVATION === '1') videoRecorder._salahFlushCapturePhases();\n")
 return text

CURRENT_PHASE_BUNDLE_SHA256 = '9aa5c7c9a77af8c8a965715dfcae7634fe88f1ddbe4849100f0f6256e18546dc'
CONNECTION_ENTRY_OBSERVATION = {'schema':'salah-capture-connection-entry/1',
 'timestampSite':'CRConnection._onMessage before original receive logger',
 'clockKind':'node-hrtime','unit':'ms','scope':'connection callback to handler only; not wire ingress or physical presentation'}
CONNECTION_MESSAGE = r"""      async _onMessage(message) {
        const salahConnectionMessageEnteredMs = process.env.SALAH_CAPTURE_PHASE_OBSERVATION === '1' && message.method === 'Page.screencastFrame' ? Number(process.hrtime.bigint())/1e6 : null;
        if (salahConnectionMessageEnteredMs !== null && message.params && typeof message.params === 'object') {
          const params = message.params, sessionId = message.sessionId || "";
          const protocol = Object.getOwnPropertyDescriptor(params, 'sessionId');
          (this._salahConnectionEntry ||= new WeakMap()).set(params, {
            atMs:salahConnectionMessageEnteredMs, params, connection:this,
            session:this._sessions.get(sessionId), sessionId,
            protocolSessionId:protocol && Object.prototype.hasOwnProperty.call(protocol,'value') ? protocol.value : null,
            protocolSessionIdInspectable:!!protocol && Object.prototype.hasOwnProperty.call(protocol,'value'),
            processId:process.pid, clockKind:'node-hrtime', clockUnit:'ms'});
        }
        this._protocolLogger("receive", message);
        if (message.id === kBrowserCloseMessageId)
          return;
        const session2 = this._sessions.get(message.sessionId || "");
        if (session2)
          session2._onMessage(message);
      }
"""
CONNECTION_HANDLER_BIND = r"""          const connection = this._client._connection, entry = connection?._salahConnectionEntry?.get(payload);
          const protocol = Object.getOwnPropertyDescriptor(payload, 'sessionId');
          const paramsSame = !!entry && entry.params === payload, connectionSame = !!entry && entry.connection === connection;
          const sessionSame = !!entry && entry.session === this._client && entry.sessionId === this._client._sessionId;
          const protocolSame = !!entry && entry.protocolSessionIdInspectable && !!protocol && Object.prototype.hasOwnProperty.call(protocol,'value') && entry.protocolSessionId === protocol.value;
          const bound = paramsSame && connectionSame && sessionSame && protocolSame && entry.processId === process.pid && entry.clockKind === 'node-hrtime' && entry.clockUnit === 'ms' && Number.isFinite(entry.atMs) && entry.atMs >= 0 && entry.atMs <= salahHandlerEnteredMs;
          const connectionEntry = {state:bound?'BOUND_SAME_PARAMS_SESSION_PROCESS':'MISSING_OR_MISMATCHED_CONNECTION_ENTRY',
            paramsSame, connectionSame, sessionSame, protocolSame,
            connectionSessionId:entry?entry.sessionId:null, handlerSessionId:this._client._sessionId,
            protocolSessionId:entry?entry.protocolSessionId:null,
            processId:entry?entry.processId:null, handlerProcessId:process.pid,
            clockKind:entry?entry.clockKind:null, clockUnit:entry?entry.clockUnit:null};
"""


def observe_connection_entry(text):
 if hashlib.sha256(text.encode('utf-8')).hexdigest()!=CURRENT_PHASE_BUNDLE_SHA256:
  raise ValueError('Connection checkpoint requires exact admitted phase-only derivation')
 connection='''      async _onMessage(message) {
        this._protocolLogger("receive", message);
        if (message.id === kBrowserCloseMessageId)
          return;
        const session2 = this._sessions.get(message.sessionId || "");
        if (session2)
          session2._onMessage(message);
      }
'''
 handler="          const handlerSeq = this._salahCaptureHandlerSeq = (this._salahCaptureHandlerSeq || 0) + 1;\n"
 fields='            eventHandlerEnteredMs:salahHandlerEnteredMs,\n'
 required="const required = ['eventHandlerEnteredMs','recorderEnteredMs','rawPersistenceStartedMs',"
 incomplete='const incomplete = records.filter(r => !r.metadata.timestampInspectable || !r.pageId || !r.receiptClock ||\n'
 header="const data = {schema:'salah-capture-phase-observation/1', outputFile:this._outputFile,\n"
 for literal in [connection,handler,fields,required,incomplete,header]:
  if text.count(literal)!=1:raise ValueError('Unsupported connection-entry checkpoint anchor')
 text=text.replace(connection,CONNECTION_MESSAGE)
 text=text.replace(handler,handler+CONNECTION_HANDLER_BIND)
 text=text.replace(fields,fields+'            connectionMessageEnteredMs:entry?entry.atMs:null, connectionEntry,\n')
 text=text.replace(required,"const required = ['connectionMessageEnteredMs','eventHandlerEnteredMs','recorderEnteredMs','rawPersistenceStartedMs',")
 text=text.replace(incomplete,incomplete+"          !r.connectionEntry || r.connectionEntry.state !== 'BOUND_SAME_PARAMS_SESSION_PROCESS' || r.connectionMessageEnteredMs > r.eventHandlerEnteredMs ||\n")
 text=text.replace(header,header+'          connectionEntryObservation:'+json.dumps(CONNECTION_ENTRY_OBSERVATION,separators=(',',':'))+',\n')
 return text


def render_bundle(original, phase_observation=False, connection_entry_observation=False):
 if connection_entry_observation and not phase_observation:raise ValueError('Connection entry requires explicit phase observation')
 text=original.decode('utf-8')
 if any(marker in text for marker in ['SALAH_CAPTURE_NATIVE_FRAMES','salah.capture.monotonic/1','SALAH_CAPTURE_CLOCK_RPC','SALAH_CAPTURE_PHASE_OBSERVATION']):
  raise ValueError('Already prepared/native-frame recorder hooks are prohibited before copy')
 if hashlib.sha256(original).hexdigest()!=ORIGINAL_BUNDLE_SHA256:
  raise ValueError('Unadmitted original installed driver bundle; exact accepted source required')
 anchor='      writeFrame(frame, timestamp) {\n'
 if text.count(anchor)!=1:raise ValueError('Unsupported driver recorder')
 text=text.replace(anchor,anchor+PATCH)
 rendered=observe_bundle(text) if phase_observation else text
 return observe_connection_entry(rendered) if connection_entry_observation else rendered


def prepare(source, destination, phase_observation=False, connection_entry_observation=False):
 source=Path(source).resolve();dest=Path(destination).resolve()
 if dest.exists() or dest==source or source in dest.parents:raise ValueError('Require a fresh separate output directory')
 bundle=source/'lib/coreBundle.js';original=bundle.read_bytes();text=original.decode()
 if (source/'SOURCE_FRAME_RECEIPT.json').exists() or any(marker in text for marker in
     ['SALAH_CAPTURE_NATIVE_FRAMES', 'salah.capture.monotonic/1', 'SALAH_CAPTURE_CLOCK_RPC']):
  raise ValueError('Already prepared/native-frame recorder hooks are prohibited before copy')
 if hashlib.sha256(original).hexdigest()!=ORIGINAL_BUNDLE_SHA256:
  raise ValueError('Unadmitted original installed driver bundle; exact accepted source required')
 anchor='      writeFrame(frame, timestamp) {\n'
 if text.count(anchor)!=1:raise ValueError('Unsupported driver recorder')
 rendered=render_bundle(original,phase_observation,connection_entry_observation)
 shutil.copytree(source,dest)
 (dest/'lib/coreBundle.js').write_text(rendered,encoding='utf-8',newline='\n')
 receipt={'schema':'salah-source-frame-driver/2','purpose':__doc__,
  'sourceBundleSha256':hashlib.sha256(original).hexdigest(),
  'modifiedBundleSha256':hashlib.sha256((dest/'lib/coreBundle.js').read_bytes()).hexdigest(),
  'patch':PATCH,'source':str(source),'destination':str(dest)}
 if phase_observation:receipt['capturePhaseObservation']={'schema':'salah-capture-phase-observation/1','sidecarSuffix':'.capture-phases.json','maximumRecords':8192,'endpointSubstitutionAllowed':False,'flushBoundary':'after existing videoRecorder._stop and artifact.reportFinished'}
 if connection_entry_observation:receipt['capturePhaseObservation']['connectionEntryObservation']=CONNECTION_ENTRY_OBSERVATION
 (dest/'SOURCE_FRAME_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return receipt


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('destination',type=Path);p.add_argument('--phase-observation',action='store_true');p.add_argument('--connection-entry-observation',action='store_true');a=p.parse_args()
 print(json.dumps(prepare(a.source,a.destination,a.phase_observation,a.connection_entry_observation)))
