# FITOM_staging 現在の状態

この文書には現在の状態だけを書く。守るべき規則はルートの`CLAUDE.md`、
そこに至った経緯は`docs/worklog/`(月ごと)にある。本文中の「worklog 3.60」は
`docs/worklog/`の該当番号の節を指す。

## 1. プロファイル

全プロファイルが`banks`に`config/profiles/unified.bankset.json`を共有参照する
(worklog 3.32)。デバイス構成に含まれないチップ向けのバンクは鳴らないだけで
実害は無い。プロファイルごとに違うのは`devices`/`hw_plugins`と`bank_overrides`。

2026年10月23日時点の構成(**確認済み**: 全17ファイルをスクリプトで集計)。
「×2(ペア)」は`stereo_pair`でL/Rに束ねたもの、「auto」は`hw_plugins[]`の
`auto_devices`でサブプロファイルのチップをそのまま開くもの。全プロファイルが
SF2(FitomSf2IF)デバイスを持つ。

| ファイル | デバイス構成 | `bank_overrides` |
|---|---|---|
| `unified_preset` | auto: OPN2/OPNA/OPNB/OPNBB=YMFMEngine | あり |
| `emu_opn` | auto: OPN2/OPNA/OPNB/OPNBB=YMFMEngine | あり |
| `emu_fmgen_opn` | auto: OPN2/OPNA/OPNB/OPNBB=FmGenEngine | あり |
| `emu_opn_stereo` | OPN2/OPNA/OPNB/OPNBB×2(ペア)=YMFMEngine | あり |
| `emu_opl` | Y8950[rhythm]/OPL3/OPL4=YMFMEngine | あり |
| `emu_opl_stereo` | Y8950[rhythm]×2/OPL3×3/OPL4×1(ペア)=YMFMEngine | あり |
| `emu_opm` | auto: OPM×4=YMFMEngine | あり |
| `emu_opz` | auto: OPZ×4=YMFMEngine | あり |
| `emu_opll` | OPLL[rhythm]/OPLLP/VRC7/OPLLX=YMFMEngine、OPLLEX=DSAemuEngine | あり |
| `emu_opll_stereo` | OPLL[rhythm]/OPLLP/VRC7/OPLLX×2(ペア)=YMFMEngine、OPLLEX=DSAemuEngine | あり |
| `fmall` | OPZ×2/OPNBB×2/OPL3+OPL4(ペア)=YMFMEngine、OPLLEX[rhythm]=DSAemuEngine | あり |
| `emu_psg_stereo` | DCSG/SCC×2(ペア)=DSAemuEngine、EPSG×2(ペア)/SSGS/SSGS2/SSGS3=EPSGemuEngine、DSG×2(ペア)=DSGemuEngine、SAA=SAASoundEngine | なし |
| `emu_msx` | OPLLEX[rhythm]/Y8950[rhythm]/SSG/SCCP=DSAemuEngine、OPM=YMFMEngine | あり |
| `emu_msx2pp` | Y8960 1基: OPLLEX[rhythm]/OPL2EX/SSGEX/SCCEX=DSAemuEngine、OPM=YMFMEngine | あり |
| `emu_pc88` | OPN/OPNA/OPM=YMFMEngine | あり |
| `emu_pc98` | OPN/OPNA/OPL3/Y8950[rhythm]=YMFMEngine | あり |
| `emu_ibmpc` | SAA×2=SAASoundEngine、OPL2[rhythm]/OPL3/OPM=YMFMEngine、DCSG=DSAemuEngine | あり |

実機(FitomHwIF)を使うプロファイルは現在無い(worklog 3.30)。

## 2. `bin/`

`bin/`はgit管理外で、マシンごとに中身が違う。下の表は、最後にビルドしたマシンで
2026年10月24日にRelease版をビルドし、`setup.ps1`で配置したときのコミット(worklog 3.70)。
他のマシンの`bin/`がこの状態だとは限らない。そのマシンの`bin/`の中身は
`bin/build_info.json`で分かる(`setup.ps1`が書く)。

