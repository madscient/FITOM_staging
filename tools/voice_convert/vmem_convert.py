#!/usr/bin/env python3
"""
DX27/DX100 VMEM SysEx → FITOM_X hwbank.json + swbank.json (OPZ2グループ) 変換ツール

対応フォーマット:
  F0 43 0n 04 20 00 [4096 bytes] CS F7
  32音色 × 128バイト VMEM形式

VMEM構造 (128バイト/音色):
  P0-9:   OP4パラメータ
  P10-19: OP2パラメータ
  P20-29: OP3パラメータ
  P30-39: OP1パラメータ
  各OP10バイト:
    P+0: ATTACK RATE (0-31)
    P+1: DECAY 1 RATE (0-31)
    P+2: DECAY 2 RATE (0-31)
    P+3: RELEASE RATE (0-15)
    P+4: DECAY 1 LEVEL (0-15)
    P+5: KEYBOARD SCALING LEVEL (0-99) ← DX21/DX100固有のソフトパラメータ。
         FITOM_X hwbank.schema.jsonに対応フィールドが存在しないため出力しない。
    P+6: [AM:1][EG_BIAS_SENS:3][KEY_VEL:2][?:2]
         AM/EG_BIAS_SENSはhw.ops[].AM / hw.ext.EGSに変換する。
         KEY_VELは対応フィールドが存在しないため出力しない。
    P+7: OUTPUT LEVEL (0-99)
    P+8: [FIXED:1][COARSE:6][?:1]
         FIXEDはhw.ext.DM0(OPZ Osc fixed freq flag)に変換する。
    P+9: [KSR:2][DETUNE:4]  DETUNE=0-14(中央7)
  P40: [LFO_SYNC:1][NOISE:1][FB:3][ALG:3]
       LFO_SYNCはswbank sw.LFSに変換する。bit3はノイズ有効フラグ(機種依存、
       DX11の一部パーカッション/効果音系音色で使用を確認)。FITOM_X側の実装に
       合わせ、検出時はhw.ext.ALG_EXTにマッピングする。

  [TODO] NoiseFrequency(hw.NFQ, 0-31)未対応:
       FITOM_XではNEビット有効時にNFQ(Noise Frequency)も設定される想定だが、
       VMEM128バイト中にNFQ専用と確認できるバイト位置が未特定(2026-07時点)。
       ノイズ有効8パッチ(prog 43,49,98,99,106,121,122,126)とそれ以外で全128
       バイトを比較したが、既知フィールド(OP×4/FB・ALG/LFO/TRANSPOSE/
       PITCH_BEND_RANGE/音色名)以外に0-31の範囲で明確に分離できる位置が
       見つからなかった。DX11の正式なVMEMフォーマット仕様書が入手でき次第、
       NFQマッピングを追加すること。現状はNFQ未設定(スキーマのデフォルト値)
       のまま出力している。
  P41: LFO SPEED (0-99)       → swbank sw.LFR (近似変換、実機カーブ不明)
  P42: LFO DELAY (0-99)       → swbank sw.LFD (近似変換、20ms単位)
  P43: PITCH MOD DEPTH (0-99) → swbank sw.depth_cents (近似変換)
  P44: AMP MOD DEPTH (0-99)   ← 対応フィールドなし、出力しない
  P45: [PMS:3][AMS:2][LFO_WAVE:2]
       LFO_WAVEはswbank sw.LWFに変換する(DX系4波形とLWF前方4種が対応)。
  P46: TRANSPOSE (0-48, 中央=24) → swbank fine_transpose (半音→セント、±1200でクリップ)
  P47: PITCH BEND RANGE (0-12)   ← 対応フィールドなし、出力しない
  P57-66: VOICE NAME (10文字 ASCII)

パラメータ変換 (VMEM → OPM/OPZ2, hwbank.schema.json準拠フラット構造):
  AR:   0-31 → OPM AR 0-31 (直接)
  D1R:  0-31 → OPM DR 0-31 (直接)
  D2R:  0-31 → OPM SR 0-31 (直接)
  RR:   0-15 → OPM RR 0-15 (直接)
  D1L:  0-15 → OPM SL 0-15 (直接)
  OL:   0-99 → OPM TL = ルックアップテーブル(実機ログカーブ)
  COARSE: P8[5:2] (4bit) → OPM MUL = 直接 (0-15)
  DT2:   P8[1:0] (2bit) → OPM DT2 = 直接 (0-3)
  DETUNE: 0-14(中央7) → OPM DT1
    DETUNE=7→DT1=0, 8-10→1-3(+), 4-6→5-7(-), 0-3→7(-), 11-14→3(+)
  KSR:  0-3 → OPM KSR 0-3 (直接、VMEMの"KS"フィールドに対応)
  AM:   0-1 → OPM AM 0-1 (直接)
  FB:   0-7 → OPM FB 0-7 (直接)
  ALG:  0-7 → OPM ALG 0-7 (直接)
  PMS:  0-7 → OPM PMS 0-7 (直接)
  AMS:  0-3 → OPM AMS 0-3 (直接)
  EG_BIAS_SENS(0-7,3bit) → hw.ext.EGS (下位3bitにそのまま格納する近似実装。
    OPZ実機レジスタ(0xC0+slot)の正確なビット割付が不明なため要検証。)
  FIXED(0-1) → hw.ext.DM0 (OPZ Osc fixed freq flag、範囲互換)

注意: VMEMのKEYBOARD SCALING LEVEL(0-99)は、OPMレジスタのKSR(Key Scale
Rate, 0-3)とは全く別の概念(DX21/DX100固有のソフトウェア的スケーリング)で
あり、混同しないこと。現状FITOM_Xにこれを表現するフィールドが無いため
変換時に破棄する(KEY_VELも同様)。AMP MOD DEPTH/PITCH BEND RANGEも同様に
対応するswbankフィールドが存在しないため破棄する。
"""

