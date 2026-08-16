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
指定している統合設計プロファイル8件(`unified_preset`/`emu_opn`/
`emu_fmgen_opn`/`emu_opl`/`emu_opm`/`emu_opz`/`emu_opll`/`fmall`)のみが
対象です。`emu_opz`(旧`emu_opm`からOPM/OPZを分離)は2026年8月11日に
追加(`docs/CLAUDE.md` 3.49節参照)。`emu_opn_stereo`/`emu_opl_stereo`/
`emu_opll_stereo`(リニアステレオ化プロファイル)は意図的に対象外
(banks/bank_overridesが対応する非ステレオ版と完全に同一で、ステレオ化は
エンジン側の音声処理設定の違いのみのため、インストゥルメントリストの
内容が重複するだけになる。2026年8月11日、ユーザー指摘)。
統合前の個別プロファイル(旧`emulator_*`/`hw_*`)は誰もメンテナンスして
おらず統合後の構成と矛盾していたため、2026年7月26日に
`config/profiles/`ごと削除済みです(`docs/CLAUDE.md` 3.30節参照)。

**`banks`の外部ファイル参照 / `bank_overrides`への対応**(2026年7月29-31日、
`docs/CLAUDE.md` 3.32/3.33節参照): 全プロファイルの`banks`は現在
`config/profiles/unified.bankset.json`への文字列参照に統一されており、
各プロファイル固有の差分は`bank_overrides`(`banks`と同一スキーマ、識別
キー一致で置換・不一致で追加)で表現されます。本スクリプトは`banks`が
文字列の場合の解決、`bank_overrides`のマージ(識別キーはセクションごとに
異なる。`hw_banks`は`group`+`bank`、`pcm_banks`は`bank`+`chip`、
`drum_banks`は`prog`、それ以外は`bank`)の両方に対応しています。

