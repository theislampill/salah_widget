#!/usr/bin/env python3
"""CP7 PARTIAL: a finite, authenticated HYG residual diagnostic, NOT a diffuse survey.
Exact catalogue identity partition; spherical flux-conserving smoothing; area-weighted tiers.
NumPy is a build/test dependency only (verified with 2.3.5). No network or random sources.
"""
from __future__ import annotations
import csv,gzip,hashlib,io,json,math
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from inspect_diffuse_source import read_retained_catalogue,write_greyscale_png
from build_authenticated_catalogue import dump
ROOT=Path(__file__).resolve().parents[1]
DIAGNOSTIC_ROLE='finite-catalogue-diagnostic-not-survey'

class Groups:
    def __init__(self,ids):self.parent={i:i for i in ids}
    def find(self,i):
        p=self.parent[i]
        if p!=i:self.parent[i]=self.find(p)
        return self.parent[i]
    def join(self,a,b):
        a,b=self.find(a),self.find(b)
        if a!=b:self.parent[max(a,b)]=min(a,b)

def numeric_id(value):
    if value is None or str(value).strip()=='':return None
    n=int(value)
    return n if n>0 else None

def partition(rows, runtime):
    """No angular/proximity identity guess. Known aliases/component links are conservative."""
    by={int(r['id']):r for r in rows}
    if len(by)!=len(rows):raise ValueError('Duplicate HYG identity in partition')
    live={int(s['hygId']):s for s in runtime}
    if len(live)!=len(runtime) or not set(live).issubset(by):raise ValueError('Bad runtime identity set')
    for i,s in live.items():
        if not isinstance(s.get('emission',{}).get('enabled'),bool):raise ValueError('Runtime emission permission required')
        if abs(float(by[i]['mag'])-s['vmag'])>1e-10:raise ValueError('Runtime/source photometry drift')
    groups=Groups(by);aliases={};unresolved=set()
    for i,r in by.items():
        if i==0:continue
        for f in ['hip','hd','hr']:
            n=numeric_id(r.get(f))
            if n is None:continue
            k=f,n
            if k in aliases:groups.join(i,aliases[k])
            else:aliases[k]=i
        p=numeric_id(r.get('comp_primary'))
        if p and p!=i:
            if p in by:groups.join(i,p)
            else:unresolved.add(i)
        if int(r.get('comp') or 1)!=1:unresolved.add(i)
    members=defaultdict(list)
    for i in by:members[groups.find(i)].append(i)
    touches={groups.find(i) for i in live}
    entries=[]
    for i,r in sorted(by.items()):
        mag,ra,dec=float(r['mag']),float(r['ra'])*15,float(r['dec'])
        if not all(math.isfinite(v) for v in [mag,ra,dec]) or not(0<=ra<360 and -90<=dec<=90 and -30<=mag<=30):raise ValueError('Invalid source photometry/direction')
        root=groups.find(i)
        if i==0:category='sun-not-stellar-background'
        elif i in live:category='runtime-emitter' if live[i]['emission']['enabled'] else 'runtime-withheld'
        elif root in touches:category='linked-to-runtime-withheld'
        elif len(members[root])>1 or i in unresolved:category='ambiguous-source-group-withheld'
        else:category='residual-diagnostic'
        flux=0. if i==0 else 10**(-.4*mag)
        entries.append({'hygId':i,'hip':numeric_id(r.get('hip')),'hd':numeric_id(r.get('hd')),'hr':numeric_id(r.get('hr')),
            'group':root,'category':category,'raDeg':ra,'decDeg':dec,'vmag':mag,'relativeV0Flux':flux})
    return entries

def cell_areas(width,height):
    if not isinstance(width,int) or not isinstance(height,int) or width<4 or height<2:raise ValueError('Grid too small')
    edges=np.linspace(-np.pi/2,np.pi/2,height+1)
    return (2*np.pi/width)*np.diff(np.sin(edges))

def deposit(entries,width,height):
    """Conservative cloud-in-cell deposition, RA periodic, cap indices clamped.
    Intermediate grid represents integrated flux per cell, not surface brightness.
    """
    grid=np.zeros((height,width),dtype=np.float64)
    for e in entries:
        if e['category']!='residual-diagnostic':continue
        x=(e['raDeg']%360)/360*width-.5;y=(e['decDeg']+90)/180*height-.5
        ix=math.floor(x);iy=math.floor(y);fx=x-ix;fy=y-iy
        for dx,wx in [(0,1-fx),(1,fx)]:
            for dy,wy in [(0,1-fy),(1,fy)]:grid[min(height-1,max(0,iy+dy)),(ix+dx)%width]+=e['relativeV0Flux']*wx*wy
    return grid

