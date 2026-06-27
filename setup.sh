#!/usr/bin/env bash
# FITOM_staging セットアップスクリプト (Linux/macOS)
# 各プロジェクトをビルドした後に実行する。
#
# 複数 hwif DLL 対応:
#   fitom_hw.so (FitomHwIF)       → ステージングルートに配置
#   fitom_fmhwif.so (FitomEmuIF)  → ステージングルートに配置
#   YMEngine.so                   → engines/ サブディレクトリに配置
# profile.json の devices[].dll でどの .so を使うか指定する。
set -euo pipefail

STAGE="$(cd "$(dirname "$0")" && pwd)"
BUILD_TYPE="${1:-Release}"

# ── プロジェクトのビルドディレクトリ (環境に合わせて変更) ──────────────────
FITOM_HWIF_BUILD="../FitomHwIF/build/linux-ninja"
FITOM_EMUIF_BUILD="../FitomEmuIF/build/linux-ninja"
YMENGINE_BUILD="../YMEngine/build/linux-ninja"

copy_if_exists() {
    local src="$1" dst="$2"
    if [ -f "$src" ]; then
        cp -f "$src" "$dst"
        echo "  OK  $src -> $dst"
    else
        echo "  SKIP $src (not found)"
    fi
}

echo "=== FITOM_staging setup ($BUILD_TYPE) ==="

# fitom_hw.so (物理チップ用)
copy_if_exists "$FITOM_HWIF_BUILD/libfitom_hw.so"      "$STAGE/fitom_hw.so"

# fitom_fmhwif.so (FMエンジン内蔵エミュレーター用)
copy_if_exists "$FITOM_EMUIF_BUILD/libfitom_fmhwif.so" "$STAGE/fitom_fmhwif.so"

# FMEngine (.so → engines/ サブディレクトリ)
mkdir -p "$STAGE/engines"
copy_if_exists "$YMENGINE_BUILD/libYMEngine.so"         "$STAGE/engines/YMEngine.so"

# logs
mkdir -p "$STAGE/logs"

echo ""
echo "Setup complete."
echo ""
echo "次のステップ:"
echo "  1. config/profiles/ から使用するプロファイルを選択（または作成）する"
echo "     - emulator_opm.profile.json        : OPM エミュレーターのみ"
echo "     - emulator_opl3.profile.json       : OPL3 エミュレーターのみ"
echo "     - hw_spfm_opm.profile.json         : SPFM OPM 実機のみ"
echo "     - hw_opm_emu_opl3.profile.json     : OPM 実機 + OPL3 エミュ混在"
echo "     - hw_opn_emu_opm_opl3.profile.json : OPN 実機 + OPM/OPL3 エミュ混在"
echo "  2. 複数 DLL 混在構成では profile の devices[].dll で .so を指定する"
echo "     例: { \"if\": \"HW\", \"dll\": \"fitom_hw.so\", ... }"
echo "  3. config/fitom.conf.json の hw_plugin.dll は単一 .so 構成時のみ使用"
echo "  4. FITOM_X を起動してプロファイルを読み込む"