| リポジトリ | コミット |
|---|---|
| FITOM_X | `b7c1e4c` |
| FitomEmuIF | `87d0a6c` |
| FitomHwIF | `a2357ea` |
| FitomSf2IF | `ae15e91` |
| YMEngine | `3600db7` |
| FMgenEngine | `4e3e82e` |
| DSAemuEngine | `46c2fbe` |
| EPSGemuEngine | `72f70d6` |
| SAASoundEngine | `7c30ab4` |
| DSGemuEngine | `f7834f6` |
| Y8960emu | `40298b9` |
| FITOM_patch_editor | `e2e0ecc` |

この状態で全17プロファイルを`bin/fitom_cli.exe`で起動し、`Failed to create HWPort`・
`unknown chip`が0件であることを確認した(**確認済み**、2026年10月24日)。出た警告は
4節の既知の項目(`emu_psg_stereo`)だけ。
`fitom_hw.dll`(FitomHwIF)も配置されている。
## 3. ドキュメント

- `docs/manuals/`: 利用者向けリファレンス。`README.md`が起点
- `docs/instruments/`: MIDIシーケンサー向けインストゥルメントリスト
  (`sekaiju/FITOM_X.ins`、`domino/FITOM_X.xml`。`tools/instrument_export/`で生成)
- `docs/voice-parameter-reference.md`: 音色パラメータの解説(FITOM_X側の原本由来。
  原本はFITOM_Xで分割・削除され、利用者向けの内容は`docs/manuals/hwpatch-reference.md`、
  チップ別の内部処理は`docs/design/chip-notes.md`へ移った)
- `docs/worklog/`: 変更・修正・調査の経緯

## 4. 未解決・要確認事項

### 聴感確認(ユーザーが確かめる)

起動ログで分かるのはデバイスとバンクのロードまでで、以下は実際に鳴らして確かめる
必要がある。確かめたら行を消し、結果を`docs/worklog/`に書く(不具合が見つかったら
下の「構成・データの問題」へ移す)。見出しのチップ構成は1節の表と同じ。

**準備**
- [ ] そのマシンの`bin/build_info.json`で、`bin/`が2節の表のコミット以降のビルドで
  あることを確かめる(違えば`.\setup.ps1 -Pull -Build`)

