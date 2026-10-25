# FITOM_staging 作業ガイド (for Claude Code)

セッションの最初にこのファイルを読み、続けて`docs/STATUS.md`(現在の状態と
未解決事項)を読むこと。このファイルには守るべき規則と技術的知見だけを書く。
現在の状態は`docs/STATUS.md`、変更・修正・調査の経緯は`docs/worklog/`
(月ごと。約束事は`docs/worklog/README.md`)に書く。

## 0. やり取りの方針

- ユーザーへの応答・報告は日本語で行う。コード内コメント・コミットメッセージの
  慣習は既存のものに合わせる。

## 1. 概要

- **FITOM_X**(別リポジトリ`../FITOM_X`): コアライブラリ・GUI・設定スキーマの原本
- **FITOM_staging**(本リポジトリ): 動作環境・プロファイル・プリセットバンク・
  変換ツール・セットアップスクリプト
- 複数のFM/PSG/PCM音源チップを、エミュレーター(FitomEmuIF + 各エンジンDLL)
  または実機(FitomHwIF)経由で統一的に扱うMIDI音源システム

```
config/
  profiles/*.profile.json       プロファイル本体
  profiles/unified.bankset.json 全プロファイル共有のバンクセット
  profiles/hw_plugins/*.json    hw_plugins[].profileが指すプラグイン固有の
                                サブプロファイル(fmemuif_* / fitom_sf2if_*)
  fitom.conf.json               システム設定(ログ等)
config_schema/*.json            JSON Schema(FITOM_Xからの写し)
banks/                          音色バンク(配置の原則はbanks/README.md)
  OPN/ OPM/ OPZ/ OPL2/ OPL3/ OPLL/ PSG/ PCM/ OPL4AWM/   チップ族ごと
  patches/ drums/ sw/ scc/      フォーマットごと
pcm_image_catalog.json          PCMメモリイメージカタログ
tools/voice_convert/            音色変換スクリプト
tools/instrument_export/        インストゥルメントリスト生成
tools/git_filters/              環境依存フィールドの正規化フィルタ
tools/launch_check/             全プロファイルの起動確認と、鳴るバンク・キットの集計
tools/profile_format/           プロファイル本体をGUIの保存形式に揃える
docs/manuals/                   利用者向けリファレンス
docs/instruments/               インストゥルメントリスト(生成物)
docs/STATUS.md                  現在の状態・未解決事項
docs/worklog/                   作業記録
docs/plans/                     他のリポジトリへの作業の依頼文(request-<リポジトリ名>.md)
bin/ roms/ wavs/ sf2/ logs/ dist/   git管理外
```

## 2. 作業の手順

### セッション開始時
1. `git pull`で最新を取得する。
2. このファイルと`docs/STATUS.md`を読む。
3. `git log --oneline -20`で他マシンでの作業を把握する。
4. `git status`で未コミットの変更が残っていないか確かめる。他のマシンで
   アクティブなセッションが無いかも確かめる。
5. `git config user.name`/`user.email`が`git log -1 --format='%an <%ae>' origin/main`と
   一致することを確かめる。コミットはauthor/committerとも`madscient`名義に
   統一している。一致しなければ、コミットする前に`git config --local`で合わせる。

### 作業中・終了時
- 変更したファイルはすべてコミットする。メッセージには何を・なぜ変えたかを書く
  (次のマシンで読む前提)。中途半端な状態で終えるときも`WIP:`付きでコミットし、
  未コミットの変更を残さない。
- 経緯は`docs/worklog/YYYY-MM.md`の末尾に節を足して書く。
- 新しく分かった規則・技術的知見は、このファイルの3節に現在形で書く。後から
  規則が変わったら、ここを書き換える(訂正を追記で積まない)。
- 状態が変わったら`docs/STATUS.md`を書き換える。解決した未解決事項は消す。
- 作業後に`git push`する。
- 同じブランチで複数マシンから同時に作業しない。大きな変更(プロファイル全体の
  再構成、スキーマ変更等)は作業用ブランチで行い、完了後にmainへマージする。
- 公開リポジトリなので、ローカル環境に固有の情報(手元のパス、MIDI機器名、
  ポート名等)を成果物・コミットメッセージに書かない。

### config_schemaの同期
- `config_schema/*.json`はFITOM_X本体の`config_schema/`からそのままコピーする。
  こちらで書き換えない(原本側の誤りも原本の修正を待つ)。
- FITOM_Xを更新したら、他の作業より先に`config_schema/`を同期する。スキーマの
  制約変更に気づかず古い前提で作業すると大きな手戻りになる。

### 検証
- 変更後は該当するJSON Schemaで検証し、`hw_banks`/`patch_banks`/`drum_banks`/
  `sw_banks`等が参照するファイルの実在(欠落参照・孤立ファイル)を確かめてから
  コミットする。
- プロファイル本体(`config/profiles/*.profile.json`)を手やスクリプトで書き換えたら、
  `python tools/profile_format/format_profiles.py`でGUIの保存形式に揃える(`--check`は
  揃っていないファイルを挙げて終了コード1を返す)。
- プロファイルを変えたら、`devices[]`の(engine, chip, index)がサブプロファイルの
  `engines[].chips[]`のスロットと1:1で対応すること(欠落・二重オープン・
  未使用スロット)を確かめる。
