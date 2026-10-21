/* Observation tooling only. Native profile endpoints own elapsed time. */
'use strict';
function createNativeMarkRecorder(perf,capacity=120000){
 const mark=perf.mark.bind(perf),clear=perf.clearMarks.bind(perf),stack=[],records=[],errors=[];
 let invalid=false,boundary=0;
 const emit=name=>{mark(name);clear(name);};
 function enter(scope){
  if(records.length>=capacity){invalid=true;return -1;}
  const token=records.length,parent=stack.at(-1)??null;
  records.push({token,scope,parent,depth:stack.length,children:0,closed:false,exception:false});
  if(parent!==null)records[parent].children++;
  stack.push(token);emit('r21:S:'+token+':'+scope);return token;
 }
 function leave(token){
  if(token<0){invalid=true;return;}
  emit('r21:E:'+token);
  if(stack.pop()!==token||!records[token]||records[token].closed){invalid=true;return;}
  records[token].closed=true;
 }
 function caught(token,e){if(records[token])records[token].exception=true;errors.push({token,message:String(e?.message??e)});}
 function boundaryMark(label){const name='r21:M:'+boundary+++':'+label;emit(name);return {name,count:records.length,depth:stack.length,invalid};}
 function control(label,count=200){
  if(stack.length)throw new Error('Controls require idle stack');
  const before=boundaryMark(label+'.before');
  for(let i=0;i<count;i++){
   emit('r21:C:'+label+':empty:'+i+':S');leave(enter('probe.empty'));emit('r21:C:'+label+':empty:'+i+':E');
   emit('r21:C:'+label+':nested:'+i+':S');const p=enter('probe.parent');leave(enter('probe.child'));leave(p);emit('r21:C:'+label+':nested:'+i+':E');
  }
  return {before,after:boundaryMark(label+'.after'),count};
 }
 return {enter,leave,caught,mark:boundaryMark,control,export:()=>({records:records.map(x=>({...x})),errors:[...errors],invalid,depth:stack.length,capacity})};
}
if(typeof module!=='undefined')module.exports={createNativeMarkRecorder};
