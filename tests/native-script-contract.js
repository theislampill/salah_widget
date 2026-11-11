/* Shared test-adapter contract. No product script is rewritten or executed here. */
(function(root,factory){
  const contract=factory();
  if(typeof module==='object'&&module.exports)module.exports=contract;
  else root.SalahNativeScriptContract=contract;
})(typeof globalThis==='object'?globalThis:this,function(){
  'use strict';
  class SetupError extends Error {
    constructor(message){super('SETUP_INCOMPLETE: '+message);this.name='SetupError';this.code='SETUP_INCOMPLETE';}
  }
  const requireSetup=(condition,message)=>{if(!condition)throw new SetupError(message);};
  const MOON_FILE_BOOTSTRAP='if(location.protocol==="file:")window.__SALAH_MOON_OFFLINE__=true;';
  // Reviewed generated prerequisite bodies at f71fef6ccf7e4efcb57b5a26688d2360461a3253.
  // A new delivery requires explicit source review/rebinding, never an automatic
  // update from the same untrusted body whose admission is being checked.
  const SPLIT_PINS=Object.freeze({
    'first-paint':'3591c4460aeb291e487ef1f750071b6b7436fa904b619fb3b54659c6fa4b83ed',
    'moon-initial':'837b77f23fffcb5fc24c3561632143733653d32918046dd1f65a17e227456a14',
    'moon-refinement':'d4f90ac35284f19e4675b6314ae60b0fc4ad441be54b1b78c74c173b1d80d7a4'
  });
  // Complete older or authored documents need an independent identity, not
  // merely fewer surviving script tags. Current generated semantic mutants remain admissible:
  // no current native-body digest is pinned here.
  const RETAINED_INPUTS=Object.freeze({
    // R0007 gated web-font activation at 58fc4af; explicitly rebound like the
    // 5e946fe inputs below, which remain admitted unchanged.
    '88740f02ef00fdcf821331b56f7ef387ec4f852d450b0e1f1765891bbe4a7ad4':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'58fc4afcfef2ca15cc03f845aaf79cc0084a60c1',path:'src/native/index.html',layout:'config,native'}),
    'ae29298b28f7ab72acb8e6803b672a1817012744d68fff7ddd41c3361e7c1f54':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'58fc4afcfef2ca15cc03f845aaf79cc0084a60c1',path:'index.html',
      parentSha256:'a6a2bec1333122b5dfe944cb33268172d13f886d00a423287e5b1d2e01324c0e',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0007 source reviewed at 5e946fe; these complete inputs are admitted by
    // explicit identity. Earlier retained records and split prerequisites stay
    // unchanged; this does not admit an altered authored or structural input.
    'e8603192a095cd8682c35416f3ecca00938d772f5152324b37f9928077eac037':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'5e946fe18a31750cf528bd58210ce79182dcf1e1',path:'src/native/index.html',layout:'config,native'}),
    'c60eef46e0feeb4fcbc2daa34ec7069af470326648d8cf53943ee42a21865308':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'5e946fe18a31750cf528bd58210ce79182dcf1e1',path:'index.html',
      parentSha256:'983f8b609eba48821e8d8c539cca7d0b9e40caf3f35a924514a4e93eb24766e9',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    '6054f1eb3e7f04aa5975707345810b64fc824bc99e17ce3798369a959a123fad':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'f71fef6ccf7e4efcb57b5a26688d2360461a3253',path:'src/native/index.html',layout:'config,native'}),
    '446453b522f56f5f1bc0afd1a3abd09b73756754fa58a6b3b0ff09ce953a2eec':Object.freeze({
      profile:'retained-historical-native',kind:'historical-source',commit:'fd2972ba64225fe9d6848e92497e6d0ed20ea624',path:'index.html',layout:'config,native'}),
    'd4e3f084aea7d264a5c790268a21aa015b5e565e1feb9ad853d953c1c8a7b26f':Object.freeze({
      profile:'retained-historical-legacy-moon',kind:'historical-source',commit:'ed5e7afbd2fcf7a59050817e2a561bcdbfa9043d',path:'index.html',layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    'bbe447167dcb751b9463b54ee29bcdcbbfeb0a521c4cd93f59b4bd429cca6b1e':Object.freeze({
      profile:'retained-historical-native',kind:'historical-source',commit:'47c0fa0c6e32618f22b43b6a18717908b0de5f5e',path:'index.html',layout:'config,native'}),
    'ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee':Object.freeze({
      profile:'retained-historical-legacy-moon',kind:'historical-source',commit:'18ff14860ff41c084b1db5f396bb62aa9c22b1be',path:'index.html',layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    'f6650909f7d2defc2edffa25c7510b4ae476fc3208d4a9625090107ff77de1de':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'f71fef6ccf7e4efcb57b5a26688d2360461a3253',path:'index.html',
      parentSha256:'b4a6831b80439d3002f9cf4fae5bc15943bc9f9f2fa5ab0c4a1fc09f33a57298',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'})
  });
  function parseScripts(source){
    requireSetup(typeof source==='string','Expected widget source text');
    return [...source.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
      .map(match=>({attributes:match[1],body:match[2]}));
  }
  function admitScripts(source,scripts,digests,sourceSha256){
    requireSetup(Array.isArray(digests)&&digests.length===scripts.length,'Missing script source identities');
    const roles=scripts.map(script=>{
      const attrs=script.attributes.trim(),body=script.body;
      if(!body.trim()){
        if(attrs==='src="config.js"')return 'config';
        if(attrs==='src="real-sky/native-sky.js"')return 'sky';
        if(attrs==='src="moon/moon-host.js"')return 'moon-host';
      }
      if(/^id="native-first-paint-code" data-sha256="[a-f0-9]{64}"$/.test(attrs))return 'first-paint';
      if(attrs==='id="moon-initial-code"')return 'moon-initial';
      if(attrs==='id="moon-refinement-code"')return 'moon-refinement';
      if(!attrs&&body.trim()===MOON_FILE_BOOTSTRAP)return 'moon-file';
      if(!attrs&&body.trim())return 'native';
      throw new SetupError('Unreviewed widget script anchors');
    });
    const count=role=>roles.filter(value=>value===role).length;
    requireSetup(count('first-paint')<=1,'Duplicate first-paint owner');
    requireSetup(count('moon-file')<=1,'Duplicate Moon file initializer');
    requireSetup(count('native')===1,'Unreviewed widget script anchors: Expected exactly one native inline runtime');
    const nativeIndex=roles.indexOf('native'),native=scripts[nativeIndex];
    requireSetup(native.body.split('\nboot();').length===2&&/\nboot\(\);\s*$/.test(native.body),'Expected the real boot caller');
    const documentSource=roles.includes('config')||/<!doctype\s+html|<(?:html|head|body)(?:\s|>)/i.test(source);
    if(documentSource)for(const anchor of ['async function fetchTimings(','async function loadPrayerData(','function model(','function render(','window.qaState=function()','async function boot(){'])
      requireSetup(native.body.split(anchor).length===2,'Missing or ambiguous native owner: '+anchor);
    const layout=roles.join(','),retained=documentSource?RETAINED_INPUTS[sourceSha256]:null;
    const split=documentSource&&!retained;
    // Tiny script-only fixtures retain their original structural-control scope;
    // a complete document must satisfy its real owner anchors and full layout.
    const snippetLayouts=['native','native,moon-file','first-paint,native'];
    requireSetup(split?layout==='config,first-paint,moon-initial,native,moon-refinement,sky':
      retained?layout===retained.layout:snippetLayouts.includes(layout),'Unreviewed widget script anchors');
    const prerequisites=[];
    for(let i=0;i<scripts.length;i++){
      const role=roles[i],body=scripts[i].body;
      if(role==='first-paint')requireSetup(scripts[i].attributes.includes('data-sha256="'+digests[i]+'"')&&body.includes('function prepareNativeFirstPaint()'),'First-paint source identity mismatch');
      if(split&&SPLIT_PINS[role])requireSetup(digests[i]===SPLIT_PINS[role],role==='first-paint'?'First-paint source identity mismatch':'Moon prerequisite source identity mismatch: '+role);
      if(role!=='native'&&body.trim())prerequisites.push({role,sha256:digests[i]});
    }
    return {native,nativeIndex,profile:split?'split-moon':retained?.profile??'structural-snippet',prerequisites,
      provenance:retained??{kind:split?'current-generated-profile':'structural-snippet'},runtimeQualified:false};
  }
  return Object.freeze({schema:'salah-native-script-adapter/1',SetupError,requireSetup,MOON_FILE_BOOTSTRAP,parseScripts,admitScripts});
});
