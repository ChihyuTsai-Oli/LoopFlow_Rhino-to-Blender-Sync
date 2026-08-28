#Requires -Version 5.1
# Link R2B dev Sync add-on + import_3dm 0.0.18 into Portable Blender via directory junctions.
# Source of truth stays in the repo; do not develop inside portable\ as the primary copy.
$ErrorActionPreference = "Stop"

$BlenderRoot = "E:\blender-5.2.1_wip"
$AddonsDir = Join-Path $BlenderRoot "portable\scripts\addons"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

$BlenderExe = Join-Path $BlenderRoot "blender.exe"
if (-not (Test-Path -LiteralPath $BlenderExe)) {
    throw "blender.exe not found at $BlenderExe. Install Portable 5.2.1 there first."
}

New-Item -ItemType Directory -Force -Path $AddonsDir | Out-Null

function Set-AddonJunction {
    param(
        [Parameter(Mandatory = $true)][string]$LinkName,
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [Parameter(Mandatory = $true)][string]$EnableHint
    )

    if (-not (Test-Path -LiteralPath $TargetPath)) {
        throw "Target not found: $TargetPath"
    }

    $LinkPath = Join-Path $AddonsDir $LinkName
    if (Test-Path -LiteralPath $LinkPath) {
        $item = Get-Item -LiteralPath $LinkPath -Force
        $isReparse = [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
        if (-not $isReparse) {
            throw "Path exists and is not a junction (remove manually then re-run): $LinkPath"
        }
        $target = $item.Target
        if ($target -is [System.Array]) {
            $target = $target[0]
        }
        $resolvedTarget = $null
        if ($target) {
            try {
                $resolvedTarget = (Resolve-Path -LiteralPath $target).Path
            }
            catch {
                $resolvedTarget = $null
            }
        }
        if ($resolvedTarget -and ($resolvedTarget -ieq $TargetPath)) {
            Write-Host "OK: $LinkName -> $TargetPath"
            return
        }
        Write-Host "Removing old junction: $LinkPath"
        Remove-Item -LiteralPath $LinkPath -Force
    }

    New-Item -ItemType Junction -Path $LinkPath -Target $TargetPath | Out-Null
    Write-Host "Created junction:"
    Write-Host "  $LinkPath"
    Write-Host "  -> $TargetPath"
    Write-Host "  Enable: $EnableHint"
}

$SyncName = "loopflow_r2b_sync_dev"
$SyncTarget = Join-Path $RepoRoot "wip\src\blender\$SyncName"
Set-AddonJunction -LinkName $SyncName -TargetPath $SyncTarget -EnableHint "LoopFlow R2B Sync (Dev Stub)"

$ImportName = "import_3dm"
$ImportTarget = Join-Path $RepoRoot "import_3dm\import_3dm-0.0.18-windows_x64"
Set-AddonJunction -LinkName $ImportName -TargetPath $ImportTarget -EnableHint "Import Rhinoceros 3D"

Write-Host ""
Write-Host "Open $BlenderExe"
Write-Host "Preferences > Add-ons: enable both:"
Write-Host "  - LoopFlow R2B Sync (Dev Stub)"
Write-Host "  - Import Rhinoceros 3D"
