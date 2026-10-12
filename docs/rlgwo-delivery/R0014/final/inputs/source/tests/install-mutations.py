#!/usr/bin/env python3
"""Targeted behavioral mutants, never edits the product or runs a real installation."""
import hashlib, json, os, pathlib, subprocess, sys, tempfile

source=pathlib.Path(sys.argv[1]).resolve()
tests=source.parent/'tests'
text=source.read_text(encoding='utf-8')
root=pathlib.Path(tempfile.mkdtemp(prefix='salah-install-mutants-'))
results=[]

def replace_once(old,new):
    if text.count(old)!=1: raise RuntimeError('Mutant boundary drift: '+old)
    return text.replace(old,new,1)

if source.suffix=='.sh':
    cases=[
        ('cached-status-stdout',replace_once("ok() { printf '[OK] %s\\n' \"$1\" >&2; }","ok() { printf '[OK] %s\\n' \"$1\"; }"),'install-bash.py'),
        ('restore-mapfile',replace_once('while IFS= read -r p || [ -n "$p" ]; do profiles+=("$p"); profile_count=$((profile_count + 1)); done < <(chromium_profiles "$user_data")','mapfile -t profiles < <(chromium_profiles "$user_data"); profile_count=${#profiles[@]}'),'install-bash.py'),
        ('stdin-human-read',replace_once('read_answer selection "Select target numbers separated by commas, or \'all\' (default all): " || exit 1','read -r -p "Select target numbers separated by commas, or \'all\' (default all): " selection'),'install-entry-bash.py'),
        ('eager-staging',replace_once('BUNDLE_ROOT=""; BUNDLE_ID=""; PRESET_ROOT=""; TERMINAL_OPEN=0','BUNDLE_ROOT=""; BUNDLE_ID=""; PRESET_ROOT=""; TERMINAL_OPEN=0\nmkdir -p "${TMPDIR:-/tmp}/salah-widget-installer"'),'install-entry-bash.py'),
        ('retained-deletion',replace_once('cleanup_staging() {\n  [ "$DRY_RUN" = 0 ] && [ -n "$WORK_ROOT" ] || return 0','cleanup_staging() {\n  [ "$DRY_RUN" = 0 ] && [ -n "$WORK_ROOT" ] || return 0\n  if verify_root "$BUNDLE_ROOT" "$BUNDLE_ID"; then rm -rf -- "$BUNDLE_ROOT"; fi'),'install-bash.py'),
        ('symlink-admission',replace_once('    [ ! -L "$current" ] || { err "Symlink in staged path: $current"; return 1; }','    : # mutant admits staged symlink'),'install-bash.py'),
        ('archive-parent-member',replace_once("or any(p in ('', '.', '..') or ':' in p for p in parts)","or any(p in ('', '.') or ':' in p for p in parts)"),'install-bash.py'),
        ('preview-cleanup',replace_once('cleanup_staging() {','cleanup_staging() {\n  rm -rf -- "${TMPDIR:-/tmp}/salah-widget-installer"'),'install-entry-bash.py'),
    ]
    for name,mutant,fixture in cases:
        path=root/(name+'.sh'); path.write_text(mutant,encoding='utf-8')
        parser=subprocess.run(['bash','-n',str(path)],capture_output=True,text=True)
        if parser.returncode: raise RuntimeError('Invalid mutant syntax: '+name+parser.stderr)
        run=subprocess.run([sys.executable,str(tests/fixture),str(path)],capture_output=True,text=True,timeout=90)
        receipt=root/(name+'.txt'); receipt.write_text(run.stdout+run.stderr,encoding='utf-8')
        parsed=json.loads(run.stdout); failed=[r['case'] for r in parsed['results'] if not r['pass_']]
        results.append(dict(case=name,syntaxExit=parser.returncode,fixtureExit=run.returncode,detected=run.returncode!=0 and bool(failed),failedCases=failed,mutant=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),receipt=str(receipt)))
