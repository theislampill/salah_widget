#!/usr/bin/env python3
"""Import an owner-authenticated full HYG4.1 CSV, preserving magnitude/colour/motion.
No network, third-party dependency or silent fallback. Acquisition is a separate operation.
This route uses HIP identities only to avoid unresolved HYG component/source duplication.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path

def number(value,field,nullable=False):
    if value is None or str(value).strip()=='':
        if nullable:return None
        raise ValueError(f'Missing {field}')
    v=float(value)
    if not math.isfinite(v):raise ValueError(f'Non-finite {field}')
    return v

def normalise_rows(rows,limit,required):
    result=[];seen=set()
    for row in rows:
        if row.get('id')=='0' or row.get('proper')=='Sol':continue
        rawhip=row.get('hip','').strip()
        if not rawhip:continue
        hip=int(rawhip)
        if hip<=0:raise ValueError('Invalid HIP identity')
        m=number(row.get('mag'),'mag')
        if m>limit and hip not in required:continue
        if hip in seen:raise ValueError(f'Duplicate HIP {hip}')
        seen.add(hip)
        ra=number(row.get('ra'),'ra');dec=number(row.get('dec'),'dec')
        if not 0<=ra<24 or not -90<=dec<=90:raise ValueError(f'Out-of-range position HIP{hip}')
        bv=number(row.get('ci'),'ci',True);dist=number(row.get('dist'),'dist',True)
        if dist is not None and (dist>=100000 or dist<=0):dist=None
        pmra=number(row.get('pmra'),'pmra',True);pmdec=number(row.get('pmdec'),'pmdec',True)
        rv=number(row.get('rv'),'rv',True)
        # HYG's zero RV can mean unknown; do not claim an observed zero from an ambiguous field.
        if rv==0:rv=None
        flags=['HYG-mean-photometry-not-live','pmra-convention-owner-confirmed-muAlphaStar']
        if pmra is None or pmdec is None:flags.append('proper-motion-unavailable')
        if bv is None:flags.append('colour-unavailable')
        result.append({'hip':hip,'hygId':row.get('id'),'raDeg':ra*15,'decDeg':dec,'vmag':m,'bv':bv,'epochJyear':2000,
          'pmRaCosDecMasYr':pmra,'pmDecMasYr':pmdec,'distancePc':dist,'radialVelocityKmS':rv,
          'spectralType':row.get('spect') or None,'variableDesignation':row.get('var') or None,
          'constellationAbbr':row.get('con') or None,'catalogueLabel':row.get('proper') or row.get('bf') or None,'flags':flags})
    missing=required-{s['hip'] for s in result}
    if missing:raise ValueError(f'Required annotation identities absent: {sorted(missing)}')
    return sorted(result,key=lambda s:(s['vmag'],s['hip']))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--sha256',required=True,help='Independently authenticated source SHA256; do not invent or omit')
    p.add_argument('--confirm-pmra-cosdec',action='store_true',required=True,help='Confirm source proper-motion convention from the source catalogue/build lineage')
    p.add_argument('--limit',type=float,default=6.5);p.add_argument('--annotations',type=Path)
    args=p.parse_args();raw=args.csv.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!=args.sha256.lower():raise SystemExit('Source SHA256 mismatch; output not written')
    required=set()
    if args.annotations:
        ann=json.loads(args.annotations.read_text());required={i for pat in ann['patterns'] for path in pat['paths'] for i in path}
    with args.csv.open(encoding='utf-8-sig',newline='') as f:stars=normalise_rows(csv.DictReader(f),args.limit,required)
    if not stars:raise SystemExit('No usable stars; output not written')
    output={'schema':'salah-real-sky/catalogue/1','id':f'HYG4.1-{digest[:16]}-V{args.limit}','licence':'CC-BY-SA-4.0',
     'attribution':'David Nash / Astronexus; normalisation and selection in Salah Real Sky','sourceSha256':digest,
     'frame':'mean equatorial J2000; epoch 2000','selection':f'HIP-only V<={args.limit}; all specified annotation endpoints retained',
     'properMotionConvention':'mu_alpha_star = dRA/dt * cos(dec), mas/year; explicitly confirmed by importing owner','stars':stars}
    args.output.parent.mkdir(parents=True,exist_ok=True);tmp=args.output.with_suffix(args.output.suffix+'.tmp');tmp.write_text(json.dumps(output,separators=(',',':'),ensure_ascii=False)+'\n');tmp.replace(args.output)
    print(f'Imported {len(stars)} real HIP sources; source SHA256 {digest}')
if __name__=='__main__':main()
