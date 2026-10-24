<#
.SYNOPSIS
  FITOM_staging セットアップスクリプト (Windows)

.DESCRIPTION
  各プロジェクトのビルド成果物を bin/ ディレクトリに配置する。
  -Build を付けない場合は、実行前に各プロジェクトをビルドしておくこと。
  配置後、各プロジェクトのコミットを bin/build_info.json に書き出す。

  bin/ レイアウト:
    bin/
      fitom_cli.exe       FITOM_X 本体 (コンソール版)
      fitom_gui.exe       FITOM_X 本体 (GUI版)
      FitomEmuIF.dll      FMエンジン内蔵エミュレーター統合プラグイン (FitomEmuIF)
      fitom_hw.dll        物理チップ用プラグイン (FitomHwIF)
      engines/
        YMFMEngine.dll    FM音源エミュレーター
        FmGenEngine.dll   fmgen系FM音源エミュレーター
        DSAemuEngine.dll  PSG系エミュレーター (SSG/DCSG/SCC/OPLL/OPL、Y8960のOPLLEX/OPL2EX/SSGEX/SCCEX)
        EPSGemuEngine.dll AY8930 (EPSG) エミュレーター
        SAASoundEngine.dll  SAA1099 エミュレーター
        DSGemuEngine.dll  YM2163 (DSG) エミュレーター
        Y8960emuEngine.dll  Y8960 (拡張OPLL部/拡張OPL2部) エミュレーター

  プラグインDLLの検索パスは実行ファイルからの相対パスで解決される。
  デフォルトでは実行ファイルと同階層 (bin/) を探索する。

.PARAMETER BuildType
  ビルド構成 (Debug / Release)。デフォルト: Release

.PARAMETER Pull
  配置の前に、各プロジェクトを upstream へ早送りする。追跡中のファイルに
  未コミットの変更があるもの、upstream と分岐しているもの、upstream の無い
  ものがあれば、どれも変更せずに中止する。管理外のファイルは問わない。

.PARAMETER Build
  配置の前に、各プロジェクトの既存のビルドディレクトリで cmake --build を
  実行する。ビルドディレクトリが未構成 (CMakeCache.txt が無い) なら中止する。

.EXAMPLE
  .\setup.ps1
  .\setup.ps1 -BuildType Debug
  .\setup.ps1 -Pull -Build

.NOTES
  実行ポリシーによりブロックされた場合:
    Unblock-File .\setup.ps1                          # ZIP 展開後のブロック解除 (推奨)
    powershell -ExecutionPolicy Bypass -File .\setup.ps1  # セッション一時許可
#>
param(
    [string]$BuildType = "Release",
    [switch]$Pull,
    [switch]$Build
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
    Y8960emu = "..\Y8960emu\build\bin\$BuildType"
}

# ── 各プロジェクトのリポジトリとビルドディレクトリ (-Pull / -Build 用) ────────
$Repos = [ordered]@{
    FitomX         = @{ Repo = "..\FITOM_X";            BuildDir = "build\windows-vs2026-x64" }
    PatchEditor    = @{ Repo = "..\FITOM_patch_editor"; BuildDir = "build\vs2026" }
    FitomEmuIF     = @{ Repo = "..\FitomEmuIF";         BuildDir = "build" }
    FitomHwIF      = @{ Repo = "..\FitomHwIF";          BuildDir = "build" }
    FitomSf2IF     = @{ Repo = "..\FitomSf2IF";         BuildDir = "build" }
    YMEngine       = @{ Repo = "..\YMEngine";           BuildDir = "build" }
    FmGenEngine    = @{ Repo = "..\FmGenEngine";        BuildDir = "build" }
    DSAemuEngine   = @{ Repo = "..\DSAemuEngine";       BuildDir = "build" }
    EPSGemuEngine  = @{ Repo = "..\EPSGemuEngine";      BuildDir = "build" }
    SAASoundEngine = @{ Repo = "..\SAASoundEngine";     BuildDir = "build" }
    DSGemuEngine   = @{ Repo = "..\DSGemuEngine";       BuildDir = "build" }
    Y8960emu       = @{ Repo = "..\Y8960emu";           BuildDir = "build" }
}

function Get-RepoPath($name) { Join-Path $Stage $Repos[$name].Repo }

