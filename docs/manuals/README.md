# FITOM_X 統合プリセットプロファイル リファレンス

MIDI Bank Select(CC#0=MSB, CC#32=LSB)とProgram Changeによる
音色選択の対応表です。

## 目次

1. [音源選択モードの概要](#1-音源選択モードの概要)
2. [バンクマップ(CC#0 / CC#32)](#2-バンクマップcc0--cc32)
3. [パフォーマンスバンク(SwPatch)マップ](swbank.md)
4. [ドラムキット一覧・ノートマップ](drumkits.md)
5. [内蔵リズム音源(CC#0=112)の楽器選択方法](builtin_rhythm.md)
6. [エミュレータ専用プロファイル一覧](emu_profiles.md)
7. [OPLL GM128パッチ対応表](opll_gm128_mapping.md)

## 1. 音源選択モードの概要

本プロファイルは、以下の3種類のBank Select方式を使い分けます。

| CC#0の値 | モード | CC#32の意味 | Program Chg.の意味 |
|---|---|---|---|
| 0 | 通常モード | PatchBank番号 | 選択したPatchBank内のパッチ番号 |
| 17,26,34,35,40,48,64,81,82,84 | 直接モード | 音源チップ内のバンク番号 | 選択したバンク内のパッチ番号 |
| 112 | 内蔵リズム音源 | 対象チップ選択(17=OPNA, 40=OPLL) | 楽器(チャンネル)番号を直接指定する |

> 直接モードでは、CC#0の値自体が「どの音源チップを使うか」を指定します。
> 対応していないチップ/バンク番号を指定した場合は無音になります。
>
> 例外として CC#0=40(OPLL), CC#32=0 の「OPLL Built-In」は、バンクファイルを
> 使わず Program Change 番号から機械的にチップ種別と音色が決まる特殊な
> バンクです。詳細は該当ページを参照してください。

## 2. バンクマップ(CC#0 / CC#32)

MIDI Bank Select(CC#0=MSB, CC#32=LSB)による音色バンクの一覧です。
「バンク名」列のリンク先に、そのバンクに含まれる全音色の一覧があります。

| CC#0 | CC#32 | 音源 | バンク名 |
|---|---|---|---|
| 0 | 0 | Native | [GM Standard Native](patches/native.md#cc320) |
| 0 | 1 | Native | [necopn GM (OPN single-layer)](patches/native.md#cc321) |
| 0 | 2 | Native | [GM Standard Native OPL2](patches/native.md#cc322) |
| 0 | 3 | Native | [GM Standard Native OPL3](patches/native.md#cc323) |
| 0 | 4 | Native | [GM Standard Native OPM](patches/native.md#cc324) |
| 17 | 0 | OPN2 | [necopn GM Bank](patches/opn2.md#cc320) |
| 17 | 1 | OPN2 | [N88-BASIC Preset](patches/opn2.md#cc321) |
| 17 | 2 | OPN2 | [MUSIC LALF Preset 1](patches/opn2.md#cc322) |
| 17 | 3 | OPN2 | [MUSIC LALF Preset 2](patches/opn2.md#cc323) |
| 26 | 0 | OPZ | [GM128 OPZ Preset](patches/opz.md#cc320) |
| 26 | 1 | OPZ | [OPMDRV.X Preset](patches/opz.md#cc321) |
| 26 | 2 | OPZ | [fb01](patches/opz.md#cc322) |
| 26 | 3 | OPZ | [dx11](patches/opz.md#cc323) |
| 26 | 4 | OPZ | [dx21](patches/opz.md#cc324) |
| 26 | 5 | OPZ | [dx100_1](patches/opz.md#cc325) |
| 26 | 6 | OPZ | [dx100_2](patches/opz.md#cc326) |
| 26 | 7 | OPZ | [tx81z](patches/opz.md#cc327) |
| 34 | 0 | OPL3_2 | [ALSA std (OPL2)](patches/opl3_2.md#cc320) |
| 34 | 1 | OPL3_2 | [Preset2OP](patches/opl3_2.md#cc321) |
| 34 | 2 | OPL3_2 | [NormalBank-1](patches/opl3_2.md#cc322) |
| 34 | 3 | OPL3_2 | [NormalBank-2](patches/opl3_2.md#cc323) |
| 34 | 4 | OPL3_2 | [NormalBank-3](patches/opl3_2.md#cc324) |
| 34 | 5 | OPL3_2 | [NormalBank-4](patches/opl3_2.md#cc325) |
| 34 | 6 | OPL3_2 | [NormalBank-5](patches/opl3_2.md#cc326) |
| 34 | 7 | OPL3_2 | [LuminousNormalBank](patches/opl3_2.md#cc327) |
| 34 | 8 | OPL3_2 | [BasicNormalBank](patches/opl3_2.md#cc328) |
| 34 | 9 | OPL3_2 | [DigitalNormalBank](patches/opl3_2.md#cc329) |
| 34 | 10 | OPL3_2 | [MicroComputerNormalBank](patches/opl3_2.md#cc3210) |
| 34 | 11 | OPL3_2 | [AcidNormalBank](patches/opl3_2.md#cc3211) |
| 34 | 12 | OPL3_2 | [ChineseNormalBank](patches/opl3_2.md#cc3212) |
| 34 | 13 | OPL3_2 | [01_Pno-Bell-OrgBank](patches/opl3_2.md#cc3213) |
| 34 | 14 | OPL3_2 | [02_Gtr-BassBank](patches/opl3_2.md#cc3214) |
| 34 | 15 | OPL3_2 | [03_Str-EnsembleBank](patches/opl3_2.md#cc3215) |
| 34 | 16 | OPL3_2 | [04_Brs-Rd-PipeBank](patches/opl3_2.md#cc3216) |
| 34 | 17 | OPL3_2 | [05_Lead-Pad-FXBank](patches/opl3_2.md#cc3217) |
| 34 | 18 | OPL3_2 | [06_Eth-Perc-SEBank](patches/opl3_2.md#cc3218) |
| 34 | 19 | OPL3_2 | [MSX-AUDIO + OPLL(x) ROM Preset](patches/opl3_2.md#cc3219) |
| 34 | 112 | OPL3_2 | [ALSA drums (OPL2)](patches/opl3_2.md#cc32112) |
| 34 | 113 | OPL3_2 | [DrumsBank](patches/opl3_2.md#cc32113) |
| 34 | 114 | OPL3_2 | [07_DrumsBank](patches/opl3_2.md#cc32114) |
| 34 | 115 | OPL3_2 | [LuminousDrumBank](patches/opl3_2.md#cc32115) |
| 34 | 116 | OPL3_2 | [BasicDrumBank](patches/opl3_2.md#cc32116) |
| 34 | 117 | OPL3_2 | [DigitalDrumBank](patches/opl3_2.md#cc32117) |
| 34 | 118 | OPL3_2 | [MicroComputerDrumBank](patches/opl3_2.md#cc32118) |
| 34 | 119 | OPL3_2 | [AcidDrumBank](patches/opl3_2.md#cc32119) |
| 35 | 0 | OPL_RHY | [MSX-AUDIO/OPLL Emulate Rhythm](patches/opl_rhy.md#cc320) |
| 40 | 0 | OPLL | [OPLL Built-In(ROM音色)](patches/opll.md#cc320) |
| 40 | 1 | OPLL | [MSX-AUDIO + OPLL(x) ROM Preset](patches/opll.md#cc321) |
| 40 | 2 | OPLL | [OPLL Presets (PSS-140 + SHS-10)](patches/opll.md#cc322) |
| 40 | 3 | OPLL | [OPLL ROM Voice SwPatch Meta (Skeleton)(ユーザー設定用)](patches/opll.md#cc323) |
| 40 | 4 | OPLL | [MA-2 Preset2OP (OPLLとして参照)](patches/opll.md#cc324) |
| 48 | 0 | OPL3 | [ALSA std (OPL3)](patches/opl3.md#cc320) |
| 48 | 1 | OPL3 | [Preset4OP](patches/opl3.md#cc321) |
| 48 | 2 | OPL3 | [MicroComputer x Digital](patches/opl3.md#cc322) |
| 48 | 3 | OPL3 | [Luminous x Basic](patches/opl3.md#cc323) |
| 48 | 4 | OPL3 | [Piano/Bell/Organ detuned](patches/opl3.md#cc324) |
| 48 | 5 | OPL3 | [Guitar/Bass detuned](patches/opl3.md#cc325) |
| 48 | 6 | OPL3 | [String Ensemble detuned](patches/opl3.md#cc326) |
| 48 | 7 | OPL3 | [Brass/Reed/Pipe detuned](patches/opl3.md#cc327) |
| 48 | 8 | OPL3 | [Lead/Pad/Fx detuned](patches/opl3.md#cc328) |
| 48 | 112 | OPL3 | [ALSA drums (OPL3)](patches/opl3.md#cc32112) |
| 64 | 0 | SSG | [PSG Shared Preset (SSG/DCSG/SAA)](patches/ssg.md#cc320) |
| 64 | 1 | SSG | [EPSG (AY8930) Preset](patches/ssg.md#cc321) |
| 64 | 2 | SSG | [SCC Preset (wave 0-7: Duty系)](patches/ssg.md#cc322) |
| 64 | 3 | SSG | [SCC Preset (wave 8-15: Duty96.875+Triangle+Downsaw+Upsaw+Sine+Harpsi+Piano+Organ)](patches/ssg.md#cc323) |
| 81 | 0 | ADPCMB | [PSS-680/PSR-38 ADPCM-B (OPNA)](patches/adpcmb.md#cc320) |
| 82 | 1 | ADPCMA | [PSS-680/PSR-38 ADPCM-A (OPNB)](patches/adpcma.md#cc321) |
| 84 | 0 | AWM | [YRW801 GM (melodic)](patches/awm.md#cc320) |
| 84 | 1 | AWM | [YRW801 GM (drum, ws>=128 fixed table)](patches/awm.md#cc321) |
| 112 | 17 | 内蔵リズム(OPNA) | [OPNA内蔵リズム](builtin_rhythm.md#opna-rhythm) |
| 112 | 40 | 内蔵リズム(OPLL) | [OPLL内蔵リズム](builtin_rhythm.md#opll-rhythm) |
