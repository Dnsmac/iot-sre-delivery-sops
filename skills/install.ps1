#Requires -Version 5.1
<#
.SYNOPSIS
  安装 BS / BSP / BUC Skills 到 Cursor（用户级 + 可选项目级）

.EXAMPLE
  .\install.ps1
  .\install.ps1 -Force
  .\install.ps1 -ProjectRoot "D:\gerrit\iot-server"
#>
param(
    [switch]$Force,
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
$SourceRoot = $PSScriptRoot

$SkillIds = @(
    "bsp-orchestrator",
    "buc-orchestrator",
    "code-review",
    "coder",
    "bsp-large-system"
)

$CommandFiles = @(
    "bs.md",
    "bsp.md",
    "buc.md",
    "code-review.md",
    "coder.md"
)

function Install-SkillsToTarget {
    param(
        [string]$SkillsRoot,
        [string]$CommandsRoot,
        [bool]$Overwrite
    )

    foreach ($id in $SkillIds) {
        $skillSrc  = Join-Path $SourceRoot "$id\SKILL.md"
        $skillDest = Join-Path $SkillsRoot $id
        $skillFile = Join-Path $skillDest "SKILL.md"

        if (-not (Test-Path $skillSrc)) { throw "Missing: $skillSrc" }

        New-Item -ItemType Directory -Force -Path $skillDest | Out-Null

        if ($Overwrite -or -not (Test-Path $skillFile)) {
            Copy-Item -Force $skillSrc $skillFile
            Write-Host "[OK] Skill -> $skillFile"
        } else {
            Write-Host "[SKIP] Skill exists (use -Force): $skillFile"
        }
    }

    New-Item -ItemType Directory -Force -Path $CommandsRoot | Out-Null

    foreach ($cmd in $CommandFiles) {
        $cmdSrc  = Join-Path $SourceRoot "commands\$cmd"
        $cmdDest = Join-Path $CommandsRoot $cmd

        if (-not (Test-Path $cmdSrc)) { throw "Missing: $cmdSrc" }

        if ($Overwrite -or -not (Test-Path $cmdDest)) {
            Copy-Item -Force $cmdSrc $cmdDest
            Write-Host "[OK] Command -> $cmdDest"
        } else {
            Write-Host "[SKIP] Command exists (use -Force): $cmdDest"
        }
    }
}

Write-Host "BS/BSP/BUC Skills install from: $SourceRoot"
Write-Host ""

$userSkills   = Join-Path $env:USERPROFILE ".cursor\skills"
$userCommands = Join-Path $env:USERPROFILE ".cursor\commands"
Install-SkillsToTarget -SkillsRoot $userSkills -CommandsRoot $userCommands -Overwrite:$Force

if ($ProjectRoot -ne "") {
    if (-not (Test-Path $ProjectRoot)) { throw "ProjectRoot not found: $ProjectRoot" }
    $projSkills   = Join-Path $ProjectRoot ".cursor\skills"
    $projCommands = Join-Path $ProjectRoot ".cursor\commands"
    Write-Host ""
    Write-Host "Project install: $ProjectRoot"
    Install-SkillsToTarget -SkillsRoot $projSkills -CommandsRoot $projCommands -Overwrite:$Force
}

Write-Host ""
Write-Host "Done. Restart Cursor (or new Agent session)."
Write-Host "Shortcuts: /bs  /bsp  /buc  /code-review  /coder"
Write-Host "Docs: $SourceRoot\QUICKSTART.md"