import json, sys, argparse, struct
from pathlib import Path

VMEM_OP_BASES = [0, 10, 20, 30]   # P0(M1), P10(C1), P20(M2), P30(C2)

# OUTPUT LEVEL (0-99) → OPM TL 変換テーブル (実機ルックアップ、非線形)
# 参考: https://nornand.hatenablog.com/entry/2021/08/22/172147
OL_TO_TL_TABLE = [
    127,127,96,86,77,72,67,62,60,56,54,51,50,48,45,44,
    42,41,40,39,37,36,35,34,33,32,31,30,29,28,28,27,
    26,25,25,24,23,23,22,21,21,20,20,19,19,18,18,17,
    17,16,16,15,15,14,14,13,13,13,12,12,11,11,11,10,
    10,9,9,9,8,8,8,7,7,7,7,6,6,6,5,5,
    5,4,4,4,3,3,3,3,2,2,2,2,1,1,1,1,
    0,0,0,0,
]

def ol_to_tl(ol):
    """OUTPUT LEVEL (0-99) → OPM TL (0-127, 0=最大) 実機ルックアップテーブル使用"""
    return OL_TO_TL_TABLE[max(0, min(99, ol))]

def detune_to_dt1(detune):
    """DETUNE (0-14, 中央=7) → OPM DT1 (0-7)"""
    diff = detune - 7
    if diff == 0:
        return 0
    elif diff > 0:
        return min(3, diff)
    else:
        return min(3, -diff) + 4

def lfospeed_to_rate(speed_0_99):
    """DX21 LFO SPEED(0-99) → swbank LFR(1-127, 対数カーブ0.5-50Hz)への近似変換。
    実機の正確な速度カーブが不明なため、0-99を1-127へ線形写像する近似実装。"""
    if speed_0_99 <= 0:
        return 0
    return max(1, min(127, round(speed_0_99 * 127 / 99)))

def lfodelay_to_lfd(delay_0_99):
    """DX21 LFO DELAY(0-99) → swbank LFD(20ms単位、0-127)への近似変換。
    実機の正確な遅延カーブが不明なため、0-99を0-127へ線形写像する近似実装。"""
    return max(0, min(127, round(delay_0_99 * 127 / 99)))