**レイヤードバンク0・ドラムキット0のGM標準統一**: `bank_overrides`により
通常モード(CC#0=0,CC#32=0)のレイヤードバンク0(`patch_banks`bank=0)・
ドラムキット0(`drum_banks`prog=0)はプロファイルごとに実際に鳴るファイル
が異なります(例: `emu_opn`は`necopn_gm.patchbank.json`、`emu_opl`は
`gm_layered_opl2.patchbank.json`)。インストゥルメントリスト上はこの
プロファイル固有の違いを反映せず、`GM_STANDARD_MELODIC_FILE`
(`necopn_gm.patchbank.json`、GM128標準音色名)・`GM_STANDARD_DRUM_FILE`
(`gm2_standard.drumkit.json`、GM2標準ドラムマップ)で全プロファイル
共通に統一表示します(ユーザー判断、2026年7月31日)。実際に鳴る音と
インストゥルメントリストの表示が一致しないプロファイルがある点に
注意してください。

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
| `pcm_banks[]` | `group`から決定(ADPCMB=81/ADPCMA=82/SSGS_ADPCM=85) | `bank` | `entries[].entry_no`(またはインデックス) | `*.pcmbank.json` |
| `drum_banks[]` | 120(ドラムキット、GM2 Percussion Bank相当) | 0固定 | `drum_banks[].prog`(キット選択) | `*.drumkit.json` |
| `sf2_banks[]` | 127(便宜的に割当。CC#0規約上の空き値) | `bank` | SF2ファイル内`preset`番号 | `*.sf2`(RIFF/SoundFont2) |

`drum_banks[]`だけは他と軸が異なる点に注意: `prog`フィールドは**CC#32
ではなくProgram Change値**です(`profile.schema.json`が`drum_banks[]`を
「バンク番号概念なし、常にbank0固定でprogのみで選択」と定義している
通り)。つまりドラムキットはCC#0=120・CC#32=0固定の1バンクの中で、
Program Changeによってキットが切り替わります(GM2ドラムマップの
Bank MSB=120/121固定・PC違いでキット切替、という仕様と同型)。
**CC#0=112は後述のOPNA/OPLL内蔵リズム音源の直接選択専用であり、通常の
ドラムキット選択とは別軸**なので、ドラムキットのバンクには使いません
(2026年8月4日、ユーザー指摘により訂正。それ以前の版ではCC#0=112を
誤って両方の意味に使っていました)。

`hw_banks[].group` → CC#0 対応表(`../FITOM_X/core/include/fitom/
FITOMdefine.h`のVOICE_PATCH_*定数、2026年8月11日確認):

| group | CC#0 | 備考 |
|---|---|---|
| `OPN` | 16 | VOICE_PATCH_OPN(YM2203等)。2026年8月、同種チップのフォールバックルート新設で追加 |
| `OPN2` | 17 | VOICE_PATCH_OPN2(YM2612/YM2608等) |
| `OPM` | 25 | VOICE_PATCH_OPM(YM2151等)。2026年8月、OPM/OPZプロファイル分離で追加 |
| `OPZ` | 26 | VOICE_PATCH_OPZ(YM2414) |
| `OPL` | 32 | VOICE_PATCH_OPL(YM3526等)。2026年8月、フォールバックルート新設で追加 |
| `OPL2` | 33 | VOICE_PATCH_OPL2(YM3812) |
| `OPL3_2` | 34 | VOICE_PATCH_OPL3_2(YMF262の2opモード) |
| `OPL_RHY` | 35 | |
| `OPLL` | 40 | `role: "builtin_swpatch_meta"`のバンクは音色として選択不可のため除外 |
| `OPLLP` | 41 | VOICE_PATCH_OPLLP(YMF281)。2026年8月、フォールバックルート新設で追加 |
| `OPLLX` | 42 | VOICE_PATCH_OPLLX(YM2423) |
| `VRC7` | 43 | VOICE_PATCH_VRC7(FS1001) |
| `OPL3` | 48 | |
| `SSG` | 64 | EPSG/DCSG/SAA/SCCも同じCC#0を共有(パッチ名の`[EPSG]`等プレフィックスで区別) |
| `AWM` | 84 | `*.samplezonebank.json` |

`pcm_banks[]`(ADPCMB/ADPCMA/SSGS_ADPCM)は`*.pcmbank.json`が`entries[]`を直接持つ場合と
`adpcm_json`で外部JSONを参照する場合(`banks/PCM/`配下の実データはこちらの
形式)があり、後者は参照先JSONの`entries`配列インデックスを`entry_no`として
自動採番します(`PatchManager`の実装に合わせた挙動)。

`drum_banks[]`は`type: "routed"`(ノートごとに個別の楽器名を持つ)の場合のみ
ノート名一覧(Sekaijuの`.Note Names`/DOMINOの`<Tone>`)を出力します。
`type: "direct"`(全域1パッチにルーティング、例: `opl4awm.drumkit.json`)は
個別の楽器名を持たないため、音色選択(1エントリ)のみ出力します。

`sw_banks[]`(パフォーマンスパッチ)は音色選択そのものではないため対象外です。

### SF2(SoundFont2)バンク

`sf2_banks[]`(`FitomSf2IF`/FluidSynth経由)の各エントリは`{bank, file,
sf2_bank}`の3フィールドを持ち、`file`(SF2ファイルへのパス、実体は
`sf2/`ディレクトリ配下、リポジトリ内に同梱)・`sf2_bank`(そのSF2ファイル
自身が内部で持つバンク番号、GM相当=0・ドラム慣習=128等)・`bank`(FITOM_X
側でのCC#32相当のインデックス)という構造です(3.31/3.36節参照)。

バンク名・パッチ名はSF2ファイル自体(RIFF形式)の`pdta`チャンク内
`phdr`(Preset Headers、各38byte固定長のレコード配列)を直接パースして
取得しています(`parse_sf2_presets()`、外部ライブラリ非依存、標準
ライブラリの`struct`のみ使用)。`sf2_bank`と一致する`wBank`を持つ
プリセットのみを抽出し、`wPreset`をProg、`achPresetName`を音色名として
使います。同じSF2ファイルを複数の`sf2_banks[]`エントリ・複数プロファイル
から参照するケースが多い(例: `GeneralUser GS v1.471.sf2`は全7
プロファイル共通)ため、ファイルパス単位で`functools.lru_cache`により
パース結果をキャッシュしています(最大31MB程度のファイルを都度読み直す
のを避けるため)。

CC#0は127を割り当てています(2026年8月4日、ユーザー指示。FITOM_Xの
CC#0規約(3.2節)で未使用の値を便宜的に使用)。

### ファイルを持たない機械合成バンク(OPLLビルトイン音色・OPLLビルトイン
リズム・OPNAビルトインリズム)

以下3種類は`hw_banks[]`/`drum_banks[]`のいずれにも現れない
「ファイルを持たない機械合成バンク」で、実際のパッチ名/楽器名は
FITOM_X本体(`../FITOM_X`)のC++ソースにハードコードされています。
プロファイルJSONの走査だけでは拾えないため、本スクリプトの
`OPLL_ROM_NAMES`/`OPLL_RHYTHM_NAMES`/`OPNA_RHYTHM_NAMES`定数に
本体ソースから転記しています(2026年8月4日、ユーザー指摘により追加)。

| バンク | CC#0 | CC#32 | Prog | 本体ソースの定義箇所 |
|---|---|---|---|---|
| OPLLビルトイン音色 | 40/41/42/43(下記参照) | 0固定 | `(variant<<4)\|instIndex`(0は無音のため未収録) | `core/src/PatchManager.cpp` `initOpllRomPatches()` の `kNames[4][16]` |
| OPLLビルトインリズム | 112 | 40固定 | 0-4(楽器番号) | `gui/bridge/FITOMBridge.cpp` `kOpllRhythmNames[]` |
| OPNAビルトインリズム | 112 | 17固定 | 0-5(楽器番号) | `gui/bridge/FITOMBridge.cpp` `kOpnaRhythmNames[]` |

**OPLLビルトイン音色はCC#0ごとに対応するチップの音色のみを出力します**
(`OPLL_BUILTIN_CC0_TO_VARIANT`、2026年8月4日ユーザー指示により訂正)。

`VOICE_PATCH_OPLL`(0x28=40)/`VOICE_PATCH_OPLLP`(0x29=41)/
`VOICE_PATCH_OPLLX`(0x2a=42)/`VOICE_PATCH_VRC7`(0x2b=43)は別々の
voicePatchType定数として定義されている一方、`PatchManager::
resolveTriple()`はhw_bank(CC#32)==0でこの4値のいずれかが来ると
`resolveOpllRomVoice(hwProg, ...)`を呼ぶだけで、呼び出し時の
voicePatchType自体は関数に渡さない。実際に鳴らすチップはhwProgに
埋め込まれたvariantSel(bit4-6)だけで再決定されるため、**ランタイム上は
CC#0=40/41/42/43のどれを選んでも同じProgに対して常に同じ結果**になる
(コード上の事実)。

しかし、FITOM_X本体・FITOM_patch_editorのパッチピッカーGUIは
`PatchManager::getOpllRomPatches(voicePatchType)`経由でCC#0ごとに
対応するvariantの音色のみへ絞り込んで表示しており、ユーザーから
「MIDIシーケンサーでもこのGUIと同じ体験(CC#0でチップが選択されている
ように見せる)にしてほしい」との指示を受け、これに倣った。CC#0→variant
の対応は`resolveOpllRomVoice`の`kVariantMap`/`getOpllRomPatches`と同じ
(`tests/test_config.cpp`のユニットテストでも検証済み):

| CC#0 | チップ | variant | Prog範囲 |
|---|---|---|---|
| 40 | OPLL(/OPLL2) | 0 | 1-15 |
| 41 | OPLLP | 2 | 33-47 |
| 42 | OPLLX | 1 | 17-31 |
| 43 | VRC7 | 3 | 49-63 |

CC#0の数値順(40,41,42,43=OPLL,OPLLP,OPLLX,VRC7)とvariant番号順
(0,1,2,3=OPLL,OPLLX,OPLLP,VRC7)で**OPLLPとOPLLXの順序が入れ替わって
いる**点に注意(単純にCC#0の並び順通りにvariantが割り当たっているわけ
ではない)。Prog番号自体は絞り込み後も実際のhwProgエンコード値
((variant<<4)|instIndex)をそのまま使う(0始まりの連番に振り直さない。
GUI側`FITOMBridge.cpp`の`info.prog = static_cast<int>(p.id)`と同じ扱い)。

OPLLビルトインリズム・OPNAビルトインリズムは、CC#0=112配下でも
`drum_banks[]`由来の通常ドラムキット(CC#32=0固定、Progでキット選択)とは
**別軸**である点に注意してください。CC#32=17/40を選んだ場合のみ、
CC#32の意味が「対象チップ選択」に、Progの意味が「楽器(物理チャンネル)
直接指定」に変わります(`docs/manuals/builtin_rhythm.md`参照)。

この3種類は**プロファイルの実際のデバイス構成(搭載チップ)に関わらず、
全対象プロファイル共通で常に追加します**(`collect_builtin_entries()`
はプロファイルに依存する引数を取らない)。当初は`hw_plugins[].profile`
(`fmemuif_*.profile.json`等)が実際に搭載しているチップ
(`engines[].chips[].chip`)で絞り込む実装にしていたが、「`unified_preset`
に登録されていない」というユーザー指摘を受けて撤廃した(2026年8月8日、
docs/CLAUDE.md 3.43節)。全対象プロファイルが共通の`unified.bankset.json`
を参照し、実際のデバイス構成に含まれないバンクエントリも変わらず表示
する(単に発音しないだけで実害がない)という設計原則(docs/CLAUDE.md
3.32節)に、他のhw_banks[]由来エントリ(例: OPLL専用チップを持たない
`unified_preset`でも通常のOPLLプリセットバンクCC#0=40 CC#32=1/2/4は
表示される)と同じ扱いに揃えている。

## 出力フォーマットの設計・制約・未検証事項

- Sekaiju/Cakewalkの`.ins`は、**1プロファイル=1つのInstrument
  Definitionセクション**として出力します(実機音源の実例`KORG_KROME.ins`・
  `Roland_SC-8850.ins`の`.Instrument Definitions`節が、1機材の中で
  持つ全バンクを`Patch[(MSB<<7)|LSB]=<Patch Namesセクション>`として
  列挙する構成になっていることに倣ったもの。バンクごとに別セクションを
  作ると、Sekaiju上でバンクの数だけ別々の「機材」として表示されてしまう
  ため、この構成は採用していません)。
- ドラムキットはCC#0=120・CC#32=0固定の1バンクしか持たないため、
  `Patch[]`は`(120<<7)|0`の1エントリのみ追加し、キットの切り替えは
  `Key[(120<<7)|0, <drum_banks[].prog>] = <Note Namesセクション>`という
  形でProgram Change値(第二引数)ごとに列挙します(実機の`GM1_GM2.ins`
  にある`[General MIDI Level 2 Drumsets]`セクション──Bank固定・PC違いで
  複数のドラムセットNote Namesを`Key[MSB,PC]`で切り替える構成──と
  同型)。`Drum[(120<<7)|0,*]=1`はドラムキットを持つプロファイルのみ
  1行だけ追加します。Sekaiju本体での実際の動作は未検証です。
- 対象プロファイル8件は、Sekaiju側は1つの`.ins`ファイルの中に8個の
  `.Instrument Definitions`セクション(=8個の機材)として、DOMINO側は
  1つの`.xml`ファイルの中に8個の`<Map>`要素として、まとめて出力します。
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
  `<Bank MSB="120" LSB="0">`(常にLSB固定)を1つだけ持たせる構成にして
  います(DOMINOの`PC`属性は1〜128の1-indexedのため`+1`しています)。
- `.Patch Names`/`.Note Names`のセクション見出し名にはプロファイル固有の
  英数字プレフィックス(`config/profiles/*.profile.json`のファイル名、
  常にASCII)+`CC0=.. CC32=..`を機械的に付与しており、一意性を優先して
  いるためそのままではやや冗長な名前になります(これらは音色名一覧の
  名前空間であり、`.Instrument Definitions`の機材名(ASCII表示名)とは
  別物です)。
