const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../../src/native/index.html'),'utf8');
const code=source.slice(source.indexOf('function fitCn('),source.indexOf('// PROCEDURAL BRANCHING LIGHTNING'));

function fixture(){
 const state={d:'path-A',shape:0,font:0,width:140,matrix:{a:1,b:0,c:0,d:1,e:8,f:8},points:0,matrices:0,lengths:0,throwAt:null};
 const cn={style:{},textContent:'Isha'},nt={};
 const svg={createSVGPoint:()=>({matrixTransform(m){return {x:this.x*m.a+this.y*m.c+m.e,y:this.x*m.b+this.y*m.d+m.f};}})};
 const newRail=()=>({getAttribute:n=>n==='d'?state.d:null,ownerSVGElement:svg,
  getTotalLength(){state.lengths++;return 200;},getScreenCTM(){state.matrices++;return state.matrix;},
  getPointAtLength(l){state.points++;if(l===state.throwAt)throw Error('interrupted sampling');return {x:20+l*1.4,y:200-(100+state.shape)*Math.sin(l*Math.PI/200)};}});
 const elements={'.cn':cn,'.nt':nt,'.arc .rail':newRail(),'.arc .horizon':{getBoundingClientRect:()=>({top:200})},'.bar':{getBoundingClientRect:()=>({top:260})}};
 const scope={_cnFit:'',cnFontSignature:()=>String(state.font),Math,isFinite,parseFloat,$:s=>elements[s],getComputedStyle:e=>e.style,
  document:{querySelector:s=>elements[s],createRange:()=>({selectNodeContents(e){this.e=e;},getBoundingClientRect(){return this.e===cn?{left:160-state.width/2,right:160+state.width/2,width:state.width,bottom:190}:{top:200,bottom:250};}}),
   createElement:()=>({getContext:()=>({measureText:()=>({actualBoundingBoxAscent:21,fontBoundingBoxDescent:7.2})})})}};
 vm.createContext(scope);vm.runInContext(code,scope);
 return {state,scope,replaceRail(){elements['.arc .rail']=newRail();},fit(){
  state.font++;cn.style={fontSize:'30px',top:'100px',marginBottom:'0px',fontFamily:'serif'};
  scope.fitCn({currentKey:'Isha',sunrise:400,sunset:1100});return {...cn.style};
 }};
}
function freshFit(state){
 const f=fixture();Object.assign(f.state,{d:state.d,shape:state.shape,width:state.width,matrix:{...state.matrix}});return f.fit();
}

test('font refits reuse one exact path sampling while fitting fresh typography',()=>{
 const f=fixture();
 for(const width of [140,220,350]){f.state.width=width;assert.deepEqual(f.fit(),freshFit(f.state));}
 assert.equal(f.state.points,201,'three font fits must not resample the unchanged SVG path 603 times');
 assert.equal(f.state.lengths,1);assert.equal(f.state.matrices,3,'screen transform remains fresh on every fit');
});

test('identical replacement paths reuse only local points and apply the current transform',()=>{
 const f=fixture();f.fit();f.replaceRail();f.state.matrix={a:.9,b:.1,c:.05,d:1.1,e:13,f:-5};
 assert.deepEqual(f.fit(),freshFit(f.state));assert.equal(f.state.points,201);assert.equal(f.state.matrices,2);
});

test('changed paths replace the sole sample set and absent paths never reuse it',()=>{
 const f=fixture();let expected=0;
 for(const [d,shape] of [['path-A',0],['path-B',35],['path-A',0],['',12],['',27],[null,40],[null,5],['  ',2],['  ',34]]){
  f.state.d=d;f.state.shape=shape;assert.deepEqual(f.fit(),freshFit(f.state));expected+=201;
  assert.equal(f.state.points,expected,'changed/absent geometry must be sampled before fitting');
 }
});

test('interrupted sampling never publishes a partial path entry',()=>{
 const f=fixture();f.fit();f.state.d='path-B';f.state.shape=30;f.state.throwAt=50;
 assert.throws(()=>f.fit(),/interrupted sampling/);assert.equal(f.state.points,252);
 f.state.throwAt=null;assert.deepEqual(f.fit(),freshFit(f.state));assert.equal(f.state.points,453);
 assert.deepEqual(f.fit(),freshFit(f.state));assert.equal(f.state.points,453);
 assert.deepEqual(Object.keys(f.scope.fitCn._arcSamples).sort(),['d','points']);
 assert.equal(f.scope.fitCn._arcSamples.points.length,201);
 assert.ok(f.scope.fitCn._arcSamples.points.every(p=>Object.keys(p).sort().join(',')==='x,y'&&Number.isFinite(p.x)&&Number.isFinite(p.y)));
});
