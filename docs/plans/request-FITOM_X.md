# FITOM_Xへの依頼: FM系の音程をプラグインが報告するクロックから計算する

FITOM_stagingから、FITOM_Xで行ってほしい作業。ユーザーの判断でFITOM_Xのバグとして扱う。
作業が終わったら、FITOM_stagingの`docs/STATUS.md` 4節の該当項目と、この依頼文を消してもらう
(FITOM_staging側で消す)。

ここに書いたコードの場所と挙動は、FITOM_X `b7c1e4c`を読んだ時点のもの。着手する前に確かめること。

## 何が起きているか

FITOM_Xのチップドライバのうち、PSG系・DSG・SAA1099・ADPCM/PCMは、プラグインが報告する
クロック(`IPort::getClock()`)から音程・再生レートを計算する(`DeviceFactory.cpp`の
`psgMasterClock()`、`ADPCM_new.cpp` L930付近)。

FM系のドライバは、固定のマスタークロックでF-Number/KCを計算していて、プラグインのクロックを
読まない(**読解のみ**):

| ドライバ | 固定値 | 場所 |
|---|---|---|
| `COPL`(OPL/OPL2/Y8950、OPL2EXを含む) | 3,579,545Hz | `OPL_new.cpp` `COPL::kMasterClock`(L33)。L781の`COPLRhythm`(内蔵リズム)でも使用 |
| `COPL3` | 14,318,180Hz | `OPL_new.cpp` L357 |
| `COPLL`系 | 3,579,545Hz | `OPLL_new.cpp` `kOpllMasterClock`(L25)。L38・L385で使用 |
| `COPN` | 3,993,600Hz | `OPN_new.cpp` L26の既定引数 |
| `COPNA`/`COPNB`/OPN2系 | 8,000,000Hz | `OPN2_new.cpp` L95の既定引数、L161・L198 |
| `COPM`/OPZ | 3,579,545Hz前提 | `OPM_new.cpp` L26(独自計算)、L310-314のKC対応 |

エミュレーター(FitomEmuIF + 各エンジン)は、サブプロファイルの`chips[].clock`のクロックで
チップを動かす。値が上の固定値と違うと、その比の分だけ音程がずれるはず(**推測**:
FITOM_X内でクロックの違いを補正している箇所は見つからなかった。鳴らして確かめてはいない)。

`ADPCM_new.cpp` L930のコメントは「FMチップドライバと同様、`port->getClock()`をmasterとして使う」
としているが、FM系ドライバは上のとおり使っていない。

## FITOM_stagingで影響を受ける構成

| プロファイル | チップ | プロファイルのクロック | 固定値 | ずれ(計算) |
|---|---|---|---|---|
| `emu_opn`/`emu_opn_stereo`/`emu_fmgen_opn`/`unified_preset`/`fmall` | OPN2/OPNA/OPNB/OPNBB | 7,159,090Hz | 8,000,000Hz | 約190セント低い |
| `emu_pc88`/`emu_pc98` | OPNA | 7,987,200Hz | 8,000,000Hz | 約3セント低い |

OPM/OPZ/OPL/OPL2/Y8950/OPL3/OPLL系/OPLLEX/OPL2EXは、今の構成では固定値と一致している。
OPL4のFM部は、`COPL3`の固定値とエンジン側の分周の関係が分からず、ずれるかどうか不明。

## してほしいこと

- FM系ドライバでも、F-Number/KCの計算にプラグインが報告するクロックを使う。報告されない
  (0を返す)ときだけ、今の固定値を使う(PSG系の`psgMasterClock()`と同じ形)。
- `COPLL`/`COPL`のコメントにある「`sampleRate`をfnumMasterに使うとFnumberが常に上限へ
  クランプされる」という注意は、`sampleRate`ではなくクロックを使う今回の変更とは別の話。
  取り違えないこと。
- OPL4(YMF278B)のFM部は、マスタークロックとFM部の分周の関係を確かめてから決める。
- 直したあと、FITOM_staging側で`emu_opn`のOPNA(7,159,090Hz)のA4が440Hzで鳴るかを、
  ユーザーが聴いて確かめる。

## 参考

- FITOM_staging `CLAUDE.md` 3節「エンジンとクロック」(この件を今の挙動として書いてある)
- FITOM_staging `docs/worklog/2026-10.md` 3.84
