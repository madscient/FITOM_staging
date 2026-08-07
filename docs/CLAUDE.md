# FITOM_staging プロジェクト引き継ぎドキュメント (for Claude Code)

このファイルはプロジェクトルート直下に置き、Claude Codeセッション開始時に
必ず最初に読むこと。複数マシンで作業するための運用ルールも記載している。

### 0. Claude Codeとのやり取り方針
- **ユーザーへの応答・報告は必ず日本語で行うこと**（コード内コメント・
  コミットメッセージの慣習は既存コードに合わせる。この方針自体は言語のみ
  の指定で、対象範囲を変更するものではない）。

---

## 1. プロジェクト概要

- **FITOM_X**: コアライブラリ + 音色バンク + 変換ツール（別リポジトリ）
- **FITOM_staging**（本リポジトリ）: 動作環境・設定・プリセットバンク・セットアップスクリプト
- 対象: 複数のFM/PSG/PCM音源チップ（OPN系, OPM/OPZ系, OPL系, OPLL系, PSG系,
  ADPCM系, AWM）をエミュレータまたは実機経由で統一的に扱うMIDI音源システム

### ディレクトリ構成
```
config/
  profiles/*.json      プロファイル本体（hw_plugins + banks構成）
  profiles/hw_plugins/*.json  hw_plugins[].profileが指すプラグイン固有の
                        サブプロファイル（FitomEmuIF用fmemuif_*.json /
                        FitomHwIF用fitom_hw_*.json）。ディレクトリ配置が
                        プロファイルの参照階層（トップ→サブ）と一致するよう
                        profiles/直下ではなくprofiles/hw_plugins/に配置
                        （2026年7月17日、3.14参照）
config_schema/*.json   各種JSON Schemaファイル
banks/
  OPN/ OPM/ OPZ/ OPL2/ OPL3/ OPLL/ PSG/ PCM/ OPL4AWM/  チップ族ごとの音色バンク
  patches/               PatchBank（ToneLayer経由の複合パッチ）
  drums/                 DrumKit（GM2ノートマッピング）
  sw/                    SwPatch（パフォーマンスパッチ、ベロシティ感度/ビブラート等）
tools/voice_convert/    音色変換スクリプト群
docs/manuals/           エンドユーザー向けレファレンスマニュアル（本セッションで作成）
```

---

## 2. 現在のリポジトリ状態（このドキュメント作成時点）

### プロファイル一覧
全6プロファイルとも`banks`は`config/profiles/unified.bankset.json`
（hw_banks 63件, sf2_banks 10件, sw_banks 7件, patch_banks 7件,
drum_banks 21件, pcm_banks 3件）を共有参照している（2026年7月29日、
3.32節参照。デバイス構成に含まれないチップ向けのバンクエントリは
単に発音しないだけで実害はない）。`devices`/`hw_plugins`（実際に
ロードするチップ構成）のみがプロファイルごとに異なる。

| ファイル | デバイス構成 |
|---|---|
| `unified_preset.profile.json` | SF2(FluidSynth)のみ（全チップ分のbanksカタログを保持する“総本山”） |
| `emu_opn.profile.json` | OPN専用（OPN/OPN2/OPNA/OPNB/OPNBB×1ずつ） |
| `emu_opl.profile.json` | OPL専用（OPL[rhythm]/Y8950/OPL2/OPL3/OPL4×1ずつ） |
| `emu_opm.profile.json` | OPM専用（OPM×2/OPZ×2） |
| `emu_opll.profile.json` | OPLL専用（OPLL[rhythm]/OPLLP/VRC7/OPLLX×1ずつ。OPLL2は3.37でエンジン非対応のため削除） |
| `fmall.profile.json` | OPM/OPZ/OPL3/OPL4AWM/OPNA/OPNBB/OPLL/OPLLP/OPLLX/VRC7構成（2026年7月19日新設） |
旧・個別プロファイル（`emulator_opm.profile.json`ほか計6件、統合前からの
遺産）は、誰もメンテナンスしておらず統合後の構成と矛盾していたため
2026年7月26日に削除した（3.30節参照）。

### ドキュメント
`docs/manuals/`（本セッションで新規作成、`FITOM_X_preset_docs`から展開）:
`README.md`（起点）/ `swbank.md` / `drumkits.md` / `builtin_rhythm.md` /
`emu_profiles.md` / `opll_gm128_mapping.md` / `patches/*.md`（チップ族ごと）

---

## 3. 必ず守るべき設計原則・技術的知見

作業前に必ず目を通すこと。誤りを繰り返さないための教訓を含む。

### 3.1 hwbank.json のトップレベル構造
- `voice_patch_type`も`chip_group`もhwbank.json自体には**持たせない**。
  チップ族の指定は**プロファイル側の`hw_banks[].group`**（文字列、細かい分類
  可: `OPN2`/`OPZ`/`OPL3_2`/`OPL_RHY`/`OPLL`/`OPL3`/`SSG`/`ADPCMB`/`ADPCMA`/
  `AWM`等）で行う。

### 3.2 VoicePatchType（CC#0直接モード値）
| 値(10進) | 値(16進) | 名称 |
|---|---|---|
| 0 | 0x00 | 通常モード（PatchBank経由） |
| 17 | 0x11 | OPN2 |
| 26 | 0x1A | OPZ |
| 34 | 0x22 | OPL3_2 |
| 35 | 0x23 | OPL_RHY（OPLレジスタ疑似リズム、HwPatch経由） |
| 40 | 0x28 | OPLL |
| 48 | 0x30 | OPL3 |
| 64 | 0x40 | SSG（PSG系共有バンクの入口） |
| 81 | 0x51 | ADPCMB |
| 82 | 0x52 | ADPCMA |
| 84 | 0x54 | AWM |
| 112 | 0x70 | 内蔵リズム音源専用バンク（OPNA/OPLL、HwPatch不要） |

### 3.3 EGT/SR/RR変換規則（OPL/OPLL系のエンベロープ変換で必須）
- EGTビット=1（サステイン）: `SR=0`, `RR=r`（シフトなし）
- EGTビット=0（パーカッシブ）: `SR=r<<1`（4bit→5bit）, `RR=r`（シフトなし）
- `ops[i].EGT`はOPL系では常に0（OPN専用のSSG-EG用、無関係）
- **`RR`は実機EGTビットの値・`SR`分岐に関わらず、常に
  `RR=変換元RRレジスタ値`（シフトなし）を格納しなければならない**
  （2026年7月20日訂正。旧記述は「EGTビット=0/パーカッシブのとき
  `RR=0`」としていたが誤り）。FITOM_Xは**OPL/OPL2/OPL3もOPLLと同じく**
  キーオン時は常に実機EGTビット=0にして`SR`の値をRRレジスタへ、
  キーオフ時は常に実機EGTビット=1にして`RR`の値をRRレジスタへ動的に
  書き込む（`updateVoice`一度きりの静的書き込みで完結するのはOPL系
  だけ、というのは誤った理解だった）。したがって`RR=0`のキャリアは
  `SR`が何であってもキーオフで事実上消音しなくなる。詳細は
  `docs/voice-parameter-reference.md`「OPL系」節、3.23/3.24参照。

### 3.4 PSG系共有バンク
全PSG系チップ（SSG/EPSG/DCSG/SAA/SCC）は`voice_patch_type=0x40`固定で
ロードされる共有バンクを使う。各パッチの`ext.target_voice_patch_type`
（`0x40`=SSG/`0x41`=EPSG/`0x42`=DCSG/`0x43`=SAA/`0x48`=SCC）で実際の対象
チップを指定する。波形選択があるのはEPSG（`ops[0].WS`=デューティ比0-8）と
SCC（`ops[0].WS`=波形メモリindex、0-127）のみ。

### 3.5 内蔵リズム音源（CC#0=112, `0x70`）— 2026年7月に`fixed_ch`廃止
- **旧**: `DrumNote::fixed_ch`で楽器（物理チャンネル）を指定
- **新**: `fixed_ch`はスキーマから完全に削除。**`patch_prog`がそのまま
  チャンネル番号として扱われる**（`hwProg`をそのままチャンネル番号として
  検証）。
- OPNA: 0=BD, 1=SD, 2=Top Cymbal, 3=HH, 4=Tom, 5=Rim Shot（レジスタ0x10
  bit0-5）
- OPLL: 0=HH, 1=Top Cymbal, 2=Tom, 3=SD, 4=BD
- OPL系疑似リズム（`VOICE_PATCH_OPL_RHY`=0x23）にも同様の「1チャンネル
  =1エントリ」制約が適用されるが、`ext.rhythm_ch`という**独立した軸**
  （`0=HH,1=CYM,2=TOM,3=SD,4=BD`）で管理されるため、同一楽器に複数の
  音色バリエーション（Pitch LFO版等）を別スロット(`patch_prog`)として
  持たせられる。

### 3.6 OPLL Built-In ROM音色
- `voice_patch_type=0x28(OPLL), hw_bank=0`は**ファイルを持たない機械合成
  領域**。`hwProg`の上位3bit=チップ種別（0=OPLL,1=OPLLX,2=OPLLP,3=VRC7）、
  下位4bit=ROM音色番号（0=無音,1-15=音色）。
- `patches[i].builtin`フィールドは**`role="builtin_swpatch_meta"`の
  バンクでのみ意味を持つ**（ユーザーがパフォーマンスパッチを紐づけるための
  領域、`unified_preset.profile.json`では`hw_banks[group=OPLL,bank=3]`）。
  通常のGM128パッチバンクでROM音色を「実際に鳴らすパッチ」として使いたい
  場合は、ToneLayerで直接`voice_patch_type=0x28, hw_bank=0, hw_prog=
  (variant<<4)|inst`を指定すればよい（`builtin`フィールドは使わない）。
- OPLL/OPLLX/OPLLP/VRC7 ROM音色名一覧、および代替用途コメント（"Also be
  used as..."等）は以下を参照（Copyright-freeレジスタダンプあり）:
  - https://sites.google.com/site/undocumentedsoundchips/yamaha/ymf281
  - https://sites.google.com/site/undocumentedsoundchips/yamaha/ym2423
  - https://github.com/plgDavid/misc/wiki/Copyright-free-OPLL(x)-ROM-patches

### 3.7 128パッチ制限
hwbank/patchbankの`prog`は`0-127`（`minimum:0, maximum:127`）。ファイル
統合時は必ず合計パッチ数を確認すること（実例: OPLL用SHS-10/PSS-170
バンクは既に125パッチ使用済みのため、MA-2 Preset2OP由来67パッチを追加
統合しようとして128パッチ超過が判明し断念した経緯がある）。

### 3.8 OPL4-AWM / ADPCM系はHwPatchを使わない
- AWM（`voice_patch_type=0x54`）・ADPCM-B（`0x51`）・ADPCM-A（`0x52`）は
  `SampleZonePatch`（`*.samplezonebank.json`または`*.pcmbank.json`）を
  使い、通常の`HwPatch`（`ops`配列）を経由しない。
- ドラムキットは`patchbank`層を経由せず、`voice_patch_type`を直接モード
  指定した`notes[]`から`hw_bank`/`hw_prog`を直接参照できる（`type:
  "direct"`のシンプルなdrumkitで全音域を1パッチにルーティングする例:
  `opl4awm.drumkit.json`）。

### 3.9 パッチ名の命名規則（2026年7月改訂）
- OPLLバリアント表記: 先頭に`[OPLL]`/`[OPLLX]`/`[OPLLP]`/`[VRC7]`の
  プレフィックス（型番は付けない）
- PSG系: 先頭に`[SSG]`/`[EPSG]`/`[DCSG]`/`[SAA]`/`[SCC]`のプレフィックス
  （`ext.target_voice_patch_type`から導出）
- SwPatchバリアント（Sustain/Decay/Vib等）を示す文字列は名前から削除し、
  末尾に`[sw_bank:sw_prog]`のポストフィクスを付与
- ToneLayerで他バンクを参照するだけのパッチ（OPLL GM128の一部等）は、
  参照先の実際のパッチ名をそのまま使う

### 3.10 opl2_merge.pyのALG設計
2つのOPL2バンクを合成して4OPパッチを作る際、各パッチのALG(cnt0/cnt1)は
**パッチ単位で各ソースバンクの元の値をそのまま個別に維持する**
（`--alg-a`/`--alg-b`未指定時）。`ConnectionSEL`は`ext.ALG_EXT`で別途
制御し、こちらは`0`固定（旧FITOM互換動作）。

### 3.11 HwPatchフィールド改名（2026年7月17日、FITOM_X側コミット94e99d6に追従）
- `ops[i].FXV` → **`PDT`**（Pseudo DeTune）に改名。`ext.DM0` →
  **`FIX`**（Fixed freq）に改名。挙動・値域は変更なし、名称のみ
  （フィールドの意味は3.2/3.10と同じ: OPN ch2 FXモード、OPL3(COPL3)
  4OP疑似デチューン）。
- 本リポジトリ側でも影響ファイルを合わせて改名済み:
  `banks/OPL3/opl2_merge/0{1-5}_*_detuned.hwbank.json`（`FXV`→`PDT`、
  疑似デチューン実データ、値=4。当時は`banks/OPL3/`直下だったが、
  3.15のディレクトリ再整理で`opl2_merge/`配下に移動済み）、
  `banks/OPM/dx11/dx11.hwbank.json`・
  `banks/OPM/dx27_dx100/{dx100_1,dx100_2,dx21}.hwbank.json`・
  `banks/OPZ/gm128/gm128_preset.hwbank.json`（`DM0`→`FIX`、いずれも
  値=0で未使用）。**JSONキー名の変更は実際の音への影響ではなく
  読み込み可否そのものに関わる**（`PatchManager.cpp`は新キー名でしか
  読まないため、リネーム漏れがあると疑似デチューン設定が無音のうちに
  無視される）。
- `DrumNote::fine_tune`の単位表記も訂正: スキーマ記述の「cents」は
  誤りで、実際は**kfs単位（1半音=64ステップ）**。`ISoundDevice::
  setNoteFine()`にそのまま渡される値であり、値・変換ロジック自体は
  元から正しかった（ドキュメントの記述ミスのみ）。
- `config_schema/{drumbank,drumkit,hwbank,fitom.conf}.schema.json`は
  FITOM_X側から丸ごとコピーして同期済み。同期のついでに気づいた
  副次的な差分（過去のセッションで追従漏れだったもの）:
  - 旧形式`*.drumbank.json`/`*.drumkit.json`のノート単位`fixed_ch`
    （ハイハットの相互チョーク用ハック）は2026年7月15日
    （FITOM_X側コミットec07eb2）に完全廃止され、代わりに
    `DrumPatch::chokeGroups`（drumkitトップレベルの`choke_groups`
    フィールド、ノート番号の配列のペアで相互ダンプを明示指定）に
    置き換わっている。本リポジトリの`banks/drums/*.drumkit.json`は
    元々`fixed_ch`を使っていなかった（grep確認済み、データ移行は
    不要）ため実害はないが、スキーマ更新に気づかず半年近く
    追従漏れになっていた。
  - `config_schema/fitom.conf.schema.json`のみ、同期後も
    `config/fitom.conf.json`実ファイルとの間でバリデーションエラーが
    残る（`audio`/`banks_dir`/`plugins.hw_plugin`をスキーマ側が
    許可していない）。これは今回の同期以前から存在した既存の drift
    （3.11の対象コミットとは無関係）。→ 3.12で解消。

### 3.12 fitom.conf.json構成監査（2026年7月17日、FITOM_X側コミットda1bfcbに追従）
FITOM_X側で「fitom.conf.jsonがパースされても実装が一切参照していない
設定項目」の監査が行われ、以下がスキーマから削除された。本リポジトリの
`config/fitom.conf.json`もこれに合わせて書き換え済み:
- `plugins.midi_plugin`/`plugins.hw_plugin`: MIDIバックエンドDLL/HWプラグ
  インDLLの指定は、実際には**プロファイル側**（`hw_plugins[]`/
  `midi_backend.dll`）でのみ解決される。`fitom.conf.json`側の同名
  フィールドはパースされるだけで一度も参照されていなかった（重複かつ
  デッド）。旧`plugins.hw_plugin.dll: "fitom_fmhwif.dll"`は削除。
- `timing.timer_ms`/`polling_interval_us`: 前者はポルタメント速度
  テーブル・ソフトLFOレート換算が1msティック固定前提で較正されており
  安全に可変化できない、後者はHWポーリングの責務がHWプラグイン側
  （`fitom_fmhwif.dll`等）に移管済みでFITOM_X本体に該当スレッドが
  存在しないため、いずれも実装のない設定として削除。旧`timing.timer_ms:
  1`は削除。
- `audio.*`/`banks_dir`: 元からFITOM_X本体のスキーマ・実装のどちらにも
  存在しなかった（`Config.cpp`をgrepしても参照箇所なし）。本リポジトリ
  独自に紛れ込んでいたデッドフィールドだったため削除。
- 一方、`log.*`は今回**新たに実装が配線された**（以前はパースされる
  だけで`Log::init()`に反映されていなかった）。`fitom_cli`/`fitom_gui`
  起動時、実行ファイルと同ディレクトリの`fitom.conf.json`があれば
  `log.level`/`log.file`/`log.console`が実際に適用される。
  現状の`config/fitom.conf.json`（`log.level=info`,
  `log.file=logs/fitom.log`）は変更不要、今後はこれが実際に効く。
- あわせて`config/profiles/*.profile.json`の`devices[].sample_rate`が
  `Config.cpp`側で44100固定になっており値を無視していたバグも
  修正された。本リポジトリの現行プロファイルはいずれも44100指定のみ
  のため実害はなかったが、将来44.1kHz以外を指定する場合は今後
  正しく反映される。
