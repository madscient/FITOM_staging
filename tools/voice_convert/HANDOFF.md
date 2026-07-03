# プリセットパッチ保守 引き継ぎパッケージ

FITOM_X本体（コアエンジン・チップドライバ）開発からプリセットパッチ
（`hwbank.json`/`drumbank.json`）の保守作業を分離し、staging プロジェクトへ
移管するための引き継ぎ資料です。

---

## 1. 引き継ぐ範囲

| 対象 | 内容 |
|---|---|
| プリセット音色バンク | `banks/` 以下、54ファイル（GM/OPM/OPZ/OPL2/OPL3/ドラム） |
| バンク変換ツール | `tools/voice_convert/` 以下、Python製の各種フォーマット変換スクリプト |
| スキーマ定義 | `config_schema/hwbank.schema.json`、`config_schema/drumbank.schema.json` |
| リファレンスドキュメント | `docs/voice-parameter-reference.md`（チップ種別ごとのフィールド意味一覧、新規作成） |

本体側（`core/`配下のC++実装、チップドライバ等）は今回の移管範囲に含まれません。
**プリセットパッチはあくまで`hwbank.schema.json`が定めるJSON形式に従うデータであり、
本体側のC++実装の詳細を知らなくても保守できるように設計されています。**

---

## 2. `hwbank.json`フォーマットの読み方

### 必読ドキュメント（優先順）

1. **`docs/voice-parameter-reference.md`**（今回新規作成）
   チップを選んだときに実際に効くフィールドと意味を一覧できるリファレンス。
   プリセット作成・修正時はまずここを見る。
2. **`config_schema/hwbank.schema.json`**
   JSON Schemaによる正式な型定義。各フィールドの`description`にも詳細説明あり。
   エディタ（VSCode等）でこのスキーマを指定すると、JSON編集時に補完・検証が効く。
3. `docs/voice-data-design.md`（本体リポジトリ側、参考情報）
   設計判断の背景・経緯。保守作業では読む必要は薄いが、「なぜこのフィールドは
   このチップでは無視されるのか」等の疑問が生じた際に参照する。

### 全体構造

```
hwbank.json
├── name, group, bank, op_count, source  … バンクメタ情報
└── patches[]                            … 音色配列 (最大128)
    ├── prog, name                       … プログラム番号・音色名
    ├── FB, ALG, AMS, PMS, NFQ, FB2       … hw (チャンネル単位パラメータ)
    ├── ops[] (最大4要素)                 … オペレータ単位パラメータ
    │   └── AR,DR,SL,SR,RR,TL,KSR,KSL,MUL,DT1,DT2,FXV,AM,VIB,EGT,WS
    └── ext                              … チップ固有拡張 (REV,EGS,DM0,DT3,ALG_EXT,HWEP)
```

**重要**: 多くのフィールドは「特定チップのみが参照し、他チップでは無視される」
設計になっている。あるチップ用に作成したパッチデータを別チップ用に流用する際は、
`voice-parameter-reference.md`で対象チップが実際に参照するフィールドを確認する。

---

## 3. 既存の変換ツール一覧

`tools/voice_convert/README.md`に各ツールの詳細な使い方がある。概要のみ記載：

| スクリプト | 対応フォーマット | 出力グループ |
|---|---|---|
| `necopn_convert.py` | N88-BASIC(86) OPNA/OPNドライバ音色 (`necopn.bin`) | OPN |
| `vmem_convert.py` | DX27/DX100 VMEM 32-Voice SysEx (`.syx`) | OPM |
| `fb01_convert.py` | Yamaha FB-01 ROMダンプ (`.dmp`) | OPM |
| `tx81z_convert.py` | TX81Z 32-Voice VMEM SysEx (`.syx`) | OPZ |
| `vma_convert.py` | MA-2 VMAファイル (`.vma`) | OPL2/OPL3 |
| `alsa_convert.py` | ALSA sbiload音色バンク (`.sb`/`.o3`) | OPL2/OPL3 |
| `opl2_merge.py` | （変換ではなく合成）OPL2バンク2本→OPL3 4OPバンク | OPL3 |

