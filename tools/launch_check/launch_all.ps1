<#
.SYNOPSIS
  各プロファイルを bin\fitom_cli.exe で1本ずつ起動し、起動ログを集計する。

.DESCRIPTION
  config/profiles/*.profile.json を順に起動し、数秒後に止めて logs/fitom.log を
  退避してから次へ進む。プロファイルごとに、HWPort・デバイス・エラー・警告の件数と、
  警告の種類ごとの件数(数字を N に置き換えてまとめたもの)を出す。

  分かるのはデバイスとバンクのロードまでで、音が意図どおり鳴るかは分からない。

  終了コード: Failed to create HWPort・unknown chip・[error]・[fatal] のどれかが出たか、
  ログが残らなかったプロファイルがあれば 1、それ以外は 0。

.PARAMETER Name
  起動するプロファイル名 (.profile.json を除いた部分)。省略時は全プロファイル。

.PARAMETER Seconds
  起動してから止めるまでの秒数。デフォルト: 8

.PARAMETER OutDir
  プロファイルごとのログの退避先。デフォルト: logs\launch_check

.EXAMPLE
  .\tools\launch_check\launch_all.ps1
  .\tools\launch_check\launch_all.ps1 -Name emu_opm,emu_msx
#>
param(
    [string[]]$Name,
    [int]$Seconds = 8,
    [string]$OutDir
)

$ErrorActionPreference = "Stop"
$Stage = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if (-not $OutDir) { $OutDir = Join-Path $Stage "logs\launch_check" }
$Cli = Join-Path $Stage "bin\fitom_cli.exe"
$Log = Join-Path $Stage "logs\fitom.log"

if (-not (Test-Path $Cli)) { throw "$Cli がありません。setup.ps1 で配置してください" }
# 既に動いている fitom_cli がログを掴んでいると、ログが混ざる
if (Get-Process -Name fitom_cli -ErrorAction SilentlyContinue) {
    throw "fitom_cli が既に動いています。止めてから実行してください"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$profiles = Get-ChildItem (Join-Path $Stage "config\profiles\*.profile.json") | Sort-Object Name
if ($Name) {
    # powershell -File 経由では a,b が配列にならず1つの文字列で届く
    $Name = $Name -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
    $profiles = $profiles | Where-Object { $Name -contains ($_.Name -replace '\.profile\.json$', '') }
    if (-not $profiles) { throw "該当するプロファイルがありません: $($Name -join ', ')" }
}

$counters = [ordered]@{
    'HWPort opened'           = 'HWPort opened'
    'Device added'            = 'Device added'
    'Failed to create HWPort' = 'Failed to create HWPort'
    'unknown chip'            = 'unknown chip'
    'error'                   = '\[(error|fatal)\]'
    'warning'                 = '\[warning\]'
}
$fatal = 'Failed to create HWPort', 'unknown chip', 'error'

# fitom_cli は SIGINT で終了しないため、強制終了して WaitForExit で確実に止める
Push-Location $Stage
$failed = $false
try {
    foreach ($p in $profiles) {
        $profileName = $p.Name -replace '\.profile\.json$', ''
        if (Test-Path $Log) { Remove-Item $Log -Force }
        $proc = Start-Process -FilePath $Cli -ArgumentList "config\profiles\$($p.Name)" -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds $Seconds
        if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
        $proc.WaitForExit()

        $dst = Join-Path $OutDir "$profileName.log"
        if (-not (Test-Path $Log)) {
            Write-Host ("{0,-16} ログが残りませんでした" -f $profileName)
            $failed = $true
            continue
        }
        Copy-Item $Log $dst -Force
        $lines = Get-Content $dst -Encoding utf8

        $parts = foreach ($key in $counters.Keys) {
            $n = @($lines | Select-String -Pattern $counters[$key]).Count
            if ($fatal -contains $key -and $n -gt 0) { $failed = $true }
            "$key=$n"
        }
        Write-Host ("{0,-16} {1}" -f $profileName, ($parts -join '  '))

        $lines | Select-String -Pattern '\[warning\]' |
            ForEach-Object { ($_.Line -replace '^.*\[warning\]\s*', '') -replace '\d+', 'N' } |
            Group-Object | Sort-Object Count -Descending |
            ForEach-Object { Write-Host ("    {0,4}  {1}" -f $_.Count, $_.Name) }
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "ログ: $OutDir"
if ($failed) { exit 1 }
exit 0
