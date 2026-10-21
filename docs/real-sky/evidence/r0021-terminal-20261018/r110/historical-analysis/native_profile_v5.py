"""Native UserTiming endpoint decoding. Never subtract an inferred overhead or impute missing calls."""
from pathlib import Path
import collections,hashlib,json,math,re,statistics,sys

def stats(v):
 s=sorted(v)
 return {'count':len(s),'min':s[0],'median':statistics.median(s),'p95':s[math.ceil(.95*len(s))-1],'max':s[-1],'zeroCount':s.count(0)}if s else None

def read_marks(profile,engine):
 rows=[]
 if engine=='chromium':
  threads={(e['pid'],e['tid']):e['args']['name']for e in profile['traceEvents']if e.get('ph')=='M'and e.get('name')=='thread_name'}
  for e in profile['traceEvents']:
   if e.get('cat')=='blink.user_timing'and e['name'].startswith('r21:'):
    assert e['ph']=='I','Unexpected UserTiming phase'
    rows.append({'name':e['name'],'at':e['ts']/1000,'pid':e['pid'],'tid':e['tid'],'documentId':e.get('args',{}).get('data',{}).get('navigationId'),'threadName':threads.get((e['pid'],e['tid']))})
 else:
  def visit(p):
   for t in p['threads']:
    sch=t['markers']['schema']
    for e in t['markers']['data']:
     if len(e)<=sch['data']:
      assert t['stringTable'][e[sch['name']]]!='UserTiming'and not t['stringTable'][e[sch['name']]].startswith('r21:'),'Truncated possibly-owned native endpoint'
      continue
     d=e[sch['data']]
     if isinstance(d,dict)and d.get('type')=='UserTiming'and str(d.get('name','')).startswith('r21:'):
      assert d['entryType']=='mark','Unexpected UserTiming entry type'
      rows.append({'name':d['name'],'at':e[sch['startTime']],'pid':t['pid'],'tid':t['tid'],'documentId':d.get('innerWindowID'),'threadName':t['name']})
   for c in p.get('processes',[]):visit(c)
  visit(profile)
 return rows

def validate_rows(rows,expected_document=None,expected_thread=None):
 assert rows,'Missing native markers'
 assert all(isinstance(x['at'],(int,float))and not isinstance(x['at'],bool)and math.isfinite(x['at'])and x['at']>=0 for x in rows),'Nonfinite/invalid native endpoint'
 assert all(re.fullmatch(r'r21:(?:S:(?:0|[1-9][0-9]*):.+|E:(?:0|[1-9][0-9]*)|M:(?:0|[1-9][0-9]*):.+|C:.+:(?:empty|nested):(?:0|[1-9][0-9]*):[SE])',x['name'])for x in rows),'Unknown/malformed native marker'
 if expected_document is not None:assert all(x['documentId']==expected_document for x in rows),'Foreign document native marker'
 if expected_thread is not None:assert all(x['threadName']==expected_thread for x in rows),'Foreign thread role'
 assert len({(x['pid'],x['tid'])for x in rows})==1,'Mixed content main threads'
 assert all(b['at']>=a['at']for a,b in zip(rows,rows[1:])),'Non-monotone original markers'
 assert len({x['name']for x in rows})==len(rows),'Duplicate native marker'

