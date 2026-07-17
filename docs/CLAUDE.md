# FITOM_staging プロジェクト引き継ぎドキュメント (for Claude Code)

このファイルはプロジェクトルート直下に置き、Claude Codeセッション開始時に
必ず最初に読むこと。複数マシンで作業するための運用ルールも記載している。

---

## 1. プロジェクト概要

- **FITOM_X**: コアライブラリ + 音色バンク + 変換ツール（別リポジトリ）
- **FITOM_staging**（本リポジトリ）: 動作環境・設定・プリセットバンク・セットアップスクリプト
- 対象: 複数のFM/PSG/PCM音源チップ（OPN系, OPM/OPZ系, OPL系, OPLL系, PSG系,
  ADPCM系, AWM）をエミュレータまたは実機経由で統一的に扱うMIDI音源システム

### ディレクトリ構成
```
config/
  profiles/*.json      プロファイル本体（hw_plugins + banks構成）
  fmemuif_*.json        FitomEmuIF用チップ構成サブプロファイル
config_schema/*.json   各種JSON Schemaファイル
banks/
  OPN/ OPM/ OPZ/ OPL2/ OPL3/ OPLL/ PSG/ PCM/ OPL4AWM/  チップ族ごとの音色バンク
  patches/               PatchBank（ToneLayer経由の複合パッチ）
  drums/                 DrumKit（GM2ノートマッピング）
  sw/                    SwPatch（パフォーマンスパッチ、ベロシティ感度/ビブラート等）
tools/voice_convert/    音色変換スクリプト群
docs/manuals/           エンドユーザー向けレファレンスマニュアル（本セッションで作成）
```

---

## 2. 現在のリポジトリ状態（このドキュメント作成時点）

### プロファイル一覧
| ファイル | 用途 |
|---|---|
| `unified_preset.profile.json` | 全チップ統合プロファイル（hw_banks 63件, sw_banks 7件, patch_banks 5件, drum_banks 15件） |
| `emu_opn.profile.json` | OPN専用（OPN/OPN2/OPNA/OPNB/OPNBB×1ずつ） |
| `emu_opl.profile.json` | OPL専用（OPL[rhythm]/Y8950/OPL2/OPL3/OPL4×1ずつ） |
| `emu_opm.profile.json` | OPM専用（OPM×2/OPZ×2） |
| `emu_opll.profile.json` | OPLL専用（OPLL/OPLL2[rhythm]/OPLLP/VRC7/OPLLX×1ずつ） |
| `emulator_opm.profile.json`ほか既存5件 | 旧・個別プロファイル（統合前からの遺産、現役利用中のため削除しないこと） |

### ドキュメント
`docs/manuals/`（本セッションで新規作成、`FITOM_X_preset_docs`から展開）:
`README.md`（起点）/ `swbank.md` / `drumkits.md` / `builtin_rhythm.md` /
`emu_profiles.md` / `opll_gm128_mapping.md` / `patches/*.md`（チップ族ごと）

---

## 3. 必ず守るべき設計原則・技術的知見

作業前に必ず目を通すこと。誤りを繰り返さないための教訓を含む。

### 3.1 hwbank.json のトップレベル構造
- `voice_patch_type`も`chip_group`もhwbank.json自体には**持たせない**。
  チップ族の指定は**プロファイル側の`hw_banks[].group`**（文字列、細かい分類
  可: `OPN2`/`OPZ`/`OPL3_2`/`OPL_RHY`/`OPLL`/`OPL3`/`SSG`/`ADPCMB`/`ADPCMA`/
  `AWM`等）で行う。

### 3.2 VoicePatchType（CC#0直接モード値）
| 値(10進) | 値(16進) | 名称 |
|---|---|---|
| 0 | 0x00 | 通常モード（PatchBank経由） |
| 17 | 0x11 | OPN2 |
| 26 | 0x1A | OPZ |
| 34 | 0x22 | OPL3_2 |
| 35 | 0x23 | OPL_RHY（OPLレジスタ疑似リズム、HwPatch経由） |
| 40 | 0x28 | OPLL |
| 48 | 0x30 | OPL3 |
| 64 | 0x40 | SSG（PSG系共有バンクの入口） |
| 81 | 0x51 | ADPCMB |
| 82 | 0x52 | ADPCMA |
| 84 | 0x54 | AWM |
| 112 | 0x70 | 内蔵リズム音源専用バンク（OPNA/OPLL、HwPatch不要） |

### 3.3 EGT/SR/RR変換規則（OPL/OPLL系のエンベロープ変換で必須）
- EGTビット=1（サステイン）: `SR=0`, `RR=r`（シフトなし）
- EGTビット=0（パーカッシブ）: `SR=r<<1`（4bit→5bit）, `RR=0`
- `ops[i].EGT`はOPL系では常に0（OPN専用のSSG-EG用、無関係）

