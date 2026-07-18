#!/usr/bin/env bash
# FITOM_staging セットアップスクリプト (Linux/macOS)
#
# 各プロジェクトのビルド成果物を bin/ ディレクトリに配置する。
# 実行前に各プロジェクトをビルドしておくこと。
#
# bin/ レイアウト:
#   bin/
#     fitom_core          FITOM_X 本体
#     FitomEmuIF.so       FMエンジン内蔵エミュレーター統合プラグイン (FitomEmuIF)
#     fitom_hw.so         物理チップ用プラグイン (FitomHwIF)
#     engines/
#       YMFMEngine.so     FM音源エミュレーター
#
# プラグインDLLの検索パスは実行ファイルからの相対パスで解決される。
# デフォルトでは実行ファイルと同階層 (bin/) を探索する。
set -euo pipefail

STAGE="$(cd "$(dirname "$0")" && pwd)"
BUILD_TYPE="${1:-Release}"

# ── プロジェクトのビルドディレクトリ (環境に合わせて変更) ──────────────────
FITOM_X_BUILD="../FITOM_X/build/linux-ninja"
FITOM_EMUIF_BUILD="../FitomEmuIF/build/linux-ninja"
FITOM_HWIF_BUILD="../FitomHwIF/build/linux-ninja"
YMENGINE_BUILD="../YMEngine/build/linux-ninja"

copy_if_exists() {
    local src="$1" dst="$2"
    if [ -f "$src" ]; then
        cp -f "$src" "$dst"
        echo "  OK   $src"
    else
        echo "  SKIP $src (not found)"
    fi
}

echo "=== FITOM_staging setup ($BUILD_TYPE) ==="

# ── bin/ を作成 ──────────────────────────────────────────────────────────────
mkdir -p "$STAGE/bin/engines"

# FITOM_X 本体
copy_if_exists "$FITOM_X_BUILD/fitom_core"          "$STAGE/bin/fitom_core"
[ -f "$STAGE/bin/fitom_core" ] && chmod +x "$STAGE/bin/fitom_core"

# プラグイン
copy_if_exists "$FITOM_EMUIF_BUILD/FitomEmuIF.so"   "$STAGE/bin/FitomEmuIF.so"
copy_if_exists "$FITOM_HWIF_BUILD/fitom_hw.so"      "$STAGE/bin/fitom_hw.so"

# FM エンジン
copy_if_exists "$YMENGINE_BUILD/YMFMEngine.so"      "$STAGE/bin/engines/YMFMEngine.so"

# ── その他 ───────────────────────────────────────────────────────────────────
mkdir -p "$STAGE/dist"
mkdir -p "$STAGE/logs"

echo ""
echo "Setup complete.  ->  bin/"
echo ""
echo "次のステップ:"
echo "  1. config/profiles/ からプロファイルを選択する"
echo "  2. 実機使用時は config/profiles/hw_plugins/fitom_hw_*.profile.json の port を確認する"
echo "  3. 起動:"
echo "     bin/fitom_core --profile config/profiles/<プロファイル名>"
