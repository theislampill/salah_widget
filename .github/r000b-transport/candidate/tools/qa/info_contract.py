"""Pure INFO predicates. AX inputs must be actual Chromium receipts in native runs."""
import re

ICON_HELP='info-existing-icon-help'
BUTTON_HELP='info-existing-settings-help'
ICON_HELP_TEXT='Existing weather icon help.'
BUTTON_HELP_TEXT='Existing settings action help.'


def norm(value):
    return ' '.join(value.split()) if isinstance(value,str) else ''


def tokens(value):
    return value.split() if isinstance(value,str) else []


def info_checks(state,ax,spec):
    info=state.get('information') or {}
    summary=norm(info.get('description'))
    name=norm(info.get('name'))
    title=norm(info.get('title'))
    header=info.get('header') or {}
    decision=info.get('decision') or {}
    truth=(state.get('qa') or {}).get('wxTruth') or {}
    wi=ax.get('#wi') or {}
    computed_name=norm(wi.get('name'))
    description=norm(wi.get('description'))
    current=norm((header.get('information') or {}).get('currentText'))
    nearby=norm((header.get('information') or {}).get('spatialText'))
    approach=norm((header.get('information') or {}).get('horizonText'))
    icon_tokens=tokens(info.get('describedBy'))
    c={
        'summaryExposed':bool(summary) and info.get('sinkExposed') is True,
        'sameDecisionSink':bool(summary) and summary==norm((header.get('information') or {}).get('summary')),
        'tooltipSameSnapshot':bool(summary) and title.count(summary)==1,
        'domNamePreservesTitleAndSummary':bool(name and summary) and name==title and name.count(summary)==1,
        'axNamePreservesSummary':wi.get('ignored') is False and bool(computed_name and summary) and computed_name.count(summary)==1,
        'axNameMatchesDOM':bool(name) and computed_name==name,
        'nativeAriaNameIncludesSummary':bool(name and summary) and name in norm((ax.get('rawAriaSnapshot')or{}).get('#wi')),
        'nativeAriaDescriptionReachable':bool(summary) and summary in norm((ax.get('rawAriaSnapshot')or{}).get('#weather-information')),
        'axDescriptionSameSnapshotOnce':bool(summary) and description.count(summary)==1,
        'existingIconDescriptionPreserved':ICON_HELP in icon_tokens and norm(ICON_HELP_TEXT) in description,
        'existingIconDOMTokenPreserved':ICON_HELP in icon_tokens,
        'informationTokenExactlyOnce':icon_tokens.count('weather-information')==1,
        'noInventedArrivalCountdown':not re.search(r'\b(?:in|within)\s+\d+\s*(?:minutes?|mins?)\b',approach,re.I),
        'noLightningGranted':(truth.get('visualPermissions') or {}).get('lightning') is False and state.get('lightning')=='off',
        'generationMatches':isinstance(header.get('generation'),int) and header.get('generation')==((decision.get('target') or {}).get('generation')),
        'cardGeometry':state.get('card')=={'width':325,'height':530},
        'footerFits':isinstance(state.get('footer'),dict) and state['footer'].get('top',-1)>=0 and state['footer'].get('bottom',531)<=530.1,
    }
    case=spec['id']
    synthetic_information=bool((decision.get('present')or{}).get('available')or (decision.get('forecast')or{}).get('scope')=='simulation-fixture'or (spec.get('preview')and decision.get('record')))
    if synthetic_information:
        c['SIMRetainedInAllExposedInformation']='SIM' in summary and 'SIM' in title and 'SIM' in name
    if case in {'INFO-conflicting','INFO-unknown','INFO-area-no-echo'}:
        expected='supported dry' if case=='INFO-area-no-echo' else case.removeprefix('INFO-')
        c['qualifiedPresentInformationReachesConsumer']=('Current: SIM '+expected) in current and current in summary and summary in name
        c['qualifiedNonWetDoesNotBorrowWetModel']=(decision.get('model') or {}).get('state')=='wet' and state.get('precip')=='off' and state.get('visibleParticles')==0
        if case=='INFO-area-no-echo':
            c['qualifiedAreaNegativeReachesConsumer']='Nearby: SIM observed area has no echo (0–10 km)' in nearby and nearby in summary
            c['noEchoNotInventedArrival']='Approach: SIM none supported; no supported arrival interval'==approach and (decision.get('horizon') or {}).get('arrival') is None
    if case.startswith('C-'):
        wet=case=='C-wet-and-approach'
        c['currentStateRetained']=('Current: SIM supported wet' if wet else 'Current: SIM supported dry') in current
        c['nearbyRangeRetained']='Nearby: SIM precipitation 8–12 km' in nearby
        c['particlesMatchCurrent']=state.get('precip')==('on' if wet else 'off') and isinstance(state.get('visibleParticles'),int) and (state['visibleParticles']>0 if wet else state['visibleParticles']==0)
        c['currentPermissionIndependent']=((truth.get('permissions') or {}).get('rain')) is wet
        if case in {'C-approach','C-wet-and-approach'}:
            c['qualifiedAbsoluteInterval']='qualified SIM interval 2026-09-07 12:40 to 2026-09-07 13:00 Asia/Riyadh' in approach
            arrival=(decision.get('horizon') or {}).get('arrival') or {}
            c['qualifiedTrajectoryIdentity']=arrival.get('derivedFrom')=='qualified-fixture-trajectory' and arrival.get('from')==1788774000000 and arrival.get('to')==1788775200000
        else:
            c['unqualifiedMovementHasNoArrival']='no supported arrival interval' in approach and 'qualified SIM interval' not in approach and '12:40' not in approach and '13:00' not in approach
    if case in {'D-live-thunder','INFO-local-settings','forecast-production-hourly'}:
        c['noLiveNearbyAdapter']='Nearby: unavailable' in nearby and 'no qualified surrounding source' in nearby
        c['noLiveArrivalAdapter']='no supported arrival interval' in approach and 'qualified SIM interval' not in approach
        c['noDirectObservationClaim']='direct local observation unavailable' in current and truth.get('observedPresent') is False
        c['noSyntheticProductionInstall']=not any(e.get('action')=='present' for e in state.get('events',[]))
        if case=='forecast-production-hourly':
            cache=(state.get('qa') or {}).get('cache') or {}
            # Raw/cache retention is not current admission; test the selected consumers.
            c['unavailableCurrentStaysUnknown']=(current.startswith('Current: unknown') and state.get('modelEligible') is False and cache.get('currentEligible') is False
                and decision.get('lane')=='live' and decision.get('current')=='unknown' and decision.get('conditionState')=='unavailable'
                and all(decision.get(key,'missing') is None for key in ['record','modelCode','renderCode']) and (decision.get('model') or {}).get('code','missing') is None
                and truth.get('current')=='unknown' and truth.get('conditionState')=='unavailable' and truth.get('rawCode','missing') is None
                and all(header.get(key,'missing') is None for key in ['code','rawCode','temperature','sourceValidAt','retrievedAt']) and header.get('conditionState')=='unavailable'
                and state.get('icon')=='—' and header.get('icon')=='—' and state.get('temperature')=='')
            c['retainedCurrentCannotBecomeEligible']=all(record is None or isinstance(record,dict) and record.get('src')=='current' and record.get('currentValidAt','missing') is None
                for record in [state.get('raw'),(state.get('cached') or {}).get('w')])
            c['unavailableCurrentEffectsOff']=(all((layer.get(permission) or {}).get(effect) is False for layer in [decision,truth]
                for permission in ['permissions','visualPermissions'] for effect in ['rain','snow','lightning'])
                and truth.get('activePrecip') is False and truth.get('activeThunder') is False and state.get('precip')=='off' and state.get('lightning')=='off'
                and state.get('rainOpacity')==0 and type(state.get('visibleParticles')) is int and state['visibleParticles']==0
                and state.get('fx')=='unavailable' and truth.get('finalDataFx')=='unavailable')
            forecast=decision.get('forecast') or {}
            forecast_text=norm((header.get('information') or {}).get('forecastText'))
            c['forecastStaysSeparate']=('numerical forecast only' in approach and 'probability unavailable' in forecast_text and cache.get('forecastTrackLoaded') is True
                and (decision.get('horizon') or {}).get('state')=='numerical-forecast-only' and (decision.get('horizon') or {}).get('arrival','missing') is None
                and forecast==truth.get('forecast') and forecast.get('provider')=='Open-Meteo' and forecast.get('product')=='hourly weather model'
                and forecast.get('validFrom')==1788773400000 and forecast.get('validUntil')==1788777000000 and forecast.get('retrievedAt')==1788773400000
                and forecast.get('amount')=={'kind':'preceding-hour-amount','value':2,'units':'mm'} and forecast.get('code')==63
                and forecast.get('probability','missing') is None and forecast.get('probabilityEvent','missing') is None
                and '2026-09-07 12:30 to 2026-09-07 13:30 Asia/Riyadh' in forecast_text and 'preceding-hour amount 2 mm' in forecast_text)
        else:
            c['modelInputStaysEstimate']='CURRENT MODEL ESTIMATE' in current and state.get('raw',{}).get('temp')==20
    if spec.get('local'):
        buckle=info.get('buckle') or {}
        button=ax.get('.buckle') or {}
        btokens=tokens(buckle.get('describedBy'))
        c['settingsDOMNameIntact']=norm(buckle.get('name')).startswith('Widget settings') and summary not in norm(buckle.get('name'))
        c['settingsDOMRoleAndTabIntact']=buckle.get('role')=='button' and buckle.get('tabindex')=='0'
        c['settingsDOMDescriptionsPreserved']=all(x in btokens for x in ['settings-persistence-status',BUTTON_HELP,'weather-information']) and btokens.count('weather-information')==1
        buckle_snapshot=norm((ax.get('rawAriaSnapshot')or{}).get('.buckle'))
        c['nativeSettingsNameAndRoleReachable']='button' in buckle_snapshot and norm(buckle.get('name')) in buckle_snapshot
        c['settingsAssociatedExposedInformation']=c['settingsDOMDescriptionsPreserved'] and c['nativeAriaDescriptionReachable']
        c['settingsActionNameIntact']=norm(buckle.get('name')).startswith('Widget settings') and norm(button.get('name'))==norm(buckle.get('name')) and summary not in norm(button.get('name'))
        c['settingsActionRoleIntact']=buckle.get('role')=='button' and buckle.get('tabindex')=='0' and button.get('role')=='button' and button.get('ignored') is False
        c['existingSettingsDescriptionPreserved']=all(x in btokens for x in ['settings-persistence-status',BUTTON_HELP,'weather-information']) and btokens.count('weather-information')==1 and norm(BUTTON_HELP_TEXT) in norm(button.get('description'))
        c['settingsAXInformationOnce']=bool(summary) and norm(button.get('description')).count(summary)==1
    return c
