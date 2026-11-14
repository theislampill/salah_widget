'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
if(process.argv.length!==5)throw Error('Expected repository, fresh output and private dependency paths');
const repo=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
fs.mkdirSync(out,{recursive:false});
const started=process.hrtime.bigint();
let browser=null,result={scope:'Rendered documentation only',complete:false};
const modules=path.resolve(process.argv[4]);
const {chromium}=require(path.join(modules,'playwright'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const {marked}=await import(require.resolve(path.join(modules,'marked')));
 const readme=fs.readFileSync(path.join(repo,'README.md'));
 const builder=fs.readFileSync(path.join(repo,'src/native/builder.html'));
 const config=fs.readFileSync(path.join(repo,'src/native/config.js'));
 const bindings={};
 for(const [name,raw] of [['README.md',readme],['src/native/builder.html',builder],['src/native/config.js',config]])bindings[name]={bytes:raw.length,sha256:sha(raw)};
 if(bindings['README.md'].sha256!=='89a712f50d7283965facf732e7438fe755bf8e905d221b2f2f7dea2228eb8016')throw Error('README candidate identity differs');
 if(bindings['src/native/builder.html'].sha256!=='457aeff9f236923972f25bdee91cc1d42db8392ca81b6040d81d36b0dae34cd2')throw Error('Builder candidate identity differs');
 if(bindings['src/native/config.js'].sha256!=='685bb0f001502dc9f1afbf03b4eb173a8a5b4aaf35f4b85c16e1565a1335159f')throw Error('Config candidate identity differs');
 fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify(bindings,null,2)+'\n');
 const rendered='<!doctype html><html><head><meta charset="utf-8"><title>R0016 README review</title><style>body{margin:32px auto;max-width:980px;padding:0 24px;color:#1f2328;font:16px/1.55 Arial,sans-serif}h1,h2,h3,h4{line-height:1.25}pre{padding:16px;overflow:auto;background:#f6f8fa;border-radius:6px;font:13px/1.5 monospace}code{font:13px/1.5 monospace}table{border-collapse:collapse}td,th{padding:6px 12px;border:1px solid #d0d7de}a{color:#0969da}img{max-width:100%}</style></head><body>'+marked.parse(readme.toString('utf8'))+'</body></html>';
 fs.writeFileSync(path.join(out,'readme-rendered.html'),rendered);
 const tmp=path.join(out,'browser-temp');fs.mkdirSync(tmp,{recursive:true});process.env.TMPDIR=tmp;
 browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:1280,height:1000},locale:'en-US',timezoneId:'UTC',colorScheme:'dark'});
 context.setDefaultTimeout(15000);
 const requests=[],errors=[];
 await context.route('**/*',async route=>{
  const u=route.request().url();requests.push(u);
  if(u==='http://r0016.review.invalid/README.html')return route.fulfill({status:200,contentType:'text/html',body:rendered});
  if(u==='http://r0016.review.invalid/builder.html')return route.fulfill({status:200,contentType:'text/html',body:builder});
  if(u==='http://r0016.review.invalid/config.js')return route.fulfill({status:200,contentType:'application/javascript',body:config});
  return route.abort();
 });
 const page=await context.newPage();page.on('pageerror',error=>errors.push(String(error)));
 await page.goto('http://r0016.review.invalid/README.html',{waitUntil:'domcontentloaded'});
 const readmeText=await page.locator('body').innerText();fs.writeFileSync(path.join(out,'readme-visible-text.txt'),readmeText);
 await page.getByRole('heading',{name:'Review a pinned file first',exact:true}).scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(out,'readme-review-route.png')});
 await page.getByRole('heading',{name:'Offline local preview',exact:true}).scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(out,'readme-preview-policy.png')});
 const previewPolicy=await page.evaluate(()=>{
  const h=[...document.querySelectorAll('h4')].find(h=>h.textContent==='Offline local preview');let text='';for(let p=h?.nextElementSibling;p&&p.tagName!=='H4';p=p.nextElementSibling)text+=p.textContent+'\n';return text;
 });
 const readmeChecks={pinnedOccurrences:(readmeText.match(/a4c617ebeedfb507c0cb7a472683cce47ad62522/g)||[]).length,oldPinAbsent:!/(dc4c251d81ccb0796e70ff0516661204277232cb|81c698bea3bfa3e2a5abee2e92fe6bb0c82a80bb|f8d3db2d6d6d84f63bf8d79cf52c6977558cb105|d96f87825f02077da7f6afe742d30aecfd1fc005)/.test(readmeText),downloadSeparate:previewPolicy.includes('separate preparation step'),zeroFilesystem:previewPolicy.includes('installer itself creates, overwrites and deletes no files or directories'),hostLimits:previewPolicy.includes('not separately proven'),noNetwork:previewPolicy.includes('no network requests'),normalNoOpen:previewPolicy.includes('still asks for normal confirmations, downloads and'),builderMain:previewPolicy.includes('published main installer'),manual:previewPolicy.includes('import remain manual')};
 if(readmeChecks.pinnedOccurrences!==4||Object.entries(readmeChecks).some(([k,v])=>k!=='pinnedOccurrences'&&v!==true))throw Error('Rendered README checks failed: '+JSON.stringify(readmeChecks));
 await page.goto('http://r0016.review.invalid/builder.html',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>typeof window.SalahConfig==='object'&&typeof installCmd==='function');
 const facts=await page.evaluate(()=>({title:document.title,installLabel:document.getElementById('install').textContent,command:installCmd(),snippet:snippet(),hash:hash(),previewStyle:document.getElementById('pv').getAttribute('style'),body:document.body.innerText}));
 if(!facts.command.cmd.includes('/main/install.sh')||/DRY_RUN|NO_OPEN/.test(facts.command.cmd))throw Error('Normal builder command changed');
 await page.getByRole('button',{name:/Install widget/}).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'builder-install-context.png')});
 result={scope:'Local rendered actual authored builder and candidate README only; external requests blocked. No served-main parity or renderer/widget visual acceptance.',browser:browser.version(),inputs:{readme:{bytes:readme.length,sha256:sha(readme)},builder:{bytes:builder.length,sha256:sha(builder)},config:{bytes:config.length,sha256:sha(config)}},readmeChecks,previewPolicy,builder:facts,requests,pageErrors:errors};
 for(const [name,binding] of Object.entries(bindings)){const raw=fs.readFileSync(path.join(repo,name));if(raw.length!==binding.bytes||sha(raw)!==binding.sha256)throw Error('Source changed: '+name);}
 if(errors.length)throw Error('Unexpected page error');
 result.complete=true;
 await context.close();
 console.log(JSON.stringify({browser:result.browser,readmeChecks,requestCount:requests.length,pageErrors:errors,inputs:result.inputs}));
})().catch(error=>{result.complete=false;result.error=String(error.stack||error);fs.writeFileSync(path.join(out,'failure.txt'),result.error);console.error(error);process.exitCode=1;}).finally(async()=>{
 try{if(browser)await browser.close();result.browserClosed=true;}catch(error){result.complete=false;result.browserCloseError=String(error);process.exitCode=1;}
 result.elapsedMilliseconds=Number(process.hrtime.bigint()-started)/1e6;
 result.command=process.argv;result.node=process.version;result.platform=process.platform;
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
});
