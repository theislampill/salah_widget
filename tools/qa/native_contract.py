"""Pure receipt discriminators; actual inputs are supplied by the root's browser run."""
import math

def effect_checks(state,samples,spec,origins=None):
    truth=(state.get('qa')or{}).get('wxTruth')or{}
    permission=(truth.get('visualPermissions')or{}).get('lightning')
    expected=spec.get('expect')or{}
    c={'neverUpgradesDirectObservation':truth.get('observedPresent')is False}
    if 'wet' in expected:
        n=state.get('visibleParticles')
        c['particlesFromActualComputedVisibility']=type(n)is int and ((state.get('precip')=='on' and n>0) if expected['wet'] else (state.get('precip')=='off' and n==0))
    if expected.get('strikes'):
        # This exception is tied to the exact declared owned synthetic observed input.
        declared=any(a.get('present',{}).get('state')=='wet' and a.get('present',{}).get('type')=='rain' and a.get('present',{}).get('lightning')=='observed' for a in spec.get('actions',[]))
        evidence=(truth.get('present')or{}).get('evidence')or{}
        c['syntheticObservedExceptionIsExact']=spec.get('preview')is True and declared and evidence.get('scope')=='simulation-fixture' and evidence.get('policy')=='synthetic-present-v1' and (evidence.get('present')or{}).get('lightning')=='observed' and truth.get('observedPresent')is False and permission is True
    else:
        c['noObservedLightningPermission']=permission is False and state.get('lightning')=='off'
        c['noActualStrikeInNegative']=bool(samples) and all(x.get('opacity')==0 and not x.get('animations') for frame in samples for x in frame)
    if 'cloud-origin' in spec.get('nativeChecks',[]):
        particles=[p for p in (origins or{}).get('particles',[]) if p.get('visible')is True]
        c['positiveParticleOriginObserved']=bool(particles)
        c['allVisibleParticlesUnderCloudColumns']=bool(particles) and (origins or{}).get('mx',0)>0 and all(isinstance(p.get('densityFraction'),(int,float)) and p['densityFraction']>.16 for p in particles)
        c['particlesStartInsideCardUnderDeck']=bool(particles) and all(isinstance(p.get('authoredTopPx'),(int,float)) and p['authoredTopPx']>=0 for p in particles)
    return c

def strike_checks(samples,spec):
    values=[x.get('opacity') for frame in samples for x in frame if isinstance(x.get('opacity'),(int,float)) and math.isfinite(x['opacity'])]
    reduced=spec.get('motion')=='reduce' and not spec.get('motionFull')
    if reduced:return {'actualReducedFlashSuppressed':bool(values) and max(values)==0,'actualReducedAnimationsStopped':all(not x.get('animations') for frame in samples for x in frame)}
    # Native WeakMap IDs distinguish actual DOM elements, including SVG className objects.
    # A minimum on the bolt cannot supply the flash's before/after low observation.
    tracks={};identity_valid=bool(samples)
    for frame_index,frame in enumerate(samples):
        seen=set()
        for item in frame:
            identity=item.get('elementId');opacity=item.get('opacity')
            if type(identity)is not int or identity<1 or identity in seen:
                identity_valid=False;continue
            seen.add(identity)
            if type(opacity)not in (int,float)or not math.isfinite(opacity):identity_valid=False;continue
            tracks.setdefault(identity,[]).append((frame_index,opacity,item.get('animations')or[]))
    temporal=False;animated=False
    if identity_valid:
        for points in tracks.values():
            if len(points)!=len(samples):continue # missing samples do not count as a return
            for peak_index,(_,peak,animations)in enumerate(points):
                if peak<=.5:continue
                before=[p[1]for p in points[:peak_index]if p[1]<=.1 and peak-p[1]>.4]
                after=[p[1]for p in points[peak_index+1:]if p[1]<=.1 and peak-p[1]>.4]
                if before and after:
                    temporal=True;animated=animated or bool(animations)
    # Keep the existing period and peak bounds; no new weather calibration.
    return {'actualExistingPeriodCovered':spec.get('strikeObservationSeconds',0)>=24,
            'actualStrikeRisePeakAndReturn':temporal,
            'actualStrikeNativeAnimation':animated}

def info_applicability(raw_checks,spec,engine):
    """Keep raw approved-oracle results; make explicit engine/synthetic applicability."""
    na={}
    if spec.get('expect',{}).get('strikes'):
        na['noLightningGranted']='INFO-only no-lightning negative does not describe this exact declared synthetic observed-lightning positive; separate strict positive oracle remains required'
    if engine=='firefox':
        for key in ['axNamePreservesSummary','axNameMatchesDOM','axDescriptionSameSnapshotOnce','existingIconDescriptionPreserved','settingsActionNameIntact','settingsActionRoleIntact','existingSettingsDescriptionPreserved','settingsAXInformationOnce']:
            if key in raw_checks:na[key]='Chromium CDP AX unavailable for Firefox; raw aria_snapshot and DOM retained, independent accessible consumer review required; no fabricated AX input'
    return {'rawApprovedOracle':raw_checks,'notApplicable':na,'applicable':{k:v for k,v in raw_checks.items()if k not in na}}

