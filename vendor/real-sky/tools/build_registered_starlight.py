#!/usr/bin/env python3
"""Deterministic V-component preparation from the authenticated Gaia/Hipparcos map.
Whole-cell exclusion precedes every filter; no HYG/Gaia photometric subtraction.
Missing native support and locally estimated replacements remain separately auditable.
"""
from pathlib import Path
import gzip,hashlib,io,json,math,subprocess
import numpy as np
from scipy.spatial import cKDTree
from healpix_grid import centres,unit_vectors,pixel_area,coarsen,ang2pix,pix2ang,checked_nside
from qualify_starmap import ROOT,SOURCE,load_source,zero_points,write_json
from cp7_acquire_source import EXPECTED_SHA256
NSIDE=256
TOLERANCE_DEG=.1
TIERS=(128,64,32)

def exclusion(nside,directions,tolerance_deg=TOLERANCE_DEG):
    n=checked_nside(nside)
    if not directions or not math.isfinite(tolerance_deg) or not 0<=tolerance_deg<=1:raise ValueError('Invalid source exclusion policy')
    lon=np.array([d['raDeg'] for d in directions]);lat=np.array([d['decDeg'] for d in directions])
    if not np.isfinite(lon).all() or not np.isfinite(lat).all() or (abs(lat)>90).any():raise ValueError('Invalid emitter position')
    c=centres(n);star=unit_vectors(lon,lat)
    dist,_=cKDTree(star).query(c,k=1,workers=1)
    # 2/n radians deliberately exceeds the maximum native HEALPix cell radius.
    # A cell intersecting the declared emitter tolerance disc is removed in full.
    radius=math.radians(tolerance_deg)+2/n
    return dist<=2*math.sin(radius/2),c,math.degrees(radius)

def fill_masked(values,mask,donors):
    a=np.asarray(values,dtype=np.float64);m=np.asarray(mask);d=np.asarray(donors)
    if a.ndim!=1 or m.shape!=a.shape or m.dtype!=bool or not np.isfinite(a).all() or (a<0).any():raise ValueError('Invalid native field/mask')
    if d.ndim!=2 or d.shape[0]!=int(m.sum()) or d.shape[1]<1 or not np.issubdtype(d.dtype,np.integer) or (d<0).any() or (d>=len(a)).any():raise ValueError('Invalid donor addresses')
    if np.any(m[d]):raise ValueError('Excluded source cannot be an estimate donor')
    out=a.copy();out[m]=np.median(a[d],axis=1)
    return out

