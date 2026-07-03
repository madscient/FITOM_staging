# FITOM_staging

FITOM_X の動作環境を構成するステージングリポジトリ。  
設定ファイル・プロファイル・プリセットバンク・変換ツールを管理する。  
DLL バイナリは Git 管理対象外（各プロジェクトからビルドして配置する）。

## ディレクトリ構成

```
FITOM_staging/
├── setup.ps1               セットアップスクリプト (Windows)
├── setup.sh                セットアップスクリプト (Linux/macOS)
├── config/
│   ├── fitom.conf.json     システム設定
│   └── profiles/           プロファイル
│       ├── emulator_opm.profile.json        OPM エミュレーター構成
│       ├── emulator_opl3.profile.json       OPL3 エミュレーター構成
│       ├── hw_spfm_opm.profile.json         SPFM 実機 OPM 構成
│       ├── hw_opm_emu_opl3.profile.json     OPM 実機 + OPL3 エミュ混在
│       └── hw_opn_emu_opm_opl3.profile.json OPN 実機 + OPM/OPL3 エミュ混在
├── config_schema/          JSON Schema 定義
│   ├── profile.schema.json
│   ├── hwbank.schema.json
│   └── drumbank.schema.json
├── banks/                  プリセット音色バンク (このリポジトリで直接管理)
│   ├── README.md           バンク一覧・出典
│   ├── OPN/
│   ├── OPM/
│   ├── OPZ/
│   ├── OPL2/
│   ├── OPL3/
│   └── drums/
├── docs/
│   └── voice-parameter-reference.md  チップ別パラメータリファレンス
├── tools/
│   └── voice_convert/      音色変換スクリプト (Python 3.8+)
│       └── README.md       各ツールの使い方
├── engines/                FM エンジン DLL 置き場 (.gitignore 対象)
└── logs/                   ログ出力先 (.gitignore 対象)
```

## 依存プロジェクトとバージョン対応表

| プロジェクト | 役割 | 備考 |
|---|---|---|
| [FITOM_X](https://github.com/madscient/FITOM_X) | コアエンジン・チップドライバ | このリポジトリはバイナリのみ依存 |
| FitomHwIF | 物理HW I/F DLL (`fitom_hw.dll`) | IHWPlugin.h 実装 |
| FitomEmuIF | FMエンジン内蔵 hwif DLL (`fitom_fmhwif.dll`) | IHWPlugin.h 実装 |
| YMEngine | FM音源エミュレーター (`engines/YMEngine.dll`) | FmEngineApi.h 実装 |

## 初回セットアップ

### 1. クローン

```bash
git clone https://github.com/madscient/FITOM_staging
cd FITOM_staging
```

`banks/` はこのリポジトリで直接管理しているため、submodule の初期化は不要。

### 2. 各プロジェクトをビルド

```bash
# FitomHwIF
cd ../FitomHwIF && cmake --preset windows-vs2022-x64 && cmake --build build/windows-vs2022-x64

# FitomEmuIF
cd ../FitomEmuIF && cmake --preset windows-vs2022-x64 && cmake --build build/windows-vs2022-x64

# YMEngine
cd ../YMEngine && cmake --preset windows-vs2022-x64 && cmake --build build/windows-vs2022-x64
```

### 3. セットアップスクリプトを実行

```powershell
# Windows
.\setup.ps1

# Linux/macOS
./setup.sh
```

### 4. プロファイルを選択して FITOM_X を起動

```bash
cd /path/to/FITOM_staging
/path/to/FITOM_X/build/.../fitom_core --profile config/profiles/emulator_opm.profile.json
```

## プリセットバンクの保守

`banks/` 以下のファイルはこのリポジトリで保守する。  
`config_schema/hwbank.schema.json` がフォーマットの正式定義。  
音色変換ツールは `tools/voice_convert/` を参照。  
チップ別のパラメータ意味は `docs/voice-parameter-reference.md` を参照。

### FITOM_X 本体との同期について

FITOM_X 本体側でチップドライバのフィールド解釈が変更された場合は、  
`config_schema/hwbank.schema.json` および `tools/voice_convert/` の対応スクリプトを  
追従して修正すること（`tools/voice_convert/HANDOFF.md` 参照）。

## プロファイルの追加・編集

`config/profiles/` に `*.profile.json` を追加してコミットする。  
バンクファイルのパスは staging ルートからの相対パスで記述する。  
複数 DLL 混在構成では `devices[].dll` で使用する DLL を指定する（詳細は各プロファイルのコメント参照）。

## 注意事項

- DLL は `.gitignore` により管理対象外。`setup.ps1` / `setup.sh` で再配置する。
- `IHWPlugin.h` は FitomHwIF・FitomEmuIF・FITOM_X の三者で手動同期が必要。  
  変更時は三リポジトリを同時にコミットすること。
- `config_schema/profile.schema.json` は FITOM_X 本体側と手動同期が必要。
