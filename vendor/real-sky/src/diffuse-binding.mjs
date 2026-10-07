import {sha256Hex} from './sha256.mjs';
import {validateCatalogue} from './catalogue.mjs';
import {createRegisteredStarlightSampler} from './registered-starlight.mjs';
const dsBindings=new WeakSet();
function dsDeepFreeze(value){if(value&&typeof value==='object'&&!Object.isFrozen(value)){for(const v of Object.values(value))dsDeepFreeze(v);Object.freeze(value);}return value;}
/** Verify EXACT catalogue bytes named by the corrected source-removal asset, then
 * parse a private frozen catalogue. The physical bridge must use binding.catalogue.
 * Asset admission/photometric uncertainty remain CP7.3's. A hash is not a signature.
 */
export function bindRegisteredStarlight(catalogueText,asset){
 if(typeof catalogueText!=='string')throw new TypeError('Unmodified catalogue UTF-8 text required');
 const catalogueSha256=sha256Hex(new TextEncoder().encode(catalogueText));
 if(catalogueSha256!==asset?.catalogueSha256)throw new TypeError('Diffuse emitter catalogue byte hash mismatch');
 const catalogue=dsDeepFreeze(validateCatalogue(JSON.parse(catalogueText)));
 const sampler=createRegisteredStarlightSampler(asset,{catalogueSha256});
 const binding=Object.freeze({catalogue,catalogueSha256,sampler,sourceSha256:sampler.sourceSha256,kind:'verified-catalogue-bound-starlight'});dsBindings.add(binding);return binding;
}
export function isBoundRegisteredStarlight(value){return !!value&&dsBindings.has(value);}