- 起動確認の前に、`bin/`が確認したい機能を含むFITOM_X(と各プラグイン・エンジン)で
  ビルドされているかを確かめる。`bin/`はマシンごとに違うので、`docs/STATUS.md`の表では
  なく、そのマシンの`bin/build_info.json`(`setup.ps1`が書く各リポジトリのコミット)を見る。
  `built: false`なら、ビルドは`setup.ps1`の外で行われていて、コミットとバイナリが
  一致する保証は無い。古いバイナリだと`unknown chip`や`PatchBank 0 not found`が出て、
  プロファイル側の不備と取り違える。
- `bin/`の更新は`.\setup.ps1 -Pull -Build`で行う。各リポジトリをupstreamへ早送りし、
  既存のビルドディレクトリでビルドしてから配置する。早送りできないリポジトリ(追跡中の
  ファイルの未コミットの変更・分岐・upstream無し)が1つでもあれば、どれも動かさずに
  中止するので、そのリポジトリを手で片付けてから再実行する。`setup.ps1`は古い名前の
  DLLを消さない。
- `setup.sh`(Linux/macOS向け)は動作実績が無く、`setup.ps1`への変更に追従していない
  (ユーザーからの情報)。`-Pull`/`-Build`相当も無い。
- 実起動の確認は、リポジトリルートで`bin/fitom_cli.exe config/profiles/<name>.profile.json`
  を起動し`logs/fitom.log`を読む。複数のプロファイルをまとめて確かめるときは
  `tools/launch_check/launch_all.ps1`(`-Name`で絞れる)を使う。1本ずつ起動して止め、
  `HWPort opened`・`Device added`・`Failed to create HWPort`・`unknown chip`・エラー・
  警告の件数と警告の種類を出し、ログを`logs/launch_check/`へ退避する。
  `fitom_cli`はSIGINTで終了しないため、手で回すときは`Start-Process -PassThru`→
  `Stop-Process -Force`→`WaitForExit()`で1本ずつ確実に止めてからログを読む(残った
  プロセスがログを掴んだまま次が起動するとログが混ざる)。
- 起動ログの警告は、変更の前後で件数と種類を比べる。既知の警告は`docs/STATUS.md`
  4節に載っている。
- `docs/manuals/emu_profiles.md`の「通常モードのパッチバンク」「ドラムキット」の表は、
  `tools/launch_check/coverage.py --markdown`の出力をそのまま載せたもの。バンク・
  プロファイルを変えたら、`launch_all.ps1`で起動ログを取り直してから作り直す。
  `coverage.py`は、起動ログのデバイス一覧にFITOM_Xの解決規則(`resolveTriple()`・
  `acceptsFallback()`等)の写しを当てて数える。音は確かめない。FITOM_X側でこれらの
  規則が変わったら、`coverage.py`も合わせて直す。
- 起動ログで分かるのはデバイスとバンクのロードまで。音が意図どおり鳴るかの
  聴感確認はユーザーが行う。

## 3. 規則と技術的知見

### バンクファイル共通
- `*.hwbank.json`は`voice_patch_type`も`chip_group`も持たない。チップ族の指定は
  プロファイル側の`hw_banks[].group`(文字列。`OPN2`/`OPZ`/`OPL3_2`/`OPL_RHY`/`OPLL`/
  `OPLLEX`/`OPL3`/`SSG`/`ADPCMB`/`ADPCMA`/`AWM`等)で行う。
- `prog`は0-127。ファイルを統合するときは合計パッチ数を先に数える。
- `ALG`/`FB`/`AMS`/`PMS`等はパッチ直下のフラットなフィールドに置く。`"hw": {...}`の
  ようなネストは`PatchManager::jsonToHwPatch`が読まず、黙って無視される。
- キー名は現行のものだけが読まれる(例: 疑似デチューンは`ops[i].PDT`、固定周波数は
  `ext.FIX`。旧名`FXV`/`DM0`は無視される)。
- `ops`を持つ通常のパッチは`prog`必須(省略するとロード時に黙って消える)。
  `builtin`参照エントリは`prog`を書かない(下記「ビルトイン音色」)。
- patchbankのPatch直下の`sw_bank`/`sw_prog`は読まれない。SwPatchとの対応は
  参照先HwPatch自身の`sw_bank`/`sw_prog`で付ける。
- パッチ名: OPLL系は先頭に`[OPLL]`/`[OPLLX]`/`[OPLLP]`/`[VRC7]`、PSG系は
  `[SSG]`/`[EPSG]`/`[DCSG]`/`[SAA]`/`[SCC]`(`ext.target_voice_patch_type`から導出)。
  SwPatchの違い(Sustain/Decay/Vib等)は名前に書かず、末尾に`[sw_bank:sw_prog]`を
  付ける。他バンクを参照するだけのパッチは参照先の名前をそのまま使う。
- 既存バンクからprogを消す前に、全`*.patchbank.json`/`*.drumkit.json`からの参照
  (group+bank+prog)を突き合わせる。消すと「無音のパッチへの参照」が
  「存在しないprogへの参照」に変わる。
- `banks/`のディレクトリ配置は`banks/README.md`の原則に従う。

### CC#0とVoicePatchType
CC#0の値がそのままVoicePatchType(直接モード)になる。0は通常モード
(PatchBank経由)。

