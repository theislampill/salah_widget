"""Behavioral controls using measured-event shapes. No synthetic verdict is native evidence."""
from copy import deepcopy
from trial_admission import assess, producer_flags


def run():
    clock={'wall':True,'advancing':False,'preview':False,'fast':False,'chrome':False}
    box=[2,3,20,10]
    base=dict(composed=True,identity='accepted',paused=False,reduced=False,rate=1,clock=clock,
        utcMs=1000,expectedUtc=1000,sunAlt=-30,dimensions=[325,530],header=box,footer=box,buckle=box,
        prayerKeys=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'],prayersReady=True,rowBoxes=[box]*6,
        cloudCurrent=True,cloudPublication='eligible-published',fixtureWx={'cloud':0,'code':0},catalogue='digest',
        cloudSource='hidden',cloudAlpha=0,calendarMoon={'phaseFraction':.08,'calendarMoonVisible':True},predicate='active')
    probe={'path':'stars.status','equals':'active'}
    pubs=[dict(kind='publication',at=t,utcMs=1000+t,ageMs=1,id='hyg:6',tier='refined',identity='accepted',
                 changed=t%100==0,nonempty=True,writes=1,epoch=1) for t in range(50,2001,50)]
    trace=dict(start=0,end=2000,frames=list(range(0,2000,16)),states=[dict(base,t=100),dict(base,t=1100)])
    history=dict(start=0,end=2000,initial={'status':'active','tier':'refined','identity':'accepted'},events=pubs,overflow=False)
    def verdict(tr=None,pr=history,scene='dark',clock='ordinary',label='unmodified'):
        return assess(base,base,tr or trace,pr,scene,[-91,-20],'normal',clock,probe,label,True)['verdict']
    assert verdict()=='passed' and verdict(scene='crescent')=='passed'
    for key,value in [('clock',{**clock,'fast':True}),('prayersReady',False),('cloudCurrent',False),
                      ('utcMs',0),('cloudAlpha',.2),('rowBoxes',[]),('sunAlt',2),('buckle',None),
                      ('composed',False),('identity','old'),('predicate','suspended')]:
        tr=deepcopy(trace);tr['states'][1][key]=value
        assert verdict(tr)=='failed',key
    assert verdict(scene='broken')=='failed' and verdict(scene='full')=='failed' and verdict(clock='simulation')=='failed'
    assert verdict({**trace,'states':[]})=='indeterminate' and verdict(pr=None)=='indeterminate'
    assert verdict(pr={**history,'overflow':True})=='indeterminate'
    assert verdict(pr={**history,'start':1})=='indeterminate'
    for events in [[],pubs[:5]+pubs[-6:],pubs[4:],pubs[:-4],[{**p,'utcMs':1000} for p in pubs],
                    [*pubs[:2],{**pubs[2],'tier':'preview'},*pubs[3:]],
                    [*pubs[:2],{**pubs[2],'ageMs':101},*pubs[3:]],
                    [*pubs,dict(kind='withdraw',at=40)], [*pubs,dict(kind='status',at=40,reason='performance guard suspended')]]:
        assert verdict(pr={**history,'events':events})=='failed'
    for mode in ['all-nominal','constant-encoded','occasional-change','masked-center-wings']:
        events=[{**p,'id':None,'changed':(mode=='occasional-change' and i==20) or (mode=='masked-center-wings' and i%2==1),
                 'nonempty':mode!='all-nominal'} for i,p in enumerate(pubs)]
        out=assess(base,base,trace,{**history,'events':events},'dark',[-91,-20],'normal','ordinary',probe,'unmodified',True)
        assert out['verdict']=='passed' and out['deliveryCadence']=='passed',mode
        assert out['publicationCount']==len(pubs) and out['nonemptyPublicationCount']==sum(e['nonempty'] for e in events)
        assert out['changedCount']==sum(e['changed'] for e in events)
        assert out['encodedChangeCadence']==('at least 10 Hz' if mode=='masked-center-wings' else 'below 10 Hz' if mode=='occasional-change' else 'no observed transitions')
        assert out['pixelEvidence']==('encoded variation observed' if out['changedCount'] else 'no encoded variation demonstrated')
        assert out['humanVisualVerdict'] is None
    repeated=[{**p,'utcMs':pubs[0]['utcMs']} for p in pubs]
    for invalid in [repeated,pubs[:2]+pubs[-2:],[]]:
        out=assess(base,base,trace,{**history,'events':invalid},'dark',[-91,-20],'normal','ordinary',probe,'unmodified',True)
        assert out['deliveryCadence']=='failed' and out['verdict']=='failed'
    assert verdict(pr=None,label='main')=='passed'
    flags='r35arm=full&r35scope=all&r35amplitude=1&r35margin=4&r35glass=0'
    assert producer_flags('unmodified',flags,True)['r35arm']=='full'
    for raw in ['skyAz=20','simMoon=1','debugMotion=1','r35tile=3','r35arm=full','r35guard=','r35foo=1','r35margin=nan']:
        try: producer_flags('unmodified',flags+'&'+raw,True)
        except ValueError: pass
        else: raise AssertionError(raw)
    for raw in ['skyAz=20','simMoon=1','debugMotion=1','r35foo=1']:
        try: producer_flags('historical',raw,False,{'skyAz':['20']})
        except ValueError: pass
        else: raise AssertionError(raw)


if __name__=='__main__': run()
