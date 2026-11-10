#!/usr/bin/env python3
"""CP3: deterministic, authenticated constellation regions, patterns and record ontology.
No network, random source, invented magnitude, or proximity-only merge. Python stdlib only.
"""
from __future__ import annotations
import csv,io,json,math,hashlib,unicodedata
from collections import defaultdict,Counter
from pathlib import Path
from build_authenticated_catalogue import ROOT,source_bytes,authenticate,make_catalogue,dump
PINS={'constellation_data_roman87.dat':'41c3102c2a1572949d8ab8a2406b2081ff60e5ce','constellation_names.dat':'f76c60842f6f4f32ca8bd2d99e033c8549f18e51','stellarium-western-lines.fab':'7adddc5c8488ebc66640b9d3fbac30fa9ee7b6a2','ASTROPY_LICENSE.rst':'5945355a71905c7f88387398591d1df67162e7a3','stellarium-western-info.ini':'34f90991a0beccc5060176c5a7c8cf0af3b21ad9'}
B1875_JD=2415020.31352-25*365.242198781

def checked(root:Path,name:str)->str:
 b=(root/'upstream'/name).read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 if h!=PINS[name]:raise ValueError('Original upstream blob mismatch: '+name)
 return b.decode('utf-8')

def read_patterns(text:str):
 out=[]
 for n,line in enumerate(text.splitlines(),1):
  q=line.split()
  if not q:continue
  k=int(q[1]);ids=list(map(int,q[2:]))
  if k<1 or len(ids)!=k*2 or any(x<=0 for x in ids):raise ValueError('Malformed constellation edges line '+str(n))
  out.append({'id':q[0],'regionAbbr':q[0],'kind':'constellation-pattern','paths':[ids[i:i+2] for i in range(0,len(ids),2)],'source':'Stellarium-western-v0.22.2','sourceLine':n,'physicalEmission':False})
 if len(out)!=88 or len({x['id'] for x in out})!=88:raise ValueError('Expected 88 unique constellation patterns')
 return out

def parse_table(text):
 a=[]
 for line in text.splitlines():
  if not line.strip() or line.startswith('#'):continue
  x,y,d,n=line.split();a.append([float(x),float(y),float(d),n])
 if len(a)!=357 or len({r[3] for r in a})!=88:raise ValueError('Invalid Roman table')
 if any(a[i][2]<a[i+1][2] for i in range(len(a)-1)):raise ValueError('Roman table must descend by declination')
 return a

def classify(ra_deg,dec_deg,table):
 if not math.isfinite(ra_deg) or not math.isfinite(dec_deg) or not -90<=dec_deg<=90:raise ValueError('Invalid direction')
 h=(ra_deg%360)/15
 for lo,hi,de,co in table:
  if lo<=h<hi and dec_deg>=de:return co
 raise ValueError('Uncovered celestial direction')

def vector(ra,dec):
 a=math.radians(ra);d=math.radians(dec);return [math.cos(d)*math.cos(a),math.cos(d)*math.sin(a),math.sin(d)]

def radec(v):
 return math.degrees(math.atan2(v[1],v[0]))%360,math.degrees(math.atan2(v[2],math.hypot(v[0],v[1])))

def precess(v,jd):
 t=(jd-2451545)/36525;k=math.pi/180/3600
 ze=(2306.2181*t+.30188*t*t+.017998*t*t*t)*k
 z=(2306.2181*t+1.09468*t*t+.018203*t*t*t)*k
 th=(2004.3109*t-.42665*t*t-.041833*t*t*t)*k
 def rz(w,a):return [w[0]*math.cos(a)-w[1]*math.sin(a),w[0]*math.sin(a)+w[1]*math.cos(a),w[2]]
 w=rz(v,ze);w=[w[0]*math.cos(th)-w[2]*math.sin(th),w[1],w[0]*math.sin(th)+w[2]*math.cos(th)]
 return rz(w,z)

