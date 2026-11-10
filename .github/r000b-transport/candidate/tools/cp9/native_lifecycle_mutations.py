#!/usr/bin/env python3
"""Isolated negative controls; never edits the candidate or scientific reference."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,tempfile,re
ROOT=Path(__file__).resolve().parents[2]
MUTANTS=[
 ('remove-frame-age','native-contract.mjs','Math.abs(current.utcMs-job.observer.utcMs)<=30000','true','native-lifecycle.test.mjs','an unchanged scene cannot admit a frame two minutes out of date'),
 ('remove-invalidation-epoch','native-lifecycle.mjs','job.native.lifecycleEpoch===this.epoch','true','native-lifecycle.test.mjs','explicit invalidation fences a pending completion even when identity is reused'),
 ('ignore-wall-discontinuity','native-lifecycle.mjs','*prior.rate)>1000','*prior.rate)>1e20','native-lifecycle.test.mjs','wall-clock backward discontinuity is caught even without a timer poll'),
 ('allow-hidden-work','native-lifecycle.mjs',"if(state.paused)return Promise.resolve({status:'paused'});","if(false)return Promise.resolve({status:'paused'});",'native-lifecycle.test.mjs','hidden state refuses forced work and obsolete completions'),
 ('reuse-asset-attempt','native-assets.mjs','this.load(controller.signal,generation)','this.load(controller.signal)','native-assets.test.mjs','retry supplies a distinct generation to the request factory so pending script requests cannot coalesce'),
 ('admit-obsolete-asset','native-assets.mjs','generation!==this.generation','false','native-assets.test.mjs','late A completion cannot replace B after retry')]
def run(root,out):
 out.mkdir(parents=True,exist_ok=True);results=[]
 with tempfile.TemporaryDirectory(prefix='cp83-negative-control-') as temp:
  t=Path(temp);(t/'tests/real-sky').mkdir(parents=True)
  for p in (root/'real-sky').rglob('*.mjs'):
   dest=t/'real-sky'/p.relative_to(root/'real-sky');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
  for n in ['native-lifecycle.test.mjs','native-assets.test.mjs']:shutil.copyfile(root/'tests/real-sky'/n,t/'tests/real-sky'/n)
  for name,file,old,new,suite,test in MUTANTS:
   path=t/'real-sky'/file;original=path.read_text(encoding='utf-8');assert old in original,name
   command=['node','--test','--test-reporter=tap','--test-name-pattern='+re.escape(test),'tests/real-sky/'+suite]
   clean=subprocess.run(command,cwd=t,capture_output=True,text=True,timeout=30);(out/(name+'-clean.tap')).write_text(clean.stdout+clean.stderr);assert clean.returncode==0,name+' clean control'
   path.write_text(original.replace(old,new));mutated=path.read_bytes()
   bad=subprocess.run(command,cwd=t,capture_output=True,text=True,timeout=30);text=bad.stdout+bad.stderr;(out/(name+'-mutant.tap')).write_text(text);path.write_text(original)
   caught=bad.returncode!=0 and re.search(r'^not ok \d+ - '+re.escape(test)+r'$',text,re.M) is not None
   results.append({'name':name,'test':test,'cleanExit':clean.returncode,'mutantExit':bad.returncode,'detectedAtNamedAssertion':caught,'source':file,'replace':old,'with':new,'mutantSha256':hashlib.sha256(mutated).hexdigest()})
   assert caught,name+' was not detected by the named production behaviour assertion'
 result={'status':'PASS','controls':results,'scope':'Six isolated native lifecycle/asset negative controls; passing clean control paired with each deliberately broken variant. Candidate untouched.'};(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('NATIVE MUTATIONS PASS',len(results));return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();run(x.root.resolve(),x.output)
