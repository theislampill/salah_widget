// Effect-free: evaluates src/native/config.js (stdin, from git show at the audited SHA) in a vm with a
// Map-backed storage; shows that builder serialization drops tz and resolution falls back to the default hint,
// then evaluates skySceneIdentity's formula (copied from index.html L2217-2220) before/after provider tz adoption.
const vm=require('vm'); const src=require('fs').readFileSync(0,'utf8');
const ctx={URLSearchParams,Object,Array,String,Number,Math,isNaN,isFinite,JSON,Date,Intl,Promise,setTimeout,clearTimeout};
ctx.window=ctx; vm.createContext(ctx); vm.runInContext(src,ctx);
const C=ctx.SalahConfig;
const hash=C.serialize({lat:24.47,lon:39.61,label:'Madinah',method:'4',tz:'Asia/Riyadh'});
const r=C.resolve('#'+hash,{getItem:()=>null,setItem(){},removeItem(){}});
const ident=(lat,lon,tz)=>[lat,lon,tz,'wall'].join('|');
console.log(JSON.stringify({serializedHash:hash,containsTz:/(^|&)tz=/.test(hash),resolvedMode:r.mode,resolvedTzHint:r.cfg.tz,
  identityAtBoot:ident(r.cfg.lat,r.cfg.lon,r.cfg.tz),identityAfterProviderAdoption:ident(r.cfg.lat,r.cfg.lon,'Asia/Riyadh')},null,1));