いずれも Python 3.8 以上、標準ライブラリのみで動作する（追加パッケージ不要）。

### 今回のセッションで修正した点（重要）

`opl2_merge.py`は当初、`hw.FB2`/`hw.ALG2`という**現行スキーマに存在しない
フィールド**を出力しており、本体側の`COPL3`実装（`hw.ALG`3bit統合方式、
`hw.FB`/`hw.FB2`の2フィールド分離方式）と整合していませんでした。
今回のセッションで両者を修正し、整合を取っています（詳細は
`voice-parameter-reference.md`の「OPL3 4OPモード」セクション参照）。

**staging移管後、他の変換ツールも同様の不整合が将来的に発生しうる**点に注意
してください。本体側でチップドライバのフィールド解釈が変更された場合、
対応する変換ツールの出力ロジックも追従して修正する必要があります。
（本体リポジトリ側の`docs/voice-parameter-reference.md`が更新された際は、
このリファレンスとの整合を都度確認することを推奨します。）

---

## 4. 既存プリセットバンクの一覧

`banks/README.md`にディレクトリ構成・出典・音色数サマリーがある。

| グループ | バンク数 | 総音色数 |
|---|---|---|
| OPN | 1 | 128 |
| OPM | 17 | 364 |
| OPZ | 4 | 128 |
| OPL2 | 20 | 2560 |
| OPL3 | 3 | 384 |
| drums(OPL2) | 8 | 376 |
| drums(OPL3) | 1 | 128 |

**未カバーのチップ**: SSG/DCSG/SCC/AY8930/SAA1099/OPLL系/ADPCM系/OPL4 AWM等、
本体側で実装済みだがプリセットバンクが存在しないチップ群がある。これらは
今後 staging 側でプリセット拡充が必要な領域として引き継ぐ。

---

## 5. `drumbank.json`フォーマット

`config_schema/drumbank.schema.json`を参照。1ドラムキット(prog)につき、
MIDIノート番号(`note`)ごとに`patch_bank`/`patch_prog`（参照する`hwbank.json`側の
音色）と`play_note`（実際に発音させるノート番号、`hwbank.json`側のtransposeは
無視して絶対指定）を持つ。

**OPL4 AWMのドラム**（`voice-parameter-reference.md`参照）は、`hwOp[0].WS`に
`128+GM標準ドラムノート番号`を設定した単一の`hwbank.json`パッチ1つだけで
GM標準ドラムキット全体を自動カバーする特殊な設計になっている点に注意
（他チップのように「ノートごとに個別パッチを用意する」必要がない）。

---

## 6. 新チップのプリセット追加時の手順（staging側の今後の作業）

1. `voice-parameter-reference.md`で対象チップが参照するフィールドを確認する
2. 変換元データ（実機ROMダンプ、SysEx等）があれば、既存の変換スクリプトを
   参考に新規スクリプトを作成する。無ければ手作業で`hwbank.json`を作成する
3. `hwbank.schema.json`でJSON構文・値域を検証する
4. 生成した`hwbank.json`を`banks/<グループ名>/`以下に配置し、`profile.json`の
   `banks.hw_banks[]`に登録する（`config/profiles/*.profile.json`参照）
5. 本体側（staging外）に実機/エミュレータで実際に鳴らして確認を依頼する

---

## 7. 連絡・確認が必要な事項

- 上記「今回のセッションで修正した点」のように、**本体側のチップドライバ実装が
  変更されると、プリセットデータの意味やスキーマも追従して変更が必要になる
  ことがある**。本体側の変更履歴（特に`hwbank.schema.json`・
  `voice-parameter-reference.md`の更新）は定期的に確認することを推奨する
- 未カバーのチップ（SSG/AY8930/SAA1099/OPLL系/ADPCM系/OPL4等）のプリセット
  拡充の優先順位は、本体側のロードマップと合わせて別途調整が必要