def tier(values,nside,target):
    n=checked_nside(nside);t=checked_nside(target)
    if t>n or len(values)!=12*n*n:raise ValueError('Invalid tier shape/resolution')
    return coarsen(values,n//t)

def write_npy_gz(path,values):
    stream=io.BytesIO();np.save(stream,values,allow_pickle=False)
    Path(path).write_bytes(gzip.compress(stream.getvalue(),compresslevel=6,mtime=0))

def build(root=ROOT):
    root=Path(root);src,h=load_source(root);raw=src[:,1];f0=zero_points(h)['V']
    run=subprocess.run(['node',str(root/'tools/export_cp7_emitters.mjs')],cwd=root,capture_output=True,text=True,check=True)
    emit=json.loads(run.stdout);directions=[d for s in emit['stars'] for d in s['directions']]
    mask,c,radius=exclusion(NSIDE,directions);good=np.flatnonzero(~mask);bad=np.flatnonzero(mask)
    distance,local=cKDTree(c[good]).query(c[bad],k=32,workers=1);donors=good[local]
    # Resolve distance ties by pixel identity, deterministic on the retained grid.
    order=np.lexsort((donors,distance),axis=1);donors=np.take_along_axis(donors,order,axis=1);distance=np.take_along_axis(distance,order,axis=1)
    filled=fill_masked(raw,mask,donors[:,:16]);strict=raw.copy();strict[mask]=np.nan
    out=root/'data/registered-starlight';out.mkdir(exist_ok=True,parents=True)
    write_json(out/'emitter-exclusion.json',emit)
    for name,a in [('native-V-strict.npy.gz',strict),('native-V-estimated.npy.gz',filled),('native-exclusion-mask.npy.gz',mask.astype(np.uint8)),('native-estimate-donors.npy.gz',donors[:,:16].astype('<i4'))]:write_npy_gz(out/name,a)
    omega=pixel_area(NSIDE);original=float(raw.sum()*omega);removed=float(raw[mask].sum()*omega);retained=float(raw[~mask].sum()*omega);replacement=float(filled[mask].sum()*omega);total=float(filled.sum()*omega)
    report={'status':'PASS','stage':'7.2','sourceSha256':EXPECTED_SHA256,'catalogueSha256':emit['catalogueSha256'],'catalogueRecords':emit['retainedRecords'],'emittedSources':emit['emitterCount'],'withheldRecords':emit['withheldCount'],'sourcePositionEpochs':emit['epochs'],
      'policy':'whole native source-cell exclusion, before any filtering; median of nearest 16 nonexcluded cells for explicitly flagged estimates',
      'positionToleranceDeg':TOLERANCE_DEG,'nativeCellRadiusEnvelopeDeg':math.degrees(2/NSIDE),'exclusionCentreRadiusDeg':radius,'nativeExcludedCells':int(mask.sum()),'nativeRetainedCells':int((~mask).sum()),'estimatedAreaFraction':float(mask.mean()),
      'strictMaster':'native-V-strict.npy.gz: NaN denotes absent source support; validity is supplied separately',
      'uncertainty':'The positional tolerance is a declared engineering contract, not an exhaustive Gaia-HYG identity crossmatch. The local-fill sensitivity is not a confidence interval or a claim to measure missing light.',
      'lightAccountingWm2nm':{'original':original,'removedAllLightInGuardCells':removed,'retainedOriginal':retained,'addedLocalEstimates':replacement,'correctedTotal':total,'originalMinusRetainedMinusRemoved':original-retained-removed,'correctedMinusRetainedMinusEstimated':total-retained-replacement},
      'estimatedFluxFraction':replacement/total,'emitterFluxIndependence':'All output dependence on masked input values is exactly zero; source overlap is removed subject to the stated position envelope. Unlisted stars outside that envelope are not claimed cross-identified.',
      'meanFloorOwnership':'This is direct extra-atmospheric unresolved integrated starlight only. CP7.4 must subtract/reconcile the integrated-starlight share of CP6 lumped natural-night floor before addition. No measured airglow claim.',
      'zeroPointWm2nm':f0,'quantity':'passband-averaged spectral radiance W m^-2 sr^-1 nm^-1','donorDistanceDeg':{'p95':float(np.percentile(np.rad2deg(2*np.arcsin(distance[:,15]/2)),95)),'max':float(np.max(np.rad2deg(2*np.arcsin(distance[:,15]/2))))},'tiers':[]}
    for count in [8,32]:
        alternative=fill_masked(raw,mask,donors[:,:count]);report.setdefault('fillNeighbourSensitivity',{})[str(count)]={'relativeTotalChange':float(alternative.sum()/filled.sum()-1),'excludedCellMedianRelativeChange':float(np.median(np.abs(alternative[mask]-filled[mask])/np.maximum(filled[mask],1e-300)))}
    # A held-out, nonemitter-cell proxy checks the interpolation, not unknown true holes.
    hold=good[::113];remain=good[~np.isin(good,hold)];_,idx=cKDTree(c[remain]).query(c[hold],k=16,workers=1);pred=np.median(raw[remain[idx]],axis=1)
    report['heldOutEstimateProxy']={'cells':len(hold),'medianAbsoluteLog10Error':float(np.median(abs(np.log10(pred/raw[hold])))),'p95AbsoluteLog10Error':float(np.percentile(abs(np.log10(pred/raw[hold])),95)),'meaning':'Stellar shot noise remains. This is interpolation sensitivity on withheld unmasked cells, not empirical validation of every excluded cell.'}
    for target in TIERS:
        values=tier(filled,NSIDE,target);fractions=tier(mask.astype(float),NSIDE,target)
        # 12 significant digits: much tighter than the declared 1e-8 serial budget.
        vs=[float(format(v,'.12g')) for v in values];mf=[float(format(v,'.12g')) for v in fractions]
        asset={'schema':'salah-real-sky/registered-starlight/1','id':f'GaiaDR3-Hipparcos-V-CP6excluded-nside{target}-v1','component':'unresolved-integrated-starlight-V','sourceSha256':EXPECTED_SHA256,'catalogueSha256':emit['catalogueSha256'],'dataAdmitted':True,'rawAdditiveCompositionAllowed':False,
          'frame':'ICRS','grid':{'type':'HEALPix','order':'NESTED','nside':target},'quantity':'passband-averaged-spectral-radiance-W-m-2-sr-1-nm-1','band':'V','zeroPointWm2nm':f0,'colourStatus':'one passband; monochrome, not a measured spectrum',
          'calibration':'source photometric scale; empirical Gaia colour transformation; unknown systematic uncertainty','fillPolicy':'median16-nonexcluded-native-cells-before-coarsening','positionToleranceDeg':TOLERANCE_DEG,'integratedWm2nm':float(math.fsum(vs)*pixel_area(target)),'values':vs,'estimatedFraction':mf,
          'attribution':'Rener Castro / TuSKan astrogo; ESA/Gaia/DPAC; ESA Hipparcos; HYG exclusion selection: David Nash / Astronexus CC-BY-SA-4.0',
          'physicalComposition':'Pending CP7.4. Do not add to CP6 lumped natural-night floor unchanged.'}
        p=out/f'V-nside{target}.json';p.write_text(json.dumps(asset,separators=(',',':'),allow_nan=False)+'\n')
        err=abs(asset['integratedWm2nm']/total-1)
        if err>1e-8:raise ValueError('Serialised tier flux budget failed')
        report['tiers'].append({'nside':target,'cells':len(values),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'integratedWm2nm':asset['integratedWm2nm'],'relativeFluxError':err,'meanEstimatedFraction':float(fractions.mean())})
    if abs(original-retained-removed)/original>1e-11 or abs(total-retained-replacement)/total>1e-11:raise ValueError('Flux ledger closure failed')
    write_json(root/'checkpoints/cp7_completion/asset-build.json',report)
    return report
if __name__=='__main__':print(json.dumps(build(),indent=2))
