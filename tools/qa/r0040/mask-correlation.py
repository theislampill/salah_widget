"""Autocorrelation across every 1/60 s lag from 0.4 to 30 s of each 60 s Canvas-command sequence."""
import sys,json
from pathlib import Path
import numpy as np
from scipy.fft import rfft,irfft,next_fast_len


def correlation(x):
    n=len(x)
    fft_len=next_fast_len(2*n-1)
    numerator=np.zeros(n)
    energy=np.zeros(n)
    for start in range(0,x.shape[1],64):
        slab=x[:,start:start+64].astype(float)
        slab-=slab.mean(axis=0)
        energy+=np.einsum('ij,ij->i',slab,slab)
        z=rfft(slab,n=fft_len,axis=0)
        numerator+=irfft((z*z.conj()).real.sum(axis=1),n=fft_len)[:n]
    cumulative=np.r_[0,np.cumsum(energy)]
    lags=np.arange(24,1801)
    den=np.sqrt(cumulative[n-lags]*(cumulative[n]-cumulative[lags]))
    if np.any(den<=0):
        raise ValueError('no usable temporal variation')
    r=numerator[lags]/den
    peak=np.argmax(r)
    return {'max':float(r[peak]),'lagSeconds':float(lags[peak]/60),'at4.2s':float(r[252-24])}


if __name__=='__main__':
    root=Path(sys.argv[1])
    report=[]
    for field in json.loads((root/'distribution.json').read_bytes()):
        x=np.memmap(root/(str(field['rate'])+'.bin'),dtype='uint8',mode='r',shape=(3600,65*59))
        result=correlation(x)
        if field['rate']==5:
            # A fixed repeating 4.2 s segment from the same actual command sequence.
            mutant=correlation(x[np.arange(len(x))%252,:])
            assert mutant['at4.2s']>.999
        field['correlation']=result
        report.append(field)
    print(json.dumps({'kind':'Canvas stroke endpoints in 5 px bins; no raster or native acceptance',
                      'lagRangeSeconds':[.4,30],'fixedLoopMutant':mutant,'cells':report},separators=(',',':')))
