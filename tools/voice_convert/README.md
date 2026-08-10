# Voice Conversion Tools

音色データを各シンセサイザーのフォーマットから FITOM_X の `hwbank.json` 形式に変換するツール群です。

## 必要環境

Python 3.8 以上 (標準ライブラリのみ使用)

## 変換ツール一覧

### `necopn_convert.py` — OPN グループ

**対応フォーマット**: N88-BASIC(86) OPNA/OPN ドライバ音色データ (`necopn.bin`)

```bash
python3 necopn_convert.py necopn.bin output.hwbank.json --bank 0 --group OPN
```

**フォーマット概要**:
- 128音色 × 64バイト (実データ50バイト + パディング14バイト)
- 各OP 6バイト: DT1/MUL, TL, KSR/AR, AM/DR, SR, SL/RR
- 格納順: M1(OP1) → C1(OP2) → M2(OP3) → C2(OP4) → FB/ALG → AMS/FMS
- 変換後 ops[] 順: [M1, C1, M2, C2]

---

### `vma_convert.py` — OPL2 / OPL3 グループ

**対応フォーマット**: MA-2 VMA ファイル (`*.vma`)

```bash
python3 vma_convert.py input.vma output.hwbank.json [--bank 0]
python3 vma_convert.py /path/to/vma/dir/ /path/to/out/ [--bank 0]
```

**フォーマット概要**:
- マジック `FM  ` + サイズ(big-endian) + 名前部(N×16B) + パラメータ部(N×26B)
- N=128(メロディ) or N=79(ドラム, MIDI note 27-105)
- byte1=0 → 2OP(OPL2), byte1=1 → 4OP(OPL3)
- パラメータはMA-2レジスタ形式(ビット位置がOPLと異なる)
- `ADP  ` マジックの ADPCM ファイルはスキップ
- 全opでAR=0(未使用プレースホルダ枠)のパッチは出力から除外(prog番号に
  欠番が生じうる)

---

### `alsa_convert.py` — OPL2 / OPL3 グループ

**対応フォーマット**: ALSA sbiload 音色バンク (`.sb`, `.o3`)

```bash
python3 alsa_convert.py std.sb std_opl2.hwbank.json
python3 alsa_convert.py std.o3 std_opl3.hwbank.json
python3 alsa_convert.py /path/to/dir/ /path/to/out/
```

**フォーマット概要**:
- `.sb` (OPL2): 128音色 × 52バイト, マジック `SBI\x1A` or `2OP\x1A`
- `.o3` (OPL3): 128音色 × 60バイト, マジック `4OP\x1A`、2OP×2の構造
- パラメータはOPLレジスタ直接値(変換不要)
- ドラムバンク: プログラム番号 = MIDI ノート番号 (35-81 に実データ)
- SBTimbre 拡張 (PercVoc, Transpos, PercPitch) をソフトパラメータとして保存

---

### `vmem_convert.py` — OPM グループ

**対応フォーマット**: DX27 / DX100 VMEM 32-Voice SysEx (`.syx`)

```bash
python3 vmem_convert.py input.syx output.hwbank.json [--bank 0]
python3 vmem_convert.py /path/to/syx/ /path/to/out/
```

**SysEx フォーマット**: `F0 43 0n 04 20 00 [4096バイト] CS F7`

**VMEM 1音色 (128バイト)**:
- P0-9: OP4 → M1 → ops[0]
- P10-19: OP2 → M2 → ops[2]
- P20-29: OP3 → C1 → ops[1]
- P30-39: OP1 → C2 → ops[3]
- P40-72: 共通パラメータ / 音色名 (10文字)

VMEM はオペレータを **OPM のレジスタスロット順 (M1,M2,C1,C2)** で格納する。
DX21/DX27/DX100/DX11 のパネル表記 OP1-4 は OPM のチェーン順 (op1=M1〜op4=C2) と
逆順であり、`OP4=M1 / OP3=C1 / OP2=M2 / OP1=C2` に対応する。

**主要変換**:

| VMEM パラメータ | 範囲 | OPM レジスタ | 変換式 |
|---|---|---|---|
| OUTPUT LEVEL | 0-99 | TL (0-127) | OL 20-99: `99 - OL` / OL 0-19: ルックアップ表 |
| （ALG由来） | — | TL に加算 | キャリアのみ `A_alg`（キャリア数 1/2/3/4 → 0/8/13/16） |
| KVS | P6[2:0] = 0-7 | TL に加算 / `VTL` | `A_kvs` 定数床 `8-KVS` を TL に加算。スイング分はモジュレータの `VTL` へ |
| AME | P6[6] | AM (0-1) | 直接 |
| EBS | P6[5:3] = 0-7 | `ops[].EGS` | 直接（下位3bitにそのまま格納する近似） |
| DECAY 1 LEVEL | 0-15 (15=減衰なし) | SL (0=減衰なし) | `15 - D1L` (極性反転) |
| FREQUENCY COARSE | P8[5:2] | MUL (0-15) | 直接 |
| DT2 | P8[1:0] | DT2 (0-3) | 直接 |
| RS | P9[4:3] | KSR (0-3) | 直接 |
| DETUNE | P9[2:0] = 0-6 (中央3) | DT1 (3bit、bit2が符号) | `3→0, 4/5/6→1/2/3, 2/1/0→5/6/7` |

`P+9` のビット配置は `[0:3][RS:2][DETUNE:3]`。DX21/DX100/DX11/TX81Z の実データ
全2560オペレータで最大値30(`0b11110`)・bit7-5が常に0・下位3bitに7が出現しない
ことから確定している。`P+8` の上位2bitも同様に常に0(固定周波数フラグではない)。