def alpha_checks(state,spec):
    radar=state.get('radar')or{}
    sample=radar.get('sample')or{}
    c={'radarUnitlessOnly':radar.get('precipMm')==0 and bool(sample) and 'uncalibrated' in radar.get('quantitativeAuthority',''),
       'alphaNeverGrantsLocalDryOrWet':(state.get('qa',{}).get('wxTruth')or{}).get('observedPresent')is False and state.get('visibleParticles')==0 and state.get('lightning')=='off'}
    if spec.get('tile')=='three-neighbours':c['threeWetNeighboursNotGroundAuthority']=sample.get('returnCount')==3 and sample.get('sampledCount')==49
    return c

def provenance_checks(state,spec):
    info=state.get('information')or{};decision=info.get('decision')or{};truth=(state.get('qa')or{}).get('wxTruth')or{}
    c={'currentSpatialHorizonForecastSameSnapshot':all(decision.get(key)==truth.get(key)for key in ['current','spatial','horizon','forecast']),
       'noFormattedNonfiniteQuantity':not any(t in (info.get('description')or'')for t in ['NaN','Infinity']),
       'rawAndCacheRemainDistinctFromSelected':not (state.get('raw')is None and state.get('cached')is not None and (state.get('cached')or{}).get('w')is None)}
    model=decision.get('model')or{};quantity=model.get('quantity');record=decision.get('record')
    if quantity is not None:
        value=quantity.get('value');c['modelAmountKindUnitsAndNoInstantaneousClaim']=isinstance(value,(int,float))and math.isfinite(value)and value>=0 and quantity.get('kind')=='preceding-interval-amount' and quantity.get('units')=='mm' and quantity.get('instantaneous')is False
        if record:
            source=record.get('currentValidAt');interval=record.get('currentIntervalSec')
            c['amountPrecedingSourceWindow']=quantity.get('to')==source and quantity.get('from')==(source-interval*1000 if source is not None and interval is not None else None)
            expected=value*3600/interval if interval else None
            expected=expected if expected is not None and math.isfinite(expected)else None
            c['finiteAverageOrExplicitUnavailable']=quantity.get('averageRateMmH')==expected
            if spec['id']=='quantity-derived-overflow':c['derivedOverflowDoesNotEraseFiniteAmount']=value>1e308 and quantity.get('averageRateMmH')is None
    if spec['id']=='quantity-interval':
        c['pointFourMmOver900Seconds']=quantity is not None and quantity.get('value')==.4 and quantity.get('to')-quantity.get('from')==900000 and quantity.get('averageRateMmH')==1.6 and 'interval average, not instantaneous'in (info.get('description')or'')
    if spec['id']in ['quantity-null','quantity-negative','quantity-string-infinity','quantity-literal-overflow']:
        c['unavailableQuantityNotZero']=(state.get('raw')or{}).get('precip','missing')is None and quantity is None and 'amount unavailable'in (info.get('description')or'')
    if spec['id']=='quantity-zero':c['zeroQuantityRetained']=quantity is not None and quantity.get('value')==0
    if spec['id']in ['synthetic-rate','synthetic-amount']:
        q=((truth.get('present')or{}).get('evidence')or{}).get('present',{}).get('quantity')or{}
        c['syntheticQuantityIndependentKindUnits']=q.get('kind')==('rate'if spec['id']=='synthetic-rate'else 'amount')and q.get('value')==(1.6 if spec['id']=='synthetic-rate'else .4)and q.get('units')==('mm/h'if spec['id']=='synthetic-rate'else 'mm')
    forecast=decision.get('forecast')
    if forecast:
        p=forecast.get('probability');event=forecast.get('probabilityEvent')
        c['probabilityNullDistinctFromZero']=event is None if p is None else isinstance(p,(int,float))and math.isfinite(p)and 0<=p<=100 and isinstance(event,dict)and event.get('event')=='precipitation'and event.get('from')==forecast.get('validFrom')and event.get('to')==forecast.get('validUntil')
    if spec.get('locationEvidence'):
        target=state.get('target')or{};e=spec['locationEvidence'];c['locationAccuracyAndOriginalFixRetained']=target.get('accuracyM')==e.get('accuracyM')and target.get('intent')==e.get('intent')
        if e.get('source')=='browser-geolocation' and 'acquiredOffsetMs'in e:c['saveNeverRenewsOriginalFix']=target.get('acquiredAt')==1788773400000+e['acquiredOffsetMs']
        elif e.get('source')!='browser-geolocation':c['nonDeviceSourceHasNoInventedFixTime']=target.get('acquiredAt')is None
    return c
