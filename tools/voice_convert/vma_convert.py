#!/usr/bin/env python3
"""
MA-2 VMA (FM) → FITOM_X hwbank.json 変換ツール

対応: FM  マジックを持つ VMA ファイル (2OP/4OP, メロディ/ドラム)
非対応: ADP  マジック (ADPCM) → スキップ

VMA フォーマット:
  byte0-3 : "FM  " マジック
  byte4-5 : 不明
  byte6-7 : データ部サイズ big-endian (N*42)
  byte8 ～ byte8+N*16-1    : 名前部 (各16バイト)
  byte8+N*16 ～             : パラメータ部 (各26バイト)
  N = 128 (メロディ) or 79 (ドラム, MIDI note 27-105に対応)

パラメータ26バイト:
  byte0   : 不明
  byte1   : OPタイプ識別子 (実測値は0/1/12など機種依存、4OP判定には使わず
            要素数固定 or 呼び出し側指定で判断する)
  byte2   : プログラム番号
  byte3   : LFO[7] | FB[5:3] | ALG[1:0]  (MA-2共通パラメータ)
  byte4   : 不明 (0x01固定)
  byte5-9 : OP1 (5バイト, MA-2形式)
  byte10-14: OP2 (5バイト)
  byte15-19: OP3 (5バイト, 2OPでは0固定)
  byte20-24: OP4 (5バイト, 2OPでは0固定)
  byte25  : パディング

MA-2 OP 5バイト:
  byte0: MULT[7:4] | VIB[3] | EGT[2] | SUS[1] | KSR[0]
  byte1: RR[7:4]   | DR[3:0]
  byte2: AR[7:4]   | SL[3:0]
  byte3: TL[7:2]   | KSL[1:0]
  byte4: DVB[7:6] | DAM[5:4] | AM[3] | WS[2:0]

FITOM_X hwbank.schema.json (フラット構造)へのマッピング:
  MULT→MUL, VIB→VIB, EGT→EGT, KSR→KSR, SL→SL, KSL→KSL, AM→AM, WS→WS
  は直接対応。
  AR/DR/TLは実機レジスタ値(4bit/4bit/6bit)をそのまま格納すると、FITOM_X
  ランタイム側の読み出し(OPL_new.cpp/OPLL_new.cpp ar4()/tl6()、格納値を
  >>1して5bit/5bit/7bit相当の「上位ビット表現」から実際のレジスタ幅を
  切り出す設計)によって値が半分になってしまうため、変換時に<<1して格納
  する(2026年7月18日修正。それ以前の変換はこの<<1が抜けており、生成済み
  hwbank.jsonは別途一括修正済み。docs/CLAUDE.md 3.17参照)。
  SUS(Sustain)/DVB(Delayed Vibrato)/DAM(Delayed AM)/LFOは対応フィールドが
  存在しないため破棄する。
  EGT[2]/RR[7:4]は実機OPLレジスタと極性が逆(2026年7月19日修正、
  parse_ma2_op()参照)のため、そのままEGT→EGT/RR→RRへは対応させない。
  変換元のRRレジスタが0の場合、キャリアオペレータで`SR=0`かつ`RR=0`
  (実機で事実上消音しない状態)になることがあるため、キャリアに限り
  RRへ最小値を補う(2026年7月20日追加、apply_carrier_rr_floor()参照。
  モジュレータ側は音声出力に寄与しないため対象外)。
"""

import json, struct, sys, argparse
from pathlib import Path

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

MIN_CARRIER_RR = 1  # SR=0かつRR=0(実機で事実上消音しない)になるキャリアに適用する最小値

def carrier_flags(op_count, alg):
    """ops[]の各要素が実際に音声出力に寄与する(キャリアである)かを判定。

    hw.ALG: bit0=CON1(前半ペア接続)、bit1=CON2(後半ペア接続、4OPのみ)、
    bit2=ConnectionSEL(4OP結合、4OPのみ)。CON=0はFM(直列、後段の
    オペレータのみキャリア)、CON=1はAM(並列、両方キャリア)。
    """
    if op_count == 2:
        con = alg & 1
        return [False, True] if con == 0 else [True, True]
    con1 = alg & 1
    con2 = (alg >> 1) & 1
    connsel = (alg >> 2) & 1
    front = [False, True] if con1 == 0 else [True, True]
    rear  = [False, True] if con2 == 0 else [True, True]
    if connsel == 0:
        return front + [False, False]
    return front + rear

