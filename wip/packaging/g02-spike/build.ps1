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

$ProductRui = Get-ChildItem -LiteralPath $Toolbar -Filter "*.rui" -File -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -ne $ProductRui) {
    Copy-Item -LiteralPath $ProductRui.FullName -Destination (Join-Path $Stage $ProductRui.Name) -Force
    Write-Host "Staged product RUI $($ProductRui.Name)"
} else {
    Write-Host "No product RUI in wip/docs/toolbar yet; yak will have commands only."
}

$Icon = Join-Path $Toolbar "icon.png"
if (Test-Path -LiteralPath $Icon) {
    Copy-Item -LiteralPath $Icon -Destination (Join-Path $Stage "icon.png") -Force
    Write-Host "Staged icon.png"
}

Get-ChildItem -LiteralPath (Join-Path $Spike "build\rh8") -Filter "*.rhp" -File -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $Stage $_.Name) -Force
    Write-Host "Staged $($_.Name)"
}

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