# 1つでも進められないリポジトリがあれば、どれも動かさずに中止する。
# 一部だけ進めると、リポジトリ間で版の食い違った bin/ ができるため。
function Invoke-Pull {
    Write-Host "--- pull ---"
    foreach ($name in $Repos.Keys) {
        $repo = Get-RepoPath $name
        git -C $repo fetch --quiet
        if ($LASTEXITCODE -ne 0) { throw "$name : git fetch に失敗しました" }
    }
    $problems = @()
    foreach ($name in $Repos.Keys) {
        $repo = Get-RepoPath $name
        # 2>$null で黙らせると、PowerShell 5.1 では $ErrorActionPreference=Stop の下で
        # 例外になるため、stderr を出さない形で upstream を引く
        $branch = git -C $repo symbolic-ref -q HEAD
        $upstream = if ($branch) { git -C $repo for-each-ref --format="%(upstream:short)" $branch }
        if (-not $upstream) { $problems += "$name : ブランチ上に無いか、upstream がありません"; continue }
        if (git -C $repo status --porcelain --untracked-files=no) {
            $problems += "$name : 追跡中のファイルに未コミットの変更があります"; continue
        }
        $ahead, $behind = (git -C $repo rev-list --left-right --count "HEAD...@{u}") -split '\s+'
        if ([int]$ahead -gt 0 -and [int]$behind -gt 0) {
            $problems += "$name : $upstream と分岐しています (ローカル $ahead 件 / upstream $behind 件)"
        }
    }
    if ($problems) {
        $problems | ForEach-Object { Write-Warning "  $_" }
        throw "pull を中止しました。どのリポジトリも変更していません。"
    }
    foreach ($name in $Repos.Keys) {
        $repo = Get-RepoPath $name
        $ahead, $behind = (git -C $repo rev-list --left-right --count "HEAD...@{u}") -split '\s+'
        if ([int]$behind -gt 0) {
            git -C $repo merge --ff-only --quiet "@{u}"
            if ($LASTEXITCODE -ne 0) { throw "$name : 早送りに失敗しました" }
        }
        $note = if ([int]$ahead -gt 0) { " (未pushのローカルコミット $ahead 件を含む)" } else { "" }
        Write-Host ("  OK   {0,-15} {1}{2}" -f $name, (git -C $repo rev-parse --short HEAD), $note)
    }
}

function Invoke-Build {
    Write-Host "--- build ($BuildType) ---"
    foreach ($name in $Repos.Keys) {
        $dir = Join-Path (Get-RepoPath $name) $Repos[$name].BuildDir
        if (-not (Test-Path (Join-Path $dir "CMakeCache.txt"))) {
            throw "$name : $dir が構成されていません (CMakeCache.txt が無い)"
        }
        Write-Host "  ...  $name"
        cmake --build $dir --config $BuildType --parallel | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "$name : ビルドに失敗しました。cmake --build `"$dir`" --config $BuildType で詳細を確認してください"
        }
        Write-Host "  OK   $name"
    }
}

# built=false のときは、bin/ の中身がこのコミットからビルドされたとは限らない
# (ビルドはこのスクリプトの外で行われている)。
function Write-BuildInfo($bin) {
    $commits = [ordered]@{}
    foreach ($name in $Repos.Keys) {
        $repo = Get-RepoPath $name
        $commits[$name] = [ordered]@{
            commit = (git -C $repo rev-parse HEAD)
            dirty  = [bool](git -C $repo status --porcelain --untracked-files=no)
        }
    }
    $info = [ordered]@{
        generated  = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
        build_type = $BuildType
        built      = [bool]$Build
        repos      = $commits
    }
    $path = Join-Path $bin "build_info.json"
    [IO.File]::WriteAllText($path, ($info | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding $false))
    Write-Host "  OK   build_info.json"
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

if ($Pull)  { Invoke-Pull }
if ($Build) { Invoke-Build }

# ── bin/ を作成 ──────────────────────────────────────────────────────────────
$Bin = Join-Path $Stage "bin"
New-Item -ItemType Directory -Force -Path $Bin | Out-Null
New-Item -ItemType Directory -Force -Path "$Bin\engines" | Out-Null

# FITOM_X 本体
Copy-IfExists "$($Projects.FitomX)\fitom_gui.exe" "$Bin\"
Copy-IfExists "$($Projects.FitomX)\fitom_cli.exe" "$Bin\"
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
Copy-IfExists "$($Projects.FmGenEngine)\FmGenEngine.dll" "$Bin\engines\"
Copy-IfExists "$($Projects.DSAemuEngine)\DSAemuEngine.dll" "$Bin\engines\"
Copy-IfExists "$($Projects.EPSGemuEngine)\EPSGemuEngine.dll" "$Bin\engines\"
Copy-IfExists "$($Projects.SAASoundEngine)\SAASoundEngine.dll" "$Bin\engines\"
Copy-IfExists "$($Projects.DSGemuEngine)\DSGemuEngine.dll" "$Bin\engines\"
Copy-IfExists "$($Projects.Y8960emu)\Y8960emuEngine.dll" "$Bin\engines\"

# ── その他 ───────────────────────────────────────────────────────────────────
Copy-IfExists ".\config\fitom.conf.json" "$Bin\"
Write-BuildInfo $Bin
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
Write-Host "     fmall.profile.json           : FMALL (OPZ/OPNBB/OPL3+OPL4AWMをL/R2枚ずつ + OPLLEX)"
Write-Host "     emu_msx.profile.json         : MSXプロファイル (OPLL[rhythm]/Y8950[rhythm]/SSG/SCC+/OPM)"
Write-Host "     emu_msx2pp.profile.json      : MSX2++プロファイル (Y8960: OPLLEX[rhythm]/OPL2EX/SSGEX/SCCEX/OPM)"
Write-Host "     emu_pc88.profile.json        : PC-88プロファイル (OPN/OPNA/OPM)"
Write-Host "     emu_pc98.profile.json        : PC-98プロファイル (OPN/OPNA/OPL3/Y8950[rhythm])"
Write-Host "     emu_ibmpc.profile.json       : IBM PCプロファイル (SAA×2/OPL2[rhythm]/OPL3/OPM/DCSG)"
Write-Host "  2. 起動 (リポジトリのルートで):"
Write-Host "     bin\fitom_cli.exe config\profiles\<プロファイル名>"
Write-Host "     bin\fitom_gui.exe"
