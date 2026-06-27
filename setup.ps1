<#
.SYNOPSIS
  FITOM_staging セットアップスクリプト (Windows)

.DESCRIPTION
  各プロジェクトのビルド成果物をステージングディレクトリに配置する。
  実行前に各プロジェクトをビルドしておくこと。

.PARAMETER BuildType
  ビルド構成 (Debug / Release)。デフォルト: Release

.EXAMPLE
  .\setup.ps1
  .\setup.ps1 -BuildType Debug
#>
param(
    [string]$BuildType = "Release"
)

$ErrorActionPreference = "Stop"
$Stage = $PSScriptRoot

# ── プロジェクトのビルドディレクトリ (環境に合わせて変更) ──────────────────
$Projects = @{
    FitomHwIF  = "..\FitomHwIF\build\windows-vs2022-x64\$BuildType"
    FitomEmuIF = "..\FitomEmuIF\build\windows-vs2022-x64\$BuildType"
    # FMEngine DLL は engines/ サブディレクトリに配置
    YMEngine   = "..\YMEngine\build\windows-vs2022-x64\$BuildType"
}

function Copy-IfExists($src, $dst) {
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  OK  $src -> $dst"
    } else {
        Write-Warning "  SKIP $src (not found)"
    }
}

Write-Host "=== FITOM_staging setup ($BuildType) ==="

# fitom_hw.dll
Copy-IfExists "$($Projects.FitomHwIF)\fitom_hw.dll" "$Stage\fitom_hw.dll"

# fitom_fmhwif.dll
Copy-IfExists "$($Projects.FitomEmuIF)\fitom_fmhwif.dll" "$Stage\fitom_fmhwif.dll"

# FMEngine DLL
New-Item -ItemType Directory -Force -Path "$Stage\engines" | Out-Null
Copy-IfExists "$($Projects.YMEngine)\YMEngine.dll" "$Stage\engines\YMEngine.dll"

# logs ディレクトリ
New-Item -ItemType Directory -Force -Path "$Stage\logs" | Out-Null

Write-Host ""
Write-Host "Setup complete."
Write-Host "  1. config/fitom.conf.json の hw_plugin.dll を目的の DLL に変更する"
Write-Host "  2. config/profiles/ から使用するプロファイルを選択する"
Write-Host "  3. FITOM_X を起動してプロファイルを読み込む"
