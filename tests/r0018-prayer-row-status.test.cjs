'use strict';
// Source-bound clock/model/render controls. Recording DOM and unrelated art doubles
// are inherited from the existing fixture; these checks make no native pixel claim.
const test=require('node:test'),assert=require('node:assert/strict');
const {AssertionError}=require('node:assert');
const {source,record,harness}=require('./r0003-harness.cjs');
const keys=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'];
const times={Fajr:'05:00',Sunrise:'06:00',Dhuhr:'12:00',Asr:'15:30',Sunset:'18:00',Maghrib:'18:00',Isha:'19:30'};
function prayer(day='07-09-2026',changes={}){
  const data=record(day,'UTC');Object.assign(data.timings,times,changes);return data;
}
function fixture(at='12:30:00',changes={},raw=source(),next=true,day='07-09-2026'){
  const [d,m,y]=day.split('-'),h=harness({source:raw,epoch:`${y}-${m}-${d}T${at}Z`,hash:'#lat=24.47&lon=39.61&tz=UTC&method=4&school=0&units=c'});
  h.seed(prayer(day,changes),next?prayer(day==='07-09-2026'?'08-09-2026':'09-09-2026',changes):null);
  return h;
}
function rows(h){
  h.run('render()');
  const html=h.nodes.get('.times').innerHTML;
  const list=[...html.matchAll(/<div class="p ([^"]*)"(?: data-prayer-key="[^"]*")?><b>([^<]+)<\/b><span class="tm">([^<]+)<\/span><\/div>/g)];
  assert.deepEqual(list.map(row=>row[2]),keys,'Actual renderer keeps all six authored rows');
  return list.map(row=>({key:row[2],roles:row[1].trim().split(/\s+/).filter(Boolean).sort().join('+'),time:row[3]}));
}
function verify(h,expected,current,next){
  const actual=rows(h),model=h.run('model()');
  assert.deepEqual(actual.map(row=>row.roles),expected,'Past/current/next classes from the actual rendered rows');
  assert.equal(model.currentKey,current);assert.equal(model.nextKey,next);
  return {actual,model};
}
test('midday fades only Fajr/Sunrise; future Maghrib/Isha remain normal',()=>{
  const h=fixture();const {actual}=verify(h,['past','past','now','on','',''],'Dhuhr','Asr');
  assert.deepEqual(actual.map(row=>row.time),['05:00','06:00','12:00','15:30','18:00','19:30']);
  assert.equal(h.nodes.get('.cn').textContent,'Dhuhr');assert.match(h.nodes.get('.left').innerHTML,/until-prayer">Asr/);
});
for(const [at,expected,current,next] of [
  ['00:00:00',['on','','','','','now'],'Isha','Fajr'],
  ['04:59:59',['on','','','','','now'],'Isha','Fajr'],
  ['05:00:00',['now','on','','','',''],'Fajr','Sunrise'],
  ['05:59:59',['now','on','','','',''],'Fajr','Sunrise'],
  ['06:00:00',['past','now','on','','',''],'Sunrise','Dhuhr'],
  ['06:19:59',['past','now','on','','',''],'Sunrise','Dhuhr'],
  ['06:20:00',['past','past','on','','',''],'Forenoon','Dhuhr'],
  ['11:59:59',['past','past','on','','',''],'Forenoon','Dhuhr'],
  ['12:00:00',['past','past','now','on','',''],'Dhuhr','Asr'],
  ['15:29:59',['past','past','now','on','',''],'Dhuhr','Asr'],
  ['15:30:00',['past','past','past','now','on',''],'Asr','Maghrib'],
  ['17:59:59',['past','past','past','now','on',''],'Asr','Maghrib'],
  ['18:00:00',['past','past','past','past','now','on'],'Maghrib','Isha'],
  ['19:29:59',['past','past','past','past','now','on'],'Maghrib','Isha'],
  ['19:30:00',['on','past','past','past','past','now'],'Isha','Fajr'],
  ['23:59:59',['on','past','past','past','past','now'],'Isha','Fajr']
])test(`actual clock boundary ${at} preserves elapsed/current/upcoming hierarchy`,()=>verify(fixture(at),expected,current,next));
test('actual midnight adoption resets elapsed statuses for the new civil day',async()=>{
  const h=fixture('23:59:59');h.run('startRenderLoop()');await h.frame();
  assert.equal(h.state().today.date.gregorian.date,'07-09-2026');
  h.wallBy(1000);await h.frame();
  assert.equal(h.state().today.date.gregorian.date,'08-09-2026');
  verify(h,['on','','','','','now'],'Isha','Fajr');
  assert.equal(h.run('model().nowMin'),0);
});
test('equal admitted clocks are normal at the event instant and past one second later',()=>{
  const h=fixture('05:00:00',{Sunrise:'05:00'});
  assert.equal(h.run('admitPrayerRecord(today,lastDate).ok'),true);
  verify(h,['','now','on','','',''],'Sunrise','Dhuhr');
  h.wallBy(1000);verify(h,['past','now','on','','',''],'Sunrise','Dhuhr');
});
test('all equal polar clocks preserve exact-instant and elapsed states without row ordering',()=>{
  const changes=Object.fromEntries(Object.keys(times).map(key=>[key,'12:00'])),h=fixture('12:00:00',changes);
  assert.equal(h.run('admitPrayerRecord(today,lastDate).ok'),true);
  verify(h,['on','','','','','now'],'Isha','Fajr');
  h.wallBy(1000);verify(h,['on','past','past','past','past','now'],'Isha','Fajr');
});
test('reordered admitted clocks classify elapsed time independently of displayed row index',()=>{
  const h=fixture('12:30:00',{Fajr:'20:00',Isha:'02:00'});
  assert.equal(h.run('admitPrayerRecord(today,lastDate).ok'),true);
  verify(h,['','past','now','on','','past'],'Dhuhr','Asr');
});
test('annotated admitted clocks use the same source clock parser as the model',()=>{
  const changes=Object.fromEntries(Object.entries(times).map(([key,value])=>[key,value+' (UTC)'])),h=fixture('12:30:00',changes);
  assert.equal(h.run('admitPrayerRecord(today,lastDate).ok'),true);
  verify(h,['past','past','now','on','',''],'Dhuhr','Asr');
});
test('missing tomorrow preserves next-key precedence while actual countdown stays unavailable',()=>{
  const h=fixture('23:00:00',{},source(),false);
  const {model}=verify(h,['on','past','past','past','past','now'],'Isha','Fajr');
  assert.equal(Number.isFinite(model.nextEpoch),false);assert.equal(Number.isFinite(model.leftMin),false);
  assert.equal(h.nodes.get('.left').textContent,'Countdown unavailable');
});
function mutant(expression){
  const raw=source(),anchor=/const dim  = [^;]+;/g;assert.equal([...raw.matchAll(anchor)].length,1,'Single actual row predicate');
  return raw.replace(anchor,'const dim  = '+expression+';');
}
function killed(raw,at,changes,expected,current,next){
  assert.throws(()=>verify(fixture(at,changes,raw),expected,current,next),error=>error instanceof AssertionError&&error.message.includes('Past/current/next classes'),'Only a row-class assertion failure kills the mutant');
}
test('mutant fading every inactive row is rejected by the actual midday caller',()=>{
  killed(mutant('!now && !on'),'12:30:00',{},['past','past','now','on','',''],'Dhuhr','Asr');
});
test('mutant inferring elapsed state by row index is rejected by reordered timings',()=>{
  killed(mutant('!now && !on && prayers.indexOf(k)<prayers.indexOf(M.currentKey)'),'12:30:00',{Fajr:'20:00',Isha:'02:00'},['','past','now','on','','past'],'Dhuhr','Asr');
});
test('mutant fading equal-time events at the exact instant is rejected',()=>{
  killed(mutant('!now && !on && mins(M.t[k])<=M.nowMin'),'05:00:00',{Sunrise:'05:00'},['','now','on','','',''],'Sunrise','Dhuhr');
});
test('mutant dropping current/next precedence is rejected after Isha',()=>{
  killed(mutant('mins(M.t[k])<M.nowMin'),'23:00:00',{},['on','past','past','past','past','now'],'Isha','Fajr');
});