- **副次的に発見**: `banks/patches/necopn_gm.patchbank.json`の
  Patch直下`sw_bank`/`sw_prog`（廃止済み階層）を削除。
  `PatchManager::loadPatchBankJson`はPatch直下の`sw_bank`/`sw_prog`を
  そもそも読まない（`name`/`poly`/`layers`のみ）ため、この128件の
  設定は最初から無音のまま無視されるデッドデータだった。SwPatchの
  実際の対応付けは参照先`banks/OPN/gm/necopn_gm.hwbank.json`の
  各パッチ自身の`sw_bank`/`sw_prog`（`HwPatch::swBank`/`swProg`、
  `jsonToHwPatch`が読む）で行う。

### 3.13 パフォーマンス情報を持たない変換元からのSwPatch割り当て方針（2026年7月20日訂正）
`necopn_gm.hwbank.json`（necopn由来のGM128、パフォーマンス情報を
持たない変換元フォーマット）のような、変換元にパフォーマンス情報
（ベロシティ感度カーブ・LFO設定等）が無いハードウェアパッチをhwbank
へコンバートする場合、**音量ベロシティセンシティ(`VTL`)のみを設定した
汎用パフォーマンスパッチ**を一律で割り当てる、というのが本プロジェクト
の標準運用。これ自体は意図した設計であり修正不要。
- **訂正**: 本節は元々「`necopn_gm.swbank.json`の`sw_prog=2`」を参照先
  として記載していたが誤りだった。実際に全プロファイルで汎用デフォルト
  として使われているのは`sw_bank=0`(`banks/sw/performance_presets.
  swbank.json`)であり、`necopn_gm.hwbank.json`を含む変換元にパフォー
  マンス情報が無いHwPatchは全て`sw_bank=0, sw_prog=2`("VelScale Mid"、
  VTL=80)を参照する（3.21節でこの`sw_prog`をALGに応じて分岐させる
  よう変更した）。`banks/sw/necopn_gm.swbank.json`・
  `default_gm.swbank.json`・`default_32.swbank.json`・
  `compat_zero.swbank.json`は、どのプロファイルの`sw_banks[]`からも
  参照されていない**孤立ファイル**（旧設計の残骸、フィールド名も
  `LFO`/`LDM`/`LDL`/`SLF`等の廃止済み旧形式のまま）と判明した。実害は
  ないが将来紛らわしいため、削除または現行スキーマへの追従が望ましい
  （未着手、4節に記載）。
- 変換元に実際のパフォーマンス情報がある場合は、その情報も変換して
  **専用のパフォーマンスパッチ**（バンク内の別`sw_prog`、例:
  `dx100_1`/`dx100_2`/`dx11`/`dx21`/`tx81z`/`fb01`は各HwPatchが
  1:1で専用の`sw_prog`を持つ）を割り当てる。
- したがって「複数パッチが同じ`sw_prog`を共有している」こと自体は
  バグの兆候ではない。個別対応の要否は変換元データの内容次第であり、
  `sw_bank`/`swbank.json`側に楽器数分のエントリが用意されているか
  どうかとは無関係に判断すること。

### 3.14 banks.*[].file相対パス基点変更 + プロファイル関連ファイルの再配置（2026年7月17日、FITOM_X側コミットeed0b4aに追従）
FITOM_X側で`banks.*[].file`（hw_banks/sw_banks/patch_banks/drum_banks/
scc_wave_banks/pcm_banks）の相対パス解決基点が、**カレントワーキング
ディレクトリからプロファイルファイル自身のディレクトリに変更**された
（`FITOMConfig::loadProfile`が`buildFromProfile`に渡す`baseDir`を
`std::filesystem::path{}`（空、旧CWD相対）から`path.parent_path()`
（プロファイル自身の親ディレクトリ）に変更）。あわせて、`drum_banks`
省略時にhw_banks等も含め全バンク種別のロードがスキップされる既存バグも
修正された。
- 本リポジトリの`config/profiles/*.profile.json`（11件）は全て
  `config/profiles/`直下にあり、`banks/`はリポジトリルート直下（2階層上）
  にあるため、`banks.*[].file`の値を全件`"banks/..."`から
  `"../../banks/..."`に書き換えた。**新しいFITOM_X本体（eed0b4a以降）を
  ビルドし直さないままこの変更を適用すると、旧CWD相対のバイナリでは
  バンクが一切見つからなくなる点に注意**（本体の更新と本リポジトリの
  プロファイル書き換えは同時に反映すること）。
- 副次的に発見: `emulator_opl3.profile.json`/`hw_opm_emu_opl3.profile.json`/
  `hw_opn_emu_opm_opl3.profile.json`の3件が、2026年7月12日のコミット
  `5825913`（`banks/OPL2/rhythm/opll_rhythm.hwbank.json`を削除し
  `unified_preset.profile.json`側は`banks/OPL2/msx_audio/
  msx_audio_preset_rhythm.hwbank.json`に切り替え済み）に追従できておらず、
  存在しないファイルを参照したままになっていた（旧CWD相対の基点でも
  実在しないファイルだったため、今回の基点変更とは無関係の既存バグ）。
  同じ内容の後継ファイルである`msx_audio_preset_rhythm.hwbank.json`を
  参照するよう修正済み。

**プロファイル関連ファイルの再配置**（同日、ディレクトリ階層をプロファイルの
参照階層に合わせる目的）:
- `hw_plugins[].profile`（FitomEmuIF/FitomHwIFなど各hwプラグインDLL自身が
  読む設定ファイルへのパス）は、FITOM_X本体では一切解釈されず
  `HWPlugin_Init()`にそのまま渡される。FitomEmuIF/FitomHwIFの実装は
  いずれも渡されたパス文字列を`std::filesystem::exists()`にそのまま渡す
  （＝プロセスのカレントワーキングディレクトリ相対）ため、本リポジトリの
  起動運用（`bin/fitom_core.exe --profile config/profiles/<name>`を
  リポジトリルートから実行）を前提にすると、値は常にリポジトリルート
  相対で書く必要がある。
- 変更前は`config/fmemuif_*.json`・`config/fitom_hw_*.json`が
  `config/profiles/`と同階層にフラットに置かれており、かつ
  `hw_plugins[].profile`側の参照も一部`"config/"`プレフィックス付き・
  一部プレフィックス無し（`fmemuif_opl3.profile.json`のように書かれ、
  CWD=リポジトリルート運用では実際には解決できない）が混在していた
  （`emulator_opl3`/`emulator_opm`/`hw_opm_emu_opl3`/
  `hw_opn_emu_opm_opl3`/`hw_spfm_opm`の計6箇所が該当。プロファイル
  ディレクトリ階層とプロファイル自身が持つ参照階層が一致していなかった
  ことに起因する既存の潜在バグ）。
- `config/fmemuif_*.json`（7件）・`config/fitom_hw_*.json`（3件）を
  `config/profiles/hw_plugins/`（トップ階層プロファイルからの参照先である
  ことをディレクトリ階層でも表す）に移動し、全プロファイルの
  `hw_plugins[].profile`を`"config/profiles/hw_plugins/<file>"`に統一。
- `config/fmhwif_opl3.profile.json`・`config/fmhwif_opm.profile.json`・
  `config/fmhwif_opm_opl3.profile.json`の3件は、内容が対応する
  `fmemuif_*.json`と完全に同一かつどこからも参照されていない（`fmemuif_`
  への改名後の削除漏れ）孤児ファイルだったため削除。
- README.mdのディレクトリ構成図・アーキテクチャ概要・プロファイル対応表、
  および`setup.ps1`/`setup.sh`の実機ポート設定案内も新しいパスに追従済み。
  README.md内の「`FMHWIF_PROFILE`環境変数が`profile_env`との組み合わせで
  自動設定される」という記述は現行のスキーマ・実装のどちらにも該当する
  仕組みが存在しない不正確な記載だったため、実際の解決方法（`profile`に
  明示パスを書く方式）の説明に修正した。

### 3.15 banks/内部ディレクトリ構成の整理（2026年7月17日）
`banks/`配下のチップ族ディレクトリ内で、変換元/生成方法ごとのサブ
ディレクトリ分けが一貫していなかった（一部チップは常にサブdirあり、
一部は無し、`drums/OPL2`・`drums/OPL3`だけ別の軸=フォーマット別トップ
レベルディレクトリの下にチップ固有HwBankが紛れ込んでいた）ため、
`banks/README.md`に明文化した以下の原則で統一した:
- `drums/`・`patches/`・`sw/`・`scc/`は**フォーマット別**（DrumKit/
  PatchBank/SwPatch/SCCWave）のトップレベルディレクトリで、チップ族
  ディレクトリとは別軸。特に`drums/`は`*.drumkit.json`
  （GM2ノートマッピング、`drum_banks[]`から参照）専用とし、prog番号=
  MIDIノート番号のチップ固有HwBank（`hw_banks[]`から高いbank番号で
  参照する「打楽器音色バンク」、DrumKitとは別物）は対象外とする。
- チップ族ディレクトリ直下は、**同一チップに複数の変換元/生成方法が
  ある場合のみ**変換元名のサブディレクトリで分ける。単一変換元、または
  自前作成（外部変換元なし）のファイルはサブディレクトリを作らずフラットに
  置く。

これに伴い実施した移動（全て`git mv`、内容変更なし）:
- `banks/drums/OPL2/{DrumsBank,07_DrumsBank,LuminousDrumBank,
  BasicDrumBank,DigitalDrumBank,MicroComputerDrumBank,AcidDrumBank}
  .hwbank.json`（いずれもMA-2 VMA形式、`source`フィールドで確認済み）
  → `banks/OPL2/ma2_vma/`（既存の同形式メロディバンクと同じ場所）
- `banks/drums/OPL2/alsa_drums.hwbank.json` → `banks/OPL2/alsa/`
  （ALSA sbiload形式、`std_opl2.hwbank.json`と同じ場所）
- `banks/drums/OPL3/alsa_drums.hwbank.json` → `banks/OPL3/alsa/`
- `banks/OPL3/`直下にフラットで置かれていた7件（`0{1-5}_*_detuned
  .hwbank.json`・`Luminous_x_Basic.hwbank.json`・
  `MicroComputer_x_Digital.hwbank.json`）は、いずれも`opl2_merge.py`で
  OPL2バンク2本を合成した派生バンク（`source`フィールドで確認済み）
  であり、既存の`OPL3/alsa/`・`OPL3/ma2_vma/`という「変換元別サブ
  ディレクトリ」の並びから外れていたため、新設した
  `banks/OPL3/opl2_merge/`に移動。
- 上記により`banks/drums/OPL2/`・`banks/drums/OPL3/`は空になり削除
  （`banks/drums/`直下は`*.drumkit.json`のみが残る）。
- 移動に伴い、参照していた5プロファイル
  （`emu_opl`/`unified_preset`が`drums/OPL2`・`drums/OPL3`の計19箇所、
  `emu_opl`/`unified_preset`が`OPL3/`直下7ファイルの計14箇所）の
  `banks.hw_banks[].file`を新しいパスに更新。`banks/README.md`・
  `tools/voice_convert/README.md`の例示パスも追従済み。

### 3.16 pcmbank.jsonのbin_file/adpcm_json参照が解決できないバグを修正（2026年7月18日）
`PatchManager::loadPcmBankJson()`は、`*.pcmbank.json`内の`bin_file`/
`adpcm_json`フィールド（相対パスの場合）を**そのpcmbank.jsonファイル
自身の親ディレクトリ**を起点に解決する（`baseDir = path.parent_path()`、
3.14の`banks.*[].file`とは別の、より以前から存在する解決規則）。
- `banks/PCM/pss680/pss680_opna.pcmbank.json`・
  `pss680_opnb.pcmbank.json`は、この2フィールドに
  `"banks/PCM/pss680/xxx.bin"`のようなリポジトリルート相対のフルパスを
  書いていた。pcmbank.json自身が既に`banks/PCM/pss680/`に置かれている
  ため、これを基点に解決すると`banks/PCM/pss680/banks/PCM/pss680/
  xxx.bin`という二重パスになり、実在しないファイルを指していた
  （3.14のbanks path変更とは無関係の、以前から存在した既存バグ）。
  同一ディレクトリ内のファイル名のみ（`"pss680_opna_adpcmb.bin"`等）に
  修正。
- `banks/PCM/pss680/`には他に`pss680_opnb_adpcmb.bin`/`.json`と
  `params_opna_adpcmb.json`/`params_opnb_adpcma.json`/
  `params_opnb_adpcmb.json`が存在するが、前者はどのpcmbank.jsonからも
  参照されていない未使用データ（OPNB用ADPCM-Bのパック済み出力だが
  対応するpcmbank.jsonが無い）、後者はadpcm_packerツールへの入力
  レシピ（wavファイル一覧、FITOM_X実行時には読み込まれないビルド用
  中間ファイル）であり、いずれも今回のバグとは無関係。

### 3.17 OPL/OPLL系 AR/DR/TLの格納規約違反を一括修正（2026年7月18日）
FITOM_Xランタイム側(`core/src/OPL_new.cpp`の`ar4()`/`tl6()`、
`core/src/OPLL_new.cpp`の同等ロジック)は、HwPatchの`AR`/`DR`/`TL`を実際の
チップレジスタへ書き込む際に必ず`>>1`する設計になっている
（`core/include/fitom/VoiceData.h:76-77`のコメントの通り「全チップ共通の
上位ビット表現で保持する。チップドライバがGET_AR等のマクロで必要な
ビット幅に切り出す」。OPLはAR/DR=4bit・TL=6bitのレジスタ幅に対し、
HwPatch側は5bit/5bit/7bitの「上位ビット表現」で保持する設計）。

このため、変換元が持つ実機レジスタ値(AR/DR=4bit 0-15、TL=6bit 0-63)を
HwBankに格納する際は**`<<1`して**格納しなければならないが、
`tools/voice_convert/alsa_convert.py`・`vma_convert.py`は共に変換元の
レジスタ値を無変換のまま格納していた(EGT/SR/RR変換は正しく`<<1`されて
いたが、AR/DR/TLだけ抜けていた)。結果、実機再生時は`>>1`により意図した
半分の値(AR/DRは0-31のはずが実質0-7相当の粗い分解能、TLは音量が
半分弱＝本来より大きい音量)になっていた。`opl2_merge.py`はこれらの値を
再計算せず入力をそのまま引き継ぐ設計のため、合成元(ma2_vma系2OPバンク)
のバグをそのまま継承していた。

**確認方法**: 正しく格納されていれば`AR`/`DR`/`TL`は必ず偶数(LSBは常に0の
パディング)になるはずだが、影響ファイルは全て奇数値を含んでいた
（全パッチ・全opsをスキャンし、AR最大値=15・DR最大値≤15・TL最大値≤63
という「4bit/4bit/6bitの生レジスタ値そのまま」の分布であることを確認)。

**対応**:
- `banks/OPL2/`・`banks/OPL3/`・`banks/OPLL/`配下の全`*.hwbank.json`
  (41ファイル、`OPLL/rom_sw_meta.hwbank.json`はpatches空のため対象外)の
  `AR`/`DR`/`TL`を機械的に2倍(`<<1`)して一括修正。値の意味・格納順・
  他フィールドは一切変更していない。`banks/OPL2/msx_audio/*`・
  `banks/OPL2/msx_audio/*`・`banks/OPLL/opll_presets.hwbank.json`は当時
  このリポジトリに変換スクリプトが残っていなかった(過去セッションでの
  変換と推測)が、同じ「4bit/4bit/6bitの生値がそのまま格納されている」
  分布だったため、同じ規則で修正可能と判断し変換元への遡り無しで直接
  修正した（`opll_presets.hwbank.json`は後日3.23で`opll_convert.py`を
  新設し変換元から再変換済み、この`<<1`規則はそちらにも引き継がれている）。
- `alsa_convert.py`・`vma_convert.py`のAR/DR/TL算出箇所に`<<1`を追加し、
  今後の変換で同じ不具合が再発しないよう修正。`opl2_merge.py`は入力を
  そのまま引き継ぐだけなので変更不要(入力が正しければ出力も正しい)。
- OPN/OPM/OPZ/PSG系は当初調査対象外としていたが、後日FITOM_X側コミット
  `c90f00c`(2026年7月18日)で判明した内容により解決済み: `VoiceData.h`の
  `FV_AR_OPM`/`FV_DR_OPM`/`FV_TL_OPM`マクロ（`>>2`シフトあり）は実際には
  どこからも呼ばれていない**未使用コード**で、実際のOPM/OPP/OPZ書き込み
  ロジック(`OPM_new.cpp`の`updateVoice`/`updateSustain`/`forceDamp`/
  `updateKey`)は本来AR/DR/SRを`>>2`、SL/RRを`>>3`する必要が無い
  （YM2151のレジスタ幅がAR/D1R/D2R=5bit・D1L/RR=4bitで、HwPatch側の
  共通ドメイン0-31/0-15と一致するため、マスクのみで良い）にもかかわらず
  誤って追加シフトしており、実効解像度がAR/DR/SRで8段階・SL/RRで2段階に
  まで劣化していた、というFITOM_X**本体側のバグ**だった。本リポジトリの
  `banks/OPM/`・`banks/OPZ/`データは元々0-31/0-15ドメインで正しく格納
  されていたため、**データ側の修正は不要**（本体側のシフト削除のみで
  解決）。OPL/OPLLの今回の問題（データ側が変換元生値のまま`<<1`されて
  いなかった）とは原因が逆(本体側の余計なシフト vs データ側のシフト
  漏れ)である点に注意。

