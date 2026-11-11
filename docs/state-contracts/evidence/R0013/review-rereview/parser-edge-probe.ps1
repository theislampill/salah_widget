param([string]$SourceFile,[string]$FixtureRoot)
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($SourceFile,[ref]$tokens,[ref]$errors)
if(@($errors).Count){throw 'Source parser failure'}
foreach($def in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true)){. ([scriptblock]::Create($def.Extent.Text))}
function Write-Warn([string]$Text){}
$utf8=New-Object Text.UTF8Encoding $false
$rows=@()
foreach($case in @(
 @('healthy-empty','{"addons":[]}'),
 @('trailing-comma','{"addons":[],}'),
 @('comment-after-root','{"addons":[]} /* trailing comment */'),
 @('comment-in-root','{/* comment */ "addons":[]}'),
 @('single-quoted-property',"{'addons':[]}"),
 @('unquoted-property','{addons:[]}'),
 @('duplicate-inventory','{"addons":[{"name":"Tabliss"}],"addons":[]}'),
 @('root-array-singleton','[{"addons":[]}]'),
 @('unsupported-version','{"schemaVersion":999999,"addons":[]}')
)){
 $profile=Join-Path $FixtureRoot $case[0]
 $null=[IO.Directory]::CreateDirectory($profile)
 [IO.File]::WriteAllText((Join-Path $profile 'extensions.json'),$case[1],$utf8)
 $r=Get-FirefoxExtensionStatus $profile
 $t=[pscustomobject]@{HasLegacyTabliss=$r.HasOld;DiscoveryStatus=$r.Status}
 $rows+=,[pscustomobject]@{case=$case[0];input=$case[1];status=$r.Status;reason=$r.Reason;eligible=(Get-DiscoveryEligibility $t);source=$r.MetadataSource}
}
[pscustomobject]@{reviewer='/root/r0013_review';host=$PSVersionTable.PSVersion.ToString();platform=[Environment]::OSVersion.Platform.ToString();sourceHash=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant();results=$rows}|ConvertTo-Json -Depth 6
