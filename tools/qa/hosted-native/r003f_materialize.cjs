'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {parseArgs}=require('node:util');
const {readNativeUi,admitNativeUi}=require('./r003f_ui.cjs');
const SOURCE_REFERENCE='156f95d0e3ec692919dc33a1c68f76ea3ef91353';
const INPUTS=Object.freeze({
  'tools/qa/r003f_owner_baseline.cjs':'a270d91d05b16d0238ac9058eec09561f0739ec0d599a636fef585f6979bede0',
  'tools/qa/r003f_capture.cjs':'af84f6c9de2534658ddc327618622a6b33803a141c026927a44890805317b982',
  'tools/qa/r003f_p1.cjs':'eaabdfa55a1043a701ef08643b7a304cce6bad217073f2d30f3c51ecc599d380',
  'tools/qa/r003f_grid.cjs':'532de10b100f3388b1fa677a4e61c1afdb221628c23c50b1229a2530ef1845a3',
  'tools/qa/r0033_isolation.cjs':'2aef5788ea21cf33a201348e2e4ab901c6d0a8d7c16251859411768cb4b8132a',
  'tools/qa/v1_net_guard.cjs':'2b00cb52a72384862156f7ba771bc5daedcb420780b05b84cf8366962b4affab',
  'real-sky/native-sky.css':'298a11d0d91a801de2e8f63b7e4997ff33d7a7423ebd0e4c8a0bbd5710f68f31'
});
const COPIED=Object.freeze(Object.keys(INPUTS).filter(p=>p.startsWith('tools/qa/')));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function replaceExactly(source,anchor,replacement,label){
  const count=source.split(anchor).length-1;
  if(!anchor||count!==1)throw new Error(label+': expected exactly one source anchor, found '+count);
  return source.replace(anchor,()=>replacement);
}
function browserReceiptSource(){
  return 'function nativeUiReceipt(){\n  const readNativeUi='+readNativeUi.toString()+';\n  const admitNativeUi='+admitNativeUi.toString()+';\n  return admitNativeUi(readNativeUi());\n}';
}
function corrected(relative,bytes,patches){
  let source=bytes.toString('utf8');
  const patch=(name,anchor,replacement)=>{
    source=replaceExactly(source,anchor,replacement,relative+' '+name);
    patches.push({path:relative,name,occurrences:1,preimageSha256:sha(anchor),postimageSha256:sha(replacement)});
  };
  if(relative==='tools/qa/r003f_capture.cjs'){
    patch('css-mime',"const types = {'.html':'text/html',","const types = {'.css':'text/css','.html':'text/html',");
    const imports="const fs=require('node:fs'),path=require('node:path'),http=require('node:http');";
    patch('ui-import',imports,imports+"\nconst {assertNativeUi}=require('./hosted-native/r003f_ui.cjs');");
    patch('read-only-ui-observation','function facts() {',browserReceiptSource()+'\nfunction facts() {\n  const nativeUi=('+browserReceiptSource()+')();');
    patch('retain-ui-in-facts','  return {motionClock:','  return {nativeUi,motionClock:');
    patch('ui-exports','module.exports={makeServer,prayerFixture,clearWeather,facts,readUiMask,checkPair,aperture,riseBracket};',
      'module.exports={makeServer,prayerFixture,clearWeather,facts,readUiMask,checkPair,aperture,riseBracket,nativeUiReceipt,assertNativeUi};');
  }
  if(relative==='tools/qa/r003f_owner_baseline.cjs'){
    patch('ui-import','const {makeServer,prayerFixture,clearWeather,facts,readUiMask}=require(\'./r003f_capture.cjs\');',
      'const {makeServer,prayerFixture,clearWeather,facts,readUiMask,nativeUiReceipt,assertNativeUi}=require(\'./r003f_capture.cjs\');');
    const after="  const sha256=digest(png), lightVerdict=calendarLightVerdict(state);";
    patch('post-capture-ui-observation',after,
      "  let nativeUiAfter;\n  try{nativeUiAfter=await page.evaluate(nativeUiReceipt);}\n  catch(error){nativeUiAfter={protocol:'R003F/native-ui/1',status:'INCOMPLETE',failures:['post-capture-read-failed'],observed:{observationError:String(error?.message??error)}};}\n"+after);
    patch('retain-post-capture-ui','  report.captures[tag]={state,sha256,lightVerdict};','  report.captures[tag]={state,sha256,lightVerdict,nativeUiAfter};');
    patch('admit-after-original-assertions','  return {state,pixels:decoded.data};',
      '  assertNativeUi(state.nativeUi);assertNativeUi(nativeUiAfter);\n  return {state,pixels:decoded.data};');
    patch('corrected-harness-identity',"  const report={protocol:'R003F/P1/B0-owner/2',engine,dpr,epoch,zone,hash,",
      "  const report={protocol:'R003F/P1/B0-owner/2',harness:{protocol:'R003F/corrected-harness/1',kind:'corrected MIME and native UI admission',\n    materializationSha256:digest(fs.readFileSync(path.join(__dirname,'../../materialization.json'))),\n    driverSha256:digest(fs.readFileSync(__filename)),captureHelperSha256:digest(fs.readFileSync(require.resolve('./r003f_capture.cjs'))),\n    uiHelperSha256:digest(fs.readFileSync(require.resolve('./hosted-native/r003f_ui.cjs')))},engine,dpr,epoch,zone,hash,");
  }
  return Buffer.from(source);
}
function regularInput(root,relative){
  let current=root;
  for(const component of relative.split('/')){
    current=path.join(current,component);const stat=fs.lstatSync(current);
    if(stat.isSymbolicLink())throw Error('source symlink is not admitted: '+relative);
  }
  if(!fs.statSync(current).isFile())throw Error('source is not a regular file: '+relative);
  return fs.readFileSync(current);
}
function materialize({source,out}){
  if(!source||!out)throw Error('explicit --source and --out are required');
  source=fs.realpathSync(source);out=path.resolve(out);
  if(out===source||out.startsWith(source+path.sep))throw Error('output must be outside source');
  if(fs.existsSync(out))throw Error('output must not exist');
  const parent=fs.realpathSync(path.dirname(out));out=path.join(parent,path.basename(out));
  if(out===source||out.startsWith(source+path.sep))throw Error('output must be outside source');
  if(fs.existsSync(out))throw Error('output must not exist');
  const inputs=new Map(),sourceFiles=[];
  for(const [relative,expected] of Object.entries(INPUTS)){
    const bytes=regularInput(source,relative),digest=sha(bytes);
    if(digest!==expected)throw Error('source digest mismatch: '+relative);
    inputs.set(relative,bytes);sourceFiles.push({path:relative,sha256:digest,bytes:bytes.length});
  }
  const patches=[],outputs=new Map(),outputFiles=[];
  for(const relative of COPIED){
    const bytes=corrected(relative,inputs.get(relative),patches);outputs.set(relative,bytes);
    outputFiles.push({path:relative,originalSha256:INPUTS[relative],sha256:sha(bytes),bytes:bytes.length});
  }
  const uiRelative='tools/qa/hosted-native/r003f_ui.cjs',uiBytes=fs.readFileSync(require.resolve('./r003f_ui.cjs'));
  outputs.set(uiRelative,uiBytes);outputFiles.push({path:uiRelative,originalSha256:null,sha256:sha(uiBytes),bytes:uiBytes.length});
  const receipt={protocol:'R003F/corrected-harness/1',status:'PREPARED',sourceReference:SOURCE_REFERENCE,
    sourceAdmission:'exact per-file SHA-256; no claim that checkout HEAD was inspected',
    materializerSha256:sha(fs.readFileSync(__filename)),sourceFiles,outputFiles,patches,
    productFilesCopied:[],assetBytesChanged:false,nativeExecution:'NOT_RUN',matrixMotion:'NOT_INCLUDED'};
  fs.mkdirSync(out,{mode:0o700});
  try{
    for(const [relative,bytes] of outputs){const destination=path.join(out,relative);fs.mkdirSync(path.dirname(destination),{recursive:true,mode:0o700});fs.writeFileSync(destination,bytes,{flag:'wx',mode:0o600});}
    fs.writeFileSync(path.join(out,'materialization.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx',mode:0o600});
  }catch(error){fs.rmSync(out,{recursive:true,force:true});throw error;}
  return receipt;
}
if(require.main===module){
  try{
    const {values}=parseArgs({options:{source:{type:'string'},out:{type:'string'}}});
    console.log(JSON.stringify(materialize(values),null,2));
  }catch(error){console.error(JSON.stringify({protocol:'R003F/corrected-harness/1',status:'INCOMPLETE',error:error.message}));process.exitCode=2;}
}
module.exports={INPUTS,COPIED,replaceExactly,browserReceiptSource,materialize};