OUTPUT LEVEL → TL の対応表は
[この記事](https://nornand.hatenablog.com/entry/2020/11/21/201911)が出典。
OL 0-19 の非線形域は
`127,122,118,114,110,107,104,102,100,98,96,94,92,90,88,86,85,84,82,81`。
**同じブログのVolumeパラメータ用テーブルは別カーブなので流用してはならない**
(流用すると減衰量が最大30dB以上不足し、モジュレータが過大変調になる)。

`A_alg` は同記事の `V_TL = A_vol + A_alg + A_ol + A_ls + A_kvs + A_ebs` のうち
アルゴリズム由来の項で、**キャリアを N 本合成したときの振幅 N 倍を打ち消す
1/N 正規化**（TL は 0.75dB/step: 2本=8→6.00dB, 3本=13→9.75dB, 4本=16→12.00dB、
それぞれ `20·log₁₀(N)` = 6.02/9.54/12.04dB に対応）。合成後の音量に寄与するのは
キャリアだけなので**モジュレータには加算しない**。記事は TX81Z のパネル表記
op 番号で「ALG5 は op1,3 が 8」等と記述しているが、`OP1=C2 / OP2=M2 / OP3=C1 /
OP4=M1` で読み替えると OPM のキャリア集合と厳密に一致する。

---

### `fb01_convert.py` — OPM グループ

**対応フォーマット**: Yamaha FB-01 ROM ダンプ (`.dmp`)

```bash
python3 fb01_convert.py rom1.dmp rom1.hwbank.json [--bank 0]
python3 fb01_convert.py /path/to/dmp/ /path/to/out/
```

**ファイル構造**: 32バイトヘッダ + 64スロット × 48バイト

**OP順序**: `OP#0(M1)→ops[0], OP#1(C1)→ops[1], OP#2(M2)→ops[2], OP#3(C2)→ops[3]`
FB-01 の voice data はレジスタ生値をチェーン順で持つため、並び替えも値の
極性反転も不要（VMEM系のようなパネル値変換が入らない）。

---

### `tx81z_convert.py` — OPZ グループ (OPM 互換拡張)

**対応フォーマット**: Yamaha TX81Z 32-Voice VMEM SysEx (`.syx`)

```bash
python3 tx81z_convert.py input.syx output.hwbank.json [--bank 0]
python3 tx81z_convert.py /path/to/syx/ /path/to/out/
```

**SysEx フォーマット**: `F0 43 0n 04 [SH] [SL] [4096バイト] CS F7`
サイズは MIDI 7bit エンコード: `(SH<<7)|SL = 4096`

**OP順序**: VCED部・ACED部とも `vmem_convert.py` と同じレジスタスロット順
(`addr0/73→ops[0]`, `addr10/75→ops[2]`, `addr20/77→ops[1]`, `addr30/79→ops[3]`)。
D1L の極性反転・`P+9` のビット配置も VMEM 系と共通。

**TX81Z 固有拡張 (ACED)**:

| パラメータ | 意味 | FITOM_X フィールド |
|---|---|---|
| OPW | 波形選択 0-7 | `WS` |
| FIX | 固定周波数モード | `FIX` |
| FIXRG | 固定周波数レンジ 0-7 | `FIXRG` |
| FINE | 微調整 0-15 | `FINE` |
| EGSFT | EG シフト 0-7 | `EGSFT` |

---

## 共通仕様: ops[] の格納順

全グループで ops[] は **[M1, C1, M2, C2]** 順に統一されています。

```
ops[0] = M1 (Modulator 1 / Operator 1)
ops[1] = C1 (Carrier 1   / Operator 2)
ops[2] = M2 (Modulator 2 / Operator 3)
ops[3] = C2 (Carrier 2   / Operator 4)  ← 2OP グループでは使用しない
```

これは**アルゴリズム図のチェーン順**（ALG=0 なら `ops[0]→ops[1]→ops[2]→ops[3]`）
であり、**実機のレジスタスロット順 (M1,M2,C1,C2) とは異なる**。チップドライバ側
(`COPM::kMap = {0,2,1,3}`) がレジスタ書き込み時に並び替える。キャリア判定
(`kCarrierMask`) もこのチェーン順の添字で定義されているため、変換元が
レジスタスロット順で格納しているフォーマット（DX/TX81Z の VMEM 等）は
`ops[1]` と `ops[2]` を入れ替えて格納する必要がある。

## 共通仕様: OPL/OPLL 系の `AR`/`DR`/`SR` と `TL` のビット幅

OPL/OPL2/OPL3/OPLL 系（`vma_convert.py` / `alsa_convert.py` / `opll_convert.py`）
は、実機レジスタ値からの変換規則がフィールドによって異なる。

| フィールド | 実機レジスタ幅 | 格納する値 |
|---|---|---|
| `AR` / `DR` / `SR` | 4bit (0-15) | 実機値 `<< 1` (0-30) |
| `TL` | 6bit (0-63) | 実機値そのまま (0-63) |

`AR`/`DR`/`SR` は全チップ共通の 5bit「上位ビット表現」で保持し、ドライバ側
(`ar4()`) が `>> 1` して 4bit へ切り出す。一方 `TL` は全チップ共通の減衰量空間
(0.75dB/step) で保持し、ドライバ側 (`effTLToReg()`) はレンジのクランプのみで
スケーリングしないため、**`TL` を `<< 1` してはならない**（ステップ幅が 1.5dB に
読み替わって減衰量が 2 倍になり、実機レジスタ値 32 以上のオペレータは 6bit の
レンジ 47.25dB を超えて飽和し消音する）。

## 共通仕様: ハードウェアLFOパラメータは変換しない

変換元が持つ **内蔵(ハードウェア)LFO のパラメータは swbank へ変換しない**。
対象は DX/TX81Z VMEM の LFO SYNC / LFO SPEED / LFO DELAY / PMD / AMD /
LFO WAVE、FB-01 の LFO speed / AMD / PMD / LFO wave / LFO sync / LFO enable。

FITOM_X は HW LFO を使用しない（`COPM::updateVoice` がレジスタ `$38+ch` に 0 を
書いて無効化する）。swbank の `sw.*` はこれとは別機構の**ソフトLFO**の設定で、
`swbank.schema.json` の `sw` 説明にも「HW LFO はボイスパラメータから切り離され、
CC#1 Modulation として別途実装されている」と明記されている。さらに `sw.LFR>0` の
音色は **CC#1（モジュレーションホイール）が作用しなくなる**仕様
（`ISoundDevice.h` の `setCC1Modulation`）。HW LFO 設定を `sw.*` に流し込むと
「常時ビブラートが掛かり、かつモジュレーションが効かない」状態になる。

`SwPatch` のデフォルトは全フィールド 0（ソフトLFO無効）なので、swbank 側は
`sw` オブジェクトを出力しないのが正しい。TRANSPOSE のような HW LFO と無関係の
演奏パラメータ（→ `fine_transpose`）は従来どおり変換する。

`hw.PMS`/`hw.AMS`（レジスタ `$38+ch` の HW LFO 感度）は変換元の情報を保つため
値としては格納するが、上記の理由で OPM/OPZ では実際には参照されない。

## 共通仕様: ベロシティ感度 (`ops[].VTL`)

swbank の `ops[]` は `VTL` のみを出力する。他のフィールドは `FmSwOp` の既定値
（すべて 0）に任せる（`jsonToSwOp` は JSON に存在するキーだけを上書きする）。

| オペレータ | VTL |
|---|---|
| キャリア | `80` 固定（`performance_presets.swbank.json` の "VelScale Mid" と同値） |
| モジュレータ | VCED の `KVS`(0-7) から換算: `0, 42, 89, 127, 127, 127, 127, 127` |

キャリアのベロシティ応答は全パッチ均一にする（演奏性優先）というプロジェクトの
方針を優先し、キャリアでは `KVS` を使わない。モジュレータの `KVS` は音色の明るさの
ベロシティ追従そのものなので変換する。

`KVS` → `VTL` の値は、実機の
[`A_kvs = ((KVS × table[velocity-1] + (7-KVS)×16) >> 3) + 1`](https://nornand.hatenablog.com/entry/2021/01/01/153911)
（7bit整数+1bit小数、`table` は velocity 1-127 の 127 要素）のうち **velocity 依存の
スイング分**を、FITOM_X の VTL 補正
`-kGM2dB[vel] × VTL/254 ÷ 0.75`（`VoiceProcessor.cpp`）で velocity 32-127 の範囲に
ついて最小二乗近似したもの。`KVS` 1-2 は残差 ±0.5 ステップ以内でほぼ一致するが、
FITOM_X の VTL は変動幅を `VTL/2` に抑える設計のため **`KVS`≥3 は `VTL=127` で飽和**
し、実機ほど深い感度は表現できない（`KVS=7`・velocity 32 で約 17dB 不足）。

`A_kvs` には velocity=127 でも残る**定数床**がある（`table[126]=0` なので
`(7-KVS)×2+1` が残り、TL ステップに直すと `8 - KVS`）。これはベロシティに依存しない
静的な減衰なので、`KVS`>0 のオペレータの **TL に加算**する（スイング分は VTL が
受け持つ）。

`A_ls`（Level Scaling、ノート番号依存）に相当するフィールドは FITOM_X に存在しない
ため、`LS` は破棄する。FB-01 の `VEL_TL`（velocity sensitivity、3bit）は `KVS` とは
別パラメータで換算カーブが不明なため未変換（FB-01 は全 op で `VTL=80`）。

## 出力フォーマット: hwbank.json

```json
{
  "name":     "バンク名",
  "group":    "OPN|OPM|OPZ|OPL2|OPL3",
  "bank":     0,
  "op_count": 2 または 4,
  "source":   "元ファイル名とフォーマット",
  "patches": [
    {
      "prog": 0,
      "name": "音色名",
      "hw":   { "ALG": 2, "FB": 6, ... },
      "ops":  [ { "AR":31, "D1R":8, "TL":0, "MUL":1, ... }, ... ]
    }
  ]
}
```

---

### `opl2_merge.py` — OPL2→OPL3 バンク合成

**用途**: 2つの OPL2 (2OP) hwbank.json を組み合わせて OPL3 (4OP) バンクを生成します。

```bash
# 基本: MicroComputer (M1/C1) + Digital (M2/C2) → CON4=1 (独立並列)
python3 opl2_merge.py \\
    banks/OPL2/ma2_vma/MicroComputerNormalBank.hwbank.json \\
    banks/OPL2/ma2_vma/DigitalNormalBank.hwbank.json \\
    banks/OPL3/opl2_merge/MicroComputer_x_Digital.hwbank.json

# CON4=0 (完全直列) で合成
python3 opl2_merge.py BankA.hwbank.json BankB.hwbank.json out.hwbank.json --con4 0

# ドラムバンク合成も同様 (出力先はメロディ用と同じくOPL3/opl2_merge/)
python3 opl2_merge.py \\
    banks/OPL2/ma2_vma/BasicDrumBank.hwbank.json \\
    banks/OPL2/ma2_vma/DigitalDrumBank.hwbank.json \\
    banks/OPL3/opl2_merge/Basic_x_Digital_drums.hwbank.json
```

**CON4 (4OP 接続モード)**:

| CON4 | 接続 | 用途 |
|---|---|---|
| 0 | M1→C1→M2→C2 (完全直列) | 最大変調深度 |
| **1** | **(M1→C1) + (M2→C2) (独立並列)** | **バンク合成推奨・デフォルト** |
| 2 | M1→(C1 + M2→C2) | 部分並列 |
| 3 | M1→C1 + M2 + M2→C2 | 3出力混合 |

**FITOM_X フィールド対応**:

| フィールド | 内容 |
|---|---|
| `hw.FB` | Bank-A の FB (M1/C1ペア、独立3bit) |
| `hw.FB2` | Bank-B の FB (M2/C2ペア、独立3bit) |
| `hw.ALG` | 3bit統合 (bit0=CON1前半ペア接続, bit1=CON2後半ペア接続, bit2=ConnectionSEL) |
| `ops[0]` | Bank-A Mod (M1) |
| `ops[1]` | Bank-A Car (C1) |
| `ops[2]` | Bank-B Mod (M2) |
| `ops[3]` | Bank-B Car (C2) |

実機OPL3は前半・後半ペアそれぞれ独立したFBレジスタを持つため、`FB`/`FB2`は
6bitへのパック無しで、それぞれ独立したフィールドとして格納する
(`core/src/OPL_new.cpp` の COPL3 実装に完全準拠)。

`midi_note` 等のドラム固有フィールドは Bank-A から自動的に引き継がれます。

### `opll_convert.py` — OPLL グループ

**対応フォーマット**: YM2413(OPLL) 実機レジスタダンプ(8byte/音色)のテキスト書き起こし

```bash
python3 opll_convert.py \
  --pss140 pss140_patches.txt --pss140-names pss140_patches_names.txt \
  --shs10 shs10_patches.txt \
  banks/OPLL/opll_presets.hwbank.json
```

入力元 (banks/OPLL/opll_presets.hwbank.json の `source` フィールド参照):
- https://github.com/plgDavid/misc/blob/master/OPLL%20Synth%20Patches/pss140_patches.txt (`$XX $XX ...` 形式、1行8byte)
- https://github.com/plgDavid/misc/blob/master/OPLL%20Synth%20Patches/pss140_patches_names.txt (1行1名前、行順=prog順)
- https://github.com/plgDavid/misc/blob/master/OPLL%20Synth%20Patches/shs10_patches.txt (C配列風 `{0xXX,...},//名前` 形式)

**フォーマット概要**: YM2413カスタム音色レジスタ R#0-R#7(8byte)そのもの。
R#0/R#1=AM|VIB|EGT|KSR|MULT(モジュレータ/キャリア)、R#2=KSL1|TL1、
R#3=KSL2|DC|DM|FB、R#4/R#5=AR|DR、R#6/R#7=SL|RR。

**OPLL特有のSR/RR変換規則に注意**: OPLLは`updateVoice`+`updateKey`の2段階
書き込みで、キーオフ時は常にFITOMの`RR`値を直接RRレジスタへ書く
(OPL系のように`SR>0`のとき`RR`が無視されるわけではない)。そのため
実機EGTビットの値に関わらず常に`RR=変換元RRレジスタ値`(シフトなし)を
格納する必要がある(`SR`のみ実機EGTビットに応じて0または変換元RR<<1)。
詳細は `docs/voice-parameter-reference.md`「OPLL系」節、
`opll_convert.py` 冒頭コメント参照。

---

## n88basic_convert.py

N88-BASIC(86) OPN音色テキストファイル群を hwbank.json に変換する。

```
python3 n88basic_convert.py <src_dir> <dst.hwbank.json> [--names names.txt] [--bank-name "バンク名"]
```

- `src_dir`: 音色ファイルが入ったディレクトリ（ファイル名=16進2桁のprog番号）
- `--names`: パッチ名一覧テキスト（1行1名、ファイル数と一致する必要あり）
- `--bank-name`: バンク名（省略時: "N88-BASIC Preset"）

参考フォーマット: https://madscient.hatenablog.jp/entry/2013/07/08/051133
