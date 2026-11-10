"""Narrow authored correction over the immutable CP9 scientific input.

The optimized camera predicate reconstructs basis vectors from normalized rays.
Roundoff can make an exact horizon sample negative, leaving zero grid radiance.
Resolve only near-zero decisions through the existing inverse projection; this
does not admit negative altitudes or shift the camera/horizon. Generated core
and bundles inherit this change through build_native.py, never hand edits.
"""
import hashlib

SOURCE_SHA256 = '837de88bdacd0aa1004cec5124cbf57549e66a6ed9f4ac29d48a14a8adf1776a'
BEFORE = 'above:(x,y)=>fw[2]+(x-cx)/f*right[2]+(cy-y)/f*up[2]>=0'
AFTER = '''above:(x,y)=>{
  // Reconstructed basis roundoff must not zero an exact-horizon grid row.
  // The uncertainty band selects the exact existing ray test, not an altitude tolerance.
  const z=fw[2]+(x-cx)/f*right[2]+(cy-y)/f*up[2];
  return Math.abs(z)>1e-12?z>0:unproject(x,y).altDeg>=0;
 }'''

def correct_horizon(source: bytes) -> bytes:
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError('CP9 horizon source drift: reconcile the authored correction')
    text=source.decode('utf-8')
    if text.count(BEFORE) != 1:
        raise ValueError('CP9 horizon predicate must occur exactly once')
    return text.replace(BEFORE,AFTER,1).encode('utf-8')
