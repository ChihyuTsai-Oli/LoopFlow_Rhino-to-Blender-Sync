#Requires -Version 5.1
# Link R2B dev Sync add-on (Git wip) into Portable Blender via directory junction.
# Source of truth stays in the repo; do not develop inside portable\ as the primary copy.
$ErrorActionPreference = "Stop"

$BlenderRoot = "C:\blender-5.2.1_wip"
$AddonName = "loopflow_r2b_sync_dev"
$RepoAddon = (Resolve-Path (Join-Path $PSScriptRoot "..\src\blender\$AddonName")).Path
$AddonsDir = Join-Path $BlenderRoot "portable\scripts\addons"
$LinkPath = Join-Path $AddonsDir $AddonName

$BlenderExe = Join-Path $BlenderRoot "blender.exe"
if (-not (Test-Path -LiteralPath $BlenderExe)) {
    throw "blender.exe not found at $BlenderExe. Install Portable 5.2.1 there first."
}

if (-not (Test-Path -LiteralPath $RepoAddon)) {
    throw "Repo add-on not found: $RepoAddon"
}

New-Item -ItemType Directory -Force -Path $AddonsDir | Out-Null

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
    if ($resolvedTarget -and ($resolvedTarget -ieq $RepoAddon)) {
        Write-Host "OK: junction already points to $RepoAddon"
        exit 0
    }
    Write-Host "Removing old junction: $LinkPath"
    Remove-Item -LiteralPath $LinkPath -Force
}

New-Item -ItemType Junction -Path $LinkPath -Target $RepoAddon | Out-Null
Write-Host "Created junction:"
Write-Host "  $LinkPath"
Write-Host "  -> $RepoAddon"
Write-Host "Open $BlenderExe, enable Add-on: LoopFlow R2B Sync (Dev Stub)."
