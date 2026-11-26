// Explicit file adapter for the byte-exact independently reviewed pure helper.
// No renderer algorithm or admission predicate is reimplemented here.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const here=path.dirname(fileURLToPath(import.meta.url));
const helper=path.resolve(here,'../../r0035/psf_within_call.mjs');
const helperSha='e6bf846750820bb9f69fa8c04c20ad91ad0a7fac666252739d22e3c02fd113fe';
const renderer='real-sky/core/src/renderer.mjs',stellar='tools/r0035/stellar_replay.mjs';
const candidate='tools/r0035/psf_within_call_renderer.mjs';
const need=(condition,message)=>{if(!condition)throw new Error(message);};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
function ancestry(file){
  for(let current=path.resolve(file);;current=path.dirname(current)){
    need(!fs.lstatSync(current).isSymbolicLink(),'regular PSF ancestry required');
    if(path.dirname(current)===current)break;
  }
}
function read(file){
  ancestry(file);
  const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{need(fs.fstatSync(fd).isFile(),'regular PSF file required');return fs.readFileSync(fd);}
  finally{fs.closeSync(fd);}
}
function row(bytes){return {bytes:bytes.length,sha256:sha(bytes)};}
const [mode,baseArg,outArg,...extra]=process.argv.slice(2);
need(['derive','check'].includes(mode)&&baseArg&&outArg&&!extra.length,'exact PSF file-entry arguments required');
const base=path.resolve(baseArg),out=path.resolve(outArg);
ancestry(base);ancestry(out);
need(fs.statSync(base).isDirectory()&&fs.statSync(out).isDirectory(),'separate existing PSF roots required');
need(base===fs.realpathSync(base)&&out===fs.realpathSync(out)&&base!==out
  &&!out.startsWith(base+path.sep)&&!base.startsWith(out+path.sep),'separate nonaliased PSF roots required');
need(sha(read(helper))===helperSha,'reviewed PSF helper source drift');
const pure=await import(pathToFileURL(helper).href);
const reference=read(path.join(base,renderer)),originalStellar=read(path.join(base,stellar));
need(read(path.join(out,renderer)).equals(reference),'candidate original renderer must remain intact');
if(mode==='derive'){
  need(read(path.join(out,stellar)).equals(originalStellar),'candidate stellar replay must start as the exact original');
  const derived=pure.deriveRenderer(reference),redirected=pure.deriveStellarReplay(originalStellar);
  pure.experimentIdentity(reference,derived,originalStellar,redirected);
  fs.writeFileSync(path.join(out,candidate),derived,{flag:'wx',mode:0o600});
  const fd=fs.openSync(path.join(out,stellar),fs.constants.O_WRONLY|fs.constants.O_NOFOLLOW);
  try{need(fs.fstatSync(fd).isFile(),'regular candidate stellar replay required');fs.ftruncateSync(fd,0);fs.writeFileSync(fd,redirected);fs.fsyncSync(fd);}
  finally{fs.closeSync(fd);}
}
const derived=read(path.join(out,candidate)),redirected=read(path.join(out,stellar));
const identity=pure.experimentIdentity(reference,derived,originalStellar,redirected);
need(pure.restoreRenderer(derived).equals(reference)&&pure.restoreStellarReplay(redirected).equals(originalStellar),
  'actual retained candidate must invert to complete original bytes');
need(read(path.join(base,renderer)).equals(reference)&&read(path.join(base,stellar)).equals(originalStellar)
  &&read(path.join(out,renderer)).equals(reference),'original source changed during PSF file admission');
process.stdout.write(JSON.stringify({protocol:'r0035-psf-file-transform/1',helperSha256:helperSha,identity,
  files:{[renderer]:row(reference),[stellar]:row(redirected),[candidate]:row(derived)}})+'\n');
