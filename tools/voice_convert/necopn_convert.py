#!/usr/bin/env python3
"""
necopn.bin → FITOM_X hwbank.json 変換ツール

フォーマット（N88-BASIC(86)互換、1音色=64バイト、パラメータごとの列方向格納）:
  [0]     FB/ALG   (D5-3=FB, D2-0=ALG)
  [1-4]   AR  (OP1,OP2,OP3,OP4の順。1の補数格納: 実値 = 31 - 生値)
  [5]     オペレータ有効マスク (常時0x0F、未使用)
  [6-9]   DR  (同上、1の補数格納: 実値 = 31 - 生値)
  [10]    LFO波形 (未使用、hwbankに対応フィールドなし)
  [11-14] SR  (同上、1の補数格納: 実値 = 31 - 生値)
  [15]    LFOディレイ (未使用)
  [16-19] RR  (同上、1の補数格納: 実値 = 15 - 生値)
  [20]    LFO速度 (未使用)
  [21-24] SL  (同上、1の補数格納: 実値 = 15 - 生値)
  [25]    LFO PMD (未使用)
  [26-29] TL  (同上、1の補数格納: 実値 = 127 - 生値、拡張なし)
  [30]    LFO AMD (未使用)
  [31-34] KSR (生値のまま、2bit)
  [35]    PMS (チャンネル、生値&0x07)
  [36-39] MUL (生値のまま、4bit)
  [40]    未使用
  [41-44] DT1 (生値のまま、3bit)
  [45]    未使用
  [46-49] AM  (生値!=0の真偽値)
  [50-63] パディング (14バイト、未使用)

各オペレータのパラメータ列はOP1,OP2,OP3,OP4の順で格納されており、これは
N88-BASIC(86)側の格納順(M1,C1,M2,C2)と一致する。FITOM_X側のops[]格納順も
[M1,C1,M2,C2]であるため、並び替えは不要。

このレイアウトは、旧FITOM(dev/fmvoice)のn88tofmb2.pl(N88→FMB2変換)と、
実際に変換済みだったdev/fmvoice/VOICE/OPNA/necopn.fmbをopn2ini.plで
デコードした結果を突き合わせて確認したもの(2026-07-19)。旧necopn_convert.py
は1音色内で「オペレータごとに6バイトずつ」読む行方向レイアウトを仮定して
いたが、実際のnecopn.binは「パラメータごとに4オペレータ分ずつ」読む列方向
レイアウトであり、オフセットが全く異なっていた(単なるAR/DR/SL/SR/RR/TLの
符号反転だけの問題ではなかった)。
"""

import json, argparse
from pathlib import Path

# GM楽器名 (prog 0-127)
GM_NAMES = [
    "Acoustic Grand Piano","Bright Acoustic Piano","Electric Grand Piano",
    "Honky-tonk Piano","Electric Piano 1","Electric Piano 2",
    "Harpsichord","Clavi","Celesta","Glockenspiel","Music Box",
    "Vibraphone","Marimba","Xylophone","Tubular Bells","Dulcimer",
    "Drawbar Organ","Percussive Organ","Rock Organ","Church Organ",
    "Reed Organ","Accordion","Harmonica","Tango Accordion",
    "Acoustic Guitar (nylon)","Acoustic Guitar (steel)",
    "Electric Guitar (jazz)","Electric Guitar (clean)",
    "Electric Guitar (muted)","Overdriven Guitar",
    "Distortion Guitar","Guitar harmonics",
    "Acoustic Bass","Electric Bass (finger)","Electric Bass (pick)",
    "Fretless Bass","Slap Bass 1","Slap Bass 2",
    "Synth Bass 1","Synth Bass 2",
    "Violin","Viola","Cello","Contrabass",
    "Tremolo Strings","Pizzicato Strings","Orchestral Harp","Timpani",
    "String Ensemble 1","String Ensemble 2","SynthStrings 1","SynthStrings 2",
    "Choir Aahs","Voice Oohs","Synth Voice","Orchestra Hit",
    "Trumpet","Trombone","Tuba","Muted Trumpet",
    "French Horn","Brass Section","SynthBrass 1","SynthBrass 2",
    "Soprano Sax","Alto Sax","Tenor Sax","Baritone Sax",
    "Oboe","English Horn","Bassoon","Clarinet",
    "Piccolo","Flute","Recorder","Pan Flute",
    "Blown Bottle","Shakuhachi","Whistle","Ocarina",
    "Lead 1 (square)","Lead 2 (sawtooth)","Lead 3 (calliope)",
    "Lead 4 (chiff)","Lead 5 (charang)","Lead 6 (voice)",
    "Lead 7 (fifths)","Lead 8 (bass + lead)",
    "Pad 1 (new age)","Pad 2 (warm)","Pad 3 (polysynth)",
    "Pad 4 (choir)","Pad 5 (bowed)","Pad 6 (metallic)",
    "Pad 7 (halo)","Pad 8 (sweep)",
    "FX 1 (rain)","FX 2 (soundtrack)","FX 3 (crystal)",
    "FX 4 (atmosphere)","FX 5 (brightness)","FX 6 (goblins)",
    "FX 7 (echoes)","FX 8 (sci-fi)",
    "Sitar","Banjo","Shamisen","Koto","Kalimba",
    "Bag pipe","Fiddle","Shanai",
    "Tinkle Bell","Agogo","Steel Drums","Woodblock",
    "Taiko Drum","Melodic Tom","Synth Drum","Reverse Cymbal",
    "Guitar Fret Noise","Breath Noise","Seashore","Bird Tweet",
    "Telephone Ring","Helicopter","Applause","Gunshot",
]

