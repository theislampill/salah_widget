// Effect-free probe: extracts pure clock functions from src/native/index.html at the audited SHA
// (read via `git show`, passed on stdin) and evaluates them in a vm with an invalid tz hint.
const vm=require('vm'); const src=require('fs').readFileSync(0,'utf8');
function grab(name){ const i=src.indexOf('function '+name+'('); if(i<0) throw new Error(name);
  let d=0,j=src.indexOf('{',i); for(let k=j;k<src.length;k++){ if(src[k]==='{')d++; else if(src[k]==='}'){d--; if(!d) return src.slice(i,k+1);} } }
const code=['utcFields','zoneFormatter','projectInZone','partsInTz','prayerCivilDay','prayerNextDay'].map(grab).join('\n');
const out={};
for(const hint of ['America/New_York','Asia/Riyadh','Asia/Riyad','Etc/Bogus']){
  const ctx={pad:n=>String(n).padStart(2,'0'),tz:hint,_partsFormatter:null,_partsFormatterZone:null,_prayerDayFormatter:null,_prayerDayZone:null,
    simNow:()=>Date.UTC(2026,10,12,21,30),Intl,Date,Number,String,Math,JSON};
  vm.createContext(ctx); vm.runInContext('let _x=0;'+code,ctx);
  out[hint]={prayerCivilDay:vm.runInContext('prayerCivilDay()',ctx),partsInTz:vm.runInContext('JSON.stringify(partsInTz(simNow()))',ctx)};
}
out.hostZone=Intl.DateTimeFormat().resolvedOptions().timeZone;
console.log(JSON.stringify(out,null,1));
