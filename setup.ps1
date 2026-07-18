<#
.SYNOPSIS
  FITOM_staging セットアップスクリプト (Windows)

.DESCRIPTION
  各プロジェクトのビルド成果物を bin/ ディレクトリに配置する。
  実行前に各プロジェクトをビルドしておくこと。

  bin/ レイアウト:
    bin/
      fitom_core.exe      FITOM_X 本体
      FitomEmuIF.dll      FMエンジン内蔵エミュレーター統合プラグイン (FitomEmuIF)
      fitom_hw.dll        物理チップ用プラグイン (FitomHwIF)
      engines/
        YMFMEngine.dll    FM音源エミュレーター

  プラグインDLLの検索パスは実行ファイルからの相対パスで解決される。
  デフォルトでは実行ファイルと同階層 (bin/) を探索する。

.PARAMETER BuildType
  ビルド構成 (Debug / Release)。デフォルト: Release

.EXAMPLE
  .\setup.ps1
  .\setup.ps1 -BuildType Debug

.NOTES
  実行ポリシーによりブロックされた場合:
    Unblock-File .\setup.ps1                          # ZIP 展開後のブロック解除 (推奨)
    powershell -ExecutionPolicy Bypass -File .\setup.ps1  # セッション一時許可
#>
param(
    [string]$BuildType = "Release"
)

$ErrorActionPreference = "Stop"
$Stage = $PSScriptRoot

# ── プロジェクトのビルドディレクトリ (環境に合わせて変更) ──────────────────
$Projects = @{
    FitomX     = "..\FITOM_X\build\windows-vs2026-x64\bin\$BuildType"
    PatchEditor= "..\FITOM_patch_editor\build\vs2026\$BuildType"
    FitomEmuIF = "..\FitomEmuIF\build\$BuildType"
    FitomHwIF  = "..\FitomHwIF\build\$BuildType"
    YMEngine   = "..\YMEngine\build\bin\$BuildType"
}

function Copy-IfExists($src, $dst) {
    if (Test-Path $src) {
        Copy-Item $src $dst -Force -Recurse
        Write-Host "  OK   $src"
    } else {
        Write-Warning "  SKIP $src (not found)"
    }
}

Write-Host "=== FITOM_staging setup ($BuildType) ==="

# ── bin/ を作成 ──────────────────────────────────────────────────────────────
$Bin = Join-Path $Stage "bin"
New-Item -ItemType Directory -Force -Path $Bin | Out-Null
New-Item -ItemType Directory -Force -Path "$Bin\engines" | Out-Null

# FITOM_X 本体
Copy-IfExists "$($Projects.FitomX)\*.exe" "$Bin\"
Copy-IfExists "$($Projects.FitomX)\*.dll" "$Bin\"
Copy-IfExists "$($Projects.FitomX)\assets" "$Bin\"

# パッチエディタ
Copy-IfExists "$($Projects.PatchEditor)\*.exe" "$Bin\"
Copy-IfExists "$($Projects.PatchEditor)\*.dll" "$Bin\"
Copy-IfExists "$($Projects.PatchEditor)\assets" "$Bin\"

# プラグイン DLL
Copy-IfExists "$($Projects.FitomEmuIF)\*.dll" "$Bin\"
Copy-IfExists "$($Projects.FitomHwIF)\*.dll"    "$Bin\"

# FM エンジン DLL
Copy-IfExists "$($Projects.YMEngine)\YMFMEngine.dll" "$Bin\engines\"

# ── その他 ───────────────────────────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path "$Stage\dist" | Out-Null
New-Item -ItemType Directory -Force -Path "$Stage\logs" | Out-Null

Write-Host ""
Write-Host "Setup complete.  ->  bin/"
Write-Host ""
Write-Host "次のステップ:"
Write-Host "  1. config/profiles/ からプロファイルを選択する"
Write-Host "     emulator_opn_family.profile.json  : OPN/OPN2/OPNA/OPNB/OPNBB (FitomEmuIF)"
Write-Host "     emulator_opm.profile.json         : OPM エミュレーター"
Write-Host "     emulator_opl3.profile.json        : OPL3 エミュレーター"
Write-Host "     hw_spfm_opm.profile.json          : SPFM 実機 OPM"
Write-Host "     hw_opm_emu_opl3.profile.json      : OPM 実機 + OPL3 エミュ混在"
Write-Host "     hw_opn_emu_opm_opl3.profile.json  : OPN 実機 + OPM/OPL3 エミュ混在"
Write-Host "  2. 実機使用時は config/profiles/hw_plugins/fitom_hw_*.profile.json の port を確認する"
Write-Host "  3. 起動:"
Write-Host "     bin\fitom_core.exe --profile config\profiles\<プロファイル名>"
