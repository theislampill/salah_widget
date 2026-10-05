#!/usr/bin/env python3
"""Rebuild the complete selected catalogue from authenticated HYG 4.0 bytes.
Stdlib only; no network or stochastic data. HYG records are not assumed to be single stars.
A later checkpoint resolves photometric overlap separately from catalogue admission.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, io, json, math
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE_SHA256='80152c797783b53449458b675eee65656f1404225481e766f8dab21c00ad3c69'
SOURCE_GIT_BLOB='c119fd384ed53d95f8c62d32e9dcdee5f7248dbb'
CONSTELLATIONS=set('And Ant Aps Aqr Aql Ara Ari Aur Boo Cae Cam Cnc CVn CMa CMi Cap Car Cas Cen Cep Cet Cha Cir Col Com CrA CrB Crv Crt Cru Cyg Del Dor Dra Equ Eri For Gem Gru Her Hor Hya Hyi Ind Lac Leo LMi Lep Lib Lup Lyn Lyr Men Mic Mon Mus Nor Oct Oph Ori Pav Peg Per Phe Pic Psc PsA Pup Pyx Ret Sge Sgr Sco Scl Sct Ser Sex Tau Tel Tri TrA Tuc UMa UMi Vel Vir Vol Vul'.split())
def dump(path:Path,obj,pretty=False):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False,indent=2 if pretty else None,separators=None if pretty else (',',':'))+'\n',encoding='utf-8')
def source_bytes(path:Path)->bytes:
 raw=path.read_bytes()
 return gzip.decompress(raw) if raw[:2]==b'\x1f\x8b' else raw

def authenticate(raw:bytes)->dict:
 sha=hashlib.sha256(raw).hexdigest();git=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if sha!=SOURCE_SHA256 or git!=SOURCE_GIT_BLOB:raise ValueError('Primary catalogue digest mismatch; do not write output')
 return {'sha256':sha,'gitBlobSha1':git,'bytes':len(raw)}
def num(row,key,nullable=True):
 s=row.get(key,'')
 if s is None or str(s).strip()=='':
  if nullable:return None
  raise ValueError('Missing '+key)
 v=float(s)
 if not math.isfinite(v):raise ValueError('Non-finite '+key)
 return v

def ident(row,key,nullable=True):
 v=num(row,key,nullable)
 if v is None:return None
 if int(v)!=v or v<0:raise ValueError('Invalid identifier '+key)
 return int(v)

def normalise(row:dict,limit:float,required_hips:set|None=None,line:int|None=None)->dict|None:
 required_hips=required_hips or set()
 hid=ident(row,'id',False)
 if hid==0:return None
 hip=ident(row,'hip');mag=num(row,'mag',False)
 if hip==0:raise ValueError('HIP zero is not a stellar identifier')
 if mag>limit and hip not in required_hips:return None
 ra=num(row,'ra',False);dec=num(row,'dec',False)
 if not 0<=ra<24 or not -90<=dec<=90 or not -2<=mag<=25:raise ValueError('Invalid coordinates/magnitude HYG '+str(hid))
 bv=num(row,'ci');dist=num(row,'dist');rv=num(row,'rv');pmra=num(row,'pmra');pmdec=num(row,'pmdec')
 if bv is not None and not -.5<=bv<=5:raise ValueError('Invalid B-V')
 flags=['catalogue-entry-not-single-star-claim','photometry-reference-not-live']
 # Source's explicitly documented RA hours/Dec degrees are canonical. Redundant radians are AUDITED.
 raw_ra_rad=num(row,'rarad');raw_de_rad=num(row,'decrad');residual=None
 if raw_ra_rad is not None and raw_de_rad is not None:
  residual=max(abs((math.degrees(raw_ra_rad)-ra*15+180)%360-180),abs(math.degrees(raw_de_rad)-dec))*3600
  if residual>3600:raise ValueError('Grossly inconsistent duplicate coordinate fields')
  if residual>.03:flags.append('redundant-radian-coordinate-disagreement-use-documented-hours-degrees')
 if bv is None:flags.append('colour-unavailable')
 if dist is None or not 0<dist<100000:flags.append('distance-unavailable-or-sentinel')
 if rv==0:flags.append('radial-velocity-zero-ambiguous')
 if pmra is None or pmdec is None:flags.append('proper-motion-unavailable')
 con=row.get('con') or None
 if con not in CONSTELLATIONS:flags.append('source-constellation-invalid-or-missing')
 lo=num(row,'var_min');hi=num(row,'var_max');known_range=lo is not None and hi is not None
 return {'id':f'hyg:{hid}','hygId':hid,'hip':hip,'hd':ident(row,'hd'),'hr':ident(row,'hr'),
  'raDeg':ra*15,'decDeg':dec,'epochJyear':2000,'vmag':mag,'bv':bv,
  'pmRaCosDecMasYr':pmra,'pmDecMasYr':pmdec,'distancePc':dist if dist is not None and 0<dist<100000 else None,
  'radialVelocityKmS':rv if rv!=0 else None,'spectralType':row.get('spect') or None,
  'constellationAbbr':con if con in CONSTELLATIONS else None,'catalogueLabel':row.get('proper') or row.get('bf') or None,
  'properName':row.get('proper') or None,'bayerFlamsteed':row.get('bf') or None,'bayer':row.get('bayer') or None,
  'flamsteed':row.get('flam') or None,'gliese':row.get('gl') or None,
  'variability':{'designation':row.get('var') or None,'brightMagnitude':min(lo,hi) if known_range else None,
   'faintMagnitude':max(lo,hi) if known_range else None,'reference':'HYG Hipparcos-Hp-derived V-adjusted historical range; NOT a current envelope',
   'lightCurve':None},
  'multiplicity':{'scope':'unknown-until-adjudicated','componentNumber':ident(row,'comp'),
   'primaryHygId':ident(row,'comp_primary'),'base':row.get('base') or None,'sourceCoverage':'Gliese subset only; absence does not imply single'},
  'sourceValues':{'raHours':ra,'decDeg':dec,'rarad':raw_ra_rad,'decrad':raw_de_rad,'rv':rv,'dist':dist,'con':con,
   'var_min':lo,'var_max':hi,'redundantCoordinateResidualArcsec':residual},
  'provenance':{'source':'HYG-4.0-authenticated','rowNumberIncludingHeader':line},
  'isRequiredEndpoint':mag>limit,'flags':flags}

def make_catalogue(rows,limit,required_hips=None):
 out=[];seen=set();hips=set()
 for line,row in enumerate(rows,2):
  s=normalise(row,limit,required_hips,line)
  if s is None:continue
  if s['id'] in seen or (s['hip'] is not None and s['hip'] in hips):raise ValueError('Duplicate admitted identity')
  seen.add(s['id']);hips.add(s['hip']);out.append(s)
 missing=set(required_hips or ())-{s['hip'] for s in out}
 if missing:raise ValueError('Required HIP endpoints absent '+repr(sorted(missing)))
 return {'schema':'salah-real-sky/catalogue/2','id':f'HYG4.0-{SOURCE_SHA256[:16]}-V{limit:g}',
  'licence':'CC-BY-SA-4.0','attribution':'David Nash / Astronexus; Salah Real Sky selection and normalisation',
  'sourceSha256':SOURCE_SHA256,'sourceGitBlobSha1':SOURCE_GIT_BLOB,
  'frame':'HYG mean-equatorial J2000 reference directions; mixed source-catalogue lineage, not uniform Gaia astrometry',
  'positionFieldPolicy':'Documented ra(hours) and dec(degrees); redundant radian fields retained and audited, not silently preferred',
  'epochJyear':2000,'properMotionConvention':'mu_alpha_star = dRA/dt*cos(dec), mas/Julian year',
  'selection':{'visualMagnitudeLimit':limit,'requiredHipEndpoints':sorted(required_hips or ()),'countMeaning':'catalogue records; multiplicity/photometry adjudication separate'},
  'stars':sorted(out,key=lambda s:(s['vmag'],s['hygId']))}

def build(root:Path=ROOT,source:Path|None=None,required_hips:set|None=None):
 source=source or root/'upstream/hygdata_v40.csv.gz'
 raw=source_bytes(source);auth=authenticate(raw);rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
 if len(rows)!=119626:raise ValueError('Unexpected primary record count')
 cats={}
 for limit in [4,5,6,6.5]:
  c=make_catalogue(rows,limit,required_hips)
  name='catalogue-v'+str(limit).replace('.','_')+'.json';dump(root/'data'/name,c);cats[str(limit)]=c
 master=cats['6.5']
 # Runtime projection input omits archival redundancy; full records stay in the master/tier assets.
 runtime_keys=['id','hygId','hip','raDeg','decDeg','epochJyear','vmag','bv','pmRaCosDecMasYr','pmDecMasYr','distancePc','radialVelocityKmS']
 runtime={k:v for k,v in master.items() if k!='stars'}
 runtime['stars']=[{k:s[k] for k in runtime_keys} for s in master['stars']]
 dump(root/'data/bright-stars.json',runtime)
 names={str(s['hip']):s['properName'] for s in master['stars'] if s['hip'] and s['properName']}
 dump(root/'data/common-names.json',{'source':'HYG4.0; historical catalogue names, not a current IAU-name certification','names':names})
 a=master['stars'];issues=[{'id':s['id'],'flags':s['flags'],'sourceValues':s['sourceValues']} for s in a if any(f.startswith(('redundant-','source-constellation')) for f in s['flags'])]
 fields=['hip','hd','hr','bv','spectralType','pmRaCosDecMasYr','pmDecMasYr','distancePc','radialVelocityKmS']
 report={'status':'PASS','primaryAuthentication':auth,'inputRecords':len(rows),'sunRecordsExcluded':1,
  'magnitudeSelection':{k:len(c['stars']) for k,c in cats.items()},'masterCount':len(a),'withHip':sum(s['hip'] is not None for s in a),
  'withoutHip':sum(s['hip'] is None for s in a),'coverage':{k:sum(s[k] is not None for s in a) for k in fields},
  'namedVariables':sum(s['variability']['designation'] is not None for s in a),
  'historicalVariableRanges':sum(s['variability']['brightMagnitude'] is not None for s in a),
  'flags':dict(sorted(Counter(f for s in a for f in s['flags']).items())),
  'exclusions':{'sun':1,'notSelectedByMagnitudeOrEndpoint':len(rows)-1-len(a)},
  'knownSourceIssues':issues,'v41':'Whole original v4.1 bytes NOT authenticated; 11 published name rows retained separately, never relabel v4.0 as v4.1'}
 # Validate the mu_alpha* interpretation against the source's rounded independent Cartesian velocities.
 residuals=[]
 byid={int(r['id']):r for r in rows}
 for s in a:
  if not s['distancePc']:continue
  r=byid[s['hygId']];ra=math.radians(s['raDeg']);de=math.radians(s['decDeg']);v=[float(r[k]) for k in ['vx','vy','vz']]
  ea=(-math.sin(ra),math.cos(ra),0);ed=(-math.cos(ra)*math.sin(de),-math.sin(ra)*math.sin(de),math.cos(de))
  scale=180/math.pi*3600000/s['distancePc']
  e=max(abs(sum(x*y for x,y in zip(v,ea))*scale-s['pmRaCosDecMasYr']),abs(sum(x*y for x,y in zip(v,ed))*scale-s['pmDecMasYr']))
  residuals.append((e,s['id']))
 residuals.sort()
 report['motionConventionCrossCheck']={'cases':len(residuals),'medianMaxAxisResidualMasYr':residuals[len(residuals)//2][0],
  'p99MaxAxisResidualMasYr':residuals[int(.99*len(residuals))][0],'worst':residuals[-10:],
  'interpretation':'Rounded/source-derived Cartesian velocities support the tangent convention but are NOT uniformly consistent independent measurements. Runtime uses supplied pmra/pmdec, not vx/vy/vz.'}
 dump(root/'checkpoints/cp2/catalogue-build.json',report,True)
 print(json.dumps({k:report[k] for k in ['status','masterCount','magnitudeSelection','coverage']}))
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--source',type=Path);p.add_argument('--required-hips',type=Path)
 args=p.parse_args();required=set(json.loads(args.required_hips.read_text())) if args.required_hips else set()
 build(args.root,args.source,required)