else:
    host=sys.argv[2] if len(sys.argv)>2 else r'C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe'
    native_env=dict(os.environ)
    # A Python child bypasses pwsh's automatic module-path adjustment for 5.1.
    # Let each native host initialize its own module search path; parent env is unchanged.
    for key in list(native_env):
        if key.lower()=='psmodulepath': del native_env[key]
    cases=[
        ('eager-staging',replace_once('function Initialize-Staging {','New-Item -ItemType Directory -Force -Path $DownloadRoot, $PresetRoot | Out-Null\n\nfunction Initialize-Staging {'),'install-entry.ps1'),
        ('clipboard-guard',replace_once('    if ($DryRun) { Write-Host "[dry-run] Clipboard copy suppressed."; return $false }','    # mutant ignores clipboard dry-run guard'),'install-powershell-guards.ps1'),
        ('cached-metadata',replace_once('    if ($DryRun) { throw "Offline preview cannot resolve remote GitHub releases or use cached metadata." }\n    if ($script:LatestRelease) { return $script:LatestRelease }','    if ($script:LatestRelease) { return $script:LatestRelease }\n    if ($DryRun) { throw "Offline preview cannot resolve remote GitHub releases or use cached metadata." }'),'install-powershell-guards.ps1'),
        ('cached-asset',replace_once('function Download-Asset($Asset) {','function Download-Asset($Asset) {\n    $cachedPreviewPath=Join-Path (Join-Path $DownloadRoot "v-fixture") $Asset.name\n    if (Test-Path -LiteralPath $cachedPreviewPath) { return $cachedPreviewPath }'),'install-powershell-guards.ps1'),
        ('copy-during-preview',replace_once('    Write-Section "Offline preview"','    Write-Section "Offline preview"\n    Set-Clipboard -Value "mutant preview copy"'),'install-entry.ps1'),
        ('selector-binding',replace_once('$assets | Where-Object { $_.name -match "(?i)chrom(e|ium).*\\.zip$" -and $_.name -notmatch "(?i)firefox|safari|source" }','$assets | Where-Object { $_.name -match "(?i)chrom(e|ium).*\\.zip$" -and $_.name -notmatch "(?i)firefox|safari|source" },'),'install-powershell.ps1'),
    ]
    parser=root/'parse.ps1'
    parser.write_text('param([string]$SourceFile)\n$t=$null;$e=$null;$null=[System.Management.Automation.Language.Parser]::ParseFile($SourceFile,[ref]$t,[ref]$e);if(@($e).Count){$e|ConvertTo-Json;exit 1}\n',encoding='ascii')
    for name,mutant,fixture in cases:
        path=root/(name+'.ps1'); path.write_text(mutant,encoding='utf-8')
        parsed=subprocess.run([host,'-NoProfile','-File',str(parser),'-SourceFile',str(path)],capture_output=True,text=True,env=native_env)
        if parsed.returncode: raise RuntimeError('Invalid mutant syntax: '+name+parsed.stdout+parsed.stderr)
        command=[host,'-NoProfile','-File',str(tests/fixture),'-SourceFile',str(path)]
        if fixture=='install-entry.ps1': command+=['-Scenario','cached']
        run=subprocess.run(command,capture_output=True,text=True,timeout=30,env=native_env)
        receipt=root/(name+'.txt'); receipt.write_text(run.stdout+run.stderr,encoding='utf-8')
        # Every valid mutant must reach the fixture's structured behavioral result.
        reached='"results"' in run.stdout or '"snapshotUnchanged"' in run.stdout
        results.append(dict(case=name,syntaxExit=parsed.returncode,fixtureExit=run.returncode,detected=run.returncode!=0 and reached,mutant=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),receipt=str(receipt)))

print(json.dumps(dict(source=hashlib.sha256(source.read_bytes()).hexdigest(),fixture=str(root),results=results),indent=2))
sys.exit(1 if any(not r['detected'] for r in results) else 0)