def select_export_prefix(rows,raw,document_readback,label,expected_thread):
 """Cut by an atomic page-side marker, never by an estimated time or token count."""
 anchor=document_readback['mark'];cut=raw['cut']
 assert anchor['name']=='r21:M:0:'+label and anchor['count']==0,'Document boundary source mismatch'
 assert isinstance(document_readback['url'],str)and document_readback['url'],'Missing page URL'
 assert math.isfinite(document_readback['timeOrigin'])and document_readback['timeOrigin']>0,'Invalid time origin'
 assert cut['name'].endswith(':export.cut')and cut['count']==len(raw['records']),'Export cut count mismatch'
 for value in [anchor,cut]:assert value['depth']==0 and value['invalid']is False,'Invalid document/export boundary'
 anchor_indices=[i for i,r in enumerate(rows)if r['name']==anchor['name']]
 cut_indices=[i for i,r in enumerate(rows)if r['name']==cut['name']]
 assert anchor_indices==[0]and len(cut_indices)==1 and cut_indices[0]>0,'Missing/duplicate/out-of-order document or export cut'
 end=cut_indices[0];prefix=rows[:end+1];suffix=rows[end+1:];source=prefix[0]
 assert isinstance(source['documentId'],(int,str))and not isinstance(source['documentId'],bool)and bool(source['documentId']),'Missing native document identity'
 validate_rows(prefix,source['documentId'],expected_thread)
 # Suffix can end in a half-call because the browser keeps running after export.
 # Preserve the original profile and report the excluded interval; no metadata join.
 assert all(isinstance(r['at'],(int,float))and not isinstance(r['at'],bool)and math.isfinite(r['at'])and r['at']>=prefix[-1]['at']for r in suffix),'Invalid post-cut native timestamp'
 document={k:source[k]for k in ['documentId','pid','tid','threadName']}
 document.update(url=document_readback['url'],boundary=anchor['name'],timeOrigin=document_readback['timeOrigin'])
 excluded={'excludedMarkers':len(suffix),'cutName':cut['name'],'cutAtMs':prefix[-1]['at'],'firstExcluded':suffix[0]if suffix else None,'lastExcluded':suffix[-1]if suffix else None,'reason':'After atomic export cut; retained in original profile, not joined to frozen JavaScript metadata.'}
 return prefix,document,excluded

def validate_boundaries(rows,declared):
 actual=[r['name']for r in rows if r['name'].startswith('r21:M:')]
 assert actual==[m['name']for m in declared],'Missing/foreign/out-of-order boundary'
 assert [int(n.split(':',3)[2])for n in actual]==list(range(len(actual))),'Boundary sequence incomplete'
 index={m['name']:m for m in declared};count=0
 for row in rows:
  if row['name'].startswith('r21:S:'):count+=1
  if row['name']in index:
   meta=index[row['name']]
   assert meta['count']==count and meta['depth']==0 and meta['invalid']is False,'Native/JavaScript boundary state/count mismatch'

def decode(rows,raw,expected_document=None,expected_thread=None):
 validate_rows(rows,expected_document,expected_thread)
 index={}
 for x in rows:
  assert x['name']not in index,'Duplicate native marker '+x['name'];index[x['name']]=x
 assert not raw['invalid']and raw['depth']==0 and not raw['errors'],'Invalid JavaScript recording'
 calls=[];stack=[];order=[]
 for x in rows:
  fields=x['name'].split(':');assert len(fields)>=3 and fields[0]=='r21'and fields[1]in['S','E','M','C'],'Unknown native marker namespace'
  if fields[1]=='S':
   token=int(fields[2]);assert token==len(order)and token<len(raw['records']),'Non-sequential/out-of-export record token';r=raw['records'][token]
   assert r['token']==token and r['scope']==':'.join(fields[3:])and r['parent']==(stack[-1]if stack else None)and r['depth']==len(stack),'Metadata/nesting mismatch'
   stack.append(token);order.append(token)
  elif fields[1]=='E':assert stack and stack.pop()==int(fields[2]),'Non-LIFO native interval'
 assert not stack and len(order)==len(raw['records']),'Missing or unclosed native intervals'
 for r in raw['records']:
  assert r['closed']and not r['exception'],'Unclosed/exception callback'
  a=index['r21:S:'+str(r['token'])+':'+r['scope']]['at'];b=index['r21:E:'+str(r['token'])]['at'];assert b>=a
  calls.append({**r,'startMs':a,'endMs':b,'inclusiveMs':b-a})
 children=collections.defaultdict(list)
 for c in calls:
  if c['parent']is not None:children[c['parent']].append(c)
 for c in calls:
  own=children[c['token']];assert len(own)==c['children']
  assert all(c['startMs']<=x['startMs']<=x['endMs']<=c['endMs']for x in own)
  exclusive=c['inclusiveMs']-sum(x['inclusiveMs']for x in own);assert exclusive>=-.00001
  c['exclusiveObservedMs']=exclusive;c['negativeExclusiveCorrectionMs']=max(0,-exclusive);c['exclusiveMs']=max(0,exclusive)
 return index,calls