### 3.18 FMエンジンDLL名統一: YMEngine → YMFMEngine（2026年7月19日）
FitomEmuIFが読み込むFMエンジンDLLは、旧名`YMEngine`から`YMFMEngine`に
改称された(同一プロジェクト・同一実体で名称のみの変更)。DLLパス解決は
`FitomEmuIF.dll`と同じディレクトリ(`bin/`)を基点に`dll`フィールドの
文字列をそのまま結合する(`FmEmuIfImpl.cpp`の`load_engine_dll()`)ため、
`engines/`配下に配置する構成では`"dll"`フィールドに`"engines/"`
プレフィックスが必須(`fmemuif_opn_profile.json`は元々この形式だった)。
- `config/profiles/hw_plugins/fmemuif_{opl3,opl5,opll5,opm,opm_opl3,
  opm_opz4,fmall}.profile.json`(7件)の`"dll": "YMEngine"`は、名前が
  古いだけでなく`"engines/"`プレフィックスも欠けており、実際には
  `bin/YMEngine.dll`(存在しない)を探す**二重に壊れた設定**だった
  （`fmemuif_opn_profile.json`のみ元から`"dll": "engines/YMFMEngine"`
  で正しかった）。全件`"dll": "engines/YMFMEngine"`に統一。
- `setup.sh`は`YMEngine.so`をコピーするままで、`setup.ps1`側が既に
  `YMFMEngine.dll`に追従済みなのと不整合だった(Windows/Linuxで手当てが
  ズレていた)。`setup.sh`のコピー元・コピー先とも`YMFMEngine.so`に統一。
- `README.md`のディレクトリ構成図・アーキテクチャ概要・依存プロジェクト
  表も追従。ただしプロジェクト名/ディレクトリ名としての`YMEngine`
  (`setup.ps1`の`$Projects.YMEngine`、`setup.sh`の`YMENGINE_BUILD`が
  指す`../YMEngine/`、依存プロジェクト表の1列目)は、上流リポジトリ名
  自体が変わっていないため変更していない(DLLファイル名のみの改称)。
- `config_schema/profile.schema.json`の`devices[].engine`例
  (`"YMEngine"`)は、FITOM_X本体側の同ファイルが2026年7月19日時点で
  未改称のままだったため、config_schemaの同期原則(5.5節、FITOM_X側
  からの直接コピー)に従いあえて追従しなかった。本体側が改称され次第
  同期すること。

### 3.19 vma_convert.pyのALG/AM/WSビット位置バグを修正 + ma2_vma全27ファイル再変換（2026年7月19日）
FITOM_X側コミット`80e25e7`(3.18の前段、`ConnectionSEL`を`ext.ALG_EXT`から
`hw.ALG`のbit2へ再統合)を受けて`banks/OPL3/`配下を調査した結果、
`ext.ALG_EXT`を実際に使っていたのは`opl2_merge/`の派生バンクのみ
（全128パッチ×7ファイルで`ALG_EXT=0`固定、ユーザー確認済みの通り
影響なし）で、`alsa/`系(alsa_convert.py出力)は元々`ALG`のbit2に
ConnectionSELを直接ハードコード済み(4OP変換時`alg = (1<<2)|(con2<<1)|
con1`)だったため無関係と判明。

一方、`tools/voice_convert/vma_convert.py`（`ma2_vma/GMmapFM4op.hwbank
.json`・`Preset4OP.hwbank.json`の変換元）に**別の、より根本的なバグ**を
発見した。VMAフォーマットの解説
(https://pcm1723.hateblo.jp/entry/20080214/1202996791 、著者による
実データ解析に基づく表)によれば、MA-2の音色パラメータ26バイト中の
グローバルバイト(byte3)は`LFO[7:6] | FB[5:3] | ALG[2:0]`という**3bit
のALG**を持つが、`vma_convert.py`は`alg = byte3 & 3`と**2bitしか**
取り出しておらず、4OP結合を示すbit2を常に欠落させていた。

実データで検証済み: `E:\マイドライブ\FITOM\material\fmvoice\vma\`配下の
全27個の.vmaファイルをスキャンした結果、**`Preset4OP.vma`と
`GMmapFM4op.vma`の2ファイルのみ、全128/128パッチでbit2=1**（他の
2OP系ファイルは全パッチでbit2=0）。この2ファイルがまさに本リポジトリの
唯一のOPL3(4OP) ma2_vma変換バンクと一致しており、`& 3`のせいで両ファイル
とも常にConnectionSEL=0（4OP非結合、独立2OPペア×2として動作)のまま
生成されていたことを確認した。

**対応**:
- `vma_convert.py`の`alg = byte3 & 3`を`alg = byte3 & 7`に修正
  (ALGを3bitフルに取り出す)。
- `Preset4OP.vma`・`GMmapFM4op.vma`を修正後のスクリプトで再変換し、
  `banks/OPL3/ma2_vma/{Preset4OP,GMmapFM4op}.hwbank.json`を上書き。
  全128パッチで`ALG`が旧値+4（bit2が立つ）になったことを検証済み。
  再変換により失われる`sw_bank: 0, sw_prog: 2`(変換スクリプトが生成
  しない、過去セッションで別途付与されたデフォルトSwPatch参照)は
  差分比較の上、全パッチに復元済み。ALG以外の差分が無いことも確認済み。
- opl2_merge由来の7ファイルは、上記の通りConnectionSEL=0前提の設計
  (`ALG_EXT`常時0)であり、今回のALGビット拡張(`& 3`→`& 7`)によっても
  実害はない(合成元2OPバンクは元々bit2=0だったファイルのみ使用)。

**副次的に発見した別バグも同時に修正**: 同じ調査中、`vma_convert.py`の
`parse_ma2_op()`におけるオペレータ5バイト目(`AM`/`WS`)のビット位置が、
上記VMAフォーマット解説記事の表(DVB[7:6]|DAM[5:4]|AM[3]|WS[2:0])と
2bitずれていた(旧コードは`AM=(b5[4]>>5)&1`(bit5)・`WS=(b5[4]>>2)&7`
(bits4-2))。この記事の表は著者による実データ解析結果であり、旧コードの
ビット位置を裏付ける記録(コミットメッセージ・コメント等)が一切
残っていなかったため、単純なビット位置ミスと判断して記事の表通り
(`AM`=bit3・`WS`=bits2-0)に修正した。

**対応(AM/WS)**:
- `parse_ma2_op()`の`AM`/`WS`抽出を修正。
- `banks/OPL2/ma2_vma/`(25件)・`banks/OPL3/ma2_vma/`(2件、上記ALG修正
  分と合わせて)、計27件全てを対応する`E:\マイドライブ\FITOM\material\
  fmvoice\vma\*.vma`から修正後のスクリプトで再変換。再変換で失われる
  `sw_bank: 0, sw_prog: 2`は全ファイル全パッチに復元済み。`AM`/`WS`
  (および該当2ファイルの`ALG`)以外のフィールドに差分が無いことを
  全27ファイルについてプログラム的に検証済み。

### 3.20 全ドラムキットにGM2標準チョークグループを追加（2026年7月19日）
`banks/drums/*.drumkit.json`（GM2ノートマッピングのDrumKit群）は、
ハイハット等の相互ダンプ（チョーク、クローズ発音時にオープンを止める等）
を実装していなかった。FITOM_X側の`choke_groups`（drumkitトップレベル、
ノート番号2個以上の配列のリスト。同グループ内のいずれかがNoteOnされると
グループ内の他ノートを強制停止する。`type: "routed"`のみ対応）を使い、
GM2標準の相互排他ノートグループを全ルーテッドドラムキットに一律追加した:
```json
"choke_groups": [[42, 44, 46], [71, 72], [73, 74], [78, 79], [80, 81]]
```
（42/44/46=Closed/Pedal/Open Hi-Hat、71/72=Short/Long Whistle、
73/74=Short/Long Guiro、78/79=Mute/Open Cuica、80/81=Mute/Open
Triangle。GM2仕様のExclusive Class相当）。
- 対象は`type: "routed"`の全15ファイル(`banks/drums/*.drumkit.json`から
  `opl4awm.drumkit.json`を除く全て。`type: "direct"`はスキーマ上
  `choke_groups`を持てない)。
- 該当ノートを含まないキットにも同じグループをそのまま追加した
  （該当ノートが無ければ単に発火しないだけで実害が無いため一律適用、
  との判断）。
- 各ファイル`choke_groups`の1行追加のみで、`notes`配列を含む既存内容は
  一切変更していないことを検証済み。

---

### 3.21 汎用VTLデフォルトのALGキャリア対応化（2026年7月20日）
3.13の「汎用パフォーマンスパッチ」(`sw_bank=0, sw_prog=2`, VTL=80を
4op全てに設定)は、TLが音量として作用するのは**キャリアオペレータのみ**
であり、モジュレータのTLは音色の明るさ（変調の深さ）に作用するという
FM音源の性質を無視して、ALGに関わらず無条件に全opsへVTLを設定していた。
どのオペレータがキャリアになるかはHwPatch自身のALG値とチップ族によって
変わるため、これを修正した。

- `banks/sw/performance_presets.swbank.json`に`prog=24-31`として、
  「VelScale Mid」(`prog=2`)と同じVTL=80を実際のキャリアopsのみに設定
  したバリアントを8種類追加した（キャリアパターンの全組み合わせ、
  詳細は`docs/manuals/swbank.md`の対応表を参照）。全4opがキャリアに
  なるケース(OPN/OPM/OPZのALG=7、OPL3のALG=3)はVTL=80が全opsに乗る
  従来の`prog=2`と一致するため新規progを作らず流用。
- `sw_bank=0, sw_prog=2`を参照している全HwPatch(48ファイル、5298
  パッチ)を対象に、各パッチ自身のALG値・チップ族(OPN/OPM/OPZ=3bit
  ALG、OPL3(4op)=ALG 0-7、OPL(2op)=1bit ALG、OPLL=キャリア固定)・
  オペレータ数から対応する新progへ機械的に付け替えた(5243パッチを
  変更、50パッチはALG=7/3で変更不要、PSG系(`banks/PSG/`,
  1オペレータなのでキャリア/モジュレータの区別が存在せず対象外)の
  336パッチと、`msx_audio_preset_rhythm.hwbank.json`のALG未設定・
  1オペレータの5パッチは非対象として現状維持)。
- 修正範囲は**上記の汎用VTLデフォルトのみ**。`dx100_1`/`dx100_2`/
  `dx11`/`dx21`/`tx81z`/`fb01`等、実機由来で1パッチずつ専用の
  `sw_prog`を持つパフォーマンスバンクは対象外とした(実機が意図的に
  モジュレータのTLにもベロシティ感度を設定していた場合、それを
  機械的にゼロ化すると本来のサウンドデザインを損なう可能性があり、
  リスクに見合わないと判断)。
- **副次的に発見・修正したバグ**: `banks/OPN/gm/necopn_gm.hwbank.json`
  （`tools/voice_convert/necopn_convert.py`の出力）だけが、`ALG`/`FB`/
  `AMS`/`PMS`を`hwbank.schema.json`が要求するパッチ直下のフラット
  フィールドではなく`"hw": {...}`というネストしたオブジェクトの中に
  格納していた。`PatchManager::jsonToHwPatch`はパッチ直下のフラットな
  フィールドしか読まない設計（3.12参照）のため、この128パッチは
  読み込み時に`ALG`が常にデフォルト値（未設定）として扱われていた
  可能性が高い（本リポジトリでは検証不可、FITOM_X本体側での動作確認が
  必要）。今回のALGキャリア対応化が実際に効くための前提として、
  128パッチ全てを他のOPN系ファイル（`music_lalf_*`等）と同じ
  フラット形式に修正した。値そのものは変更していないことをプログラム的
  に検証済み。`tools/voice_convert/necopn_convert.py`の出力ロジック
  自体も同時にフラット出力へ修正済みのため、今後`necopn.bin`から
  再変換しても同じ不具合は再発しない。

### 3.22 hwif/emuif向けPCMメモリイメージカタログを新設・配線（2026年7月20日）
`config_schema/profile.schema.json`の`hw_plugins[].profile`説明が、
ADPCM/PCM系サンプルメモリを要するチップ（YM2608/YM2610/YM2610B/YMF278等）
向けに「PCMメモリイメージカタログ(`pcm_image_catalog.schema.json`参照)」
を予告していたが、本リポジトリには実体が存在しなかった。当初FITOM_X本体
側にも存在しないと誤認してローカル暫定スキーマを作成したが、実際には
`../FitomEmuIF`・`../FitomHwIF`（隣接リポジトリ）のドキュメント
（`FitomEmuIF/README.md`「PCM/ADPCMイメージカタログ」節、
`FitomHwIF/docs/profile-reference.md`「PCMカタログとの連携」節）で
既に具体的な参照方法・フォーマットが規定されており、`FITOM_X/config_schema/
pcm_image_catalog.schema.json`にも正式スキーマが存在していた（本リポジトリの
`config_schema/`への同期漏れだった）。誤った暫定版は破棄し、正式スキーマの
verbatimコピーに置き換えた。

- **フォーマット**: `images`は配列ではなく、種別名をキーとする**オブジェクト**
  （`ADPCM-A` / `ADPCM-B` / `OPNB_ADPCM-B` / `OPNA_RHYTHM` / `OPL4AWM`の5キー、
  1種別1ファイルのみ）。他の`config_schema/*.json`同様、本ファイルは
  FITOM_X本体からのverbatimコピーであり、独自にフィールドを追加しない。
- **パス解決基点の不整合を`../FitomEmuIF`側で修正済み（2026年7月20日）**。
  導入当初、`pcm_catalog`自体（プラグイン固有プロファイル中のカタログへの
  パス指定フィールド）はFitomEmuIF・FitomHwIFとも**指定元プロファイル
  ファイル自身のディレクトリ**基点で解決するのに対し、カタログ**内部**の
  `images{}`の値（実イメージファイルへのパス）はFitomEmuIFのみ**実行時
  カレントディレクトリ**基点（FitomHwIFは最初からカタログファイル自身の
  ディレクトリ基点）という食い違いがあり、同じカタログJSONをhwif/emuif両方
  で共用できなかった。ステージング運用上「カタログファイル基点」の方が
  CWD（起動時の作業ディレクトリ）に依存せず可搬性が高く、かつFITOM_X本体が
  `banks.*[].file`の解決基点をCWD相対から参照元ファイル相対へ変更した経緯
  （3.14参照）とも整合するため、これを正とし、FitomEmuIF側
  （`FmEmuIfImpl.cpp`の`apply_pcm_images()`、`load_engine()`にカタログ
  ディレクトリを引き回すよう変更）をFitomHwIFの`PcmCatalog::load()`と同じ
  規則に合わせて修正した（`../FitomEmuIF`は独立リポジトリのため、本リポジトリ
  とは別にコミットが必要。ビルド確認済み、`bin/FitomEmuIF.dll`は再デプロイ
  済み）。FitomEmuIF側のREADME.md・`pcm_images.catalog.example.json`・
  `CLAUDE.md`（設計判断の経緯6.）も合わせて修正済み。
  - 両プラグインとも「カタログファイル自身のディレクトリ」基点に統一された
    ため、カタログファイルの置き場所はもはやリポジトリルート固定である必要は
    ない。ただし本リポジトリでは変更のリスクを避けるため、現状
    `pcm_image_catalog.json`をリポジトリルート直下に置いたままとしている
    （`images{}`の値`banks/PCM/...`・`roms/...`はそのままリポジトリルート
    相対として引き続き有効）。将来的に`config/profiles/hw_plugins/`配下へ
    移設する場合は、`images{}`の値を移設先からの相対パスに書き換えること。
- **登録イメージ**（`pcm_image_catalog.json`、リポジトリルート直下）:
  - `ADPCM-A` → `banks/PCM/pss680/pss680_opnb_adpcma.bin`（OPNB/OPNBB用）
  - `ADPCM-B` → `banks/PCM/pss680/pss680_opna_adpcmb.bin`（OPNA/Y8950用）
  - `OPNB_ADPCM-B` → `banks/PCM/pss680/pss680_opnb_adpcmb.bin`（OPNB/OPNBB用、
    OPNA/Y8950とはアドレッシング境界が異なるため別イメージ・別キー）
  - `OPNA_RHYTHM` → `roms/ym2608_rhythm.rom`（YM2608内蔵リズム音源ROM）
  - `OPL4AWM` → `roms/yrw801.rom`（YMF278/OPL4のAWM波形ROM）
  - いずれも既存の`*.pcmbank.json`（PatchManagerが読む発音オフセット
    メタデータ）とは別物（生のメモリダンプイメージそのもの）。
- **配線**: ADPCM/AWM対応チップ（OPNA/OPNB/OPNBB/Y8950/OPL4）を含む
  `fmemuif_opn_profile.json`・`fmemuif_fmall.profile.json`・
  `fmemuif_opl5.profile.json`の3件に`"pcm_catalog": "../../../pcm_image_catalog.json"`
  を追加。それ以外のfmemuif_*/fitom_hw_*サブプロファイルは対応チップを
  含まないため未配線（`fitom_hw_*.profile.json`は現状すべてOPN/OPMのみで
  ADPCM対応チップを持つ実機構成が無く、`pcm_catalog`を追加しても意味を
  持たないため見送った。今後OPNA/OPNB実機構成を追加する際に配線すること）。

### 3.23 OPLLのRR=0(キーオフで消音しない)バグを修正 + opll_convert.py新設・再変換（2026年7月20日）
`banks/OPLL/opll_presets.hwbank.json`（PSS-140+SHS-10、125パッチ）の
約70%のキャリアオペレータで`SR=0`かつ`RR=0`になっており、実機で
キーオフしても音が減衰しない(=消音しない)バグをユーザー報告により発見・
修正した。

