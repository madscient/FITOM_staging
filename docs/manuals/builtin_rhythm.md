# 内蔵リズム音源(CC#0=112)の楽器選択方法

[← バンクマップに戻る](README.md#2-バンクマップcc0--cc32)

## この方式について

CC#0=112は、OPNA(YM2608)またはOPLL(YM2413)チップが内蔵する
固定のドラム音を直接鳴らす特殊なバンクです。CC#32で対象チップを
選び、**Program Change番号(patch_prog)がそのまま楽器(物理
チャンネル)番号として扱われます**。

[ドラムキット一覧](drumkits.md)の「OPNA Built-in set」
「OPLL Built-in set」は、あらかじめGM2ドラムノートに
適切な楽器番号を割り当て済みです。以下は、各チップが
内蔵する楽器と番号の対応です。

## <a id="opna-rhythm"></a>OPNA(YM2608)内蔵リズム — CC#32=17

| Prog(楽器番号) | 楽器 |
|---|---|
| 0 | Bass Drum |
| 1 | Snare Drum |
| 2 | Top Cymbal |
| 3 | Hi-Hat |
| 4 | Tom-tom |
| 5 | Rim Shot |

→ 実際のノート割り当ては[OPNA Built-in set](drumkits.md#prog11-opna-built-in-set)を参照

## <a id="opll-rhythm"></a>OPLL(YM2413)内蔵リズム — CC#32=40

| Prog(楽器番号) | 楽器 |
|---|---|
| 0 | Hi-Hat |
| 1 | Top Cymbal |
| 2 | Tom-tom |
| 3 | Snare Drum |
| 4 | Bass Drum |

→ 実際のノート割り当ては[OPLL Built-in set](drumkits.md#prog12-opll-built-in-set)を参照

> OPLLはHi-Hat/Snare Drumが同じ発音レジスタを共有し、
> Top Cymbal/Tom-tomも同じ発音レジスタを共有します。
> そのため、これらを同時に異なる音程で鳴らそうとすると、
> 後から発音した方の音程が両方に適用されます。

## OPL内蔵疑似リズム(CC#0=35)との違い

CC#0=35(OPL_RHY)は、上記のCC#0=112とは別の仕組みです。
こちらは通常の音色データ(HwPatch)を持つため、1つの楽器に
対して複数の音色バリエーション(例: 通常のTomとピッチLFO付き
Tom)を用意できます。楽器の判別には`Prog`とは別の内部識別子
が使われるため、`Prog`は単純に「その楽器の何番目の音色か」
を表す通し番号になります。
詳細は[OPL_RHY音色一覧](patches/opl_rhy.md)を参照してください。
