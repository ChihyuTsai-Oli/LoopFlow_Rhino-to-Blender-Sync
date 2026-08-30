#Requires -Version 5.1
# Pack LoopFlow ToolBox as a traditional Blender add-on zip (not yak).
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$AddonSrc = Join-Path $RepoRoot "wip\src\blender\loopflow_toolbox"
$OutDir = Join-Path $RepoRoot "wip\packaging\toolbox\build"
$ZipName = "loopflow_toolbox-1.0.0.zip"
$InnerName = "loopflow_toolbox"

if (-not (Test-Path -LiteralPath $AddonSrc)) {
    throw "Missing ToolBox add-on: $AddonSrc"
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$ZipTmp = Join-Path $env:TEMP "r2b-toolbox-addon-zip"
if (Test-Path -LiteralPath $ZipTmp) {
    Remove-Item -LiteralPath $ZipTmp -Recurse -Force
}
$ZipInner = Join-Path $ZipTmp $InnerName
New-Item -ItemType Directory -Path $ZipInner | Out-Null

& robocopy $AddonSrc $ZipInner /E /XD __pycache__ /XF *.pyc blender_manifest.toml /NFL /NDL /NJH /NJS /nc /ns | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "robocopy zip staging failed: $LASTEXITCODE"
}
$LASTEXITCODE = 0

$ZipOut = Join-Path $OutDir $ZipName
if (Test-Path -LiteralPath $ZipOut) {
    Remove-Item -LiteralPath $ZipOut -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($ZipTmp, $ZipOut)
Remove-Item -LiteralPath $ZipTmp -Recurse -Force

Write-Host "Packed:"
Write-Host "  $ZipOut"
Write-Host "Install in Blender: Edit > Preferences > Add-ons > Install from Disk"
Write-Host "Do not add this zip to the Rhino yak."