def parse_voice(data, base):
    """1音色(64バイト)のパラメータをバイト列から解析"""
    fb_alg = data[base + 0]
    fb  = (fb_alg >> 3) & 0x07
    alg =  fb_alg        & 0x07
    pms = data[base + 35] & 0x07

    ops = []
    for i in range(4):
        raw_ar  = data[base + 1  + i]
        raw_dr  = data[base + 6  + i]
        raw_sr  = data[base + 11 + i]
        raw_rr  = data[base + 16 + i]
        raw_sl  = data[base + 21 + i]
        raw_tl  = data[base + 26 + i]
        ksr     = data[base + 31 + i] & 0x03
        mul     = data[base + 36 + i] & 0x0F
        dt1     = data[base + 41 + i] & 0x07
        am_flag = data[base + 46 + i] != 0

        ops.append({
            "AR":  0x1F - (raw_ar & 0x1F),
            "DR":  0x1F - (raw_dr & 0x1F),
            "SR":  0x1F - (raw_sr & 0x1F),
            "RR":  0x0F - (raw_rr & 0x0F),
            "SL":  0x0F - (raw_sl & 0x0F),
            "TL":  0x7F - (raw_tl & 0x7F),
            "KSR": ksr,
            "MUL": mul,
            "DT1": dt1,
            "AM":  1 if am_flag else 0,
        })

    return fb, alg, pms, ops

def convert(src_path, dst_path, bank_no=0, group="OPN"):
    data = Path(src_path).read_bytes()
    assert len(data) == 128 * 64, f"Expected 8192 bytes, got {len(data)}"

    patches = []
    for prog in range(128):
        base = prog * 64
        fb, alg, pms, ops = parse_voice(data, base)

        name = GM_NAMES[prog] if prog < len(GM_NAMES) else f"Program {prog}"

        # FITOM_X HwPatch JSON形式
        # FITOM_X ops[] 格納順: [M1, C1, M2, C2] (necopn.binの格納順そのまま)
        patches.append({
            "prog": prog,
            "name": name,
            "FB":  fb,
            "ALG": alg,
            "AMS": 0,   # necopn.binにチャンネルAMSの格納は無い(常に0)
            "PMS": pms,
            "ops": ops,
        })

    out = {
        "name": "necopn GM Bank",
        "group": group,
        "bank": bank_no,
        "source": "necopn.bin (Windows OPNA driver preset, N88-BASIC(86) format)",
        "patches": patches
    }

    Path(dst_path).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Converted {len(patches)} patches → {dst_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="necopn.bin → FITOM_X hwbank.json")
    parser.add_argument("input",  help="necopn.bin")
    parser.add_argument("output", help="output .hwbank.json")
    parser.add_argument("--bank", type=int, default=0, help="HwBank番号 (default: 0)")
    parser.add_argument("--group", default="OPN", help="チップグループ (default: OPN)")
    args = parser.parse_args()
    convert(args.input, args.output, args.bank, args.group)