def pmd_to_depth_cents(pmd_0_99):
    """DX21 PITCH MOD DEPTH(0-99) → swbank depth_cents への近似変換。
    実機の正確なセント換算が不明なため、0-99を0-600セントへ線形写像する近似実装。"""
    return round(pmd_0_99 * 600 / 99)

def transpose_to_fine(transpose_0_48):
    """DX21 TRANSPOSE(0-48, 中央=24) → swbank fine_transpose(セント、±1200でクリップ)"""
    semitones = transpose_0_48 - 24
    cents = semitones * 100
    return max(-1200, min(1200, cents))

def parse_vmem_voice(vbytes):
    """128バイトのVMEMデータを解析してHwPatch(フラット構造)+SwPatchデータに変換"""
    ops = []
    for op_base in VMEM_OP_BASES:
        p = vbytes[op_base:op_base+10]
        ar   = p[0] & 0x1F
        d1r  = p[1] & 0x1F
        d2r  = p[2] & 0x1F
        rr   = p[3] & 0x0F
        d1l  = p[4] & 0x0F
        am      = (p[6] >> 7) & 1
        eg_bias = (p[6] >> 4) & 7      # EG_BIAS_SENS (0-7)
        # key_vel = (p[6] >> 2) & 3    # 対応フィールドなし、破棄
        ol   = p[7] & 0x7F
        fixed  = (p[8] >> 7) & 1
        mul    = (p[8] >> 2) & 0xF
        dt2    =  p[8] & 0x03
        ksr    = (p[9] >> 4) & 3
        detune =  p[9] & 0x0F

        tl  = ol_to_tl(ol)
        dt1 = detune_to_dt1(detune)

        ops.append({
            "AR": ar, "DR": d1r, "SR": d2r, "RR": rr, "SL": d1l,
            "TL": tl, "KSR": ksr, "MUL": mul, "DT1": dt1, "DT2": dt2, "AM": am,
            "EGS": eg_bias,   # EG bias(7bit、OPZのみ、オペレータ単位): DX21/DX100の
                              # EG_BIAS_SENS(3bit)をそのまま格納(範囲0-7は0-127の部分集合)
        })

    p40 = vbytes[40]
    lfo_sync = (p40 >> 7) & 1
    fb       = (p40 >> 3) & 0x07   # 3bit(0-7)
    noise    = ((p40 >> 3) & 0x08) != 0   # bit3: ノイズ有効フラグ(機種依存)
    alg      =  p40 & 7

    p45 = vbytes[45]
    pms      = (p45 >> 4) & 7
    ams      = (p45 >> 2) & 3
    lfo_wave =  p45 & 3          # 0-3、swbank.LWFの前方4種(0-3)と直接対応

    lfo_speed = vbytes[41]
    lfo_delay = vbytes[42]
    pmd       = vbytes[43]
    # amd = vbytes[44]  # 対応フィールドなし、破棄
    transpose = vbytes[46]
    # pitch_bend_range = vbytes[47]  # 対応フィールドなし、破棄

    # P8のFIXEDは全4オペレータ共通のはずなので先頭opの値を代表として使う
    p8_op0 = vbytes[VMEM_OP_BASES[0]+8]
    fixed_flag = (p8_op0 >> 7) & 1

    name = ''.join(
        chr(vbytes[57+i]) if 32 <= vbytes[57+i] <= 126 else ' '
        for i in range(10)
    ).rstrip()

    return {
        "name": name,
        "FB": fb, "ALG": alg, "AMS": ams, "PMS": pms,
        "ops": ops,
        "ext": {
            "DM0": fixed_flag,      # OPZ Osc fixed freq flag(未実装、要データシート再確認)
            "ALG_EXT": 1 if noise else 0,  # ノイズ有効フラグ
        },
        "sw": {
            "LWF": lfo_wave,
            "LFS": lfo_sync,
            "LFM": 0,               # 対応フィールドなし、repeat固定
            "LFD": lfodelay_to_lfd(lfo_delay),
            "LFR": lfospeed_to_rate(lfo_speed),
            "LFI": 0,               # 対応フィールドなし、即フルデプス固定
            "depth_cents": pmd_to_depth_cents(pmd),
        },
        "fine_transpose": transpose_to_fine(transpose),
    }

