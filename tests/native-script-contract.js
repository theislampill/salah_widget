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
  // R000B first-paint rebind: reviewed composition and preview-host changes on
  // engineering baseline eebba178172f96b3ffe5ab3845bc0fffd57c6e1b, with uncommitted
  // frozen owners (not a source-revision claim for the separate plan HEAD):
  // real-sky/native-composition.mjs SHA256 d3e5d216cad8942e923c9418ed18458f8d8a6e719238c7001288c730323e4fb5
  // real-sky/native-preview-host.mjs SHA256 2d77893c59b5fd25fcbe5a647133e6a9e7aacd986f143666975e811d3412b3e8
  // Moon bodies retain the review at f71fef6ccf7e4efcb57b5a26688d2360461a3253.
  // A new delivery requires explicit source review/rebinding, never an automatic
  // update from the same untrusted body whose admission is being checked.
  // R0021 rebind (branch claude/r0021-instance-lifecycle-20261111 over 645b53cc):
  // first-paint carries the preview-host construction custody; moon-initial
  // carries moon-install-guard.mjs and the instance-captured detail in
  // moon-native.mjs. Previous pins, retained for attribution: first-paint
  // be62ab92d4eb436981a2a3f8ce48c4961249c2904f14d31435f75d8a2657a9c7 (R000B),
  // moon-initial 837b77f23fffcb5fc24c3561632143733653d32918046dd1f65a17e227456a14
  // (f71fef6c review). moon-refinement is unchanged.
  // R0021 second rebind at de68e848: moon-initial 5f1d42df4e3d962a9c0b82d30db77db3291ba0083de4489516dc76050e2aafe5
  // (dcc8206b) -> 4dc7140f (Moon detail acquired at the registration boundary with unwind).
  // R0021 third rebind at 145b7ba9: moon-initial 4dc7140f763417d0d8928e02f96cb010eec31f5363fb234f656785d7bfaae90b
  // (de68e848) -> d5e648ac (a half-built runtime reports disposed and leaves the registry slot).
  // R0027 first-paint rebind: the only R0027 change to the generated first-paint body is
  // the reviewed retention-only spectral transform (tools/native_core_spectral_cache.py,
  // generated real-sky/core/src/spectral.mjs SHA256
  // 4fcda07d1fc5a210d7d748a4c33518ed3068dbbf25eacf7415fa10abaad14489). History: R0027 on accepted main
  // 645b53cc5d04d35444f6da0e27bf5a5b6b11ce67 rebound be62ab92 (R000B) -> 8817c6599ff3958574b8d34f0cf9355368522ce03a6bc4e70fa5adfcedddcd8b;
  // R0027 stacked on the R0021 candidate 68891b4f (main 32f97b06): R0021 a0f86bc427d9708befb520439dbaac78af16a21ef2be7825643f2c6ccc198819
  // -> 1ba361b6 (R0021 body plus the same spectral transform).
  const SPLIT_PINS=Object.freeze({
    'first-paint':'1ba361b60f46ac631f70315b2542018c151013cb83c6b4e0f458da63ed55769e',
    'moon-initial':'d5e648ac08b80a8291140eddbd73dc7305aa7d40f38ebcbea71e239d5be54f16',
    'moon-refinement':'d4f90ac35284f19e4675b6314ae60b0fc4ad441be54b1b78c74c173b1d80d7a4'
  });
  // Complete older or authored documents need an independent identity, not
  // merely fewer surviving script tags. Current generated semantic mutants remain admissible:
  // no current native-body digest is pinned here.
  const RETAINED_INPUTS=Object.freeze({
    // R0027 stacked on the R0021 candidate 68891b4f (main 32f97b06) by merge 5dd7c558: legacy-Moon structural control
    // of index e3a3dedb (R0021 generated index plus the R0027 spectral hunks only). The authored source is R0021's,
    // unchanged; every entry below, including R0021's 4af7e86f and R0027's 902f326d, remains admitted unchanged.
    '1a5c50314e0d4c86dd2a7222211843a154e899addc44bffc944fa74777125fc8':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'5dd7c558207d76aa022f0bda73354918cc3bfc46',path:'index.html',
      parentSha256:'e3a3dedbfaaf5e5d604add26fa071852da109d72773a077b444fdd376f771185',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0021 stacked on the R000F candidate 2aa3bd11 (R0003 54e29e6a, main 7f2e8d16) by merge 65f7c75a: legacy-Moon
    // structural control of index 0f765e33. The authored source is the admitted b09f51ed (64258c86) unchanged;
    // every entry below, including R0021's 20d1a5b0 (dcc8206b), remains admitted unchanged.
    '4af7e86f00694948bec61dae4d0d9b36218a125d40828bebcc06f5abe49c91f7':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'65f7c75a89bbc9f737dc72d8cbf79a213fc76a73',path:'index.html',
      parentSha256:'0f765e335ffb348d4f3cd35f2c379dfd13e8998b3f7df5e7496583561c4925fb',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0003 reconciled onto accepted main 7f2e8d16 (R0026) by merge 64258c86;
    // explicitly rebound like the a06957c6 and ff7b042d inputs below, which remain admitted unchanged.
    'b09f51ed5d48f8b3978b5644e3661fee3935886744e4b320853a1c5bb815ffd8':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'64258c865846aa27b70681ae33038dae017f864c',path:'src/native/index.html',layout:'config,native'}),
    '5269f97a5370cf26469f30a47b53d3d17c23e3286f91347f1c1f7995409f286d':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'64258c865846aa27b70681ae33038dae017f864c',path:'index.html',
      parentSha256:'9f2fb30b19aa103c2511418970291bba84dbe3bf3acaca536f4410a8669498d5',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0003 configuration-effect classifier at a06957c6 on accepted main 645b53cc;
    // explicitly rebound like the ba0851ae inputs below, which remain admitted unchanged.
    'e7538e8767d3dc95c11031becc9a2a26d05833617baf1bcf73aa430ad32eb6e7':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'a06957c6ef3f838e3b02c664492b4423342d60ab',path:'src/native/index.html',layout:'config,native'}),
    'ee53ffdce473d0381cc1ec532bbd6b763b1978ed8dddca68dadbd2d9207c0d5f':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'a06957c6ef3f838e3b02c664492b4423342d60ab',path:'index.html',
      parentSha256:'598287a419f43ce52eb71d4c68e0f3d51013446bbf89666086ce1f40150fed21',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0026 review follow-up (settings partial/unavailable wording) at ff7b042d;
    // explicitly rebound like the ba2a8679 inputs below, which remain admitted unchanged.
    'b68ed74b5c3b110d231c3672628b98925dae09bd1836b04bb61602469be97b34':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'ff7b042d8a65b9376e40da26e5ffcf10d6ca0233',path:'src/native/index.html',layout:'config,native'}),
    'aec0d2243be01598cebb89ba87ad31bc2c992ffd5b4eb55a3e600f7754415f74':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'ff7b042d8a65b9376e40da26e5ffcf10d6ca0233',path:'index.html',
      parentSha256:'987125da46481042b6c8a5eacceec638b99a090cd61afbca6918d9115b281f82',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0026 settings search consumer (detailed outcomes) at ba2a8679 on accepted main 645b53cc;
    // explicitly rebound like the ba0851ae inputs below, which remain admitted unchanged.
    'bcd68708a37f2fab9546c113b8c4b141e6b79fb4bcb511d73655058f1dd7f867':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'ba2a867939a60ab3814a82f89fa18757022ce2ff',path:'src/native/index.html',layout:'config,native'}),
    '4604961a23877063a80a84822ce2dc0532903fb92b8146e21117c514b06519cf':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'ba2a867939a60ab3814a82f89fa18757022ce2ff',path:'index.html',
      parentSha256:'01b720c58e4885978af06c2b3893256cfeae425139418b4fab7279a5b1f8ad5c',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0021 instance lifecycle at dcc8206b0e466fefc4827872e7d784b99ff56c63 over accepted main 645b53cc: legacy-Moon
    // structural control of index c6e0e2e0; earlier entries below remain admitted unchanged.
    '20d1a5b0564d0bc8bb5d4f56a3b65ed33b4738d7b49494293dcca2c26b2f7f0c':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'dcc8206b0e466fefc4827872e7d784b99ff56c63',path:'index.html',
      parentSha256:'c6e0e2e089d53a00626c3014f1db040162af8849a35973d8b453b1c19b00a2ff',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0027 generated spectral retention on accepted main 645b53cc: only the generated
    // root index.html changed (authored src/native/index.html unchanged, so its
    // R000D identity below stays current); the R000D inputs below remain admitted unchanged.
    '902f326da4b79e3e64b56877b8a2a93421174f6e893a00f423b049f13d57f052':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'77014952203f373d3646cef7ea291a2196833aa6',path:'index.html',
      parentSha256:'df1c6e9daf008247d9c6377275a6a905039ff58e2d4c21694d8824590022b37f',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R000D elapsed retry record at ba0851ae on accepted main da126880;
    // explicitly rebound like the d5ede8b9 inputs below, which remain admitted unchanged.
    '2444e2a9017a4ce3e54c5a3f186668798f29b883fe0fe869f036dcf80f44c81c':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'ba0851ae28520c0b402dcbd876e3135f502500df',path:'src/native/index.html',layout:'config,native'}),
    '7a83847286468bd9f2443e36b2709ba555e89bf79a9523d8e19b28eb6a2b7a9d':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'ba0851ae28520c0b402dcbd876e3135f502500df',path:'index.html',
      parentSha256:'e41ba4341cb22741f97719dc08bccfad895f8fe5f11bc67288ad70663913f1f5',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R000B reconciled with accepted main dbf3370f (R0017 + R0007) at merge
    // d5ede8b9; explicitly rebound like the ec69edf inputs below, which remain
    // admitted unchanged.
    '2fb7e8e04175b921b7d4c9057b0c655db89f9064c01b52068124394d0d334dfd':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'d5ede8b9f9a03953dba58eb3525e86c3d1653084',path:'src/native/index.html',layout:'config,native'}),
    '240178afe7e01d8cbe64ce3aa4de5ccdab41713188ee292e7813f26d4909eb98':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'d5ede8b9f9a03953dba58eb3525e86c3d1653084',path:'index.html',
      parentSha256:'dc2af3801a4314d062ed904c7c95610a0f6afd37166e1e7ef88cf1d5bd97dc82',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0007 gated web-font activation at ec69edf; explicitly rebound like the
    // 5e946fe inputs below, which remain admitted unchanged.
    'e059305e2602adead696c2639c5332656e240f1b58628dde05924414ea99bc8d':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'ec69edf863cae569462d91a4a5ae2feb6554fbe1',path:'src/native/index.html',layout:'config,native'}),
    '494b8424a5e35108aec7604cb2e2fbda7ca33c61522005786e3674176fb5aa15':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'ec69edf863cae569462d91a4a5ae2feb6554fbe1',path:'index.html',
      parentSha256:'5a200d9ab428c24ad7967253ee57156fcbca3483c123eed228bd88fd354dd6ab',
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
