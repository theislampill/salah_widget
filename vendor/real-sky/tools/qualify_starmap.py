#!/usr/bin/env python3
"""Authenticate the supplied numerical source and document its limited-band contract.
No downloads, no artistic calibration, no claim that Gaia is a complete diffuse-light survey.
"""
from pathlib import Path
from functools import lru_cache
import gzip,hashlib,json,re,math
from decimal import Decimal
import numpy as np
from cp7_acquire_source import authenticate,EXPECTED_SHA256,EXPECTED_ROWS
ROOT=Path(__file__).resolve().parents[1]
SOURCE='upstream/cp7/starmap-o8-BVRI-total.txt.gz'
QUANTITY='# quantity: passband-averaged spectral radiance, W m^-2 sr^-1 nm^-1'

def header(path):
    out=[]
    with gzip.open(path,'rt',encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):out.append(line.rstrip())
            else:break
    return out

def zero_points(h):
    if [x for x in h if x.startswith('# quantity:')]!=[QUANTITY]:raise ValueError('Ambiguous/unsupported radiance units')
    z={}
    for band in 'BVRI':
        a=[x for x in h if x.startswith('# zero points '+band+':')]
        b=[x for x in h if x.startswith('# flux to radiance '+band+':')]
        if len(a)!=1 or len(b)!=1:raise ValueError('Missing/ambiguous passband calibration')
        m=re.fullmatch(r'# zero points '+band+r': Gaia DR3 G VEGAMAG ([0-9.]+); '+band+r' ([0-9.e+-]+) W m\^-2 nm\^-1',a[0])
        if not m:raise ValueError('Unrecognised passband zero-point header')
        graw,fraw=m.groups();g,f0=map(float,(graw,fraw));araw=b[0].split(':')[1].split()[0];factor=float(araw)
        # Each literal is rounded independently. Test overlap of its rounding
        # interval, not more precision than the publisher printed. No values change.
        half=lambda text: .5*float(Decimal(1).scaleb(Decimal(text).as_tuple().exponent))
        lo=(f0-half(fraw))*10**(-.4*(g+half(graw)))
        hi=(f0+half(fraw))*10**(-.4*(g-half(graw)))
        if not f0>0 or not math.isfinite(factor) or factor+half(araw)<lo or factor-half(araw)>hi:raise ValueError('Inconsistent passband conversion factor')
        z[band]=f0
    return z

@lru_cache(maxsize=2)
def load_source(root=ROOT):
    p=Path(root)/SOURCE;authenticate(p);h=header(p)
    for prefix,value in [('# bands:','# bands: B V R I'),('# grid:','# grid: HEALPix order 8, NESTED, ICRS')]:
        if [s for s in h if s.startswith(prefix)]!=[value]:raise ValueError('Ambiguous source columns/grid')
    zero_points(h)
    with gzip.open(p,'rt',encoding='utf-8') as f:a=np.loadtxt(f)
    if a.shape!=(EXPECTED_ROWS,5) or not np.array_equal(a[:,0],np.arange(EXPECTED_ROWS)):raise ValueError('Incomplete/nonsequential all-sky source')
    if not np.isfinite(a).all() or (a[:,1:]<0).any():raise ValueError('Invalid radiance')
    a=a[:,1:].copy();a.setflags(write=False)
    return a,h

def write_json(p,obj):
    Path(p).parent.mkdir(exist_ok=True,parents=True)
    Path(p).write_text(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def qualify(root=ROOT):
    root=Path(root);a,h=load_source(root);z=zero_points(h);omega=4*math.pi/len(a)
    report={'status':'PASS','stage':'7.1','scope':'actual source possession, format, provenance and fitness for a limited-band integrated-starlight component',
      'sourceSha256':EXPECTED_SHA256,'sourceBytes':(root/SOURCE).stat().st_size,'sourceRows':len(a),
      'frame':'ICRS','grid':'HEALPix NESTED','order':8,'nside':256,'pixelSolidAngleSr':omega,'pixelScaleDeg':math.degrees(math.sqrt(omega)),
      'quantity':'passband-averaged spectral radiance W m^-2 sr^-1 nm^-1','zeroPointsWm2nm':z,'headerPrecisionPolicy':'Printed zero-point and factor rounding intervals must intersect; published values are not rescaled.', 'zeroPointEquation':'L_band = F0_band * sum(10^(-0.4*m_band)) / Omega_pixel',
      'bands':{b:{'min':float(a[:,i].min()),'median':float(np.median(a[:,i])),'max':float(a[:,i].max()),'zeroCells':int((a[:,i]==0).sum()),'integratedWm2nm':float(a[:,i].sum()*omega)} for i,b in enumerate('BVRI')},
      'sourceHeader':h,'intendedReuse':'Retain source and attributions; derived exclusion mask keeps HYG CC-BY-SA notice; see SOURCE_QUALIFICATION.md and THIRD_PARTY_NOTICES.md',
      'sourceAuthentication':'Uploaded bytes match previously retrieved GitHub release asset digest, not merely a new local hash',
      'component':'catalogue-aggregated integrated starlight; not total natural night sky',
      'calibrationStatus':'source photometric zero-point scale; Gaia-to-BVRI empirical transformations and missing-colour recovery are modelled, not four directly measured spectra',
      'unavailableUncertainty':'No per-cell covariance, counts, colour-validity mask or completeness map is supplied. Global absolute accuracy is not certified.',
      'epochPolicy':'Frozen ICRS map; Gaia source_id bins and Hipparcos supplement have mixed position epochs. Do not precess axes from 2016 or propagate one star across the map.',
      'headerCaveat':'The header statement about Gaia seeing nothing brighter than G=5 is not used as a selection, completeness or subtraction rule.',
      'rawAdditiveCompositionAllowed':False,'rawOverlap':'contains CP6 point emitters; corrected assets required before addition',
      'missingComponents':['airglow','zodiacal light','terrestrial skyglow','lunar/solar atmospheric scatter','diffuse interstellar scattered/emission light not represented by catalogue sources','unresolved objects missing from Gaia'],
      'spatialCoverage':'All native indices are present; this is format coverage, not observational completeness.'}
    write_json(root/'provenance/cp7/admitted/source-qualification.json',report)
    return report
if __name__=='__main__':print(json.dumps(qualify(),indent=2))