def spherical_smooth(flux, sigma_deg=5., radius_sigmas=3.):
    """Symmetric, area-balanced, truncated spherical Gaussian *engineering* filter.
    Sinkhorn diagonal balancing makes both total flux and a constant radiance field
    invariant on this non-equal-area grid. No measured telescope PSF is asserted.
    """
    f=np.asarray(flux,dtype=np.float64)
    if f.ndim!=2 or not np.isfinite(f).all() or (f<0).any():raise ValueError('Invalid flux grid')
    if not math.isfinite(sigma_deg) or not .1<=sigma_deg<=30:raise ValueError('Invalid smoothing sigma')
    if not math.isfinite(radius_sigmas) or not 1<=radius_sigmas<=5:raise ValueError('Invalid filter extent')
    h,w=f.shape;omega=cell_areas(w,h);lat=-np.pi/2+(np.arange(h)+.5)*np.pi/h
    cosine=np.cos(np.arange(w)*2*np.pi/w);sig=math.radians(sigma_deg);limit=sig*radius_sigmas
    kernels={};matrix=np.zeros((h,h),dtype=np.float64)
    for j in range(h):
        for q in range(h):
            if abs(lat[j]-lat[q])>limit:continue
            cosg=np.sin(lat[j])*np.sin(lat[q])+np.cos(lat[j])*np.cos(lat[q])*cosine
            angle=np.arccos(np.clip(cosg,-1,1));kernel=np.where(angle<=limit,np.exp(-.5*(angle/sig)**2),0.)
            kernels[j,q]=kernel;matrix[j,q]=kernel.sum()*omega[q]
    scale=1/np.sqrt(matrix.sum(axis=1))
    residual=math.inf
    for iteration in range(500):
        sums=scale*(matrix@scale);residual=float(np.max(abs(sums-1)))
        if residual<1e-13:break
        scale=scale/np.sqrt(sums)
    else:raise ValueError('Spherical filter balancing failed')
    spectra=np.fft.rfft(f,axis=1);out=np.zeros_like(spectra)
    for (j,q),kernel in kernels.items():
        weights=kernel*scale[j]*scale[q]*omega[q]
        out[q]+=spectra[j]*np.fft.rfft(weights)
    result=np.fft.irfft(out,n=w,axis=1)
    negative=float(-result[result<0].sum());result=np.maximum(result,0.)
    total=float(f.sum());error=abs(float(result.sum())-total)/max(total,1e-300)
    if total and error>1e-11:raise ValueError('Smoothing loses flux')
    return result,{'sigmaDeg':sigma_deg,'truncationSigma':radius_sigmas,'method':'spherical Gaussian with symmetric solid-angle balancing','balancingIterations':iteration,'maxBalancingResidual':residual,'fftNegativeRoundoffClippedFlux':negative,'relativeFluxError':error,'measuredOpticalPSF':False}

