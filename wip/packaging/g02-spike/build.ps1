#Requires -Version 5.1
# R2B G02：rhproj → rhp → 刪自動 RUI → 複製產品 RUI／圖示 → yak
$ErrorActionPreference = "Stop"

$Spike = $PSScriptRoot
$RepoRoot = (Resolve-Path (Join-Path $Spike "..\..\..")).Path
$Toolbar = Join-Path $RepoRoot "wip\docs\toolbar"
$Rhproj = Join-Path $Spike "loopflow-rhino-to-blender-sync.rhproj"
$RhinoCode = "C:\Program Files\Rhino 8\System\RhinoCode.exe"
$Yak = "C:\Program Files\Rhino 8\System\yak.exe"

if (-not (Test-Path -LiteralPath $Rhproj)) {
    Write-Host "缺少 $Rhproj"
    Write-Host "請在 Rhino Script Editor 新增專案後另存成這個檔名。步驟見 README.md。"
    exit 1
}
if (-not (Test-Path -LiteralPath $RhinoCode)) {
    Write-Host "找不到 RhinoCode.exe：$RhinoCode"
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

$ProductRui = Get-ChildItem -LiteralPath $Toolbar -Filter "*.rui" -File -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -ne $ProductRui) {
    $DestRui = Join-Path $Spike $ProductRui.Name
    Copy-Item -LiteralPath $ProductRui.FullName -Destination $DestRui -Force
    Write-Host "Copied product RUI $($ProductRui.Name)"
} else {
    Write-Host "No product RUI in wip/docs/toolbar yet; yak will have commands only."
}

$Icon = Join-Path $Toolbar "icon.png"
if (Test-Path -LiteralPath $Icon) {
    Copy-Item -LiteralPath $Icon -Destination (Join-Path $Spike "icon.png") -Force
    Write-Host "Copied icon.png"
}

if (-not (Test-Path -LiteralPath $Yak)) {
    Write-Host "找不到 yak.exe：$Yak"
    exit 1
}

Push-Location $Spike
try {
    & $Yak build
    if ($LASTEXITCODE -ne 0) {
        throw "yak build failed: $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

Write-Host "Done. Install the .yak locally, then fully quit Rhino before testing."
