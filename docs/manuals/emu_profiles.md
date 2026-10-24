# エミュレータ専用プロファイル一覧

[← 目次に戻る](README.md)

`config/profiles/`にあるプロファイルです。どれもエミュレーターで音源チップを鳴らします。
特定の音源チップファミリーを集めたプロファイルと、実在した機種のサウンド構成を
模したプロファイルがあります。

## 共通事項

**バンク番号:** パッチバンク(CC#32)とドラムキット(Program Change)の番号は、全プロファイル
共通の番号です(`config/profiles/unified.bankset.json`)。全プロファイルが同じバンクを
読み込みますが、プロファイルに無いチップ向けのバンクは鳴りません。以下の各節には、
そのプロファイルで鳴るものだけを挙げています。

**通常モードのバンク0とドラムキット0:** CC#0=0, CC#32=0のパッチバンクと、リズムチャンネルの
Program Change 0のドラムキットは、プロファイルごとに、そのプロファイルのチップで鳴るものが
割り当てられています。バンク0に割り当てたパッチバンクは、全プロファイル共通の番号
(CC#32=1-6)でも選べます。

**鳴る音色・ノートの数:** 表の「鳴る音色」「鳴るノート」が「全128」のようになっていれば、
すべて鳴ります。「104/128」のようになっているものは、対応するチップがプロファイルに無い
ため、一部だけが鳴ります。ドラムキットの数には、割り当てる音の無いノートを含めていません。

**SoundFont:** どのプロファイルでも、MIDI入力ポートのうちプロファイルで決めた1つの
チャンネル15・16は、SoundFont(SF2)で鳴ります。SF2ファイルは付属していないため、
`unified.bankset.json`の`sf2_banks`に書かれた名前で`sf2/`フォルダに置いてください。

**ステレオ:** チップ構成の表で「左右1組」としているものは、同じチップ2個を左と右に分けて
1つの音源として扱い、パンポットを左右の音量比で表現します。

## チップファミリー別プロファイル

### 統合プリセットプロファイル

設定ファイル: `config/profiles/unified_preset.profile.json`

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| OPN2 | 1 | 7,159,090Hz | YMFMEngine | |
| OPNA | 1 | 7,159,090Hz | YMFMEngine | 内蔵リズム・ADPCM-B付き |
| OPNB | 1 | 7,159,090Hz | YMFMEngine | ADPCM-A・ADPCM-B付き |
| OPNBB | 1 | 7,159,090Hz | YMFMEngine | ADPCM-A・ADPCM-B付き |

チップ構成と鳴るパッチバンク・ドラムキットは、OPNエミュプロファイルと同じです。

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | necopn GM (OPN single-layer) | 全128 |
| 1 | necopn GM (OPN single-layer) | 全128 |

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | PSS-480 GM Drum Kit (OPNB ADPCM-A) | 全18 |
| 11 | OPNA Built-in Rhythm set | 全18 |
| 16 | PSS-590 Power Kit (OPNB ADPCM-A) | 全19 |
| 17 | PSS-590 GM Drum Kit (OPNB ADPCM-A) | 全19 |
| 18 | PSS-680 GM Drum Kit (OPNB ADPCM-A) | 全35 |
| 19 | RX5 GM Drum Kit (OPNB ADPCM-A) | 全20 |
| 20 | RX11/21L GM Drum Kit (OPNB ADPCM-A) | 全35 |
| 21 | PSS-480 GM Drum Kit (OPNB ADPCM-A) | 全18 |
| 22 | RX5 Extra Kit (OPNB ADPCM-A) | 全23 |
| 24 | PSS-590 Electronic Kit (OPNB ADPCM-A) | 全19 |
| 40 | PSS-680 Brush Kit (OPNB ADPCM-A) | 全35 |

### OPNエミュプロファイル

設定ファイル: `config/profiles/emu_opn.profile.json`

同じチップ構成の別版が2つあります。鳴るパッチバンクとドラムキットは、どれも同じです。
- `emu_fmgen_opn.profile.json`: エンジンをFmGenEngineにしたもの
- `emu_opn_stereo.profile.json`: 各チップを2個ずつ載せ、左右1組にしたもの

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| OPN2 | 1 | 7,159,090Hz | YMFMEngine | |
| OPNA | 1 | 7,159,090Hz | YMFMEngine | 内蔵リズム・ADPCM-B付き |
| OPNB | 1 | 7,159,090Hz | YMFMEngine | ADPCM-A・ADPCM-B付き |
| OPNBB | 1 | 7,159,090Hz | YMFMEngine | ADPCM-A・ADPCM-B付き |

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | necopn GM (OPN single-layer) | 全128 |
| 1 | necopn GM (OPN single-layer) | 全128 |

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | PSS-480 GM Drum Kit (OPNB ADPCM-A) | 全18 |
| 11 | OPNA Built-in Rhythm set | 全18 |
| 16 | PSS-590 Power Kit (OPNB ADPCM-A) | 全19 |
| 17 | PSS-590 GM Drum Kit (OPNB ADPCM-A) | 全19 |
| 18 | PSS-680 GM Drum Kit (OPNB ADPCM-A) | 全35 |
| 19 | RX5 GM Drum Kit (OPNB ADPCM-A) | 全20 |
| 20 | RX11/21L GM Drum Kit (OPNB ADPCM-A) | 全35 |
| 21 | PSS-480 GM Drum Kit (OPNB ADPCM-A) | 全18 |
| 22 | RX5 Extra Kit (OPNB ADPCM-A) | 全23 |
| 24 | PSS-590 Electronic Kit (OPNB ADPCM-A) | 全19 |
| 40 | PSS-680 Brush Kit (OPNB ADPCM-A) | 全35 |

### OPLエミュプロファイル

設定ファイル: `config/profiles/emu_opl.profile.json`

同じチップ構成の別版があります。鳴るパッチバンクとドラムキットは同じです。
- `emu_opl_stereo.profile.json`: Y8950を2個(左右1組)、OPL3を3個とOPL4を1個(OPL3どうしで
  1組、OPL3とOPL4のFM部で1組)載せたもの。OPL4のAWM部は1個のままです

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| Y8950 | 1 | 3,579,545Hz | YMFMEngine | 内蔵リズム有効、ADPCM-B付き |
| OPL3 | 1 | 14,318,180Hz | YMFMEngine | |
| OPL4 | 1 | 33,868,800Hz | YMFMEngine | AWM(PCM)部付き |

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | GM Standard Layered OPL2 | 全128 |
| 2 | GM Standard Layered OPL2 | 全128 |
| 3 | GM Standard Layered OPL3 | 全128 |
| 6 | GM Standard Layered OPL4AWM | 全128 |

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | OPL Built-in Rhythm (GM2 mapped) | 全21 |
| 2 | ALSA Preset 2OP set | 全47 |
| 3 | ALSA Preset 4OP set | 全47 |
| 4 | MA-2 Preset 2OP set | 全79 |
| 5 | MA-2 Basic 2OP set | 全79 |
| 6 | MA-2 Luminous 2OP set | 全79 |
| 7 | MA-2 MicroComputer 2OP set | 全79 |
| 8 | MA-2 Digital 2OP set | 全79 |
| 9 | MA-2 Acid 2OP set | 全79 |
| 10 | MA-2 Variant 2OP set | 全79 |
| 13 | OPL Built-in Rhythm (GM2 mapped) | 全21 |
| 15 | OPL4 AWM GM std kit | 全61(ノート27-87) |

### OPMエミュプロファイル

設定ファイル: `config/profiles/emu_opm.profile.json`

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| OPM | 4 | 3,579,545Hz | YMFMEngine | |

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | GM Standard Layered OPM | 全128 |
| 4 | GM Standard Layered OPM | 全128 |

このバンクのうち、OPZの拡張機能(波形選択・リバーブ・EGバイアス)を使う12音色は、
OPMでは拡張機能なしの音で鳴ります。

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | GM2 Standard Kit | 全61 |

GM2 Standard Kitは、上のパッチバンクの音色で鳴ります。

### OPZエミュプロファイル

設定ファイル: `config/profiles/emu_opz.profile.json`

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| OPZ | 4 | 3,579,545Hz | YMFMEngine | |

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | GM Standard Layered OPM | 全128 |
| 4 | GM Standard Layered OPM | 全128 |

OPM向けのバンクですが、OPZで鳴ります。

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | GM2 Standard Kit | 全61 |

GM2 Standard Kitは、上のパッチバンクの音色で鳴ります。

### OPLLエミュプロファイル

設定ファイル: `config/profiles/emu_opll.profile.json`

同じチップ構成の別版があります。鳴るパッチバンクとドラムキットは同じです。
- `emu_opll_stereo.profile.json`: OPLL・OPLLP・VRC7・OPLLXを2個ずつ載せ、左右1組にしたもの。
  OPLLEXは1個のままです

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| OPLL | 1 | 3,579,545Hz | YMFMEngine | 内蔵リズム有効 |
| OPLLP | 1 | 3,579,545Hz | YMFMEngine | |
| VRC7 | 1 | 3,579,545Hz | YMFMEngine | |
| OPLLX | 1 | 3,579,545Hz | YMFMEngine | |
| OPLLEX | 1 | 3,579,545Hz | DSAemuEngine | Y8960のOPLL部。チャンネルごとの定位を持ち、パンポットがそのまま効きます |

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | GM Standard Layered OPLL | 全128 |
| 5 | GM Standard Layered OPLL | 全128 |

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | OPLL Built-in Rhythm (COPLLRhythm, GM2 mapped) | 全21 |
| 12 | OPLL Built-in Rhythm (COPLLRhythm, GM2 mapped) | 全21 |

### PSGエミュプロファイル

設定ファイル: `config/profiles/emu_psg_stereo.profile.json`

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| DCSG | 2 | 3,579,545Hz | DSAemuEngine | 左右1組 |
| SCC | 2 | 3,579,545Hz | DSAemuEngine | 左右1組 |
| EPSG | 2 | 2,000,000Hz | EPSGemuEngine | 左右1組 |
| SSGS | 1 | 4,096,000Hz | EPSGemuEngine | ADPCM部付き |
| SSGS2 | 1 | 12,288,000Hz | EPSGemuEngine | ADPCM部付き |
| SSGS3 | 1 | 16,384,000Hz | EPSGemuEngine | |
| DSG | 2 | 1,000,000Hz | DSGemuEngine | 左右1組。内蔵リズム付き |
| SAA | 1 | 8,000,000Hz | SAASoundEngine | |

通常モード(CC#0=0)で鳴るパッチバンクはありません。音色は直接モード(PSG系はCC#0=64、
DSGはCC#0=68)で選びます。ドラムキット0も空です。

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 14 | DSG Built-in Rhythm (CDSGRhythm, GM2 mapped) | 全14 |
| 25 | PSS-680 GM Drum Kit (SSGS) | 全35 |
| 26 | RX11/21L GM Drum Kit (SSGS) | 全29 |

### FM全部盛りプロファイル

設定ファイル: `config/profiles/fmall.profile.json`

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| OPZ | 2 | 3,579,545Hz | YMFMEngine | 左右1組 |
| OPNBB | 2 | 7,159,090Hz | YMFMEngine | 左右1組。ADPCM-A・ADPCM-B付き |
| OPL3 | 1 | 14,318,180Hz | YMFMEngine | OPL4のFM部と左右1組 |
| OPL4 | 1 | 33,868,800Hz | YMFMEngine | FM部はOPL3と左右1組。AWM(PCM)部付き |
| OPLLEX | 1 | 3,579,545Hz | DSAemuEngine | Y8960のOPLL部、内蔵リズム有効。チャンネルごとの定位を持ち、パンポットがそのまま効きます |

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | GM Standard Layered OPL4AWM | 全128 |
| 1 | necopn GM (OPN single-layer) | 全128 |
| 2 | GM Standard Layered OPL2 | 全128 |
| 3 | GM Standard Layered OPL3 | 全128 |
| 4 | GM Standard Layered OPM | 全128 |
| 5 | GM Standard Layered OPLL | 全128 |
| 6 | GM Standard Layered OPL4AWM | 全128 |

CC#32=4はOPZで、CC#32=5はOPLLEXで鳴ります。

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | OPL4 AWM GM std kit | 全61(ノート27-87) |
| 2 | ALSA Preset 2OP set | 全47 |
| 3 | ALSA Preset 4OP set | 全47 |
| 4 | MA-2 Preset 2OP set | 全79 |
| 5 | MA-2 Basic 2OP set | 全79 |
| 6 | MA-2 Luminous 2OP set | 全79 |
| 7 | MA-2 MicroComputer 2OP set | 全79 |
| 8 | MA-2 Digital 2OP set | 全79 |
| 9 | MA-2 Acid 2OP set | 全79 |
| 10 | MA-2 Variant 2OP set | 全79 |
| 12 | OPLL Built-in Rhythm (COPLLRhythm, GM2 mapped) | 全21 |
| 15 | OPL4 AWM GM std kit | 全61(ノート27-87) |
| 16 | PSS-590 Power Kit (OPNB ADPCM-A) | 全19 |
| 17 | PSS-590 GM Drum Kit (OPNB ADPCM-A) | 全19 |
| 18 | PSS-680 GM Drum Kit (OPNB ADPCM-A) | 全35 |
| 19 | RX5 GM Drum Kit (OPNB ADPCM-A) | 全20 |
| 20 | RX11/21L GM Drum Kit (OPNB ADPCM-A) | 全35 |
| 21 | PSS-480 GM Drum Kit (OPNB ADPCM-A) | 全18 |
| 22 | RX5 Extra Kit (OPNB ADPCM-A) | 全23 |
| 24 | PSS-590 Electronic Kit (OPNB ADPCM-A) | 全19 |
| 40 | PSS-680 Brush Kit (OPNB ADPCM-A) | 全35 |

## OPLL用GM128パッチバンクの内訳

OPLLエミュプロファイルの通常モードパッチバンク
(`gm_layered_opll.patchbank.json`)は、以下3種類のソースを
組み合わせて128音色を構成しています。
詳細な対応表は[OPLL GM128パッチ対応表](opll_gm128_mapping.md)を
参照してください。

| ソース | 参照方法 | 件数 |
|---|---|---|
| OPLL Built-In ROM | `hw_bank=0`(チップ内蔵、機械合成) | 37 |
| SHS-10/PSS-170 | `hw_bank=2` | 24 |
| MA-2 Preset2OP | `hw_bank=4`(OPL2用バンクをOPLLとして直接参照) | 67 |

## 機種別プロファイル

実在した機種のサウンド構成を模したプロファイルです。搭載チップに応じて
複数のエミュレーションエンジンを組み合わせています。

### MSXプロファイル

設定ファイル: `config/profiles/emu_msx.profile.json`

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| OPLLEX | 1 | 3,579,545Hz | DSAemuEngine | MSX-MUSIC(Y8960のOPLL部で代用)、内蔵リズム有効 |
| Y8950 | 1 | 3,579,545Hz | DSAemuEngine | MSX-AUDIO、内蔵リズム有効、ADPCM-B付き |
| SSG | 1 | 2,000,000Hz | DSAemuEngine | 本体内蔵PSG |
| SCC+ | 1 | 3,579,545Hz | DSAemuEngine | SCC-I |
| OPM | 1 | 3,579,545Hz | YMFMEngine | SFG-05 |

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | GM Standard Layered OPLL | 全128 |
| 2 | GM Standard Layered OPL2 | 58/128 |
| 4 | GM Standard Layered OPM | 全128 |
| 5 | GM Standard Layered OPLL | 全128 |

MSX-MUSICには、OPLL・OPLL-P・OPLL-X・VRC7の4種類のROM音色を内蔵したOPLLEXを使って
います。このため、OPLL-P/OPLL-X/VRC7のROM音色を使う音色も鳴ります。
CC#32=2はY8950で鳴り、Y8950で再現できない音色は鳴りません。

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | OPLL Built-in Rhythm (COPLLRhythm, GM2 mapped) | 全21 |
| 2 | ALSA Preset 2OP set | 26/47 |
| 4 | MA-2 Preset 2OP set | 27/79 |
| 5 | MA-2 Basic 2OP set | 38/79 |
| 6 | MA-2 Luminous 2OP set | 35/79 |
| 7 | MA-2 MicroComputer 2OP set | 50/79 |
| 8 | MA-2 Digital 2OP set | 36/79 |
| 9 | MA-2 Acid 2OP set | 28/79 |
| 10 | MA-2 Variant 2OP set | 27/79 |
| 12 | OPLL Built-in Rhythm (COPLLRhythm, GM2 mapped) | 全21 |
| 13 | OPL Built-in Rhythm (GM2 mapped) | 全21 |

### MSX2++プロファイル

設定ファイル: `config/profiles/emu_msx2pp.profile.json`

Y8960カートリッジ1基分の構成です。OPLLEX/OPL2EX/SSGEX/SCCEXはチャンネルごとの
定位を持ち、パンポットがそのまま効きます。

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| OPLLEX | 1 | 3,579,545Hz | DSAemuEngine | Y8960のOPLL部、内蔵リズム有効 |
| OPL2EX | 1 | 3,579,545Hz | DSAemuEngine | Y8960のOPL2部、ADPCM-B付き |
| SSGEX | 1 | 1,789,772Hz | DSAemuEngine | Y8960のSSG部(YM2149×2) |
| SCCEX | 1 | 3,579,545Hz | DSAemuEngine | Y8960のSCC部 |
| OPM | 1 | 3,579,545Hz | YMFMEngine | Y8960のOPM部 |

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | GM Standard Layered OPLL | 全128 |
| 2 | GM Standard Layered OPL2 | 101/128 |
| 4 | GM Standard Layered OPM | 全128 |
| 5 | GM Standard Layered OPLL | 全128 |

CC#32=0・5はOPLLEXで鳴ります。OPLL系ROM音色(CC#0=40-43, CC#32=0)もOPLLEXで鳴り、
CC#0=44でも選択できます。

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | OPLL Built-in Rhythm (COPLLRhythm, GM2 mapped) | 全21 |
| 2 | ALSA Preset 2OP set | 全47 |
| 4 | MA-2 Preset 2OP set | 46/79 |
| 5 | MA-2 Basic 2OP set | 62/79 |
| 6 | MA-2 Luminous 2OP set | 52/79 |
| 7 | MA-2 MicroComputer 2OP set | 65/79 |
| 8 | MA-2 Digital 2OP set | 59/79 |
| 9 | MA-2 Acid 2OP set | 52/79 |
| 10 | MA-2 Variant 2OP set | 46/79 |
| 12 | OPLL Built-in Rhythm (COPLLRhythm, GM2 mapped) | 全21 |
| 13 | OPL Built-in Rhythm (GM2 mapped) | 10/21 |

### PC-88プロファイル

設定ファイル: `config/profiles/emu_pc88.profile.json`

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| OPN | 1 | 3,993,600Hz | YMFMEngine | サウンドボード |
| OPNA | 1 | 7,987,200Hz | YMFMEngine | サウンドボードII、内蔵リズム・ADPCM-B付き |
| OPM | 1 | 3,579,545Hz | YMFMEngine | |

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | necopn GM (OPN single-layer) | 全128 |
| 1 | necopn GM (OPN single-layer) | 全128 |
| 4 | GM Standard Layered OPM | 全128 |

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | OPNA Built-in Rhythm set | 全18 |
| 11 | OPNA Built-in Rhythm set | 全18 |

### PC-98プロファイル

設定ファイル: `config/profiles/emu_pc98.profile.json`

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| OPN | 1 | 3,993,600Hz | YMFMEngine | PC-9801-26K |
| OPNA | 1 | 7,987,200Hz | YMFMEngine | PC-9801-86、内蔵リズム・ADPCM-B付き |
| OPL3 | 1 | 14,318,180Hz | YMFMEngine | |
| Y8950 | 1 | 3,579,545Hz | YMFMEngine | 内蔵リズム有効、ADPCM-B付き |

ADPCM-B(CC#0=81)はOPNAとY8950の2チップにまたがる1デバイスとして扱われます。

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | necopn GM (OPN single-layer) | 全128 |
| 1 | necopn GM (OPN single-layer) | 全128 |
| 2 | GM Standard Layered OPL2 | 全128 |
| 3 | GM Standard Layered OPL3 | 全128 |

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | OPNA Built-in Rhythm set | 全18 |
| 2 | ALSA Preset 2OP set | 全47 |
| 3 | ALSA Preset 4OP set | 全47 |
| 4 | MA-2 Preset 2OP set | 全79 |
| 5 | MA-2 Basic 2OP set | 全79 |
| 6 | MA-2 Luminous 2OP set | 全79 |
| 7 | MA-2 MicroComputer 2OP set | 全79 |
| 8 | MA-2 Digital 2OP set | 全79 |
| 9 | MA-2 Acid 2OP set | 全79 |
| 10 | MA-2 Variant 2OP set | 全79 |
| 11 | OPNA Built-in Rhythm set | 全18 |
| 13 | OPL Built-in Rhythm (GM2 mapped) | 全21 |

### IBM PCプロファイル

設定ファイル: `config/profiles/emu_ibmpc.profile.json`

**チップ構成:**

| チップ | 数 | クロック | エンジン | 備考 |
|---|---|---|---|---|
| SAA | 2 | 8,000,000Hz | SAASoundEngine | Game Blaster/CMS、2枚で12ch1デバイス |
| OPL2 | 1 | 3,579,545Hz | YMFMEngine | AdLib、内蔵リズム有効 |
| OPL3 | 1 | 14,318,180Hz | YMFMEngine | Sound Blaster Pro2以降 |
| OPM | 1 | 3,579,545Hz | YMFMEngine | IBM Music Feature Card |
| DCSG | 1 | 3,579,545Hz | DSAemuEngine | PCjr/Tandy |

**通常モード(CC#0=0)のパッチバンク:**

| CC#32 | パッチバンク | 鳴る音色 |
|---|---|---|
| 0 | GM Standard Layered OPL3 | 全128 |
| 2 | GM Standard Layered OPL2 | 全128 |
| 3 | GM Standard Layered OPL3 | 全128 |
| 4 | GM Standard Layered OPM | 全128 |

**ドラムキット:**

| prog | ドラムキット | 鳴るノート |
|---|---|---|
| 0 | OPL Built-in Rhythm (GM2 mapped) | 全21 |
| 2 | ALSA Preset 2OP set | 全47 |
| 3 | ALSA Preset 4OP set | 全47 |
| 4 | MA-2 Preset 2OP set | 全79 |
| 5 | MA-2 Basic 2OP set | 全79 |
| 6 | MA-2 Luminous 2OP set | 全79 |
| 7 | MA-2 MicroComputer 2OP set | 全79 |
| 8 | MA-2 Digital 2OP set | 全79 |
| 9 | MA-2 Acid 2OP set | 全79 |
| 10 | MA-2 Variant 2OP set | 全79 |
| 13 | OPL Built-in Rhythm (GM2 mapped) | 全21 |
