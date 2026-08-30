#Requires -Version 5.1
# R2B G02: rhproj -> rhp -> drop auto RUI -> stage product files -> yak
$ErrorActionPreference = "Stop"

$Spike = $PSScriptRoot
$RepoRoot = (Resolve-Path (Join-Path $Spike "..\..\..")).Path
$Toolbar = Join-Path $RepoRoot "wip\docs\toolbar"
$Rhproj = Join-Path $Spike "loopflow-rhino-to-blender-sync.rhproj"
$RhinoCode = "C:\Program Files\Rhino 8\System\RhinoCode.exe"
$Yak = "C:\Program Files\Rhino 8\System\yak.exe"

if (-not (Test-Path -LiteralPath $Rhproj)) {
    Write-Host "Missing $Rhproj"
    Write-Host "Save the Script Editor project as this filename. See README.md."
    exit 1
}
if (-not (Test-Path -LiteralPath $RhinoCode)) {
    Write-Host "RhinoCode.exe not found: $RhinoCode"
    exit 1
}

Write-Host "Building $Rhproj"
& $RhinoCode project build $Rhproj
if ($LASTEXITCODE -ne 0) {
    throw "RhinoCode project build failed: $LASTEXITCODE"
}

Get-ChildItem -LiteralPath $Spike -Filter "*.rui" -File -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Removing auto-generated RUI $($_.Name)"
    Remove-Item -LiteralPath $_.FullName -Force
}

$AutoRuiDir = Join-Path $Spike "build\rh8"
if (Test-Path -LiteralPath $AutoRuiDir) {
    Get-ChildItem -LiteralPath $AutoRuiDir -Filter "*.rui" -File -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "Removing auto-generated RUI $($_.Name)"
        Remove-Item -LiteralPath $_.FullName -Force
    }
}

$Stage = Join-Path $Spike "build\yak-stage"
if (Test-Path -LiteralPath $Stage) {
    Remove-Item -LiteralPath $Stage -Recurse -Force
}
New-Item -ItemType Directory -Path $Stage | Out-Null
Copy-Item -LiteralPath (Join-Path $Spike "manifest.yml") -Destination (Join-Path $Stage "manifest.yml")

$Icon = Join-Path $Toolbar "icon.png"
if (Test-Path -LiteralPath $Icon) {
    Copy-Item -LiteralPath $Icon -Destination (Join-Path $Stage "icon.png") -Force
    Write-Host "Staged icon.png"
}

$StagedRhp = Get-ChildItem -LiteralPath (Join-Path $Spike "build\rh8") -Filter "*.rhp" -File -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $StagedRhp) {
    throw "RhinoCode did not produce an .rhp"
}
Copy-Item -LiteralPath $StagedRhp.FullName -Destination (Join-Path $Stage $StagedRhp.Name) -Force
Write-Host "Staged $($StagedRhp.Name)"

$ProductRui = Get-ChildItem -LiteralPath $Toolbar -Filter "*.rui" -File -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -ne $ProductRui) {
    # Rhino 只自動載入與 .rhp 同名的 .rui（出圖 LoopFlow.rhp／LoopFlow.rui）
    $RuiName = $StagedRhp.BaseName + ".rui"
    Copy-Item -LiteralPath $ProductRui.FullName -Destination (Join-Path $Stage $RuiName) -Force
    Write-Host "Staged product RUI $RuiName (matches rhp)"
} else {
    Write-Host "No product RUI in wip/docs/toolbar yet; yak will have commands only."
}

$Templates = Join-Path $Stage "templates"
New-Item -ItemType Directory -Force -Path $Templates | Out-Null
$AddonSrc = Join-Path $RepoRoot "wip\src\blender\loopflow_r2b_sync_dev"
if (-not (Test-Path -LiteralPath $AddonSrc)) {
    throw "Missing Blender add-on: $AddonSrc"
}
# zip 內層必須與 blender_manifest.toml 的 id 相同；不打 _vendor（.pyd 會讓 Windows／Dropbox 改名失敗）
$ZipTmp = Join-Path $env:TEMP "r2b-yak-addon-zip"
if (Test-Path -LiteralPath $ZipTmp) {
    Remove-Item -LiteralPath $ZipTmp -Recurse -Force
}
$ZipInner = Join-Path $ZipTmp "loopflow_r2b_sync"
New-Item -ItemType Directory -Path $ZipInner | Out-Null
& robocopy $AddonSrc $ZipInner /E /XD __pycache__ _vendor /XF *.pyc /NFL /NDL /NJH /NJS /nc /ns | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "robocopy zip staging failed: $LASTEXITCODE"
}
$LASTEXITCODE = 0
$ZipOut = Join-Path $Templates "loopflow_r2b_sync.zip"
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path -LiteralPath $ZipOut) {
    Remove-Item -LiteralPath $ZipOut -Force
}
[System.IO.Compression.ZipFile]::CreateFromDirectory($ZipTmp, $ZipOut)
Set-Content -LiteralPath (Join-Path $Templates ".loopflow_yak_version") -Value "0.1.4" -Encoding ascii -NoNewline
Write-Host "Staged Blender add-on zip"

if (-not (Test-Path -LiteralPath $Yak)) {
    Write-Host "yak.exe not found: $Yak"
    exit 1
}

Get-ChildItem -LiteralPath $Spike -Filter "*.yak" -File -ErrorAction SilentlyContinue | Remove-Item -Force

Push-Location $Stage
try {
    & $Yak build
    if ($LASTEXITCODE -ne 0) {
        throw "yak build failed: $LASTEXITCODE"
    }
    Get-ChildItem -LiteralPath $Stage -Filter "*.yak" -File | ForEach-Object {
        $DestYak = Join-Path $Spike $_.Name
        Copy-Item -LiteralPath $_.FullName -Destination $DestYak -Force
        Write-Host "Wrote $DestYak"
    }
} finally {
    Pop-Location
}

Write-Host "Done. Install the .yak locally, then fully quit Rhino before testing."