**原因**: このファイルは3.17時点で「変換元スクリプトがこのリポジトリに
残っていない」と記載した通り、由来不明の一括integrationデータ
（コミット`5752665`、由来不明）だった。`note`フィールド（文字コード破損
していたが復元可能）から、変換時に3.3のOPL系規則（EGTビット=0/
パーカッシブ→`RR=0`）をそのまま適用していたことが判明。しかし3.3に
追記した通り、**OPLLはOPLと異なりキーオフ時に常に`RR`の値を直接RR
レジスタへ書く**ため、`SR`分岐に関わらず`RR=変換元RRレジスタ値`を
格納しなければならない。OPL系向けの規則をOPLLに無条件適用したことが
バグの原因だった。

**対応**:
- `hwbank.json`自身の`source`フィールドに記載されていた実機レジスタ
  ダンプの一次資料URL（`https://github.com/plgDavid/misc/blob/master/
  OPLL%20Synth%20Patches/{pss140_patches.txt,pss140_patches_names.txt,
  shs10_patches.txt}`）を取得し、新規`tools/voice_convert/opll_convert.py`
  でゼロから再変換した（YM2413カスタム音色レジスタR#0-R#7、8byte/音色の
  直接パース。詳細は同スクリプト冒頭コメント・`tools/voice_convert/
  README.md`参照）。
- 再変換の結果、125パッチ中113 opsで`RR`が変化（想定通りの修正）。
  それ以外のフィールドは全パッチ・全opsで一致することをプログラム的に
  検証済み(名前の並び順一致含む)。ただし例外が2件:
  - `prog=1`("Accordion 2")のみ、`RR`以外にも`FB`/`AR`/`DR`/`SL`/`TL`/
    `KSL`/`WS`が旧データと乖離していた。実機レジスタダンプから手計算で
    再検証した結果、新データ（再変換結果）が正しく、旧データ側に
    (原因不明の、この1パッチだけの)別の独立したバグがあったと判断した。
  - モジュレータ(`ops[0]`)側の`WS`(波形選択)ビット位置が、当初想定した
    「R#3の bit5=DM」ではなく、**実データとの照合の結果 bit3=DM**である
    ことが判明（キャリア側`DC`=bit4は当初想定通り）。旧データとの
    全数比較で100/100件一致したため確定。`opll_convert.py`はこの
    正しいビット位置で実装済み。
- **実害の確認**: `ops[0]`(モジュレータ)側のRR=0はOPLLでも実害がない
  （モジュレータの減衰はキャリアの出力音量に対する副次的な音色変化に
  過ぎず、最終的な消音はキャリア側のRRで決まる）。実際に消音しなかった
  のはキャリア(`ops[1]`)側のRR=0のケース（125パッチ中88パッチ、約70%）。

**副次的に判明した事実**: OPLLの`hw.ALG`は音色ごとの接続切替機構が
実機に存在しない（常にモジュレータ→キャリアのFM接続のみ）ため常に0固定。

### 3.24 OPL2/OPL3/OPLL変換スクリプト全体にキャリアRRの最小値補正を追加（2026年7月20日）
3.23のOPLL修正後、ユーザーから「既に変換済みのOPL系hwbankにも同様の
RR=0パッチが残っているので直してほしい」との指摘を受け、`banks/OPL2/`・
`banks/OPL3/`・`banks/OPLL/`配下の全hwbank.jsonを対象に、キャリア
オペレータ（ALGから実際に音声出力に寄与すると判定できるop）に限定して
`SR=0`かつ`RR=0`（実機で事実上消音しない状態）になっている箇所を機械的に
洗い出した。

**判明した内容**: いずれも各変換スクリプト自体のロジックは(3.23までの
修正で)正しく、**変換元の生レジスタ値自体に元々RR=0が含まれていた**
ケースだった(スクリプトのバグではなくデータ起因)。実機上でも
このデータをそのまま焼けば同じ「事実上消音しない」結果になる。
- `Preset4OP.vma`/`GMmapFM4op.vma`(OPL3 4opモード)由来の10音色/ファイル
  （DrawOrgn/PercOrgn/Acordion/ChoirAah/Fr.Horn/SprnoSax/Echoes/Bagpipe/
  RevCymbl/Gunshot、両ファイルで内容重複）。ALG=5/7の音色で、FM直列
  接続なら通常キャリアにならないM1やM2側が、ALG次第で並列(AM)接続により
  実際にはキャリアとして寄与しているケースを含む(3.23までの調査で
  見落としていた箇所)。
- `std.sb`(ALSA sbiload、OPL2)由来の2音色(Guitar FretNoise/Bird Tweet)。
- `opll_presets.hwbank.json`(3.23で再変換済みのもの)側でも19音色。

**対応**: `vma_convert.py`・`alsa_convert.py`・`opll_convert.py`の
3スクリプトに共通の考え方で`carrier_flags()`(ALGからキャリアかどうか
判定。2opは`bit0`、4opは`bit0`/`bit1`/`bit2`(ConnectionSEL)を見る。
OPLLは常にALG=0固定なので`ops[1]`のみキャリア)と`apply_carrier_rr_floor()`
(キャリアかつ`AR>0`かつ`SR=0`かつ`RR=0`の場合のみ`RR=1`に補正、
モジュレータ側は音声出力に寄与しないため対象外)を追加。
`banks/OPL3/ma2_vma/{GMmapFM4op,Preset4OP}.hwbank.json`・
`banks/OPL2/alsa/std_opl2.hwbank.json`・`banks/OPLL/opll_presets.hwbank.json`
の4ファイルを再変換して反映(それぞれ10/10/2/19箇所のRRのみ変更、他の
フィールド・`sw_bank`/`sw_prog`は差分無しをプログラム的に検証済み)。
上記4ファイル以外の全OPL2/OPL3/OPLLバンク(`opl2_merge`由来含む)は
再変換しても差分ゼロだったため未変更。
- 対応後、`banks/OPL2/`・`banks/OPL3/`・`banks/OPLL/`配下の全キャリア
  オペレータで`SR=0`かつ`RR=0`の組み合わせが0件であることを確認済み。

  **【3.25で訂正】**: 本節の「3.23までの修正で各スクリプトのロジックは
  正しい」「`SR>0`なら`RR`は無視される」という前提は誤りだったことが
  3.25で判明した。本節が対応した4ファイルの修正内容自体は結果的に
  正しかったが(いずれも`SR=0`かつ`RR=0`だったため)、`alsa_convert.py`
  由来の他バンク(`SR>0`かつ`RR=0`だった485箇所)が見落とされていた。
  3.25参照。

### 3.25 OPL系のRR変換規則の誤りを訂正 + alsa_convert.py本体バグ修正（2026年7月20日）
3.24の対応後、ユーザーから「FITOM_Xでは、キーオン時に必ずEGT=0として
SR設定値をRRレジスタに書き込み、キーオフ時にEGT=1としてRR設定値を
RRレジスタに書き込む制御をしている。したがってRR設定値が0になっている
とキーオフ時にEGT=1,RR=0が書き込まれ消音しなくなる。これはOPL/OPLL系
特有の制御としてFITOM_Xのドキュメント記載済み」との訂正を受けた。

**判明した誤り**: `docs/voice-parameter-reference.md`の旧記述(および
3.3/3.23/3.24)は「OPLは`updateVoice`一度きりの静的な書き込みで完結し、
`SR>0`のときは実機RRレジスタに`SR`由来の値が書き込まれ`RR`フィールドは
無視される。OPLLだけが`updateVoice`+`updateKey`の2段階書き込みで動的に
RRを切り替える特殊なチップ」としていたが、**これはOPL系のドキュメント
記述そのものが誤っていた**(3.23時点でOPLLについて検証・訂正した際、
OPL系の記述も同様に誤りが無いか裏取りすべきだったが怠っていた)。
実際にはFITOM_XはOPL/OPL2/OPL3もOPLLと全く同じく、キーオン時=常に
実機EGTビット0+`SR`値、キーオフ時=常に実機EGTビット1+`RR`値、という
動的な書き込みを行う。したがって**`RR`は`SR`の値に関わらず常にキーオフ
時に実機へ反映される**ため、`RR=0`のキャリアは`SR`が何であっても
キーオフで事実上消音しなくなる。

**実害**: `alsa_convert.py`の`decode_op()`が、実機EGTビット=0
(パーカッシブ)のとき`RR=0`を明示的に格納していた(3.24時点でもこの
ロジックは「正しい」ものとして温存されていた)。この結果、
`banks/OPL2/alsa/{std_opl2,alsa_drums}.hwbank.json`・
`banks/OPL3/alsa/{std_opl3,alsa_drums}.hwbank.json`の4ファイルで
計485箇所(内訳: std_opl2=109, std_opl3=260, alsa_drums(OPL2)=58,
alsa_drums(OPL3)=58)のキャリアオペレータが、3.24の判定基準
(`SR=0`かつ`RR=0`)では検出されず見落とされていた。また、変換
スクリプトを持たない`banks/OPL2/msx_audio/{msx_audio_preset,
msx_audio_preset_rhythm}.hwbank.json`(3.17参照)にも同じ誤った規則で
変換されたと見られる61箇所が見つかった。

**対応**:
- `docs/voice-parameter-reference.md`のOPL系節・OPLL系節、
  `docs/CLAUDE.md` 3.3を訂正(「OPL/OPL2/OPL3もOPLLと同じ動的書き込み」
  「`RR`は`SR`分岐に関わらず常に変換元RRレジスタ値を格納」に統一)。
- `alsa_convert.py`の`decode_op()`を、`vma_convert.py`/`opll_convert.py`
  と同じく`RR`を実機EGTビットの値に関わらず常に変換元RRレジスタ値と
  なるよう修正(パーカッシブ分岐での`RR=0`ハードコードを撤廃)。
- `vma_convert.py`・`alsa_convert.py`・`opll_convert.py`の
  `apply_carrier_rr_floor()`から`SR==0`条件を撤廃し、キャリアの`RR==0`
  のみで判定するよう統一(`SR`が非ゼロでも`RR=0`は消音しないバグに
  なるため)。
- `banks/OPL2/alsa/{std_opl2,alsa_drums}.hwbank.json`・
  `banks/OPL3/alsa/{std_opl3,alsa_drums}.hwbank.json`を再変換して反映
  (計485箇所のRRのみ変更、他フィールド・`sw_bank`/`sw_prog`は差分無しを
  プログラム的に検証済み)。
- `banks/OPL2/msx_audio/{msx_audio_preset,msx_audio_preset_rhythm}
  .hwbank.json`(変換元スクリプトが本リポジトリに存在しない、3.17参照)は、
  各`note`フィールドに記載された変換規則から同じバグの混入が確認できた
  ため、再変換ではなくデータへの直接パッチで対応: 該当61箇所は全て
  `SR>0`(=`SR`に変換元RRレジスタ<<1の値が残っていた)だったため、
  `RR = SR >> 1`で元のRR値を復元。`SR==0`かつ`RR==0`の箇所(=真に
  復元不能なデータ)は今回0件だった。
- 対応後、`banks/OPL2/`・`banks/OPL3/`・`banks/OPLL/`配下の全キャリア
  オペレータで`RR==0`(`SR`の値を問わず)の組み合わせが0件であることを
  再確認済み。

### 3.26 vma_convert.pyのEGT極性判定が誤りだったことが判明、反転を撤回（2026年7月22日）
3.25までのRR修正作業の副産物として温存していた「MA-2形式のEGTビットは
実機OPLレジスタと極性が逆」という前提（2026年7月19日コミット`872caff`で
導入）が、**そもそも誤りだった**とユーザー指摘により判明した。

**指摘内容**: 「EGT=0なら減衰音、EGT=1なら持続音が正しい」（実機OPLの
標準的な規約と同じ）。

**検証**: `E:\マイドライブ\FITOM\material\fmvoice\vma\`の実ファイルから、
持続音系（Organ/Strings/Choir/Brass/Sax/Flute/Pad等、名前キーワードで
判定）と減衰音系（Piano/Bell/Chime/Marimba/Xylophone/Guitar/Drum等）を
抽出し、キャリアオペレータの生MA-2 EGTビットを全27ファイル・926音色で
統計照合した:
- 持続音系キーワード一致(370音色): **97.6%**が生EGT=1
- 減衰音系キーワード一致(556音色): **83.5%**が生EGT=0

これは実機OPLの規約(EGT=1=サステイン,EGT=0=パーカッシブ)と**そのまま
一致**しており、反転は不要だったことを示す。872caffの反転により、
実際にはオルガン等の持続音系がパーカッシブ(継続減衰)扱いに、ピアノ等の
減衰音系がサステイン(キーオンでは無限に保持)扱いになる、逆方向の
バグが混入していた(872caffのコミットメッセージが挙げた「GrandPiano-2が
SR=0になる」という根拠自体は、当時参照したのが別バンクの別データ
だった可能性が高いが、原因の特定はできていない。いずれにせよ統計的な
裏付けを取らずに1音色の聴感比較だけで結論づけたことが誤りの温床
だった)。

**対応**:
- `vma_convert.py`の`parse_ma2_op()`のSR算出条件を反転前(872caff以前)の
  向きに戻した(`egt_bit==1`→`SR=0`、`egt_bit==0`→`SR=変換元RR<<1`)。
  ただし`RR`は3.25で確立した規則(実機EGTビットの値に関わらず常に
  変換元RRレジスタ値)をそのまま維持している(872caff以前の実装は
  この部分は`RR=0`にしてしまう別のバグを持っていたため、単純な
  リバートではなく現行の正しいRRロジックと組み合わせた)。
- `banks/OPL2/ma2_vma/`(25件)・`banks/OPL3/ma2_vma/`(2件)の全27ファイルを
  再変換。`SR`/`RR`フィールドのみ計4394箇所変更、他のフィールド
  (`AR`/`DR`/`SL`/`TL`/`KSL`/`MUL`/`AM`/`VIB`/`WS`/`FB`/`ALG`)は
  無変更であることをプログラム的に検証済み。
- `banks/OPL3/opl2_merge/`配下の7ファイル(`opl2_merge.py`はSR/RR/EGTを
  再計算せず入力をそのまま引き継ぐ設計、3.10参照)も、対応する合成元
  OPL2バンクのprog単位でops[]が1:1対応することを確認した上で、SR/RRの
  みを同様に反映(構造的な不一致は0件を確認済み)。
- 再変換後のデータでも同じ統計検証を実施し、持続音系キーワード一致の
  98.7%が`SR=0`(サステイン型)になっていることを確認した(減衰音系は
  電子ピアノ等の実際にサステイン寄りの音作りをした音色が一定数含まれる
  ため、オルガン系ほどのクリーンな相関にはならないが、これ自体は
  データの多様性であり異常ではない)。

### 3.27 vma_convert.pyで未使用プレースホルダ枠を出力から除外（2026年7月22日）
MA-2 VMAファイルは128音色(メロディ)/79音色(ドラム)分の固定スロットを
持つが、実際に使われているのはその一部で、残りは全パラメータ0の
未使用プレースホルダ枠になっている。従来の`vma_convert.py`はこれを
除外せず、埋め込み名が空のためGMフォールバック名(`GM_NAMES[prog]`)が
機械的に付与された「名前は付いているのに無音」というパッチとして
そのまま出力していた。ユーザー指摘により発見。

**判定方法**: 全4オペレータ(2opは2つ)で`AR=0`(アタックレートが0=envelope
が一切立ち上がらない=絶対に音が出ない)のパッチをプレースホルダと判定。
実データを検証した結果、この条件に該当する1051音色は**全て**埋め込み名が
空(=GMフォールバック名のみ)であり、意図的に名付けられた音色が誤って
除外される(false positive)ケースは0件だった。バイトパターンも
`00 00 00 00 a0`(4オペレータ共通)という一貫したテンプレート値で、
明確に「未初期化のプレースホルダ」と判断できる。

**対応**:
- `vma_convert.py`の`convert_vma()`に、全opがAR=0のパッチをスキップする
  処理を追加。
- `banks/OPL2/ma2_vma/`(25件)・`banks/OPL3/ma2_vma/`(2件)を再変換。
  計1051音色を除外(内訳は多岐、例: `01_Pno-Bell-OrgBank`128→58、
  `NormalBank-5`128→4)。生存した音色は3.26の修正結果と完全に一致
  (フィールド差分0)であることを検証済み。除外によりprog番号に欠番が
  生じるが、`alsa_convert.py`が未使用エントリ(マジック0x00000000)を
  除外する際も同様に欠番が生じる既存の設計と整合的。
- `banks/OPL3/opl2_merge/`配下、自己合成(`_detuned`系5ファイル)は
  合成元と同じprogが除外されるためそのまま反映(128→58/37/21/43/47)。
  `Luminous_x_Basic`・`MicroComputer_x_Digital`は合成元4バンクとも
  プレースホルダ0件だったため変化なし(128→128)。`opl2_merge.py`は
  2バンクのprog積集合のみ出力する設計(`merge_banks()`)のため、手動で
  PDT等の付与済みフィールドを保つ目的で再実行はせず、既存の合成済み
  ファイルから該当progを直接除外する方式で対応した。

**`banks/OPL2/ma2_vma/{DrumsBank,07_DrumsBank}.hwbank.json`は対象外**:
除外前に、他ファイルからのprog参照が無いかをサブエージェントで全
`*.patchbank.json`/`*.drumkit.json`に対して調査したところ、
`banks/drums/{ma2_preset_2op,ma2_variant_2op}.drumkit.json`
(`unified_preset.profile.json`のbank 113/114、GM2ノート27,28,
31-36,103-105に対応)が、まさにこの2ファイルの空プレースホルダ枠
(prog 0,1,4-9,76-78、実データで内容が完全に一致する同一テンプレート
であることを確認済み)を参照していることが判明した。除外すると
「無音だが存在するパッチへの参照」から「存在しないprogへの参照
(ダングリング参照)」に変わり、ランタイムでの挙動が未定義になる
リスクがあるため、安全側に倒してこの2ファイルのみ3.27の対象から除外し
3.26(EGT極性修正)の状態のまま維持した(`git checkout HEAD --`で復元)。
他の17ファイルについては、対応する`hw_banks[].group`+`bank`番号の
組み合わせを全`*.drumkit.json`と突き合わせ、ダングリング参照が0件
であることを別途プログラム的に再検証済み。
- **副次的に発見した既存の問題(今回は未対応)**: 上記2ファイルの
  該当11 progは今回の変更以前から実データが完全に空(音が一切出ない)
  だった。つまり`ma2_preset_2op`/`ma2_variant_2op`の該当11ドラムノート
  (27,28,31-36,103-105)は、今回の変更の有無に関わらず**元々鳴らない**
  設定になっている。これらのノートに何を割り当てるべきかはデータ
  設計判断が必要なため、今回は現状維持とし4節に記載する。

### 3.28 config/profiles/配下の環境依存フィールドをgit clean/smudgeフィルタで正規化（2026年7月26日）
`config/profiles/*.profile.json`の`midi_inputs`(MIDI入力デバイス名)・
`config/profiles/hw_plugins/fitom_hw_*.profile.json`の`interfaces[].port`
(実機シリアルポート名)は、テスト機ごとに実際の接続環境に合わせて
書き換えざるを得ないフィールドで、従来はテストのたびに`git status`に
無関係な差分が出ていた(典型例: `emu_opn.profile.json`の`midi_inputs`)。

**当初検討し不採用にした案**: `git update-index --skip-worktree`は
副作用が大きい(pullでの更新が作業ツリーに反映されず気づきにくい)ため
不採用。ファイルごとのtemplate化+`.gitignore`も、環境依存フィールドを
持つ全プロファイル(トップレベル7件+hw_plugins3件)に同じ対応を都度
繰り返す必要があり運用の手間が大きいため不採用。

**採用した方式**: gitのclean/smudgeフィルタ(`filter=envlocal`)で
`midi_inputs`配列の全要素・`"port"`の値を`"__LOCAL__"`という
プレースホルダーへ正規化してから索引に格納する。ワーキングツリー側は
実際の値のまま自由に書き換えてよく、`git add`/`git status`/`git diff`
はいずれもクリーンなままになる(それ以外のフィールドの変更は通常通り
検出される)。

- フィルタ本体: `tools/git_filters/normalize_env_fields.py`(標準入力→
  標準出力のテキスト置換のみ。JSONをフルパース→再ダンプする方式は
  一部ファイル(`fitom_hw_*.profile.json`のslots配列等)が1行に詰めて
  書かれたオブジェクトを複数行に展開してしまい無関係な差分を生むため
  不採用。正規表現でのピンポイント置換に留めている)。
- `.gitattributes`: `config/profiles/**/*.json filter=envlocal
  eol=crlf`。フィルタ名の宣言と対象パターンのみで、フィルタの実行
  コマンド自体はセキュリティ上ローカルのgit configへの登録が必須
  (`setup.ps1`/`setup.sh`が自動登録する。手動なら`git config
  filter.envlocal.clean "python tools/git_filters/
  normalize_env_fields.py"` / `filter.envlocal.smudge cat`)。
