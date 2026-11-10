// Each mutant executes the whole product and the same behavior fixtures. A missing
// terminal, bootstrap exception or incomplete case count cannot earn detection.
// These are source/command controls, never compositor or elapsed-motion evidence.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process');
const {root,sha}=require('./r001d-harness.cjs');
const sourcePath=process.argv.slice(2).find(a=>!a.startsWith('--'))||path.join(root,'index.html'),source=fs.readFileSync(sourcePath,'utf8');
const outputArg=process.argv.find(a=>a.startsWith('--output-dir='));
const outputDir=outputArg?path.resolve(outputArg.slice('--output-dir='.length)):fs.mkdtempSync(path.join(os.tmpdir(),'salah-sky-mutants-'));
fs.mkdirSync(outputDir,{recursive:true});
function change(html,from,to){assert.equal(html.split(from).length,2,'mutation anchor matches once: '+from.slice(0,65));return html.replace(from,to);}
const counts={'r0021-reveal':18,'r0025-continuity':9,'r0025-lifecycle':16},controls=[],mutations=[];
function run(name,suite,file){
  const result=cp.spawnSync(process.execPath,[path.join(root,'tests',suite+'.cjs'),file],{cwd:root,encoding:'utf8',timeout:30000,maxBuffer:4*1024*1024});
  const log=result.stdout+result.stderr,logPath=path.join(outputDir,name+'.log');fs.writeFileSync(logPath,log);
  assert.equal(result.error,undefined,'child process completed: '+name);
  const terminal=JSON.parse(result.stdout.trim().split('\n').at(-1));
  assert.equal(terminal.sourceSha256,sha(fs.readFileSync(file)),'actual mutant source identity');
  assert.equal(terminal.pass+terminal.fail,counts[suite],'all declared behavior cases reached');
  if(suite==='r0021-reveal'){assert.equal(terminal.terminal,true);assert.equal(terminal.missing,0);assert.equal(terminal.executed,counts[suite]);}
  return {name,suite,exit:result.status,terminal,logPath,logSha256:sha(Buffer.from(log)),failures:log.split('\n').filter(l=>l.startsWith('FAIL '))};
}
for(const suite of Object.keys(counts)){
  const control=run('healthy-'+suite,suite,sourcePath);assert.equal(control.exit,0);assert.equal(control.terminal.fail,0);controls.push(control);
}
const definitions=[
  ['new-wind-before-elapsed','r0025-continuity',html=>change(change(html,'\n  advanceCloudMotion(simNow()/1000);\n','\n'),'  CS.wx=A.windUX; CS.wy=A.windUY; CS.wspd=0.06+0.6*A.windSpeedNorm;','  CS.wx=A.windUX; CS.wy=A.windUY; CS.wspd=0.06+0.6*A.windSpeedNorm;\n  advanceCloudMotion(simNow()/1000);')],
  ['ordinary-daily-reseed','r0025-continuity',html=>change(html,'const _cs=_cloudMotion.population;','const _cs=(_cloudFieldSeed+Math.floor(t/86400)*3.13)%617;')],
  ['frozen-visual-interval','r0025-continuity',html=>change(html,'dt=elapsed*rate;','dt=0;')],
  ['empty-deck-skips-time','r0025-lifecycle',html=>change(html,'  if(!advanceCloudMotion(t)){ _cloudDirty=false; return; }\n  if(S.covLow+S.covMid+S.covHigh<0.02){ _cloudDirty=false; return; }','  if(S.covLow+S.covMid+S.covHigh<0.02){ _cloudDirty=false; return; }\n  if(!advanceCloudMotion(t)){ _cloudDirty=false; return; }')],
  ['missing-periodic-wings','r0025-lifecycle',html=>change(html,'for(let copy=-1;copy<=1;copy++){','for(let copy=0;copy<=0;copy++){')],
  ['wrap-adds-positive-period','r0025-lifecycle',html=>change(html,'const _cloudWrap=(v,p)=>{ const r=v%p; return r<0?r+p:r; };','const _cloudWrap=(v,p)=>((v%p)+p)%p;')],
  ['initial-sky-defaults-visible','r0021-reveal',html=>change(html,'<div class="c sky-pending sky-initializing">','<div class="c">')],
  ['filtered-background-unmasked','r0021-reveal',html=>change(html,'<g class="stellar-background" mask="url(#stellar-cutout)">','<g class="stellar-background">')],
  ['mask-retains-default-transform','r0021-reveal',html=>change(html,'if(mask) mask.setAttribute("transform",transform);','/* mask transform omitted */')],
  ['projection-retains-prior-anchor','r0021-reveal',html=>change(html,'if(ADVANCING || !_starsProjected || _starProjectionKey!==skySceneIdentity()) projectStars(simDate());','if(ADVANCING || !_starsProjected) projectStars(simDate());')],
  ['stale-first-paint-reveals','r0021-reveal',html=>change(html,' || !A.moonObservation || A.moonObservation.fresh!==true','')],
  ['undecoded-surface-ready','r0021-reveal',html=>change(html,'!!(_pbrReady && photo && photo.getAttribute("href") && _skySceneKey!==null)','!!(_skySceneKey!==null)')],
];
let detected=0,failed=0;
for(const [name,suite,mutate] of definitions){
  try{
    const file=path.join(outputDir,name+'.html');fs.writeFileSync(file,mutate(source));const observation=run(name,suite,file);mutations.push(observation);
    assert.equal(observation.exit,1,'behavior mutant exits nonzero');assert.ok(observation.terminal.fail>0,'a reached behavior assertion rejects the mutant');
    assert.ok(observation.failures.length>0);assert.ok(!observation.failures.some(l=>/not defined|is not a function|Unexpected token|INCOMPLETE/.test(l)),'setup failure cannot masquerade as detection');
    detected++;console.log('DETECTED '+name+' '+observation.failures.map(l=>l.split(' :: ')[0]).join(' | '));
  }catch(e){failed++;console.log('FAIL '+name+' :: '+e.message.split('\n')[0]);}
}
const receipt={sourcePath,sourceSha256:sha(Buffer.from(source)),fixtureSha256:sha(fs.readFileSync(__filename)),outputDir,controls,mutations,detected,failed,limits:'actual whole source and reached behavior assertions; no native pixels/elapsed-motion/cost'};
fs.writeFileSync(path.join(outputDir,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({sourcePath:receipt.sourcePath,sourceSha256:receipt.sourceSha256,fixtureSha256:receipt.fixtureSha256,declared:definitions.length,executed:detected+failed,detected,failed,receipt:path.join(outputDir,'receipt.json'),limits:receipt.limits}));process.exitCode=failed?1:0;
