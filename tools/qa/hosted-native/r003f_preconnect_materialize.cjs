'use strict';
// Source-only derivative of the exact corrected B0 harness; no product writes.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {parseArgs}=require('node:util');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const PINS=Object.freeze({
  'r003f_materialize.cjs':'2fc95820151e08ff416ce10890a801045a960cd49c65eff499a1cf0ee4473fbc',
  'r003f_ui.cjs':'ccce93bcbe1bcd4834789e03ead8a2a104710e4955e05d57cc846ab4a341c82a',
  'r003f_preconnect_input.cjs':'6497cc23dd21cd9a622870dc51fceb8885a125d30b4b8776401ebc475e1ab3b7'
});
function need(value,message){if(!value)throw Error('R003F preconnect materialization: '+message);}
function pinned(name){
  const p=path.join(__dirname,name),s=fs.lstatSync(p);
  need(s.isFile()&&!s.isSymbolicLink(),'regular pinned helper required: '+name);
  const b=fs.readFileSync(p);need(sha(b)===PINS[name],'pinned helper differs: '+name);return b;
}
// Validate locally owned implementation bytes before evaluating their exports.
for(const name of Object.keys(PINS))pinned(name);
const B=require('./r003f_materialize.cjs'),S=require('./r003f_preconnect_input.cjs');
function driver(bytes,patches){
  let source=bytes.toString('utf8');
  const patch=(name,anchor,replacement)=>{
    source=B.replaceExactly(source,anchor,replacement,'preconnect '+name);
    patches.push({path:'tools/qa/r003f_owner_baseline.cjs',name,occurrences:1,preimageSha256:sha(anchor),postimageSha256:sha(replacement)});
  };
  patch('explicit-external-closure',"['root','out','engine','dpr','playwright','pngjs','executable']",
    "['root','out','engine','dpr','playwright','pngjs','executable','materialization-sha256']");
  const population="assert.ok(['chromium','firefox','webkit'].includes(engine) && [1,2].includes(dpr));";
  patch('population-and-source-admission-before-browser-import',population,population+
    "\nassert.ok(engine==='webkit' && dpr===1,'preconnect input diagnostic supports only WebKit DPR1');"+
    "\nconst I=require('./hosted-native/r003f_preconnect_input.cjs');"+
    "\nI.admitClosure(path.resolve(__dirname,'../..'),a['materialization-sha256']);"+
    "\nconst input=I.createInput({root,out});");
  patch('before-parse-document-callback','const server=makeServer(root), prayer=prayerFixture(ordinary,zone);',
    'const server=input.guardServer(makeServer(root,input.indexFor)), prayer=prayerFixture(ordinary,zone);');
  patch('distinct-diagnostic-identity',
    "  const report={protocol:'R003F/P1/B0-owner/2',harness:{protocol:'R003F/corrected-harness/1',kind:'corrected MIME and native UI admission',",
    "  const report={protocol:'R003F/P1/B0-preconnect-input/1',qualification:'ALTERED_INPUT_DIAGNOSTIC_ONLY',\n"+
    "    servedDocument:input.evidence,nativeAcceptance:'NOT_EVALUATED',humanAcceptance:'OUTSTANDING',\n"+
    "    harness:{protocol:'R003F/preconnect-input-harness/1',kind:'two exact preconnect spans omitted from served index before parsing',");
  patch('input-helper-identity',
    "    uiHelperSha256:digest(fs.readFileSync(require.resolve('./hosted-native/r003f_ui.cjs')))},engine,dpr,epoch,zone,hash,",
    "    uiHelperSha256:digest(fs.readFileSync(require.resolve('./hosted-native/r003f_ui.cjs'))),\n"+
    "    inputHelperSha256:digest(fs.readFileSync(require.resolve('./hosted-native/r003f_preconnect_input.cjs')))},engine,dpr,epoch,zone,hash,");
  patch('retain-each-actual-navigation-response',"      await p.goto(origin+'/index.html'+hash+suffix); return p;",
    "      let response;\n"+
    "      try{response=await p.goto(origin+'/index.html'+hash+suffix);}\n"+
    "      catch(error){input.recordNavigationFailure(error,origin+'/index.html');throw error;}\n"+
    "      await input.recordResponse(response,origin+'/index.html'); return p;");
  patch('document-admission-and-distinct-success',"    report.status='MEASURED'; await C.context.close();",
    "    input.assertComplete(); report.originalRecipeStatus='MEASURED';\n"+
    "    report.status='"+S.SUCCESS+"'; await C.context.close();");
  return Buffer.from(source);
}
function materialize({source,runtime,out}){
  need(source&&runtime&&out,'explicit --source, --runtime and --out are required');
  source=fs.realpathSync(source);runtime=fs.realpathSync(runtime);out=path.resolve(out);
  const outside=()=>need(![source,runtime].some(p=>out===p||out.startsWith(p+path.sep)),'output must be outside source and runtime');
  outside();need(!fs.existsSync(out),'output must not exist');
  const parent=fs.realpathSync(path.dirname(out));out=path.join(parent,path.basename(out));
  outside();need(!fs.existsSync(out),'output must not exist');
  const index=path.join(runtime,'index.html'),indexStat=fs.lstatSync(index);
  need(indexStat.isFile()&&!indexStat.isSymbolicLink(),'regular runtime index required');
  const documentInput=S.deriveIndex(fs.readFileSync(index)).identity;
  for(const name of Object.keys(PINS))pinned(name);
  const stage=fs.mkdtempSync(path.join(parent,'r003f-preconnect-stage-'));let created=false;
  try{
    const base=path.join(stage,'base'),baseReceipt=B.materialize({source,out:base});
    const baseBytes=fs.readFileSync(path.join(base,'materialization.json'));
    need(sha(baseBytes)===S.BASE_MATERIALIZATION,'original corrected materialization differs');
    const outputs=new Map(),outputFiles=[],patches=[];
    for(const row of baseReceipt.outputFiles){
      const original=fs.readFileSync(path.join(base,row.path));
      need(original.length===row.bytes&&sha(original)===row.sha256,'base output differs: '+row.path);
      const bytes=row.path==='tools/qa/r003f_owner_baseline.cjs'?driver(original,patches):original;
      outputs.set(row.path,bytes);outputFiles.push({path:row.path,baseSha256:row.sha256,sha256:sha(bytes),bytes:bytes.length});
    }
    const helper='tools/qa/hosted-native/r003f_preconnect_input.cjs',helperBytes=pinned('r003f_preconnect_input.cjs');
    outputs.set(helper,helperBytes);outputFiles.push({path:helper,baseSha256:null,sha256:sha(helperBytes),bytes:helperBytes.length});
    need(JSON.stringify([...outputs.keys()].sort())===JSON.stringify([...S.OUTPUTS].sort()),'output population differs');
    const receipt={protocol:S.SOURCE_PROTOCOL,status:'PREPARED',baseMaterializationSha256:sha(baseBytes),baseMaterialization:baseReceipt,
      materializerSha256:sha(fs.readFileSync(__filename)),inputHelperSha256:sha(helperBytes),documentInput,outputFiles,patches,
      productFilesCopied:[],assetBytesChanged:false,nativeExecution:'NOT_RUN'};
    fs.mkdirSync(out,{mode:0o700});created=true;
    for(const [relative,bytes] of outputs){const p=path.join(out,relative);fs.mkdirSync(path.dirname(p),{recursive:true,mode:0o700});fs.writeFileSync(p,bytes,{flag:'wx',mode:0o600});}
    fs.writeFileSync(path.join(out,'materialization.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx',mode:0o600});
    S.admitClosure(out,sha(fs.readFileSync(path.join(out,'materialization.json'))));
    return receipt;
  }catch(error){if(created)fs.rmSync(out,{recursive:true,force:true});throw error;}
  finally{fs.rmSync(stage,{recursive:true,force:true});}
}
if(require.main===module){
  try{const {values}=parseArgs({options:{source:{type:'string'},runtime:{type:'string'},out:{type:'string'}}});console.log(JSON.stringify(materialize(values),null,2));}
  catch(error){console.error(JSON.stringify({protocol:S.SOURCE_PROTOCOL,status:'INCOMPLETE',error:error.message}));process.exitCode=2;}
}
module.exports={PINS,materialize};