- **`eol=crlf`が必須な理由**: このリポジトリは`core.autocrlf=true`だが
  `.gitattributes`が元々存在しなかったため、一部ファイル
  (`emu_opl.profile.json`・`emu_opn.profile.json`)は索引にも
  CRLFのまま保存されてしまっていた(本来の`core.autocrlf`の動作では
  索引は常にLFのはず)。`eol=crlf`を指定せず`filter=envlocal`だけ
  だと、cleanフィルタの出力(CRLF保持)に対してさらに`core.autocrlf`の
  checkin変換(CRLF→LF)が二重にかかり、対象2ファイルが全行差分化して
  しまう(1回試して確認済み)。`eol=crlf`を指定すると索引には常にLFで
  正規化されるため、上記2ファイルは初回のみ「改行コード是正+
  フィールド値変更」の差分になるが、既に索引がLFで正しかった残り
  8ファイルは無傷(フィールド値のみの最小差分)になることを確認済み。
- 新しく環境依存フィールドを持つプロファイルを追加する場合、ファイル名
  が`config/profiles/**/*.json`に一致してさえいれば`.gitattributes`の
  追記は不要(パターンマッチで自動適用される)。ただし新しい種類の
  環境依存フィールド(`midi_inputs`/`port`以外)を追加する場合は
  `normalize_env_fields.py`側の正規表現追加が必要。

### 3.29 MIDIシーケンサー向けインストゥルメントリストの自動生成を新設（2026年7月26日、同日中に3.30で構成変更）
`config/profiles/*.profile.json`から、Cakewalk/Sekaiju用`.ins`ファイルと
DOMINO用`.xml`ファイルを機械生成する`tools/instrument_export/
generate_instruments.py`を新設した。当初は当時存在した全11プロファイル
分を`docs/instruments/{sekaiju,domino}/`配下にプロファイルごと個別
ファイルとして生成したが、その後3.30の変更で対象プロファイル・出力
ファイル構成とも変わっている。以下は初版時点の設計メモ。

- **変換ロジック**: `patch_banks[]`→CC#0=0、`hw_banks[].group`→CC#0
  (3.2節のVoicePatchType対応表通り)、`pcm_banks[].group`→CC#0(ADPCMB=81/
  ADPCMA=82)、`drum_banks[]`→CC#0=112という対応で、各バンクファイル
  (`*.hwbank.json`/`*.patchbank.json`/`*.samplezonebank.json`/
  `*.pcmbank.json`/`*.drumkit.json`)の`patches[]`/`entries[]`/`notes[]`
  から`prog`(またはノート番号)と`name`を収集し、CC#0/CC#32/Prog単位の
  一覧に組み立てている。詳細は`tools/instrument_export/README.md`参照。
- **旧プロファイル(`emulator_*`/`hw_*`)のgroup旧称に対応**(初版時点、
  3.30で旧プロファイル自体を削除したため後日不要になった):
  `emulator_opm.profile.json`等はhw_banks[].groupを統合後の命名
  (`OPN2`/`OPZ`/`OPL3_2`)ではなく旧称(`OPN`/`OPM`/`OPL2`)のまま使って
  いたため、当初は変換スクリプト内の`GROUP_CC0_HW`に旧称エイリアスとして
  追加していたが、3.30で旧プロファイル自体を削除したため、現在の
  `GROUP_CC0_HW`にはこのエイリアスは存在しない。
- **sw_banks[]は対象外**: パフォーマンスパッチ(ベロシティ感度・ビブラート
  等)は音色選択そのものではないため、インストゥルメントリストには含めて
  いない。
- **未検証事項**: 生成した`.ins`/`.xml`はいずれもJSON/XMLとしての構文
  検証(XML well-formed性、`.ins`側のセクション名一意性・`Patch[]`添字
  重複無し)のみプログラム的に確認済みで、Sekaiju/Cakewalk/DOMINO本体での
  実際の読み込み動作は未検証。

**【訂正】`.Instrument Definitions`は1プロファイル=1機材にまとめる
（2026年7月26日、ユーザー指摘により同日中に修正）**: 初版はCC#0/CC#32の
バンクごとに独立した`.Instrument Definitions`セクション(バンク単位で
別々の「機材」)を作っていたが、これはSekaiju上でバンクの数だけ別々の
機材として表示されてしまう誤りだった。実機音源の実例
(`Sekaiju8.3/instrument/KORG_KROME.ins`・`Roland_SC-8850.ins`)の
`.Instrument Definitions`節を確認したところ、いずれも1機材=1セクション
であり、その中で持つ全バンクを`Patch[(MSB<<7)|LSB]=<Patch Names
セクション>`として列挙する構成だった。これに倣い、プロファイル全体を
1つのセクションにまとめるよう修正した。あわせて、`Key[]`/`Drum[]`の
第一引数は「対象バンクのPatch[]添字の値と一致させる」という規則も
上記2ファイルから確認した(`GM1_GM2.ins`の`Key[120,0]`のような
「生のBank MSB値のみ」の書き方は例外的で、他2ファイルはいずれも
Patch[]添字と同じ値を使っている多数派のパターンに合わせた)。
ドラムキットは同一セクション内でメロディ音色と混在するため、
`Drum[*,*]=1`のようなワイルドカード指定はできず(メロディ側までドラム
扱いになってしまう)、ドラムキットの`Patch[]`添字ごとに個別に
`Drum[<添字>,*]=1`を立てる方式にした。詳細は
`tools/instrument_export/README.md`参照。
- **Studio One / REAPER対応は保留(2026年7月26日、ユーザー判断)**:
  いずれも本リポジトリの作業環境に実機(実ソフト)が無く動作検証ができない
  ため、Sekaiju/DOMINOの2形式に留めた。Studio Oneは特にDOMINOの`.xml`
  (1ファイル完結)と異なり、パッチ名を独自スクリプト言語の`.txt`
  (`Patchnames`フォルダ、メーカー別)として定義し、そこから実際にDAWで
  使う「デバイス」パネル定義(別のXML、`User Devices`フォルダ配下)を
  生成する2層構造で、`.txt`スクリプトの正確な構文(同梱の
  `script documentation.txt`)も未確認。将来、検証可能な環境が用意でき
  次第、着手を検討する(Studio One側はPreSonusフォーラムの「Instrument
  Definition Manager」ツールや`script documentation.txt`の内容を先に
  確認すること)。

### 3.30 統合前の個別プロファイル6件を削除 + インストゥルメントリストを1ファイルに統合（2026年7月26日）
ユーザー指摘・判断により、2点の大きな構成変更を行った。

**1. 統合前の個別プロファイル(`emulator_*`/`hw_*`、計6件)を削除**:
`emulator_opl3.profile.json`・`emulator_opm.profile.json`・
`emulator_opn_family.profile.json`・`hw_opm_emu_opl3.profile.json`・
`hw_opn_emu_opm_opl3.profile.json`・`hw_spfm_opm.profile.json`は
「誰もメンテナンスしておらず統合後の構成と矛盾している」とのユーザー
判断により削除した。あわせて、これら6件だけが参照し他プロファイルから
参照されていなかった孤立予定のhw_pluginsサブプロファイル6件
(`fmemuif_opl3.profile.json`・`fmemuif_opm.profile.json`・
`fitom_hw_opm.profile.json`・`fmemuif_opm_opl3.profile.json`・
`fitom_hw_opn.profile.json`・`fitom_hw_spfm_opm.profile.json`)も
削除した(削除前に全11プロファイルの`hw_plugins[].profile`参照を
突き合わせ、`fmemuif_opn_profile.json`のように新プロファイル側
(`unified_preset`/`emu_opn`等)からも共有参照されているものは残置)。
これにより、実機(FitomHwIF)構成のプロファイルは本リポジトリから
一時的に無くなった。実機構成が必要になった場合は、削除前のコミット
(`git log -- config/profiles/hw_spfm_opm.profile.json`等で辿れる)を
参照して再構成すること。README.md・setup.ps1のプロファイル一覧・
起動例も合わせて更新済み。

**2. インストゥルメントリストを1ファイルに統合**:
3.29で新設した`generate_instruments.py`は当初、プロファイル(当時11件)
ごとに個別の`.ins`/`.xml`ファイルを生成し、かつ`.Instrument
Definitions`セクションもCC#0/CC#32のバンクごとに分けていた(3.29の
訂正で1プロファイル=1セクションに直したのが直前の修正)。今回さらに
「`.Instrument Definitions`は1セクション=1機材なので、対象プロファイル
全部を1つの`.ins`/`.xml`ファイルにまとめられるはず」とのユーザー指摘を
受け、実際に1ファイルにまとめる設計に変更した。
- 対象は上記1.の削除により残った統合設計6プロファイル
  (`unified_preset`/`emu_opn`/`emu_opl`/`emu_opm`/`emu_opll`/`fmall`)
  のみ。`generate_instruments.py`の`TARGET_PROFILES`辞書に固定リストと
  して定義し、`--profile`引数(旧: 変換対象を指定)は廃止した。
- 出力先を`docs/instruments/sekaiju/<profile>.ins`(プロファイルごと)
  から`docs/instruments/sekaiju/FITOM_X.ins`(1ファイル)に変更。DOMINO側
  も同様に`docs/instruments/domino/FITOM_X.xml`1ファイルに統合。
  Sekaiju側は1つの`.ins`内に6つの`.Instrument Definitions`セクション
  (=6機材)、DOMINO側は1つの`.xml`内に6つの`<Map>`要素(DOMINOの仕様上
  `<Map>`は複数定義できる、`InstrumentList`/`DrumSetList`とも)として
  並べている。
- **`.Instrument Definitions`/`<Map>`の見出し名にマルチバイト文字は
  使えない**とのユーザー指摘を受け、`config/profiles/*.profile.json`の
  日本語`profile_name`をそのまま使うのをやめ、`TARGET_PROFILES`辞書で
  プロファイルキーごとに`"FITOM_X Unified Profile"`のようなASCII名を
  個別に割り当てるようにした(`.Patch Names`/`.Note Names`側のセクション
  名は元々プロファイルキー(ファイル名、常にASCII)ベースだったため
  変更不要)。
- 詳細・対応表は`tools/instrument_export/README.md`参照。

**【訂正】ドラムキットの`drum_banks[].prog`はCC#32ではなくProgram
Change値だった（2026年7月26日、ユーザー指摘により同日中に修正）**:
上記時点の実装は`drum_banks[].prog`をCC#32(Bank Select LSB)相当として
扱い、キットごとに異なる`Patch[(112<<7)|prog]`(Sekaiju)・
`<Bank MSB="112" LSB="<prog>">`(DOMINO)を割り当てていたが、これは誤り
だった。`profile.schema.json`が`drum_banks[]`を「バンク番号概念なし、
常にbank0固定でprogのみで選択」と定義している通り、`prog`は
**Program Change値**であり、CC#0=112・CC#32=0固定の**1つのバンク**の
中でProgram Changeによってキットが切り替わる(GM2ドラムマップの
Bank MSB=120/121固定・PC違いでキット切替、という仕様と同型)。
- Sekaiju側: ドラムキット用`Patch[]`はプロファイルにつき
  `Patch[(112<<7)|0]=<Prog→キット名一覧のPatch Namesセクション>`の
  1エントリのみにし、`Key[(112<<7)|0, <prog>] = <Note Namesセクション>`
  という形でProgram Change値(第二引数)ごとにノート名を切り替えるよう
  修正した(実機の`GM1_GM2.ins`の`[General MIDI Level 2 Drumsets]`と
  同型の構成)。
- DOMINO側: `<DrumSetList>`もキットごとに個別の
  `<PC Name="<キット名>" PC="<prog+1>">`タグ(DOMINOのPC属性は
  1〜128の1-indexedのため`+1`)を作り、その中の`<Bank>`は常に
  `LSB="0"`固定にするよう修正した。
- `DrumKit`データクラスのフィールド名も`cc32`→`prog`に変更し、
  変数名からも意味の取り違えが起きないようにした。

### 3.31 FitomSf2IF(SF2/FluidSynth)対応: unified_preset.profile.jsonへのsf2_banks/sf2_channel_windows新設（2026年7月27日）
FITOM_XにSF2(SoundFont2)/FluidSynth統合機能が追加された(設計検討は
`../FITOM_X/docs/sf2-fluidsynth-integration.md`で確定済み・FITOM_X本体側
実装も完了済み、実際にSF2を鳴らす`IHWPlugin`実装は別リポジトリ
`../FitomSf2IF`、設計は確定済みだが本リポジトリには未ビルド)のを受け、
統合プロファイルにSF2直行パスの配線を追加した。

**事前作業(スキーマ同期)**: `config_schema/profile.schema.json`・
`hwbank.schema.json`・`sccwave.schema.json`をFITOM_X本体から再同期した
(5.5節の運用ルール通り)。前回同期以降、`sf2_banks`/`sf2_channel_windows`
新設に加え、`pcm_banks[].chip`/`group`/`offsets_only`新設・`master_volume`/
`master_pitch`新設・`midi_backend`の説明文がRtMidi統一実装を反映、と
複数の差分が溜まっていたため、まとめて反映した。`hwbank.schema.json`の
差分はOPL3 `ALG`のConnectionSELビット統合(3.19関連)に伴う説明文更新のみ
(実データ・バリデーション結果に影響なし)、`sccwave.schema.json`は内容差分
なし(改行コードのみ)。同期後、既存11プロファイル全件が新スキーマでも
バリデーション(`jsonschema`)を通過することを確認済み。

**`unified_preset.profile.json`への配線**:
- `hw_plugins[]`に`FitomSf2IF`(`FitomSf2IF.dll`)を追加。設定ファイルは
  新設`config/profiles/hw_plugins/fitom_sf2if_profile.json`
  (`../FitomSf2IF/sf2if_profile.example.json`の内容をそのまま流用、
  audio_driver等は既定値のまま)。
- `devices[]`(このプロファイルには元々存在せず、FitomEmuIF側は
  `hw_plugins[].auto_devices`で自動生成されていた)を新設し、
  `{ "if": "HW", "chip": "SF2", "plugin": "FitomSf2IF" }`の1エントリのみ
  配置(設計ドキュメント4節⑥の通り、`serial`/`port`/`slot`等FM/PSG固有
  フィールドは一切指定しない)。
