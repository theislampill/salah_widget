"""Finite R0007 request-ingress experiment; no product scheduling or font refetch.

Synchronous buffered body/disposal calls cannot be interrupted by the acceptance
budgets below. The existing independent producer timeout is their hard bound.
"""
import hashlib
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

MODE = 'late-css-held-fonts-v1'
CSS_URL = 'https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=Inter:wght@400;500;600&display=swap'
CSS_PATTERN = re.compile('^' + re.escape(CSS_URL) + '$')
FONT_PATTERN = re.compile(r'^https://fonts\.gstatic\.com/[^#]*$')
CSS_CAP, FONT_CAP, TOTAL_CAP = 262144, 4194304, 8388608
OMITTED_ERROR_TEXT = 'OMITTED_UNTRUSTED_ERROR_TEXT'
SAFE_ERROR_TYPES = frozenset({'Error','TimeoutError','RuntimeError','ValueError','AssertionError','TypeError',
                            'OSError','FileNotFoundError','PermissionError','UnicodeDecodeError','KeyError',
                            'IndexError','AttributeError','NotImplementedError'})

class DiagnosticError(RuntimeError):
    """Only this helper's explicitly authored reasons may retain message text."""
    def __init__(self, message, *, source_type='DiagnosticError', provenance='INTERNALLY_AUTHORED_FIXED_REASON'):
        self.error_details={'errorType':source_type,'message':message,'messageProvenance':provenance}
        super().__init__(source_type+': '+message)

def error_receipt(error):
    if type(error) is DiagnosticError:return dict(error.error_details)
    name=type(error).__name__
    return {'errorType':name if name in SAFE_ERROR_TYPES else 'ExternalError',
            'message':OMITTED_ERROR_TEXT,'messageProvenance':OMITTED_ERROR_TEXT}

def sanitized_exception(error):
    receipt=error_receipt(error)
    return DiagnosticError(receipt['message'],source_type=receipt['errorType'],provenance=receipt['messageProvenance'])

def error_text(error):
    receipt=error_receipt(error)
    return receipt['errorType']+': '+receipt['message']

