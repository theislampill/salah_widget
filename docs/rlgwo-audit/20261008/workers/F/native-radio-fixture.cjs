'use strict';
// Preparation starts no browser. Primary may start this server and press native keys.
// Original r001a-radio.cjs expectations are preserved; current script anchors replace
// no consumer logic in healthy mode. Preview transport is blank to avoid terrain work.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ROOT=path.resolve('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget');
const OUT=__dirname,raw=fs.readFileSync(path.join(ROOT,'builder.html'),'utf8'),config=fs.readFileSync(path.join(ROOT,'config.js'));
function once(source,from,to){if(source.split(from).length!==2)throw Error('Current source anchor must match exactly once: '+from.slice(0,50));return source.replace(from,to);}
function page(mutant=''){
 let source=raw;
 if(mutant==='arrows'){
  const start=source.indexOf('modeGroup.addEventListener("keydown"'),end=source.indexOf('\n});',start)+4;
  if(start<0||end<4)throw Error('Current arrow handler boundary missing');
  source=source.slice(0,start)+source.slice(end);
 }else if(mutant==='tabindex')source=once(source,'button.tabIndex=selected?0:-1;','');
 else if(mutant)throw Error('Unknown bounded mutation');
 const pre=`<script>(()=>{
 const data=new Map(),writes=[];
 Object.defineProperty(window,'localStorage',{value:{getItem:k=>data.get(String(k))??null,setItem:(k,v)=>{writes.push({op:'set',key:String(k)});data.set(String(k),String(v));},removeItem:k=>{writes.push({op:'remove',key:String(k)});data.delete(String(k));}}});
 window.__radioFixture={writes,mutant:${JSON.stringify(mutant)},builderSha256:${JSON.stringify(sha(raw))},storage:'private per-document map; owner origin untouched'};
 })();</script>`;
 const boundary=`<script>SalahConfig.coarseDetect=async()=>null;</script>`;
 source=once(source,'<script src="config.js">',pre+'<script src="config.js">');
 source=once(source,'<script>\n"use strict";\nconst $=',boundary+'<script>\n"use strict";\nconst $=');
 const inspect=`<script>window.__radioFixture.snapshot=()=>{
 const b=[...document.querySelectorAll('.modebtn')],iframe=document.getElementById('pv'),code=document.getElementById('code').value;
 const src=/src="([^"]+)"/.exec(code)?.[1],rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};};
 return {mode:embedMode,focus:document.activeElement.id,buttons:b.map(e=>({id:e.id,checked:e.getAttribute('aria-checked'),tabIndex:e.tabIndex,active:e.classList.contains('active'),disabled:e.disabled,rect:rect(e),outline:getComputedStyle(e).outline,focusVisible:e.matches(':focus-visible')})),revision:+new URL(iframe.src).searchParams.get('r'),iframeSrc:iframe.src,iframeAllow:iframe.getAttribute('allow')||'',code,codeHash:src?new URL(src).hash:null,iframeHash:new URL(iframe.src).hash,viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},fonts:document.fonts.status,userAgent:navigator.userAgent,mutant:window.__radioFixture.mutant};
};</script>`;
 return once(source,'</body>',inspect+'</body>');
}
if(require.main===module){
 const evidence=process.argv[2]?path.resolve(process.argv[2]):null;
 if(!evidence||!fs.existsSync(evidence))throw Error('Primary must supply a new existing owned evidence directory');
 let origin='';const server=http.createServer((req,res)=>{
  try{const u=new URL(req.url,'http://127.0.0.1'),mutant=u.searchParams.get('mutant')||'';
   if(u.pathname==='/builder.html'){const bytes=page(mutant);fs.appendFileSync(path.join(evidence,'requests.jsonl'),JSON.stringify({route:u.pathname+u.search,mutant,builderSha256:sha(raw),fixtureSha256:sha(bytes),atUtc:new Date().toISOString()})+'\n');res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(bytes);}
   else if(u.pathname==='/config.js'){res.writeHead(200,{'Content-Type':'text/javascript; charset=utf-8','Cache-Control':'no-store'});res.end(config);}
   else if(u.pathname==='/index.html'){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end('<!doctype html><title>Contained preview transport</title>');}
   else {res.writeHead(404);res.end('Bounded radio fixture only');}
  }catch(e){res.writeHead(500,{'Content-Type':'text/plain'});res.end(String(e));}
 });
 server.listen(0,'127.0.0.1',()=>{origin='http://127.0.0.1:'+server.address().port;const receipt={origin,pid:process.pid,target:'18ff14860ff41c084b1db5f396bb62aa9c22b1be',sourceBuilderSha256:sha(raw),sourceConfigSha256:sha(config),fixtureSha256:sha(fs.readFileSync(__filename)),routes:{healthy:origin+'/builder.html',arrows:origin+'/builder.html?mutant=arrows',tabindex:origin+'/builder.html?mutant=tabindex'},limits:'No browser results yet. Same production radio/default-action/update functions; isolated storage/coarse-detect boundary; preview body suppressed to avoid Moon terrain; emitted hash/allow/snippet checked, real iframe render not claimed.'};fs.writeFileSync(path.join(evidence,'server.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(receipt));});
}
module.exports={page,raw,sha};
