#!/usr/bin/env python3
"""R0013 semantic mutants through actual parsers, builders and main callers.

Every discriminating mutant must parse, fail its named behavioral assertions,
and preserve paired healthy controls. Native downstream parser protection is
measured and retained separately; an observed survivor never earns mutation
credit. The exact source is never edited.
"""
import hashlib, json, os, pathlib, subprocess, sys, tempfile

SOURCE=pathlib.Path(sys.argv[1]).resolve()
TEXT=SOURCE.read_text(encoding='utf-8')
TESTS=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(tempfile.mkdtemp(prefix='salah-discovery-mutants-')).resolve()
RESULTS=[]
APPLICABILITY=[]
HOST_FACTS={}
BASH=os.environ.get('SALAH_TEST_BASH','/bin/bash')
PS=sys.argv[2] if len(sys.argv)>2 else os.environ.get('INSTALL_TEST_PS7',r'C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe')
CONTROLS=['actual parser empty','actual parser new','strict JSON complex valid control']

def changed(old,new):
    if TEXT.count(old)!=1: raise RuntimeError('Mutant boundary drift: '+old)
    return TEXT.replace(old,new,1)

if SOURCE.suffix=='.sh':
    cases=[
        ('missing-to-absence',changed('0|0||unknown|metadata-absent|firefox-extensions-json|%s','0|0||known-neither|metadata-absent|firefox-extensions-json|%s'),['actual parser missing','actual missing metadata is held']),
        ('catch-to-absence',changed('emit("unknown", "metadata-malformed")','emit("known-neither", "metadata-malformed")'),['actual parser malformed','actual unknown only refuses before staging']),
        ('drop-builder-knowledge',changed('|$discovery_status|$discovery_reason|$discovery_evidence|$discovery_source")','")'),['actual target builder keeps states and source identity']),
        ('default-all-admits-unknown',changed("*) printf 'unknown-held' ;;","*) printf 'eligible-known' ;;"),['actual all mixed selection keeps useful known peer','actual unknown only refuses before staging']),
        ('known-both-becomes-safe-new',changed('emit(status, "supported-metadata")','if has_new and has_old:\n    has_old = False\n    status = "known-new"\nemit(status, "supported-metadata")'),['actual parser both','actual known both refuses before staging']),
        ('no-python-negative-proves-absence',changed("%s|%s|%s|unknown|parser-unavailable|firefox-text-heuristic|%s","%s|%s|%s|known-neither|parser-unavailable|firefox-text-heuristic|%s"),['no Python empty','no Python mixed preview keeps independent Chromium peer']),
        ('held-summary-erased',changed('Selected targets: %s eligible, %s held, %s refused.','Selected targets: %s eligible, %s omitted, %s refused.'),['actual all mixed selection keeps useful known peer']),
        ('diagnostic-on-record-stream',changed('emit("unknown", "metadata-malformed")','print("metadata parse diagnostic")\n    emit("unknown", "metadata-malformed")'),['actual parser malformed']),
        ('insufficient-identity-proves-absence',changed('    if not hay.strip():\n        emit("unknown", "metadata-unsupported")\n        raise SystemExit\n',''),['insufficient identity empty-object','actual insufficient identity held with known peer']),
        ('newline-producer-alias',changed('case "$p" in *$\'\\n\'*|*$\'\\r\'*) warn "Unsupported newline in Firefox profile path; profile excluded before selection." ;;','case "$p" in *$\'\\n\'*|*$\'\\r\'*) printf \'%s\\n\' "$p" ;;'),['newline profile cannot alias a safe target firefox']),
        ('duplicate-json-keys-admitted',changed(', object_pairs_hook=unique_object',''),['strict JSON duplicate-addons','strict JSON escaped-duplicate-name','actual duplicate keys cannot hide legacy from selection']),
        ('non-json-constants-admitted',changed(', parse_constant=reject_constant',''),['strict JSON non-json-NaN','strict JSON non-json-Infinity']),
    ]
    fixture=[sys.executable,str(TESTS/'install-discovery.py')]