# Owner-approved test observation; it never edits the link or product state.
MEDIA_CONTROL = r"""({operation,url}) => {
 const key='__r0007FontIngressMedia';
 if(operation==='close'){
   if(!window[key])throw new Error('media observer was not installed');
   return window[key].close();
 }
 if(operation!=='install'||window[key])throw new Error('invalid/repeated media observer installation');
 const link=document.querySelector('link[rel="stylesheet"][href^="https://fonts.googleapis.com/css2?"]');
 if(!link||link.tagName!=='LINK'||!link.isConnected||link.ownerDocument!==document||link.href!==url)
   throw new Error('media observer exact original LINK unavailable');
 const now=performance.now.bind(performance),records=[],secondaryErrors=[],secondaryErrorDetails=[];
 class MediaDiagnosticError extends Error{}
 let observer=null,installed=false,closed=false,disconnected=false,firstError=null,
     firstErrorDetails=null,totalRecords=0,batch=0,additionalErrorCount=0;
 const installedAtPerformanceMs=now(),initialMedia=link.media;
 const fail=error=>{
   const trusted=error instanceof MediaDiagnosticError,name=error?.name,
     detail={errorType:trusted?'DiagnosticError':['Error','TypeError','RangeError','SyntaxError'].includes(name)?name:'PageError',
       message:trusted?error.message:'OMITTED_UNTRUSTED_ERROR_TEXT',
       messageProvenance:trusted?'INTERNALLY_AUTHORED_FIXED_REASON':'OMITTED_UNTRUSTED_ERROR_TEXT'};
   if(firstError===null){firstError=detail.message;firstErrorDetails=detail;}
   else if(secondaryErrors.length<16){secondaryErrors.push(detail.message);secondaryErrorDetails.push(detail);}
   else additionalErrorCount++;
 };
 const receive=(pending,deliveryKind)=>{
   if(!pending.length)return;
   try{
     const deliveredAtPerformanceMs=now(),currentMediaAtDelivery=link.media,batchId=++batch,
           offset=totalRecords,remaining=Math.max(0,16-records.length);
     totalRecords+=pending.length;
     for(let i=0;i<Math.min(remaining,pending.length);i++){
       const mutation=pending[i];
       if(mutation.type!=='attributes'||mutation.target!==link||mutation.attributeName!=='media')
         throw new MediaDiagnosticError('unexpected media mutation record');
       records.push({record:offset+i+1,batch:batchId,orderWithinBatch:i+1,
         oldValue:mutation.oldValue,currentMediaAtDelivery,deliveredAtPerformanceMs,deliveryKind,
         activationUpperBoundPerformanceMs:pending.length===1&&mutation.oldValue!=='all'&&currentMediaAtDelivery==='all'
           ?deliveredAtPerformanceMs:null});
     }
     if(totalRecords>16)fail(new MediaDiagnosticError('media record cap exceeded (16)'));
   }catch(error){fail(error);}
 };
 const read=()=>({installed,closed,disconnected,installedAtPerformanceMs,initialMedia,totalRecords,
   records:records.map(record=>({...record})),firstError,firstErrorDetails,
   secondaryErrors:secondaryErrors.slice(),secondaryErrorDetails:secondaryErrorDetails.slice(),additionalErrorCount,
   timingMeaning:'DELIVERY_UPPER_BOUND_NOT_ATTRIBUTE_WRITE_TIME'});
 const close=()=>{
   if(closed)return read();
   try{if(observer)receive(observer.takeRecords(),'cleanup-drain');}catch(error){fail(error);}
   try{if(observer){observer.disconnect();disconnected=true;}}catch(error){fail(error);}
   closed=true;return read();
 };
 window[key]=Object.freeze({read,close});
 try{
   observer=new MutationObserver(pending=>receive(pending,'callback'));
   observer.observe(link,{attributes:true,attributeFilter:['media'],attributeOldValue:true});installed=true;
 }catch(error){fail(error);}
 return read();
}"""