### 3.4 PSG系共有バンク
全PSG系チップ（SSG/EPSG/DCSG/SAA/SCC）は`voice_patch_type=0x40`固定で
ロードされる共有バンクを使う。各パッチの`ext.target_voice_patch_type`
（`0x40`=SSG/`0x41`=EPSG/`0x42`=DCSG/`0x43`=SAA/`0x48`=SCC）で実際の対象
チップを指定する。波形選択があるのはEPSG（`ops[0].WS`=デューティ比0-8）と
SCC（`ops[0].WS`=波形メモリindex、0-127）のみ。

### 3.5 内蔵リズム音源（CC#0=112, `0x70`）— 2026年7月に`fixed_ch`廃止
- **旧**: `DrumNote::fixed_ch`で楽器（物理チャンネル）を指定
- **新**: `fixed_ch`はスキーマから完全に削除。**`patch_prog`がそのまま
  チャンネル番号として扱われる**（`hwProg`をそのままチャンネル番号として
  検証）。
- OPNA: 0=BD, 1=SD, 2=Top Cymbal, 3=HH, 4=Tom, 5=Rim Shot（レジスタ0x10
  bit0-5）
- OPLL: 0=HH, 1=Top Cymbal, 2=Tom, 3=SD, 4=BD
- OPL系疑似リズム（`VOICE_PATCH_OPL_RHY`=0x23）にも同様の「1チャンネル
  =1エントリ」制約が適用されるが、`ext.rhythm_ch`という**独立した軸**
  （`0=HH,1=CYM,2=TOM,3=SD,4=BD`）で管理されるため、同一楽器に複数の
  音色バリエーション（Pitch LFO版等）を別スロット(`patch_prog`)として
  持たせられる。

### 3.6 OPLL Built-In ROM音色
- `voice_patch_type=0x28(OPLL), hw_bank=0`は**ファイルを持たない機械合成
  領域**。`hwProg`の上位3bit=チップ種別（0=OPLL,1=OPLLX,2=OPLLP,3=VRC7）、
  下位4bit=ROM音色番号（0=無音,1-15=音色）。
- `patches[i].builtin`フィールドは**`role="builtin_swpatch_meta"`の
  バンクでのみ意味を持つ**（ユーザーがパフォーマンスパッチを紐づけるための
  領域、`unified_preset.profile.json`では`hw_banks[group=OPLL,bank=3]`）。
  通常のGM128パッチバンクでROM音色を「実際に鳴らすパッチ」として使いたい
  場合は、ToneLayerで直接`voice_patch_type=0x28, hw_bank=0, hw_prog=
  (variant<<4)|inst`を指定すればよい（`builtin`フィールドは使わない）。
- OPLL/OPLLX/OPLLP/VRC7 ROM音色名一覧、および代替用途コメント（"Also be
  used as..."等）は以下を参照（Copyright-freeレジスタダンプあり）:
  - https://sites.google.com/site/undocumentedsoundchips/yamaha/ymf281
  - https://sites.google.com/site/undocumentedsoundchips/yamaha/ym2423
  - https://github.com/plgDavid/misc/wiki/Copyright-free-OPLL(x)-ROM-patches

### 3.7 128パッチ制限
hwbank/patchbankの`prog`は`0-127`（`minimum:0, maximum:127`）。ファイル
統合時は必ず合計パッチ数を確認すること（実例: OPLL用SHS-10/PSS-170
バンクは既に125パッチ使用済みのため、MA-2 Preset2OP由来67パッチを追加
統合しようとして128パッチ超過が判明し断念した経緯がある）。

### 3.8 OPL4-AWM / ADPCM系はHwPatchを使わない
- AWM（`voice_patch_type=0x54`）・ADPCM-B（`0x51`）・ADPCM-A（`0x52`）は
  `SampleZonePatch`（`*.samplezonebank.json`または`*.pcmbank.json`）を
  使い、通常の`HwPatch`（`ops`配列）を経由しない。
- ドラムキットは`patchbank`層を経由せず、`voice_patch_type`を直接モード
  指定した`notes[]`から`hw_bank`/`hw_prog`を直接参照できる（`type:
  "direct"`のシンプルなdrumkitで全音域を1パッチにルーティングする例:
  `opl4awm.drumkit.json`）。

### 3.9 パッチ名の命名規則（2026年7月改訂）
- OPLLバリアント表記: 先頭に`[OPLL]`/`[OPLLX]`/`[OPLLP]`/`[VRC7]`の
  プレフィックス（型番は付けない）
- PSG系: 先頭に`[SSG]`/`[EPSG]`/`[DCSG]`/`[SAA]`/`[SCC]`のプレフィックス
  （`ext.target_voice_patch_type`から導出）
- SwPatchバリアント（Sustain/Decay/Vib等）を示す文字列は名前から削除し、
  末尾に`[sw_bank:sw_prog]`のポストフィクスを付与