else:
    CONTROLS.append('actual strict validator valid paired control')
    capabilities=ROOT/'host-parser-capabilities.ps1'
    capabilities.write_text(r'''
$ErrorActionPreference='Stop'
$data=ConvertFrom-Json -InputObject '[{"addons":[]}]'
$accepted=@{}
foreach($row in @(
    @('trailing-comma','{"addons":[],}'),@('array-trailing-comma','{"addons":[],"other":[1,]}'),
    @('trailing-comment','{"addons":[]} /* comment */'),@('single-quotes',"{'addons':[]}"),@('bare-key','{addons:[]}')
)){
    try{$null=ConvertFrom-Json -InputObject $row[1] -ErrorAction Stop;$accepted[$row[0]]=$true}
    catch{$accepted[$row[0]]=$false}
}
[pscustomobject]@{version=$PSVersionTable.PSVersion.ToString();singletonType=$data.GetType().FullName;singletonIsArray=($data -is [array]);singletonIsObject=($data -is [pscustomobject]);accepts=$accepted}|ConvertTo-Json -Depth 8 -Compress
''',encoding='ascii')
    probe_env=dict(os.environ)
    for key in list(probe_env):
        if key.lower()=='psmodulepath': del probe_env[key]
    probe=subprocess.run([PS,'-NoProfile','-File',str(capabilities)],env=probe_env,capture_output=True,text=True,timeout=20)
    (ROOT/'host-parser-capabilities.stdout.txt').write_text(probe.stdout,encoding='utf-8')
    (ROOT/'host-parser-capabilities.stderr.txt').write_text(probe.stderr,encoding='utf-8')
    if probe.returncode: raise RuntimeError('Native parser acquisition failed: '+probe.stderr)
    HOST_FACTS=json.loads(probe.stdout)
    if not all(isinstance(HOST_FACTS['accepts'].get(k),bool) for k in ('trailing-comma','array-trailing-comma','trailing-comment','single-quotes','bare-key')):
        raise RuntimeError('Incomplete native parser capabilities')
    cases=[
        ('catch-to-absence',changed("$result.Reason='metadata-malformed'","$result.Reason='metadata-malformed'; $result.Status='known-neither'"),['actual parser malformed','actual unknown only refuses before staging']),
        ('singleton-root-array-admitted',changed("$raw -notmatch '^\\s*\\{' -or ",''),['unsupported shape root-singleton-empty','unsupported shape root-singleton-new','actual singleton root array held with known peer']),
        ('drop-builder-knowledge',changed('DiscoveryStatus=$status.Status; DiscoveryReason=$status.Reason;','DiscoveryStatus=$null; DiscoveryReason=$status.Reason;'),['actual target builder keeps states source and safe peers']),
        ('default-all-admits-unknown',changed("default { return 'unknown-held' }","default { return 'eligible-known' }"),['actual all mixed selection keeps known peer','actual unknown only refuses before staging']),
        ('known-both-becomes-safe-new',changed("$result.Reason='supported-metadata'","$result.Reason='supported-metadata'\n        if ($result.HasNew -and $result.HasOld) { $result.HasOld=$false; $result.Status='known-new' }"),['actual parser both','actual both refuses before staging']),
        ('held-summary-erased',changed('Selected targets: $eligibleCount eligible, $heldCount held, $refusedCount refused.','Selected targets: $eligibleCount eligible, $heldCount omitted, $refusedCount refused.'),['actual all mixed selection keeps known peer']),
        ('diagnostic-on-object-stream',changed('Write-Warn "Firefox discovery held: malformed metadata."','Write-Output "metadata parse diagnostic"'),['actual parser malformed']),
        ('insufficient-identity-proves-absence',changed('        if ([string]::IsNullOrWhiteSpace($hay)) { $supported=$false; break }\n',''),['insufficient identity empty-object','actual insufficient identity held with known peer']),
        ('strict-json-guard-bypassed',changed("        if (-not (Test-StrictJson $raw)) { throw 'Invalid or ambiguous JSON metadata.' }\n",''),['strict JSON trailing-comma','strict JSON trailing-comment','strict JSON single-quotes','strict JSON bare-key','actual duplicate keys cannot hide legacy from selection']),
        ('duplicate-json-keys-admitted',changed('                if (-not $frame.Keys.Add($keyText.ToString())) { return $false }','                [void]$frame.Keys.Add($keyText.ToString())'),['strict JSON duplicate-addons','strict JSON escaped-duplicate-name','actual duplicate keys cannot hide legacy from selection']),
        ('trailing-separators-admitted',changed("$frame.State=if ($frame.Kind -eq 'object') { 'key' } else { 'value' }","$frame.State=if ($frame.Kind -eq 'object') { 'key-or-end' } else { 'value-or-end' }"),['actual strict validator object-trailing-comma','actual strict validator array-trailing-comma','strict JSON trailing-comma','strict JSON array-trailing-comma']),
    ]
    fixture=[PS,'-NoProfile','-File',str(TESTS/'install-discovery.ps1'),'-SourceFile']
    parser=ROOT/'parse.ps1'
    parser.write_text('param([string]$SourceFile)\n$t=$null;$e=$null;$null=[Management.Automation.Language.Parser]::ParseFile($SourceFile,[ref]$t,[ref]$e);if(@($e).Count){exit 1}\n',encoding='ascii')