# Read only explicitly named fields; do not invoke fixture snapshots, model,
# renderer, font loading, clocks or product timers, and never transport HTML/SVG.
OBSERVATION = """expectedUrl => {
 const pageReadStartedMs=performance.now();
 try {
 const fixture=window.__prayerFixture, observer=window.__r0007FontSettlement;
 const link=document.querySelector('link[rel="stylesheet"][href^="https://fonts.googleapis.com/css2?"]');
 const envelope=value=>({date:value?.date?.gregorian?.date??null,
   timings:Object.fromEntries(['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'].map(k=>[k,value?.timings?.[k]??null]))});
 const textElement=e=>{
   if(!e)return {unavailable:true};
   const r=e.getBoundingClientRect(),css=getComputedStyle(e);
   return {text:String(e.textContent??'').slice(0,4096),
     font:{family:css.fontFamily,weight:css.fontWeight,style:css.fontStyle,stretch:css.fontStretch,size:css.fontSize},
     geometry:{x:r.x,y:r.y,width:r.width,height:r.height}};
 };
 const textRun=selector=>textElement(document.querySelector(selector));
 const labelElements=[...document.querySelectorAll('.left .until-label')];
 if(labelElements.length>16)throw new Error('left text observation cap exceeded');
 const leftLabels=labelElements.map(textElement);
 const text=Object.fromEntries(['.c','.cn','.nt','.left','.times','#loc','#wt','#wi','#weather-information','#ce','#ah','.left .until-time','.left .until-prayer']
   .map(selector=>[selector,textRun(selector)]));
 const prayerRows=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'].map(key=>{
   const row='.times .p[data-prayer-key="'+key+'"]';
   return {key,name:textRun(row+' b'),time:textRun(row+' .tm')};
 });
 const fontSettlement=observer?.read()??null;
 const faces=[...document.fonts].filter(face=>/^(Fraunces|Inter)$/i.test(String(face.family||'').replace(/["']/g,'').trim()));
 // The existing observer enumerates this same relevant FontFaceSet order in read().
 // Match its metadata in this synchronous read before associating its stable ID.
 const relevantFaces=faces.map((face,index)=>{
   const observed=fontSettlement?.faces?.[index];
   const associated=fontSettlement?.faces?.length===faces.length&&observed&&
     observed.family===face.family&&observed.weight===face.weight&&observed.style===face.style;
   return {observerId:associated?observed.id:null,fontFaceSetOrdinal:index+1,
     family:face.family,weight:face.weight,style:face.style,stretch:face.stretch,
     unicodeRange:face.unicodeRange,display:face.display,status:face.status};
 });
 const observation={renderOrdinal:fixture?.ordinal??null,
   current:envelope(typeof today==='undefined'?null:today),next:envelope(typeof tomorrow==='undefined'?null:tomorrow),text,prayerRows,relevantFaces,leftLabels,
   mediaObservation:window.__r0007FontIngressMedia?.read()??null,
   link:{url:link?.href??null,connected:!!link?.isConnected,
     identityMatches:!!link&&link.ownerDocument===document&&link.href===expectedUrl,
     media:link?.media??null,terminal:observer?.stylesheetTerminal(link)??null},
   fontSettlement};
 const pageReadFinishedMs=performance.now();
 return {...observation,pageReadStartedMs,pageReadFinishedMs,pagePerformanceMs:pageReadFinishedMs};
 } catch(error) {
   const name=error?.name,observationError={name:['Error','TypeError','RangeError','SyntaxError'].includes(name)?name:'PageError',
     message:'OMITTED_UNTRUSTED_ERROR_TEXT',messageProvenance:'OMITTED_UNTRUSTED_ERROR_TEXT'};
   const pageReadFinishedMs=performance.now();
   return {pageReadStartedMs,pageReadFinishedMs,observationError};
 }
}"""

def validate_font_ingress(case, issue):
    if 'fontIngress' not in case:
        return False
    if case['fontIngress'] != MODE or issue != 7:
        raise ValueError('unsupported R0007 font ingress mode/issue')
    if case.get('entry') != 'index.html' or case.get('iframe') or case.get('offline') or case.get('imageRules'):
        raise ValueError('font ingress requires root index and no conflicting routes')
    return True