| 値 | 16進 | 名称 |
|---|---|---|
| 0 | 0x00 | 通常モード(PatchBank経由) |
| 16 | 0x10 | OPN |
| 17 | 0x11 | OPN2 |
| 25 | 0x19 | OPM |
| 26 | 0x1A | OPZ |
| 32 | 0x20 | OPL |
| 33 | 0x21 | OPL2 |
| 34 | 0x22 | OPL3_2 |
| 35 | 0x23 | OPL_RHY(OPLレジスタ疑似リズム、HwPatch経由) |
| 40 | 0x28 | OPLL |
| 41 | 0x29 | OPLLP |
| 42 | 0x2A | OPLLX |
| 43 | 0x2B | VRC7 |
| 44 | 0x2C | OPLLEX(Y8960拡張OPLL部) |
| 48 | 0x30 | OPL3 |
| 64 | 0x40 | SSG(PSG系共有バンクの入口) |
| 68 | 0x44 | DSG(YM2163、ビルトイン音色専用) |
| 81 | 0x51 | ADPCMB |
| 82 | 0x52 | ADPCMA |
| 84 | 0x54 | AWM |
| 112 | 0x70 | 内蔵リズム音源の直接選択 |
| 127 | 0x7F | SILENCE(解決成功・ただし発音しない。プレースホルダ用) |

正確な値の原本はFITOM_Xの`core/include/fitom/FITOMdefine.h`。
`unified.bankset.json`は同じバンクファイルを複数のgroup(`OPN`と`OPN2`等)から
共有参照し、フォールバック先のVoicePatchTypeでも同じバンクを選べるようにしている。

### 値の格納規約(チップ族ごと)
- `TL`はチップを問わず0.75dB/stepの減衰量空間で保持する。OPL/OPLL系は実機の
  レジスタ値(0-63)を**そのまま**格納する(`<<1`しない。ランタイムはクランプのみで、
  63以上は62に飽和する)。
- OPL/OPLL系の`AR`/`DR`/`SR`は上位ビット表現で保持するため、実機の4bit値を`<<1`して
  格納する。
- OPM/OPZの`AR`/`DR`/`SR`(0-31)・`SL`/`RR`(0-15)は実機と同じドメインで、
  シフトしない。
- OPL/OPLL系のEGT/SR/RR: 実機EGTビット=1(持続)なら`SR=0`、EGTビット=0
  (減衰)なら`SR=変換元RR<<1`。`RR`はEGTビットに関わらず常に変換元RRレジスタ値
  (シフトなし)。
  - OPL/OPL2/OPL3: FITOM_Xはキーオン時にEGT=0で`SR`の値を、キーオフ時にEGT=1で`RR`の値を
    RRレジスタへ書く(動的な書き換え)。`RR=0`のキャリアは`SR`が何であってもキーオフで
    消音しない。
  - OPLL系: FITOM_XはEGT/RRを動的に書き換えない。音色を書くときに`SR>0`ならEGT=0・
    RRレジスタ=`SR>>1`(キーオフ後もこのレートで減衰し、`RR`は使われない)、`SR==0`なら
    EGT=1・RRレジスタ=`RR`(FITOM_Xの`docs/design/chip-notes.md`「EGTとRRの静的な変換」)。
    上の変換規則なら、どちらでもRRレジスタに入る値は変換元RRと一致する。`SR==0`かつ
    `RR=0`のキャリアはキーオフで消音しない。
  - 変換時は`AR>0`のキャリアの`RR==0`を`RR=1`に補正する(`apply_carrier_rr_floor()`)。
    `banks/OPL2`・`OPL3`・`OPLL`配下で、`AR>0`のキャリアに`RR==0`は無い状態を保つ
    (`AR=0`の空パッチは対象外)。
- `ops[i].EGT`はOPN専用(SSG-EG用)で、OPL系では常に0。
- OPM/OPN/OPZの`ops[]`はアルゴリズム図のチェーン順`[M1,C1,M2,C2]`
  (FITOM_Xの`COPM::kMap={0,2,1,3}`)。
- OPLLの`hw.ALG`は常に0(音色ごとの接続切替が実機に無い)。
- OPM/OPZの`hw.PMS`/`hw.AMS`は、ノートオンのたびに`$38+ch`へ書かれる(`COPM::enablePM`/
  `enableAM`)。HW LFOの速さ・深さはチップ全体で1系統で、CC#14(Depth)/CC#15(Rate)で
  決まり、既定は0(効かない)。CC#1 ModulationはHW LFOではなくソフトウェアのピッチ変調
  (FITOM_X `b7c1e4c`の`OPM_new.cpp`・`MidiCh.cpp`を読んで確認。**読解のみ**)。

### PSG系・DSG
- PSG系(SSG/EPSG/DCSG/SAA/SCC)は`voice_patch_type=0x40`固定の共有バンクを使い、
  各パッチの`ext.target_voice_patch_type`(`0x40`=SSG/`0x41`=EPSG/`0x42`=DCSG/
  `0x43`=SAA/`0x48`=SCC)で対象チップを指定する。波形選択はEPSG(`ops[0].WS`=
  デューティ比0-8)とSCC(`ops[0].WS`=波形メモリindex 0-127)のみ。
- DSG(YM2163)は共有バンクの対象外。全音色がビルトインの20音色
  (`prog = 波形index*4 + エンベロープindex`)で、CC#0=68。CC#32は無視されるため
  `hw_banks[]`のエントリは不要(登録しても引かれない)。内蔵リズムはCC#0=112・
  CC#32=68(0=BD, 1=HC, 2=SDN, 3=HHO, 4=HHD)で、`rhythm_mode`に関わらず常に
  展開される。DSGのリズムは`play_note`(音程)も`gate_time`も効かない。

