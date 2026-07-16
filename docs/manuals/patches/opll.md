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
| 64 | [OPLL] Violin |
| 65 | [OPLL] Guitar |
| 66 | [OPLL] Piano |
| 67 | [OPLL] Flute |
| 68 | [OPLL] Clarinet |
| 69 | [OPLL] Oboe |
| 70 | [OPLL] Trumpet |
| 71 | [OPLL] Organ |
| 72 | [OPLL] Horn |
| 73 | [OPLL] Synthesizer |
| 74 | [OPLL] Harpsichord |
| 75 | [OPLL] Vibraphone |
| 76 | [OPLL] Synthesizer Bass |
| 77 | [OPLL] Acoustic Bass |
| 78 | [OPLL] Electric Guitar |
| 79 | [OPLLX] Strings |
| 80 | [OPLLX] Guitar |
| 81 | [OPLLX] Electric Guitar |
| 82 | [OPLLX] Electric Piano 2 |
| 83 | [OPLLX] Flute |
| 84 | [OPLLX] Marimba |
| 85 | [OPLLX] Trumpet |
| 86 | [OPLLX] Harmonica |
| 87 | [OPLLX] Tuba |
| 88 | [OPLLX] Synth Brass 2 |
| 89 | [OPLLX] Short Saw |
| 90 | [OPLLX] Vibraphone |
| 91 | [OPLLX] Electric Guitar 2 |
| 92 | [OPLLX] Synth Bass 2 |
| 93 | [OPLLX] Sitar |
| 94 | [OPLLP] Clarinet |
| 95 | [OPLLP] Synth Bass |
| 96 | [OPLLP] Piano |
| 97 | [OPLLP] Flute |
| 98 | [OPLLP] Square Wave |
| 99 | [OPLLP] Space Oboe |
| 100 | [OPLLP] Trumpet |
| 101 | [OPLLP] Wow Bell |
| 102 | [OPLLP] Electric Guitar |
| 103 | [OPLLP] Vibes |
| 104 | [OPLLP] Bass |
| 105 | [OPLLP] Vibraphone |
| 106 | [OPLLP] Vibrato Bell |
| 107 | [OPLLP] Click Sine |
| 108 | [OPLLP] Noise and Tone |
| 109 | [VRC7] Buzzy Bell |
| 110 | [VRC7] Guitar |
| 111 | [VRC7] Wurly |
| 112 | [VRC7] Flute |
| 113 | [VRC7] Clarinet |
| 114 | [VRC7] Synth |
| 115 | [VRC7] Trumpet |
| 116 | [VRC7] Organ |
| 117 | [VRC7] Bells |
| 118 | [VRC7] Vibes |
| 119 | [VRC7] Vibraphone |
| 120 | [VRC7] Tutti |
| 121 | [VRC7] Fretless |
| 122 | [VRC7] Synth Bass |
| 123 | [VRC7] Sweep |

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

## <a id="cc324"></a>CC#32=4: MA-2 Preset2OP (OPLLとして参照)

`Preset2OP.hwbank.json`(元はOPL2用GM128バンク)を、OPLL用として
直接参照したものです。GM128配列の音色が一通り揃っています。
`GM Standard Native OPLL`(通常モード、CC#0=0, CC#32=?)から
組み立てる際のフォールバック候補としても使われています。

| Prog | 名称 |
|---|---|
| 0 | GrandPno |
| 1 | BritePno |
| 2 | E.GrandP |
| 3 | HnkyTonk |
| 4 | E.Piano1 |
| 5 | E.Piano2 |
| 6 | Harpsi |
| 7 | Clavi |
| 8 | Celesta |
| 9 | Glocken |
| 10 | MusicBox |
| 11 | Vibes |
| 12 | Marimba |
| 13 | Xylophon |
| 14 | TubulBel |
| 15 | Dulcimer |
| 16 | DrawOrgn |
| 17 | PercOrgn |
| 18 | RockOrgn |
| 19 | ChrchOrg |
| 20 | ReedOrgn |
| 21 | Acordion |
| 22 | Harmnica |
| 23 | TangoAcd |
| 24 | NylonGtr |
| 25 | SteelGtr |
| 26 | JazzGtr |
| 27 | CleanGtr |
| 28 | Mute.Gtr |
| 29 | Ovrdrive |
| 30 | Dist.Gtr |
| 31 | GtrHarmo |
| 32 | Aco.Bass |
| 33 | FngrBass |
| 34 | PickBass |
| 35 | Fretless |
| 36 | SlapBas1 |
| 37 | SlapBas2 |
| 38 | SynBass1 |
| 39 | SynBass2 |
| 40 | Violin |
| 41 | Viola |
| 42 | Cello |
| 43 | Contrabs |
| 44 | Trem.Str |
| 45 | Pizz.Str |
| 46 | Harp |
| 47 | Timpani |
| 48 | Strings1 |
| 49 | Strings2 |
| 50 | Syn.Str1 |
| 51 | Syn.Str2 |
| 52 | ChoirAah |
| 53 | VoiceOoh |
| 54 | SynVoice |
| 55 | Orch.Hit |
| 56 | Trumpet |
| 57 | Trombone |
| 58 | Tuba |
| 59 | Mute.Trp |
| 60 | Fr.Horn |
| 61 | BrasSect |
| 62 | SynBras1 |
| 63 | SynBras2 |
| 64 | SprnoSax |
| 65 | AltoSax |
| 66 | TenorSax |
| 67 | Bari.Sax |
| 68 | Oboe |
| 69 | Eng.Horn |
| 70 | Bassoon |
| 71 | Clarinet |
| 72 | Piccolo |
| 73 | Flute |
| 74 | Recorder |
| 75 | PanFlute |
| 76 | Bottle |
| 77 | Shakhchi |
| 78 | Whistle |
| 79 | Ocarina |
| 80 | SquareLd |
| 81 | Saw.Lead |
| 82 | CaliopLd |
| 83 | ChiffLd |
| 84 | CharanLd |
| 85 | VoiceLd |
| 86 | FifthLd |
| 87 | Bass&Ld |
| 88 | NewAgePd |
| 89 | WarmPad |
| 90 | PolySyPd |
| 91 | ChoirPad |
| 92 | BowedPad |
| 93 | MetalPad |
| 94 | HaloPad |
| 95 | SweepPad |
| 96 | Rain |
| 97 | SoundTrk |
| 98 | Crystal |
| 99 | Atmosphr |
| 100 | Bright |
| 101 | Goblins |
| 102 | Echoes |
| 103 | Sci-Fi |
| 104 | Sitar |
| 105 | Banjo |
| 106 | Shamisen |
| 107 | Koto |
| 108 | Kalimba |
| 109 | Bagpipe |
| 110 | Fiddle |
| 111 | Shanai |
| 112 | TnklBell |
| 113 | Agogo |
| 114 | SteelDrm |
| 115 | WoodBlok |
| 116 | TaikoDrm |
| 117 | MelodTom |
| 118 | Syn.Drum |
| 119 | RevCymbl |
| 120 | FretNoiz |
| 121 | BrthNoiz |
| 122 | Seashore |
| 123 | Tweet |
| 124 | Telphone |
| 125 | Helicptr |
| 126 | Applause |
| 127 | Gunshot |