def apply_carrier_rr_floor(ops, alg):
    """キャリアオペレータのRRが0(実機で事実上消音しない)になっている
    場合、RR に最小値を補う。

    変換元(MA-2/実機ダンプ等)のRRレジスタ自体が0の場合にこの状態が
    発生する。FITOM_Xはキーオフ時に`SR`の値に関わらず常に`RR`をRR
    レジスタへ書き込むため、`SR`が非ゼロでもRR=0は消音しないバグになる
    (2026年7月20日、`SR`分岐を撤廃。旧実装は`SR==0`の場合のみ対象と
    誤解していた)。モジュレータ側は音声出力に寄与しないため実害が無く、
    変換元の値をそのまま保持する(Preset4OP.vma/GMmapFM4op.vmaの一部
    音色でキャリア側がこの状態になり、キーオフで消音しないバグが見つ
    かったため対応。docs/CLAUDE.md 3.24参照)。
    """
    for op, is_carrier in zip(ops, carrier_flags(len(ops), alg)):
        if is_carrier and op.get("AR", 0) > 0 and op["RR"] == 0:
            op["RR"] = MIN_CARRIER_RR

def parse_ma2_op(b5):
    """MA-2形式5byte 1オペレータ → hwbank.schema.json準拠フラットop

    MA-2形式のEGTビット(b5[0]bit2)は実機OPLレジスタのEGTビットとは
    極性が逆(2026年7月19日、実データとの聴感比較により判明。ピアノ等の
    減衰音がSR=0(サステイン)になってしまうバグがあった)。
    MA-2側のEGTビット/RRレジスタ(b5[1]上位4bit)をFITOMのSR/RRへ
    変換元EGT=0の場合: 変換先SR=0, 変換先RR=変換元RR
    変換元EGT=1の場合: 変換先SR=変換元RR, 変換先RR=変換元RR
    SRのみ、AR/DR/TLと同じ4bit→5bit「上位ビット表現」で<<1して格納する
    (OPL_new.cpp ar4()側で>>1されるため。RRは直接4bit値のまま)。
    """
    egt_bit = (b5[0] >> 2) & 1
    rr_reg  = (b5[1] >> 4) & 0xF
    sr = (rr_reg << 1) if egt_bit == 1 else 0
    rr = rr_reg
    return {
        "MUL":  (b5[0] >> 4) & 0xF,
        "VIB":  (b5[0] >> 3) & 1,
        "EGT":  0,   # OPL系では無関係、常に0
        "KSR":   b5[0] & 1,
        "SR":    sr,
        "RR":    rr,
        # AR/DR/TLはFITOM_X側で読み出し時に>>1されるため(OPL_new.cpp ar4()/tl6())、
        # 実機レジスタ値(4bit/4bit/6bit)を<<1して格納する(上位ビット表現)。
        "DR":   (b5[1] & 0xF) << 1,
        "AR":  ((b5[2] >> 4) & 0xF) << 1,
        "SL":    b5[2] & 0xF,
        "TL":  ((b5[3] >> 2) & 0x3F) << 1,
        "KSL":   b5[3] & 3,
        "AM":    (b5[4] >> 3) & 1,
        "WS":     b5[4] & 7,
        # SUS(b5[0]bit1)/DVB(b5[4]bit7-6)/DAM(b5[4]bit5-4)は対応フィールドなし、破棄
        # (2026年7月19日、AM/WSのビット位置を実データ解析に基づく一次資料
        # (https://pcm1723.hateblo.jp/entry/20080214/1202996791 のMA-2
        # Operatorバイト4テーブル: DVB[7:6]|DAM[5:4]|AM[3]|WS[2:0])に修正。
        # 旧実装(AM=bit5,WS=bits4-2)には根拠となる記録が無く、単純な
        # ビット位置ミスと判断)
    }

