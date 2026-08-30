#Requires -Version 5.1
# Link R2B dev Sync add-on into Portable Blender via directory junction.
# import_3dm is embedded inside Sync (with rhino3dm wheels); no separate addon needed.
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
Set-AddonJunction -LinkName $SyncName -TargetPath $SyncTarget -EnableHint "LoopFlow Rhino to Blender Sync"

# Remove legacy standalone import_3dm junction (embedded in Sync now)
$LegacyImport = Join-Path $AddonsDir "import_3dm"
if (Test-Path -LiteralPath $LegacyImport) {
    $item = Get-Item -LiteralPath $LegacyImport -Force
    $isReparse = [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
    if ($isReparse) {
        Write-Host "Removing legacy import_3dm junction: $LegacyImport"
        cmd /c "rmdir `"$LegacyImport`""
        if (Test-Path -LiteralPath $LegacyImport) {
            Write-Host "WARNING: could not remove $LegacyImport ; delete it manually."
        }
    }
    else {
        Write-Host "WARNING: $LegacyImport exists and is not a junction; leave untouched."
    }
}

Write-Host ""
Write-Host "Open $BlenderExe"
Write-Host "Preferences > Add-ons: enable LoopFlow Rhino to Blender Sync only."
Write-Host "Models Import/Update embeds import_3dm + rhino3dm; no separate Import Rhinoceros 3D needed."
