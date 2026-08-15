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
        DSAemuEngine.dll  PSG系エミュレーター (SSG/DCSG/SCC/OPLL/OPL)
        EPSGemuEngine.dll AY8930 (EPSG) エミュレーター
        SAASoundEngine.dll  SAA1099 エミュレーター
        DSGemuEngine.dll  YM2163 (DSG) エミュレーター

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
    FitomSf2IF = "..\FitomSf2IF\build\$BuildType"
    YMEngine   = "..\YMEngine\build\bin\$BuildType"
    FmGenEngine  = "..\FmGenEngine\build\bin\$BuildType"
    DSAemuEngine = "..\DSAemuEngine\build\bin\$BuildType"
    EPSGemuEngine = "..\EPSGemuEngine\build\bin\$BuildType"
    SAASoundEngine = "..\SAASoundEngine\build\bin\$BuildType"
    DSGemuEngine = "..\DSGemuEngine\build\bin\$BuildType"
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

# ── config/profiles/ の環境依存フィールド(MIDI入力名・実機ポート名)を ──────
# ── gitの索引上プレースホルダーへ正規化するcleanフィルタをローカル登録 ──────
# (.gitattributesはフィルタ名の宣言のみで、実行コマンド自体はセキュリティ上
#  ローカルgit configへの登録が必須。詳細はtools/git_filters/README相当の
#  コメントを.gitattributes参照)
git -C $Stage config filter.envlocal.clean "python tools/git_filters/normalize_env_fields.py"
git -C $Stage config filter.envlocal.smudge "cat"
git -C $Stage config filter.envlocal.required "true"
Write-Host "  OK   git filter 'envlocal' registered"

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
Copy-IfExists "$($Projects.FitomSf2IF)\*.dll"    "$Bin\"

# FM エンジン DLL
Copy-IfExists "$($Projects.YMEngine)\YMFMEngine.dll" "$Bin\engines\"
Copy-IfExists "$($Projects.FmGenEngine)\FmGenEngineApi.dll" "$Bin\engines\"
Copy-IfExists "$($Projects.DSAemuEngine)\DSAemuEngine.dll" "$Bin\engines\"
Copy-IfExists "$($Projects.EPSGemuEngine)\EPSGemuEngine.dll" "$Bin\engines\"
Copy-IfExists "$($Projects.SAASoundEngine)\SAASoundEngine.dll" "$Bin\engines\"
Copy-IfExists "$($Projects.DSGemuEngine)\DSGemuEngine.dll" "$Bin\engines\"

# ── その他 ───────────────────────────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path "$Stage\dist" | Out-Null
New-Item -ItemType Directory -Force -Path "$Stage\logs" | Out-Null

Write-Host ""
Write-Host "Setup complete.  ->  bin/"
Write-Host ""
Write-Host "次のステップ:"
Write-Host "  1. config/profiles/ からプロファイルを選択する"
Write-Host "     unified_preset.profile.json  : 全チップ統合プロファイル (GM+専用バンク一式)"
Write-Host "     emu_opn.profile.json         : OPNエミュプロファイル (OPN/OPN2/OPNA/OPNB/OPNBB)"
Write-Host "     emu_opl.profile.json         : OPLエミュプロファイル (OPL/Y8950/OPL2/OPL3/OPL4)"
Write-Host "     emu_opm.profile.json         : OPMエミュプロファイル (OPM×2/OPZ×2)"
Write-Host "     emu_opll.profile.json        : OPLLエミュプロファイル (OPLL[rhythm]/OPLLP/VRC7/OPLLX)"
Write-Host "     emu_psg_stereo.profile.json  : PSGエミュプロファイル (SSG/DCSG/SCC/EPSG/DSG 各2 リニアステレオ + SAA)"
Write-Host "     fmall.profile.json           : FMALL (10チップ統合)"
Write-Host "  2. 起動:"
Write-Host "     bin\fitom_core.exe --profile config\profiles\<プロファイル名>"
