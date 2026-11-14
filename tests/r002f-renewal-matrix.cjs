'use strict';
// R002F (issue 96) owner condition: "never worse than main" DEMONSTRATED over the skew/lag x poll-phase matrix with
// the real functions. Both sides run the native inline runtime of a BUILT entry: main = `git show <ref>:index.html`
// (default origin/main, override R002F_MATRIX_MAIN_REF), candidate = this tree's generated index.html. The only
// test-side transformation, applied identically to both bodies, makes calls to the absent native sky host's methods
// optional (`SalahNativeSkyHost?.m(` -> `SalahNativeSkyHost?.m?.(`); no weather code is touched. Each cell is the
// actual loop driven across one boundary (margin 3 s) by weather-renewal-fixture with a floor-to-15-min provider
// stub. L = device clock AHEAD of the provider (skew) or provider publication lag. Request latency zero.
// Run: node --test tests/r002f-renewal-matrix.cjs (about 35 min; needs the main ref in git, so it is a registered
// pre-merge evidence recipe, not part of the default glob). Any counterexample is printed, never filtered.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {execFileSync}=require('node:child_process');
const F=require('./weather-renewal-fixture.cjs'),{parseScripts}=require('./native-script-contract.js'),{B}=F;
const FRAME=250, Ls=[0,1,2,3,5,10,20,30,60];
function builtDoc(text){
  const sc=parseScripts(text).filter(s=>!s.attributes.trim()&&s.body.includes('async function boot(){'));
  assert.equal(sc.length,1,'one native inline runtime in the built entry');
  return '<script src="config.js"></script><script>'+sc[0].body.replace(/SalahNativeSkyHost\?\.(\w+)\(/g,'SalahNativeSkyHost?.$1?.(')+'</script>';
}
const mainRef=process.env.R002F_MATRIX_MAIN_REF||'origin/main';
let MAIN=null; try{ MAIN=builtDoc(execFileSync('git',['show',mainRef+':index.html'],{cwd:path.join(__dirname,'..'),maxBuffer:1<<27}).toString()); }catch(e){ MAIN=null; }
const CAND=builtDoc(fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8'));
// Phases (ms) swept over (0, 30] s: every 1 s, plus the cells either side of each L and of the margin.
const phases=[...new Set([...Array.from({length:30},(_,i)=>(i+1)*1000),250,500,2750,3250,...Ls.flatMap(L=>[L*1000-FRAME,L*1000,L*1000+FRAME])]
  .filter(p=>p>0&&p<=30000))].sort((a,b)=>a-b);
async function gap(source,phaseMs,kind,L){
  const s=await F.scene({source,phaseMs,frame:FRAME,[kind]:L*1000}); const frames=await s.run(B+100000); const g=F.gap(frames);
  if(g.offAt==null){ assert(frames.every(f=>f.sel),'no unselected frame: renewed within one frame'); return 0; }   // gap shorter than one frame
  assert(g.onAt!=null,'recovered within 100 s: '+JSON.stringify({kind,L,phaseMs,g}));
  return g.onAt;
}
for(const kind of ['skewMs','lagMs'])
  test(`never worse than main: ${kind==='skewMs'?'device clock ahead':'provider publication lag'} L x poll phase (${phases.length} phases)`,{skip:MAIN?false:'git ref '+mainRef+' unavailable'},async t=>{
    const rows=[], worse=[];
    for(const L of Ls){ let sm=0,sc=0,n=0,better=0;
      for(const p of phases){ const m=await gap(MAIN,p,kind,L), c=await gap(CAND,p,kind,L); sm+=m; sc+=c; n++;
        if(c>m) worse.push({L,phaseMs:p,main:m,candidate:c}); else if(c<m) better++; }
      rows.push({L,meanMainS:+(sm/n/1000).toFixed(2),meanCandidateS:+(sc/n/1000).toFixed(2),candidateBetterCells:better,cells:n}); }
    t.diagnostic(JSON.stringify({kind,margin:3000,frameMs:FRAME,rows}));
    assert.deepEqual(worse,[],'counterexamples (candidate gap > main gap)');
  });
