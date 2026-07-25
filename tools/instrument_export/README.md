# Instrument Export Tools

`config/profiles/*.profile.json`(および参照先の`banks/`配下)から、MIDI
シーケンサー用のインストゥルメント定義ファイルを生成するツールです。

## 必要環境

Python 3.8 以上(標準ライブラリのみ使用)

## `generate_instruments.py`

```bash
# 全プロファイルを変換(既定の出力先: docs/instruments/)
python3 generate_instruments.py

# 特定のプロファイルのみ変換
python3 generate_instruments.py --profile config/profiles/unified_preset.profile.json

# 出力先を変更
python3 generate_instruments.py --out-dir /path/to/out
```

**出力形式**:

| 出力先 | 対応ソフト | 拡張子 |
|---|---|---|
| `docs/instruments/sekaiju/<profile>.ins` | Cakewalk / SONAR / Sekaiju | `.ins` (Shift_JIS) |
| `docs/instruments/domino/<profile>.xml` | DOMINO | `.xml` (Shift_JIS) |

## 変換ロジック

プロファイルの`banks`配下の各配列を、CC#0(Bank Select MSB)値ごとに
以下のように読み替えて音色一覧を組み立てます(対応関係は
`docs/CLAUDE.md` 3.2節、`docs/manuals/README.md`のバンクマップ表と同じ):

| ソース配列 | CC#0 | CC#32 | Prog | 参照ファイル形式 |
|---|---|---|---|---|
| `patch_banks[]` | 0(通常モード) | `bank` | `patches[].prog` | `*.patchbank.json` |
| `hw_banks[]` | `group`から決定(下表) | `bank` | `patches[].prog` | `*.hwbank.json` / `*.samplezonebank.json`(AWM) |
| `pcm_banks[]` | `group`から決定(ADPCMB=81/ADPCMA=82) | `bank` | `entries[].entry_no`(またはインデックス) | `*.pcmbank.json` |
| `drum_banks[]` | 112(内蔵リズム/ドラムキット) | `prog` | (ノート単位) | `*.drumkit.json` |

`hw_banks[].group` → CC#0 対応表:

| group | CC#0 | 備考 |
|---|---|---|
| `OPN2` / `OPN`(旧称) | 17 | |
| `OPZ` / `OPM`(旧称) | 26 | 旧プロファイルはOPM実チップ用の直接モード音色も同じOPZ用HwBankを共有 |
| `OPL3_2` / `OPL2`(旧称) | 34 | |
| `OPL_RHY` | 35 | |
| `OPLL` | 40 | `role: "builtin_swpatch_meta"`のバンクは音色として選択不可のため除外 |
| `OPL3` | 48 | |
| `SSG` | 64 | EPSG/DCSG/SAA/SCCも同じCC#0を共有(パッチ名の`[EPSG]`等プレフィックスで区別) |
| `AWM` | 84 | `*.samplezonebank.json` |

`OPN`/`OPM`/`OPL2`という旧称は統合前の個別プロファイル
(`emulator_*.profile.json`/`hw_*.profile.json`)だけが使っており、参照先の
`hwbank.json`実体が新プロファイル側でOPN2/OPZ/OPL3_2として参照されている
ファイルと同一であることを確認した上でエイリアスとして扱っています
(`GROUP_CC0_HW`定義部のコメント参照)。

`pcm_banks[]`(ADPCMB/ADPCMA)は`*.pcmbank.json`が`entries[]`を直接持つ場合と
`adpcm_json`で外部JSONを参照する場合(`banks/PCM/`配下の実データはこちらの
形式)があり、後者は参照先JSONの`entries`配列インデックスを`entry_no`として
自動採番します(`PatchManager`の実装に合わせた挙動)。

`drum_banks[]`は`type: "routed"`(ノートごとに個別の楽器名を持つ)の場合のみ
ノート名一覧(Sekaijuの`.Note Names`/DOMINOの`<Tone>`)を出力します。
`type: "direct"`(全域1パッチにルーティング、例: `opl4awm.drumkit.json`)は
個別の楽器名を持たないため、音色選択(1エントリ)のみ出力します。

`sw_banks[]`(パフォーマンスパッチ)は音色選択そのものではないため対象外です。

## 出力フォーマットの制約・未検証事項

- Sekaiju/Cakewalkの`.ins`ドラムキット部は、実機の`GM1/GM2 Instrument
  Definition File`(`GM1_GM2.ins`)にある`Key[MSB,PC]=<Note Names
  セクション>`という書式を参考に、1ドラムキット=1つの独立した
  Instrument Definition(`Patch[]`は固定1エントリ、`Key[<CC#0>,0]=...`)
  として出力しています。Sekaiju本体での実機能動作は未検証です。
- DOMINOの`<DrumSetList>`は`<PC Name="Drum Kits" PC="1">`の下に全ドラム
  キットを`<Bank MSB="112" LSB="<CC#32>">`として並べる構成にしています
  (Programでの切り替えは使わず、Bank(LSB)のみで切り替える設計)。
- どちらの出力も**セクション見出し名にプロファイル固有の英数字プレフィックス
  + `CC0=.. CC32=..`を機械的に付与**しており、一意性を優先しているため
  そのままではやや冗長な名前になります(Sekaiju側でユーザーが表示名を
  リネームすることを想定)。
