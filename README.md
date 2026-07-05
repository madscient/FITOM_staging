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
│   │
│   ├── profiles/           FITOM_X プロファイル (hw_plugins + banks を定義)
│   │   ├── emulator_opm.profile.json        OPM エミュレーター構成
│   │   ├── emulator_opl3.profile.json       OPL3 エミュレーター構成
│   │   ├── emulator_opn_family.profile.json OPN/OPN2/OPNA/OPNB/OPNBB 5チップ同時
│   │   ├── hw_spfm_opm.profile.json         SPFM 実機 OPM 構成
│   │   ├── hw_opm_emu_opl3.profile.json     OPM 実機 + OPL3 エミュ混在
│   │   └── hw_opn_emu_opm_opl3.profile.json OPN 実機 + OPM/OPL3 エミュ混在
│   │
│   ├── fmhwif_profile.json         FitomEmuIF 用 (OPN ファミリー 5チップ)
│   ├── fmhwif_opm.profile.json     FitomEmuIF 用 (OPM 単体)
│   ├── fmhwif_opl3.profile.json    FitomEmuIF 用 (OPL3 単体)
│   ├── fmhwif_opm_opl3.profile.json FitomEmuIF 用 (OPM + OPL3 混在)
│   ├── fitom_hw_spfm_opm.profile.json  FitomHwIF 用 (SPFM OPM 単体)
│   ├── fitom_hw_opm.profile.json   FitomHwIF 用 (SPFM OPM、混在用)
│   └── fitom_hw_opn.profile.json   FitomHwIF 用 (SPFM OPN、混在用)
│
├── config_schema/          JSON Schema 定義
│   ├── profile.schema.json
│   ├── patchbank.schema.json
│   ├── hwbank.schema.json
│   └── drumbank.schema.json
├── banks/                  プリセット音色バンク (このリポジトリで直接管理)
│   ├── README.md
│   ├── OPN/ OPM/ OPZ/ OPL2/ OPL3/ drums/
│   ├── sw/                 SwBank (ベロシティ感度・LFO)
│   └── patches/            PatchBank (ToneLayer 定義)
├── docs/
│   └── voice-parameter-reference.md
├── tools/
│   └── voice_convert/
├── bin/                    実行ファイル・プラグイン置き場 (.gitignore 対象)
│   ├── fitom_core(.exe)    FITOM_X 本体
│   ├── FitomEmuIF.dll/.so
│   ├── fitom_hw.dll/.so
│   └── engines/
│       └── YMEngine.dll/.so
├── dist/                   インストールパッケージ成果物 (.gitignore 対象)
└── logs/                   ログ出力先 (.gitignore 対象)
```

## アーキテクチャ概要

```
FITOM_X (profile.json)
  └── hw_plugins[]          プラグイン DLL を名前登録
        ├── FitomEmuIF.dll  ← fmhwif_profile.json でチップ構成を管理
        │     └── YMEngine.dll (bin/engines/ に配置)
        └── fitom_hw.dll    ← fitom_hw_*.profile.json で実機構成を管理
```

FITOM_X 本体はエミュレーターか実機かを区別しない。  
チップ種・クロック・チャンネル数はすべてプラグイン側のプロファイルで管理し、  
`auto_devices: true` で FITOM_X に自動列挙させる。

### プロファイルの対応関係

| FITOM_X プロファイル | FitomEmuIF プロファイル | FitomHwIF プロファイル |
|---|---|---|
| emulator_opn_family | fmhwif_profile.json (5チップ) | — |
| emulator_opm | fmhwif_opm.profile.json | — |
| emulator_opl3 | fmhwif_opl3.profile.json | — |
| hw_spfm_opm | — | fitom_hw_spfm_opm.profile.json |
| hw_opm_emu_opl3 | fmhwif_opl3.profile.json | fitom_hw_opm.profile.json |
| hw_opn_emu_opm_opl3 | fmhwif_opm_opl3.profile.json | fitom_hw_opn.profile.json |

## 依存プロジェクト

| プロジェクト | 役割 | 備考 |
|---|---|---|
| [FITOM_X](https://github.com/madscient/FITOM_X) | コアエンジン | このリポジトリはバイナリのみ依存 |
| FitomHwIF | 物理HW I/F DLL (`fitom_hw.dll`) | IHWPlugin 実装 |
| FitomEmuIF | FMエンジン内蔵 hwif DLL (`FitomEmuIF.dll`) | IHWPlugin 実装 |
| YMEngine | FM音源エミュレーター (`YMEngine.dll`) | engines/ に配置 |

## 初回セットアップ

### 1. クローン

```bash
git clone https://github.com/madscient/FITOM_staging
cd FITOM_staging
```

### 2. 各プロジェクトをビルドしてセットアップスクリプトを実行

```powershell
# Windows
.\setup.ps1

# Linux/macOS
./setup.sh
```

### 3. プロファイルを選択して起動

```powershell
# FITOM_X プロファイルを指定して起動
fitom_core.exe --profile config/profiles/emulator_opn_family.profile.json
```

エミュレーター使用時は `FMHWIF_PROFILE` 環境変数が自動設定される  
（`hw_plugins[].profile` + `profile_env` の組み合わせによる）。  
実機使用時は `FITOM_HW_PROFILE` が同様に設定される。

### 4. 実機使用時の追加設定

`config/fitom_hw_*.profile.json` の `port` を環境に合わせて変更する。

```json
{ "type": "SPFM_LIGHT", "port": "COM3", ... }
```

## プリセットバンクの保守

`banks/` 以下はこのリポジトリで保守する。  
`config_schema/hwbank.schema.json` がフォーマットの正式定義。  
音色変換ツールは `tools/voice_convert/` 参照。  
チップ別パラメータは `docs/voice-parameter-reference.md` 参照。

FITOM_X 本体側でチップドライバのフィールド解釈が変更された場合は、  
`config_schema/` および `tools/voice_convert/` を追従して修正すること。

## 注意事項

- DLL は `.gitignore` により管理対象外。`setup.ps1` / `setup.sh` で再配置する。
- `IHWPlugin.h` は FitomHwIF・FitomEmuIF・FITOM_X の三者で手動同期が必要。
- `config_schema/profile.schema.json` は FITOM_X 本体側と手動同期が必要。
- `config/fitom_hw_*.profile.json` の `port` は環境依存。コミット前に確認すること。