- `banks.sf2_banks`に、`docs/sf2_source.txt`記載順(General User GS→
  YAMAHA RX5→YAMAHA RX11→YAMAHA RX15 Drums→Phoenix MT-32→CMI Orchestra
  Hit)・各ファイル内は`sf2_bank`昇順で計10エントリ(`bank`0-9)を登録した。
  各sf2ファイルの内部バンク構成は、本リポジトリに`fluidsynth`本体や
  sfinfo相当のツールが無いため、SF2(RIFF)ファイルの`phdr`(preset header)
  チャンクを直接パースするワンオフスクリプトで実データから確認した。

  | bank | file | sf2_bank | 内容 |
  |---|---|---|---|
  | 0 | GeneralUser GS v1.471.sf2 | 0 | GM128 melody |
  | 1 | GeneralUser GS v1.471.sf2 | 128 | GM percussion(標準) |
  | 2 | YAMAHA_RX5.sf2 | 0 | RX5 単発melodic(Timpani/Gunshot) |
  | 3 | YAMAHA_RX5.sf2 | 1 | RX5 DX系melodic抜粋(Clav/Marimba/EBass/Orch) |
  | 4 | YAMAHA_RX5.sf2 | 128 | RX5 ドラムキット5種(Standard/IncludeRom/Power/Electric/Rock) |
  | 5 | Yamaha_RX11.sf2 | 128 | RX11 ドラムキット5種 |
  | 6 | Yamaha_RX15_Drums.sf2 | 0 | RX15 ドラムキット(単一) |
  | 7 | Phoenix_MT-32.sf2 | 0 | MT-32 melodic 128パッチ |
  | 8 | Phoenix_MT-32.sf2 | 128 | MT-32 リズムバリエーション11種 |
  | 9 | CMI_Orchestra_Hit_Soundfont.sf2 | 0 | CMI Orchestra Hit(単一) |

  `GeneralUser GS v1.471.sf2`はこの他にbank1-16(GS variation、楽器の
  ごく一部だけを差し替えた別ティンバー集)・bank120(GS方式percussion、
  bank128と内容重複する旧形式)も持つが、今回は主要な2バンク(0, 128)のみ
  登録し、GS variation群は登録を見送った(4節に記載)。
- `sf2_channel_windows`は、既存の`midi_inputs`2件(`[0]`=loopMIDI Port 1→
  MPU0、`[1]`=microKEY-25→MPU1)のうちMPU0(DAW/シーケンサー想定)のch12-15
  の4chを`fluidsynth_chan`0-3へ静的に割り当てる暫定値とした(MPU2/3は
  本プロファイルの`midi_inputs`に対応デバイスが無く、窓を割り当てても
  MIDIメッセージ自体が届かず機能しないため除外)。既存のCC#0ベースの
  ネイティブ経路(ch0-11)との衝突を避けるための控えめな初期値であり、
  実際の運用(同時に何パート鳴らすか等)に応じて要調整。
  **【2026年8月2日、3.36で変更】** ユーザー指示によりデフォルトを
  ch14/15(0起算)の2chのみに変更した。本節(3.31)のch12-15/4chという
  記述は初版時点の記録としてそのまま残してある。

**未検証**: `FitomSf2IF`プラグイン本体は`../FitomSf2IF`側で設計・実装
済みだが、本リポジトリに`FitomSf2IF.dll`としてビルド・配置されていない
ため、今回の設定一式はJSON構文・スキーマレベルの検証(`jsonschema`)と
参照ファイルの実在確認のみ行った。実際に`fitom_core.exe`上でSF2が鳴る
ことは未確認(4節に記載)。

---

### 3.32 banksセクションを外部ファイル化し、6プロファイルで共有参照するよう変更（2026年7月29日、FITOM_X側コミットb672de2に追従）
FITOM_X本体側に`banks`セクションの外部ファイル参照機能
（`"banks": "<ファイルパス>"`という文字列を指定すると、参照先JSON
オブジェクトの内容がそのまま`banks`として展開される。パス解決基点は
プロファイル自身のディレクトリ）が新設されたのを受け、ユーザー指摘
（「デバイス構成とバンクセット構成を分離した方がマニュアルがシンプルに
なる」）により、6プロファイル全件の`banks`直書きを廃止し、単一の外部
ファイル`config/profiles/unified.bankset.json`への参照に統一した。

**事前作業(スキーマ同期)**: `config_schema/profile.schema.json`の
`banks`をFITOM_X本体の最新版（`oneOf`: 文字列 or 従来のオブジェクト
直書き）に再同期。

**移行內容**: `unified_preset.profile.json`が持っていた`banks`
オブジェクト（hw_banks 63件・sf2_banks 10件・sw_banks 7件・
patch_banks 5件・drum_banks 21件・pcm_banks 2件）をそのまま
`config/profiles/unified.bankset.json`へ切り出し、6プロファイル全件の
`banks`を`"unified.bankset.json"`という文字列参照に置き換えた。

**移行前の差分調査で判明した事実（重要）**: 5プロファイル
（`emu_opn`/`emu_opl`/`emu_opm`/`emu_opll`/`fmall`）の旧`banks`は、
`hw_banks`/`sw_banks`はunified_presetの完全なコピー（bank番号も
一致、hwbank.json内部の`sw_bank`/`sw_prog`参照との整合を保つため
意図的に維持されていたもの、fmallの`_comment`参照）だった一方、
`patch_banks`/`drum_banks`/`pcm_banks`は各プロファイルが「そのチップ
向けの既定バンクをローカルでbank/prog 0に付け替える」という個別の
再番号付けを行っていた。単純に`unified_preset`の値へ差し替えると
以下2点が失われることが判明したため、統合前に`unified.bankset.json`
側へ追加してカバーした:
- `patch_banks`: `emu_opll`が参照していた`gm_layered_opll.patchbank.json`・
  `fmall`が参照していた`gm_layered_opl4awm.patchbank.json`は、
  旧`unified_preset.profile.json`の`patch_banks`(5件)に**そもそも
  含まれていなかった**（各プロファイルが独自追加していたファイル）。
  そのまま差し替えるとこの2ファイルがどのプロファイルからも
  参照されなくなり、OPLL/FMALLの通常モードGM128パッチバンクが完全に
  無音になるところだった。`unified.bankset.json`の`patch_banks`に
  bank5/bank6として追加。
- `pcm_banks`: `emu_opn`が持っていた3件目のエントリ
  （`group=ADPCMB, chip=OPNB, offsets_only=true`、OPNB/OPNBB用ADPCM-B
  の物理オフセットテーブル。OPNAとはバウンダリ整列が異なるため別建てが
  必要、`pcmbank.schema.json`の`chip`説明参照）は、旧`unified_preset`
  の`pcm_banks`(2件、OPNA想定)に含まれていなかった。そのまま差し替える
  とOPNB/OPNBBのADPCM-B発音時のオフセット計算が誤ったものになる
  ところだった。`unified.bankset.json`の`pcm_banks`にbank2として追加し、
  同一group内でchip違いを併用するため（スキーマの規則通り）既存bank0にも
  `"chip": "OPNA"`を明示。
- `drum_banks`は各プロファイルのローカルbank/prog0エントリ
  （`opll_rhythm.drumkit.json`・`opl_builtin_rhythm.drumkit.json`等）が
  いずれも`unified_preset`側に(別のprog番号で)既に含まれていたため、
  ファイルの追加は不要だった（番号が変わるのみ）。

