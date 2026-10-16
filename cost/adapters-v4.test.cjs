'use strict';
// Synthetic native delegates only: this does not launch a browser or measure product cost.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Target extends EventTarget{addEventListener(...a){return super.addEventListener(...a);}removeEventListener(...a){return super.removeEventListener(...a);}}
class DomNode extends Target{}
class Canvas extends DomNode{constructor(){super();this._w=300;this._h=150;}get width(){return this._w;}set width(v){this._w=Number(v);}get height(){return this._h;}set height(v){this._h=Number(v);}}
class Doc extends DomNode{constructor(){super();this.fonts=Object.assign([],{status:'loaded',check:()=>true});this.visibilityState='visible';}createElement(tag){return tag==='canvas'?new Canvas():new DomNode();}querySelector(){return null;}querySelectorAll(){return [];}}
class NativeWorker extends Target{constructor(url){super();this.url=url;this.sent=[];}postMessage(...a){if(a[0]==='throw')throw new Error('native-post');this.sent.push(a);return 'sent';}terminate(){this.dead=true;return 'terminated';}}
let seq=0,clock=0;const raf=new Map(),timers=new Map();
const context={module:{exports:{}},performance:{now:()=>++clock/1000},EventTarget:Target,Node:DomNode,HTMLCanvasElement:Canvas,Document:Doc,Worker:NativeWorker,document:new Doc(),devicePixelRatio:1,innerWidth:390,innerHeight:600,Date,Intl,structuredClone,WeakRef,ArrayBuffer,Float32Array,Float64Array,Uint8Array,Uint16Array,Map,WeakMap,WeakSet,Set};
context.window=context;
context.requestAnimationFrame=fn=>{raf.set(++seq,fn);return seq;};context.cancelAnimationFrame=id=>{raf.delete(id);return 'cancelled';};
for(const type of ['Timeout','Interval']){context['set'+type]=(fn,delay,...args)=>{timers.set(++seq,{fn,args,type});return seq;};context['clear'+type]=id=>{timers.delete(id);return 'cleared';};}
vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/probe-v4.js','utf8'),context);
const receiver={receiver:true};let called=[];
const id=context.requestAnimationFrame(function(t){called.push([this,t]);return 17;});assert.equal(raf.get(id).call(receiver,42),17);assert.equal(called[0][0],receiver);assert.equal(called[0][1],42);
const cancel=context.requestAnimationFrame(()=>assert.fail('cancelled callback'));assert.equal(context.cancelAnimationFrame(cancel),'cancelled');assert(!raf.has(cancel));
const fail=context.requestAnimationFrame(()=>{throw new Error('native-raf');});assert.throws(()=>raf.get(fail).call(receiver,43),/native-raf/);
const tid=context.setTimeout(function(a,b){assert.equal(this,receiver);assert.deepEqual([a,b],[3,4]);return 19;},5,3,4);const timer=timers.get(tid);assert.equal(timer.fn.apply(receiver,timer.args),19);
const int=context.setInterval(function(){return this;},5);assert.equal(timers.get(int).fn.call(receiver),receiver);assert.equal(context.clearTimeout(int),'cleared');
const cancelledTimer=context.setTimeout(()=>assert.fail(),5);assert.equal(context.clearInterval(cancelledTimer),'cleared');assert(!timers.has(cancelledTimer));
const target=new Target();let count=0,who;
function listener(){count++;who=this;}
target.addEventListener('x',listener);target.addEventListener('x',listener,{once:true});target.dispatchEvent(new Event('x'));target.dispatchEvent(new Event('x'));assert.equal(count,2);assert.equal(who,target);
target.removeEventListener('x',listener);target.dispatchEvent(new Event('x'));assert.equal(count,2);
target.addEventListener('x',listener,{once:true});target.dispatchEvent(new Event('x'));target.dispatchEvent(new Event('x'));assert.equal(count,3);
const ctl=new AbortController();target.addEventListener('x',listener,{signal:ctl.signal,once:true});ctl.abort();target.addEventListener('x',listener);target.dispatchEvent(new Event('x'));target.dispatchEvent(new Event('x'));assert.equal(count,5);target.removeEventListener('x',listener);
const object={handleEvent(){assert.equal(this,object);count++;}};target.addEventListener('o',object,{once:true});target.dispatchEvent(new Event('o'));target.dispatchEvent(new Event('o'));assert.equal(count,6);
const worker=new context.Worker('blob:owned');assert(worker instanceof NativeWorker);const transfer=[];assert.equal(worker.postMessage({kind:'render'},transfer),'sent');assert.equal(worker.sent[0][1],transfer);assert.throws(()=>worker.postMessage('throw'),/native-post/);
const boot=Object.freeze({kind:'boot',base:'http://127.0.0.1:54321/salah_widget/moon/',offline:false,workerSource:'source'});worker.postMessage(boot,transfer);assert.equal(worker.sent.at(-1)[0],boot);assert.equal(worker.sent.at(-1)[1],transfer);
worker.dispatchEvent(new MessageEvent('message',{data:{kind:'ready'}}));const job=Object.freeze({id:2,key:'current',epoch:1});worker.dispatchEvent(new MessageEvent('message',{data:Object.freeze({kind:'result',id:2,identity:job})}));worker.dispatchEvent(new Event('message'));assert.equal(worker.terminate(),'terminated');
const observed=context.__r21.snapshot().workers[0];assert.equal(observed.readyCount,1);assert.equal(observed.boot.base,boot.base);assert.equal(observed.boot.workerSourceLength,6);assert.deepEqual(JSON.parse(JSON.stringify(observed.lastResult.identity)),job);assert(observed.boot.at<observed.readyAt&&observed.readyAt<observed.lastResult.at);assert.equal(observed.errors.length,0);assert.equal(observed.terminated,true);
const canvas=context.document.createElement('canvas');canvas.width=640;canvas.height=320;assert.equal(canvas.width,640);assert.equal(canvas.height,320);
const buffer=new Float32Array(3);context.__r21.registerOwner('test',()=>({buffer,alias:buffer.subarray(1),rules:[[1,2],[3,4]],canvas,disposed:false}));
let snap=context.__r21.snapshot();const inv=snap.owners.test.inventory.arraysAndCanvases;assert.equal(new Set(inv.filter(x=>x.bufferId).map(x=>x.bufferId)).size,1);assert(inv.some(x=>x.type==='Array'&&x.length===2));assert.equal(snap.owners.test.instanceCount,1);assert.equal(snap.counts.rafExecuted,2);assert.equal(snap.counts.workerMessagesIn,3);assert.equal(snap.counts.canvasResizeWrites,2);
context.__r21.registerOwner('test',()=>({disposed:true}));assert.equal(context.__r21.snapshot().owners.test.instanceCount,2);
console.log('PASS: RAF receiver/return/throw/cancel; timeout arguments/receiver/cross-cancel; listener duplicate/once/remove/abort-readd/object; Worker return/throw/transfer/terminate; canvas setters; unique buffers/array lengths/duplicate owners');