- ToneLayerで他バンクを参照するだけのパッチ（OPLL GM128の一部等）は、
  参照先の実際のパッチ名をそのまま使う

### 3.10 opl2_merge.pyのALG設計
2つのOPL2バンクを合成して4OPパッチを作る際、各パッチのALG(cnt0/cnt1)は
**パッチ単位で各ソースバンクの元の値をそのまま個別に維持する**
（`--alg-a`/`--alg-b`未指定時）。`ConnectionSEL`は`ext.ALG_EXT`で別途
制御し、こちらは`0`固定（旧FITOM互換動作）。

---

## 4. 未解決・要確認事項

- `fmemuif_opl5.profile.json`/`fmemuif_opm_opz4.profile.json`/
  `fmemuif_opll5.profile.json`（新規作成した4チップ構成サブプロファイル）
  の**クロック値は一般的な標準値からの推測**（特にOPL4=33,868,800Hzは
  未検証）。実機/エンジン仕様に合わせた確認・調整が必要。
- `emu_opm.profile.json`/`emu_opll.profile.json`の`drum_banks`は「統合
  プロファイルのまま」全15件を引き継いでいる。他チップ用ドラムキット
  （ALSA/MA-2等）も含まれるため、絞り込みが必要か要検討。
- OPLL GM128（`gm_native_opll.patchbank.json`）は MA-2 Preset2OP由来が
  67/128と過半数。ソースを増やせる余地がないか、要継続検討。

---

## 5. マシン間コンテキスト共有ルール

複数マシンでClaude Codeを使ってこのプロジェクトを継続する際は、以下を
必ず守ること。

### 5.1 単一の真実の情報源（Single Source of Truth）
- **このファイル（`CLAUDE.md`、プロジェクトルート直下）が、マシン間で
  共有する唯一のコンテキストである。** 会話ログやチャット履歴はマシン間
  で共有されないため、引き継ぎたい情報は必ずこのファイルに書き出す。
- Gitリポジトリそのもの（コミット履歴・ファイル内容）が実際の作業成果
  の正であり、このファイルはそれを読み解くための「地図」である。

### 5.2 セッション開始時の手順（新しいマシン/新しいセッションの最初に必ず実行）
1. `git pull`で最新の状態を取得する。
2. この`CLAUDE.md`を読み、「4. 未解決・要確認事項」を確認する。
3. `git log --oneline -20`で直近のコミット履歴を確認し、他マシンでの
   作業内容を把握する。
4. 作業前に`git status`でuntracked/uncommittedな変更がないか確認する
   （前回のセッションで手元に残った未コミットの変更がある場合、他マシン
   では見えないため注意）。

### 5.3 セッション終了時の手順（作業を中断・完了するたびに必ず実行）
1. 変更したすべてのファイルをコミットする。コミットメッセージには
   「何を」「なぜ」変更したかを明記する（次のマシンで読む前提で書く）。
2. このセッションで新たに判明した設計原則・注意点があれば、
   「3. 必ず守るべき設計原則・技術的知見」に追記する。
3. 未解決のまま残った作業があれば、「4. 未解決・要確認事項」に追記する。
4. 完了した項目は「4. 未解決・要確認事項」から削除する。
5. `git push`して、他マシンから参照可能な状態にする。
6. **未コミットの変更を残したままセッションを終了しない。** 中途半端な
   状態で終える場合も、`WIP:`プレフィックス付きでコミットしておく。

### 5.4 同時作業の回避
- 同じブランチで複数マシンから同時に作業しない（コンフリクトの原因）。
  作業を開始する前に、他マシンでアクティブなセッションがないか確認する
  （Slack等のチームコミュニケーションツールでの一言宣言を推奨）。
- 大きな変更（プロファイル全体の再構成、スキーマ変更等）を行う際は、
  作業用ブランチを切ってから作業し、完了後にmainへマージする。

### 5.5 スキーマ変更の伝播
- `config_schema/*.json`はFITOM_X本体側から提供される。新しい
  `FITOM_X.zip`を受け取ったら、まず`config_schema/`配下を最新化してから
  他の作業を行う（スキーマの制約変更に気づかず古い前提で作業すると、
  後で大量の手戻りが発生する。本セッションでも`ops[i].WS`の範囲変更
  (`0-7`→`0-127`)、`fixed_ch`廃止、`ext.rhythm_ch`新設等、複数回の
  仕様変更が発生した）。
- スキーマ変更に気づいた場合は、変更内容と対応した差分をこの
  `CLAUDE.md`の「3. 必ず守るべき設計原則・技術的知見」に追記する。

### 5.6 検証を欠かさない
- 変更後は必ず該当するJSON Schemaでバリデーションを行い、
  `hw_banks`/`patch_banks`/`drum_banks`/`sw_banks`が参照する全ファイルの
  実在確認（孤立参照・欠落参照がないか）を行ってからコミットする。
