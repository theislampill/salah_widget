'use strict';
// R0041 (issue 143) row R41-P0: re-anchor every line permalink of the issue body and run the plan's `git log -S`
// searches. Recipe (no browser, no network: the issue body is read from a local file the caller saved with
// `gh issue view 143 --json body -q .body`).
// For each https://github.com/<repo>/blob/<sha>/<path>#La[-Lb] link (and each "S:Lnn" reference, which the body
// defines as src/native/index.html at its base): the lines at the pinned commit are looked up at <target> (default
// main) by exact text; the result is the re-anchored range, or WRONG (the text is not found, or found elsewhere than
// one place).
// Usage: node p0-anchors.cjs <issueBody.md> <outJson> [target=origin/main] [base=47faae32]
const fs=require('node:fs'),{execFileSync}=require('node:child_process');
const [bodyFile,outFile,target='origin/main',base='47faae32b21e08adc8928f139f0c5387c7316e71']=process.argv.slice(2);
const body=fs.readFileSync(bodyFile,'utf8');
const git=(...a)=>execFileSync('git',a,{encoding:'utf8',maxBuffer:1<<28});
const cache=new Map();const show=(sha,p)=>{const k=sha+':'+p;if(!cache.has(k)){try{cache.set(k,git('show',k).split('\n'));}catch(e){cache.set(k,null);}}return cache.get(k);};
const refs=[];
for(const m of body.matchAll(/https:\/\/github\.com\/[^/]+\/[^/]+\/blob\/([0-9a-f]{40})\/([^#\s)]+)#L(\d+)(?:-L(\d+))?/g))refs.push({kind:'permalink',sha:m[1],path:m[2],a:+m[3],b:+(m[4]||m[3])});
for(const m of body.matchAll(/S:L(\d+)(?:-L(\d+))?/g))refs.push({kind:'S:L',sha:base,path:'src/native/index.html',a:+m[1],b:+(m[2]||m[1])});
const seen=new Set(),out=[];
for(const r of refs){const key=[r.sha,r.path,r.a,r.b].join('|');if(seen.has(key))continue;seen.add(key);
  const src=show(r.sha,r.path),dst=show(target,r.path);
  if(!src){out.push({...r,verdict:'WRONG',reason:'path or line absent at the pinned commit'});continue;}
  const lines=src.slice(r.a-1,r.b);if(lines.length!==r.b-r.a+1){out.push({...r,verdict:'WRONG',reason:'range beyond the file at the pinned commit'});continue;}
  if(!dst){out.push({...r,verdict:'WRONG',reason:'path absent at target'});continue;}
  const hits=[];for(let i=0;i+lines.length<=dst.length;i++){let ok=true;for(let k=0;k<lines.length;k++)if(dst[i+k]!==lines[k]){ok=false;break;}if(ok)hits.push(i+1);}
  out.push({...r,verdict:hits.length===1?(hits[0]===r.a?'SAME':'MOVED'):hits.length?'AMBIGUOUS':'CHANGED',targetRange:hits.length===1?[hits[0],hits[0]+lines.length-1]:null,hits:hits.length,firstLine:lines[0].trim().slice(0,90)});}
const searches={};for(const s of ['(s.waxing?-1:1)','chi<0','detail.clear()','fallback(']){searches[s]=git('log','--format=%h %s','-S'+s,base+'..'+target,'--','.').trim().split('\n').filter(Boolean);}
const summary=out.reduce((a,r)=>{a[r.verdict]=(a[r.verdict]||0)+1;return a;},{});
fs.writeFileSync(outFile,JSON.stringify({schema:'r0041-p0/1',base,target,targetSha:git('rev-parse',target).trim(),references:out.length,summary,searches,anchors:out},null,1)+'\n');
console.log(JSON.stringify(summary),JSON.stringify(searches));
for(const r of out)if(r.verdict!=='SAME')console.log(r.verdict,r.kind,r.path,`L${r.a}-L${r.b}`,r.targetRange?`-> L${r.targetRange[0]}-L${r.targetRange[1]}`:'',r.reason||'');
