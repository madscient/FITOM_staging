# FITOM_staging

FITOM_X の動作環境を構成するステージングリポジトリ。  
設定ファイル・プロファイル・プリセットバンク・変換ツールを管理する。  
DLL バイナリは Git 管理対象外（各プロジェクトからビルドして配置する）。

## ディレクトリ構成

```
FITOM_staging/
├── setup.ps1               セットアップスクリプト (Windows)
├── setup.sh                セットアップスクリプト (Linux/macOS)
├── pcm_image_catalog.json  PCM/ADPCMイメージカタログ (hwif/emuif共用、
│                           config_schema/pcm_image_catalog.schema.json 準拠。
│                           images[]の値はカタログファイル自身のディレクトリ
│                           相対で解決される、FitomEmuIF/FitomHwIF共通規則)
├── config/
│   ├── fitom.conf.json     システム設定
│   │
│   ├── profiles/           FITOM_X プロファイル階層 (ディレクトリ配置を
│   │   │                   プロファイルの参照階層に合わせている)
│   │   ├── unified_preset.profile.json      全チップ統合プロファイル (GM+専用バンク一式)
│   │   ├── emu_opn.profile.json             OPNエミュプロファイル (OPN/OPN2/OPNA/OPNB/OPNBB)
│   │   ├── emu_opl.profile.json             OPLエミュプロファイル (OPL[rhythm]/Y8950/OPL2/OPL3/OPL4)
│   │   ├── emu_opm.profile.json             OPMエミュプロファイル (OPM×2/OPZ×2)
│   │   ├── emu_opll.profile.json            OPLLエミュプロファイル (OPLL[rhythm]/OPLLP/VRC7/OPLLX)
│   │   ├── fmall.profile.json               FMALL (OPM/OPZ/OPL3/OPL4AWM/OPNA/OPNBB/OPLL/OPLLP/OPLLX/VRC7)
│   │   │
│   │   └── hw_plugins/     上記プロファイルの hw_plugins[].profile が指す
│   │       │               プラグイン固有サブプロファイル (第2階層)
│   │       ├── fmemuif_opn_profile.json    FitomEmuIF 用 (OPN ファミリー 5チップ、unified_preset/emu_opnが共用)
│   │       ├── fmemuif_opl5.profile.json   FitomEmuIF 用 (OPL系 5チップ)
│   │       ├── fmemuif_opm_opz4.profile.json FitomEmuIF 用 (OPM/OPZ 4チップ)
│   │       ├── fmemuif_opll5.profile.json  FitomEmuIF 用 (OPLL系 5チップ)
│   │       └── fmemuif_fmall.profile.json  FitomEmuIF 用 (FMALL 10チップ)
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
│                           (config/profiles/*.profile.json の banks.*[].file
│                            からは "../../banks/..." で参照する。相対パスの
│                            基点は参照元プロファイルファイル自身のディレクトリ)
├── docs/
│   └── voice-parameter-reference.md
├── tools/
│   └── voice_convert/
├── bin/                    実行ファイル・プラグイン置き場 (.gitignore 対象)
│   ├── fitom_core(.exe)    FITOM_X 本体
│   ├── FitomEmuIF.dll/.so
│   ├── fitom_hw.dll/.so
│   └── engines/
│       ├── YMFMEngine.dll/.so
│       ├── DSAemuEngine.dll/.so
│       ├── EPSGemuEngine.dll/.so
│       ├── SAASoundEngine.dll/.so
│       └── DSGemuEngine.dll/.so
├── dist/                   インストールパッケージ成果物 (.gitignore 対象)
└── logs/                   ログ出力先 (.gitignore 対象)
```

## アーキテクチャ概要

```
FITOM_X (config/profiles/*.profile.json)
  └── hw_plugins[]          プラグイン DLL を名前登録
        ├── FitomEmuIF.dll  ← hw_plugins[].profile (config/profiles/hw_plugins/
        │     │                fmemuif_*.profile.json) でチップ構成を管理
        │     └── YMFMEngine.dll / DSAemuEngine.dll /
        │         EPSGemuEngine.dll / SAASoundEngine.dll /
        │         DSGemuEngine.dll
        │         (bin/engines/ に配置)
        └── fitom_hw.dll    ← hw_plugins[].profile (config/profiles/hw_plugins/
                               fitom_hw_*.profile.json) で実機構成を管理
```

