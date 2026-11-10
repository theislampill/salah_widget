"""Bounded S1 launcher correction, independently discriminated in R0021 r67.

Chromium 148.0.7778.96 enables RenderDocument by default. The installed capture
driver disables it. Remove only that token, retaining every other driver flag;
reject an unreviewed browser version or a changed effective feature list.
This is acquisition configuration, not a product fix or timing qualification.
"""
import re

VERSION='148.0.7778.96'
DISABLED='AvoidUnnecessaryBeforeUnloadCheckSync,BoundaryEventDispatchTracksNodeRemoval,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate,AutoDeElevate,RenderDocument,OptimizationHints,msForceBrowserSignIn,msEdgeUpdateLaunchServicesPreferredVersion'
OLD_ARGUMENT='--disable-features='+DISABLED
NEW_ARGUMENT='--disable-features='+','.join(x for x in DISABLED.split(',') if x!='RenderDocument')

def restore_options(options):
 return {**options,'ignore_default_args':[*options.get('ignore_default_args',[]),OLD_ARGUMENT],
         'args':[*options.get('args',[]),NEW_ARGUMENT]}

def verify_launch(version,command_line):
 if version!=VERSION:raise ValueError('Unreviewed Chromium version for RenderDocument restoration')
 actual=re.findall(r'--disable-features=([^\s"]+)',command_line)
 if actual!=[NEW_ARGUMENT.split('=',1)[1]]:raise ValueError('Effective disabled-feature list differs from reviewed restoration')
 if 'RenderDocument' in command_line:raise ValueError('Unexpected explicit RenderDocument override')
 return {'browserVersion':version,'commandLine':command_line,'removedDisabledFeature':'RenderDocument',
         'otherDisabledFeaturesUnchanged':True,'basis':'R0021 r63/r67 independent causal control; source default restoration only'}
