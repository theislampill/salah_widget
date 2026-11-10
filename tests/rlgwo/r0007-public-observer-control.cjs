/* Pure observer-program controls. DOM/events/fonts/rAF below are explicit doubles;
   this is never native rendering, font loading, or presentation evidence. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(0,'utf8');
async function run(){
 const listeners={},events=[],link={tagName:'LINK',rel:'stylesheet',href:'https://fonts.googleapis.com/css2?family=Inter&display=swap',media:'print',disabled:false,sheet:null};
 const fontListeners={};const face={family:'Inter',style:'normal',weight:'400',status:'loading'};
 let resolveFonts,clock=0;const fonts={status:'loading',ready:new Promise(resolve=>{resolveFonts=resolve;}),addEventListener(type,fn){fontListeners[type]=fn;},*[Symbol.iterator](){yield face;}};
 const box={x:1,y:2,width:325,height:530},element={textContent:'fixture',innerHTML:'fixture',tagName:'DIV',getBoundingClientRect(){events.push('read-only-geometry');return box;}};
 const document={readyState:'loading',fonts,addEventListener(){},querySelectorAll(selector){return selector==='link[rel="stylesheet"]'?[link]:[];},querySelector(){return element;}};
 const window={Date,setTimeout,addEventListener(type,fn){listeners[type]=fn;},qaState(){events.push('actual-last-render-read');return {render:{atMs:123,nextKey:'Isha',remainingMinutes:91}};},render(){throw Error('product render must never run');}};
 const context={window,Date,document,URL,WeakMap,JSON,Number,Promise,Error,performance:{now:()=>clock},setTimeout,clearTimeout,
  requestAnimationFrame(callback){setTimeout(()=>{clock+=16;callback(clock);},0);}};
 vm.runInNewContext(source.replace('__EPOCH__','1788822000000'),context);
 const P=window.__r0007PublicDelivery;
 assert.equal(P.fontState().cssReady,false,'pending authored link must not be settled');
 listeners.load({target:link,isTrusted:false});link.media='all';link.sheet={};
 assert.equal(P.fontState().cssReady,false,'synthetic load must not create terminal receipt');
 link.media='print';listeners.load({target:link,isTrusted:true});
 assert.equal(P.fontState().cssReady,false,'trusted load alone does not prove authored media application');
 link.media='all';assert.equal(P.fontState().cssReady,true);
 let completed=false;const awaiting=P.awaitTypography().then(x=>{completed=true;return x;});
 await new Promise(resolve=>setTimeout(resolve,0));assert.equal(completed,false,'must await actual fonts.ready promise');
 fonts.status='loaded';face.status='loaded';resolveFonts();const receipt=await awaiting;
 assert.equal(receipt.dirtyState,'not-exposed');assert.ok(receipt.readyPromiseFulfilled||receipt.settled,'font promise returned');
 assert.equal(window.__r0007FontSettlement.settled(),false,'ready/status alone cannot credit a missing terminal event');
 let stableCompleted=false;const pendingStable=P.observeStable().then(value=>{stableCompleted=true;return value;});
 for(let i=0;i<5;i++)await new Promise(resolve=>setTimeout(resolve,0));
 assert.equal(stableCompleted,false,'public stable-render barrier cannot accept ready-before-terminal-event');
 fontListeners.loadingdone({fontfaces:[face]});events.push('later-product-font-listener-returned');
 assert.equal(window.__r0007FontSettlement.settled(),false,'dispatch receipt cannot be credited until deferred native task');
 assert.equal(window.__r0007FontSettlement.read().pendingDeferred,1);
 await new Promise(resolve=>setTimeout(resolve,0));
 assert.equal(window.__r0007FontSettlement.settled(),true);
 assert.equal(window.__r0007FontSettlement.read().events.at(-1).kind,'deferred-receipt');
 const stable=await pendingStable;assert.equal(stable.observations.length,3);assert.equal(stable.dirtyState,'not-exposed');
 assert.ok(events.includes('read-only-geometry'));assert.ok(events.includes('actual-last-render-read'));
 link.sheet=null;link.media='print';listeners.error({target:link,isTrusted:true});
 assert.equal(P.fontState().cssReady,true,'genuine CSS error may settle honest native fallback');
 assert.equal(P.fontState().links[0].receipt.type,'error');
 console.log(JSON.stringify({status:'PASS_PURE_OBSERVER_CONTROLS',checks:['pending-link','untrusted-event','media-application','actual-fonts-ready-promise','ready-before-terminal-event-rejected','dispatch-before-deferred-receipt-rejected','typed-deferred-event-settlement','read-only-geometry','stable-native-callback-observation','genuine-error-fallback'],nativeExecutions:0,networkRequests:0}));
}
run().catch(error=>{console.error(error);process.exitCode=1;});