def rebin_flux(flux,factor=2):
    f=np.asarray(flux,dtype=np.float64);h,w=f.shape
    if not isinstance(factor,int) or factor<1 or h%factor or w%factor:raise ValueError('Rebin factor must divide both dimensions')
    return f.reshape(h//factor,factor,w//factor,factor).sum(axis=(1,3))

def map_asset(flux,source_sha,partition_sha,filter_info):
    h,w=flux.shape;values=flux/cell_areas(w,h)[:,None]
    # Numeric roundoff is explicitly bounded in the report. No arbitrary artistic intensity scale.
    serial=[float(format(float(v),'.12g')) for v in values.ravel()]
    integrated=math.fsum(v*float(cell_areas(w,h)[i//w]) for i,v in enumerate(serial))
    return {'schema':'salah-real-sky/diffuse-map/1','id':f'HYG4.0-residual-diagnostic-{w}x{h}',
        'role':DIAGNOSTIC_ROLE,'productionAdmissible':False,'sourceSha256':source_sha,'partitionSha256':partition_sha,
        'licence':'CC-BY-SA-4.0','attribution':'David Nash / Astronexus HYG4.0; finite-source engineering derivative',
        'frame':'mean-equatorial-J2000','epochJyear':2000,
        'quantity':'relative-V0-flux-per-steradian','bands':['catalogue-V'],'colourStatus':'monochrome; no measured full spectrum',
        'grid':{'type':'equirectangular-cell-centred','width':w,'height':h,'lonOriginDeg':0,'latOriginDeg':-90,'lonStepDeg':360/w,'latStepDeg':180/h,'order':'south-to-north rows, RA increases right'},
        'supportKind':'defined-finite-catalogue-field-not-survey-coverage','observationalCoverage':None,
        'zeroMeaning':'No contribution from this finite admitted partition after stated processing; NOT measured darkness',
        'missingPhysicalComponents':['unlisted stars','diffuse Galactic scattering/emission','nebulae/galaxies','airglow','zodiacal light','extragalactic background'],
        'timeAssumption':'Frozen source distribution at catalogue J2000; frame transforms only, no proper motion/parallax for the map',
        'filter':filter_info,'totalRelativeV0Flux':integrated,'values':serial,'validMask':[1]*(w*h)}

def build(root=ROOT):
    rows,auth=read_retained_catalogue(root/'upstream/hygdata_v40.csv.gz')
    runtime=json.loads((root/'data/bright-stars.json').read_text())['stars']
    entries=partition(rows,runtime)
    rootout=root/'data/diffuse';rootout.mkdir(exist_ok=True,parents=True);evidence=root/'checkpoints/cp7_2';evidence.mkdir(exist_ok=True,parents=True)
    text=io.StringIO(newline='');writer=csv.DictWriter(text,fieldnames=list(entries[0]),lineterminator='\n');writer.writeheader();writer.writerows(entries)
    ledger=text.getvalue().encode();compressed=gzip.compress(ledger,compresslevel=9,mtime=0)
    (rootout/'finite-source-partition.csv.gz').write_bytes(compressed);partition_sha=hashlib.sha256(ledger).hexdigest()
    residual=[e for e in entries if e['category']=='residual-diagnostic'];raw=deposit(residual,256,128)
    smooth,filt=spherical_smooth(raw);total=math.fsum(e['relativeV0Flux'] for e in residual)
    assets=[]
    for factor in [1,2,4]:
        field=rebin_flux(smooth,factor);asset=map_asset(field,auth['sha256'],partition_sha,filt);name=f"hyg-residual-{asset['grid']['width']}x{asset['grid']['height']}.json";dump(rootout/name,asset)
        assets.append({'path':'data/diffuse/'+name,'sha256':hashlib.sha256((rootout/name).read_bytes()).hexdigest(),'width':asset['grid']['width'],'height':asset['grid']['height'],'totalRelativeV0Flux':asset['totalRelativeV0Flux'],'serialisationRelativeFluxError':abs(asset['totalRelativeV0Flux']-total)/total})
    category_counts=Counter(e['category'] for e in entries)
    budget={c:math.fsum(e['relativeV0Flux'] for e in entries if e['category']==c) for c in sorted(category_counts)}
    pointids={s['hygId'] for s in runtime if s['emission']['enabled']};residualids={e['hygId'] for e in residual}
    if pointids&residualids:raise ValueError('Point-source light duplicated in residual')
    if category_counts['sun-not-stellar-background']!=1 or len(entries)!=sum(category_counts.values()):raise ValueError('Incomplete source partition')
    # Area-balanced smoothing must preserve a constant surface-brightness field too.
    flat=cell_areas(64,32)[:,None]*np.ones((32,64));constant,constant_info=spherical_smooth(flat)
    constant_error=float(np.max(abs(constant/flat-1)))
    if constant_error>1e-10:raise ValueError('Smoothing invents structure in constant radiance')
    report={'stage':'7.2','stageStatus':'PARTIAL_DIAGNOSTIC_ONLY','checkpoint7Status':'OPEN','productionDiffuseSourceAdmitted':False,
        'inputKind':'Previously retained authenticated HYG4.0; no new optical survey',
        'inputNonSolarRecords':len(rows)-1,'partitionCounts':dict(sorted(category_counts.items())),
        'fluxBudgetRelativeV0':budget,'totalListedNonSolarFlux':math.fsum(e['relativeV0Flux'] for e in entries),
        'residualSourceCount':len(residual),'runtimeEmittingIdIntersection':sorted(pointids&residualids),'allRuntimeRowsExcluded':not bool({s['hygId'] for s in runtime}&residualids),
        'duplicatePolicy':'Known HIP/HD/HR aliases and explicit component links unioned. All source-only multi-record groups conservatively withheld; groups touching any runtime row also withheld. No proximity-only merge. Unrecorded astrophysical multiplicity remains unknown.',
        'partitionCsvUncompressedSha256':partition_sha,'sourceSha256':auth['sha256'],
        'depositionRelativeFluxError':abs(float(raw.sum())-total)/total,'filter':filt,
        'constantRadianceControlMaxRelativeError':constant_error,'assets':assets,
        'surveyCompleteness':'UNKNOWN; numerical grid definition does not establish observed diffuse coverage',
        'naturalNightAccounting':'Not composed with CP6. Adding this diagnostic to its lumped night floor is not authorised; survey-dependent decomposition remains CP7.4.',
        'dependencies':{'builderPython':'3.10+','numpyTested':np.__version__,'runtime':'No NumPy or external JS dependencies'},
        'acceptance':{'finiteIdentityPartition':'PASS','knownCatalogueOverlap':'PASS for retained identities/links only','fluxConservation':'PASS','sphericalConstantControl':'PASS','actualDiffuseSurvey':'BLOCKED','totalDiffuseRadiometricCalibration':'NOT_ESTABLISHED'}}
    dump(evidence/'build-report.json',report,True)
    # Preview, with a documented nonphysical logarithmic stretch, north up.
    density=smooth/cell_areas(256,128)[:,None];write_greyscale_png(evidence/'finite-source-diagnostic.png',256,128,density[::-1].ravel().tolist())
    return report
if __name__=='__main__':print(json.dumps(build(),indent=2))
