#Requires -Version 5.1
# Link R2B ToolBox add-on into Portable Blender via directory junction.
# Independent from Sync; does not copy into yak templates.
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

$Name = "loopflow_toolbox"
$Target = Join-Path $RepoRoot "wip\src\blender\$Name"
Set-AddonJunction -LinkName $Name -TargetPath $Target -EnableHint "LoopFlow ToolBox"

Write-Host ""
Write-Host "Open $BlenderExe"
Write-Host "Preferences > Add-ons: enable LoopFlow ToolBox."
Write-Host "N-panel: LoopFlow > ToolBox. This add-on is not in the Rhino yak."