### OPLL系のビルトイン音色・OPLLEX
- `voice_patch_type`がOPLL系(40-43)で`hw_bank=0`のときはファイルを持たない
  ROM音色領域。`hwProg`の上位3bit=variant(0=OPLL, 1=OPLLX, 2=OPLLP, 3=VRC7)、
  下位4bit=ROM音色番号(0=無音, 1-15)。
- 発音時はhwProgだけで鳴るチップと音色が決まる(CC#0=40/41/42/43のどれでも同じ)。
  GUIのパッチピッカーとインストゥルメントリストは、CC#0ごとに対応するvariantだけを
  見せる。CC#0の数値順(40,41,42,43=OPLL,OPLLP,OPLLX,VRC7)とvariant番号順
  (0,1,2,3=OPLL,OPLLX,OPLLP,VRC7)はOPLLPとOPLLXが入れ替わっている。
- ROM音色は標準OPLL系(OPLL/OPLLX/OPLLP/VRC7)どうしではフォールバックしない。
  要求したvariantのチップが無いときは、OPLLEX(4バンク全てを内蔵)があればOPLLEXで
  鳴る(`resolveOpllRomVoice()`)。どちらも無ければ鳴らない。
  ユーザー音色(`ext.ALG_EXT & 1 == 0`)はOPLL系の間(OPLLEXを含む)で相互に
  フォールバックする(`opllFamilyAcceptsFallback()`)。
- OPLLEX(CC#0=44)は別のHwBank名前空間(`hw_banks[].group`は`"OPLLEX"`)。
  `ext.ALG_EXT`がOPLLEXでだけ3bit(bit0=preset選択、bit2-1=チャンネル別ROMプリセット
  バンク)。CC#0=44ではhwProgのvariantを「OPLLEX自身のどのBANKか」と解釈し、常に
  OPLLEXで鳴らす。OPLLEX用の`hw_banks[]`は追加しない(既存のOPLL系ユーザー音色バンクが
  フォールバックで鳴るため)。
- GM128パッチバンクでROM音色を鳴らすには、ToneLayerで`voice_patch_type=0x28,
  hw_bank=0, hw_prog=(variant<<4)|inst`を直接指定する。
- ROM音色名と代替用途の一次資料:
  - https://sites.google.com/site/undocumentedsoundchips/yamaha/ymf281
  - https://sites.google.com/site/undocumentedsoundchips/yamaha/ym2423
  - https://github.com/plgDavid/misc/wiki/Copyright-free-OPLL(x)-ROM-patches

### ビルトイン音色用メタバンク
- `role="builtin_swpatch_meta"`のバンクは、ビルトイン音色(OPLL系ROM音色とDSG)に
  パフォーマンスパッチを紐づける領域で、`patches[i].builtin`はこのroleでだけ意味を
  持つ。`builtin.patch_type`(`OPLL`/`OPLLX`/`OPLLP`/`VRC7`/`DSG`)で対象を区別し、
  `patch_no`の値域はOPLL系1-15、DSG 0-19。
- 保持スロットは1つだけ。`hw_banks[]`にこのroleのエントリを複数書くと後勝ちで
  上書きされるため、全チップ分を1ファイル(`banks/OPLL/rom_sw_meta.hwbank.json`、
  `hw_banks[group=OPLL,bank=3]`)にまとめる。チップ専用のファイルを作らない。
- `builtin`参照エントリでは`prog`を書かない。`prog`は検索キーではなく128要素の
  格納スロット位置にすぎず、チップ間で共有の名前空間なので、明示すると後勝ちで
  片方が黙って消える。省略すればローダが自動採番する。明示するならチップごとに
  範囲を分ける(例: OPLL系0-59、DSG 60-79)。
- 未設定のセンチネルは-1(DSGの`prog 0`は正規の音色)。

### PCM系(AWM・ADPCM)
- AWM(0x54)・ADPCM-B(0x51)・ADPCM-A(0x52)は`HwPatch`(`ops`)を使わず、
  `SampleZonePatch`(`*.samplezonebank.json`/`*.pcmbank.json`)を使う。
- AWMの波形ごとの校正`pitch_offset`/`key_scaling`/`tone_attenuate`/
  `volume_factor`は、ALSA `sound/drivers/opl4/yrw801.c`の`opl4_sound`の同名
  メンバーと同じ規約。OPL4AWM以外のチップでは使われない。
- `*.pcmbank.json`内の`bin_file`/`adpcm_json`はそのpcmbank.json自身の
  ディレクトリ基点で解決される。
- ADPCM-Aの`patch_prog`は`entries[]`の配列インデックスそのもので、パック用レシピ
  (`params_*.json`)の`wav_files[]`の並び順で決まる。欠番を作れないため、エントリーを
  抜くと後続のprogが繰り上がり、参照する全ドラムキットが別の音を指す。並びを変えた
  ときの波及先: レシピ→`adpcm_packer`で`.bin`/`.json`再生成、`*.pcmbank.json`の
  `swpatches`、ADPCM-Aを参照するドラムキット、`unified.bankset.json`/プロファイル、
  `docs/manuals/`、`docs/instruments/`。
- サンプルの開始アドレスはチップのアドレス単位に揃っていなければならない。FITOM_Xは
  開始オフセットを`addrShift`ビット右シフトしてレジスタへ書くため、揃っていないと
  下位ビットが黙って落ちる。単位はOPNA/Y8950のADPCM-Bが4byte(`addrShift=2`)、
  OPNB/OPNBBのADPCM-Bが256byte(`addrShift=8`)、ADPCM-Aが256byte。`*.pcmbank.json`の
  `boundary`(`adpcm_packer`の整列単位、32か256)はこの単位の倍数にする。
  FITOM_Xは`boundary`を検証に使わない。
- OPNB/OPNBBのADPCM-BはOPNA/Y8950とアドレス単位が違うため、メモリイメージ
  (カタログキー`OPNB_ADPCM-B`)とオフセット表(`pcm_banks`の`chip: "OPNB"`)を別に持つ。
  同じgroupでchip違いのエントリを併用するときは`chip`を明示する。
- 同じカタログキーのイメージを使うチップ(OPNAとY8950の`ADPCM-B`等)は、1つの
  メモリイメージを共有する。`pcm_banks[].chip`を分けても別のイメージは載らないため、
  通常のプリセットとは排他になる(worklog 3.63、ユーザーからの情報)。
- ADPCM-Bを持つチップには、`pcm_banks`に`chip`の一致するエントリを必ず置く(今は
  OPNA=bank 0、OPNB/OPNBB=bank 2、Y8950=bank 4、OPL2EX=bank 5。Y8950とOPL2EXは
  OPNA向けと同じ`*.pcmbank.json`を`offsets_only: true`で指す)。一致が無いと、FITOM_Xは
  groupが同じバンクのうち`unordered_map`で最初に見つかったものを使うため、OPNB向けの
  表が黙って選ばれうる。どの表が使われたかは起動ログの
  `CAdPcmBase: PCM voice table registered, ... (bank N)`で分かる。
- `offsets_only: true`のバンクから、FITOM_Xは音色を作らない(CC#32で選んでも鳴らない)。
  インストゥルメントリストにも載せない。
- `wavs/`はgit管理外、`banks/PCM/common/_fixed_source/`は管理下。`wavs/`の音が
  8bitで`_fixed_source/`に同じ音の16bit版があるときは、パック用レシピは
  `_fixed_source/`側を参照する。

### ドラムキット
- 通常のドラムキット(`drum_banks[]`)は`prog`がProgram Change値。CC#32=0の1バンク内で
  Program Changeによってキットが切り替わる。
- 内蔵リズム音源(CC#0=112)は`patch_prog`がそのままチャンネル番号。
  OPNA: 0=BD, 1=SD, 2=Top Cymbal, 3=HH, 4=Tom, 5=Rim Shot。
  OPLL: 0=HH, 1=Top Cymbal, 2=Tom, 3=SD, 4=BD。
  OPL系疑似リズム(0x23)は`ext.rhythm_ch`(0=HH, 1=CYM, 2=TOM, 3=SD, 4=BD)が楽器を
  決める別軸のため、同じ楽器に複数のバリエーションを別progで持てる。
  ビルトインリズム用のキットは`drum_banks[]`のprog 11=OPNA, 12=OPLL, 13=OPL,
  14=DSG。
- `type: "direct"`のキットはpatchbankを経由せず、`voice_patch_type`を直接指定して
  `hw_bank`/`hw_prog`を参照し、`note_min`/`note_max`の全域を1パッチへ流す
  (例: `opl4awm.drumkit.json`)。
- ハイハット等のチョークは`choke_groups`(drumkitトップレベル)で書く。旧`fixed_ch`は
  廃止。`type: "routed"`のキットには全てGM2標準の
  `[[42,44,46],[71,72],[73,74],[78,79],[80,81]]`を付ける(該当ノートが無ければ
  発火しないだけ)。`type: "direct"`は`choke_groups`を持てない。
- `type: "routed"`のキットはGM2のノート27-87を全て持つ。割り当てる音が無いノートは
  `voice_patch_type=127`(SILENCE、`patch_bank`/`patch_prog`は0)の無音エントリにし、
  名前の末尾に`(placeholder)`を付ける。存在しないprogやパートを指して無音にすると
  解決失敗になり、叩くたびに警告が出るので使わない。
- `DrumNote::fine_tune`はkfs単位(1半音=64ステップ)。

### SwPatch(パフォーマンスパッチ)
- 変換元にパフォーマンス情報(ベロシティ感度・LFO等)が無いHwPatchには、
  `sw_bank=0`(`banks/sw/performance_presets.swbank.json`)のVTLだけを設定した
  汎用パッチを割り当てる。VTLはキャリアにだけ掛ける: キャリアの組み合わせごとの
  prog 24-31(対応表は`docs/manuals/swbank.md`)、全opがキャリアになるもの
  (OPN/OPM/OPZのALG=7、OPL3のALG=3)はprog 2。
- 変換元にパフォーマンス情報があるバンクは1パッチずつ専用の`sw_prog`を持つ。
  複数パッチが同じ`sw_prog`を共有していること自体はバグではない。
- 変換元のHW LFO設定(LFO SPEED/DELAY/PMD/WAVE/SYNC等)を`sw.*`(ソフトLFO)へ
  流さない。`sw.LFR>0`の音色ではCC#1のモジュレーションが効かなくなる。ソフトLFOを
  使わないパッチは`sw`オブジェクト自体を書かない(既定は全フィールド0)。
- `ops[]`の各要素は値を持つキーだけを書く(`{"VTL":80}`等)。`jsonToSwOp`は存在する
  キーだけを上書きする。
- DX/TX81Z由来(VMEM): キャリアは`VTL=80`固定、モジュレータはKVSから
  `KVS 0-7 → VTL 0/42/89/127/127/127/127/127`、KVS>0のopはTLに`8-KVS`を加算する。
  FB-01はKVSを持たないため全opで`VTL=80`。

### プロファイル
- パスの基点:
  - `banks`/`bank_overrides`の文字列参照と`banks.*[].file`は、プロファイル自身の
    ディレクトリ基点。
  - `hw_plugins[].profile`はプロセスのカレントディレクトリ基点(プラグインがそのまま
    開く)。リポジトリルートから起動する前提で`"config/profiles/hw_plugins/<file>"`と書く。
  - サブプロファイルの`engines[].dll`は`FitomEmuIF.dll`のディレクトリ(`bin/`)基点。
    `"engines/<DLL名>"`と書く。
  - サブプロファイルの`pcm_catalog`はサブプロファイル自身の基点、カタログ内
    `images{}`の値はカタログファイル自身の基点。
- `config/fitom.conf.json`(実行時は`bin/`へコピーされる)が扱うのは`log.*`と
  `profiles.root`だけ。HWプラグイン・MIDIバックエンドのDLLはプロファイル側
  (`hw_plugins[]`/`midi_backend.dll`)で指定する。
- 全プロファイルの`banks`は`"unified.bankset.json"`(共有カタログ)にする。デバイス
  構成に無いチップ向けのバンクは鳴らないだけで実害は無い。
- `unified.bankset.json`の`sw_banks[].bank`の番号は、各hwbankのパッチが持つ`sw_bank`の
  値から参照されている。番号を付け替えると黙ってずれる。
- `bank_overrides`は`banks`と同じ形で、識別キーが一致すれば置換、しなければ追加
  (削除はできない)。識別キーは`hw_banks`=group+bank、`pcm_banks`=bank+chip、
  `drum_banks`=prog、他は`bank`。HWチップを持つプロファイルは、レイヤードバンク0と
  ドラムキット0をそのプロファイルに必ずあるデバイス向けのものに置き換える
  (共有カタログのbank0は空のskeleton)。
- `devices[]`:
  - `chip`の文字列は、エンジンの受理名とFITOM_Xの正式名(`resolveChipDeviceId()`)を
    同時に満たす必要がある(FitomEmuIFはそのままエンジンへ渡す)。
  - 明示する`devices[]`には`type: "FMHWIF"`と`engine`が必須。`engine`はサブ
    プロファイルの`engines[].dll`と完全一致させる。
  - `auto_devices: true`は`devices[]`を置き換えない。列挙が先にスロットを使うため、
    同じチップを指す`devices[]`は黙ってスキップされる。`devices[]`で構成を書くなら
    `auto_devices: false`にする。`auto_devices`のまま内蔵リズムを使うなら
    `hw_plugins[].auto_devices_rhythm_mode`にチップ名を列挙する。
  - `devices[]`の要素に`_comment`を置かない(`HWPlugin_Open`のparamsへ転送され
    起動ログに出る)。理由はトップレベルの`_comment`に書く。
- ステレオの扱いはFITOM_Xの`FITOMConfig::getChipPanType()`の分類で決まる
  (どのチップがどれに当たるかは、そのswitch文が原本):
  - `Mono`(SSG・OPLL系・OPL/OPL2/Y8950・DCSG・SCC・EPSG・DSG・素のOPN等)は、
    `stereo_pair: true` + `pan: 1`/`2`(プラグイン側でL/Rへ振り分け)で2個を束ねる。
  - `ThreeWay`(チップ自身がL/R出力ビットを持つOPM/OPZ/OPL3系/OPN2・OPNA・OPNB系と
    そのADPCM部)は`stereo_pair: "L"`/`"R"`(`pan: 0`)を使える。ただしOPZはL単独の
    定位ビットが無く、L側は左右に分離されない(FITOM_Xのコメント)。
  - `Continuous`(chごとの定位をハードで持つSAA・OPL4のAWM部・SSGS系・Y8960の
    OPLLEX/OPL2EX/SSGEX/SCCEX)は束ねず、1個を`pan: 0`で載せる。束ねると本来の
    パンポットを潰した上でチップを2倍使う。FITOM_Xの`subDeviceAcceptsStereoPair()`は
    このうちOPL4のAWM部・SSGS系・OPLLEX/OPL2EXに`stereo_pair`を伝播しない。
- 内蔵リズムは`resolveBuiltinRhythm()`が同系統のデバイスの最初の1件しか使わない。
  同系統のチップに重ねて`rhythm_mode`を付けない。OPLLEXのリズムはCC#0=112の
  「OPLL」選択で、標準OPLLのリズムが無い構成なら鳴る。
- 同じVoicePatchTypeのチップを複数載せると`mergeSpannableDevices()`が1デバイスへ
  統合する。素のOPN(YM2203)はcomposite展開されずSSG部を持たない。
- OPMとOPZの間のフォールバックは非対称。OPM向け(0x19)の音色は常にOPZで鳴る。
  OPZ向け(0x1A)の音色がOPMで鳴るのは、OPZの拡張(`ops[].WS`/`REV`/`EGS`/`DT3`)を
  1つも使っていないときだけ(`copmAcceptsFallback()`/`copzAcceptsFallback()`)。
  OPMとOPZのどちらの構成でも使うレイヤードバンクは、レイヤーをOPM向けにする。
- `sf2_banks`/`sf2_channel_windows`を持つプロファイルは`devices[]`に
  `{ "if": "HW", "chip": "SF2", "plugin": "FitomSf2IF" }`が必須(無いと起動時エラー)。
  `unified.bankset.json`が`sf2_banks`を持つため、これを参照する全プロファイルが該当する。
  `sf2_channel_windows`の既定はch14/15(0起算)→`fluidsynth_chan` 0/1。`mpu`は
  DAW側入力のMPU番号に合わせる(判別できなければ0)。SF2直行パスは窓に入ったchの
  CC#0を見ない。
- `config/profiles/**/*.json`は`filter=envlocal eol=crlf`。`midi_inputs`の各要素と
  `"port"`の値は索引上`"__LOCAL__"`に正規化され、作業ツリー側は自由に書き換えてよい。
  フィルタの実行コマンドは`setup.ps1`/`setup.sh`がローカルのgit configへ登録する。
  新しい種類の環境依存フィールドを足すときは`tools/git_filters/normalize_env_fields.py`
  に正規表現を足す。フィルタは正規表現によるテキスト置換に留める(JSONを読み込んで
  書き直すと、1行に詰めたオブジェクトが展開されて無関係な差分が出る)。
- プロファイル本体は、FITOM_XのGUIが保存する形(キーを辞書順に並べ、インデント2、
  1行に詰めない)で置く。GUIはMIDIポートを設定するたびにファイル全体をこの形で
  書き直すため、別の形で置くと整形だけの差分が出る。サブプロファイル(`hw_plugins/`)は
  GUIが保存するか確かめていないので、手書きの形のままにしている。
- ADPCM/AWMを持つチップを載せるサブプロファイルには
  `"pcm_catalog": "../../../pcm_image_catalog.json"`を書く。カタログの`images`は
  種別名(`ADPCM-A`/`ADPCM-B`/`OPNB_ADPCM-B`/`OPNA_RHYTHM`/`OPL4AWM`/`SSGS_ADPCM`)を
  キーとするオブジェクトで、1種別1ファイル。

### エンジンとクロック
エンジンDLLごとに受理するチップ名が固定で、どのチップをどのエンジンで鳴らすかは
これで決まる(各エンジンのREADMEが原本)。

| エンジン(DLL名) | 受理するチップ名 |
|---|---|
| `YMFMEngine`(リポジトリ名はYMEngine) | Y8950/OPL/OPL2/OPL3/OPL4/OPN/OPNA/OPNB/OPNBB/OPN2/OPM/OPLL/OPLLP/OPLLX/OPZ/VRC7 |
| `FmGenEngine`(リポジトリ名はFMgenEngine) | OPN/OPNA/OPNB/OPNBB/OPN2/OPM/SSG |
| `DSAemuEngine` | SSG/OPLL/OPLLP/OPLLX/VRC7/Y8950/OPL/OPL2/SCC/SCCP/DCSG/OPL2EX/OPLLEX/SSGEX/SCCEX |
| `EPSGemuEngine` | EPSG/SSG/SSGS/SSGS2/SSGS3 |
| `Y8960emuEngine` | OPL2EX/OPLLEX |
| `SAASoundEngine` | SAA |
| `DSGemuEngine` | DSG |

- YMFMEngineはOPLL2を持たない。
- エンジンのDLL名が変わったら、サブプロファイルの`engines[].dll`、プロファイルの
  `devices[].engine`、`setup.ps1`(コピー行とヘッダー)・`setup.sh`、`README.md`の対応表を
  揃える。`setup.ps1`は古い名前のDLLを消さないので、`bin/engines/`に残った旧DLLは
  別に消す。
- Y8960(OPLLEX/OPL2EX/SSGEX/SCCEX)はDSAemuEngineで鳴らす。SSGEX/SCCEXを持つのは
  DSAemuEngineだけで、Y8960emuEngineは`src/`を検索した範囲では定位レジスタの実装が
  見当たらない(**読解のみ**、`40298b9`)。Y8960emuEngineが定位レジスタとSSGEX/SCCEXを
  実装したら見直す。Y8960のOPMは拡張レジスタを持たない標準のYM2151で、`chip: "OPM"`で
  載せる(FITOM_Xの`docs/design/chip-notes.md`「Y8960 の拡張ブロック」)。
- エミュレーターは`chips[].clock`のクロックでチップを動かす。FITOM_Xがそのクロックを使うか
  どうかはチップ族で違う(FITOM_X `b7c1e4c`を読んで確認。**読解のみ**):
  - PSG系・DSG・SAA・ADPCM/PCM: FITOM_Xはプラグインが報告するクロック(`port->getClock()`)
    から音程・再生レートを計算する。どの値を書いても音程は合い、値が変えるのはそのクロックで
    動くチップの音(ノイズ・エンベロープ・リズムROM等)だけ。
  - FM系: FITOM_Xは固定のマスタークロックでF-Number/KCを計算し、プロファイルの値を読まない
    (OPL/OPL2/Y8950/OPLL系=3579545、OPL3=14318180、OPN=3993600、OPN2/OPNA/OPNB=8000000、
    OPM/OPZ=3579545前提)。プロファイルの値がこれと違うと、その比の分だけ音程がずれる。
    FITOM_Xのバグとして扱う(STATUS 4節)。直るまでは、FM系の音程の確認では
    この食い違いを先に疑う。

### 変換スクリプト(`tools/voice_convert/`)
- **MA-2 VMA**(`vma_convert.py`): グローバルバイトのALGは3bit(`byte3 & 7`)。
  オペレータ5バイト目は`AM`=bit3・`WS`=bits2-0。EGTビットは実機OPLと同じ極性
  (1=持続、0=減衰)。全opの`AR=0`のパッチは未使用のプレースホルダとして出力しない
  (progに欠番が出る)。
- **VMEM(DX21/DX27/DX100/DX11/TX81Z)**(`vmem_convert.py`/`tx81z_convert.py`):
  - オペレータはレジスタのスロット順M1,M2,C1,C2で格納されている(パネル表記の
    OP4=M1/OP3=C1/OP2=M2/OP1=C2)。`addr10→ops[2]`、`addr20→ops[1]`。
  - `P+9`は`[0:3][RS:2][DETUNE:3]`。`DT1`はDETUNE 0-6(中央3、`3→0, 4/5/6→1/2/3,
    2/1/0→5/6/7`)、`KSR=(p9>>3)&3`。
  - `P+6`は`[0:1][AME@bit6][EBS@bits5-3][KVS@bits2-0]`。
  - `SL = 15 - d1l`(VMEMはレベル、OPMのD1Lは減衰量で極性が逆)。
  - `TL`はOUTPUT LEVEL用の変換表(20-99は`99 - OL`、0-19は専用ルックアップ表。
    https://nornand.hatenablog.com/entry/2020/11/21/201911 )。同じブログの
    Volumeパラメータ用の表は別のカーブなので流用しない。
  - キャリアのTLにキャリア本数による正規化`A_alg`(1本0/2本8/3本13/4本16)を加算する。
  - `P+8`のbit7は実データで一度も立たない死んだフィールドで、`ext.FIX`に割り当てない。
  - `tx81z_convert.py`は今も`"hw"`/`"sw"`をネストした旧形式のhwbankを1本出すだけで、
    swbankを出さない。ネストした`hw`は読まれないため、出力はそのままバンクとしては
    使えず、in-place更新の値の材料にだけ使う。
  - `banks/OPZ/gm128/gm128_preset.hwbank.json`はDX/TX/FB-01由来・`opmdrv`由来・由来不明の
    パッチが混在する手組みのバンク。VMEMの変換規則を直したら、`ALG`/`FB`/ops全フィールドの
    一致で由来を特定し、VMEM由来のパッチにだけ同じ修正を反映する。
- **FB-01**(`fb01_convert.py`): voice dataは既にチェーン順で、並べ替えない。
  レジスタ生値のダンプなので、VMEMの値解釈・`A_alg`は掛けない。
- **OPLLカスタム音色**(`opll_convert.py`): R#3のDM(モジュレータ波形)=bit3、
  DC(キャリア波形)=bit4。
- **ALSA sbiload**(`alsa_convert.py`): 未使用エントリ(マジック`0x00000000`)を
  出力しないため、progに欠番が出る。
- `banks/OPL2/msx_audio/`には変換スクリプトが無い。規則を直したときは、各ファイルの
  `note`に書かれた変換規則を読んで、データを直接直す。
- **opl2_merge.py**: 2つのOPL2バンクから4OPパッチを作る。ALGはパッチ単位で各ソースの
  元の値を維持し(`--alg-a`/`--alg-b`未指定時)、ConnectionSELは`ext.ALG_EXT`=0。
  入力の値をそのまま引き継ぐだけなので、合成元を直したら派生バンク
  (`banks/OPL3/opl2_merge/`)へprog・op単位で同じ修正を反映する(再合成すると後付けの
  `PDT`等が消えるため、in-placeで直す)。
- 後加工(フラット化・`sw_bank`/`sw_prog`付与等)の入った既存バンクは、丸ごと
  再変換せず該当フィールドだけをin-placeで更新する。再変換で`sw_bank`/`sw_prog`が
  落ちる場合は復元する。いずれも、変更が意図したフィールドだけであることを
  git HEADとの比較でプログラム的に確かめる。
- 変換規則の極性やビット位置を変えるときは、1音色の聴感比較ではなく実データ全体の
  分布・統計で裏付ける。

### インストゥルメントリスト(`tools/instrument_export/`)
- `generate_instruments.py`が共有バンクセット`unified.bankset.json`から、Sekaiju/Cakewalk用
  `docs/instruments/sekaiju/FITOM_X.ins`とDOMINO用`docs/instruments/domino/FITOM_X.xml`を
  生成する。機材は`FITOM_X`の1つだけ(ASCII名。マルチバイト不可)。全プロファイルが同じ
  バンクセットを読むので、名前と音の対応はプロファイルによらない(チップが無くて鳴らない
  音色があるだけ)。プロファイルごとの機材は作らない。詳細は同ディレクトリの`README.md`。
- `sw_banks`は載せない。レイヤードバンク0・ドラムキット0は、プロファイルごとの
  実際の割り当てに関わらずGM標準の名前で表示する。
- ファイルを持たないビルトインも載せる(搭載チップで絞らない): OPLL ROM音色(CC#0=40/41/42/43はそれぞれのvariant、CC#0=44は4バンク60音色に
  `[OPLL]`等を前置)、DSGビルトイン(CC#0=68)、内蔵リズム(CC#0=112、CC#32=17=OPNA/
  40=OPLL/68=DSG)。名前の原本はFITOM_XのGUIブリッジ(`FITOMBridge.cpp`)と
  `PatchManager`のテーブル。
- 通常ドラムキットはCC#0=120(GM2 Percussion相当)、SF2バンクはCC#0=127(sf2ファイルの
  `phdr`をパースして名前を取る)に置く。どちらもリスト上の表示規約。
- `sf2/`の無いマシンで再生成するとSF2の音色名が抜ける。再生成は`sf2/`のある
  マシンで行う。
