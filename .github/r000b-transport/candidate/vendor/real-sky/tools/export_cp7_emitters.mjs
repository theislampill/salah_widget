/** Export the actual CP6 permissioned emission set at source-relevant position epochs. */
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {propagateJ2000,vectorRaDec} from '../src/astronomy.mjs';
const input=fs.readFileSync(new URL('../data/bright-stars.json',import.meta.url));
const catalogue=JSON.parse(input),epochs=[1991.25,2000,2015.5,2016];
if(catalogue.stars.some(s=>typeof s.emission?.enabled!=='boolean'))throw Error('Missing emission permission');
const stars=catalogue.stars.filter(s=>s.emission.enabled).map(s=>({id:s.id,hip:s.hip,vmag:s.vmag,motionAvailable:s.pmRaCosDecMasYr!==null&&s.pmDecMasYr!==null,directions:epochs.map(epoch=>({epoch,...vectorRaDec(propagateJ2000(s,epoch))}))}));
const report={schema:'salah-real-sky/emitter-exclusion/1',catalogueSha256:createHash('sha256').update(input).digest('hex'),catalogueId:catalogue.id,retainedRecords:catalogue.stars.length,emitterCount:stars.length,withheldCount:catalogue.stars.length-stars.length,epochs,policy:'Only emission.enabled sources; all magnitude tiers are subsets of this master. Mask native source cells before any filtering.',stars};
console.log(JSON.stringify(report));