class FontIngressController:
    def __init__(self, page, case_output, trace, case):
        validate_font_ingress(case, 7)
        self.page, self.output, self.case = page, Path(case_output), case
        self.phase, self.allowed = 'created', set()
        self.requests, self.responses = {}, {}
        self.listeners, self.routes, self.pending_routes = [], [], []
        self.abort_attempted = set()
        self.api = None
        self.disposed = False
        self.released = False
        self.deadline = None
        self.closed = None
        self.media_frame = None
        self.record = {'mode': MODE, 'routingHttpCacheDisabled': True,
                       'networkScope': 'shared-controlled-routing-environment',
                       'fontSelectionAuthority': 'COMPUTED_CANDIDATES_NOT_PER_GLYPH_SELECTION',
                       'videoClockAssociation': {'offset': None, 'status': 'UNKNOWN_NO_FRAME_ALIGNMENT'},
                       'requests': [], 'observations': [], 'hostEvaluations': [], 'errors': [], 'css': {},
                       'retainedFontBytes': 0, 'fontRequestCount': 0}
        trace['fontIngress'] = self.record

    def _latch(self, error, operation, row=None):
        receipt = {'phase': self.phase, 'operation': operation, **error_receipt(error),
                   'atMonotonic': time.monotonic()}
        if row is not None: receipt['requestId'] = row['requestId']
        self.record['errors'].append(receipt)
        self.record.setdefault('firstError', receipt)

    def check(self):
        if self.record['errors']:
            error = self.record['errors'][0]
            raise DiagnosticError(error['message'],source_type=error['errorType'],provenance=error['messageProvenance']) from None

    def _guard(self, operation, callback):
        def guarded(value):
            try: callback(value)
            except Exception as error: self._latch(error, operation)
        return guarded

    def install(self):
        try: self._install()
        except Exception as error:
            self._latch(error, 'install')
            raise sanitized_exception(error) from None

    def _install(self):
        self.phase = 'installed'
        for event, callback in [('request', self._request), ('response', self._response),
                                ('requestfinished', self._finished), ('requestfailed', self._failed)]:
            guarded = self._guard(event, callback)
            self.listeners.append((event, guarded))
            self.page.on(event, guarded)
        for pattern in (CSS_PATTERN, FONT_PATTERN):
            guarded = self._guard('route', self._route)
            self.routes.append((pattern, guarded))
            self.page.route(pattern, guarded)
        self.check()

    def _entry(self, request):
        if request in self.requests: return self.requests[request]
        previous = request.redirected_from
        parent = self.requests.get(previous)
        if request.url == CSS_URL: kind = 'css'
        elif request.url in self.allowed or parent and parent['row']['kind'] == 'font': kind = 'font'
        else: return None
        row = {'requestId': len(self.requests)+1, 'kind': kind, 'url': request.url,
               'method': request.method, 'resourceType': request.resource_type,
               'phase': self.phase, 'atMonotonic': time.monotonic(), 'terminal': None,
               'disposition': 'observed', 'attempts': []}
        entry = {'request': request, 'response': None, 'route': None, 'row': row}
        self.requests[request] = entry
        self.record['requests'].append(row)
        if parent: row['redirectedFromId'] = parent['row']['requestId']
        if previous is not None or request.redirected_to is not None:
            self._latch(DiagnosticError('unsupported redirected native transaction'), 'redirect', row)
        if (request.method != 'GET' or request.resource_type != ('stylesheet' if kind == 'css' else 'font')
                or request.frame != self.page.main_frame):
            self._latch(DiagnosticError('unsupported target request method/type/frame'), 'request', row)
        if kind == 'css':
            if sum(r['kind'] == 'css' for r in self.record['requests']) != 1:
                self._latch(DiagnosticError('multiple CSS requests'), 'request', row)
        else:
            self.record['fontRequestCount'] += 1
            if self.record['fontRequestCount'] > 16:
                self._latch(DiagnosticError('16-request font cap exceeded'), 'request', row)
        if self.phase == 'closing':
            self._latch(DiagnosticError('late matching request during close'), 'request', row)
        return entry

    def _request(self, request): self._entry(request)

    def _route(self, route):
        self.pending_routes.append(route)
        entry = self._entry(route.request)
        if entry is None:
            route.continue_()
            self.pending_routes.remove(route)
            return
        row = entry['row']
        if entry['route'] is not None:
            raise DiagnosticError('duplicate route association')
        entry['route'] = route
        row['disposition'] = 'held'
        if self.phase == 'closing':
            self._dispose_route(entry, 'abort')
            return
        valid = (route.request.method == 'GET' and route.request.frame == self.page.main_frame
                 and route.request.resource_type == ('stylesheet' if row['kind'] == 'css' else 'font'))
        if not valid or row['kind'] == 'font' and (self.released or self.record['fontRequestCount'] > 16):
            self._dispose_route(entry, 'continue')

    def _response(self, response):
        entry = self._entry(response.request)
        if entry is None: return
        row = entry['row']
        if entry['response'] is not None: raise DiagnosticError('multiple responses for native request')
        if response in self.responses: raise DiagnosticError('response associated with multiple requests')
        self.responses[response] = len(self.responses)+1
        entry['response'] = response
        row.update(responseId=self.responses[response], responseUrl=response.url, status=response.status,
                   mime=response.headers.get('content-type', '').split(';',1)[0].strip().lower(),
                   responseAtMonotonic=time.monotonic())
        if response.url != row['url'] or response.status != 200:
            self._latch(DiagnosticError('unexpected native terminal URL/status'), 'response', row)
        if row['mime'] not in ({'text/css'} if row['kind']=='css' else {'font/woff2','font/woff'}):
            self._latch(DiagnosticError('unsupported native response MIME'), 'response', row)
        if response.request.redirected_from is not None or response.request.redirected_to is not None:
            self._latch(DiagnosticError('unsupported native redirect'), 'response', row)

    def _terminal(self, request, terminal):
        entry = self._entry(request)
        if entry is None: return
        row = entry['row']
        if row['terminal'] is not None: raise DiagnosticError('duplicate/contradictory native terminal')
        row.update(terminal=terminal, terminalAtMonotonic=time.monotonic())
        if terminal == 'finished' and entry['response'] is None:
            raise DiagnosticError('native finished without associated response')
        if terminal == 'failed':
            row['failure'] = OMITTED_ERROR_TEXT
            row['failureProvenance'] = OMITTED_ERROR_TEXT
            if row['disposition'] != 'aborting':
                self._latch(DiagnosticError('native request failed'), 'requestfailed', row)

    def _finished(self, request): self._terminal(request, 'finished')
    def _failed(self, request): self._terminal(request, 'failed')

    def _dispose_route(self, entry, action):
        row, route = entry['row'], entry['route']
        if action == 'abort': self.abort_attempted.add(route)
        row['attempts'].append({'action': action, 'atMonotonic': time.monotonic(), 'returned': False})
        row['disposition'] = {'continue':'continuing','abort':'aborting','fulfill':'fulfilling'}[action]
        try:
            if action == 'continue': route.continue_()
            elif action == 'abort': route.abort()
            else: route.fulfill(response=self.api)
            if route in self.pending_routes: self.pending_routes.remove(route)
            row['attempts'][-1]['returned'] = True
            row['disposition'] = {'continue':'continued','abort':'aborted','fulfill':'fulfilled'}[action]
        except Exception:
            row['disposition'] = action + '-failed'
            raise

    def _budget(self, deadline, phase):
        if time.monotonic() >= deadline:
            raise DiagnosticError(phase + ' acceptance deadline expired')

    def _save(self, data, name, deadline, limit):
        self._budget(deadline, 'body custody')
        if not data or len(data) > limit: raise DiagnosticError('empty body or retained-byte cap exceeded')
        relative = Path('font-ingress')/name
        path = self.output/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        checksum = hashlib.sha256(data).hexdigest()
        self._budget(deadline, 'body custody')
        path.write_bytes(data)
        self._budget(deadline, 'body custody')
        return {'path': relative.as_posix(), 'bytes': len(data), 'sha256': checksum}

    def _parse_css(self, data):
        if len(data) > CSS_CAP: raise DiagnosticError('CSS retained-byte/parser cap exceeded')
        text = data.decode('utf-8', errors='strict')
        # Google font CSS is a finite flat @font-face stylesheet. Reject dynamic,
        # escaped or nested grammar rather than guess which resource is admitted.
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        if '\\' in text or re.search(r'@import\b', text, re.I):
            raise DiagnosticError('unsupported CSS escape/import')
        faces = list(re.finditer(r'@font-face\s*\{([^{}]*)\}', text, re.I))
        remainder = re.sub(r'@font-face\s*\{[^{}]*\}', '', text, flags=re.I)
        if not faces or remainder.strip(): raise DiagnosticError('unsupported CSS syntax')
        urls = set()
        for face in faces:
            body = face.group(1)
            matches = list(re.finditer(r'url\(\s*(?:"([^"\n]*)"|\'([^\'\n]*)\'|([^\s()\'";]+))\s*\)', body, re.I))
            if len(re.findall(r'url\s*\(', body, re.I)) != len(matches) or not matches:
                raise DiagnosticError('unsupported CSS resource syntax')
            for match in matches:
                url = next(value for value in match.groups() if value is not None)
                parsed = urlsplit(url)
                if parsed.scheme != 'https' or parsed.netloc != 'fonts.gstatic.com' or parsed.fragment or not parsed.path.startswith('/'):
                    raise DiagnosticError('unsupported CSS font URL')
                urls.add(url)
        if len(urls) > 64: raise DiagnosticError('64 declared URL cap exceeded')
        return urls

    def _evaluate(self, frame, expression, argument, operation):
        row={'id':len(self.record['hostEvaluations'])+1,'operation':operation,
             'startedMonotonic':time.monotonic(),'returned':False,
             'pageReadStartedMs':None,'pageReadFinishedMs':None,'pageTimingStatus':'UNAVAILABLE_NO_RETURN'}
        self.record['hostEvaluations'].append(row)
        try:
            value=frame.evaluate(expression,argument)
            row['returned']=True
            if isinstance(value,dict) and 'pageReadStartedMs' in value and 'pageReadFinishedMs' in value:
                row.update(pageReadStartedMs=value['pageReadStartedMs'],pageReadFinishedMs=value['pageReadFinishedMs'],
                           pageTimingStatus='PAGE_READ_SPAN_NOT_VIDEO_ALIGNMENT')
            else:row['pageTimingStatus']='NOT_A_PHASE_READ'
            return value
        except Exception as error:
            row['errorType']=error_receipt(error)['errorType']
            raise sanitized_exception(error) from None
        finally:row['finishedMonotonic']=time.monotonic()

    def _media_receipt(self, value):
        self.record['mediaObservation']=value
        if not isinstance(value,dict) or not value.get('installed'):
            raise DiagnosticError('media observer installation unavailable')
        if value.get('firstError'):
            raise DiagnosticError('media observer reported failure')

    def _observation(self, frame, name=None, applied=False):
        observation = self._evaluate(frame,OBSERVATION,CSS_URL,name or self.phase)
        if not isinstance(observation,dict):raise DiagnosticError('malformed phase observation')
        observation['hostEvaluationId']=self.record['hostEvaluations'][-1]['id']
        observation['atMonotonic'] = time.monotonic()
        if name:
            observation['phase'] = name
            self.record['observations'].append(observation)
        if observation.get('observationError'):
            self.record.setdefault('observationErrors',[]).append(observation)
            raise DiagnosticError('phase observation failed')
        if self.media_frame is not None:self._media_receipt(observation.get('mediaObservation'))
        state, link = observation.get('fontSettlement'), observation.get('link', {})
        if not isinstance(state, dict): raise DiagnosticError('native font observer missing')
        faces = state.get('faces', [])
        if (state.get('lifecycleErrors') or any(f.get('status')=='error' or f.get('loadingerrorReceipt') for f in faces)
                or any(e.get('type')=='loadingerror' and e.get('faces') for e in state.get('events', []))
                or any(e.get('event')=='error' for e in state.get('stylesheetEvents', []))):
            raise DiagnosticError('native font/stylesheet/observer lifecycle error')
        if applied:
            terminal = link.get('terminal') or {}
            if not (link.get('url')==CSS_URL and link.get('connected') and link.get('identityMatches')
                    and link.get('media')=='all' and terminal.get('event')=='load'
                    and terminal.get('isTrusted') is True and terminal.get('url')==CSS_URL and faces):
                return observation, False
        self.check()
        return observation, True

    def _dispose_api(self):
        if self.api is None or self.disposed: return
        self.disposed = True  # one attempt, also if the protocol raises
        self.record['css']['apiDisposal'] = 'attempted'
        try:
            self.api.dispose()
            self.record['css']['apiDisposal'] = 'disposed'
        except Exception as error:
            self.record['css']['apiDisposal'] = 'failed'
            self._latch(error, 'api-dispose')

    def _custody(self):
        self.check()
        for entry in list(self.requests.values()):
            row, response = entry['row'], entry['response']
            if row['terminal'] != 'finished' or response is None or 'body' in row: continue
            self._budget(self.deadline, 'settlement/custody')
            if row['kind'] == 'css':
                try:
                    data = response.body()
                except Exception as error:
                    self._budget(self.deadline, 'settlement/custody')
                    native = {'status':'unavailable', 'reason':OMITTED_ERROR_TEXT,'reasonDetails':error_receipt(error)}
                else:
                    self._budget(self.deadline, 'settlement/custody')
                    if len(data)>CSS_CAP: raise DiagnosticError('native CSS retained-byte cap exceeded')
                    checksum = hashlib.sha256(data).hexdigest()
                    if checksum != self.record['css']['apiBody']['sha256']:
                        raise DiagnosticError('native CSS hash differs from unmodified fulfillment')
                    native = {'status':'captured','bytes':len(data),'sha256':checksum}
                row['body'] = native
                self.record['css'].update(nativeBody=native, requestId=row['requestId'],responseId=row['responseId'],
                    nativeTerminal='finished', deliveredCssSha256=self.record['css']['apiBody']['sha256'])
            else:
                data = response.body()
                self._budget(self.deadline, 'settlement/custody')
                if len(data)>FONT_CAP or self.record['retainedFontBytes']+len(data)>TOTAL_CAP:
                    raise DiagnosticError('font retained-byte cap exceeded')
                row['body'] = self._save(data, 'font-'+str(row['requestId'])+'.bin', self.deadline, FONT_CAP)
                self.record['retainedFontBytes'] += len(data)
            self.check()

    def _complete(self):
        return bool(self.requests) and all(e['row']['terminal']=='finished' and 'body' in e['row'] for e in self.requests.values())

    def run(self, frame):
        try: self._run(frame)
        except Exception as error:
            self._latch(error, 'run')
            raise sanitized_exception(error) from None

    def _run(self, frame):
        self.check()
        self.phase = 'before-css'
        self.media_frame=frame
        self._media_receipt(self._evaluate(frame,MEDIA_CONTROL,{'operation':'install','url':CSS_URL},'media-install'))
        self._observation(frame, 'before-css')
        self.page.wait_for_timeout(500)
        self.check()
        css = [e for e in self.requests.values() if e['row']['kind']=='css']
        if len(css)!=1 or css[0]['route'] is None or css[0]['row']['disposition']!='held':
            raise DiagnosticError('missing/single held CSS request prerequisite')
        self.phase = 'css-acquisition'
        acquisition = time.monotonic()+10
        try:
            self.api = css[0]['route'].fetch(timeout=10000,max_redirects=0,max_retries=0)
            self._budget(acquisition, 'CSS acquisition')
            if self.api.url!=CSS_URL or self.api.status!=200 or self.api.headers.get('content-type','').split(';',1)[0].strip().lower()!='text/css':
                raise DiagnosticError('unexpected CSS URL/status/MIME')
            data = self.api.body()
            self._budget(acquisition, 'CSS acquisition')
            self.allowed = self._parse_css(data)
            self.record['css']['declaredUrls'] = sorted(self.allowed)
            self.record['css']['apiBody'] = self._save(data,'css-api.css',acquisition,CSS_CAP)
            self._dispose_route(css[0], 'fulfill')
            self.record['css']['fulfillment'] = 'fulfilled'
            application = time.monotonic()+10
            self._budget(acquisition, 'CSS acquisition')
        finally:
            self._dispose_api()
        self.check()
        self.phase = 'css-application'
        while True:
            self._budget(application, 'CSS application')
            observation, applied = self._observation(frame, applied=True)
            self._budget(application, 'CSS application')
            if applied: break
            self.page.wait_for_timeout(min(50, max(1,(application-time.monotonic())*1000)))
        observation['phase']='css-applied'; self.record['observations'].append(observation)
        self.record['css']['applicationObserved'] = True
        self.phase = 'fonts-held'
        loading = any(f['status']=='loading' for f in observation['fontSettlement']['faces'])
        self.page.wait_for_timeout(2000)
        end, applied = self._observation(frame, 'fonts-held-end', applied=True)
        loading = loading or any(f['status']=='loading' for f in end['fontSettlement']['faces'])
        if not applied: raise DiagnosticError('CSS application lost during ingress hold')
        held = [e for e in self.requests.values() if e['row']['kind']=='font' and e['row']['disposition']=='held']
        if self.case.get('variant')!='font-fallback' and (not held or not loading):
            raise DiagnosticError('baseline lacks held font demand/loading during fixed window')
        self.phase, self.released, self.deadline = 'settlement', True, time.monotonic()+15
        self.record['settlementDeadlineMonotonic'] = self.deadline
        for entry in held:
            self._budget(self.deadline, 'settlement')
            self._dispose_route(entry,'continue')
            self.check()
        while True:
            self._budget(self.deadline, 'settlement/custody')
            self._custody()
            observation, applied = self._observation(frame, applied=True)
            self._budget(self.deadline, 'settlement/custody')
            if not applied: raise DiagnosticError('CSS application lost during settlement')
            state=observation['fontSettlement']
            if state.get('settled') is True and state.get('pendingDeferred')==0 and self._complete(): break
            self.page.wait_for_timeout(min(50, max(1,(self.deadline-time.monotonic())*1000)))
        observation['phase']='after-fonts'; self.record['observations'].append(observation)
        self.phase='presentation-tail'

    def finalize(self, frame):
        try: self._finalize(frame)
        except Exception as error:
            self._latch(error, 'finalize')
            raise sanitized_exception(error) from None

    def _finalize(self, frame):
        self.phase='finalizing'
        self.check()
        if self.deadline is None: raise DiagnosticError('no settlement/custody phase')
        # Capture only already-finished late transactions; never wait at this cut.
        self._custody()
        observation, applied = self._observation(frame, 'post-tail-cut', applied=True)
        state=observation['fontSettlement']
        if not applied or state.get('settled') is not True or state.get('pendingDeferred')!=0 or not self._complete():
            raise DiagnosticError('late incomplete native transaction/observer at finalization')
        self.check()
        self.record['finalization']={'status':'FINALIZED','atMonotonic':time.monotonic(),
                                     'requestCount':len(self.requests)}
        self.phase='finalized'

    def _abort_pending(self):
        for route in list(self.pending_routes):
            if route in self.abort_attempted: continue
            self.abort_attempted.add(route)
            entry = next((e for e in self.requests.values() if e['route'] is route), None)
            if entry is not None:
                try: self._dispose_route(entry,'abort')
                except Exception as error: self._latch(error,'route-abort',entry['row'])
            else:
                attempt={'action':'abort','returned':False,'atMonotonic':time.monotonic()}
                self.record.setdefault('unassociatedRouteCleanup',[]).append(attempt)
                try:
                    route.abort()
                    attempt['returned']=True
                    self.pending_routes.remove(route)
                except Exception as error:
                    attempt['error']=error_text(error);attempt['errorDetails']=error_receipt(error)
                    self._latch(error,'unassociated-route-abort')

    def close(self):
        if self.closed is not None: return self.closed
        self.phase='closing'
        if self.media_frame is not None:
            try:
                receipt=self._evaluate(self.media_frame,MEDIA_CONTROL,{'operation':'close','url':CSS_URL},'media-close')
                self.record['mediaClose']=receipt
                self._media_receipt(receipt)
                if not receipt.get('closed') or not receipt.get('disconnected'):
                    raise DiagnosticError('media observer cleanup incomplete')
            except Exception as error:self._latch(error,'media-close')
        self._abort_pending()
        self._dispose_api()
        for pattern, callback in self.routes:
            try: self.page.unroute(pattern,callback)
            except Exception as error: self._latch(error,'unroute')
        self._abort_pending()
        for event, callback in self.listeners:
            try: self.page.remove_listener(event,callback)
            except Exception as error: self._latch(error,'remove-listener')
        self.closed={'status':'FAILED' if self.record['errors'] else 'CLOSED','atMonotonic':time.monotonic(),
                     'errors':list(self.record['errors'])}
        self.record['close']=self.closed
        self.phase='closed'
        return self.closed
