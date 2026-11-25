import {installLab} from './live_lab.mjs';
const q=new URLSearchParams(location.hash.slice(1));
if(q.has('r35arm')){
  const keys=['r35arm','r35scope','r35amplitude','r35glass','r35margin'];
  if(keys.every(key=>q.get(key)?.trim())){
    window.R0035Lab=installLab({tile:q.has('r35tile')?Number(q.get('r35tile')):16,guard:q.get('r35guard')!=='off',arm:q.get('r35arm'),scope:q.get('r35scope'),multiplier:Number(q.get('r35amplitude')),
      glassFactor:Number(q.get('r35glass')),margin:Number(q.get('r35margin'))});
  }
}