**プロファイルを問わないもの**
- [ ] `bank_overrides`(worklog 3.33/3.77): `emu_psg_stereo`以外の16本で、
  通常モード(CC#0=0, CC#32=0)の音色と、ドラムchのprog 0のキットが鳴る。読み込まれる
  ことは**確認済み**(2026年10月24日、起動ログの`Patch bank=0 prog=0 is empty`が
  この16本では0件)
- [ ] SF2(worklog 3.31/3.36): MIDI ch15/16(0起算の14/15)がSF2で鳴る。全17本でSF2の
  HWPortが開くことは**確認済み**(2026年10月23日、起動ログ)。`sf2/`(配布対象外)の無い
  マシンでは`SF2 phdr parse: cannot open`の警告が出る。`unified_preset`/`emu_opm`/
  `emu_opn`/`fmall`の`sf2_channel_windows`の`mpu`は、`midi_inputs`が`__LOCAL__`で
  DAW側のMPUを判別できず0を暫定採用している。鳴らないときはこの値も確かめる
- [ ] ドラムキットの無音プレースホルダ(worklog 3.57): `type: "routed"`のキットで、
  割り当てる音の無いノート(名前の末尾が`(placeholder)`)が鳴らず、他のノートは鳴る
- [ ] 汎用VTL(worklog 3.21): `sw_bank=0`の汎用パッチ(prog 2, 24-31)を割り当てた音色で、
  ベロシティがキャリアにだけ効く。FITOM_X本体が`sw_prog`で指定されたSwPatchのVTLを
  正しいopへ適用していることは、このリポジトリからは確かめていない
- [ ] インストゥルメントリスト(`docs/instruments/`の`.ins`/`.xml`)がSekaiju/Cakewalk/
  DOMINOで読み込める(構文検証のみ。Studio One/REAPERは検証環境が無いため保留、
  worklog 3.29)

**`emu_opm`(OPM×4) / `emu_opz`(OPZ×4)**
- [ ] レイヤードバンク(worklog 3.73): OPZの拡張(WS/REV/EGS)を使う12音色(prog 0,19,20,
  28,30,43,50,65,66,94,98,105)が、`emu_opm`では拡張の抜けた音で鳴る。これを受け入れ
  られるか。`emu_opz`では拡張も効くはず(PatchManagerを読んだだけ。**未検証**)。
  ドラムキット`opm_standard`(prog 0)のノート28,30,43,50,65,66も同じ12音色を指す。
  他の116音色は両方で鳴るはず(起動時の解決はどちらも**確認済み**: 起動ログ)
- [ ] DX/TX81Z/FB-01由来のバンク(worklog 3.44〜3.48。直接モードCC#0=25(OPM)/26(OPZ)、
  CC#32=2 FB-01、3 DX11、4 DX21、5 DX100_1、6 DX100_2、7 TX81Z): データ側の整合性検証
  のみ。特にDT1(デチューン)とSL(D1L極性)は音の印象を大きく変える
- [ ] 同じバンクのモジュレータへのVTL適用(worklog 3.48): モジュレータのベロシティ追従が
  意図どおり効く。本体側は修正済み(FITOM_X `0293740`。**読解のみ**)。KVS>=3が
  `VTL=127`で飽和して実機より約17dB浅くなる点が聴感上問題になるかも評価する(データ側
  では解消できない。必要なら本体側でVTLの変動幅上限`VTL/2`を見直す)

**`emu_opn` / `emu_fmgen_opn` / `emu_opn_stereo`(OPN2/OPNA/OPNB/OPNBB)**
- [ ] ADPCM-Aのドラムキット(prog 0=PSS-480、16-22・24・40)が意図した音色で鳴る。
  機種の入れ替え(worklog 3.62)でprogがずれているため、キットごとに確かめる。
  鳴れば`pcm_image_catalog.json`経由のADPCM-Aのイメージのロード(worklog 3.22)も
  確かめたことになる
- [ ] ADPCM-B(CC#0=81)と、OPNAの内蔵リズム(ドラムのprog 11、またはCC#0=112・
  CC#32=17)が鳴る(イメージのロード、worklog 3.22)

**`emu_opl` / `emu_opl_stereo`(Y8950[リズム]/OPL3/OPL4)、`fmall`**
- [ ] OPL4のAWM(worklog 3.35): 意図した音高・音量で鳴る。`fmall`は通常モードの
  バンク0とドラムのprog 0がAWM。`emu_opl`/`emu_opl_stereo`ではCC#0=84の直接モードか、
  ドラムのprog 15。対応する本体側の修正(FITOM_X `830e59a`)込みのバイナリは配置済み。
  確かめたのはJSON構文・スキーマ検証と、全610ゾーンのフィールド充足だけ。鳴れば
  AWMのROMイメージのロード(worklog 3.22)も確かめたことになる
- [ ] Y8950のADPCM-B(CC#0=81)が鳴る(イメージのロード、worklog 3.22)

**OPLLEX: `emu_opll` / `emu_opll_stereo` / `fmall`**
- [ ] OPLLEX(CC#0=44)が鳴り、MIDIのパンポットがchごとの定位として効く(worklog 3.64/3.66)。
  デバイスが生成されることまでしか確かめていない

**`emu_msx2pp`(Y8960: OPLLEX[リズム]/OPL2EX/SSGEX/SCCEX、OPM)**
- [ ] OPLLEX・OPL2EX・SSGEX・SCCEX・OPMが鳴り、OPLLEX/OPL2EX/SSGEX/SCCEXでMIDIの
  パンポットがchごとの定位として効く(worklog 3.64/3.66)
- [ ] SCCEXが鳴る(下の`emu_msx`のSCC+と同じ経緯)
- [ ] OPL2EX内蔵のADPCM-B(CC#0=81・CC#32=0)が鳴る(worklog 3.79)。イメージはカタログの
  `ADPCM-B`(OPNA向けと共有)をFitomEmuIFが渡し、FITOM_XはOPNA向けと同じオフセット表
  (`pcm_banks`のbank 5)を使う。FitomEmuIF・DSAemuEngineがイメージを渡せたかはログに
  出ないので、**読解のみ**。オフセット表の選択は起動ログで**確認済み**

**`emu_msx`(OPLLEX[リズム]/Y8950[リズム]/SSG/SCC+、OPM)**
- [ ] 各チップが鳴る(worklog 3.60。起動ログでの確認のみ)
- [ ] MSX-MUSICをOPLLからOPLLEXに替えた(worklog 3.78): レイヤードバンク0の128音色と
  ドラムキット0の21ノートが、すべてOPLLEXで鳴る(解決できることは**確認済み**:
  `coverage.py`)。それまでOPLLで鳴っていた104音色と内蔵リズムも、OPLLEXで鳴るように
  なった
- [ ] SCC+が鳴る。以前の無音の原因2件(DSAemuEngineがemu2212のレジスタ窓の外へ書いて
  いた件、FITOM_Xの`CSCC`のレジスタ配置が重複していた件)は、どちらもコード上は解消
  している(**読解のみ**、2026年10月23日)。DSAemuEngine(`46c2fbe`)は
  `SCC_write(scc, 0x9000, 0x3F)`で有効化してから`0x9800+reg`へ書き、FITOM_X
  (`e528e23`)の`CSCC`は無印SCCを周波数`0x80`/音量`0x8A`/イネーブル`0x8F`、
  SCC+を`0xA0`/`0xAA`/`0xAF`で書く。鳴ったら、プロファイル`_comment`の「SCC+は無音」を
  直す

**`emu_pc88`(OPN/OPNA/OPM) / `emu_ibmpc`(SAA×2/OPL2[リズム]/OPL3/OPM/DCSG)**
- [ ] 各チップが鳴る(worklog 3.60。起動ログでの確認のみ)

**`emu_pc98`(OPN/OPNA/OPL3/Y8950[リズム])**
- [ ] 各チップが鳴る(worklog 3.60。起動ログでの確認のみ)
- [ ] ADPCM-B(CC#0=81)が、OPNAとY8950に統合された1デバイスとして正しく鳴る。
  worklog 3.60は「Y8950側へ回ったボイスがOPNA基準のオフセット表で再生される」
  可能性を挙げた。ただし、根拠にした「Y8950は4byte境界でOPNAと違う」は、FITOM_Xの
  コード上は成り立たない(両者ともアドレス単位4byte、**読解のみ**)

**`emu_psg_stereo`(DCSG/SCC×2/EPSG×2/SSGS/SSGS2/SSGS3/DSG×2/SAA)**
- [ ] SSGS系・DCSG・EPSG・SAAが鳴る(worklog 3.53。起動ログでの確認のみ)
- [ ] SCCが鳴る(上の`emu_msx`のSCC+と同じ経緯)
- [ ] DSG(worklog 3.54/3.55): ビルトイン音色(CC#0=68、prog 0-19)と内蔵リズム
  (ドラムのprog 14、またはCC#0=112・CC#32=68)が鳴る

### 構成・データの問題

- **`emu_psg_stereo`が`bank_overrides`を持たない**(worklog 3.53): 通常モードの
  bank 0が空のskeletonのまま。演奏はCC#0=0x40(SSG共有バンク)の直接モードで行う
  前提。揃えるならPSG系向けのレイヤードpatchbankを新設して`bank_overrides`で
  差し替える(ユーザー指示で作成していない)。
- **`setup.sh`が`setup.ps1`と食い違っている**(worklog 3.71): `setup.sh`は動作実績が無く、
  `setup.ps1`への変更に追従していないため、動作が相当食い違っているはず(ユーザーからの情報)。
  `-Pull`/`-Build`相当も無い。Linux/macOSで使うときに`setup.ps1`と突き合わせて直す。
- **ADPCM-B抜粋バンクが未参照**(worklog 3.63): `wavs_y8950_adpcmb_excerpt`は
  通常のADPCM-Bプリセットとの割り当て方を検討中のため、意図的にどこからも参照して
  いない。ADPCM-Bは親チップが違っても1つのメモリイメージに束ねられるため、
  通常のプリセットとは排他になる。
- `banks/drums/ma2_preset_2op.drumkit.json`・`ma2_variant_2op.drumkit.json`の
  GM2ドラムノート27,28,31-36,103-105(計11ノート)は、参照先
  (`banks/OPL2/ma2_vma/DrumsBank.hwbank.json`・`07_DrumsBank.hwbank.json`の
  prog 0,1,4-9,76-78)が全パラメータ空のプレースホルダのため鳴らない(worklog 3.27)。
  変換元`.vma`にも実データが無く、このリポジトリからは直せない。実害の大小は未評価。
- `banks/OPZ/gm128/gm128_preset.hwbank.json`の23パッチ(prog 10,23,31,36,37,54,59,
  67,76,77,83,88,92,97,100,108,109,110,111,119,120,121,126)は、`source`が挙げる
  8バンクのいずれとも`ALG`/`FB`/ops全フィールドが一致せず由来が特定できていない
  (worklog 3.44)。並び順・値解釈が正しいかの確認が必要。
- `banks/sw/necopn_gm.swbank.json`・`default_gm.swbank.json`・
  `default_32.swbank.json`・`compat_zero.swbank.json`は、どのプロファイルの
  `sw_banks[]`からも参照されていない旧形式(`LFO`/`LDM`/`LDL`/`SLF`等)の
  ファイル(worklog 3.13/3.21)。削除するか現行スキーマへ追従させるか要判断。
- `config/profiles/hw_plugins/fmemuif_fmall.profile.json`と
  `fmemuif_opm_opz4.profile.json`は、どのプロファイルからも参照されていない
  (worklog 3.59で、再利用しうるため残した)。`fmemuif_fmall`のOPLLEXは
  旧構成(Y8960emuEngine)のまま。
- `fmemuif_opl5.profile.json`/`fmemuif_opm_opz4.profile.json`/
  `fmemuif_opll5.profile.json`のクロック値は一般的な標準値からの推測
  (特にOPL4=33,868,800Hzは未検証)。
- OPLL GM128(`gm_layered_opll.patchbank.json`)はMA-2 Preset2OP由来が67/128と過半数。
  ソースを増やせる余地がないか要継続検討。
- `GeneralUser GS v1.471.sf2`のGS variationバンク(sf2_bank 1-16, 120)は
  `sf2_banks`未登録(worklog 3.31)。必要になったら`bank=10`以降に追加する。

### 判断待ち・保留

- **【保留】`profile_name`が実際の構成と食い違っている**(worklog 3.75): 必要ならユーザーが
  直す(ユーザー指示)。`emu_opn`/`emu_opn_stereo`/`emu_fmgen_opn`は「OPN/OPN2/OPNA/OPNB/
  OPNBB」だがOPNは載っていない。`emu_opl`/`emu_opl_stereo`は「OPL[rhythm]/Y8950/OPL2/OPL3/
  OPL4」だが、OPLとOPL2は載っておらず、リズムはY8950。`emu_psg_stereo`は「SSG/DCSG/SCC/
  EPSG/DSG 各2」だが、SSGは載っておらず、SSGS/SSGS2/SSGS3が各1。`unified_preset`は
  「全チップGM+専用バンク一式」だが、載っているのはOPN系4チップだけ。`emu_msx`は
  「OPLL[rhythm]/…」だが、OPLLはOPLLEXに替えた(worklog 3.78)。
- **CC#0=127の二重の意味**(worklog 3.57): FITOM_X本体では`VOICE_PATCH_SILENCE`
  (無音バンク)だが、インストゥルメントリストではSF2バンクの表示に使っている。
  SF2直行パスは`sf2_channel_windows`で切り分けられCC#0を見ないため実害は無いが、
  リスト上で「SF2バンク」に見えるものを窓外のchで選ぶと無音になる。表示規約を
  別のCC#0値へ移すか、リスト側に注記を足すか要判断。
- **ビルトイン音色用メタバンクが空**(worklog 3.54): `banks/OPLL/rom_sw_meta.hwbank.json`は
  空のスケルトンで、OPLL系ROM音色・DSGビルトイン音色のどちらにも
  パフォーマンスパッチが割り当てられていない。パッチ設計の判断が必要。
- **`emu_psg_stereo`をインストゥルメントリストに載せるか**(worklog 3.53):
  `TARGET_PROFILES`に入れていない。PSG系単独構成で既存8機材のいずれとも異なる。
- **【保留】PCED `LFOS=3`(Vibrato)の音色のソフトLFO変換**(worklog 3.45):
  DX/TX81Z/FB-01のLFOパラメータは一律「HW LFO用」として破棄しているが、
  TX81Z/DX11のPCEDで`LFOS=3`を選んだ場合は実機でもソフトウェアLFOとして動作する。
  該当音色は`sw.*`へ変換するのが本来正しい。実機のソフトLFOアルゴリズムの情報が
  無いため保留。調査済みの事実:
  - PCEDのダンプは手元に存在しない。変換元素材のSysEx系ファイル132件は全て
    フォーマット`0x04`(32音色VMEM)で、PCED/PMEMは1件も無い。VMEM 128バイト内にも
    LFOSに相当するフィールドは無い。
  - LFOSはパフォーマンスのインストゥルメント枠ごとの設定でボイスの属性ではないため、
    PCEDを入手できても128音色バンクへ1:1では対応しない。
  - LFO設定が音に効きうる音色数(PMD/AMDとPMS/AMSが共に非0、かつLFO SPEED>0)。
    変換を入れた場合の影響範囲の上限:

    | バンク | 音色 | ビブラート有効 | トレモロ有効 |
    |---|---|---|---|
    | dx11 | 128 | 80 | 23 |
    | dx21 | 128 | 61 | 14 |
    | dx100_1 | 128 | 47 | 12 |
    | dx100_2 | 128 | 34 | 14 |
    | tx81z | 128 | 76 | 25 |
    | 合計 | 640 | **298 (47%)** | 88 |

    `fb01`は80音色ともPMS/AMSが0で変調が成立しないため0音色。`gm128_preset`は
    全128パッチが`sw_bank=0`を参照しており対象外。
  - 変換を入れる場合に決めること: (1) LFOSの値の決め方(「ビブラートが有効な音色は
    一律LFOS=3相当とみなす」等)、(2) LFO SPEED→Hz と PMD×PMS→セントの実機換算。
    深さは実機ではPMDとPMSの積で決まるため、PMD単独からセントへ線形写像するのは誤り。
- TX81Z実機のTL算出式`V_TL = A_vol + A_alg + A_ol + A_ls + A_kvs + A_ebs`のうち、
  実装済みは`A_ol`(worklog 3.44)・`A_alg`(3.47)・`A_kvs`の分解(3.48)。`A_ls`
  (Level Scaling、ノート番号依存)は受け皿が無く未変換、`A_ebs`(EG bias)も未変換
  (`ops[].EGS`に生値のみ格納)。`A_vol`は実機のマスターボリューム相当のため対象外。
- `fb01`は KVSを持たないため全opで`VTL=80`のまま(モジュレータにもVTLが乗る)。
  FB-01の`VEL_TL`(3bit、op単位)を`VTL`へ換算できれば整理できるが、換算カーブが不明。
- `docs/voice-parameter-reference.md`はFITOM_X側の原本由来だが、こちらで直した節
  (worklog 3.25/3.35/3.51)と「原本由来なので直さない」とした節(3.37/3.45)があり、
  バンクのパスは意図的に原本と変えている(3.35)。どこまでこちらで書き換えてよいかの
  方針が決まっていない。原本がFITOM_X側で削除されたので、この写しを残すか、
  FITOM_X側の文書(`docs/manuals/hwpatch-reference.md`等)への参照に置き換えるかも
  合わせて未決。
- `config_schema/profile.schema.json`の`devices[].engine`の`examples`が
  `["YMEngine", "AYEngine"]`のまま(現行の値は`"engines/YMFMEngine"`等)。FITOM_X側の
  原本のdriftで、写しは直さない方針のため本体側の更新を待つ。
- `CLAUDE.md`3節「値の格納規約」は、FITOM_XがOPLLでもキーオン/キーオフのたびに
  EGT/RRを書き換えるとしているが、FITOM_XのOPLL系は`updateVoice`での静的な変換
  (`SR>0`ならEGT=0・RRレジスタ=`SR>>1`、`SR==0`ならEGT=1・RRレジスタ=`RR`)で、
  動的に書き換えるのはOPL系だけ(FITOM_Xの`docs/design/chip-notes.md`「EGTとRRの
  静的な変換」)。`tools/voice_convert/opll_convert.py`の冒頭コメントと
  `docs/voice-parameter-reference.md`も同じ前提で書かれている。変換規則
  (`apply_carrier_rr_floor()`を含む)への影響は確かめていない。
