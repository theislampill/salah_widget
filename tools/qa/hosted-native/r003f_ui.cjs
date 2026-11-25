'use strict';

// Both functions are self-contained so their exact source can be evaluated in
// the page. They observe DOM/layout/style only; they do not call a product API.
function readNativeUi(){
  const observed={coordinateSpace:'card-border-box-css-px'};
  try{
    const cards=[...document.querySelectorAll('.c')];observed.cardCount=cards.length;
    const card=cards[0];if(!card)return observed;
    const base=card.getBoundingClientRect();
    const style=el=>{
      const s=getComputedStyle(el);
      return Object.fromEntries(['display','visibility','opacity','position','zIndex','fontSize','lineHeight','color',
        'backgroundColor','overflow','transform','contentVisibility','backdropFilter','webkitBackdropFilter','filter','clipPath','boxSizing']
        .map(key=>[key,s[key]??'']));
    };
    const record=el=>{
      const r=el.getBoundingClientRect(),ancestors=[];
      for(let parent=el.parentElement;parent;parent=parent.parentElement)ancestors.push(style(parent));
      return {text:(el.textContent??'').trim(),rect:{left:r.left-base.left,top:r.top-base.top,right:r.right-base.left,
        bottom:r.bottom-base.top,width:r.width,height:r.height},style:style(el),ancestors};
    };
    const all=selector=>[...card.querySelectorAll(selector)].map(record);
    observed.card=record(card);
    observed.header=all('.h');observed.location=all('.h .e');observed.buckle=all('.h .buckle');observed.weather=all('.h .wt');
    observed.times=all('.times');
    observed.rows=[...card.querySelectorAll('.times .p')].map(el=>({...record(el),key:el.getAttribute('data-prayer-key'),
      labels:[...el.querySelectorAll('b')].map(record),times:[...el.querySelectorAll('.tm')].map(record)}));
    observed.footer=all('.d');observed.gregorian=all('.d .ce');observed.hijri=all('.d .ah');
    observed.refinedCanvas=all('.real-sky-canvas');observed.previewCanvas=all('.real-sky-preview');
  }catch(error){observed.observationError=String(error?.message??error);}
  return observed;
}

function admitNativeUi(observed){
  const failures=[],fail=(condition,reason)=>{if(!condition)failures.push(reason);};
  const o=observed&&typeof observed==='object'?observed:{};
  const list=value=>Array.isArray(value)?value:[];
  const keys=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'];
  const validRect=r=>r&&['left','top','right','bottom','width','height'].every(k=>Number.isFinite(r[k]))&&
    r.width>0&&r.height>0&&r.right>r.left&&r.bottom>r.top;
  const contained=(r,parent)=>validRect(r)&&validRect(parent)&&r.left>=parent.left&&r.top>=parent.top&&r.right<=parent.right&&r.bottom<=parent.bottom;
  const visible=s=>s&&s.display&&s.display!=='none'&&s.visibility==='visible'&&s.contentVisibility!=='hidden'&&
    s.opacity!==''&&Number.isFinite(Number(s.opacity))&&Number(s.opacity)>0;
  const check=(node,name,{display,text=false,parent}={})=>{
    fail(!!node,name+': missing');if(!node)return;
    fail(contained(node.rect,o.card?.rect),name+': rectangle outside card or empty');
    if(parent)fail(contained(node.rect,parent.rect),name+': rectangle outside containing UI');
    fail(visible(node.style)&&Array.isArray(node.ancestors)&&node.ancestors.every(visible),name+': hidden or missing style');
    if(display)fail(node.style?.display===display,name+': expected '+display+' layout');
    if(text){
      fail(typeof node.text==='string'&&node.text.trim().length>0,name+': empty text');
      fail(Number.parseFloat(node.style?.fontSize)>0,name+': zero or missing font size');
      const color=node.style?.color;
      fail(typeof color==='string'&&color!==''&&color!=='transparent'&&!/^rgba\([^)]*,\s*0(?:\.0*)?\s*\)$/.test(color),name+': transparent or missing text color');
    }
  };
  const single=(field,options)=>{
    const rows=list(o[field]);fail(rows.length===1,field+': expected one node');check(rows[0],field,options);return rows[0];
  };
  fail(o.coordinateSpace==='card-border-box-css-px','missing coordinate contract');
  fail(!o.observationError,'observation read failed: '+(o.observationError??''));
  fail(o.cardCount===1,'expected one card');
  fail(validRect(o.card?.rect)&&o.card.rect.left===0&&o.card.rect.top===0&&o.card.rect.width===325&&o.card.rect.height===530&&
    o.card.rect.right===325&&o.card.rect.bottom===530,'expected 325x530 card rectangle');
  check(o.card,'card');
  const header=single('header',{display:'grid'});
  single('location',{text:true,parent:header});single('buckle',{parent:header});single('weather',{text:true,parent:header});
  const times=single('times',{display:'grid'}),rows=list(o.rows);
  fail(rows.length===6,'expected six prayer rows');
  fail(new Set(rows.map(r=>r?.key)).size===6,'expected six distinct prayer identities');
  rows.forEach((row,i)=>{
    const name='prayer '+(row?.key??i);check(row,name,{display:'flex',parent:times});
    fail(row?.key===keys[i],name+': wrong identity or order');
    const labels=list(row?.labels),values=list(row?.times);
    fail(labels.length===1&&values.length===1,name+': expected one label and time');
    check(labels[0],name+' label',{text:true,parent:row});check(values[0],name+' time',{text:true,parent:row});
    fail(labels[0]?.text===row?.key,name+': label does not match identity');
    fail(typeof values[0]?.text==='string'&&/^(?:[01]?\d|2[0-3]):[0-5]\d(?:\s*[ap]m)?$/i.test(values[0].text),name+': unpopulated or invalid displayed time');
    if(i)fail(validRect(rows[i-1]?.rect)&&validRect(row?.rect)&&row.rect.top>=rows[i-1].rect.bottom,name+': rows overlap or are out of order');
  });
  const footer=single('footer',{display:'flex'});
  single('gregorian',{text:true,parent:footer});single('hijri',{text:true,parent:footer});
  if(validRect(header?.rect)&&validRect(times?.rect))fail(times.rect.top>=header.rect.bottom,'prayer rows precede or overlap header');
  if(validRect(times?.rect)&&validRect(footer?.rect))fail(footer.rect.top>=times.rect.bottom,'footer precedes or overlaps prayer rows');
  // A hidden preview is normal after refined composition. Positioning still
  // has to come from the real stylesheet, so either canvas cannot enter flow.
  for(const field of ['refinedCanvas','previewCanvas']){
    const canvases=list(o[field]);fail(canvases.length===1,field+': expected one native canvas');
    fail(canvases[0]?.style?.position==='absolute',field+': stylesheet positioning missing');
  }
  return {protocol:'R003F/native-ui/1',status:failures.length?'INCOMPLETE':'PASS',failures,observed:o};
}

function assertNativeUi(receipt){
  const checked=admitNativeUi(receipt?.observed);
  if(receipt?.protocol!=='R003F/native-ui/1'||receipt?.status!=='PASS'||!Array.isArray(receipt?.failures)||receipt.failures.length||checked.status!=='PASS'){
    const error=new Error('R003F native UI admission incomplete: '+(checked.failures.join('; ')||'invalid receipt'));
    error.code='R003F_UI_INCOMPLETE';error.nativeUi=checked;throw error;
  }
  return checked;
}
module.exports={readNativeUi,admitNativeUi,assertNativeUi};
