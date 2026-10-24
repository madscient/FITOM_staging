# Instrument Export Tools

全プロファイルが共有するバンクセット`config/profiles/unified.bankset.json`(および参照先の
`banks/`配下)から、MIDIシーケンサー用のインストゥルメント定義ファイルを生成するツールです。

## 必要環境

Python 3.8 以上(標準ライブラリのみ使用)

## `generate_instruments.py`

```bash
# 既定の出力先(docs/instruments/)に生成
python3 generate_instruments.py

# 出力先を変更
python3 generate_instruments.py --out-dir /path/to/out
```

**出力は機材1つ(`FITOM_X`)だけです。** 全プロファイルが同じバンクセットを読むため、
CC#0/CC#32/Program Changeと音色名の対応はプロファイルによりません。プロファイルの
チップ構成によって鳴らない音色があるだけで、名前が別の音を指すことはありません。

**レイヤードバンク0・ドラムキット0**: 通常モード(CC#0=0, CC#32=0)のレイヤードバンク0と
ドラムキット0は、プロファイルごとに`bank_overrides`で別のファイルが敷かれます
(共有バンクセット側は空)。敷かれるのはどれもGM配列の音色・キットなので、リスト上は
`GM_STANDARD_MELODIC_FILE`(`necopn_gm.patchbank.json`、GM128標準音色名)・
`GM_STANDARD_DRUM_FILE`(`gm2_standard.drumkit.json`、GM2標準ドラムマップ)の名前で載せます。
実際に鳴る音色の名前とは一致しないことがあります。

| 出力先 | 対応ソフト | 拡張子 |
|---|---|---|
| `docs/instruments/sekaiju/FITOM_X.ins` | Cakewalk / SONAR / Sekaiju | `.ins` (Shift_JIS) |
| `docs/instruments/domino/FITOM_X.xml` | DOMINO | `.xml` (Shift_JIS) |

## 変換ロジック

バンクセットの各配列を、CC#0(Bank Select MSB)値ごとに以下のように読み替えて
音色一覧を組み立てます(対応関係は`CLAUDE.md`「CC#0とVoicePatchType」節、
`docs/manuals/README.md`のバンクマップ表と同じ):

| ソース配列 | CC#0 | CC#32 | Prog | 参照ファイル形式 |
|---|---|---|---|---|
| `patch_banks[]` | 0(通常モード) | `bank` | `patches[].prog` | `*.patchbank.json` |
| `hw_banks[]` | `group`から決定(下表) | `bank` | `patches[].prog` | `*.hwbank.json` / `*.samplezonebank.json`(AWM) |
| `pcm_banks[]` | `group`から決定(ADPCMB=81/ADPCMA=82/SSGS_ADPCM=85) | `bank` | `entries[].entry_no`(またはインデックス) | `*.pcmbank.json` |
| `drum_banks[]` | 120(ドラムキット、GM2 Percussion Bank相当) | 0固定 | `drum_banks[].prog`(キット選択) | `*.drumkit.json` |
| `sf2_banks[]` | 127(便宜的に割当。CC#0規約上の空き値) | `bank` | SF2ファイル内`preset`番号 | `*.sf2`(RIFF/SoundFont2) |

`drum_banks[]`だけは他と軸が異なります。`prog`フィールドは**CC#32ではなくProgram Change値**
で、ドラムキットはCC#0=120・CC#32=0固定の1バンクの中で、Program Changeによって切り替わります
(GM2ドラムマップのBank MSB=120/121固定・PC違いでキット切替、という仕様と同型)。
**CC#0=112はOPNA/OPLL/DSG内蔵リズム音源の直接選択専用で、通常のドラムキット選択とは別軸**
なので、ドラムキットのバンクには使いません。

`hw_banks[].group` → CC#0 対応表(`../FITOM_X/core/include/fitom/FITOMdefine.h`の
VOICE_PATCH_*定数):

| group | CC#0 | 備考 |
|---|---|---|
| `OPN` | 16 | VOICE_PATCH_OPN(YM2203等) |
| `OPN2` | 17 | VOICE_PATCH_OPN2(YM2612/YM2608等) |
| `OPM` | 25 | VOICE_PATCH_OPM(YM2151等) |
| `OPZ` | 26 | VOICE_PATCH_OPZ(YM2414) |
| `OPL` | 32 | VOICE_PATCH_OPL(YM3526等) |
| `OPL2` | 33 | VOICE_PATCH_OPL2(YM3812) |
| `OPL3_2` | 34 | VOICE_PATCH_OPL3_2(YMF262の2opモード) |
| `OPL_RHY` | 35 | |
| `OPLL` | 40 | `role: "builtin_swpatch_meta"`のバンクは音色として選択不可のため除外 |
| `OPLLP` | 41 | VOICE_PATCH_OPLLP(YMF281) |
| `OPLLX` | 42 | VOICE_PATCH_OPLLX(YM2423) |
| `VRC7` | 43 | VOICE_PATCH_VRC7(FS1001) |
| `OPLLEX` | 44 | VOICE_PATCH_OPLLEX(Y8960拡張OPLL部)。このgroupのプリセットバンクは無い(OPLLEXはOPLL系のユーザー音色バンクをフォールバックで受け入れる) |
| `OPL3` | 48 | |
| `SSG` | 64 | EPSG/DCSG/SAA/SCCも同じCC#0を共有(パッチ名の`[EPSG]`等プレフィックスで区別) |
| `AWM` | 84 | `*.samplezonebank.json` |

`pcm_banks[]`(ADPCMB/ADPCMA/SSGS_ADPCM)は`*.pcmbank.json`が`entries[]`を直接持つ場合と
`adpcm_json`で外部JSONを参照する場合(`banks/PCM/`配下の実データはこちらの形式)があり、
後者は参照先JSONの`entries`配列インデックスを`entry_no`として自動採番します
(`PatchManager`の実装に合わせた挙動)。`offsets_only: true`のバンクは特定チップ向けの
オフセット表で、FITOM_Xはここから音色を作らない(CC#32で選んでも鳴らない)ため載せません。

`drum_banks[]`は`type: "routed"`(ノートごとに個別の楽器名を持つ)の場合のみノート名一覧
(Sekaijuの`.Note Names`/DOMINOの`<Tone>`)を出力します。`type: "direct"`(全域1パッチに
ルーティング、例: `opl4awm.drumkit.json`)は個別の楽器名を持たないため、音色選択(1エントリ)
のみ出力します。

`sw_banks[]`(パフォーマンスパッチ)は音色選択そのものではないため対象外です。

### SF2(SoundFont2)バンク

`sf2_banks[]`(`FitomSf2IF`/FluidSynth経由)の各エントリは`{bank, file, sf2_bank}`の
3フィールドを持ちます。`file`はSF2ファイルへのパス(実体は`sf2/`配下、git管理外)、
`sf2_bank`はそのSF2ファイル自身が内部で持つバンク番号(GM相当=0・ドラム慣習=128等)、
`bank`はFITOM_X側でのCC#32相当のインデックスです。

バンク名・パッチ名はSF2ファイル自体(RIFF形式)の`pdta`チャンク内`phdr`(Preset Headers、
各38byte固定長のレコード配列)を直接パースして取得します(`parse_sf2_presets()`、標準
ライブラリの`struct`のみ使用)。`sf2_bank`と一致する`wBank`を持つプリセットのみを抽出し、
`wPreset`をProg、`achPresetName`を音色名として使います。同じSF2ファイルを複数の
`sf2_banks[]`エントリから参照するため、ファイルパス単位で`functools.lru_cache`により
パース結果をキャッシュします。`sf2/`の無いマシンで生成するとSF2の音色名が抜けるため、
生成は`sf2/`のあるマシンで行います。

### ファイルを持たない機械合成バンク(OPLL/DSGビルトイン音色・内蔵リズム)

以下は`hw_banks[]`/`drum_banks[]`のいずれにも現れない「ファイルを持たない機械合成バンク」で、
実際のパッチ名/楽器名はFITOM_X本体(`../FITOM_X`)のC++ソースにハードコードされています。
バンクセットの走査だけでは拾えないため、本スクリプトの定数に本体ソースから転記しています。

| バンク | CC#0 | CC#32 | Prog | 本体ソースの定義箇所 |
|---|---|---|---|---|
| OPLLビルトイン音色 | 40/41/42/43(下記参照) | 0固定 | `(variant<<4)\|instIndex`(0は無音のため未収録) | `core/src/PatchManager.cpp` `initOpllRomPatches()` の `kNames[4][16]` |
| OPLLEXビルトイン音色 | 44 | 0固定 | `(BANK<<4)\|instIndex`(BANK=0-3の4バンク全て、0は無音のため未収録) | 同上(音色データはOPLL系と同じ`kNames[4][16]`を共有) |
| DSGビルトイン音色 | 68 | 0固定 | `波形index*4+エンベロープindex`(0-19) | `core/src/PatchManager.cpp` `initDsgBuiltinPatches()` |
| OPLL内蔵リズム | 112 | 40固定 | 0-4(楽器番号) | `gui/bridge/FITOMBridge.cpp` `kOpllRhythmNames[]` |
| OPNA内蔵リズム | 112 | 17固定 | 0-5(楽器番号) | `gui/bridge/FITOMBridge.cpp` `kOpnaRhythmNames[]` |
| DSG内蔵リズム | 112 | 68固定 | 0-4(楽器番号) | `gui/bridge/FITOMBridge.cpp` `kDsgRhythmNames[]` |

**OPLLビルトイン音色はCC#0ごとに対応するチップの音色のみを出力します**
(`OPLL_BUILTIN_CC0_TO_VARIANT`)。

`PatchManager::resolveTriple()`はhw_bank(CC#32)==0でCC#0=40/41/42/43のいずれかが来ると
`resolveOpllRomVoice()`へ委譲し、委譲先はこの4値については渡されたvoicePatchTypeを捨てます。
実際に鳴らすチップはhwProgに埋め込まれたvariantSel(bit4-6)だけで決まるため、**ランタイム上は
CC#0=40/41/42/43のどれを選んでも同じProgに対して常に同じ結果**になります(CC#0=44のOPLLEXだけは
例外)。一方、FITOM_X本体・FITOM_patch_editorのパッチピッカーは
`PatchManager::getOpllRomPatches(voicePatchType)`経由でCC#0ごとに対応するvariantの音色のみへ
絞り込んで表示しており、MIDIシーケンサー側でも同じ体験(CC#0でチップが選択されているように
見せる)にするため、これに倣います。CC#0→variantの対応は`resolveOpllRomVoice`の`kVariantMap`/
`getOpllRomPatches`と同じです:

| CC#0 | チップ | variant | Prog範囲 |
|---|---|---|---|
| 40 | OPLL(/OPLL2) | 0 | 1-15 |
| 41 | OPLLP | 2 | 33-47 |
| 42 | OPLLX | 1 | 17-31 |
| 43 | VRC7 | 3 | 49-63 |

CC#0の数値順(40,41,42,43=OPLL,OPLLP,OPLLX,VRC7)とvariant番号順(0,1,2,3=OPLL,OPLLX,OPLLP,VRC7)
で**OPLLPとOPLLXの順序が入れ替わっている**点に注意してください。Prog番号は絞り込み後も実際の
hwProgエンコード値((variant<<4)|instIndex)をそのまま使います(0始まりの連番に振り直さない。
GUI側`FITOMBridge.cpp`の`info.prog = static_cast<int>(p.id)`と同じ扱い)。

#### OPLLEX(CC#0=44)だけは4バンクすべてを1バンクに並べる

`VOICE_PATCH_OPLLEX`(0x2c=44)はY8960の拡張OPLL部で、OPLL/OPLL-X/OPLL-P/VRC7の4バンク分の
ROMを1チップに内蔵しています(実機レジスタ0x40-0x48のチャンネル別BANK選択)。
`resolveOpllRomVoice()`はCC#0=44の場合に限り、hwProgのvariantSelを「OPLLEX自身のどのBANKか」
として解釈し、常にOPLLEX自身で発音します。

このためCC#0=44ではvariantの絞り込みを行わず、4バンク60音色(Prog 1-15/17-31/33-47/49-63)
すべてを1つのバンク(CC#32=0)に並べます。同一バンク内で同名の音色(`Vibraphone`等)が衝突する
ため、音色名にはBANK名(`[OPLL]`/`[OPLL-X]`/`[OPLL-P]`/`[VRC7]`)を前置して区別しています
(`.ins`側は書式上`[`が使えないため、`_ins_sanitize()`により`(OPLL)`のような丸括弧へ置換されます)。

標準4チップ側(CC#0=40/41/42/43)からも、対象チップが接続されていない場合はOPLLEXへ
フォールバックして発音されます。CC#0=44は「必ずOPLLEXで鳴らす」明示ルートという位置づけです。

内蔵リズムは、CC#0=112配下でも`drum_banks[]`由来の通常ドラムキット(CC#0=120)とは**別軸**です。
CC#32の意味が「対象チップ選択」に、Progの意味が「楽器(物理チャンネル)直接指定」になります
(`docs/manuals/builtin_rhythm.md`参照)。

## 出力フォーマットの設計・制約・未検証事項

- Sekaiju/Cakewalkの`.ins`は、機材を1つのInstrument Definitionセクションとして出力します
  (実機音源の実例`KORG_KROME.ins`・`Roland_SC-8850.ins`の`.Instrument Definitions`節が、
  1機材の中で持つ全バンクを`Patch[(MSB<<7)|LSB]=<Patch Namesセクション>`として列挙する構成に
  なっていることに倣ったもの。バンクごとに別セクションを作ると、Sekaiju上でバンクの数だけ
  別々の「機材」として表示されてしまう)。
- ドラムキットはCC#0=120・CC#32=0固定の1バンクしか持たないため、`Patch[]`は`(120<<7)|0`の
  1エントリのみ追加し、キットの切り替えは`Key[(120<<7)|0, <drum_banks[].prog>] = <Note Names
  セクション>`という形でProgram Change値(第二引数)ごとに列挙します(実機の`GM1_GM2.ins`に
  ある`[General MIDI Level 2 Drumsets]`セクション──Bank固定・PC違いで複数のドラムセット
  Note Namesを`Key[MSB,PC]`で切り替える構成──と同型)。`Drum[(120<<7)|0,*]=1`を1行だけ
  追加します。Sekaiju本体での実際の動作は未検証です。
- 機材名(`.Instrument Definitions`のセクション名、DOMINOの`<Map Name>`)はASCIIの`FITOM_X`
  (`MACHINE_NAME`)。Sekaiju/Cakewalkのセクション名にマルチバイト文字は使えません。
- DOMINOの`<DrumSetList>`は、ドラムキットごとに個別の`<PC Name="<キット名>"
  PC="<drum_banks[].prog + 1>">`タグを作り、その中に`<Bank MSB="120" LSB="0">`(常にLSB固定)を
  1つだけ持たせる構成です(DOMINOの`PC`属性は1〜128の1-indexedのため`+1`しています)。
- `.Patch Names`/`.Note Names`のセクション見出し名は、機材名+`CC0=.. CC32=..`(または
  `Drum Prog=..`)を機械的に付けたもので、一意性を優先しています。
