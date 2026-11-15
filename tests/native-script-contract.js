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
  // R0033 rebind (issue 100, branch claude/r0033-moon-recovery-20261115 over main 90cccd2f):
  // moon-initial d5e648ac -> f233b816 (moon-native.mjs bounded recovery, initial-tier
  // eligibility, presence predicate and throw guards; build_moon.py construction-failure
  // head rule); moon-refinement d4f90ac3 -> 93afaebd (optional-call tail and the worker's
  // recovery cache mode). Both await independent source review with the R0033 candidate.
  // R0036 rebind (issue 103, branch claude/r0036-diagnostic-purity-20261115 over main a196351b):
  // moon-initial f233b816 -> 067034c8 (moon-native.mjs: the named presence predicate and the
  // non-adopting observe() diagnostic accessor; production getters unchanged). moon-refinement and
  // first-paint unchanged. Awaits independent source review with the R0036 candidate.
  const SPLIT_PINS=Object.freeze({
    'first-paint':'94f1927e521acffc6112ddd2dbe6866952b60c0eb966901741fc155cd7d91980',
    'moon-initial':'067034c815be4d8d024b5c36cb3ed64c00f96127e3b7078ce6f2449da01578d8',
    'moon-refinement':'93afaebdcb06b2d15d7d5381a90f0c976b3e465f70937cc7121045b186691117'
  });
  // Complete older or authored documents need an independent identity, not
  // merely fewer surviving script tags. Current generated semantic mutants remain admissible:
  // no current native-body digest is pinned here.
  const RETAINED_INPUTS=Object.freeze({
    // R0036 (issue 103) diagnostic purity, branch claude/r0036-diagnostic-purity-20261115 over main a196351b at a5c7e885:
    // authored source 26059840 and the legacy-Moon structural control 5b3abea2 of its generated index 388ee9ae. Every entry below remains admitted.
    '26059840189d3feea64ee4047728409f3c07a32d04d06eb0ebaca091489e554d':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'a5c7e885de13e859e5e0b4afc4660d09e18f2b14',path:'src/native/index.html',layout:'config,native'}),
    '5b3abea2a8ad31038a9ce4f5fff5cac14035b5342b53b90d39e32ba8eb08edef':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'a5c7e885de13e859e5e0b4afc4660d09e18f2b14',path:'index.html',
      parentSha256:'388ee9ae156223f4d7e643c1a4f261c8f2394e791b1e1230b275397c6e1ee925',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0033 re-bind after merging main 8990c36d (R0031): authored source 90b0f642 and the legacy-Moon structural control e0acbaae of its generated index 3615841c. Every entry below remains admitted.
    '90b0f642789a8ff0acf34a980f63a0625464d4cf0253571e227907d5fafb4bb8':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'0329221a249e588ec198115a4fe291cac4461180',path:'src/native/index.html',layout:'config,native'}),
    'e0acbaae2779808d4572d6e1c7086f0def471295c69180b02630f0d8638d9347':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'0329221a249e588ec198115a4fe291cac4461180',path:'index.html',
      parentSha256:'3615841cf332bec531b9d8756c6b53ced60e34e5052b0ebf62aafda303e9c608',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0033 re-bind after merging main 48ba76db (R0032): authored source ed528a43 and the legacy-Moon structural control 09cf6f64 of its generated index d526dd35. Every entry below remains admitted.
    'ed528a4344a10f1dbc8fa260027e22edd80bfad5dba76ed78a7cc367a2eda217':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'978d4be9966e6ce3677960d6023b916feb94677f',path:'src/native/index.html',layout:'config,native'}),
    '09cf6f641bbe3bf7b2ec010411c7f2998e8badb9d192b5f84c3f83f094f2bd01':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'978d4be9966e6ce3677960d6023b916feb94677f',path:'index.html',
      parentSha256:'d526dd35e4117bd46f9c8d060b63ed2ded1326f486766d85c0b2ab703a11c354',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0033 (issue 100) Moon recovery and light eligibility, branch claude/r0033-moon-recovery-20261115 merged with main
    // ebb2704e: authored source 7bd8ed2f and the legacy-Moon structural control of its generated index 18395d51.
    // Every entry below remains admitted unchanged. Re-bind again when rebuilt on a later main.
    '7bd8ed2f48e187bcb4b6322e8fc48d17b297816f050bec62c562e64e7e2423ce':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'claude/r0033-moon-recovery-20261115',path:'src/native/index.html',layout:'config,native'}),
    'a46c55335e63e14da44c106e0c1bc0bf5b778c07e94f915e9bfe9ccc9201d671':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'claude/r0033-moon-recovery-20261115',path:'index.html',
      parentSha256:'18395d5126091807a11dca66df462bd3fa9556ae4bc7e52ffc34eb3dc70bfbe9',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0031 GPS slice (issue 98, D-31-3 A) merged with main 93f7c262 at 100b7946: authored source 41f0dac6, structural control cbf30d6b of its generated index 1c79fc29. Every entry below remains admitted.
    '41f0dac66ed4ddfc2e6d520c8989bfe798d371b351b00d0d6887b7b9e0bcd013':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'100b79462a58cb3067d2d2915ead50bd35151c93',path:'src/native/index.html',layout:'config,native'}),
    'cbf30d6b6ecc435f70b44d78d565c43c37bea1711ba320325ebd272bd1fc123d':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'100b79462a58cb3067d2d2915ead50bd35151c93',path:'index.html',
      parentSha256:'1c79fc29c6431fd9896087aa66f050ed8b78eb70d23a4e070f9f4051a49dc696',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R003A merged with main 2722590f (R0034-A1, R0030) at d2b31fa1: authored source 07bbcaf9, structural control 4273983a of its generated index cccd79a0. Every entry below remains admitted.
    '07bbcaf9bdfa86d71ff6ea4690b7ca571139732d519c22c0c97cce775a3906a1':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'d2b31fa127343362ad8c8298bd85ffe450a5ce00',path:'src/native/index.html',layout:'config,native'}),
    '4273983a9376b60e51f0aed8b26863b4156c5d32ae2fe4544a74404b107bdad7':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'d2b31fa127343362ad8c8298bd85ffe450a5ce00',path:'index.html',
      parentSha256:'cccd79a0b040a6a218779b90c29c316e760e680a672ba2fbfbc09592d0966823',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R003A merged with main 9d903d6b (R002F) at 4ccf24c3: authored source 3cb56719, structural control 76ecda80 of its generated index c5fd54fc. Every entry below, including R002F's
    // and R003A's earlier entries, remains admitted unchanged.
    '3cb56719084e8f9bf11ad61b42089ef3aa47109c831d6b2d7aaad4c79c701f80':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'4ccf24c35da1c9503515559e10b758c5f51316fa',path:'src/native/index.html',layout:'config,native'}),
    '76ecda80bad3fa6d5e747b9b203c865cd803ff5e5e874e28a5e636f4cec27ece':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'4ccf24c35da1c9503515559e10b758c5f51316fa',path:'index.html',
      parentSha256:'c5fd54fcc9d4d104bab1380c0eddd3cc498e254a6e2f56434463add73919484c',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R003A reconciliation (issue 124 rewritten body) at a424a03d: authored source 646e8fdd (painter withdraws all five
    // solar optics first, owner gate G4 b) and structural control 0931aedc of its generated index e808f07d. Every entry below, including R003A's 4d5cc6aa/038b1667, remains admitted.
    '646e8fddcee9ab5970d785d751fea37dece28934ce6bd7fa855e9a1ff4cd9330':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'a424a03da01cef6e6feb54781bf43911b739910d',path:'src/native/index.html',layout:'config,native'}),
    '0931aedc20211413bfca17482df6f706dfa95dc1d91330c55857153fe45aa011':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'a424a03da01cef6e6feb54781bf43911b739910d',path:'index.html',
      parentSha256:'e808f07d4e41c6d9217033fcd67abfc00e6df8ba7b5d73cf1d5f792b8df9f8db',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R003A (issue 124) sky-stage hardening at 6de96906 on main 516d8cc8: authored source 4d5cc6aa (no-timetable optic
    // withdrawal list and one comment) and the legacy-Moon structural control 038b1667 of its generated index 401e3472. Every entry below, including R0034's 9bbec583 and R002E's 3c80fd51, remains admitted unchanged.
    '4d5cc6aae336f46e98d47eb5c0d15b0723f196b5803a23c03e3b936b17cd20e6':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'6de9690685f0bc3eabde3c2a6566f39186c30551',path:'src/native/index.html',layout:'config,native'}),
    '038b1667838d448ac8a4cceda7459f2a0349c00ad9ae0fad7dbdc7f7d707f7e6':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'6de9690685f0bc3eabde3c2a6566f39186c30551',path:'index.html',
      parentSha256:'401e34720bc29f6c77cf173f5689e0b6feb400d9cf43e55abd8b19a5ecaa130f',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0030 (issue 97) candidate 2969319f merged with main 9d903d6b (R002F): authored source fc353bf6 and the legacy-Moon
    // structural control of its generated index 7c2175b2. Every entry below, including R002F's and the earlier R0030 ones, remains admitted.
    'fc353bf6562ef4fadc34a82366ef7f80587e8a3f977d9f6dc6a83ad29661a490':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'2969319fda7ab49b9b349faf2ffe22065b860aed',path:'src/native/index.html',layout:'config,native'}),
    '605f9d68658c7cd9b0f8e8496f6a71969f0eff3f2eb8f60c8c8e0234399ab9a5':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'2969319fda7ab49b9b349faf2ffe22065b860aed',path:'index.html',
      parentSha256:'7c2175b281e3f441ca803f4f63f2396a3fa70cea9e33b1235eeebba6eb6b9ffa',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0030 (issue 97) settings Reset authority at 02451947 on main 516d8cc8: authored source 87619166 and the
    // legacy-Moon structural control of its generated index f475f8ca. Settings block only; every entry below remains
    // admitted unchanged. Re-bind again when rebuilt on a later main.
    '87619166e79e2b50300b43002bd1acfda907aba25b4ef56424f6e36ae34ea211':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'024519475b45c468e94eb39c2b1eb5b2275ab468',path:'src/native/index.html',layout:'config,native'}),
    '364b384e0407c772b1493d3cb7d76657116dbf9ef5d988fe592d8021e1e982e9':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'024519475b45c468e94eb39c2b1eb5b2275ab468',path:'index.html',
      parentSha256:'f475f8ca0576b3d3e11c8c3bd957c1d0e85d2e035587203c4a4aa3757378243f',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0034 (issue 101) refined-sky identity candidate 1f13b185 on main 664ebe22: the authored native body is unchanged
    // (no new authored entry); legacy-Moon structural control of its generated index dbc77c67. Every entry below,
    // including R002E's 3c80fd51 and 3c1f1a0a, remains admitted unchanged. Re-bind again when rebuilt on a later main.
    '9bbec5832f3a6c4cd13e731a41ea59f5e0996988a5da07400238ac80a9ad071f':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'1f13b185dc82ff4319aaf2d1311af114e9137e4f',path:'index.html',
      parentSha256:'dbc77c678d45c83f73297808cba729258b82903df7d0b771164a988465865190',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0031 GPS slice (issue 98) merged with main 48ba76db (R0032) at 83b9b5df: authored source 27500ed5 and the
    // legacy-Moon structural control of its generated index 78c3ae8a. Every entry below remains admitted.
    '27500ed5c462451f6685915b9d9ee40f3171516ee09144de6ca4e549fa78f070':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'83b9b5df52678fffd01318e18f5c1530ded48aee',path:'src/native/index.html',layout:'config,native'}),
    '08800e5a9c882880c83a6640fd30d94328b2d36c0b701ef2208bfc1619ae2a78':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'83b9b5df52678fffd01318e18f5c1530ded48aee',path:'index.html',
      parentSha256:'78c3ae8a01a9c1398682f92a463d95a6bfd076f427c9af8042cb7ec1d3ec6bd0',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0032 (issue 99) review round merged with main 93f7c262 (R003A) on R0032 tip 3162f303: authored source 074bdc2a and the
    // legacy-Moon structural control of its generated index a2336574. Every entry below remains admitted.
    '074bdc2a599ffa02cab61b463800ad96991bbbde631b808d0991afa5993fbbd2':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'3162f30341c7d096ffcdef887090c1910b7b2c65',path:'src/native/index.html',layout:'config,native'}),
    '9f4e8ed3ba7f5d2b397b0e430e6dd3946858decb5c2bfb0b40e40fc8fe41b553':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'3162f30341c7d096ffcdef887090c1910b7b2c65',path:'index.html',
      parentSha256:'a233657480dd35f31364fa99d07aedb015e4204077410a5581f70a0d4290caaf',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0032 (issue 99) merged with main ab4a8751 (R0030) on R0032 tip b3529605: authored source a890727f and the legacy-Moon
    // structural control of its generated index 740ac7e7. Every entry below, including R0032's unmerged d78aab9f/583ae220, remains admitted.
    'a890727f1aec54b0bdde36aad209426a804aed20dcda08b60a39686c01895b4d':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'b35296055a8a04f3a27d6e310109f422f377236d',path:'src/native/index.html',layout:'config,native'}),
    'dd8b9cfdd232a3010d7b441a9dd0542bfe644a91b43d54e29cbe05fde3821b45':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'b35296055a8a04f3a27d6e310109f422f377236d',path:'index.html',
      parentSha256:'740ac7e746edf2a24d4f4c4400808f1c2d99ece079803c175bb7174832919ca1',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R0032 (issue 99) location retention and radar minimisation da1de6ce on main 90cccd2f: authored source d78aab9f
    // and the legacy-Moon structural control of its generated index 998908b5. Every entry below remains admitted unchanged.
    'd78aab9fc94b10b91094b83eed58b9c2c5b3cab5040a3490856c367854a3976a':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'da1de6ce9402937d5ca1a5dd75b0d6f0144a14e3',path:'src/native/index.html',layout:'config,native'}),
    '583ae2200eb779a1d0b710dc3aa22fd5982edaa6fd54b0303be48d9fd1ca27c5':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'da1de6ce9402937d5ca1a5dd75b0d6f0144a14e3',path:'index.html',
      parentSha256:'998908b50e770b66db5137a75a5f805f9f6d8b1ed1f9269116492f66a1141f9f',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R002F (issue 96) weather renewal and preview range, merged with main 516d8cc8: authored source cbefc6cb
    // and the legacy-Moon structural control of its generated index 226266a2. Every entry below, including
    // R002E's 3c80fd51 and 3c1f1a0a, remains admitted unchanged.
    'cbefc6cb456696d4c1a1e075c1d0ae2cd64f4870f77749910354164e1f782461':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'f7e35be7a70b584990f555762c28056fb75cd91c',path:'src/native/index.html',layout:'config,native'}),
    '580a0ee3b199b2f1649e4a77030b5699f03905138c72687e85469314c17791d8':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'f7e35be7a70b584990f555762c28056fb75cd91c',path:'index.html',
      parentSha256:'226266a2b8d4862df980e76744d6ab3a833e11f8cf7392efed5297ccf45a231c',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R002E (issue 95) prayer presentation residuals merged with main 885d5a31 at 421a44a9: authored source 3c80fd51
    // and the legacy-Moon structural control of its generated index 3a93bfc9. Every entry below, including R002C's
    // 88eade13 and 78079b51, remains admitted unchanged.
    '3c80fd51023af712f4c20f86afbdb77811b0fc908bfb841165b3a2137975dcaf':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'421a44a95adec4050413c073af7e9d8aab843175',path:'src/native/index.html',layout:'config,native'}),
    '3c1f1a0a0793e7ebab2d3dcf509ab7b0187eb12757cd84af558f2f6a8c98a849':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'421a44a95adec4050413c073af7e9d8aab843175',path:'index.html',
      parentSha256:'3a93bfc9168508bd7643e28bba31fbc7d35b0eada21a56113361dedf01d916ba',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R002C (issue 93) render-loop containment at 46908d51 (review corrections; replaces the undelivered 6e4e4588 entry 147b96cd/224a104d), on main bcd02af2: authored source
    // 88eade13 and the legacy-Moon structural control of its generated index 531bea69. Every entry below, including
    // R002D's e6cd59af and 9e8f20a6, remains admitted unchanged.
    '88eade138fc6cdaa42d9f1c4d086b38e68a5b5429767f164ed496be08f9d4922':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'46908d515d5e813bc0e1cb5aa22fd1bb6b7f6b3a',path:'src/native/index.html',layout:'config,native'}),
    '78079b518620578a964eefb4646b4fd1ebd3f586c79f00cf6830c0809b804d55':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'46908d515d5e813bc0e1cb5aa22fd1bb6b7f6b3a',path:'index.html',
      parentSha256:'531bea691d326b27656a7e21c8a379deaf61e352d3f8468c6997ade2d7e2e09a',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
    // R002D (issue 94) timezone authority at ee2f9d12 on accepted main 5b846476: authored source e6cd59af and the
    // legacy-Moon structural control of its generated index 794bb701. Every entry below, including the main
    // b09f51ed authored source and 1a5c5031 structural control, remains admitted unchanged.
    'e6cd59af4d6a187c11003554d8c7b90250397fd430826f86e44d78f43b829536':Object.freeze({
      profile:'current-authored-native',kind:'current-authored-source',commit:'ee2f9d129d3d5debd12abeefaaca071fd01b6100',path:'src/native/index.html',layout:'config,native'}),
    '9e8f20a6bd19fe2894309cacb49277e05718b81a8463f5398a29b146ff42d30f':Object.freeze({
      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:'ee2f9d129d3d5debd12abeefaaca071fd01b6100',path:'index.html',
      parentSha256:'794bb701a34c69448954a6e835fa1f20ceab1338ac733de9a65984c2bd3992f1',
      transform:'Remove both complete Moon initial/refinement tags once; append the exact legacy file flag and moon-host tag before </body>; all other bytes unchanged.',
      layout:'config,first-paint,native,sky,moon-file,moon-host'}),
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
