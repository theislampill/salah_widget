'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'../../..');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const get=f=>fs.readFileSync(path.join(root,f),'utf8');
const snippet=f=>fs.readFileSync(path.join(__dirname,f),'utf8');
const paths=['real-sky/native-preview-host.mjs','real-sky/native-composition.mjs','moon/src/moon-native.mjs','moon/src/moon-detail.mjs','real-sky/native-host-hooks.js','src/native/index.html'];
const pins=['8d5cdf82091c7d29eea60ab3418468c9dbcec0d5880224b1f7e68930ad513103','d3e5d216cad8942e923c9418ed18458f8d8a6e719238c7001288c730323e4fb5','01c0e6c91da7c71b8cbc20918ce8a10c2f6a261654abd40c94adcd158c8546e9','c5f336a5f42e3774866d66215e2944b2cde7afad05db801868980121fa70a8b8','a2cdc9f979ad0387cfed68a6ab6224842d525059c079ebdbf1ac9f2b5518f752','7f9eb1514f8d96097273d1ce9be6607b82ccb0c6df41a5094508dab787401249'];
function once(s,a,b){if(s.split(a).length!==2)throw Error('source owner drift: '+a.slice(0,70));return s.replace(a,()=>b);}
function between(s,a,b){const i=s.indexOf(a),j=s.indexOf(b,i+1);if(i<0||j<0)throw Error('missing source range');return s.slice(i,j);}
const geometryKey=`function geometryKey(g){return g&&JSON.stringify([g.rect.left,g.rect.top,g.rect.width,g.rect.height,g.x,g.y,g.w,g.h,g.dpr,g.opacity,g.left,g.top,g.width,g.height,g.up,g.originX,g.originY,g.scaleX,g.scaleY]);}`;
function stageDetail(detail){
 let s=between(detail,'function startMoonDetail(){','function projectSurfaceCodes');
 s=once(s,'function startMoonDetail(){','function startResearchDetail(current){');
 s=once(s,'!window.SalahMoonRuntime?.surface()','!current()');
 s=once(s,between(s,'  const base=document.querySelector','  const {width:W,height:H,dpr}=g;'),'  // No attachment or visible owner is touched by preparation.\n');
 s=once(s,' return {adopt(s){',' '+geometryKey+'\n return {node:cv,geometryKey:()=>geometryKey(geometry()),adopt(s){');
 return s;
}
function transform(){
 const src=paths.map(get);src.forEach((s,i)=>{if(sha(s)!==pins[i])throw Error('unreviewed preimage '+paths[i]);});
 let [preview,composition,moon,detail,hooks,native]=src;
 const geometry=between(detail,' function geometry(){',' function available()');
 const moonCode=stageDetail(detail)+'\nfunction researchGeometryKey(){const table=true,surface=true;'+geometry+geometryKey+';return geometryKey(geometry());}\n'+snippet('detail-stage.js');
 moon=once(moon,' function adopt(m,record){',moonCode+'\n function adopt(m,record){');
 moon=once(moon,'  detail.adopt({linear:m.surfaceLinear,calendarLinear:m.calendarLinear,coverage:m.surfaceCoverage,size:m.surfaceSize,extent:m.surfaceExtent,identity:m.physicalIdentity});','  const researchAdoptedMaterial={linear:m.surfaceLinear,calendarLinear:m.calendarLinear,coverage:m.surfaceCoverage,size:m.surfaceSize,extent:m.surfaceExtent,identity:m.physicalIdentity};\n  detail.adopt(researchAdoptedMaterial);');
 moon=once(moon,'  status.quality=m.diagnostics.quality.status;', '  researchMaterial.set(accepted,researchAdoptedMaterial);\n  status.quality=m.diagnostics.quality.status;');
 moon=once(moon,'  surface(){const s=capture(', '  researchMoonLease,\n  surface(){const s=capture(');
 composition=once(composition,' capture(rows=530){',' capture(rows=530,researchLease=null){');
 composition=once(composition,'  const surface=window.SalahNativeSkyHost.lunarSurface();','  const surface=researchLease?null:window.SalahNativeSkyHost.lunarSurface();');
 composition=once(composition,'  const detail=!!window.SalahMoonRuntime?.detailEnabled;', '  const detail=researchLease?true:!!window.SalahMoonRuntime?.detailEnabled;');
 preview=once(preview,' function clear(reason,all=false){',' '+snippet('preview-stage.js')+'\n function clear(reason,all=false){');
 preview=once(preview,"canvas.style.visibility='hidden';}","canvas.style.visibility='hidden';dropSlots();}");
 preview=once(preview,'const bottom=foreground.bottom(),rows=nativeForegroundRows(530,bottom,previousMoonBottom),capture=foreground.capture(rows);',"const lease=value&&previousMoon&&card.classList.contains('real-sky-preview-ready')?window.SalahMoonRuntime?.researchMoonLease?.():null;\n  const bottom=foreground.bottom(),rows=nativeForegroundRows(530,bottom,previousMoonBottom),capture=foreground.capture(rows,lease);\n  if(lease)capture.researchMoon=lease;");
 preview=once(preview,'     const nextFrame=pixels',`     const lease=capture.researchMoon;
     if(lease){const entry=++transactionRevision;
      try{return publishSlot(next,pixels,base,image,solarMask,capture,bottom,rows,entry,lease,revision);}
      catch(error){if(entry!==transactionRevision||disposed||window.SalahSkyPreview!==preview||card.classList.contains('real-sky-composed'))return false;
       if(!priorMoonCurrent()){clear('research previous Moon no longer current');return retryPreview(retried);}
       throw error;}
     }
     if(selected()){clear('research presentation must release an unsupported Moon route');return retryPreview(retried);}
     const nextFrame=pixels`);
 preview=once(preview,'status.draws++;lastPaint=performance.now();return true;',"status.draws++;lastPaint=performance.now();previousMoon=window.SalahMoonDetail?.state?.skyOwner==='atmospheric-preview'?window.SalahMoonRuntime?.researchMoonLease?.():null;return true;");
 preview=once(preview,' function update(retried=false){\n  if(disposed)return;',' function update(retried=false){\n  if(disposed)return;synchronizeSelection();');
 preview=once(preview,'if(value&&!nativeResultCurrent(value.job,s))',"if(selected()&&!priorMoonCurrent())clear('research Moon changed before update');\n   if(value&&!nativeResultCurrent(value.job,s))");
 preview=once(preview,'get frame(){return previewFrame;},get state(){return structuredClone(status);}',"get frame(){return selected()?.frame??previewFrame;},get state(){const slot=selected();return structuredClone(slot&&status.researchGeneration!==slot.id?slot.receipt:status);}");
 preview=once(preview,'if(disposed)return;disposed=true;retireFirstPaint();','if(disposed)return;disposed=true;dropSlots();retireFirstPaint();');
 // Currentness gates also cover errors before the transaction callback (decode,
 // foreground/readback). A Moon withdrawal cannot leave a selected detail visible.
 preview=preview.replaceAll('if(!retained.paused&&publishable(value,retained)&&host.cloudsCurrent(status.composition?.cloudAuthority))','if(priorMoonCurrent()&&!retained.paused&&publishable(value,retained)&&host.cloudsCurrent(status.composition?.cloudAuthority))');
 preview=once(preview,'window.SalahSkyPreview=preview={update,clear,present(now){',"window.SalahSkyPreview=preview={update,clear,researchMoonWithdraw(){if(selected()&&!withdrawingResearch)clear('research lunar presentation withdrawn');},present(now){");
 preview=once(preview,'function clear(reason,all=false){clearedReceipt=', 'let withdrawingResearch=false;\n function clear(reason,all=false){if(withdrawingResearch)return;withdrawingResearch=true;try{clearedReceipt=');
 preview=once(preview,"canvas.style.visibility='hidden';dropSlots();}","canvas.style.visibility='hidden';dropSlots();}finally{withdrawingResearch=false;}}");
 moon=once(moon,'clear(){inner.clear();},clearFor(owner){','clear(){inner.clear();window.SalahSkyPreview?.researchMoonWithdraw?.();},clearFor(owner){');
 moon=once(moon,'inner.clear();return true;},compose','inner.clear();window.SalahSkyPreview?.researchMoonWithdraw?.();return true;},compose');
 // A leased replacement still needs the original, layout-derived solar anchor.
 // Keep existing default presentation/diagnostic behavior for other callers.
 hooks=once(hooks,'capture(includePresentation=true){','capture(includePresentation=true,includeMoon=includePresentation){');
 hooks=once(hooks,'moonReady:includePresentation?', 'moonReady:includeMoon?');
 preview=once(preview,'anchor=host.capture().solarAnchor','anchor=host.capture(true,!prepared.capture.researchMoon).solarAnchor');
 // The presenter must observe every active generation before the rate throttle.
 // A producer notification only withdraws. It never recursively paints a cloud
 // while that producer is still publishing its new authority.
 preview=once(preview,'function present(now){if(disposed)return;const s=host.capture(false);','function present(now){if(disposed)return;revokeIfStale();const s=host.capture(false);');
 preview=once(preview,'if(disposed)return;synchronizeSelection();','if(disposed)return;synchronizeSelection();revokeIfStale();');
 preview=once(preview,'function clear(reason,all=false){if(withdrawingResearch)', 'function clear(reason,all=false,cloudReceipt){if(withdrawingResearch)');
 preview=once(preview,'try{clearedReceipt=host.reconcileClouds();','try{clearedReceipt=cloudReceipt??host.reconcileClouds();');
 preview=once(preview,'preview={update,clear,researchMoonWithdraw()', 'preview={update,clear,researchRevokeIfStale:revokeIfStale,researchMoonWithdraw()');
 preview=once(preview,'withdrawingResearch=true;try{clearedReceipt=', 'withdrawingResearch=true;try{const slot=selected();if(slot){withdrawSlot(slot,reason,all,cloudReceipt);return;}if(!all&&withdrawalStyle&&!value&&!pendingValue&&!solarPublication.pending&&!window.SalahFirstPaint?.value&&!card.classList.contains("real-sky-preview-ready"))return;clearedReceipt=');
 preview=once(preview,'disposed=true;dropSlots();retireFirstPaint();','disposed=true;dropSlots();withdrawalStyle?.remove();retireFirstPaint();');
 // Moon adoption publishes/withdraws its existing route first. Check selection
 // in this same task, including when the texture publication itself failed.
 moon=once(moon,'status.lastAdoption={at:began,prefixMs,totalMs:performance.now()-began,source:status.visibleSource};','status.lastAdoption={at:began,prefixMs,totalMs:performance.now()-began,source:status.visibleSource};window.SalahSkyPreview?.researchRevokeIfStale?.();');
 native=once(native,'_cloudPublication={decision,record,scene,mode,receipt};return receipt;','_cloudPublication={decision,record,scene,mode,receipt};window.SalahSkyPreview?.researchRevokeIfStale?.(receipt);return receipt;');
 native=once(native,'function renderMoon(){\n','function renderMoon(){try{\n');
 native=once(native,'\n}\n\n// PROJECTED STARFIELD:', '\n}finally{window.SalahSkyPreview?.researchRevokeIfStale?.();}}\n\n// PROJECTED STARFIELD:');
 return {paths,sources:src,outputs:[preview,composition,moon,detail,hooks,native],stage:stageDetail(detail)};
}
function combine(){
 const {prayerOnlyCandidate}=require('../r002f_a2_architecture.cjs');
 const {canonicalQuarantineCandidate}=require('../r002f_a2_quarantine.cjs');
 const prepared=transform(),outputs=[...prepared.outputs];
 outputs[2]=canonicalQuarantineCandidate(outputs[2]);outputs[5]=prayerOnlyCandidate(outputs[5]);
 return {paths,sources:prepared.sources,outputs};
}
function quarantineOnly(){
 const {canonicalQuarantineCandidate}=require('../r002f_a2_quarantine.cjs');
 const prepared=transform(),outputs=[...prepared.sources];outputs[2]=canonicalQuarantineCandidate(outputs[2]);
 return {paths,sources:prepared.sources,outputs};
}
if(require.main===module){
 const out=process.argv[2];if(!out||fs.existsSync(out))throw Error('supply a fresh output directory');
 const mode=process.argv[3];if(mode&&!['--combined','--quarantine-only'].includes(mode))throw Error('unknown research arm');
 const {paths,sources,outputs}=mode==='--combined'?combine():mode==='--quarantine-only'?quarantineOnly():transform();fs.mkdirSync(out,{recursive:true});
 const manifest=[];
 for(let i=0;i<outputs.length;i++){
  if(outputs[i]===sources[i])continue;
  const file=paths[i],dst=path.join(out,file);fs.mkdirSync(path.dirname(dst),{recursive:true});fs.writeFileSync(dst,outputs[i]);
  let patch;try{execFileSync('diff',['-u','--label','a/'+file,'--label','b/'+file,path.join(root,file),dst]);}catch(error){if(error.status!==1)throw error;patch=error.stdout;}
  fs.appendFileSync(path.join(out,'transaction.patch'),patch);manifest.push({file,original:sha(sources[i]),candidate:sha(outputs[i])});
 }
 fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({files:manifest,unchangedDetail:pins[3],patch:sha(fs.readFileSync(path.join(out,'transaction.patch')))},null,2)+'\n');
}
module.exports={transform,combine,stageDetail,sha};
