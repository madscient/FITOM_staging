# OPLL (CC#0=40) 音色一覧

OPLL/OPLLX/OPLLP/VRC7系 2オペレータFM音源

[← バンクマップに戻る](../README.md#2-バンクマップcc0--cc32)

## <a id="cc320"></a>CC#32=0: OPLL Built-In

チップに内蔵されたROM音色を直接指定します。バンクファイルは
存在せず、Program Change番号から機械的にチップ種別と音色が
決まります。

```
Program Change番号の内訳:
  上位3bit(Prog >> 4): チップ種別 (0=OPLL, 1=OPLLX, 2=OPLLP, 3=VRC7)
  下位4bit(Prog & 0xF): ROM音色番号 (0=無音, 1-15=音色)
```

| Prog | チップ種別 | 音色番号 | 名称 |
|---|---|---|---|
| 0 | OPLL | 0 | (無音) |
| 1 | OPLL | 1 | Violin |
| 2 | OPLL | 2 | Guitar |
| 3 | OPLL | 3 | Piano |
| 4 | OPLL | 4 | Flute |
| 5 | OPLL | 5 | Clarinet |
| 6 | OPLL | 6 | Oboe |
| 7 | OPLL | 7 | Trumpet |
| 8 | OPLL | 8 | Organ |
| 9 | OPLL | 9 | Horn |
| 10 | OPLL | 10 | Synthesizer |
| 11 | OPLL | 11 | Harpsichord |
| 12 | OPLL | 12 | Vibraphone |
| 13 | OPLL | 13 | Synthesizer Bass |
| 14 | OPLL | 14 | Acoustic Bass |
| 15 | OPLL | 15 | Electric Guitar |
| 16 | OPLLX | 0 | (無音) |
| 17 | OPLLX | 1 | Strings |
| 18 | OPLLX | 2 | Guitar |
| 19 | OPLLX | 3 | Electric Guitar |
| 20 | OPLLX | 4 | Electric Piano 2 |
| 21 | OPLLX | 5 | Flute |
| 22 | OPLLX | 6 | Marimba |
| 23 | OPLLX | 7 | Trumpet |
| 24 | OPLLX | 8 | Harmonica |
| 25 | OPLLX | 9 | Tuba |
| 26 | OPLLX | 10 | Synth Brass 2 |
| 27 | OPLLX | 11 | Short Saw |
| 28 | OPLLX | 12 | Vibraphone |
| 29 | OPLLX | 13 | Electric Guitar 2 |
| 30 | OPLLX | 14 | Synth Bass 2 |
| 31 | OPLLX | 15 | Sitar |
| 32 | OPLLP | 0 | (無音) |
| 33 | OPLLP | 1 | Clarinet |
| 34 | OPLLP | 2 | Synth Bass |
| 35 | OPLLP | 3 | Piano |
| 36 | OPLLP | 4 | Flute |
| 37 | OPLLP | 5 | Square Wave |
| 38 | OPLLP | 6 | Space Oboe |
| 39 | OPLLP | 7 | Trumpet |
| 40 | OPLLP | 8 | Wow Bell |
| 41 | OPLLP | 9 | Electric Guitar |
| 42 | OPLLP | 10 | Vibes |
| 43 | OPLLP | 11 | Bass |
| 44 | OPLLP | 12 | Vibraphone |
| 45 | OPLLP | 13 | Vibrato Bell |
| 46 | OPLLP | 14 | Click Sine |
| 47 | OPLLP | 15 | Noise and Tone |
| 48 | VRC7 | 0 | (無音) |
| 49 | VRC7 | 1 | Buzzy Bell |
| 50 | VRC7 | 2 | Guitar |
| 51 | VRC7 | 3 | Wurly |
| 52 | VRC7 | 4 | Flute |
| 53 | VRC7 | 5 | Clarinet |
| 54 | VRC7 | 6 | Synth |
| 55 | VRC7 | 7 | Trumpet |
| 56 | VRC7 | 8 | Organ |
| 57 | VRC7 | 9 | Bells |
| 58 | VRC7 | 10 | Vibes |
| 59 | VRC7 | 11 | Vibraphone |
| 60 | VRC7 | 12 | Tutti |
| 61 | VRC7 | 13 | Fretless |
| 62 | VRC7 | 14 | Synth Bass |
| 63 | VRC7 | 15 | Sweep |

> ROM音色はチップごとに実データが異なるため、指定した
> チップ種別が接続されていない場合は無音になります(自動的に
> 別チップ種別へ切り替わることはありません)。

## <a id="cc321"></a>CC#32=1: MSX-AUDIO + OPLL(x) ROM Preset

| Prog | 名称 |
|---|---|
| 0 | Piano 1 |
| 1 | Piano 2 |
| 2 | Violin |
| 3 | Flute |
| 4 | Clarinet |
| 5 | Oboe |
| 6 | Trumpet |
| 7 | PipeOrgn |
| 8 | Xylophon |
| 9 | Organ |
| 10 | Guitar |
| 11 | Santool |
| 12 | Elecpian |
| 13 | Clavicod |
| 14 | Harpsicd |
| 15 | Harpscd2 |
| 16 | Vibraphn |
| 17 | Koto |
| 18 | Taiko |
| 19 | Engine |
| 20 | UFO |
| 21 | SynBell |
| 22 | Chime |
| 23 | SynBass |
| 24 | Synthsiz |
| 25 | SynPercu |
| 26 | SynRhyth |
| 27 | HarmDrum |
| 28 | Cowbell |
| 29 | ClseHiht |
| 30 | SnareDrm |
| 31 | BassDrum |
| 32 | Piano 3 |
| 33 | Elecpia2 |
| 34 | Santool2 |
| 35 | Brass |
| 36 | Flute 2 |
| 37 | Clavicd2 |
| 38 | Clavicd3 |
| 39 | Koto 2 |
| 40 | PipeOrg2 |
| 41 | PohdsPLA |
| 42 | RohdsPRA |
| 43 | Orch L |
| 44 | Orch R |
| 45 | SynViol |
| 46 | SynOrgan |
| 47 | SynBrass |
| 48 | Tube |
| 49 | Shamisen |
| 50 | Magical |
| 51 | Huwawa |
| 52 | WnderFlt |
| 53 | Hardrock |
| 54 | Machine |
| 55 | MachineV |
| 56 | Comic |
| 57 | SE_Comic |
| 58 | SE_Laser |
| 59 | SE_Noise |
| 60 | SE_Star |
| 61 | SE_Star2 |
| 62 | Engine 2 |
| 63 | Silence |
| 64 | Violin [OPLL(YM2413)] |
| 65 | Guitar [OPLL(YM2413)] |
| 66 | Piano [OPLL(YM2413)] |
| 67 | Flute [OPLL(YM2413)] |
| 68 | Clarinet [OPLL(YM2413)] |
| 69 | Oboe [OPLL(YM2413)] |
| 70 | Trumpet [OPLL(YM2413)] |
| 71 | Organ [OPLL(YM2413)] |
| 72 | Horn [OPLL(YM2413)] |
| 73 | Synthesizer [OPLL(YM2413)] |
| 74 | Harpsichord [OPLL(YM2413)] |
| 75 | Vibraphone [OPLL(YM2413)] |
| 76 | Synthesizer Bass [OPLL(YM2413)] |
| 77 | Acoustic Bass [OPLL(YM2413)] |
| 78 | Electric Guitar [OPLL(YM2413)] |
| 79 | Strings [OPLL-X(YM2423)] |
| 80 | Guitar [OPLL-X(YM2423)] |
| 81 | Electric Guitar [OPLL-X(YM2423)] |
| 82 | Electric Piano 2 [OPLL-X(YM2423)] |
| 83 | Flute [OPLL-X(YM2423)] |
| 84 | Marimba [OPLL-X(YM2423)] |
| 85 | Trumpet [OPLL-X(YM2423)] |
| 86 | Harmonica [OPLL-X(YM2423)] |
| 87 | Tuba [OPLL-X(YM2423)] |
| 88 | Synth Brass 2 [OPLL-X(YM2423)] |
| 89 | Short Saw [OPLL-X(YM2423)] |
| 90 | Vibraphone [OPLL-X(YM2423)] |
| 91 | Electric Guitar 2 [OPLL-X(YM2423)] |
| 92 | Synth Bass 2 [OPLL-X(YM2423)] |
| 93 | Sitar [OPLL-X(YM2423)] |
| 94 | Clarinet [OPLL-P(YMF281)] |
| 95 | Synth Bass [OPLL-P(YMF281)] |
| 96 | Piano [OPLL-P(YMF281)] |
| 97 | Flute [OPLL-P(YMF281)] |
| 98 | Square Wave [OPLL-P(YMF281)] |
| 99 | Space Oboe [OPLL-P(YMF281)] |
| 100 | Trumpet [OPLL-P(YMF281)] |
| 101 | Wow Bell [OPLL-P(YMF281)] |
| 102 | Electric Guitar [OPLL-P(YMF281)] |
| 103 | Vibes [OPLL-P(YMF281)] |
| 104 | Bass [OPLL-P(YMF281)] |
| 105 | Vibraphone [OPLL-P(YMF281)] |
| 106 | Vibrato Bell [OPLL-P(YMF281)] |
| 107 | Click Sine [OPLL-P(YMF281)] |
| 108 | Noise and Tone [OPLL-P(YMF281)] |
| 109 | Buzzy Bell [VRC7(FS1001)] |
| 110 | Guitar [VRC7(FS1001)] |
| 111 | Wurly [VRC7(FS1001)] |
| 112 | Flute [VRC7(FS1001)] |
| 113 | Clarinet [VRC7(FS1001)] |
| 114 | Synth [VRC7(FS1001)] |
| 115 | Trumpet [VRC7(FS1001)] |
| 116 | Organ [VRC7(FS1001)] |
| 117 | Bells [VRC7(FS1001)] |
| 118 | Vibes [VRC7(FS1001)] |
| 119 | Vibraphone [VRC7(FS1001)] |
| 120 | Tutti [VRC7(FS1001)] |
| 121 | Fretless [VRC7(FS1001)] |
| 122 | Synth Bass [VRC7(FS1001)] |
| 123 | Sweep [VRC7(FS1001)] |

## <a id="cc322"></a>CC#32=2: OPLL Presets (PSS-140 + SHS-10)

| Prog | 名称 |
|---|---|
| 0 | Accordion 1 |
| 1 | Accordion 2 |
| 2 | Alpenhorn |
| 3 | Alto Sax |
| 4 | Bagpipe |
| 5 | Banjo |
| 6 | Bar Chimes |
| 7 | Bass Clarinet |
| 8 | Bassoon |
| 9 | Boom Piano |
| 10 | Bowed bass |
| 11 | Brass & Marimba |
| 12 | Cello |
| 13 | Chime & Organ |
| 14 | Chimes |
| 15 | Clarinet |
| 16 | Classic Guitar |
| 17 | Clavi 1 |
| 18 | Clavi 2 |
| 19 | Drip |
| 20 | Electric Bass |
| 21 | Electric Piano 1 |
| 22 | Electric Piano 2 |
| 23 | Electric Trumpet |
| 24 | Electron Organ |
| 25 | Fantastic Piano |
| 26 | Fireworks |
| 27 | Flute |
| 28 | Fork Guitar 1 |
| 29 | Fork Guitar 2 |
| 30 | Funky Marimba |
| 31 | Glass Celesta |
| 32 | Glockenspiel |
| 33 | Gurgle |
| 34 | Hand Bell |
| 35 | Handsaw |
| 36 | Harmonica |
| 37 | Harp |
| 38 | Harpsichord 1 |
| 39 | Harpsichord 2 |
| 40 | Harpsichord 3 |
| 41 | Hawaiian Guitar |
| 42 | Honky-Tonk Piano 1 |
| 43 | Honky-Tonk Piano 2 |
| 44 | Horn |
| 45 | Human Voice 1 |
| 46 | Human Voice 2 |
| 47 | Human Voice 3 |
| 48 | Ice Block |
| 49 | Jamisen |
| 50 | Jazz Guitar |
| 51 | Jazz Organ |
| 52 | Jug |
| 53 | Koto |
| 54 | Leaf Spring |
| 55 | Marimba |
| 56 | Metallic Synth |
| 57 | Music Box |
| 58 | Mute Bass |
| 59 | Mute Trumpet |
| 60 | Oboe |
| 61 | Panflute |
| 62 | Piano 1 |
| 63 | Piano 2 |
| 64 | Piccolo |
| 65 | Picked Bass |
| 66 | Pipe Organ 1 |
| 67 | Pipe Organ 2 |
| 68 | Popcorn |
| 69 | Reed Organ |
| 70 | Reverse |
| 71 | Rock Guitar 1 |
| 72 | Rock Guitar 2 |
| 73 | Shamisen |
| 74 | Sine Wave |
| 75 | Slap Bass |
| 76 | Small Church |
| 77 | Soft Trombone |
| 78 | Soprano Sax |
| 79 | Steel Drum 1 |
| 80 | Steel Drum 2 |
| 81 | Street Organ |
| 82 | Strings |
| 83 | Synth Bass |
| 84 | Synth Brass |
| 85 | Tenor Sax |
| 86 | Toy Piano |
| 87 | Transistor Organ |
| 88 | Tremolo Organ |
| 89 | Trombone |
| 90 | Trumpet |
| 91 | Tuba |
| 92 | Ukulele |
| 93 | Vibraphone |
| 94 | Violin 1 |
| 95 | Violin 2 |
| 96 | Whistle |
| 97 | Wide Bell |
| 98 | Wood Bass 1 |
| 99 | Wood Bass 2 |
| 100 | Synthesizer |
| 101 | Jazz Organ |
| 102 | Pipe Organ |
| 103 | Piano |
| 104 | Harpsichord |
| 105 | Electric Piano |
| 106 | Celesta |
| 107 | Vibraphone |
| 108 | Marimba |
| 109 | Steel Drum |
| 110 | Violin |
| 111 | Cello |
| 112 | Jazz Guitar |
| 113 | Rock Guitar |
| 114 | Wood Bass |
| 115 | Trumpet |
| 116 | Trombone |
| 117 | Horn |
| 118 | Saxophone |
| 119 | Clarinet |
| 120 | Flute |
| 121 | Oboe |
| 122 | Harmonica |
| 123 | Whistle |
| 124 | Music Box |

## <a id="cc323"></a>CC#32=3: Built-In with performance(ユーザー設定用)

上記「OPLL Built-In」(CC#32=0)のROM音色に対して、ベロシティ感度や
ビブラートなどのパフォーマンスパッチ(SwPatch)を個別に割り当てる
ための設定領域です。工場出荷時点では空の状態(未割り当て)で
提供されています。

割り当てを追加すると、ROM音色そのものを選択したとき
(CC#0=40, CC#32=0)に、指定したパフォーマンスパッチが自動的に
適用されるようになります。
