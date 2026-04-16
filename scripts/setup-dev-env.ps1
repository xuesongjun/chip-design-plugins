#Requires -Version 5.1
<#
.SYNOPSIS
    Windows Claude Code 芯片开发环境自动配置脚本

.DESCRIPTION
    自动完成以下配置：
    1. 检测并安装 MSYS2（如未安装）
    2. 通过 pacman 安装必要工具（verilator）
    3. 将 MSYS2 路径加入 Windows 用户 PATH
    4. 配置 Claude Code settings.json（切换 bash 为 MSYS2）
    5. 创建 ~/.bashrc

    脚本具备幂等性：重复执行不会破坏已有配置。

.PARAMETER Msys2Path
    MSYS2 安装路径，默认为 C:\msys64

.PARAMETER SkipMsys2Install
    跳过 MSYS2 安装（已手动安装时使用）

.PARAMETER SkipPackages
    跳过 pacman 包安装

.PARAMETER SkipClaudeConfig
    跳过 Claude Code settings.json 配置

.EXAMPLE
    .\setup-dev-env.ps1
    .\setup-dev-env.ps1 -SkipMsys2Install -SkipPackages
    .\setup-dev-env.ps1 -Msys2Path "D:\msys64"
#>

[CmdletBinding()]
param(
    [string]$Msys2Path = "C:\msys64",
    [switch]$SkipMsys2Install,
    [switch]$SkipPackages,
    [switch]$SkipClaudeConfig
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step { param([string]$Message); Write-Host "`n▶ $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message); Write-Host "  ✓ $Message" -ForegroundColor Green }
function Write-Skipped { param([string]$Message); Write-Host "  - $Message (已跳过)" -ForegroundColor DarkGray }
function Write-Warning2 { param([string]$Message); Write-Host "  ! $Message" -ForegroundColor Yellow }
function Write-Fail { param([string]$Message); Write-Host "  ✗ $Message" -ForegroundColor Red }

function Install-Msys2 {
    Write-Step "检测 MSYS2"
    $bashExe = Join-Path $Msys2Path "usr\bin\bash.exe"

    if (Test-Path $bashExe) {
        Write-Success "MSYS2 已安装：$Msys2Path"
        return
    }

    if ($SkipMsys2Install) {
        Write-Fail "MSYS2 未找到（路径：$Msys2Path），且指定了 -SkipMsys2Install"
        throw "请先安装 MSYS2 后重试，或通过 -Msys2Path 指定正确路径"
    }

    Write-Host "  MSYS2 未安装，正在通过 winget 安装..." -ForegroundColor Yellow

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Fail "winget 不可用"
        Write-Host "  请手动从 https://www.msys2.org/ 下载安装到 $Msys2Path" -ForegroundColor Yellow
        throw "缺少 winget，无法自动安装 MSYS2"
    }

    winget install --id MSYS2.MSYS2 --location $Msys2Path --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "winget 安装 MSYS2 失败（退出码：$LASTEXITCODE）" }

    $timeout = 60; $elapsed = 0
    while (-not (Test-Path $bashExe) -and $elapsed -lt $timeout) {
        Start-Sleep -Seconds 2; $elapsed += 2
    }

    if (-not (Test-Path $bashExe)) { throw "MSYS2 安装完成但找不到 $bashExe" }
    Write-Success "MSYS2 安装完成：$Msys2Path"
}

function Install-Msys2Packages {
    Write-Step "安装 MSYS2 包"
    if ($SkipPackages) { Write-Skipped "pacman 包安装"; return }

    $pacman = Join-Path $Msys2Path "usr\bin\pacman.exe"
    if (-not (Test-Path $pacman)) { throw "找不到 pacman：$pacman" }

    $packages = [ordered]@{
        "mingw-w64-ucrt-x86_64-verilator" = "ucrt64\bin\verilator_bin.exe"
    }

    foreach ($pkg in $packages.GetEnumerator()) {
        $binPath = Join-Path $Msys2Path $pkg.Value
        if (Test-Path $binPath) { Write-Skipped "$($pkg.Key) 已安装"; continue }
        Write-Host "  安装 $($pkg.Key)..." -ForegroundColor Yellow
        & $pacman -S --noconfirm $pkg.Key
        if ($LASTEXITCODE -ne 0) { Write-Warning2 "$($pkg.Key) 安装失败，继续执行" }
        else { Write-Success "$($pkg.Key) 安装完成" }
    }
}

