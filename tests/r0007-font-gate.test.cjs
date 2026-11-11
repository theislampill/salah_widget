'use strict';
// Browser-free controls for the authored web-font activation gate. Synthetic
// FontFaceSet/link doubles prove the gate's ordering and fail-closed policy only;
// they do not certify native pixels or a real font-service observation.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../src/native/index.html'),'utf8').replace(/\r\n/g,'\n');
const style=source.slice(source.indexOf('<style>'),source.indexOf('</style>'));
const START='// Optional web typography.',END='// Size the present-prayer name';
const FACES=['400 14px Inter','600 14px Inter','600 14px Fraunces'];
const WEB=/\b(Inter|Fraunces)\b/;

function rules(css){
 const out=[];css.replace(/\/\*[\s\S]*?\*\//g,'').replace(/([^{}]+)\{([^{}]*)\}/g,(_,selector,body)=>{out.push({selector:selector.trim(),body});return _;});
 return out;
}
function gateCode(){
 const start=source.indexOf(START),end=source.indexOf(END);
 assert.ok(start>0&&end>start,'authored activation gate precedes the name-fit cache');
 const fontChanged=source.match(/function cnFontChanged\(\)\{[^}]+\}/)[0];
 return source.slice(start,end)+'\n'+fontChanged;
}
function scene({media='print',linkPresent=true,loads=null}={}){
 const calls=[],settlers=[],classes=new Set(),linkListeners=[];
 const link={media,addEventListener(type,fn){assert.equal(type,'load');linkListeners.push(fn);}};
 const fonts={load(descriptor){calls.push(descriptor);
  if(loads)return loads(descriptor);
  return new Promise((resolve,reject)=>settlers.push({descriptor,resolve,reject}));}};
 const document={fonts,documentElement:{classList:{add:c=>classes.add(c),contains:c=>classes.has(c)}},
  getElementById:id=>linkPresent&&id==='webfont-css'?link:null};
 const context=vm.createContext({document,Object,Promise,_cnFit:'cached-fallback-fit',_renderDirty:false});
 vm.runInContext(gateCode(),context);
 return {calls,settlers,classes,context,
  // The authored attribute handler runs first, then any listener added later.
  loadStylesheet(){link.media='all';for(const fn of linkListeners)fn({type:'load'});},
  async settle(){await new Promise(r=>setImmediate(r));}};
}

test('initial custom properties name no web-font family; activation adds the current full stacks',()=>{
 const all=rules(style);
 const body=all.find(r=>r.selector==='body');
 assert.ok(body,'body rule exists');
 assert.match(body.body,/--font-body:system-ui,-apple-system,"Segoe UI",sans-serif;/);
 assert.match(body.body,/--font-display:Georgia,"Times New Roman",serif;/);
 const gated=all.filter(r=>WEB.test(r.body));
 assert.deepEqual(gated.map(r=>r.selector),['html.webfonts body'],'only the activated rule names a web family');
 assert.ok(gated[0].body.includes('--font-body:"Inter",system-ui,-apple-system,"Segoe UI",sans-serif;'));
 assert.ok(gated[0].body.includes('--font-display:"Fraunces",Georgia,"Times New Roman",serif;'));
 for(const r of all)if(/font-family\s*:/.test(r.body))
  assert.doesNotMatch(r.body.match(/font-family\s*:[^;]*/)[0],WEB,r.selector+' must use the gated custom properties');
 const dialogHeading=all.find(r=>r.selector==='.date-dialog h2');
 assert.match(dialogHeading.body,/font-family:var\(--font-display\)/);
});

test('stylesheet stays non-blocking and its attribute handler is unchanged',()=>{
 const tag=source.match(/<link[^>]*href="https:\/\/fonts\.googleapis\.com\/css2[^>]*>/)[0];
 assert.match(tag,/ id="webfont-css"/);
 assert.match(tag,/ media="print"/);
 assert.match(tag,/ onload="this\.media='all'"/);
});

test('no face is requested before the stylesheet applies; activation waits for every requested load',async()=>{
 const s=scene();
 await s.settle();
 assert.deepEqual(s.calls,[],'nothing is requested while the stylesheet is pending');
 s.loadStylesheet();
 assert.deepEqual(s.calls,FACES,'exactly the faces used by visible UI');
 for(const [index,settler] of s.settlers.slice(0,2).entries()){
  settler.resolve([{family:'face'+index}]);await s.settle();
  assert.equal(s.classes.has('webfonts'),false,'partial loads keep fallback stacks');
  assert.equal(s.context._cnFit,'cached-fallback-fit');
 }
 s.settlers[2].resolve([{family:'Fraunces'}]);await s.settle();
 assert.equal(s.classes.has('webfonts'),true,'all loads non-empty activates the full stacks');
 assert.equal(s.context._cnFit,'','activation invalidates the .cn fit cache');
 assert.equal(s.context._renderDirty,true,'activation schedules the re-fit render');
 s.loadStylesheet();assert.equal(s.calls.length,3,'a later load event requests nothing again');
});

test('a rejected or empty load leaves fallback stacks permanently with no retry',async()=>{
 for(const failing of [d=>d.includes('Fraunces')?Promise.resolve([]):Promise.resolve([{}]),
                       d=>d.startsWith('600 14px Inter')?Promise.reject(new Error('network')):Promise.resolve([{}]),
                       ()=>{throw new Error('syntax');}]){
  const s=scene({loads:failing});
  s.loadStylesheet();await s.settle();await s.settle();
  assert.equal(s.classes.has('webfonts'),false);
  assert.equal(s.context._cnFit,'cached-fallback-fit','failure does not invalidate the fallback fit');
  const before=s.calls.length;s.loadStylesheet();await s.settle();
  assert.equal(s.calls.length,before,'no retry');
 }
});

test('stylesheet already applied before the script runs is requested at once; a missing load never is',async()=>{
 const early=scene({media:'all',loads:()=>Promise.resolve([{}])});
 assert.deepEqual(early.calls,FACES);
 await early.settle();assert.equal(early.classes.has('webfonts'),true);
 const never=scene();await never.settle();
 assert.deepEqual(never.calls,[]);assert.equal(never.classes.has('webfonts'),false);
 const absent=scene({linkPresent:false});await absent.settle();
 assert.deepEqual(absent.calls,[]);
});