def build_regions(table,names):
 ras=sorted({v for r in table for v in r[:2]});des=sorted({-90.,90.,*(r[2] for r in table)})
 grid=[[classify((ra+rb)*7.5,(da+db)/2,table) for ra,rb in zip(ras,ras[1:])] for da,db in zip(des,des[1:])]
 nx=len(ras)-1;ny=len(des)-1;edges=[]
 # Merge only contiguous edges separating the SAME two regions. RA=0/24 is one meridian.
 for j in range(1,ny):
  i=0
  while i<nx:
   pair=(grid[j-1][i],grid[j][i]);end=i+1
   while end<nx and (grid[j-1][end],grid[j][end])==pair:end+=1
   if pair[0]!=pair[1]:edges.append({'a':[ras[i]*15,des[j]],'b':[ras[end]*15,des[j]],'regions':list(pair),'curve':'constant-declination'})
   i=end
 for i in range(nx):
  j=0
  while j<ny:
   pair=(grid[j][(i-1)%nx],grid[j][i]);end=j+1
   while end<ny and (grid[end][(i-1)%nx],grid[end][i])==pair:end+=1
   if pair[0]!=pair[1]:edges.append({'a':[ras[i]*15,des[j]],'b':[ras[i]*15,des[end]],'regions':list(pair),'curve':'meridian'})
   j=end
 region_data={n:{'abbr':n,'name':names[n],'areaSteradians':0.,'labelAnchorB1875':None,'labelArea':0.} for n in sorted(names)}
 for j,(da,db) in enumerate(zip(des,des[1:])):
  for i,(ra,rb) in enumerate(zip(ras,ras[1:])):
   area=math.radians((rb-ra)*15)*(math.sin(math.radians(db))-math.sin(math.radians(da)))
   r=region_data[grid[j][i]];r['areaSteradians']+=area
   if area>r['labelArea']:r['labelArea']=area;r['labelAnchorB1875']=[(ra+rb)*7.5,(da+db)/2]
 for r in region_data.values():r.pop('labelArea');r['areaSquareDegrees']=r['areaSteradians']*(180/math.pi)**2
 return {'schema':'salah-real-sky/constellations/1','source':'Nancy G. Roman 1987 (CDS VI/42), Astropy table transport','sourceBlobSha1':PINS['constellation_data_roman87.dat'],'boundaryFrame':'B1875-mean-equatorial','boundaryEquinoxJD':B1875_JD,'algorithm':'First eligible row; lower RA inclusive, upper RA exclusive, lower declination inclusive; RA wraps; poles use same rule','precisionNote':'Roman table printed to 0.0001h and 0.0001deg; NOT a replacement for higher precision original Delporte line work. J2000/B1875 conversion is IAU1976, not an FK4 E-term conversion. Close-boundary cases merit a precision audit.','nameCorrections':{'Cha':['Chamaleon','Chamaeleon'],'Oph':['Ophiucus','Ophiuchus'],'PsA':['Pisces Austrinus','Piscis Austrinus']},'table':table,'regions':list(region_data.values()),'edges':edges,'gridVerification':{'raIntervals':nx,'decIntervals':ny,'cellCount':nx*ny,'classifiedCells':sum(len(r) for r in grid),'coveredSteradians':sum(r['areaSteradians'] for r in region_data.values())}}

