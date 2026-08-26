# エミュレータ専用プロファイル一覧

[← 目次に戻る](README.md)

統合プロファイル(`unified_preset.profile.json`)から、特定の音源
チップファミリーに絞ったプロファイルです。1つのプロファイルに
複数の同系統チップをまとめてロードします。

2026年7月29日以降、`banks`セクションは全プロファイル共通の
`config/profiles/unified.bankset.json`を参照する構成に変更されました
（`docs/CLAUDE.md` 3.32節参照）。これに伴い、以下のパッチバンク
(CC#32)・ドラムキット(prog)の番号は、各プロファイル固有のローカル番号
ではなく`unified.bankset.json`側の番号（全プロファイル共通）です。
各プロファイルは実際には`unified.bankset.json`の全エントリを内部で
ロードしますが、以下の各節に挙げているのはそのプロファイルが持つ
チップ構成で**実際に発音するもの**のみです（他チップ向けのエントリも
ロードはされますが、対応するチップが無いため単に鳴らないだけです）。

## OPNエミュプロファイル

設定ファイル: `config/profiles/emu_opn.profile.json`

**チップ構成:**
- OPN(3,579,545Hz)
- OPN2(7,159,090Hz)
- OPNA(7,159,090Hz)
- OPNB(7,159,090Hz)
- OPNBB(7,159,090Hz)

**通常モード(CC#0=0, CC#32=1)のパッチバンク:**
- `necopn_gm.patchbank.json`

**ドラムキット(prog16-22, 24, 40のうち以下9種):**
- PSS-560 GM Drum Kit (OPNB) [prog21]
- PSS-590 GM Drum Kit (OPNB) [prog17]
- PSS-680 GM Drum Kit (OPNB) [prog18]
- RX5 GM Drum Kit (OPNB) [prog19]
- RX11/21L GM Drum Kit (OPNB) [prog20]
- RX5 Extra Kit (OPNB) [prog22]
- PSS-590 Power Kit (OPNB) [prog16, GM2 PC#17相当]
- PSS-590 Electronic Kit (OPNB) [prog24, GM2 PC#25相当]
- PSS-680 Brush Kit (OPNB) [prog40, GM2 PC#41相当]

収録ドラムキット総数: 9種類

## OPLエミュプロファイル

設定ファイル: `config/profiles/emu_opl.profile.json`

**チップ構成:**
- OPL(3,579,545Hz)
- Y8950(3,579,545Hz)
- OPL2(3,579,545Hz)
- OPL3(14,318,180Hz)
- OPL4(33,868,800Hz)

**通常モード(CC#0=0, CC#32=2)のパッチバンク:**
- `gm_layered_opl2.patchbank.json`

**ドラムキット(prog13):**
- OPL Built-in set

収録ドラムキット総数: 1種類

## OPMエミュプロファイル

設定ファイル: `config/profiles/emu_opm.profile.json`

**チップ構成:**
- OPM(3,579,545Hz)
- OPM(3,579,545Hz)
- OPZ(3,579,545Hz)
- OPZ(3,579,545Hz)

**通常モード(CC#0=0, CC#32=4)のパッチバンク:**
- `gm_layered_opm.patchbank.json`

**ドラムキット:** ALSA/MA-2/OPNA/OPLL/OPL Built-in/OPL4-AWM各種
(prog2-13,15)に加え、PSS-590/680・RX5・RX11/21L・PSS-560のADPCM-A GM
ドラムキット(prog17-22)、およびGM2バリエーション相当のPSS-590
Power/Electronic Kit(prog16,24)・PSS-680 Brush Kit(prog40)を収録。

収録ドラムキット総数: 22種類

## OPLLエミュプロファイル

設定ファイル: `config/profiles/emu_opll.profile.json`

**チップ構成:**
- OPLL(3,579,545Hz、ビルトインリズム有効)
- OPLLP(3,579,545Hz)
- VRC7(3,579,545Hz)
- OPLLX(3,579,545Hz)

**通常モード(CC#0=0, CC#32=5)のパッチバンク:**
- `gm_layered_opll.patchbank.json`

**ドラムキット:** OPLL Built-in set(prog12)に加え、ALSA/MA-2/OPNA/OPL
Built-in/OPL4-AWM各種(prog2-13,15)、PSS-590/680・RX5・RX11/21L・
PSS-560のADPCM-A GMドラムキット(prog17-22)、およびGM2バリエーション
相当のPSS-590 Power/Electronic Kit(prog16,24)・PSS-680 Brush
Kit(prog40)を収録。

収録ドラムキット総数: 23種類

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

| チップ | クロック | エンジン | 備考 |
|---|---|---|---|
| OPLL | 3,579,545Hz | DSAemuEngine | MSX-MUSIC、ビルトインリズム有効 |
| Y8950 | 3,579,545Hz | DSAemuEngine | MSX-AUDIO、ビルトインリズム有効 |
| SSG | 2,000,000Hz | DSAemuEngine | 本体内蔵PSG |
| SCC+ | 3,579,545Hz | DSAemuEngine | SCC-I |
| OPM | 3,579,545Hz | YMFMEngine | SFG-05 |

**通常モード(CC#0=0, CC#32=0)のパッチバンク:** `gm_layered_opll.patchbank.json`

**ドラムキット(prog0):** OPLL Built-in set

OPLL-P/OPLL-X/VRC7のROM音色を参照するパッチは、対応するチップを
搭載していないため発音しません。

### MSX2++プロファイル

設定ファイル: `config/profiles/emu_msx2pp.profile.json`

**チップ構成:**

| チップ | クロック | エンジン | 備考 |
|---|---|---|---|
| OPLLEX×2 | 3,579,545Hz | Y8960emuEngine | リニアステレオ、ビルトインリズム有効 |
| OPL2EX×2 | 3,579,545Hz | Y8960emuEngine | リニアステレオ |
| SSG×2 | 2,000,000Hz | DSAemuEngine | リニアステレオ |
| DCSG×2 | 3,579,545Hz | DSAemuEngine | リニアステレオ |
| SCC | 3,579,545Hz | DSAemuEngine | |

**通常モード(CC#0=0, CC#32=0)のパッチバンク:** `gm_layered_opll.patchbank.json`

**ドラムキット(prog0):** OPLL Built-in set

OPLL系ROM音色(CC#0=40-43, CC#32=0)はOPLLEXへフォールバックしないため
発音しません。OPLLEX自身のROM音色はCC#0=44で選択します。

### PC-88プロファイル

設定ファイル: `config/profiles/emu_pc88.profile.json`

**チップ構成:**

| チップ | クロック | エンジン | 備考 |
|---|---|---|---|
| OPN | 3,993,600Hz | YMFMEngine | サウンドボード |
| OPNA | 7,987,200Hz | YMFMEngine | サウンドボードII、ビルトインリズム/ADPCM-B付き |
| OPM | 3,579,545Hz | YMFMEngine | |

**通常モード(CC#0=0, CC#32=0)のパッチバンク:** `necopn_gm.patchbank.json`

**ドラムキット(prog0):** OPNA Built-in set

### PC-98プロファイル

設定ファイル: `config/profiles/emu_pc98.profile.json`

**チップ構成:**

| チップ | クロック | エンジン | 備考 |
|---|---|---|---|
| OPN | 3,993,600Hz | YMFMEngine | PC-9801-26K |
| OPNA | 7,987,200Hz | YMFMEngine | PC-9801-86、ビルトインリズム/ADPCM-B付き |
| OPL3 | 14,318,180Hz | YMFMEngine | |
| Y8950 | 3,579,545Hz | YMFMEngine | ビルトインリズム有効 |

**通常モード(CC#0=0, CC#32=0)のパッチバンク:** `necopn_gm.patchbank.json`

**ドラムキット(prog0):** OPNA Built-in set

ADPCM-B(CC#0=81)はOPNAとY8950の2チップにまたがる1デバイスとして扱われます。

### IBM PCプロファイル

設定ファイル: `config/profiles/emu_ibmpc.profile.json`

**チップ構成:**

| チップ | クロック | エンジン | 備考 |
|---|---|---|---|
| SAA×2 | 8,000,000Hz | SAASoundEngine | Game Blaster/CMS、2枚で12ch1デバイス |
| OPL2 | 3,579,545Hz | YMFMEngine | AdLib、ビルトインリズム有効 |
| OPL3 | 14,318,180Hz | YMFMEngine | Sound Blaster Pro2以降 |
| OPM | 3,579,545Hz | YMFMEngine | IBM Music Feature Card |
| DCSG | 3,579,545Hz | DSAemuEngine | PCjr/Tandy |

**通常モード(CC#0=0, CC#32=0)のパッチバンク:** `gm_layered_opl3.patchbank.json`

**ドラムキット(prog0):** OPL Built-in set
