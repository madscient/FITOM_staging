# 内蔵リズム音源(CC#0=112)の楽器選択方法

[← バンクマップに戻る](README.md#2-バンクマップcc0--cc32)

## この方式について

CC#0=112は、OPNA(YM2608)またはOPLL(YM2413)チップが内蔵する
固定のドラム音を直接鳴らす特殊なバンクです。CC#32で対象チップを
選びますが、**楽器そのものはProgram Changeでは選択できません**。
楽器は「固定チャンネル(fixed channel)」という内部的な仕組みで
決まっており、この値はMIDIメッセージとして直接送ることが
できません。

そのため、CC#0=112は単独のパートで使うのではなく、
[ドラムキット一覧](drumkits.md)の
「OPNA Built-in set」「OPLL Built-in set」を経由して使います。
ドラムキット側が、MIDIノート番号ごとに適切な固定チャンネルを
自動的に割り当てます。

以下は、各チップが内蔵する楽器と固定チャンネル番号の対応です。
(この番号を直接指定する操作画面はありませんが、
ドラムキットがどの楽器を鳴らしているかを把握する参考になります)

## <a id="opna-rhythm"></a>OPNA(YM2608)内蔵リズム — CC#32=17

| 固定チャンネル | 楽器 |
|---|---|
| 0 | Bass Drum |
| 1 | Snare Drum |
| 2 | Top Cymbal |
| 3 | Hi-Hat |
| 4 | Tom-tom |
| 5 | Rim Shot |

→ 実際のノート割り当ては[OPNA Built-in set](drumkits.md#prog11-opna-built-in-set)を参照

## <a id="opll-rhythm"></a>OPLL(YM2413)内蔵リズム — CC#32=40

| 固定チャンネル | 楽器 |
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