def convert_syx(src_path, dst_hwbank_path, dst_swbank_path, bank_no=0):
    data = Path(src_path).read_bytes()

    if data[0] != 0xF0 or data[1] != 0x43:
        print(f"SKIP {src_path}: not Yamaha SysEx")
        return False
    if data[3] != 0x04:
        print(f"SKIP {src_path}: format={data[3]:02x} (expected 0x04 = 32-voice)")
        return False
    if data[-1] != 0xF7:
        print(f"WARN {src_path}: no EOX at end")

    voice_data = data[6:-2]
    if len(voice_data) != 4096:
        print(f"SKIP {src_path}: voice_data length={len(voice_data)} (expected 4096)")
        return False

    src_name = Path(src_path).stem
    hw_patches = []
    sw_patches = []
    valid_count = 0

    for i in range(32):
        vbytes = voice_data[i*128:(i+1)*128]
        voice  = parse_vmem_voice(vbytes)

        is_init = (voice["name"] == "INIT VOICE" or voice["name"] == "")
        if not is_init:
            valid_count += 1

        pname = voice["name"] if voice["name"] else f"Voice {i}"

        hw_patches.append({
            "prog": i, "name": pname,
            "FB": voice["FB"], "ALG": voice["ALG"],
            "AMS": voice["AMS"], "PMS": voice["PMS"],
            "ops": voice["ops"],
            "ext": voice["ext"],
            "sw_bank": bank_no, "sw_prog": i,
        })
        sw_patches.append({
            "prog": i, "name": pname,
            "sw": voice["sw"],
            "fine_transpose": voice["fine_transpose"],
        })

    hw_out = {
        "name":             src_name,
        "voice_patch_type": "OPZ2",
        "op_count": 4,
        "source":  f"{Path(src_path).name} (DX27/DX100 VMEM SysEx)",
        "note":    "OPM系最上位(OPZ2)として宣言。ops[]=[M1,C1,M2,C2]順。"
                    "VMEM格納順(OP4,OP2,OP3,OP1)がそのままこの順に対応。"
                    "sw_bank/sw_progで対になるswbank(同名.swbank.json)を参照。"
                    "KEYBOARD SCALING LEVEL/KEY_VEL/AMP MOD DEPTH/"
                    "PITCH_BEND_RANGEは対応フィールドが存在しないため破棄。"
                    "ext.EGS/DM0はEG_BIAS_SENS/FIXEDからの近似変換(実機の正確な"
                    "ビット割付は未検証)。",
        "patches": hw_patches,
    }
    sw_out = {
        "name": f"{src_name} (Performance)",
        "bank": bank_no,
        "note": "VMEMのLFO_SYNC/LFO_WAVE/LFO速度/LFO遅延/PMD/TRANSPOSEから変換。"
                "LFO速度・遅延・PMD・TRANSPOSEの換算式は実機の正確なカーブが"
                "不明なため線形近似。LFM/LFIは対応フィールドがないため固定値。",
        "patches": sw_patches,
    }

    Path(dst_hwbank_path).write_text(
        json.dumps(hw_out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    Path(dst_swbank_path).write_text(
        json.dumps(sw_out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"OK {src_name}: {valid_count}/32音色 → {dst_hwbank_path} + {dst_swbank_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DX27/DX100 VMEM SysEx → FITOM_X hwbank.json + swbank.json (OPZ2グループ)")
    parser.add_argument("input",  help="*.syx ファイル (またはディレクトリ)")
    parser.add_argument("output", help="出力先ディレクトリ")
    parser.add_argument("--bank", type=int, default=0)
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    dst.mkdir(parents=True, exist_ok=True)

    def do_convert(f):
        hw_out = dst / (f.stem + ".hwbank.json")
        sw_out = dst / (f.stem + ".swbank.json")
        convert_syx(str(f), str(hw_out), str(sw_out), args.bank)

    if src.is_dir():
        for f in sorted(src.glob("*.syx")):
            do_convert(f)
    else:
        do_convert(src)