**この移行による既知の挙動変化**: 上記の通りファイル自体の消失は防いだ
が、各プロファイルの「通常モード(CC#0=0,CC#32=0)でbank/prog=0が指す
パッチバンク/ドラムキット」は、旧来のチップ固有デフォルト
（例: `emu_opn`なら`necopn_gm.patchbank.json`）から、全プロファイル
共通の`gm_layered_skeleton.patchbank.json`（`patch_banks`bank0）に
変わった。各チップ固有のGM128バンクは消えたわけではなく、
`unified.bankset.json`が定義する新しいbank/prog番号
（`docs/manuals/emu_profiles.md`に反映済み）で引き続き選択できる。
単一の共有カタログである以上、5チップ分の「それぞれのbank0」を同時に
維持することはできない（同じbank番号に複数チップ分のファイルを
同時に割り当てられないため）ことによる、設計上不可避のトレードオフ。

**検証**: 6プロファイル全件・`unified.bankset.json`単体とも
`jsonschema`で`profile.schema.json`に対して検証済み。
`unified.bankset.json`が参照する111件中101件（`sf2/`配下の10件を除く、
配布対象外のためgitignore対象、3.31以前から未コミット）の実ファイル
存在を確認済み。

**この移行により4節の以下の項目が解消**: 「`emu_opm`/`emu_opll`の
`drum_banks`が統合プロファイルのまま全15件を引き継いでおり絞り込みが
必要か要検討」という項目は、そもそも全プロファイルがカタログ全体を
共有参照するのが設計原則（3.32）になったことで前提が変わり、
「絞り込み」自体が不要という結論になった（README.mdの設計原則通り、
デバイス構成に含まれないバンクエントリは単に発音しないだけで実害が
ない）。

### 3.33 `bank_overrides`で6プロファイルのレイヤードバンク0/ドラムキット0の無音を解消（2026年7月30日、FITOM_X側コミットc2bbe83に追従）
3.32の移行で判明していた「通常モード(CC#0=0,CC#32=0)のデフォルトパッチ
（レイヤードバンク0`patch_banks`bank0・ドラムキット0`drum_banks`prog0）
が全プロファイル共通で無音になる」という既知の挙動変化に対応するため、
FITOM_X本体側に新設された`bank_overrides`（`banks`と同一スキーマ、
識別キー一致で置換・不一致で追加、削除は不可）を使い、6プロファイル
それぞれにそのプロファイルへ必ず存在するデバイス向けのバンクを
bank0/prog0として割り当てた。

**事前作業(スキーマ同期)**: `config_schema/profile.schema.json`を
FITOM_X本体最新版から丸ごとコピー。`banks`オブジェクト形式の定義を
`definitions.banksObject`へ切り出し、新設の`bank_overrides`
（`banks`と同じ`oneOf`(文字列/オブジェクト)）が`$ref`で共有する形に
リファクタリングされている。

**各プロファイルへの割り当て**（`patch_banks`は`bank`、`drum_banks`は
`prog`が識別キー。カッコ内は`unified.bankset.json`側で同一ファイルが
既に使われている番号で、重複を許容する運用）:

| プロファイル | レイヤードバンク0 | ドラムキット0 |
|---|---|---|
| `emu_opn` | `necopn_gm.patchbank.json`(bank1と重複) | `pss560_opnb.drumkit.json`(prog21と重複) |
| `emu_opl` | `gm_layered_opl2.patchbank.json`(bank2と重複) | `opl_builtin_rhythm.drumkit.json`(prog13と重複) |
| `emu_opm` | `gm_layered_opm.patchbank.json`(bank4と重複) | `gm2_standard.drumkit.json`(新規) |
| `emu_opll` | `gm_layered_opll.patchbank.json`(bank5と重複) | `opll_rhythm.drumkit.json`(prog12と重複) |
| `fmall` | `gm_layered_opl4awm.patchbank.json`(bank6と重複) | `opl4awm.drumkit.json`(prog15と重複) |
| `emu_fmgen_opn` | `necopn_gm.patchbank.json`(bank1と重複) | `pss560_opnb.drumkit.json`(prog21と重複) |

いずれも3.32以前（統合前）に各プロファイルがローカルで持っていた
bank0/prog0の再番号付けと同じファイルを踏襲している（`5f2d080^`時点の
各`banks.patch_banks`/`banks.drum_banks`をgit履歴から復元して確認）。
`unified_preset.profile.json`はSF2(FluidSynth)デバイスのみでHWチップを
一切持たないため対象外とした（`bank_overrides`のレイヤードバンク/
ドラムキットはCC#0/CC#32経由の通常モードHwPatch解決でのみ使われ、
SF2直行パスとは無関係）。

`emu_opm`（OPM×2/OPZ×2構成）だけは、`unified.bankset.json`の
`drum_banks`にOPM/OPZ固有のchip依存ドラムキットが1件も存在しない
（`voice_patch_type`固定の`opna_builtin`/`opl_builtin_rhythm`/
`opll_rhythm`等はいずれも別チップ向け）ため、代わりに
`gm2_standard.drumkit.json`を採用した。このファイルは特定チップに
依存せず、全61ノートが`patch_bank=0`（＝このオーバーライドで
`gm_layered_opm.patchbank.json`に差し替え済みのレイヤードバンク0）
経由で発音する設計のため、OPMデバイスでも問題なく鳴る（ユーザー確認済み）。

**検証**: 6プロファイル全件を`jsonschema`で更新後の`profile.schema.json`
に対して再検証しVALID、`bank_overrides`が参照する全10ファイルの実在も
確認済み。`bin/fitom_cli.exe`での実行時ロード確認は試みたが、
同梱バイナリが2026年7月28日ビルド（`bank_overrides`実装
[FITOM_X側コミットc2bbe83、7月29日]より前）のため、この環境では
`PatchBank 0 not found`/`DrumPatch not found bank=0 prog=0`が引き続き
出力される（バイナリ未更新が原因であり、プロファイル側の設定不備では
ない）。`bank_overrides`対応版でのビルド後、実機/実プラグイン環境での
再確認が必要。

### 3.34 generate_instruments.pyをbanks外部ファイル参照/bank_overridesに対応（2026年7月31日）
3.32/3.33の変更後、`tools/instrument_export/generate_instruments.py`
(3.29/3.30参照)を未対応のまま実行すると、`banks`が文字列(外部ファイル
参照)であることを想定していない旧コードが`AttributeError: 'str' object
has no attribute 'get'`で停止する状態になっていた。ユーザー指示
「統合パッチバンクプロファイルに基づいてインストゥルメントリストを
更新してほしい」を受け、以下を対応した。

- `resolve_banks_dict()`: `banks`/`bank_overrides`いずれも文字列(外部
  参照)・オブジェクト直書きの両方を受け付けるようにした。
- `apply_bank_overrides()`: `bank_overrides`を識別キー一致で置換・
  不一致で追加する形でマージ。識別キーはセクションごとに異なる
  (`profile.schema.json`の`bank_overrides`説明文通り): `hw_banks`は
  `group`+`bank`の複合キー、`pcm_banks`は`bank`+`chip`の複合キー、
  `drum_banks`は`prog`、それ以外(`sw_banks`/`patch_banks`/`sf2_banks`/
  `scc_wave_banks`)は`bank`単独。
- `TARGET_PROFILES`に新設プロファイル`emu_fmgen_opn`(FmGenエンジン版
  OPN、`emu_opn`と同構成でエンジンのみ異なる)を追加(7件に)。
- **レイヤードバンク0・ドラムキット0はGM標準へ強制統一**(ユーザー指示
  「レイヤードパッチ0、ドラムキット0はプロファイルごとに違いがあるが、
  インストゥルメントリストとしてはGM標準で良い」に対応): 3.33の
  `bank_overrides`により`patch_banks`bank=0・`drum_banks`prog=0は
  プロファイルごとに実際に鳴るファイルが異なる(例:
  `emu_opn`→`necopn_gm.patchbank.json`、`emu_opl`→
  `gm_layered_opl2.patchbank.json`)が、これらを`load_profiles()`内で
  無条件に`banks/patches/necopn_gm.patchbank.json`(GM128標準音色名)・
  `banks/drums/gm2_standard.drumkit.json`(GM2標準ドラムマップ、`name`
  は`data.get("name")`「GM2 Standard Kit」を使わせるため`db`側の
  `name`は除去)へ差し替える`force_gm_standard_bank0()`を追加し、
  `bank_overrides`のマージ結果に対して`banks`/`bank_overrides`解決の
  最後に適用する。プロファイル間でbank0/prog0の表示が統一される一方、
  実際に発音する内容とインストゥルメントリストの表示が一致しない
  プロファイルがある(意図した挙動)。
- 検証: `.ins`は666セクションで名前重複なし、`.xml`は`encoding`宣言を
  一時的にUTF-8へ差し替えた上で`xml.etree.ElementTree`によるwell-formed
  検証をパス(Shift_JISのままでは`ElementTree`がmulti-byteエンコーディング
  を直接扱えないための回避策、恒久的な検証コードには未組み込み)。
  生成結果は7プロファイル・melodic 44072パッチ・drum_kits 160キット
  (全プロファイルが同一の共有カタログ`unified.bankset.json`を参照する
  設計(3.32)のため、バンク一覧自体は各プロファイルで同一内容になる)。
- 詳細は`tools/instrument_export/README.md`参照。

### 3.35 AWMサンプルゾーンに波形ごとのピッチ/音量校正フィールドを追加（2026年8月2日、FITOM_X側コミット830e59aに追従）
FITOM_X本体側で「OPL4 AWMのFnumber/Octave計算式がAWM用でなく、波形ごとの
ピッチ/音量校正データも欠落していた」バグが修正されたのを受け、5.5節の
運用ルール通り`config_schema/samplezonebank.schema.json`を本体側から
丸ごとコピーし、あわせて実データ2件も同期した。

**本体側で判明していた根本原因**（詳細は`../FITOM_X/docs/chip-driver-architecture.md`
「Fnumber/Octave計算式と波形ごとのピッチ/音量校正」節）:
1. `COPL4AWM::getFnumber()`がOPN/OPM系FM合成用の`getFnumberFromHz()`を
   誤って流用しており、AWMエンジン(ymfm)の
   `step=((0x400|fnum)<<(octave+7))>>2`という別の式・符号付き4bit Octave
   (-8〜+7)と噛み合っていなかった。
2. YRW801のROM波形は実測でないと絶対ピッチ・音量が分からない(ウェーブ
   テーブルヘッダに情報が無い)ため、1を直しても波形ごとの校正データが
   無いと数オクターブ単位でピッチがずれる。

**スキーマ差分**（`SampleZone`=`zones[]`の各要素に4フィールド追加、いずれも
既定値を持つ任意フィールドのため既存データは無変更でも引き続きvalid）:

| フィールド | 型/範囲 | 既定 | 意味 |
|---|---|---|---|
| `pitch_offset` | integer -32768〜32767 | 0 | 波形ごとのピッチ校正値(100/128セント単位) |
| `key_scaling` | integer 0〜1000 | 100 | ノート追従率(%、100=通常追従、0=固定ピッチ) |
| `tone_attenuate` | integer 0〜127 | 0 | 追加減衰量(7bit、加算) |
| `volume_factor` | integer 0〜254 | 254 | 音量スケール(254=無補正、実装側は`(254-att)*volume_factor/254`と適用) |

いずれもALSA `sound/drivers/opl4/yrw801.c`の`opl4_sound`構造体の同名
メンバーと**同一規約**（本体実装もALSAの`snd_opl4_update_pitch()`/
`snd_opl4_update_volume()`と同じ適用式）。**OPL4AWM以外のチップ
(ADPCM-B/PCMD8等、`root_note`ベースでピッチを計算する)では未使用**。
`root_note`の説明も「Fnumber計算がチップ側で完結するため未使用」から
「`pitch_offset`/`key_scaling`ベースの計算を使うため未使用」に改められている。

**実データの同期**: `banks/OPL4AWM/opl4awm_yrw801_gm.samplezonebank.json`
(128パッチ/553ゾーン)・`opl4awm_yrw801_drum.samplezonebank.json`
(1パッチ/57ゾーン)を、本体側の`config/profiles/`配下の原本
（yrw801.cから機械抽出した校正値を`wave_index`完全一致でマージ済み、
欠落・曖昧一致ゼロで全件マッチ）から上書きコピーした。
- 差分は**全ゾーンへの上記4フィールド追加のみ**で、`wave_index`/`key_min`/
  `key_max`/`name`等の既存フィールドに変更は無いことを確認済み。
- 全610ゾーンに4フィールドが揃っていること、および両ファイルが更新後の
  `samplezonebank.schema.json`でvalidであることを`jsonschema`で検証済み。
- 実測値の分布(参考): GM側は`pitch_offset` -750〜9853 / `key_scaling`
  5〜100(固定ピッチ系の波形を含む) / `tone_attenuate` 0〜68 /
  `volume_factor` 40〜254。ドラム側は`key_scaling`=100・
  `tone_attenuate`=0で一律、`volume_factor`は204〜244。

**`docs/voice-parameter-reference.md`のOPL4 AWM節も更新**: `SampleZone`
フィールド表に上記4フィールドを追加し、校正の必要性の説明・4フィールド入りの
JSON例に差し替えた。あわせて、2026年7月の`sw_bank`/`sw_prog`新設
(`SampleZonePatch`へのSwPatch紐づけ)が本リポジトリ側の同節に未反映だった
のも同時に追従した。バンクファイルのパスは本体側原本の`config/profiles/...`
ではなく、本リポジトリの実配置である`banks/OPL4AWM/...`に書き換えている
(本体側原本との意図的な差分。同節に注記済み)。

**未検証**: 本体側の`getFnumber()`/`updateVolExp()`修正込みのバイナリが
本リポジトリの`bin/`にビルド・配置されていないため、実際にAWMが正しい
音高・音量で鳴ることは未確認（JSON構文・スキーマ検証のみ済み）。4節に記載。

---

### 3.36 全7プロファイルにSF2(FluidSynth)デバイス定義を配線 + sf2_channel_windowsのデフォルトをch14/15の2chに変更（2026年8月2日）
3.32で`banks`が`unified.bankset.json`への共有参照に統一されたことで、
全7プロファイル(emu_fmgen_opn追加済み、3.34参照)が`sf2_banks`(10件)を
間接的に持つ状態になっていたが、`devices[chip="SF2"]`エントリを実際に
持つのは`unified_preset.profile.json`のみだった。設計ドキュメント
(`../FITOM_X/docs/sf2-fluidsynth-integration.md`4節⑦)により、
`sf2_banks`/`sf2_channel_windows`に何らかのエントリがあるにもかかわらず
`chip=="SF2"`のdevices[]エントリが存在しない場合はFITOM_X起動時エラーに
なる仕様のため、この状態のままでは`unified_preset`以外の6プロファイルは
いずれも起動できない可能性が高かった。

ユーザー指示により、まず`emu_opll`/`emu_opm`の2件へSF2デバイス定義を
追加し、続けて残り`emu_opl`/`emu_opn`/`fmall`/`emu_fmgen_opn`の4件にも
同様の対応を行い、これで全7プロファイルが`devices[chip="SF2"]`を持つ
状態になった。

- `emu_opll.profile.json`: `hw_plugins[]`には既に`FitomSf2IF`が登録済み
  だった(登録時期・経緯不明、`devices[]`側の対応するエントリが欠落した
  半端な状態だったと見られる)。既存の`devices[]`(当時はOPLL/OPLL2
  [rhythm]/OPLLP/VRC7/OPLLXの5件、3.28コミット`00eea3c`で明示化済み。
  OPLL2はこの直後に3.37で削除)に`{chip:"SF2", plugin:"FitomSf2IF"}`を
  追加。
- `emu_opm.profile.json`/`emu_opn.profile.json`/`fmall.profile.json`/
  `emu_fmgen_opn.profile.json`: いずれも`hw_plugins[]`に`FitomSf2IF`が
  未登録だったため新規追加。`devices[]`自体がこれらのプロファイルには
  存在しなかった(FitomEmuIF側`auto_devices:true`のみでチップ構成を
  自動生成する設計、3.32時点から変更なし)ため、SF2用の1エントリのみを
  持つ`devices[]`を新設した(unified_presetの前例と同じく、
  `auto_devices`と明示`devices[]`の併用はスキーマ上許容されている)。
- `emu_opl.profile.json`: 既存の`devices[]`(Y8950[rhythm]/OPL3/OPL4の
  3件)に`{chip:"SF2", plugin:"FitomSf2IF"}`を追加。

**`sf2_channel_windows`はch14/15(0起算)の2chをデフォルトとする方針に
変更**(ユーザー指示。3.31/3.36初版ではch12-15の4chを割り当てていたが、
「MIDI CH14, 15をデフォルトでsf2チャンネルに割り当てる」という指示に
伴い、`unified_preset`/`emu_opll`/`emu_opm`を含む全7プロファイルで
ch14→`fluidsynth_chan`0、ch15→`fluidsynth_chan`1の2エントリに統一)。
割り当て先MPUは、各プロファイルの`midi_inputs`で"loopMIDI Port 1"
(DAW/シーケンサー想定)が指すMPU番号に合わせた(プロファイルごとに
`midi_inputs`配列内の並び順が異なるため、MPU番号もプロファイルごとに
異なる):

| プロファイル | loopMIDIのMPU番号 | sf2_channel_windowsのmpu |
|---|---|---|
| `unified_preset` | 不明(`__LOCAL__`×2) | 0(暫定) |
| `emu_opl` | 1(`midi_inputs[1]`) | 1 |
| `emu_opll` | 1(`midi_inputs[1]`) | 1 |
| `emu_opm` | 不明(`__LOCAL__`×2) | 0(暫定) |
| `emu_opn` | 不明(`__LOCAL__`×4) | 0(暫定) |
| `fmall` | 不明(`__LOCAL__`×2) | 0(暫定) |
| `emu_fmgen_opn` | 0(`midi_inputs[0]`) | 0 |

`midi_inputs`が`__LOCAL__`(3.28のgit clean/smudgeフィルタによる環境
依存値のプレースホルダ)のプロファイルは、どちらがDAW側か本リポジトリ
からは判別できないためMPU0を暫定値とした。

**検証**: 全7プロファイルとも`jsonschema`で`profile.schema.json`に対して
再検証しVALID。ただし`chip=="SF2"`デバイス存在チェック自体はJSON Schema
では表現できないFITOM_Xローダー側の実行時バリデーションのため、本
リポジトリからは検証できない(4節参照)。

### 3.37 OPLLエミュプロファイルからOPLL2を削除（2026年8月2日）
`emu_opll`のOPLL系チップ構成を5チップから4チップ(OPLL/OPLLP/VRC7/OPLLX)へ
変更した。**エミュレーションエンジン(YMFMEngine)がOPLL2に対応していない**
ためで、意図的な削除である(ユーザー判断)。

- `config/profiles/hw_plugins/fmemuif_opll5.profile.json`: `chips[]`から
  `{chip:"OPLL2", clock:3579545}`を削除。
- `config/profiles/emu_opll.profile.json`: `devices[]`からOPLL2の独立
  エントリを削除し、**ビルトインリズムはOPLL側の`rhythm_mode: true`へ
  移した**(従来はOPLL=リズム無効・OPLL2=リズム有効という2デバイス構成で
  役割を分けていた。3.5節のOPLLビルトインリズム、および`rhythm_mode`
  プロファイル設定によるOPLL系リズム制御は、この1デバイス構成でも
  そのまま有効)。
- ファイル名`fmemuif_opll5.profile.json`の"5"は5チップ構成に由来するが、
  参照元(`emu_opll.profile.json`の`hw_plugins[].profile`)の書き換えを伴う
  改名はリスクに見合わないため、名前はそのままとした。

**追従した記述**(いずれもOPLL2を含む5チップ構成のままだった):
`config/profiles/emu_opll.profile.json`の`profile_name`・`README.md`の
ディレクトリ構成図・`setup.ps1`のプロファイル一覧・`docs/CLAUDE.md`2節の
プロファイル一覧表および3.36節・`docs/manuals/emu_profiles.md`の
「OPLLエミュプロファイル」節のチップ構成。
- `docs/voice-parameter-reference.md`の`COPLL2`に関する記述(165行目付近の
  見出し・212行目のFnumberビット配置の注記)は**変更していない**。これらは
  FITOM_X本体側のチップドライバクラスの仕様説明であり、本リポジトリの
  特定プロファイルがそのチップを構成に含むかどうかとは別の話のため
  (本体側にドライバ自体は引き続き存在する)。

### 3.38 OPLLビルトイン音色・OPLLビルトインリズム・OPNAビルトインリズムをインストゥルメントリストに追加（2026年8月4日、ユーザー指摘）
`generate_instruments.py`(3.29/3.30/3.34)は`hw_banks[]`/`drum_banks[]`を
走査してバンク一覧を組み立てるため、これら配列に一切現れない「ファイルを
持たない機械合成バンク」3種類(3.6節のOPLL Built-In ROM音色、3.5節の
内蔵リズム音源)がインストゥルメントリストから漏れていた。実際のパッチ名/
楽器名はFITOM_X本体(`../FITOM_X`)のC++ソースにハードコードされている
ため、本体を調査の上、名前を転記して追加した。

- **OPLLビルトイン音色**(CC#0=40・CC#32=0固定、`core/src/
  PatchManager.cpp`の`initOpllRomPatches()`内`kNames[4][16]`): variant
  (0=OPLL/OPLL2, 1=OPLLX, 2=OPLLP, 3=VRC7)ごとに15音色(index1-15、
  index0は各variant共通で無音のダミーのため未収録)。`Prog =
  (variant<<4)|instIndex`。ソースコメントには「非公式・耳コピ由来の
  近似データ」との注記があり、正式なROM名と異なる可能性がある。
- **OPLLビルトインリズム**(CC#0=112・CC#32=40固定、`gui/bridge/
  FITOMBridge.cpp`の`kOpllRhythmNames[]`): Prog(楽器番号)0-4 =
  Hi-Hat/Top Cymbal/Tom/Snare Drum/Bass Drum。
- **OPNAビルトインリズム**(CC#0=112・CC#32=17固定、同ファイルの
  `kOpnaRhythmNames[]`): Prog(楽器番号)0-5 = Bass Drum/Snare Drum/
  Top Cymbal/Hi-Hat/Tom/Rim Shot。
- これら2つのビルトインリズムは、CC#0=112配下の内蔵リズム音源専用選択
  であり、`drum_banks[]`由来の通常ドラムキット(CC#0=120固定・CC#32=0
  固定、Progでキット選択。3.39節参照)とは全く別のCC#0を使う別軸
  (3.5節・`docs/manuals/builtin_rhythm.md`参照)。
- どのプロファイルにどのvariant/チップを追加するかは決め打ちにせず、
  `collect_engine_chips()`で`hw_plugins[].profile`(`fmemuif_*.profile.
  json`等)が実際に搭載しているチップ(`engines[].chips[].chip`)を読み、
  `OPLL_CHIP_TO_VARIANT`で対応するvariantのみを動的に追加するようにした
  (プロファイル構成が将来変わっても自動的に追従する)。結果:
  `emu_opl`/`emu_opm`は3種類とも追加なし、`emu_opll`はOPLLビルトイン
  音色・リズムのみ、`unified_preset`/`emu_opn`/`emu_fmgen_opn`はOPNA
  ビルトインリズムのみ、両方搭載する`fmall`は3種類とも追加。
- `hw_plugins[].profile`はプロセスのCWD(=リポジトリルート想定)相対で
  書かれる規約(3.14節)であり、プロファイル自身のディレクトリ相対では
  ない点に注意(実装時に一度取り違えて`FileNotFoundError`になった)。
- 詳細・対応表は`tools/instrument_export/README.md`「ファイルを持たない
  機械合成バンク」節参照。

### 3.39 通常ドラムキットのバンクをCC#0=112から120へ訂正（2026年8月4日、ユーザー指摘）
3.29以来、`generate_instruments.py`は`drum_banks[]`由来の通常ドラムキット
(GM2ノートマッピング済み、Progでキット選択)を**CC#0=112**の1バンクとして
出力していたが、これは誤りだった。**CC#0=112はOPNA/OPLL内蔵リズム音源の
直接選択専用**(3.5節、3.38節のOPLLビルトインリズム・OPNAビルトイン
リズム)であり、通常ドラムキットとは意味が異なる別のCC#0を使うべき
だった。3.38でビルトインリズム2種を追加した際、両者が同じCC#0=112を
共有する形になり誤りが露見した。

実機のGM2規格・`Sekaiju8.3/instrument/GM1_GM2.ins`(`Patch[15360]`=
`120<<7`の`[General MIDI Level 2 Drumsets]`)に倣い、通常ドラムキットの
CC#0は**120**(GM2 Percussion Bank相当)に変更した。

- `generate_instruments.py`: `CC0_RHYTHM = 112`という単一定数を
  `CC0_DRUM_KIT = 120`(通常ドラムキット)・`CC0_BUILTIN_RHYTHM = 112`
  (内蔵リズム音源直接選択)の2つに分離。ドラムキット用の`Patch[]`/
  `Key[]`/`Drum[]`(Sekaiju)・`<Bank MSB>`(DOMINO)は`CC0_DRUM_KIT`
  (120)を、OPLL/OPNAビルトインリズムのエントリ(`collect_builtin_
  entries()`)は引き続き`CC0_BUILTIN_RHYTHM`(112)を使うよう修正した。
- `tools/instrument_export/README.md`のドラムキット関連記述も
  CC#0=112→120へ訂正(ビルトインリズムの記述はCC#0=112のまま変更なし)。
- 再生成後、Sekaiju側`Patch[15360]=<profile> Drum Kits`・
  `Key[15360,<prog>]=...`・DOMINO側`<Bank MSB="120" LSB="0">`に
  切り替わったこと、ビルトインリズム側(`CC0=112 CC32=17/40`)が
  影響を受けていないことをプログラム的に検証済み。

### 3.40 SF2(SoundFont2)バンクをインストゥルメントリストに追加（2026年8月4日、ユーザー指示）
`sf2_banks[]`(`FitomSf2IF`/FluidSynth経由、3.31/3.36節)は`hw_banks[]`/
`patch_banks[]`と異なりFITOM_X独自のJSON音色定義を持たず、実体である
`sf2/*.sf2`ファイル(RIFF/SoundFont2形式、`sf2/`ディレクトリにリポジトリ
同梱)自身にバンク名・パッチ名が埋め込まれているため、これまで
インストゥルメントリストに反映されていなかった。

- **CC#0=127を割り当て**(ユーザー指示。3.2節のVoicePatchType対応表は
  0-127の空間のうち0/17/26/34/35/40/48/64/81/82/84/112/120を使用済みで、
  127はFITOM_X側で特に意味を持たない値のため、SF2バンク用に便宜的に
  使用する)。
- **SF2ファイル自体をパースしてバンク名・パッチ名を取得**:
  `generate_instruments.py`に`parse_sf2_presets()`を新設し、外部
  ライブラリに依存せず標準ライブラリの`struct`のみでSF2(RIFF形式)の
  `pdta`チャンク内`phdr`(Preset Headers、38byte固定長レコード配列、
  `achPresetName[20]`/`wPreset`/`wBank`等)を直接パースする実装にした。
  `sf2_banks[].sf2_bank`(SF2ファイル自身が内部で持つバンク番号)と
  一致するプリセットのみを抽出し、`wPreset`をProg、`achPresetName`を
  音色名として`CC0=127, CC#32=sf2_banks[].bank`のバンクへ割り当てる。
  同一SF2ファイル(例: `GeneralUser GS v1.471.sf2`、全7プロファイル
  共通参照)を複数プロファイル・複数`sf2_banks[]`エントリから読む
  ケースが多いため、ファイルパス単位で`functools.lru_cache`により
  パース結果をキャッシュしている(最大31MB程度のファイルを都度
  読み直すコストを避けるため)。
- 再生成後、`unified_preset`の`CC0=127 CC32=0`バンクが
  `GeneralUser GS v1.471.sf2`のGM128名(`Stereo Grand`等)と一致する
  こと、XML well-formed性・`.ins`側`Patch[]`一意性を再検証済み。
- 詳細は`tools/instrument_export/README.md`「SF2(SoundFont2)バンク」節
  参照。

### 3.41 OPLLビルトイン音色はCC#0=40だけでなく41/42/43でも同一内容と判明、インストゥルメントリストを訂正（2026年8月4日、ユーザー指摘）
3.38でOPLLビルトイン音色をCC#0=40(OPLL)固定の1バンクとして追加したが、
ユーザーから「CC#0=40-43/CC#32=0がハードコーディングでOPLL系ビルトイン
パッチとして解決される」との指摘を受け、`../FITOM_X/core/src/
PatchManager.cpp`を直接確認したところ、以下が判明した。

- `core/include/fitom/FITOMdefine.h`は`VOICE_PATCH_OPLL`(0x28=40)・
  `VOICE_PATCH_OPLLP`(0x29=41)・`VOICE_PATCH_OPLLX`(0x2a=42)・
  `VOICE_PATCH_VRC7`(0x2b=43)という**4つの独立したvoicePatchType定数**
  を持つ(3.6節・3.38節では「CC#0=40固定、hwProgの上位3bitでチップ種別を
  切替」とだけ記載しており、CC#0自体が4値に分かれていることに触れて
  いなかった)。
- `PatchManager::resolveTriple()`は`hw_bank(CC#32)==0`かつ
  `voicePatchType`がこの4値のいずれかであれば、`resolveOpllRomVoice(
  hwProg, config, logContext)`を呼ぶだけで、**voicePatchType自体は
  引数として渡していない**(該当箇所: `if (hwBank == 0 && (voicePatchType
  == VOICE_PATCH_OPLL || ... == VOICE_PATCH_VRC7)) { return
  resolveOpllRomVoice(hwProg, config, logContext); }`)。
- `resolveOpllRomVoice()`内では、hwProgの上位3bit(`variantSel = (hwProg
  >> 4) & 0x7`)を`kVariantMap[8] = {VOICE_PATCH_OPLL, VOICE_PATCH_OPLLX,
  VOICE_PATCH_OPLLP, VOICE_PATCH_VRC7, 0,0,0,0}`で実際のvoicePatchType
  (`actualVpt`)へ変換し直し、`config.findDeviceIndexByVoicePatchType(
  actualVpt)`でデバイスを検索する。つまり呼び出し時のCC#0(voicePatchType)
  は「hw_bank=0のOPLL系ビルトイン音色バンクへの入口かどうか」の判定
  にしか使われず、実際にどのチップの音色が鳴るかはhwProg自体が完全に
  決定する。
- 結果として、**CC#0=40/41/42/43のどれを選んでも、同じProg番号なら
  常に同じ音・同じチップが鳴る**(FITOM_X本体の実装上の仕様であり、
  バグではない)。

これを受け、`generate_instruments.py`の`collect_builtin_entries()`を、
OPLLビルトイン音色についてはCC#0=40/41/42/43の4バンク全てに同じ内容
(搭載チップに応じたvariantの音色一覧)を出力するよう修正した
(`OPLL_BUILTIN_CC0_VALUES = [40, 41, 42, 43]`)。OPLLビルトインリズム・
OPNAビルトインリズム(CC#0=112固定)は今回の対象外(変更なし)。

`docs/manuals/README.md`(「1.音源選択モードの概要」の直接モードCC#0
一覧・「2.バンクマップ」表)・`docs/manuals/patches/opll.md`(CC#32=0節)
も、CC#0=41/42/43でも同一内容になる旨を追記して訂正した。
`tools/instrument_export/README.md`にも同様の説明を追記。

### 3.42 OPLLビルトイン音色は「CC#0でチップが選択されているように見える」表示に変更（2026年8月4日、ユーザー指示）
3.41の対応（CC#0=40/41/42/43の4バンク全てに同じ内容を出力）に対し、
ユーザーから「FITOM_Xの実動作としてはCC#0の値はチップ選択に使用され
ないが、MIDIシーケンサーでのパッチ選択の便宜上、CC#0でチップが選択
されているように見せたい。FITOM_X本体やパッチエディタのパッチピッカー
もそのような動作をしている」との指示を受けた。

`../FITOM_X`本体・`../FITOM_patch_editor`を調査した結果:
- FITOM_X本体のパッチピッカー(`apps/fitom_gui/PatchPickerDialog.cpp`)・
  モニター表示(`gui/bridge/FITOMBridge.cpp`の`getHwBankPatches()`)は、
  いずれも`PatchManager::getOpllRomPatches(voicePatchType)`経由で
  CC#0(voicePatchType)ごとに対応するvariantの音色のみへ絞り込んで表示
  している。FITOM_patch_editor側も同じロジックを移植済み
  (`src/BuiltinVoices.cpp`の`opllRomVariantSel()`/`opllRomVoices()`)。
- 3.41で「ランタイム上はCC#0に関わらずhwProgだけで結果が決まる」とした
  事実自体は正しい(`resolveOpllRomVoice()`はvoicePatchTypeを引数に
  取らない)が、GUI側の「音色選択の絞り込み表示」段階と「実際の発音
  解決」段階は意図的に分離された設計であり、両者は矛盾しない。
- **CC#0→variant番号の対応**(`kVariantMap`/`getOpllRomPatches`と同一、
  `tests/test_config.cpp`のユニットテストでも検証済み):

  | CC#0 | チップ | variant | Prog範囲(instIndex 1-15) |
  |---|---|---|---|
  | 40 | OPLL(/OPLL2) | 0 | 1-15 |
  | 41 | OPLLP | 2 | 33-47 |
  | 42 | OPLLX | 1 | 17-31 |
  | 43 | VRC7 | 3 | 49-63 |

  CC#0の数値順(40,41,42,43=OPLL,OPLLP,OPLLX,VRC7)とvariant番号順
  (0,1,2,3=OPLL,OPLLX,OPLLP,VRC7)で**OPLLPとOPLLXの順序が入れ替わって
  いる**点に注意(3.41時点で「CC#0=41→prog17-31」というユーザーの
  当初の想定を検証エージェントで確認したところ、これは誤りで正しくは
  「CC#0=41→OPLLP→prog33-47、CC#0=42→OPLLX→prog17-31」だった)。

対応:
- `generate_instruments.py`の`collect_builtin_entries()`を、
  `OPLL_BUILTIN_CC0_VALUES`(4バンク全てに同一内容)から
  `OPLL_BUILTIN_CC0_TO_VARIANT = {40: 0, 41: 2, 42: 1, 43: 3}`
  (CC#0ごとに対応するvariantのみ)へ変更。Prog番号は絞り込み後も
  実際のhwProgエンコード値((variant<<4)|instIndex)をそのまま使う
  (0始まりの連番に振り直さない。GUI側`FITOMBridge.cpp`の
  `info.prog = static_cast<int>(p.id)`と同じ扱い)。
- `docs/manuals/README.md`・`docs/manuals/patches/opll.md`・
  `tools/instrument_export/README.md`に、CC#0→variant対応表と
  「ランタイムは無関係だがGUI/インストゥルメントリストは絞り込む」旨を
  追記。
- 再生成後、CC#0=40が`1=Violin`〜`15=Electric Guitar`、CC#0=41が
  `33=Electric Strings`〜`47=Noise and Tone`、CC#0=42が`17=Strings`〜
  `31=Sitar`、CC#0=43が`49=Buzzy Bell`〜`63=Sweep`になっていること、
  XML well-formed性・`.ins`側`Patch[]`/`Key[]`一意性を再検証済み。

## 4. 未解決・要確認事項
（各節末尾で「4節に記載」とした項目をここにまとめている。本セクション
見出しが過去のある時点で欠落していたため、2026年7月29日に補完した。）

- `banks/drums/ma2_preset_2op.drumkit.json`・`ma2_variant_2op.drumkit.json`
  のGM2ドラムノート27,28,31-36,103-105(計11ノート)は、参照先
  (`banks/OPL2/ma2_vma/DrumsBank.hwbank.json`・`07_DrumsBank.hwbank.json`
  のprog 0,1,4-9,76-78)が全パラメータ空の未使用プレースホルダのため、
  今回の変更以前から実質無音(3.27参照)。本来何を鳴らすべきかのデータが
  無く、変換元`.vma`側にも実データが存在しないため、このリポジトリからは
  修正できない(該当ノートの`name`も`Drum Note N`という機械生成の
  フォールバック名のままで、元々意図された楽器名の情報が無い)。
  実害の大小は未評価のため、要判断。
- `config_schema/profile.schema.json`のFITOM_X側原本に、以下2点の
  drift/未反映を発見済み（config_schemaは本体側から直接コピーする方針
  のため、本リポジトリ側では未対応。本体側の更新を待って同期する）:
  - `devices[].engine`の例が`"YMEngine"`のまま（3.18のDLL名改称が
    schema例に未反映）。
  - `midi_backend`の説明文が旧WinMM/ALSA/WMS個別実装の記述のままで、
    FITOM_X本体のコミット`4a3864f`（MIDIバックエンドをRtMidi統一実装に
    置き換え）が本リポジトリの`config_schema/profile.schema.json`に
    未反映（2026年7月19日時点、本体側`config_schema/`と本リポジトリの
    コピーを比較して判明）。
- `fmemuif_opl5.profile.json`/`fmemuif_opm_opz4.profile.json`/
  `fmemuif_opll5.profile.json`（新規作成した4チップ構成サブプロファイル）
  の**クロック値は一般的な標準値からの推測**（特にOPL4=33,868,800Hzは
  未検証）。実機/エンジン仕様に合わせた確認・調整が必要。
- OPLL GM128（`gm_layered_opll.patchbank.json`）は MA-2 Preset2OP由来が
  67/128と過半数。ソースを増やせる余地がないか、要継続検討
  （2026年7月19日確認: この67パッチはToneLayerで`voice_patch_type=OPLL,
  hw_bank=4`(`Preset2OP.hwbank.json`)を参照しているのみで値のコピーは
  持たないため、3.19のAM/WS修正は参照側の書き換えなしに自動的に反映
  済み。追加対応は不要と判断）。
- `banks/sw/necopn_gm.swbank.json`・`default_gm.swbank.json`・
  `default_32.swbank.json`・`compat_zero.swbank.json`の4ファイルは、
  3.21の調査でどのプロファイルの`sw_banks[]`からも参照されていない
  孤立ファイルと判明した。フィールド名も`LFO`/`LDM`/`LDL`/`SLF`等、
  現行の`swbank.schema.json`(`LWF`/`depth_cents`/`SLS`/`SLI`等)より前の
  旧形式のまま放置されている。実害はないが、紛らわしいため削除するか
  現行スキーマに追従させるか要判断（2026年7月20日時点、未着手）。
- 3.21で`sw_bank=0, sw_prog=2`参照を8種のキャリア別prog(24-31)へ
  機械的に付け替えたが、これはあくまで**データ側の対応**であり、
  FITOM_X本体側の実行エンジンが`HwPatch::sw_prog`で指定された
  SwPatchのVTLを実際に`ops[i]`ごとの正しいインデックスへ適用している
  ことまでは本リポジトリからは検証できていない（コアエンジンのソース
  非公開のため）。本体側で動作確認することが望ましい。
- 3.22で新設した`pcm_image_catalog.json`（リポジトリルート直下）・
  `config_schema/pcm_image_catalog.schema.json`（FITOM_X本体からの
  verbatimコピー）は今回のセッションで動作未検証（JSON構文とパス実在性
  のみ確認済み、実際に`fitom_core.exe`+FitomEmuIF.dllでADPCM RAM/AWM ROM
  が正しくロードされることは未確認）。実機/エミュレータでの動作確認が
  望ましい。
- 3.29/3.30で新設した`docs/instruments/sekaiju/FITOM_X.ins`・
  `docs/instruments/domino/FITOM_X.xml`は、Sekaiju/Cakewalk/DOMINO本体
  での読み込み動作が未検証（構文検証のみ済み）。実機/実ソフトでの動作
  確認が望ましい（Studio One/REAPER対応の要否は3.29末尾の記述の通り
  検証環境待ちで保留中）。
- 3.31で`unified_preset.profile.json`に追加した`sf2_banks`/
  `sf2_channel_windows`/`devices[chip=SF2]`は、`FitomSf2IF.dll`が本
  リポジトリに未ビルド・未配置のため実機能未検証（JSON構文・スキーマ
  検証のみ済み）。`../FitomSf2IF`側のビルドが完了し`bin/`へ配置され
  次第、実際にSF2が鳴るか動作確認が必要。
- `GeneralUser GS v1.471.sf2`のGS variationバンク（sf2_bank 1-16, 120）は
  `sf2_banks`未登録（3.31参照）。必要になった場合は`bank=10`以降に追加
  すること。
- 3.35でスキーマ・実データを同期したAWMの波形ごとピッチ/音量校正
  (`pitch_offset`/`key_scaling`/`tone_attenuate`/`volume_factor`)は、
  対応する本体側修正(FITOM_X側コミット`830e59a`、`COPL4AWM::getFnumber()`
  の式差し替えと`updateVolExp()`での校正値適用)込みのバイナリが`bin/`に
  未配置のため、実際にAWMが意図した音高・音量で鳴ることは未検証
  (JSON構文・スキーマ検証、全610ゾーンのフィールド充足確認のみ済み)。
  本体側の対応版ビルド後に実機/実エンジン環境での確認が必要。
- 3.33で6プロファイルに追加した`bank_overrides`（レイヤードバンク0/
  ドラムキット0の無音解消）は、`bin/fitom_cli.exe`が対応コミット
  （FITOM_X側`c2bbe83`）より前のビルド（2026年7月28日）のため、この
  リポジトリの環境では実行時ロード確認ができていない（JSON構文・
  スキーマ検証、参照ファイル実在確認のみ済み）。`bank_overrides`対応版
  バイナリに更新後、実機/実エンジン環境で実際に音が出ることの確認が
  必要。
- 3.36で全7プロファイルに配線した`sf2_channel_windows`（ch14/15の2ch）
  も3.31と同様、`FitomSf2IF.dll`が本リポジトリに未ビルド・未配置のため
  実機能未検証。特に`unified_preset`/`emu_opm`/`emu_opn`/`fmall`の
  `mpu`値は`midi_inputs`が`__LOCAL__`(環境依存)でDAW側MPUを判別できず
  MPU0を暫定的に採用しているため、実際の接続環境によっては調整が必要。

---

## 5. マシン間コンテキスト共有ルール

複数マシンでClaude Codeを使ってこのプロジェクトを継続する際は、以下を
必ず守ること。

### 5.1 単一の真実の情報源（Single Source of Truth）
- **このファイル（`CLAUDE.md`、プロジェクトルート直下）が、マシン間で
  共有する唯一のコンテキストである。** 会話ログやチャット履歴はマシン間
  で共有されないため、引き継ぎたい情報は必ずこのファイルに書き出す。
- Gitリポジトリそのもの（コミット履歴・ファイル内容）が実際の作業成果
  の正であり、このファイルはそれを読み解くための「地図」である。

### 5.2 セッション開始時の手順（新しいマシン/新しいセッションの最初に必ず実行）
1. `git pull`で最新の状態を取得する。
2. この`CLAUDE.md`を読み、「4. 未解決・要確認事項」を確認する。
3. `git log --oneline -20`で直近のコミット履歴を確認し、他マシンでの
   作業内容を把握する。
4. 作業前に`git status`でuntracked/uncommittedな変更がないか確認する
   （前回のセッションで手元に残った未コミットの変更がある場合、他マシン
   では見えないため注意）。

### 5.3 セッション終了時の手順（作業を中断・完了するたびに必ず実行）
1. 変更したすべてのファイルをコミットする。コミットメッセージには
   「何を」「なぜ」変更したかを明記する（次のマシンで読む前提で書く）。
2. このセッションで新たに判明した設計原則・注意点があれば、
   「3. 必ず守るべき設計原則・技術的知見」に追記する。
3. 未解決のまま残った作業があれば、「4. 未解決・要確認事項」に追記する。
4. 完了した項目は「4. 未解決・要確認事項」から削除する。
5. `git push`して、他マシンから参照可能な状態にする。
6. **未コミットの変更を残したままセッションを終了しない。** 中途半端な
   状態で終える場合も、`WIP:`プレフィックス付きでコミットしておく。

### 5.4 同時作業の回避
- 同じブランチで複数マシンから同時に作業しない（コンフリクトの原因）。
  作業を開始する前に、他マシンでアクティブなセッションがないか確認する
  （Slack等のチームコミュニケーションツールでの一言宣言を推奨）。
- 大きな変更（プロファイル全体の再構成、スキーマ変更等）を行う際は、
  作業用ブランチを切ってから作業し、完了後にmainへマージする。

### 5.5 スキーマ変更の伝播
- `config_schema/*.json`はFITOM_X本体側から提供される。新しい
  `FITOM_X.zip`を受け取ったら、まず`config_schema/`配下を最新化してから
  他の作業を行う（スキーマの制約変更に気づかず古い前提で作業すると、
  後で大量の手戻りが発生する。本セッションでも`ops[i].WS`の範囲変更
  (`0-7`→`0-127`)、`fixed_ch`廃止、`ext.rhythm_ch`新設等、複数回の
  仕様変更が発生した）。
- スキーマ変更に気づいた場合は、変更内容と対応した差分をこの
  `CLAUDE.md`の「3. 必ず守るべき設計原則・技術的知見」に追記する。

### 5.6 検証を欠かさない
- 変更後は必ず該当するJSON Schemaでバリデーションを行い、
  `hw_banks`/`patch_banks`/`drum_banks`/`sw_banks`が参照する全ファイルの
  実在確認（孤立参照・欠落参照がないか）を行ってからコミットする。
