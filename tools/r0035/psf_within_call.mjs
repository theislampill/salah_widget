// Source-only R0035 experiment. This module performs no file, browser or network
// operation. It derives a separately named module; it never patches the core.
import {createHash} from 'node:crypto';

const rendererDigest='173283b65c4b89cd1c85067131183ad2a306199850f41ae070ede463de5add6b';
const stellarDigest='d58e92294f2f99b2d2405b153a228ec0a5484064f3efe09e0d26babb34acc4e7';
const prefix='// R0035 source-only within-call horizontal-integral derivative; no native qualification.\n';
const oldLoop=' for(let j=ys;j<=ye;j++){';
const newLoop=' const horizontal=[];\n'+oldLoop;
const oldWeight=' const wx=.5*(erf((i+1-x)*inv)-erf((i-x)*inv)),w=Math.max(0,wx*wy),k=(j*width+i)*3;';
// First-row evaluation remains interleaved with the original buffer writes.
// Only later rows reuse wx. Never hoist wy, flux products, channel/part work,
// or the per-pixel multiply/add; Number values retain binary64 precision.
const newWeight=' const wx=j===ys?(horizontal[i-xs]=.5*(erf((i+1-x)*inv)-erf((i-x)*inv))):horizontal[i-xs],w=Math.max(0,wx*wy),k=(j*width+i)*3;';
const dependencies=['astronomy.mjs','photometry.mjs','spectral.mjs','optics.mjs'];
const oldImport="import {renderStars} from '../../real-sky/core/src/renderer.mjs';";
const newImport="import {renderStars} from './psf_within_call_renderer.mjs';";

function bytes(value){if(!Buffer.isBuffer(value))throw new TypeError('Actual source Buffer bytes required');return value;}
function sha(value){return createHash('sha256').update(bytes(value)).digest('hex');}
function pinned(value,expected){if(sha(value)!==expected)throw new Error('Reference source digest identity mismatch');return value.toString('utf8');}
function once(source,oldText,newText){
  const index=source.indexOf(oldText);
  if(index<0||source.indexOf(oldText,index+oldText.length)>=0)throw new Error('Missing or ambiguous exact experiment seam');
  return source.slice(0,index)+newText+source.slice(index+oldText.length);
}
export function deriveRenderer(reference){
  let source=pinned(reference,rendererDigest);
  source=once(once(source,oldLoop,newLoop),oldWeight,newWeight);
  for(const name of dependencies)source=once(source,"from './"+name+"'","from '../../real-sky/core/src/"+name+"'");
  return Buffer.from(prefix+source);
}
export function restoreRenderer(candidate){
  let source=bytes(candidate).toString('utf8');
  if(!source.startsWith(prefix))throw new Error('Missing source-only derivative identity');
  source=source.slice(prefix.length);
  for(const name of dependencies)source=once(source,"from '../../real-sky/core/src/"+name+"'","from './"+name+"'");
  source=once(once(source,newWeight,oldWeight),newLoop,oldLoop);
  const reference=Buffer.from(source);pinned(reference,rendererDigest);return reference;
}
export function deriveStellarReplay(reference){
  return Buffer.from(once(pinned(reference,stellarDigest),oldImport,newImport));
}
export function restoreStellarReplay(candidate){
  const reference=Buffer.from(once(bytes(candidate).toString('utf8'),newImport,oldImport));
  pinned(reference,stellarDigest);return reference;
}
export function experimentIdentity(reference,candidate,stellar,redirected){
  if(!deriveRenderer(reference).equals(bytes(candidate))||!restoreRenderer(candidate).equals(reference)
      ||!deriveStellarReplay(stellar).equals(bytes(redirected))||!restoreStellarReplay(redirected).equals(stellar))
    throw new Error('Derivative bytes do not match the exact admitted source transformation');
  const identity=value=>({bytes:value.length,sha256:sha(value)});
  return {protocol:'r0035-within-call-psf/1',scope:'within-one-splat-horizontal-integrals',
    referenceRenderer:identity(reference),candidateRenderer:identity(candidate),
    originalStellarReplay:identity(stellar),redirectedStellarReplay:identity(redirected),
    nativeQualification:'NOT_RUN',humanAcceptance:'OUTSTANDING'};
}
