# エミュレータ専用プロファイル一覧

[← 目次に戻る](README.md)

統合プロファイル(`unified_preset.profile.json`)から、特定の音源
チップファミリーに絞ったプロファイルです。1つのプロファイルに
複数の同系統チップをまとめてロードします。

## OPNエミュプロファイル

設定ファイル: `config/profiles/emu_opn.profile.json`

**チップ構成:**
- OPN(3,579,545Hz)
- OPN2(7,159,090Hz)
- OPNA(7,159,090Hz)
- OPNB(7,159,090Hz)
- OPNBB(7,159,090Hz)

**通常モード(CC#0=0, CC#32=0)のパッチバンク:**
- `necopn_gm.patchbank.json`

**ドラムキット(prog0-5, 16, 24, 40):**
- PSS-560 GM Drum Kit (OPNB)
- PSS-590 GM Drum Kit (OPNB)
- PSS-680 GM Drum Kit (OPNB)
- RX5 GM Drum Kit (OPNB)
- RX11/21L GM Drum Kit (OPNB)
- RX5 Extra Kit (OPNB)
- PSS-590 Power Kit (OPNB) [GM2 PC#17相当]
- PSS-590 Electronic Kit (OPNB) [GM2 PC#25相当]
- PSS-680 Brush Kit (OPNB) [GM2 PC#41相当]

収録ドラムキット総数: 9種類

## OPLエミュプロファイル

設定ファイル: `config/profiles/emu_opl.profile.json`

**チップ構成:**
- OPL(3,579,545Hz)
- Y8950(3,579,545Hz)
- OPL2(3,579,545Hz)
- OPL3(14,318,180Hz)
- OPL4(33,868,800Hz)

**通常モード(CC#0=0, CC#32=0)のパッチバンク:**
- `gm_layered_opl2.patchbank.json`

**ドラムキット(prog0):**
- OPL Built-in set

収録ドラムキット総数: 1種類

## OPMエミュプロファイル

設定ファイル: `config/profiles/emu_opm.profile.json`

**チップ構成:**
- OPM(3,579,545Hz)
- OPM(3,579,545Hz)
- OPZ(3,579,545Hz)
- OPZ(3,579,545Hz)

**通常モード(CC#0=0, CC#32=0)のパッチバンク:**
- `gm_layered_opm.patchbank.json`

**ドラムキット:** ALSA/MA-2/OPNA/OPLL/OPL Built-in/OPL4-AWM各種
(prog2-13,15)に加え、PSS-590/680・RX5・RX11/21L・PSS-560のADPCM-A GM
ドラムキット(prog17-22)、およびGM2バリエーション相当のPSS-590
Power/Electronic Kit(prog16,24)・PSS-680 Brush Kit(prog40)を収録。

収録ドラムキット総数: 22種類

## OPLLエミュプロファイル

設定ファイル: `config/profiles/emu_opll.profile.json`

**チップ構成:**
- OPLL(3,579,545Hz)
- OPLL2(3,579,545Hz)
- OPLLP(3,579,545Hz)
- VRC7(3,579,545Hz)
- OPLLX(3,579,545Hz)

**通常モード(CC#0=0, CC#32=0)のパッチバンク:**
- `gm_layered_opll.patchbank.json`

**ドラムキット:** OPLL Built-in set(prog0)に加え、ALSA/MA-2/OPNA/OPL
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