function Add-Msys2ToPath {
    Write-Step "配置用户 PATH 环境变量"
    $msys2Paths = @(
        (Join-Path $Msys2Path "usr\bin"),
        (Join-Path $Msys2Path "ucrt64\bin")
    )

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if (-not $userPath) { $userPath = "" }
    $pathEntries = $userPath -split ";" | Where-Object { $_ -ne "" }

    $added = @()
    foreach ($p in $msys2Paths) {
        $normalized = $p.TrimEnd("\")
        $alreadyExists = $pathEntries | Where-Object { $_.TrimEnd("\") -ieq $normalized }
        if ($alreadyExists) { Write-Skipped "$p 已在用户 PATH 中" }
        else { $pathEntries += $p; $added += $p }
    }

    if ($added.Count -eq 0) { return }
    $newPath = ($pathEntries -join ";")
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    foreach ($p in $added) { Write-Success "已添加到用户 PATH：$p" }
    $env:Path = $newPath + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
}

function Set-ClaudeConfig {
    Write-Step "配置 Claude Code settings.json"
    if ($SkipClaudeConfig) { Write-Skipped "Claude Code 配置"; return }

    $claudeDir    = Join-Path $env:USERPROFILE ".claude"
    $settingsFile = Join-Path $claudeDir "settings.json"
    $bashExe      = Join-Path $Msys2Path "usr\bin\bash.exe"
    $bashrcFile   = Join-Path $env:USERPROFILE ".bashrc"

    if (-not (Test-Path $claudeDir)) { New-Item -ItemType Directory -Path $claudeDir | Out-Null }

    if (Test-Path $settingsFile) {
        $timestamp  = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupFile = "$settingsFile.backup.$timestamp"
        Copy-Item $settingsFile $backupFile
        Write-Success "已备份原配置：$backupFile"
        $settings = Get-Content $settingsFile -Raw | ConvertFrom-Json
    } else {
        $settings = [PSCustomObject]@{}
    }

    if (-not ($settings.PSObject.Properties.Name -contains "env")) {
        $settings | Add-Member -MemberType NoteProperty -Name "env" -Value ([PSCustomObject]@{})
    }

    $envNode = $settings.env
    $newEnv = @{
        "SHELL"           = $bashExe
        "BASH_ENV"        = $bashrcFile
        "MSYS2_PATH_TYPE" = "inherit"
    }

    foreach ($key in $newEnv.Keys) {
        if ($envNode.PSObject.Properties.Name -contains $key) { $envNode.$key = $newEnv[$key] }
        else { $envNode | Add-Member -MemberType NoteProperty -Name $key -Value $newEnv[$key] }
    }

    $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
    Write-Success "settings.json 已更新"
}

function New-Bashrc {
    Write-Step "创建 ~/.bashrc"
    $bashrcFile = Join-Path $env:USERPROFILE ".bashrc"
    $homeMsys = ($env:USERPROFILE -replace "\\", "/") -replace "^([A-Za-z]):", { "/" + $_.Groups[1].Value.ToLower() }

    if (Test-Path $bashrcFile) { Write-Skipped "~/.bashrc 已存在" }
    else {
        @"
# 此文件通过 BASH_ENV 在每个非交互式 bash 进程中自动加载
export HOME="$homeMsys"
"@ | Set-Content $bashrcFile -Encoding UTF8
        Write-Success "~/.bashrc 已创建：$bashrcFile"
    }
    Write-Success "HOME 已重定向：$homeMsys"
}

function Write-Summary {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  配置完成！" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "`n后续步骤：" -ForegroundColor White
    Write-Host "  1. 重启 Claude Code 使配置生效" -ForegroundColor White

    $veriblePath = "C:\tools\verible"
    if (-not (Test-Path $veriblePath)) {
        Write-Host "  2. 手动安装 Verible（LSP 支持）：" -ForegroundColor White
        Write-Host "     https://github.com/chipsalliance/verible/releases" -ForegroundColor DarkGray
    } else { Write-Success "Verible 已安装：$veriblePath" }

    Write-Host "  3. 在 Claude Code 中安装插件：" -ForegroundColor White
    Write-Host "     /plugin marketplace add xuesongjun/chip-design-plugins" -ForegroundColor DarkGray
    Write-Host "     /plugin install hdl-toolkit@chip-design" -ForegroundColor DarkGray
    Write-Host "     /plugin install systemverilog-lsp@chip-design" -ForegroundColor DarkGray
    Write-Host ""
}

try {
    Write-Host "`nChip Design - Claude Code Windows 开发环境配置" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

    Install-Msys2
    Install-Msys2Packages
    Add-Msys2ToPath
    Set-ClaudeConfig
    New-Bashrc
    Write-Summary
}
catch {
    Write-Host "`n✗ 错误：$_" -ForegroundColor Red
    Write-Host "  请检查上方输出，解决问题后重新运行脚本" -ForegroundColor Yellow
    exit 1
}