def convert_vma(src_path, dst_path, force_2op=False, bank_name=None):
    data = Path(src_path).read_bytes()

    magic = data[:4]
    if magic != b'FM  ':
        print(f"SKIP {src_path}: magic={magic} (非FMファイル)")
        return False

    data_size = struct.unpack_from('>H', data, 6)[0]
    N = data_size // 42
    is_drum = (N == 79)

    param_base = 8 + N * 16
    # OPタイプ判定バイトは機種依存で不定値(0/1/12等)を取るため、
    # force_2opオプション優先。未指定時はALG/FB値レンジから推定する
    # (2OPは通常ALG 0-1・FB 0-7に収まる)。
    is_4op = False
    if not force_2op:
        sample_off = param_base + 1
        is_4op = (len(data) > sample_off and data[sample_off] == 1)

    group = "OPL3" if is_4op else "OPL3_2"

    patches = []
    for i in range(N):
        name_off = 8 + i * 16
        raw_name = data[name_off:name_off+16].rstrip(b'\x00').decode('ascii', errors='replace')

        off   = param_base + i * 26
        chunk = data[off:off+26]

        prog  = chunk[2]
        byte3 = chunk[3]
        fb    = (byte3 >> 3) & 7
        # ALGは3bit(bit2-0)。bit2はOPL3の4OP結合有効化(ConnectionSEL、
        # FITOM_X側ではhw.ALGのbit2に統合済み)。以前は"& 3"で2bitしか
        # 取り出しておらず、4OP音色でConnectionSELが常に0(未結合)に
        # なってしまうバグがあった(2026年7月19日修正。実データ確認:
        # Preset4OP.vma/GMmapFM4op.vmaは全128音色でbit2=1、他の2OP系
        # vmaファイルは全て0であることを確認済み)。
        alg   =  byte3 & 7

        op1 = parse_ma2_op(chunk[5:10])
        op2 = parse_ma2_op(chunk[10:15])
        ops = [op1, op2]
        if is_4op:
            ops.append(parse_ma2_op(chunk[15:20]))
            ops.append(parse_ma2_op(chunk[20:25]))

        apply_carrier_rr_floor(ops, alg)

        if raw_name:
            name = raw_name
        elif not is_drum and int(prog) < len(GM_NAMES):
            name = GM_NAMES[int(prog)]
        else:
            name = f"Drum Note {27+i}" if is_drum else f"Program {prog}"

        patch = {
            "prog": i if is_drum else int(prog),
            "name": name,
            "FB":   fb,
            "ALG":  alg,
            "ops":  ops,
        }
        patches.append(patch)

    src_name = Path(src_path).stem
    op_str = "4OP" if is_4op else "2OP"
    kind   = "drum" if is_drum else "melody"
    out = {
        "name":             bank_name or src_name,
        "voice_patch_type": group,
        "op_count":         4 if is_4op else 2,
        "source":           f"{Path(src_path).name} (MA-2 VMA FM format)",
        "note":             f"MA-2 VMA形式 {op_str} {kind} バンク。"
                            "SUS/DVB/DAM/LFOフィールドは対応フィールドが"
                            "存在しないため変換時に破棄。"
                            "MA-2形式のEGTビット/RRレジスタ(実機OPLとは極性が逆)をFITOMのSR/RRフィールドに変換"
                            "(変換元EGT=1→SR=RRレジスタ<<1,RR=RRレジスタ。"
                            "変換元EGT=0→SR=0,RR=RRレジスタ)。"
                            "ops[i].EGTフィールド自体はOPL系では無関係のため常に0。"
                            f"キャリアオペレータがSR=0かつRR=0(消音しない状態)に"
                            f"なる場合はRR={MIN_CARRIER_RR}へ補正(モジュレータ側は対象外)。",
        "patches": patches,
    }
    Path(dst_path).write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"OK {src_name}: {N}音色 {group}({op_str}) {kind} → {dst_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MA-2 VMA → FITOM_X hwbank.json")
    parser.add_argument("input",  help="*.vma ファイル (または *.vma を含むディレクトリ)")
    parser.add_argument("output", help="出力先ファイル or ディレクトリ")
    parser.add_argument("--force-2op", action="store_true", help="OPタイプ判定を無視して強制的に2OP(OPL3_2)として変換")
    parser.add_argument("--bank-name", default=None, help="バンク名(省略時はファイル名)")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)

    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for vma in sorted(src.glob("*.vma")):
            out = dst / (vma.stem + ".hwbank.json")
            convert_vma(str(vma), str(out), args.force_2op, args.bank_name)
    else:
        if dst.is_dir():
            dst = dst / (src.stem + ".hwbank.json")
        convert_vma(str(src), str(dst), args.force_2op, args.bank_name)
