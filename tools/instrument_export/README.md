# Instrument Export Tools

`config/profiles/*.profile.json`(および参照先の`banks/`配下)から、MIDI
シーケンサー用のインストゥルメント定義ファイルを生成するツールです。

## 必要環境

Python 3.8 以上(標準ライブラリのみ使用)

## `generate_instruments.py`

```bash
# 既定の出力先(docs/instruments/)に生成
python3 generate_instruments.py

# 出力先を変更
python3 generate_instruments.py --out-dir /path/to/out
```

**対象プロファイル**: `TARGET_PROFILES`(スクリプト冒頭)で固定リスト
指定している統合設計プロファイル6件(`unified_preset`/`emu_opn`/
`emu_opl`/`emu_opm`/`emu_opll`/`fmall`)のみが対象です。統合前の個別
プロファイル(旧`emulator_*`/`hw_*`)は誰もメンテナンスしておらず統合後の
構成と矛盾していたため、2026年7月26日に`config/profiles/`ごと削除済み
です(`docs/CLAUDE.md` 3.30節参照)。

**出力形式**: 対象プロファイル全件を**1つのファイル**にまとめて出力します
(プロファイルごとにファイルを分けません。理由は後述)。

| 出力先 | 対応ソフト | 拡張子 |
|---|---|---|
| `docs/instruments/sekaiju/FITOM_X.ins` | Cakewalk / SONAR / Sekaiju | `.ins` (Shift_JIS) |
| `docs/instruments/domino/FITOM_X.xml` | DOMINO | `.xml` (Shift_JIS) |

## 変換ロジック

プロファイルの`banks`配下の各配列を、CC#0(Bank Select MSB)値ごとに
以下のように読み替えて音色一覧を組み立てます(対応関係は
`docs/CLAUDE.md` 3.2節、`docs/manuals/README.md`のバンクマップ表と同じ):

| ソース配列 | CC#0 | CC#32 | Prog | 参照ファイル形式 |
|---|---|---|---|---|
| `patch_banks[]` | 0(通常モード) | `bank` | `patches[].prog` | `*.patchbank.json` |
| `hw_banks[]` | `group`から決定(下表) | `bank` | `patches[].prog` | `*.hwbank.json` / `*.samplezonebank.json`(AWM) |
| `pcm_banks[]` | `group`から決定(ADPCMB=81/ADPCMA=82) | `bank` | `entries[].entry_no`(またはインデックス) | `*.pcmbank.json` |
| `drum_banks[]` | 112(内蔵リズム/ドラムキット) | 0固定 | `drum_banks[].prog`(キット選択) | `*.drumkit.json` |

`drum_banks[]`だけは他と軸が異なる点に注意: `prog`フィールドは**CC#32
ではなくProgram Change値**です(`profile.schema.json`が`drum_banks[]`を
「バンク番号概念なし、常にbank0固定でprogのみで選択」と定義している
通り)。つまりドラムキットはCC#0=112・CC#32=0固定の1バンクの中で、
Program Changeによってキットが切り替わります(GM2ドラムマップの
Bank MSB=120/121固定・PC違いでキット切替、という仕様と同型)。

`hw_banks[].group` → CC#0 対応表:

| group | CC#0 | 備考 |
|---|---|---|
| `OPN2` | 17 | |
| `OPZ` | 26 | |
| `OPL3_2` | 34 | |
| `OPL_RHY` | 35 | |
| `OPLL` | 40 | `role: "builtin_swpatch_meta"`のバンクは音色として選択不可のため除外 |
| `OPL3` | 48 | |
| `SSG` | 64 | EPSG/DCSG/SAA/SCCも同じCC#0を共有(パッチ名の`[EPSG]`等プレフィックスで区別) |
| `AWM` | 84 | `*.samplezonebank.json` |

