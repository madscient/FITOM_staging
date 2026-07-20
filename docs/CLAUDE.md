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
| ファイル | 用途 |
|---|---|
| `unified_preset.profile.json` | 全チップ統合プロファイル（hw_banks 63件, sw_banks 7件, patch_banks 5件, drum_banks 15件） |
| `emu_opn.profile.json` | OPN専用（OPN/OPN2/OPNA/OPNB/OPNBB×1ずつ） |
| `emu_opl.profile.json` | OPL専用（OPL[rhythm]/Y8950/OPL2/OPL3/OPL4×1ずつ） |
| `emu_opm.profile.json` | OPM専用（OPM×2/OPZ×2） |
| `emu_opll.profile.json` | OPLL専用（OPLL/OPLL2[rhythm]/OPLLP/VRC7/OPLLX×1ずつ） |
| `fmall.profile.json` | OPM/OPZ/OPL3/OPL4AWM/OPNA/OPNBB/OPLL/OPLLP/OPLLX/VRC7構成（2026年7月19日新設、hw_banks 26件・sw_banks 7件、patch_banks 0番=`gm_native_opl4awm.patchbank.json`[ToneLayer0でAWM直参照のGM128バンク、新規作成]、drum_banks 0番=`opl4awm.drumkit.json`のみ） |
| `emulator_opm.profile.json`ほか既存5件 | 旧・個別プロファイル（統合前からの遺産、現役利用中のため削除しないこと） |

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

## 4. 未解決・要確認事項

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
- `emu_opm.profile.json`/`emu_opll.profile.json`の`drum_banks`は「統合
  プロファイルのまま」全15件を引き継いでいる。他チップ用ドラムキット
  （ALSA/MA-2等）も含まれるため、絞り込みが必要か要検討。
- OPLL GM128（`gm_native_opll.patchbank.json`）は MA-2 Preset2OP由来が
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
