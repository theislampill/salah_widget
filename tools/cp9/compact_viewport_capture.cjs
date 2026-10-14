'use strict';
// Version-bound QA preload: native pixels for an actually received unfinished head.
// It neither modifies the HTML/DOM nor makes a product-readiness/timing claim.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const PINS={
 'lib/server/screenshotter.js':'9aaff6c173c6a9a1c80e831dd92ccc24097243d49ad600dc87c4bc1fad9c625b',
 'lib/server/chromium/crPage.js':'71aab16b0912f23cb9aa3095b8072bfc6fbd6e47e4e13a7be3684b796aa1cd28',
 'lib/server/firefox/ffPage.js':'e3722511c4bff1a88a91f4909e6c127a64141577add8b32525aee9ea58781f21',
 'lib/server/page.js':'1837b232c356095f405b25a836031737fb7646247aae8e033c62dd861d2a345a',
 'lib/server/frames.js':'707fc3b31832b9fba8abfca3b788232404349714a5cc5e3af0c2250892ee767e',
 'types/protocol.d.ts':'b34209befaf07b7cc1932e5cc137ce121cbc9f892551126962d9e908be91adb4',
 'package.json':'3fab71772897b5ba5739aee60001d5eb82e28f903bfc82ca93f39b4194d8ce58'
};
const READ="(() => {const s=document.getElementById('moon-initial-code'),v=window.visualViewport;return {readyState:document.readyState,bodyPresent:!!document.body,cardPresent:!!document.querySelector('.c'),receiverPresent:!!window.SalahMoonInitial,runtimePresent:!!window.SalahMoonRuntime,href:location.href,width:innerWidth,height:innerHeight,dpr:devicePixelRatio,scrollX,scrollY,visualScale:v?.scale??null,visualOffsetLeft:v?.offsetLeft??null,visualOffsetTop:v?.offsetTop??null,visualPageLeft:v?.pageLeft??null,visualPageTop:v?.pageTop??null,scriptPresent:!!s,scriptText:s?.textContent??null};})()";
function bound(value,spec){
 const u=new URL(value.href),text=value.scriptText;
 assert(u.protocol==='http:'&&u.hostname==='127.0.0.1'&&u.pathname==='/index.html','Unexpected capture target');
 assert(value.readyState==='loading'&&value.bodyPresent===false&&value.cardPresent===false,'Unfinished bodyless head required');
 assert(value.receiverPresent===false&&value.runtimePresent===false,'Receiver/runtime cannot execute before release');
 assert(value.width===390&&value.height===600&&value.dpr===1,'Only existing 390x600/DPR1 diagnostic viewport');
 assert(value.scrollX===0&&value.scrollY===0&&value.visualScale===1&&value.visualOffsetLeft===0&&value.visualOffsetTop===0&&value.visualPageLeft===0&&value.visualPageTop===0,'Unscrolled unzoomed viewport origin required');
 assert(value.scriptPresent===true&&typeof text==='string','Actual received script required');
 assert(Buffer.byteLength(text,'utf8')===spec.prefixBytes&&sha(Buffer.from(text,'utf8'))===spec.prefixSha256,'Received prefix drift');
 return {...value,scriptText:undefined,prefixBytes:spec.prefixBytes,prefixSha256:spec.prefixSha256};
}
function install(Screenshotter,spec,sink,log){
 assert(spec.viewport.width===390&&spec.viewport.height===600&&spec.viewport.dpr===1);
 const marker=Symbol.for('salah.f1.compact.native.capture');assert(!Screenshotter.prototype[marker],'Duplicate capture preload');
 Screenshotter.prototype[marker]=true;const original=Screenshotter.prototype.screenshotPage;let ordinal=0;
 Screenshotter.prototype.screenshotPage=async function(progress,options){
  const read=()=>progress.race(this._page.mainFrame().nonStallingRawEvaluateInExistingMainContext(READ));
  const initial=await read();
  // Completed/recovery pages keep the existing screenshotter, including its gates.
  if(initial.bodyPresent===true||initial.readyState!=='loading')return original.call(this,progress,options);
  return this._queue.postTask(async()=>{
   const before=bound(await read(),spec);
   assert(!options.fullPage&&!options.clip&&!options.style&&!options.mask?.length&&!options.omitBackground&&(!options.type||options.type==='png'),'Plain viewport PNG only');
   const delegate=this._page.delegate,name=delegate.constructor.name;
   let method,args,session;
   if(name==='CRPage'){
    method='Page.captureScreenshot';session=delegate._mainFrameSession._client;
    args={format:'png',fromSurface:false,captureBeyondViewport:false,clip:{x:0,y:0,width:390,height:600,scale:1}};
   }else if(name==='FFPage'){
    method='Page.screenshot';session=delegate._session;
    args={mimeType:'image/png',clip:{x:0,y:0,width:390,height:600},omitDeviceScaleFactor:false};
   }else throw Error('Only pinned Chromium/Firefox delegates');
   log({stage:'native-command-enter',method,args});progress.log('F1 compact native command '+method+' entered');
   // The existing caller progress owns the unchanged 30s screenshot budget.
   const response=await progress.race(session.send(method,args));
   log({stage:'native-send-resolved',method});
   const pixels=Buffer.from(response.data,'base64');
   log({stage:'post-capture-read-enter',method});
   const afterRead=await read();
   log({stage:'post-capture-read-resolved',method});
   const after=bound(afterRead,spec);
   assert(after.href===before.href,'Capture target changed');
   assert(pixels.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))&&pixels.toString('ascii',12,16)==='IHDR','Native response is not PNG');
   assert(pixels.readUInt32BE(16)===390&&pixels.readUInt32BE(20)===600,'Native PNG viewport mismatch');
   const receipt={schema:'f1-held-native-viewport-pixels/1',ordinal:++ordinal,method,args,
    captureKind:name==='CRPage'?'browser-view-copy-fromSurface-false':'native-Firefox-screenshot-fixed-clip',
    before,after,pngSha256:sha(pixels),pngBytes:pixels.length,width:390,height:600,dpr:1,
    firstCompositorFrameProof:false,ordinaryStartupTimingProof:false};
   sink(receipt);log({stage:'native-command-return',method,pngSha256:receipt.pngSha256});
   return pixels;
  });
 };
}
module.exports={install,bound,PINS,READ};
if(process.env.SALAH_F1_CAPTURE_SPEC){
 const specPath=path.resolve(process.env.SALAH_F1_CAPTURE_SPEC),spec=JSON.parse(fs.readFileSync(specPath,'utf8'));
 assert(spec.schema==='f1-compact-native-capture-spec/1');
 assert(sha(fs.readFileSync(__filename))===spec.hookSha256,'Capture hook drift');
 for(const [relative,expected] of Object.entries(PINS))assert(sha(fs.readFileSync(path.join(spec.playwrightPackage,relative)))===expected,'Installed source drift: '+relative);
 assert(spec.prefixBytes===61356&&spec.prefixSha256==='17956826a1a4f8986cffb3555d7b5cbd1456a770cfc204ffa1ba73918a85e26c');
 const receipts=path.resolve(spec.receiptsDir);assert(path.dirname(receipts)===path.dirname(specPath),'Receipt path outside admitted output');
 fs.mkdirSync(receipts,{recursive:false});
 const sink=r=>fs.writeFileSync(path.join(receipts,String(r.ordinal).padStart(4,'0')+'.json'),JSON.stringify(r,null,2)+'\n',{encoding:'utf8',flag:'wx'});
 const log=r=>process.stderr.write('F1_COMPACT_NATIVE_CAPTURE '+JSON.stringify(r)+'\n');
 install(require(path.join(spec.playwrightPackage,'lib/server/screenshotter.js')).Screenshotter,spec,sink,log);
}
