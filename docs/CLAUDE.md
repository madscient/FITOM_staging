# FITOM_staging プロジェクト引き継ぎドキュメント (for Claude Code)

このファイルはプロジェクトルート直下に置き、Claude Codeセッション開始時に
必ず最初に読むこと。複数マシンで作業するための運用ルールも記載している。

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
- EGTビット=0（パーカッシブ）: `SR=r<<1`（4bit→5bit）, `RR=0`
- `ops[i].EGT`はOPL系では常に0（OPN専用のSSG-EG用、無関係）

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

### 3.13 パフォーマンス情報を持たない変換元からのSwPatch割り当て方針
`necopn_gm.hwbank.json`（necopn由来のGM128、パフォーマンス情報を
持たない変換元フォーマット）は、全128パッチが`banks/sw/necopn_gm.
swbank.json`の`sw_prog=2`（音量ベロシティセンシティビティ(`VTL`)の
みを設定し、他の感度パラメータ・ソフトLFOは全て無効化した汎用
パフォーマンスパッチ）を一律で参照している。**これは意図した設計**
であり、修正不要（2026年7月確認済み）。
- 変換元にパフォーマンス情報（ベロシティ感度カーブ・LFO設定等）が
  無いハードウェアパッチをhwbankへコンバートする場合、**音量ベロシ
  ティセンシティのみを設定した汎用パフォーマンスパッチ**を一律で
  割り当てる、というのが本プロジェクトの標準運用。
- 変換元に実際のパフォーマンス情報がある場合は、その情報も変換して
  **専用のパフォーマンスパッチ**（バンク内の別`sw_prog`）を割り当てる。
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

---

## 4. 未解決・要確認事項

- `fmemuif_opl5.profile.json`/`fmemuif_opm_opz4.profile.json`/
  `fmemuif_opll5.profile.json`（新規作成した4チップ構成サブプロファイル）
  の**クロック値は一般的な標準値からの推測**（特にOPL4=33,868,800Hzは
  未検証）。実機/エンジン仕様に合わせた確認・調整が必要。
- `emu_opm.profile.json`/`emu_opll.profile.json`の`drum_banks`は「統合
  プロファイルのまま」全15件を引き継いでいる。他チップ用ドラムキット
  （ALSA/MA-2等）も含まれるため、絞り込みが必要か要検討。
- OPLL GM128（`gm_native_opll.patchbank.json`）は MA-2 Preset2OP由来が
  67/128と過半数。ソースを増やせる余地がないか、要継続検討。
- `banks/drums/*.drumkit.json`（GM2ドラムキット群）はハイハット等の
  相互チョーク（クローズ発音時にオープンを止める等）を実装していない。
  2026年7月15日にFITOM_X側で追加された`choke_groups`
  （drumkitトップレベル、ノート番号ペアの配列）を使えば実現できるが、
  現状は未適用（元々`fixed_ch`ハックも使っていなかったため後退では
  なく、単純に未着手の改善余地）。

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
