// Test-only native transport redirect and actual HTMLImageElement observer, before product parsing.
function transportFetch(kind,input,init,row){
  const target=new URL('/transport',location.href),t=caseSpec.transport;
  const number=report.ledger.filter(value=>value.transport?.kind===kind).length+1;
  const policy=t.abortPolicy||'native-signal';
  if(!['native-signal','ignore-old-weather-signal'].includes(policy))throw Error('Closed transport abort policy required');
  if(policy==='ignore-old-weather-signal'&&(t.stage!=='weather-body'||!['ignored-abort','superseded-target'].includes(t.gap)))
    throw Error('Ignored signal is restricted to the two reviewed weather-body controls');
  const signal=init?.signal,ignore=policy==='ignore-old-weather-signal'&&kind==='weather'&&number===1;
  if(ignore&&!signal)throw Error('Ignored-abort control requires the actual captured product AbortSignal');
  target.search=new URLSearchParams({run:t.run,document:documentId,case:caseId,kind,clientNow:String(fixtureNow())});
  row.transport={kind,number,document:documentId,clientNow:fixtureNow(),realDispatchAt:NativeDate.now(),
    realTryAt:kind==='weather'&&typeof lastWxTry==='number'?lastWxTry-clockNow+realEpoch:null,
    generationAtDispatch:typeof _runtimeGeneration==='number'?_runtimeGeneration:null,
    operationAtDispatch:typeof _wxRequests==='object'?_wxRequests[kind==='weather'?'weather':'radar']?.operationId??null:null,
    abortPolicy:policy,signalCaptured:!!signal,signalPassed:!!signal&&!ignore};
  row.signalEvents=[];
  if(signal)signal.addEventListener('abort',()=>row.signalEvents.push({at:performance.now(),aborted:signal.aborted}),{once:true});
  row.result='native-loopback-requested';
  const headers=new Headers(init?.headers);headers.set('X-Weather-Test-Token',t.token);
  const transportInit={...init,headers};
  if(ignore)delete transportInit.signal; // Only this old transport signal changes; product abort/deadline/finalizers stay real.
  return nativeFetch(target,transportInit).then(response=>{
    row.status=response.status;row.result='native-loopback-headers';row.nativeResponse=response instanceof Response;
    const nativeJson=response.json.bind(response);
    response.json=()=>{
      row.jsonReads++;row.bodyStartedAt=performance.now();
      return nativeJson().then(value=>{row.bodySettledAt=performance.now();row.bodyOutcome='fulfilled';return value;},error=>{
        row.bodySettledAt=performance.now();row.bodyOutcome='rejected';row.bodyError=String(error);throw error;
      });
    };
    return response;
  },error=>{row.fetchSettledAt=performance.now();row.fetchOutcome='rejected';row.fetchError=String(error);throw error;});
}
function installTransportImageObserver(){
  const descriptor=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src'),events=[];
  if(!descriptor?.set||!descriptor.configurable)throw Error('Native Image src observer unsupported');
  Object.defineProperty(HTMLImageElement.prototype,'src',{...descriptor,set(value){
    if(String(value).includes('/transport-tile/')){
      const row={image:this,url:String(value),startedAt:performance.now(),onloadSource:String(this.onload),onerrorSource:String(this.onerror),nativeLoads:[],nativeErrors:[]};
      this.addEventListener('load',()=>row.nativeLoads.push(performance.now()));
      this.addEventListener('error',()=>row.nativeErrors.push(performance.now()));events.push(row);
    }
    descriptor.set.call(this,value);
  }});
  window.__weatherTransportImages=()=>events.map(row=>({url:row.url,startedAt:row.startedAt,onloadSource:row.onloadSource,onerrorSource:row.onerrorSource,
    handlersDetached:row.image.onload===null&&row.image.onerror===null,nativeImage:row.image instanceof HTMLImageElement,
    nativeLoads:row.nativeLoads.slice(),nativeErrors:row.nativeErrors.slice(),complete:row.image.complete,naturalWidth:row.image.naturalWidth}));
}
