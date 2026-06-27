#!/usr/bin/env bash
# FITOM_staging セットアップスクリプト (Linux/macOS)
# 各プロジェクトをビルドした後に実行する。
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

# fitom_hw.so
copy_if_exists "$FITOM_HWIF_BUILD/libfitom_hw.so"      "$STAGE/fitom_hw.so"

# fitom_fmhwif.so
copy_if_exists "$FITOM_EMUIF_BUILD/libfitom_fmhwif.so" "$STAGE/fitom_fmhwif.so"

# FMEngine
mkdir -p "$STAGE/engines"
copy_if_exists "$YMENGINE_BUILD/libYMEngine.so"         "$STAGE/engines/YMEngine.so"

# logs
mkdir -p "$STAGE/logs"

echo ""
echo "Setup complete."
echo "  1. config/fitom.conf.json の hw_plugin.dll を目的の .so に変更する"
echo "  2. config/profiles/ から使用するプロファイルを選択する"
echo "  3. FITOM_X を起動してプロファイルを読み込む"
