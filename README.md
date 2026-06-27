# FITOM_staging

FITOM_X の動作環境を構成するステージングリポジトリ。  
設定ファイル・プロファイル・セットアップスクリプトを管理する。  
DLL バイナリは Git 管理対象外（各プロジェクトからビルドして配置する）。

## ディレクトリ構成

```
FITOM_staging/
├── setup.ps1               セットアップスクリプト (Windows)
├── setup.sh                セットアップスクリプト (Linux/macOS)
├── config/
│   ├── fitom.conf.json     システム設定
│   └── profiles/           プロファイル
│       ├── emulator_opm.profile.json    OPM エミュレーター構成
│       ├── emulator_opl3.profile.json   OPL3 エミュレーター構成
│       └── hw_spfm_opm.profile.json     SPFM 実機 OPM 構成
├── banks/                  → FITOM_X の banks/ を submodule 参照
├── engines/                FM エンジン DLL 置き場 (.gitignore 対象)
└── logs/                   ログ出力先 (.gitignore 対象)
```

## 依存プロジェクトとバージョン対応表

| プロジェクト | 役割 | 備考 |
|---|---|---|
| [FITOM_X](https://github.com/madscient/FITOM_X) | コア + banks/ | submodule (banks/ のみ sparse checkout) |
| FitomHwIF | 物理HW I/F DLL (`fitom_hw.dll`) | IHWPlugin.h 実装 |
| FitomEmuIF | FMエンジン内蔵 hwif DLL (`fitom_fmhwif.dll`) | IHWPlugin.h 実装 |
| YMEngine | FM音源エミュレーター (`engines/YMEngine.dll`) | FmEngineApi.h 実装 |

## 初回セットアップ

### 1. クローン

```bash
git clone https://github.com/madscient/FITOM_staging
cd FITOM_staging

# banks/ を FITOM_X から sparse checkout で取得
git submodule update --init --filter=blob:none --sparse
```

### 2. 各プロジェクトをビルド

```bash
# FitomHwIF
cd ../FitomHwIF && cmake --preset windows-vs2022-x64 && cmake --build build/windows-vs2022-x64

# FitomEmuIF
cd ../FitomEmuIF && cmake --preset windows-vs2022-x64 && cmake --build build/windows-vs2022-x64

# YMEngine (FMエンジン DLL)
cd ../YMEngine && cmake --preset windows-vs2022-x64 && cmake --build build/windows-vs2022-x64
```

### 3. セットアップスクリプトを実行

```powershell
# Windows
.\setup.ps1

# Linux/macOS
./setup.sh
```

スクリプトは各プロジェクトのビルドディレクトリから DLL をコピーする。  
ビルドディレクトリのパスは `setup.ps1` / `setup.sh` 冒頭の変数で変更できる。

### 4. 設定を確認

`config/fitom.conf.json` の `hw_plugin.dll` を使用する DLL に変更する。

| 構成 | dll 設定 |
|---|---|
| FMエンジンエミュレーターのみ | `"fitom_fmhwif.dll"` |
| 物理HWのみ | `"fitom_hw.dll"` |

### 5. プロファイルを選択して FITOM_X を起動

```bash
# FITOM_X のビルドディレクトリから起動（staging ディレクトリを作業ディレクトリに指定）
cd /path/to/FITOM_staging
/path/to/FITOM_X/build/.../fitom_core --profile config/profiles/emulator_opm.profile.json
```

## プロファイルの追加

`config/profiles/` に `*.profile.json` を追加してコミットする。  
`banks/` のパスは `banks/OPM/...` のように相対パスで記述する（staging ルートからの相対）。

## 注意事項

- DLL は `.gitignore` により管理対象外。`setup.ps1` / `setup.sh` で再配置する。
- `IHWPlugin.h` は FitomHwIF・FitomEmuIF・FITOM_X の三者で手動同期が必要。  
  変更時は三リポジトリを同時にコミットすること。
