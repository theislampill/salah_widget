import hashlib,json,pathlib
OUT=pathlib.Path(__file__).parent;ROOT=pathlib.Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
fixes={
 23:{'17-11':'Primary Astra independently reconciled the exact source/contract/evidence and this open conclusion. The specific final actual required-consumer matrix remains unverified above; eight individually accounted native legacy failures and four TODOs are not automatic blockers.'},
 24:{'18-08':'Delivered source/public baseline and current geometry are independently verified; primary Astra reconciled the actual default opacity/intended-color gap. Issue-specific frozen-noon and native intended-color contrast proof is still required before readability closure.'},
 37:{'25-10':'Bounded retained state and one animation loop are supported by source controls. The original same-quiescent cloud-painter before/after measurement is missing; broad full-pipeline performance is not this gate. N001 PARTIAL is scoped rather than a blanket blocker.'}}
summarypath=OUT/'summary.json';summary=json.loads(summarypath.read_text(encoding='utf-8'))
for n in [23,24,26,29,33,34,37]:
 p=OUT/f'{n}-assessment.json';a=json.loads(p.read_text(encoding='utf-8'));cp=OUT/f'{n}-comment.md';text=cp.read_text(encoding='utf-8')
 for ident,new in fixes.get(n,{}).items():
  r=next(r for r in a['requirementMatrix'] if r['id']==ident);old=r['observed'];assert old in text;text=text.replace(old,new);r['observed']=new
 assert 'unreconciled' not in text and 'No fresh product tests' not in text
 assert text.count('<!-- RLGWO-AUDIT:18ff14860ff41c084b1db5f396bb62aa9c22b1be:')==1
 assert a['publication']['reconciledByPrimary'] and not a['publication']['approved'] and not a['publication']['posted']
 for r in a['requirementMatrix']:
  for ref in r['authoredOwners']+r['deliveredConsumers']:
   assert (ROOT/ref['path']).is_file()
   if ref['lines']:assert 1<=ref['lines'][0]<=ref['lines'][1]<=len((ROOT/ref['path']).read_text(encoding='utf-8').splitlines())
 assert 'AUDIT_EVIDENCE_COMMIT' in text
 cp.write_text(text,encoding='utf-8');a['publication']['preparedCommentSha256']=hashlib.sha256(text.encode()).hexdigest();summary['preparedCommentSha256'][str(n)]=a['publication']['preparedCommentSha256'];p.write_text(json.dumps(a,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
summarypath.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'parseAndRefs':'PASS','mandatoryRows':sum(json.loads((OUT/f'{n}-assessment.json').read_text())['requirementMatrix'].__len__() for n in [23,24,26,29,33,34,37]),'primaryReconciled':True,'approved':False,'posted':False,'preparedHashes':summary['preparedCommentSha256']}))