def resolve_systems(stars):
 by={s['hygId']:s for s in stars};members=defaultdict(set)
 for s in stars:
  p=s['multiplicity']['primaryHygId']
  if p and p!=s['hygId'] and p in by:members[p].update([p,s['hygId']])
 groups=[]
 for root,ids in sorted(members.items()):
  a=[by[i] for i in sorted(ids)];hip=[s for s in a if s['hip'] is not None]
  # Explicitly distinct HIP component rows; or component-only Gliese/HR rows with no combined HIP entry.
  components=len(hip)==len(a) or not hip
  if components:
   emit=[s['id'] for s in a];mode='component-entries';evidence='Distinct supplied component rows; no simultaneous combined row in this explicit HYG group. Source values retained, no orbital or high-resolution photometry claim.'
  else:
   # Conservative and exposed, not a claim that the retained V is a certified system total.
   representative=min(hip,key=lambda s:s['vmag']);emit=[representative['id']];mode='ambiguous-representative'
   evidence='HYG links Gliese component rows to a HIP-containing group, but does not certify whether HIP V is component or combined. Retain one HIP photometric representative; withhold additive ambiguous records. May undercount true component light; no invented deblending.'
  if root in [24549,36744,83755,61748]:evidence+=' Bright-system overlap reviewed explicitly (Capella/Castor/Sabik/Porrima); never add the companion on top of the retained bright-system entry.'
  gid='system:hyg:'+str(root)
  group={'id':gid,'primaryRecordId':f'hyg:{root}','memberIds':[s['id'] for s in a],'emitterIds':emit,'mode':mode,'evidence':evidence,'source':'HYG4.0 comp/comp_primary/base fields; compilation coverage is incomplete','combinedMagnitude':None,'orbitModel':None}
  groups.append(group)
  for s in a:s['emission']={'enabled':s['id'] in emit,'groupId':gid,'role':'component-entry' if components else ('photometric-representative' if s['id'] in emit else 'withheld-overlap'),'scopeVerified':components,'reason':mode}
 for s in stars:
  if 'emission' not in s:s['emission']={'enabled':True,'groupId':None,'role':'catalogue-photometric-source','scopeVerified':False,'reason':'No explicit overlap group; NOT a claim of physical singleness'}
 return {'schema':'salah-real-sky/systems/1','groups':groups,'policy':'No angular-proximity-only deduplication. Ambiguous combined/component photometry is withheld rather than added. Catalogue inventory and rendered emission are distinct.','unresolvedGroupCount':sum(g['mode']=='ambiguous-representative' for g in groups),'limitations':['Not a complete census of physical multiplicity.','No guessed component fluxes, binary orbits, variable-star phases or photometric corrections.','Some retained representatives may be component-only: conservative withholding can be too faint. Raw measurements remain available for later source adjudication.']}

def aliases(stars,root):
 out=defaultdict(set);entries=[]
 def add(name,id,kind,source):
  if not name:return
  key=' '.join(unicodedata.normalize('NFC',name).lower().split());out[key].add(id);entries.append({'alias':name,'recordId':id,'kind':kind,'source':source})
 for s in stars:
  for name,kind in [(s['properName'],'historical-common-name'),(s['bayerFlamsteed'],'catalogue-designation'),(s['gliese'],'catalogue-designation'),(s['id'],'stable-record-id')]:add(name,s['id'],kind,'HYG4.0')
  if s['hip']:add('HIP '+str(s['hip']),s['id'],'catalogue-designation','HYG4.0')
 # Name updates are separately labelled; never assert the full numerical source is HYG4.1.
 ids={s['hygId'] for s in stars}
 p=root/'upstream/hyg-v41-recovered-name-rows.csv'
 if p.exists():
  for r in csv.DictReader(p.open()):
   hid=int(r.get('id') or 0)
   if hid in ids:add(r.get('proper'),f'hyg:{hid}','unofficial-component-alias','Separately recovered HYG4.1 name row; NOT full4.1 authentication')
 return {'schema':'salah-real-sky/aliases/1','normalisation':'Unicode NFC, lower case, whitespace collapsed; aliases are NOT identities','entries':entries,'index':{k:sorted(v) for k,v in sorted(out.items())},'ambiguousAliases':{k:sorted(v) for k,v in sorted(out.items()) if len(v)>1}}