`pcm_banks[]`(ADPCMB/ADPCMA)は`*.pcmbank.json`が`entries[]`を直接持つ場合と
`adpcm_json`で外部JSONを参照する場合(`banks/PCM/`配下の実データはこちらの
形式)があり、後者は参照先JSONの`entries`配列インデックスを`entry_no`として
自動採番します(`PatchManager`の実装に合わせた挙動)。

`drum_banks[]`は`type: "routed"`(ノートごとに個別の楽器名を持つ)の場合のみ
ノート名一覧(Sekaijuの`.Note Names`/DOMINOの`<Tone>`)を出力します。
`type: "direct"`(全域1パッチにルーティング、例: `opl4awm.drumkit.json`)は
個別の楽器名を持たないため、音色選択(1エントリ)のみ出力します。

`sw_banks[]`(パフォーマンスパッチ)は音色選択そのものではないため対象外です。

## 出力フォーマットの設計・制約・未検証事項

- Sekaiju/Cakewalkの`.ins`は、**1プロファイル=1つのInstrument
  Definitionセクション**として出力します(実機音源の実例`KORG_KROME.ins`・
  `Roland_SC-8850.ins`の`.Instrument Definitions`節が、1機材の中で
  持つ全バンクを`Patch[(MSB<<7)|LSB]=<Patch Namesセクション>`として
  列挙する構成になっていることに倣ったもの。バンクごとに別セクションを
  作ると、Sekaiju上でバンクの数だけ別々の「機材」として表示されてしまう
  ため、この構成は採用していません)。
- ドラムキットはCC#0=112・CC#32=0固定の1バンクしか持たないため、
  `Patch[]`は`(112<<7)|0`の1エントリのみ追加し、キットの切り替えは
  `Key[(112<<7)|0, <drum_banks[].prog>] = <Note Namesセクション>`という
  形でProgram Change値(第二引数)ごとに列挙します(実機の`GM1_GM2.ins`
  にある`[General MIDI Level 2 Drumsets]`セクション──Bank固定・PC違いで
  複数のドラムセットNote Namesを`Key[MSB,PC]`で切り替える構成──と
  同型)。`Drum[(112<<7)|0,*]=1`はドラムキットを持つプロファイルのみ
  1行だけ追加します。Sekaiju本体での実際の動作は未検証です。
- 対象プロファイル6件は、Sekaiju側は1つの`.ins`ファイルの中に6つの
  `.Instrument Definitions`セクション(=6つの機材)として、DOMINO側は
  1つの`.xml`ファイルの中に6つの`<Map>`要素として、まとめて出力します。
  `.Instrument Definitions`は1セクション=1機材である以上、プロファイル
  ごとにファイルを分ける必要はなく、DOMINOも`<Map>`タグを複数持てる
  仕様のため、1ファイルにまとめることでシーケンサー側に読み込む音源
  定義ファイルが1つで済みます。
- `.Instrument Definitions`/`<Map>`の見出し名(プロファイル表示名)には
  マルチバイト文字を使えないため、`generate_instruments.py`の
  `TARGET_PROFILES`辞書でプロファイルキーごとに`"FITOM_X Unified
  Profile"`のようなASCII名を個別に割り当てています
  (`config/profiles/*.profile.json`側の日本語`profile_name`は使いません)。
- DOMINOの`<DrumSetList>`も同じ理由で、ドラムキットごとに個別の
  `<PC Name="<キット名>" PC="<drum_banks[].prog + 1>">`タグを作り、その中に
  `<Bank MSB="112" LSB="0">`(常にLSB固定)を1つだけ持たせる構成にして
  います(DOMINOの`PC`属性は1〜128の1-indexedのため`+1`しています)。
- `.Patch Names`/`.Note Names`のセクション見出し名にはプロファイル固有の
  英数字プレフィックス(`config/profiles/*.profile.json`のファイル名、
  常にASCII)+`CC0=.. CC32=..`を機械的に付与しており、一意性を優先して
  いるためそのままではやや冗長な名前になります(これらは音色名一覧の
  名前空間であり、`.Instrument Definitions`の機材名(ASCII表示名)とは
  別物です)。