def invoke(source,names):
    env=dict(os.environ,SALAH_DISCOVERY_CASES=json.dumps(CONTROLS+names))
    for key in list(env):
        if key.lower()=='psmodulepath': del env[key]
    result=subprocess.run(fixture+[str(source)],env=env,capture_output=True,text=True,timeout=90)
    receipt=ROOT/(source.stem+'.result.json')
    receipt.write_text(result.stdout,encoding='utf-8')
    receipt.with_suffix('.stderr').write_text(result.stderr,encoding='utf-8')
    payload=json.loads(result.stdout)
    rows={r['case']:r for r in payload['results']}
    if set(rows)!=set(CONTROLS+names): raise RuntimeError('Fixture did not reach required controls/assertions: '+str(set(rows)))
    return result,rows,receipt

# A healthy result for the exact candidate is required before fault injection.
all_names=sorted({name for _,_,names in cases for name in names})
healthy,rows,receipt=invoke(SOURCE,all_names)
healthy_ok=healthy.returncode==0 and all(r.get('pass_',r.get('pass',False)) for r in rows.values())
RESULTS.append(dict(case='exact-source paired controls and assertions',pass_=healthy_ok,fixtureExit=healthy.returncode,receipt=str(receipt)))
if healthy_ok:
    for name,mutant,assertions in cases:
        path=ROOT/(name+SOURCE.suffix);path.write_text(mutant,encoding='utf-8')
        parse_cmd=[BASH,'-n',str(path)] if SOURCE.suffix=='.sh' else [PS,'-NoProfile','-File',str(parser),'-SourceFile',str(path)]
        parsed=subprocess.run(parse_cmd,capture_output=True,text=True,timeout=20)
        if parsed.returncode: raise RuntimeError('Invalid mutant syntax: '+name+parsed.stdout+parsed.stderr)
        result,rows,receipt=invoke(path,assertions)
        failed=[n for n in assertions if not rows[n].get('pass_',rows[n].get('pass',False))]
        controls_ok=all(rows[n].get('pass_',rows[n].get('pass',False)) for n in CONTROLS)
        detail=dict(case=name,syntaxExit=parsed.returncode,fixtureExit=result.returncode,failedCases=failed,pairedControlsPass=controls_ok,mutant=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),receipt=str(receipt))
        if name=='singleton-root-array-admitted' and HOST_FACTS.get('version','').startswith('5.1.') and HOST_FACTS.get('singletonIsArray') is True:
            # Actual PS5.1 preserves the array, so the separate production type
            # check protects the same consumer. Retain, never credit, this survivor.
            if result.returncode==0 and not failed and controls_ok:
                APPLICABILITY.append(dict(detail,executed=True,detected=False,disposition='non-discriminating on this acquired host: singleton array retained and downstream production type check still refuses; no mutation PASS'))
                continue
        required=list(assertions)
        if name in ('strict-json-guard-bypassed','trailing-separators-admitted'):
            required=[n for n in assertions if not n.startswith('strict JSON ') or HOST_FACTS['accepts'].get(n[len('strict JSON '):],True)]
        protected=[n for n in assertions if n not in required]
        RESULTS.append(dict(detail,detected=bool(required and result.returncode and set(failed)==set(required) and controls_ok),requiredFailedCases=required,downstreamProtectedCases=protected))
print(json.dumps(dict(source=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),fixture=str(ROOT),hostParserCapabilities=HOST_FACTS,results=RESULTS,applicability=APPLICABILITY),indent=2))
sys.exit(0 if all(r.get('detected',r.get('pass_',False)) for r in RESULTS) else 1)