def build(root=ROOT):
 for n in PINS:checked(root,n)
 table=parse_table(checked(root,'constellation_data_roman87.dat'))
 names=dict(l.split(' ',1) for l in checked(root,'constellation_names.dat').splitlines() if l and not l.startswith('#'));names={k:v.strip() for k,v in names.items()};names.update(Cha='Chamaeleon',Oph='Ophiuchus',PsA='Piscis Austrinus')
 regions=build_regions(table,names);patterns=read_patterns(checked(root,'stellarium-western-lines.fab'))
 required={hip for p in patterns for line in p['paths'] for hip in line}
 raw=source_bytes(root/'upstream/hygdata_v40.csv.gz');authenticate(raw);rows=list(csv.DictReader(io.StringIO(raw.decode())))
 master=make_catalogue(rows,6.5,required);systems=resolve_systems(master['stars']);by={s['hygId']:s for s in master['stars']}
 mismatches=[]
 for s in master['stars']:
  ra,de=radec(precess(vector(s['raDeg'],s['decDeg']),B1875_JD));co=classify(ra,de,table)
  s['constellationMembership']={'abbr':co,'directionEpochJyear':2000,'method':'J2000 mean direction -> IAU1976 precession -> B1875 Roman87 lookup','sourceToken':s['sourceValues']['con']}
  if co!=s['constellationAbbr']:mismatches.append({'recordId':s['id'],'sourceToken':s['sourceValues']['con'],'computed':co,'raB1875Deg':ra,'decB1875Deg':de})
 master['ontologyRevision']=3;master['id']+='-CP3';master['selection']['countMeaning']='Retained catalogue records, including one faint line endpoint; emission.enabled is the separate light-contribution permission'
 for limit in [4,5,6,6.5]:
  c=make_catalogue(rows,limit,required)
  for s in c['stars']:s.update(emission=by[s['hygId']]['emission'],constellationMembership=by[s['hygId']]['constellationMembership'])
  c['ontologyRevision']=3;c['id']+='-CP3';dump(root/'data'/('catalogue-v'+str(limit).replace('.','_')+'.json'),c)
 dump(root/'data/catalogue-v6_5.json',master)
 keys=['spectralType','hr','id','hygId','hip','raDeg','decDeg','epochJyear','vmag','bv','pmRaCosDecMasYr','pmDecMasYr','distancePc','radialVelocityKmS','emission','constellationMembership','isRequiredEndpoint']
 compact={k:v for k,v in master.items() if k!='stars'};compact['stars']=[{k:s[k] for k in keys} for s in master['stars']];dump(root/'data/bright-stars.json',compact)
 for p in patterns:p['label']=names[p['id']]
 old=json.loads((root/'tests/fixtures/checkpoint1-annotations.json').read_text())
 extra=[dict(p,kind='asterism',physicalEmission=False) for p in old['patterns'] if p['id'] in ['SummerTriangle','WinterTriangle']]
 extra += [{'id':'BigDipper','label':'Big Dipper','kind':'asterism','regionAbbr':'UMa','source':'Subset of authenticated Stellarium Ursa Major strokes','paths':[[67301,65378,62956,59774,54061,53910,58001,59774]],'physicalEmission':False},{'id':'LittleDipper','label':'Little Dipper','kind':'asterism','regionAbbr':'UMi','source':'Authenticated Stellarium Ursa Minor pattern, alternate asterism label','paths':next(p['paths'] for p in patterns if p['id']=='UMi'),'physicalEmission':False}]
 annotations={'schema':'salah-real-sky/annotations/2','licence':'CC-BY-SA-4.0; see THIRD_PARTY_NOTICES.md','enabledByDefault':False,'status':'Cultural chart patterns; NOT physical connections or the definition of constellation regions','patterns':patterns+extra}
 dump(root/'data/annotations.json',annotations);dump(root/'data/constellations.json',regions);dump(root/'data/star-systems.json',systems);dump(root/'data/star-aliases.json',aliases(master['stars'],root))
 report={'status':'PASS','sourcePins':PINS,'catalogueRecords':len(master['stars']),'magnitudeLimitedRecords':sum(s['vmag']<=6.5 for s in master['stars']),'faintRequiredEndpoints':[{'hip':s['hip'],'vmag':s['vmag'],'id':s['id']} for s in master['stars'] if s['vmag']>6.5], 'constellationRegions':len(regions['regions']),'constellationPatterns':len(patterns),'asterisms':len(extra),'uniquePatternEndpoints':len(required),'unresolvedEndpoints':[],'boundaryEdges':len(regions['edges']),'gridVerification':regions['gridVerification'],'photometricGroups':len(systems['groups']),'unresolvedPhotometricGroups':systems['unresolvedGroupCount'],'withheldOverlapRecords':sum(not s['emission']['enabled'] for s in master['stars']),'emittingRecords':sum(s['emission']['enabled'] for s in master['stars']),'sourceMembershipDisagreements':mismatches,'nameCorrections':regions['nameCorrections'],'approximationBoundary':systems['limitations']}
 dump(root/'checkpoints/cp3/ontology-build.json',report,True)
 print(json.dumps({k:v for k,v in report.items() if k not in ['sourcePins','sourceMembershipDisagreements','approximationBoundary','nameCorrections']}))
 return report
if __name__=='__main__':build()
