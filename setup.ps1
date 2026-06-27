<#
.SYNOPSIS
  FITOM_staging セットアップスクリプト (Windows)

.DESCRIPTION
  各プロジェクトのビルド成果物をステージングディレクトリに配置する。
  実行前に各プロジェクトをビルドしておくこと。

  複数 hwif DLL 対応:
    fitom_hw.dll (FitomHwIF)       → ステージングルートに配置
    fitom_fmhwif.dll (FitomEmuIF)  → ステージングルートに配置
    YMEngine.dll                   → engines/ サブディレクトリに配置
  profile.json の devices[].dll でどの DLL を使うか指定する。

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

# fitom_hw.dll (物理チップ用)
Copy-IfExists "$($Projects.FitomHwIF)\fitom_hw.dll" "$Stage\fitom_hw.dll"

# fitom_fmhwif.dll (FMエンジン内蔵エミュレーター用)
Copy-IfExists "$($Projects.FitomEmuIF)\fitom_fmhwif.dll" "$Stage\fitom_fmhwif.dll"

# FMEngine DLL (engines/ サブディレクトリ)
New-Item -ItemType Directory -Force -Path "$Stage\engines" | Out-Null
Copy-IfExists "$($Projects.YMEngine)\YMEngine.dll" "$Stage\engines\YMEngine.dll"

# logs ディレクトリ
New-Item -ItemType Directory -Force -Path "$Stage\logs" | Out-Null

Write-Host ""
Write-Host "Setup complete."
Write-Host ""
Write-Host "次のステップ:"
Write-Host "  1. config/profiles/ から使用するプロファイルを選択（または作成）する"
Write-Host "     - emulator_opm.profile.json      : OPM エミュレーターのみ"
Write-Host "     - emulator_opl3.profile.json     : OPL3 エミュレーターのみ"
Write-Host "     - hw_spfm_opm.profile.json       : SPFM OPM 実機のみ"
Write-Host "     - hw_opm_emu_opl3.profile.json   : OPM 実機 + OPL3 エミュ混在"
Write-Host "     - hw_opn_emu_opm_opl3.profile.json : OPN 実機 + OPM/OPL3 エミュ混在"
Write-Host "  2. 複数 DLL 混在構成では profile の devices[].dll で DLL を指定する"
Write-Host "     例: { ""if"": ""HW"", ""dll"": ""fitom_hw.dll"", ... }"
Write-Host "  3. config/fitom.conf.json の hw_plugin.dll は単一 DLL 構成時のみ使用"
Write-Host "  4. FITOM_X を起動してプロファイルを読み込む"
