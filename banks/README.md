# Preset Banks

FITOM_X プリセット音色バンク。`config/profiles/*.profile.json` の `banks`
セクションから参照される。

## ディレクトリ構成の原則

- **チップ族ごとのトップレベルディレクトリ**（`OPN/` `OPM/` `OPZ/` `OPL2/`
  `OPL3/` `OPLL/` `PSG/` `PCM/` `OPL4AWM/`）に、そのチップが読み込む
  HwBank/SampleZoneBank 形式のファイル（`*.hwbank.json` /
  `*.samplezonebank.json` / `*.pcmbank.json`）をすべて置く。
  ドラム用途か否か（打楽器の音色かメロディ楽器の音色か）はディレクトリを
  分ける基準にしない。**loaderは`hw_banks[]`/`drum_banks[]`のどちらから
  読み込むかで区別するが、置き場所はチップ族単位で統一する。**
- チップ族の直下は、**同一チップに対して複数の変換元/生成方法がある場合
  のみ**、変換元・生成ツール名のサブディレクトリで分ける
  （例: `OPL2/alsa/` `OPL2/ma2_vma/` `OPL2/msx_audio/`、
  `OPM/dx11/` `OPM/dx27_dx100/` `OPM/fb01/` `OPM/opmdrv/`）。
  変換元が単一、または外部変換元を持たない自前作成ファイル（例:
  `OPLL/rom_sw_meta.hwbank.json`、`PSG/*.hwbank.json`）は、そのチップの
  直下にフラットに置く（サブディレクトリを無理に作らない）。
- **`drums/`・`patches/`・`sw/`・`scc/` はチップ非依存のフォーマット別
  トップレベルディレクトリ**であり、上記のチップ族ディレクトリとは別軸。
  - `drums/` は **`*.drumkit.json`（DrumKit、GM2ノート番号マッピング、
    `drum_banks[]`から参照）専用**。チップ固有のHwBank形式（prog番号=
    MIDIノート番号の「打楽器音色バンク」、`hw_banks[]`から参照）は対象外
    ―― これは上記の通り、該当チップのディレクトリ側（例:
    `OPL2/ma2_vma/DrumsBank.hwbank.json`）に置く。
  - `patches/` は PatchBank（ToneLayer経由の複合パッチ、複数チップを
    横断しうる）。
  - `sw/` は SwPatch（ベロシティ感度・LFO等のパフォーマンスパッチ）。
    詳細は`sw/README.md`参照。
  - `scc/` は SCC/SCC+波形テーブル（`*.sccwave.json`）。

## ディレクトリ構成（現状）

```
banks/
├── OPN/
│   ├── gm/            necopn_gm.hwbank.json           (N88-BASIC/OPNA driver GM配列)
│   ├── music_lalf/     music_lalf_1/2.hwbank.json
│   └── n88basic/       n88basic_preset.hwbank.json
├── OPM/
│   ├── dx11/            dx11.hwbank.json
│   ├── dx27_dx100/      dx100_1/2.hwbank.json, dx21.hwbank.json
│   ├── fb01/            fb01.hwbank.json
│   ├── gm_fill/         necopn_fill.hwbank.json
│   └── opmdrv/          opmdrv_preset.hwbank.json
├── OPZ/
│   ├── gm128/           gm128_preset.hwbank.json
│   └── tx81z/           tx81z.hwbank.json
├── OPL2/
│   ├── alsa/            std_opl2.hwbank.json, alsa_drums.hwbank.json
│   ├── ma2_vma/         01〜06_*Bank/*NormalBank/*DrumBank/Preset2OP.hwbank.json
│   └── msx_audio/       msx_audio_preset(_rhythm).hwbank.json
├── OPL3/
│   ├── alsa/            std_opl3.hwbank.json, alsa_drums.hwbank.json
│   ├── ma2_vma/         GMmapFM4op.hwbank.json, Preset4OP.hwbank.json
│   └── opl2_merge/      OPL2バンク2本をopl2_merge.pyで4OP合成した派生バンク群
│                         (*_detuned.hwbank.json, Luminous_x_Basic.hwbank.json,
│                          MicroComputer_x_Digital.hwbank.json)
├── OPLL/                opll_presets.hwbank.json (外部変換元、単一のためサブdir無し)
│                         rom_sw_meta.hwbank.json (自前作成メタバンク)
├── PSG/                 psg_shared_preset/epsg_preset/scc_preset_1/2.hwbank.json
│                         (自前作成、外部変換元なし)
├── OPL4AWM/              opl4awm_yrw801_gm/drum.samplezonebank.json
├── PCM/
│   └── pss680/           pss680_opna/opnb.pcmbank.json + 付随bin/json
├── drums/                DrumKit(*.drumkit.json、GM2ノートマッピング)
├── patches/              PatchBank(*.patchbank.json、ToneLayer経由の複合パッチ)
├── sw/                   SwPatch(*.swbank.json、ベロシティ感度/LFO。README.md参照)
└── scc/                  SCC波形テーブル(*.sccwave.json)
```

## プロファイルからの参照方法

`*.profile.json` の `banks` セクションでバンクファイルを指定します。
パスは**参照元プロファイルファイル自身のディレクトリ**からの相対パスで
指定します(`config/profiles/*.profile.json` から見て `banks/` はリポジトリ
ルート直下、2階層上にあるため `../../banks/...` と書く)。

```json
{
  "banks": {
    "hw_banks": [
      { "group": "OPM", "bank": 0, "file": "../../banks/OPM/dx27_dx100/dx100_1.hwbank.json" },
      { "group": "OPL2","bank": 0, "file": "../../banks/OPL2/alsa/std_opl2.hwbank.json" },
      { "group": "OPL3_2", "bank": 112, "file": "../../banks/OPL2/alsa/alsa_drums.hwbank.json" }
    ],
    "sw_banks": [
      { "bank": 0, "file": "../../banks/sw/default_32.swbank.json" }
    ],
    "drum_banks": [
      { "prog": 0, "file": "../../banks/drums/gm2_standard.drumkit.json" }
    ]
  }
}
```

打楽器音色のHwBank(prog番号=MIDIノート番号)も、`drum_banks[]`ではなく
`hw_banks[]`から高いbank番号(例: 112〜)を割り当てて読み込む運用です。
