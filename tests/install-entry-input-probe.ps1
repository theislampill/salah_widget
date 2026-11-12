# NEW definition-only child read probe. No installer source is evaluated.
# The receiver pins the complete source and this probe before interpreting it.
function Invoke-R0016EntryInputProbe {
    param([string]$SourcePath,[string]$SourceSha256,[string]$ProbePath,[string]$ProofPath,
          [string]$Phase,[string]$Nonce,[string]$ExpectedHost)
    $ErrorActionPreference='Stop'
    if([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT){throw 'Input probe requires native Windows'}
    if($Phase -cnotin @('direct-pre-discovery','held-module-startup','held-before-source')){throw 'Unknown input probe phase'}
    if($Nonce -cnotmatch '^[0-9a-f]{32}$'){throw 'Invalid input probe nonce'}
    $factCache=@{}
    function Get-R0016ProbeFileFact([string]$Path) {
        $full=[IO.Path]::GetFullPath($Path)
        if($factCache.ContainsKey($full)){return $factCache[$full]}
        $info=[IO.FileInfo]::new($full);$info.Refresh()
        if(-not $info.Exists -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Probe fact requires an existing non-reparse file'}
        $stamp=$info.LastWriteTimeUtc.Ticks;$length=$info.Length
        $bytes=[IO.File]::ReadAllBytes($full);$hasher=[Security.Cryptography.SHA256]::Create()
        try{$hash=([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
        $info.Refresh()
        if($info.Length -ne $length -or $info.LastWriteTimeUtc.Ticks -ne $stamp -or $bytes.Length -ne $length){throw 'Probe input changed during readback'}
        $value=[pscustomobject]@{path=$full;bytes=$bytes.Length;sha256=$hash}
        $factCache[$full]=$value
        return $value
    }
    function Get-R0016ProbeTextFact($Text) {
        if($null -eq $Text){return $null}
        $bytes=[Text.Encoding]::UTF8.GetBytes([string]$Text);$hasher=[Security.Cryptography.SHA256]::Create()
        try{$hash=([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
        return [pscustomobject]@{type=$Text.GetType().FullName;utf8Bytes=$bytes.Length;sha256=$hash}
    }
    function Get-R0016ProbeError($ErrorRecord) {
        $cause=$ErrorRecord.Exception.GetBaseException()
        return [pscustomobject]@{exceptionType=$cause.GetType().FullName;nativeCode=($cause.HResult -band 65535);
            errorId=[string]$ErrorRecord.FullyQualifiedErrorId;category=[string]$ErrorRecord.CategoryInfo.Category;message=$cause.Message}
    }
    $sourceFact=Get-R0016ProbeFileFact $SourcePath
    if($sourceFact.sha256 -cne $SourceSha256){throw 'Input probe source digest mismatch'}
    $probeFact=Get-R0016ProbeFileFact $ProbePath
    $hostPath=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    $subject=[IO.Path]::GetFullPath($env:INSTALL_SUBJECT_ROOT)
    $controlRoot=[IO.Path]::Combine([IO.DirectoryInfo]::new($subject).Parent.FullName,'control')+[IO.Path]::DirectorySeparatorChar
    if(-not ([IO.Path]::GetFullPath($ProofPath)).StartsWith($controlRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'Input proof output escaped owned control root'}
    $probeError=$null;$envRows=New-Object 'System.Collections.Generic.List[object]'
    $commands=New-Object 'System.Collections.Generic.List[object]'
    $queries=New-Object 'System.Collections.Generic.List[object]'
    $providerFact=$null;$sid=$null
    try {
    $expectedRoots=@{LOCALAPPDATA=(Join-Path $subject 'local');APPDATA=(Join-Path $subject 'roam');ProgramFiles=(Join-Path $subject 'pf');'ProgramFiles(x86)'=(Join-Path $subject 'pf86')}
    foreach($key in $expectedRoots.Keys){
        if([Environment]::GetEnvironmentVariable($key,'Process') -cne $expectedRoots[$key]){throw ('Probe discovery environment escaped exact owned root: '+$key)}
    }
    $allEnvironment=[Environment]::GetEnvironmentVariables('Process')
    foreach($key in @('SALAH_WIDGET_PRESET_URL','SALAH_WIDGET_HASH','SALAH_INSTALL_SOURCE','TABLISSNG_REPO',
        'LOCALAPPDATA','APPDATA','ProgramFiles','ProgramFiles(x86)','HOME','USERPROFILE','TEMP','TMP','PSModulePath','PSModuleAnalysisCachePath')){
        $matches=@($allEnvironment.Keys|Where-Object{[string]$_ -ieq $key})
        if($matches.Count -gt 1){throw 'Ambiguous child environment key'}
        [void]$envRows.Add([pscustomobject]@{name=$key;present=($matches.Count -eq 1);value=[Environment]::GetEnvironmentVariable($key,'Process')})
    }
    foreach($name in @('Test-Path','Get-ChildItem','Get-Content','ConvertFrom-Json')){
        $command=@(Get-Command -Name $name -ErrorAction Stop)
        if($command.Count -ne 1 -or $command[0].CommandType -ne [Management.Automation.CommandTypes]::Cmdlet){throw ('Unexpected source-read command binding: '+$name)}
        $command=$command[0]
        if(-not $command.Module -or -not $command.ImplementingType){throw 'Missing native read command/module identity'}
        [void]$commands.Add([pscustomobject]@{name=$name;commandType=[string]$command.CommandType;source=[string]$command.Source;
            definition=[string]$command.Definition;implementingType=$command.ImplementingType.FullName;
            moduleVersion=$command.Module.Version.ToString();module=(Get-R0016ProbeFileFact $command.Module.Path);
            assembly=(Get-R0016ProbeFileFact $command.ImplementingType.Assembly.Location)})
    }
    $providers=@(Get-PSProvider -PSProvider FileSystem -ErrorAction Stop)
    if($providers.Count -ne 1){throw 'Ambiguous FileSystem provider'}
    $provider=$providers[0]
    $providerFact=[pscustomobject]@{name=$provider.Name;implementingType=$provider.ImplementingType.FullName;
        capabilities=[string]$provider.Capabilities;assembly=(Get-R0016ProbeFileFact $provider.ImplementingType.Assembly.Location)}
    function Test-R0016ProbePath([string]$Id,[string]$Path) {
        $result=$false;$errorValue=$null
        try{$result=Microsoft.PowerShell.Management\Test-Path -LiteralPath $Path -ErrorAction Stop}
        catch{$errorValue=Get-R0016ProbeError $_}
        [void]$queries.Add([pscustomobject]@{id=$Id;operation='Test-Path';path=$Path;success=($null -eq $errorValue);exists=[bool]$result;error=$errorValue})
        if($errorValue){throw ('Input path query failed: '+$Id)}
        return [bool]$result
    }
    function Read-R0016ProbeMetadata([string]$Id,[string]$Path,[string]$Mode) {
        $value=$null;$errorValue=$null;$byteFact=$null;$parseError=$null;$parseSucceeded=$false
        try{
            if($Mode -ceq 'strict-utf8'){
                $decoder=New-Object System.Text.UTF8Encoding -ArgumentList $false,$true
                $value=[IO.File]::ReadAllText($Path,$decoder)
            } else {$value=Microsoft.PowerShell.Management\Get-Content -Raw -LiteralPath $Path -ErrorAction Stop}
            $byteFact=Get-R0016ProbeFileFact $Path
            try{$null=ConvertFrom-Json -InputObject $value -ErrorAction Stop;$parseSucceeded=$true}
            catch{$parseError=Get-R0016ProbeError $_}
        } catch {$errorValue=Get-R0016ProbeError $_}
        [void]$queries.Add([pscustomobject]@{id=$Id;operation='metadata-read';path=$Path;mode=$Mode;
            success=($null -eq $errorValue);bytes=$byteFact;text=(Get-R0016ProbeTextFact $value);error=$errorValue;
            nativeJsonParseSucceeded=$parseSucceeded;nativeJsonParseError=$parseError})
    }
    $configs=@(
        @('chrome','chromium','LOCALAPPDATA','Google\Chrome\User Data','Google\Chrome\Application\chrome.exe',@('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA')),
        @('edge','chromium','LOCALAPPDATA','Microsoft\Edge\User Data','Microsoft\Edge\Application\msedge.exe',@('ProgramFiles(x86)','ProgramFiles','LOCALAPPDATA')),
        @('brave','chromium','LOCALAPPDATA','BraveSoftware\Brave-Browser\User Data','BraveSoftware\Brave-Browser\Application\brave.exe',@('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA')),
        @('chromium','chromium','LOCALAPPDATA','Chromium\User Data','Chromium\Application\chrome.exe',@('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA')),
        @('firefox','firefox','APPDATA','Mozilla\Firefox\Profiles','Mozilla Firefox\firefox.exe',@('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA')),
        @('librewolf','firefox','APPDATA','LibreWolf\Profiles','LibreWolf\librewolf.exe',@('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA'))
    )
    foreach($config in $configs){
        $key=[string]$config[0];$family=[string]$config[1]
        $userData=Join-Path ([Environment]::GetEnvironmentVariable($config[2],'Process')) $config[3]
        $index=0
        foreach($variable in $config[5]){
            $path=Join-Path ([Environment]::GetEnvironmentVariable($variable,'Process')) $config[4]
            if(Test-R0016ProbePath ($key+'/exe/'+$index) $path){break}
            $index++
        }
        if(-not (Test-R0016ProbePath ($key+'/user-data') $userData)){continue}
        $enumerationErrors=@()
        $directories=@(Microsoft.PowerShell.Management\Get-ChildItem -LiteralPath $userData -Directory -ErrorAction SilentlyContinue -ErrorVariable +enumerationErrors)
        $entryRows=@($directories|ForEach-Object{[pscustomobject]@{name=$_.Name;path=$_.FullName;kind='directory';attributes=[int]$_.Attributes}})
        $errors=@($enumerationErrors|ForEach-Object{Get-R0016ProbeError $_})
        [void]$queries.Add([pscustomobject]@{id=$key+'/profiles';operation='enumerate-directories';path=$userData;
            entries=$entryRows;success=($errors.Count -eq 0);errors=$errors;sourceErrorAction='SilentlyContinue'})
        if($errors.Count){throw 'Source profile enumeration had an error; input association is not proved'}
        $profileIndex=0
        foreach($directory in $directories){
            $base=$key+'/profile/'+$profileIndex;$profileIndex++
            $preferences=Join-Path $directory.FullName 'Preferences'
            if($family -ceq 'chromium'){
                $selected=($directory.Name -eq 'Default' -or $directory.Name -match '^Profile \d+$')
                if(-not $selected){$selected=Test-R0016ProbePath ($base+'/selection-preferences') $preferences}
                if(-not $selected){continue}
                $newIds=if($key -ceq 'edge'){@('mkaphhbkcccpgkfaifhhdfckagnkcmhm','dlaogejjiafeobgofajdlkkhjlignalk')}else{@('dlaogejjiafeobgofajdlkkhjlignalk')}
                $oldIds=if($key -ceq 'edge'){@('lklaendlmlfkaabeleddanafeinnenih','hipekcciheckooncpjeljhnekcoolahp')}else{@('hipekcciheckooncpjeljhnekcoolahp')}
                foreach($id in @($newIds)+@($oldIds)){
                    $null=Test-R0016ProbePath ($base+'/extension/'+$id) (Join-Path (Join-Path $directory.FullName 'Extensions') $id)
                }
                if(Test-R0016ProbePath ($base+'/preferences') $preferences){Read-R0016ProbeMetadata ($base+'/preferences-read') $preferences 'native-get-content'}
            } else {
                $metadata=Join-Path $directory.FullName 'extensions.json'
                if(Test-R0016ProbePath ($base+'/extensions-json') $metadata){Read-R0016ProbeMetadata ($base+'/extensions-read') $metadata 'strict-utf8'}
            }
        }
    }
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
    try{$sid=$identity.User.Value}finally{$identity.Dispose()}
    } catch {$probeError=Get-R0016ProbeError $_}
    $value=[ordered]@{schema='r0016-entry-child-input-proof.v1';phase=$Phase;pid=$PID;nonce=$Nonce;nativeWindows=$true;
        expectedHost=$ExpectedHost;commandHost=$hostPath;hostVersion=$PSVersionTable.PSVersion.ToString();hostEdition=$PSVersionTable.PSEdition;
        source=$sourceFact;probe=$probeFact;subject=$subject;identitySid=$sid;
        culture=[Globalization.CultureInfo]::CurrentCulture.Name;uiCulture=[Globalization.CultureInfo]::CurrentUICulture.Name;defaultCodePage=[Text.Encoding]::Default.CodePage;
        environment=$envRows.ToArray();commands=$commands.ToArray();provider=$providerFact;queries=$queries.ToArray();complete=($null -eq $probeError);error=$probeError;
        scope='Source-bound read probe only. No installer execution or product acceptance is asserted by this proof.'}
    if([IO.File]::Exists($ProofPath) -or [IO.File]::Exists($ProofPath+'.partial')){throw 'Input proof path already occupied'}
    [IO.File]::WriteAllText($ProofPath+'.partial',($value|ConvertTo-Json -Depth 30),(New-Object Text.UTF8Encoding $false))
    [IO.File]::Move($ProofPath+'.partial',$ProofPath)
    if($probeError){throw ('Input probe incomplete: '+$probeError.exceptionType+' '+$probeError.message)}
}