FITOM_X 本体はエミュレーターか実機かを区別しない。  
チップ種・クロック・チャンネル数はすべてプラグイン側のプロファイルで管理し、  
`auto_devices: true` で FITOM_X に自動列挙させる。

`hw_plugins[].profile` の文字列は FITOM_X 本体では一切解釈されず、
`HWPlugin_Init()` にそのまま渡されてプラグイン DLL 自身が解決する
（FitomEmuIF/FitomHwIF とも、実行時カレントディレクトリからの相対パスとして
解決する実装になっている）。起動は常にリポジトリルートを CWD として行う運用
のため、本リポジトリの `profile` 値は常に `config/profiles/hw_plugins/` から
始まるリポジトリルート相対パスで統一している。

### プロファイルの対応関係

| FITOM_X プロファイル | FitomEmuIF サブプロファイル |
|---|---|
| unified_preset | fmemuif_opn_profile.json |
| emu_opn | fmemuif_opn_profile.json |
| emu_opl | fmemuif_opl5.profile.json |
| emu_opm | fmemuif_opm_opz4.profile.json |
| emu_opll | fmemuif_opll5.profile.json |
| fmall | fmemuif_fmall.profile.json |
| emu_psg_stereo | fmemuif_psg_stereo.profile.json |

(いずれも `config/profiles/hw_plugins/` 配下)

統合前の個別プロファイル(`emulator_*.profile.json`/`hw_*.profile.json`、
FitomHwIF実機構成を含む)は誰もメンテナンスしておらず統合後の構成と
矛盾していたため、2026年7月26日に`config/profiles/`および対応する
`hw_plugins/`サブプロファイルごと削除した。実機(FitomHwIF)構成を
使う場合は、削除前の履歴(`git log -- config/profiles/hw_spfm_opm.profile.json`等)
を参照して再構成すること。

## 依存プロジェクト

| プロジェクト | 役割 | 備考 |
|---|---|---|
| [FITOM_X](https://github.com/madscient/FITOM_X) | コアエンジン | このリポジトリはバイナリのみ依存 |
| FitomHwIF | 物理HW I/F DLL (`fitom_hw.dll`) | IHWPlugin 実装 |
| FitomEmuIF | FMエンジン内蔵 hwif DLL (`FitomEmuIF.dll`) | IHWPlugin 実装 |
| YMEngine | FM音源エミュレーター (`YMFMEngine.dll`、旧名`YMEngine.dll`から改称) | engines/ に配置 |
| DSAemuEngine | digital-sound-antiques系エミュレーター (`DSAemuEngine.dll`) | engines/ に配置 |
| EPSGemuEngine | AY8930(EPSG)エミュレーター (`EPSGemuEngine.dll`) | engines/ に配置 |
| SAASoundEngine | SAA1099エミュレーター (`SAASoundEngine.dll`) | engines/ に配置 |
| DSGemuEngine | YM2163(DSG)エミュレーター (`DSGemuEngine.dll`) | engines/ に配置 |

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
fitom_core.exe --profile config/profiles/unified_preset.profile.json
```

実際に読み込まれるサブプロファイルは、選択した FITOM_X プロファイルの
`hw_plugins[].profile` に明示的なパスとして書かれている
（`config/profiles/hw_plugins/*.json`、上記「プロファイルの対応関係」参照）。
環境変数 `FMEMUIF_PROFILE` はプラグイン側のフォールバック探索にのみ使われ、
`profile` が明示されている本リポジトリの構成では使用されない。

### 4. 実機使用時の追加設定

`config/profiles/hw_plugins/fitom_hw_*.profile.json` の `port` を環境に合わせて変更する。

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
- `config/profiles/hw_plugins/fitom_hw_*.profile.json` の `port` は環境依存。コミット前に確認すること。
