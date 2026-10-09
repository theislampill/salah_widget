'use strict';
// Preparation only. Imports original repository fixtures without starting their
// servers, adapts only local asset transport/export anchors, writes under B.
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const ROOT='C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget';
const OUT=path.join(__dirname,'browser-fixtures'),TARGET='18ff14860ff41c084b1db5f396bb62aa9c22b1be';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const source=fs.readFileSync(path.join(ROOT,'index.html'),'utf8');
assert.equal(sha(Buffer.from(source)),'ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee');
const secFile=path.join(ROOT,'tests/r0001-browser-fixture.cjs'),secSource=fs.readFileSync(secFile,'utf8');
const secModule=new Module(secFile,module);secModule.filename=secFile;secModule.paths=Module._nodeModulePaths(path.dirname(secFile));
secModule._compile(secSource+'\nmodule.exports.documentFixture=documentFixture;\n',secFile);
const security=secModule.exports;
const calendar=require(path.join(ROOT,'tests/r0009-browser-fixture.cjs'));
const {record}=require(path.join(ROOT,'tests/r0009-calendar-harness.cjs'));
const {mutateDate}=require(path.join(ROOT,'tests/r0009-date-mutations.cjs'));
const {ordinary,polar,clone}=require(path.join(ROOT,'tests/r0002-harness.cjs'));
const CANARY=security.CANARY,rows=[];
fs.mkdirSync(OUT,{recursive:true});
function once(text,before,after){assert.equal(text.split(before).length-1,1,'one isolated adaptation anchor');return text.replace(before,after);}
function localFetch(page,kind){
  const opening=kind==='security'?'window.fetch=async input=>{':'window.fetch=input=>{';
  page=once(page,opening,'const retainedFixtureLocalFetch=window.fetch.bind(window);\n'+opening);
  const anchor=kind==='security'?'window.__uiFixture.requests.push(url.href);':'requests.push(url.href);';
  return once(page,anchor,anchor+'\n      if(url.origin===location.origin)return retainedFixtureLocalFetch(input);');
}
function emit(id,issue,html,hash,meta={}){
  assert.equal(html.split('\nboot().then(()=>setTimeout(render,0));').length-1,1,'original real boot-and-final-render hook retained');
  for(const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g))if(script[1].trim())new vm.Script(script[1]);
  const file=id+'.html';fs.writeFileSync(path.join(OUT,file),html);
  rows.push({id,issue,file,hash,fixtureSha256:sha(html),sourceSha256:sha(source),...meta});
}
const securityCases=[
  ['ordinary','ordinary','YYYY-MM-DD','12:30',null],
  ['hash-format','hash-format',CANARY,'12:30',null],
  ['saved-format','saved-format',null,'12:30',null],
  ['provider-month','provider-month','DD MMMM YYYY','12:30',null],
  ['preview-day','preview-day','YYYY-MM-DD','12:30',null],
  ['after-maghrib','provider-month','DD MMMM YYYY','19:00',null],
  ['held-out-tokens','ordinary','YYYY YY MMMM MMM MM M DD D','12:30',null],
  ['literal-control','ordinary','التاريخ "\' & < > YYYY','12:30',null],
  ['stale-control','stale',CANARY,'12:30',null],
  ['ce-mutant','hash-format',CANARY,'12:30','ce'],
  ['ah-mutant','hash-format',CANARY,'12:30','ah'],
  ['preview-mutant','preview-day','YYYY-MM-DD','12:30','preview']
];
for(const [name,testCase,format,time,mutant] of securityCases){
  let hash=testCase==='saved-format'?'#local=1&tz=Asia%2FRiyadh&simTime='+time+'&simWx=0&motion=full':security.HASH.replace('simTime=12:30','simTime='+time)+'&datefmt='+encodeURIComponent(format);
  const page=localFetch(security.documentFixture(source,{testCase,mutant}), 'security');
  emit('r0001-'+name,1,page,hash,{kind:'security',name,testCase,mutant,expectedConfigSource:testCase==='saved-format'?'localStorage':'hash'});
}
// Keep the original declared calendar cases and input data. Primary may select
// just issue9's non-long cases; retained source suite covers the other branches.
for(const name of calendar.cases){
  const spec=calendar.spec(name),page=localFetch(calendar.buildPage(source,spec),'calendar');
  emit('r0009-'+name,9,page,calendar.routeHash(spec),{kind:'calendar',name,spec});
}
for(const [name,mutation] of [['title-mutant','after-only-title'],['hold-mutant','backwards-hold']]){
  const spec=calendar.spec(name==='title-mutant'?'missing':'before');
  if(name==='hold-mutant'){spec.today=record('07','10');spec.tomorrow=record('08','11');}
  emit('r0009-'+name,9,localFetch(calendar.buildPage(mutateDate(source,mutation),spec),'calendar'),calendar.routeHash(spec),{kind:'calendar',name,spec,mutant:mutation});
}
// Full captured arc controls are copied from the already-executed existing
// r000a marker test. No replacement drawArc/model/elevation is injected.
function dayAfter(data){
  const next=clone(data),g=data.date.gregorian,d=new Date(0);
  d.setUTCFullYear(+g.year,+g.month.number-1,+g.day+1);const dd=String(d.getUTCDate()).padStart(2,'0'),mm=String(d.getUTCMonth()+1).padStart(2,'0'),yy=String(d.getUTCFullYear());
  next.date.gregorian={...g,date:dd+'-'+mm+'-'+yy,day:dd,month:{...g.month,number:d.getUTCMonth()+1},year:yy};return next;
}
const london=clone(ordinary);london.date.gregorian={date:'21-06-2026',day:'21',month:{number:6,en:'June'},year:'2026'};
london.timings={Fajr:'02:31',Sunrise:'04:43',Dhuhr:'13:02',Asr:'17:25',Sunset:'21:22',Maghrib:'21:22',Isha:'23:27'};
london.meta={timezone:'Europe/London',method:{id:3,params:{Fajr:18,Isha:17}},latitudeAdjustmentMethod:'ANGLE_BASED'};
const tromso=polar('summer').envelope.data;
const madinah=clone(ordinary);madinah.timings={Fajr:'04:46',Sunrise:'06:05',Dhuhr:'12:20',Asr:'15:49',Sunset:'18:34',Maghrib:'18:34',Isha:'20:04'};
madinah.meta={timezone:'Asia/Riyadh',method:{id:4,params:{Fajr:18.5,Isha:'90 min'}},latitudeAdjustmentMethod:'ANGLE_BASED'};
for(const [name,data,lat,lon,clock] of [
 ['london',london,51.5074,-0.1278,'2026-06-21T11:00:00Z'],
 ['tromso',tromso,69.6492,18.9553,'2026-06-21T10:00:00Z'],
 ['madinah',madinah,24.47,39.61,'2026-09-07T09:00:00Z']
])for(const mutant of name==='london'?[null,'universal-14']: [null]){
  const spec={...calendar.spec('before'),name:'marker-'+name,clock,zone:data.meta.timezone,today:data,tomorrow:dayAfter(data)};
  let input=source;if(mutant)input=once(input,'const adj = classification&&classification.status==="unreachable-angle";','const adj = minRealE > -14 && (p.k==="Fajr"||p.k==="Isha");');
  const hash='#lat='+lat+'&lon='+lon+'&label='+name+'&method='+data.meta.method.id+'&tz='+encodeURIComponent(spec.zone)+'&datefmt=YYYY-MM-DD&simWx=0&motion=full';
  emit('r000a-'+name+(mutant?'-mutant':''),10,localFetch(calendar.buildPage(input,spec),'calendar'),hash,{kind:'markers',name,mutant,spec,lat,lon});
}
// Original-case transition inputs are exposed as data; driver calls the original
// fixture admittedState/setInstant hooks, not a duplicate renderer.
const transitions=[
 {name:'same-day-10',clock:'2026-09-07T17:59:59Z',today:record('07','10'),tomorrow:record('08','11'),want:'1448-02-10'},
 {name:'same-day-09',clock:'2026-09-07T17:59:59Z',today:record('07','09'),tomorrow:record('08','10'),want:'1448-02-09'},
 {name:'post-maghrib',clock:'2026-09-07T18:01:00Z',today:record('07','19'),tomorrow:record('08','20'),want:'1448-02-20'},
 {name:'reverse-boundary',clock:'2026-09-07T17:59:59Z',today:record('07','19'),tomorrow:record('08','20'),want:'1448-02-19'},
 {name:'midnight-promotion',clock:'2026-09-08T00:00:00Z',today:record('08','20'),tomorrow:record('09','21'),want:'1448-02-20'},
 ...['08','10','10'].map((v,i)=>({name:'accepted-duplicate-skip-'+i,clock:'2026-09-07T17:59:59Z',today:record('07',v),tomorrow:record('08','11'),want:'1448-02-'+v})),
 {name:'long-sleep',clock:'2026-09-27T10:00:00Z',today:record('27','08'),tomorrow:record('28','09'),want:'1448-02-08'}
];
for(const [name,todayHijri,nextHijri,want] of [
 ['month-boundary',{year:'1447',month:{number:11,en:'Dhu al-Qadah'},day:'29'},{year:'1447',month:{number:12,en:'Dhu al-Hijjah'},day:'01'},'1447-12-01'],
 ['year-boundary',{year:'1447',month:{number:12,en:'Dhu al-Hijjah'},day:'30'},{year:'1448',month:{number:1,en:'Muharram'},day:'01'},'1448-01-01']
]){const t=record(),n=record('08','01');t.date.hijri=todayHijri;n.date.hijri=nextHijri;transitions.push({name,clock:'2026-09-07T18:00:00Z',today:t,tomorrow:n,want});}
const manifest={schema:'B-native-fixture-preparation/1',auditTarget:TARGET,root:ROOT,sourceSha256:sha(source),configSha256:sha(fs.readFileSync(path.join(ROOT,'config.js'))),originalFixtures:[{file:'tests/r0001-browser-fixture.cjs',sha256:sha(secSource)},{file:'tests/r0009-browser-fixture.cjs',sha256:sha(fs.readFileSync(path.join(ROOT,'tests/r0009-browser-fixture.cjs')))}],adaptations:['Expose original documentFixture export only in an in-memory module; preserve original functions/data/expectations.','Permit only same-origin unchanged asset fetches in original prayer-only interceptor; other external provider fetches retain rejection.','Current script/boot anchors checked exactly once; same source setup and real boot/render retained.','Primary date-only browser runner may explicitly defer optional native-data and Moon worker/WASM requests; no astronomy/whole-renderer PASS inferred.','Arc payloads/negative copied from existing exact full marker tests; no model/drawArc/CSS replacement.'],canary:CANARY,rows,transitions,execution:'PREPARED_NOT_BROWSER_EXECUTED'};
fs.writeFileSync(path.join(OUT,'manifest.json'),JSON.stringify(manifest,null,2));
console.log(JSON.stringify({manifest:path.join(OUT,'manifest.json'),fixtures:rows.length,sourceSha256:manifest.sourceSha256,browserExecuted:false},null,2));
