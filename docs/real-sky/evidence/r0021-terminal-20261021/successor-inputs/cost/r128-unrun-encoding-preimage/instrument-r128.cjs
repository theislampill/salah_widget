/* Disposable observer insertion. Production inputs are read-only. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const acorn=require('${TOOL_CACHE}/OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe/node-v24.15.0-win-x64/node_modules/command-code/node_modules/acorn');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const base=path.resolve(__dirname,'../builds');
const names={A:'baseline-18ff',B:'integrated-r31-file-transport'};
const dest=path.resolve(__dirname,'instrumented-r128');
if(fs.existsSync(dest))throw new Error('Preserve existing instrumented output');
const manifest={schema:'r0021-passive-cost-source/v1',acornVersion:acorn.version,createdAt:new Date().toISOString(),instrumenterSha256:hash(fs.readFileSync(__filename)),sides:{}};
const mains=new Set(['atmosphere','paint','renderMoon','paintClouds','applyTheme','render','commitSkyScene']);
function processSource(text,file,scriptId){
 const ast=acorn.parse(text,{ecmaVersion:'latest',sourceType:'script',locations:true});
 const edits=[],roles=[],owners=[],fnNames=new WeakMap();
 const main=file==='index.html'&&!scriptId&&text.includes('function renderMoon()');
 function insert(pos,s,priority=0){edits.push({pos,text:s,priority});}
 function bodyStart(node){let at=node.body.start+1;for(const s of node.body.body){if(!s.directive)break;at=s.end;}return at;}
 function variables(node){return new Set(node.body.body.flatMap(s=>s.type==='VariableDeclaration'?s.declarations.map(d=>d.id.type==='Identifier'?d.id.name:null):[]).filter(Boolean));}
 function walk(node,ancestors=[],parent=null){
  if(!node||typeof node!=='object')return;
  const fn=/Function/.test(node.type),name=node.id?.name||(parent?.type==='MethodDefinition'?parent.key?.name:'')||'',chain=ancestors.map(a=>a.id?.name||fnNames.get(a)||'<anon>');if(fn)fnNames.set(node,name);
  let role=null;
  if(fn&&!node.async&&!node.generator){
   if(main&&mains.has(name))role='main.'+name;
   else if(main&&name==='loop'&&chain.includes('startRenderLoop'))role='main.renderLoop';
   else if(name==='prepareNativeFirstPaint')role='head.prepareNativeFirstPaint';
   else if(chain.includes('startNativeSkyPreview')&&['paint','update','present','tick','prepareForeground','publishPreview','rejectPreview','paintFailed'].includes(name))role='preview.'+name;
   else if(chain.includes('startMoonDetail')&&name==='compose')role='moon.detailCompose';
   else if((file==='moon/moon-host.js'||scriptId==='moon-initial-code')&&['poll','adopt','syncTexture','initialPresentation'].includes(name))role='moon.'+name;
   else if(chain.includes('startNativeSky')&&['compose','accept','animate','publishComposition','rejectComposition','compositionFailed'].includes(name))role='sky.'+name;
   else if(parent?.type==='AssignmentExpression'&&parent.left?.type==='MemberExpression'&&parent.left.property.name==='onmessage')role=main?'main.firstTaskYield':(file==='real-sky/native-sky.js'?'sky':'moon')+'.workerMessage';
   if(chain.includes('NativeForegroundCapture')&&['capture','prepareSolarMask'].includes(name))role='foreground.'+name;
   if(chain.includes('NativeSolarMaskPublication')&&['publish','finish','cancel','dispose'].includes(name))role='mask.'+name;
   if(chain.includes('NativeSolarMaskPublication')&&chain.includes('publish')&&!name)role=node.params.length?'mask.decodeRejected':'mask.decodeFulfilled';
   if(chain.includes('NativeSolarMaskPublication')&&name==='constructor')insert(node.body.end-1,';window.__r21Resources.register(this);');
   if(chain.includes('NativeSolarMaskPublication')&&chain.includes('publish')&&!name&&node.params.length&&node.body.type==='BlockStatement'){
    insert(bodyStart(node),';window.__r21Resources.reaction(this,revision,"rejected");try{',1);
    insert(node.body.end-1,'}finally{window.__r21Resources.reactionComplete(this,revision,"rejected");}',-1);
   }
   if(role){
    const token='__r0021_token_'+node.start;
    const block=node.body.type==='BlockStatement';
    insert(block?bodyStart(node):node.body.start,`${block?';':'{'}const ${token}=window.__r21.enter(${JSON.stringify(role)});try{${block?'':'return ('}`);
    insert(block?node.body.end-1:node.body.end,`${block?'':');'}}catch(__r0021_error){window.__r21.caught(${token},__r0021_error);throw __r0021_error;}finally{window.__r21.leave(${token});}${block?'':'}'}`);
    roles.push({role,function:name||'<anonymous>',ancestors:chain,line:node.loc.start.line,start:node.start,end:node.end,originalFunctionSha256:hash(text.slice(node.start,node.end))});
   }
   const vars=node.body.type==='BlockStatement'?variables(node):new Set();
   let owner=null,fields=null;
   if(name==='startNativeSky'){
    owner='sky';fields=['frame','job','pendingJob','paintedFrame','paintedJob','previousPresentation','previousSolarMask','foreground','canvas','disposed','animationId','solarPublication'];
   }else if(name==='startNativeSkyPreview'){
    owner='preview';fields=['solarPublication','foreground','canvas','disposed','value','pendingValue','previewFrame','baseBytes','catalogueRevision'];
   }else if(vars.has('upperBytes')&&vars.has('accepted')&&vars.has('pending')&&vars.has('worker')){
    owner='moon';fields=['upperBytes','calendarBytes','waitingPreview','canvas','disposed','ready','pending','accepted','serial','epoch','profileMode','timer','deadline','startFrame','worker'];
   }else if(name==='startMoonDetail'){
    owner='moonDetail';fields=['cv','cloudCv','last','disposed','table','calendarTable','surface','prepared','projected'];
   }else if(name==='createInitialMoon'){
    owner='moonInitial';fields=['material','coverage','records','indices','rule'];
   }
   if(owner){
    fields=fields.filter(x=>vars.has(x));
    insert(bodyStart(node),`;window.__r21.registerOwner(${JSON.stringify(owner)},()=>({${fields.join(',')}}));`);
    owners.push({owner,fields,line:node.loc.start.line});
   }
  }
  for(const [k,v]of Object.entries(node)){
   if(k==='loc')continue;
   if(Array.isArray(v)){for(const child of v)if(child?.type)walk(child,(fn||node.type==='ClassDeclaration')?[...ancestors,node]:ancestors,node);}
   else if(v?.type)walk(v,(fn||node.type==='ClassDeclaration')?[...ancestors,node]:ancestors,node);
  }
 }
 walk(ast);
 edits.sort((a,b)=>a.pos-b.pos||a.priority-b.priority);
 let output='',last=0;const insertions=[];
 for(const edit of edits){output+=text.slice(last,edit.pos);insertions.push({at:output.length,text:edit.text});output+=edit.text;last=edit.pos;}
 output+=text.slice(last);
 acorn.parse(output,{ecmaVersion:'latest',sourceType:'script'});
 let reversed=output;for(const e of [...insertions].reverse()){if(reversed.slice(e.at,e.at+e.text.length)!==e.text)throw new Error('Insertion identity');reversed=reversed.slice(0,e.at)+reversed.slice(e.at+e.text.length);}
 if(reversed!==text)throw new Error('Insertion removal changed original bytes');
 return {output,roles,owners,insertions:insertions.map(e=>({at:e.at,length:e.text.length,sha256:hash(e.text)})),roundTrip:true};
}
for(const [side,name]of Object.entries(names)){
 const root=path.join(base,name),record={root,files:{}};manifest.sides[side]=record;
 for(const file of ['index.html','moon/moon-host.js','real-sky/native-sky.js']){
  const original=fs.readFileSync(path.join(root,file)),text=original.toString('utf8');
  if(!Buffer.from(text).equals(original))throw new Error('Non-UTF8 source');
  let output,parts=[];
  if(file.endsWith('.html')){
   output=text.replace(/<script\b([^>]*)>([\s\S]*?)<\/script>/g,(whole,attrs,js)=>{
    if(!js.trim()||/type\s*=\s*["']application\//.test(attrs))return whole;
    const id=/\bid=["']([^"']+)/.exec(attrs)?.[1]||'';
    const r=processSource(js,file,id);parts.push({scriptId:id,...r,output:undefined});
    return '<script'+attrs+'>'+r.output+'</script>';
   });
  }else{const r=processSource(text,file,'');output=r.output;parts.push({...r,output:undefined});}
  const out=path.join(dest,side,file);fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,output);
  record.files[file]={originalSha256:hash(original),instrumentedSha256:hash(output),originalBytes:original.length,instrumentedBytes:Buffer.byteLength(output),parts};
 }
}
fs.writeFileSync(path.join(dest,'SOURCE-MAP.json'),JSON.stringify(manifest,null,2)+'\n');
for(const [side,rec]of Object.entries(manifest.sides))console.log(side,JSON.stringify(Object.entries(rec.files).map(([file,r])=>({file,roles:r.parts.flatMap(p=>p.roles.map(x=>x.role)),owners:r.parts.flatMap(p=>p.owners)}))));
