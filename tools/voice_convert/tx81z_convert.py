#!/usr/bin/env python3
"""
Yamaha TX81Z 32-Voice VMEM SysEx → FITOM_X hwbank.json (OPMグループ) 変換ツール

フォーマット (Image4より):
  F0 43 0n 04 10 00 [4096 bytes] CS F7
  32音色 × 128バイト 拡張VMEM (VCED+ACED)

1音色 128バイト構成:
  addr  0-9:   OP4 VCED (→ OPM M1 → ops[0])
  addr 10-19:  OP2 VCED (→ OPM M2 → ops[2])
  addr 20-29:  OP3 VCED (→ OPM C1 → ops[1])
  addr 30-39:  OP1 VCED (→ OPM C2 → ops[3])
               VMEMの格納順はOPMのレジスタスロット順(M1,M2,C1,C2)。TX81Zの
               パネル表記OP1-4はOPMのチェーン順(op1=M1..op4=C2)と逆順のため、
               OP4=M1 / OP3=C1 / OP2=M2 / OP1=C2 に対応する。
  addr 40:     [SY:1][FBL:3][ALG:3]  SY=LFO sync (HW LFO用、変換しない)
  addr 41:     LFS (LFO speed)       (HW LFO用、変換しない)
  addr 42:     LFD (LFO delay)       (HW LFO用、変換しない)
  addr 43:     PMD                   (HW LFO用、変換しない)
  addr 44:     AMD                   (HW LFO用、変換しない)
  addr 45:     [PMS:3][AMS:2][LFW:2] LFW=LFO波形 (HW LFO用、変換しない)
  addr 46:     TRPS (transpose 0-48, 中央=24)
  addr 47:     [PBR:4] pitch bend range
  addr 48:     [MO:1][SU:1][PO:1][PM:1][CH:2]
  addr 49:     PORT
  addr 50-56:  FC VOL, MW PITCH/AMPLI, BC PITCH/AMPLI/P.BIAS/E.BIAS
  addr 57-66:  VOICE NAME (10文字 ASCII)
  addr 67-69:  PEG PR1-3
  addr 70-72:  PEG PL1-3
  addr 73-74:  OP4 ACED拡張 (→ ops[0])
  addr 75-76:  OP2 ACED拡張 (→ ops[2])
  addr 77-78:  OP3 ACED拡張 (→ ops[1])
  addr 79-80:  OP1 ACED拡張 (→ ops[3])
  addr 81:     REV
  addr 82:     FC PITCH
  addr 83:     FC AMPLI
  addr 84-127: padding (0)

OP VCED 10バイト:
  +0: [b4:0]=AR(0-31)
  +1: [b4:0]=D1R(0-31)
  +2: [b4:0]=D2R(0-31)
  +3: [b3:0]=RR(0-15)
  +4: [b3:0]=D1L(0-15、15=減衰なし) → OPM SL = 15 - D1L (極性反転)
      VMEMはパネル上の「レベル」(大きいほど大音量)を格納するが、OPMの
      D1Lレジスタは「減衰量」(0=減衰なし)であり極性が逆のため反転する。
  +5: LS(0-99) keyboard level scaling
  +6: [0:1][AME:1][EBS:3][KVS:3]  AME=bit6, EBS=bits5-3, KVS=bits2-0
      実データ全2560オペレータの分布から確定(bit7は一度も立たない)。
  +7: OUT(0-99) → TL: OUT 20-99 は `99 - OUT`、OUT 0-19 はルックアップテーブル
      さらにキャリアのTLには A_alg(キャリア本数による音量正規化: 1本=0/2本=8/
      3本=13/4本=16) を加算する。モジュレータは対象外。
  +8: F [b5:2]=MUL(4bit), [b1:0]=DT2(2bit)
  +9: [0:3][RS:2][DBT:3]  RS=0-3, DBT: 0-6(中央3、パネル表記-3〜+3) → DT1
      実データ全2560オペレータで最大値30(0b11110)・bit7-5が常に0・
      下位3bitに7が出現しないことから確定したビット配置。

OP ACED 2バイト:
  byte0: [EGSFT:3][FIX:1][FIXRG:4]
  byte1: [OPW:3][FINE:4]

TX81Z固有拡張 (FITOM_X OPZ対応):
  OPW: 波形選択 0-7 (OPM拡張 = FmHwOp::WS に格納)
  FIX: 固定周波数モード
  FIXRG: 固定周波数レンジ (0-7)
  FINE: 微調整 (0-15)
  EGSFT: EG shift (0-7)
"""

import json, argparse, struct
from pathlib import Path

# VMEMはオペレータをOPMのレジスタスロット順(M1,M2,C1,C2)で格納するが、
# FITOM_Xのops[]はチェーン順[M1,C1,M2,C2]。2番目と3番目を入れ替える。
VCED_BASES = [0, 20, 10, 30]      # ops[0]=M1, ops[1]=C1, ops[2]=M2, ops[3]=C2
ACED_BASES = [73, 77, 75, 79]

# OUT (0-99) → OPM TL(減衰量) 変換テーブル (実機ルックアップ)
# 参考: https://nornand.hatenablog.com/entry/2020/11/21/201911
# OUT 20-99 は Aol = 99 - OUT の線形域。OUT 0-19 のみ非線形に減衰量が加速する。
# Volumeパラメータ用の別テーブルとは異なるカーブなので流用してはならない。
OUT_TO_TL_NONLINEAR = [
    127, 122, 118, 114, 110, 107, 104, 102, 100, 98,
     96,  94,  92,  90,  88,  86,  85,  84,  82,  81,
]

def out_to_tl(out):
    """OUT (0-99) → OPM TL (0-127, 0=最大音量)"""
    out = max(0, min(99, out))
    return OUT_TO_TL_NONLINEAR[out] if out < 20 else 99 - out

# ALGごとのキャリアops添字 (ops[]=[M1,C1,M2,C2]のチェーン順。
# FITOM_XのCSoundDevice::kCarrierMask={08,08,08,08,0A,0E,0E,0F}と同一)
CARRIER_OPS_BY_ALG = {
    0: (3,), 1: (3,), 2: (3,), 3: (3,),
    4: (1, 3),
    5: (1, 2, 3), 6: (1, 2, 3),
    7: (0, 1, 2, 3),
}

# A_alg: キャリア本数による音量正規化の減衰量 (キャリア数 → TLステップ)。
# キャリアをN本合成すると振幅がN倍になるため、20*log10(N)相当を減衰させる
# (TLは0.75dB/step: 2本=6.00dB, 3本=9.75dB, 4本=12.00dB)。
# 出典: https://nornand.hatenablog.com/entry/2020/11/21/201911
# (同記事はTX81Zパネル表記のop番号で「ALG5はop1,3が8」等と記載しているが、
#  OP1=C2/OP2=M2/OP3=C1/OP4=M1で読み替えるとキャリア集合と完全に一致する)
A_ALG_BY_CARRIER_COUNT = {1: 0, 2: 8, 3: 13, 4: 16}

# キャリアのベロシティ→TL感度 (汎用デフォルト固定)。実機のKVSはキャリアにも
# 設定されているが、キャリアのベロシティ応答は演奏性を優先して全パッチ均一に
# するというプロジェクトの方針を優先する。
CARRIER_VTL = 80

# モジュレータのベロシティ→TL感度: VCEDのKVS(0-7)から換算する。
# 実機のA_kvs(velocity依存の減衰量)のスイング分を、FITOM_XのVTL補正
# (-kGM2dB[vel] * VTL/254 / 0.75、VoiceProcessor.cpp)でvelocity 32-127の
# 範囲について最小二乗近似した値。KVS 1-2は残差±0.5ステップ以内でほぼ一致
# するが、FITOM_XのVTLは変動幅をVTL/2に抑える設計のためKVS>=3はVTL=127で
# 飽和し、実機ほど深い感度は表現できない(KVS=7・velocity32で約17dB不足)。
# 出典: https://nornand.hatenablog.com/entry/2021/01/01/153911
KVS_TO_VTL = {0: 0, 1: 42, 2: 89, 3: 127, 4: 127, 5: 127, 6: 127, 7: 127}

def kvs_tl_floor(kvs):
    """A_kvsのうちvelocity=127でも残る定数床[TLステップ]。
    実機は `attKVS = ((KVS*table[vel-1] + (7-KVS)*16) >> 3) + 1` (7bit整数+1bit小数)
    で、table[126]=0のためvelocity=127では `(7-KVS)*2+1` が残る。その半分(=TL
    ステップ)を四捨五入すると `8 - KVS` になる。ベロシティに依存しない静的な
    減衰なのでTLへ加算する(スイング分はVTLが受け持つ)。"""
    return (8 - kvs) if kvs else 0

def apply_alg_attenuation(alg, ops, tl_key="TL"):
    """キャリアのTLにA_alg(キャリア本数による音量正規化)を加算する。
    モジュレータのTLは変調指数を決めるもので合成後の音量に寄与しないため対象外。"""
    carriers = CARRIER_OPS_BY_ALG[alg & 7]
    att = A_ALG_BY_CARRIER_COUNT[len(carriers)]
    if not att:
        return
    for i in carriers:
        ops[i][tl_key] = min(127, ops[i][tl_key] + att)

def dbt_to_dt1(dbt):
    """DBT/DETUNE (0-6, 中央=3) → OPM DT1 (3bit、bit2が符号)"""
    diff = dbt - 3
    if diff == 0:   return 0
    elif diff > 0:  return diff        # +1〜+3
    else:           return -diff + 4   # -1〜-3 → 5〜7

def parse_op(vp, ap):
    """VCED 10バイト + ACED 2バイト → FmHwOp辞書"""
    mul = (vp[8] >> 2) & 0xF
    dt2 =  vp[8] & 0x03
    dt1 = dbt_to_dt1(vp[9] & 0x07)
    rs  = (vp[9] >> 3) & 0x03

    opw   = (ap[1] >> 4) & 0x07   # TX81Z wave shape → WS
    fine  =  ap[1] & 0x0F
    fix   = (ap[0] >> 4) & 0x01
    fixrg =  ap[0] & 0x0F
    egsft = (ap[0] >> 5) & 0x07

    return {
        # OPMレジスタ値
        "AR":  vp[0] & 0x1F,
        "D1R": vp[1] & 0x1F,
        "D2R": vp[2] & 0x1F,
        "RR":  vp[3] & 0x0F,
        "D1L": 15 - (vp[4] & 0x0F),
        "TL":  min(127, out_to_tl(vp[7]) + kvs_tl_floor(vp[6] & 7)),
        "MUL": mul,
        "DT1": dt1,
        "DT2": dt2,
        "KS":  rs,
        "AM":  (vp[6] >> 6) & 1,   # AME (bit7ではなくbit6。実データで確認)
        "WS":  opw,               # TX81Z波形 (OPZ拡張)
        # TX81Z固有拡張
        "FIX":   fix,
        "FIXRG": fixrg,
        "FINE":  fine,
        "EGSFT": egsft,
        # ソフトパラメータ
        "EBS": (vp[6] >> 3) & 7,  # EG Bias Sensitivity
        "KVS":  vp[6] & 7,         # Key Velocity Sensitivity
        "LS":   vp[5],             # Level Scaling
    }

def parse_voice(vbytes):
    """128バイトの拡張VMEMデータを解析"""
    name = ''.join(
        chr(vbytes[57+i]) if 32 <= vbytes[57+i] <= 126 else ' '
        for i in range(10)
    ).rstrip()

    # ops: [M1(OP4), C1(OP3), M2(OP2), C2(OP1)]
    ops = [
        parse_op(vbytes[vb:vb+10], vbytes[ab:ab+2])
        for vb, ab in zip(VCED_BASES, ACED_BASES)
    ]

    b40 = vbytes[40]
    b45 = vbytes[45]
    b48 = vbytes[48]

    apply_alg_attenuation(b40 & 7, ops)

    # SwPatch側のops: キャリアは汎用デフォルト固定、モジュレータはKVS由来
    carriers = CARRIER_OPS_BY_ALG[b40 & 7]
    sw_ops = [{"VTL": CARRIER_VTL if i in carriers else KVS_TO_VTL[ops[i]["KVS"]]}
              for i in range(4)]

    # addr40 bit7(SY=LFO sync) / addr41(LFO speed) / addr42(LFO delay) /
    # addr43(PMD) / addr44(AMD) / addr45下位2bit(LFW=LFO波形)は、TX81Z実機の
    # 内蔵(ハードウェア)LFOを駆動するパラメータ。FITOM_XはHW LFOを使用せず
    # (`COPM::updateVoice`がレジスタ$38+chに0を書いて無効化する)、swbankの
    # `sw.*`は別機構であるソフトLFOの設定であるため変換しない。さらに
    # `sw.LFR>0`の音色はCC#1(モジュレーションホイール)が作用しなくなる仕様
    # (`ISoundDevice.h`の`setCC1Modulation`)のため、流し込むと「常時ビブラートが
    # 掛かりモジュレーションが効かない」状態になる。
    return {
        "name": name,
        "hw": {
            "ALG": b40 & 7,
            "FB":  (b40 >> 3) & 7,
            # PMS/AMSは実機レジスタ$38+chのHW LFO感度。値は保持するが
            # FITOM_XがHW LFOを無効化するため実際には参照されない。
            "PMS": (b45 >> 4) & 7,
            "AMS": (b45 >> 2) & 3,
            "REV": vbytes[81],
        },
        "ops": ops,
        "sw_ops": sw_ops,
        "sw": {
            "transpose":  vbytes[46] - 24,  # 0-48 → -24〜+24
            "pitch_bend": vbytes[47] & 0xF,
            "port_time":  vbytes[49],
            "peg_pr":     [vbytes[67], vbytes[68], vbytes[69]],
            "peg_pl":     [vbytes[70], vbytes[71], vbytes[72]],
            "fc_pitch":   vbytes[82],
            "fc_ampli":   vbytes[83],
        },
    }

def convert(src_path, dst_path, bank_no=0):
    data = Path(src_path).read_bytes()

    # SysEx検証
    assert data[0] == 0xF0 and data[1] == 0x43, "Not Yamaha SysEx"
    assert data[3] == 0x04, f"Format={data[3]:02x} (expected 0x04)"
    data_size = (data[4] << 7) | data[5]   # MIDI 7bit encoding
    assert data_size == 4096, f"Data size={data_size} (expected 4096)"
    assert data[-1] == 0xF7, "No EOX"

    voice_data = data[6:-2]
    assert len(voice_data) == 4096, f"Voice data length={len(voice_data)}"

    src_name = Path(src_path).stem
    patches  = []

    for i in range(32):
        vbytes = voice_data[i*128:(i+1)*128]
        voice  = parse_voice(vbytes)
        patches.append({
            "prog": i,
            "name": voice["name"],
            "hw":   voice["hw"],
            "ops":  voice["ops"],
            "sw":   voice["sw"],
        })

    out = {
        "name":     src_name,
        "group":    "OPM",          # TX81Zは OPZ(YM2414) だが OPMグループ互換
        "chip":     "OPZ",          # TX81Z固有拡張を示す
        "bank":     bank_no,
        "op_count": 4,
        "source":   f"{Path(src_path).name} (TX81Z 32-Voice VMEM SysEx)",
        "note":     "ops[]=[M1,C1,M2,C2]順。WS=OPZ波形(0-7)、FIX/FIXRG/FINE/EGSFTはOPZ拡張。"
                    "LFO SYNC/SPEED/DELAY/PMD/AMD/WAVEはHW LFO用のため変換していない。",
        "patches":  patches,
    }
    Path(dst_path).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"OK {src_name}: 32音色 OPZ(4OP) → {dst_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TX81Z 32-Voice VMEM SysEx → FITOM_X hwbank.json")
    parser.add_argument("input",  help="*.syx ファイル (またはディレクトリ)")
    parser.add_argument("output", help="出力先ファイル or ディレクトリ")
    parser.add_argument("--bank", type=int, default=0)
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)

    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src.glob("*.syx")):
            out = dst / (f.stem + ".hwbank.json")
            convert(str(f), str(out), args.bank)
    else:
        if dst.is_dir():
            dst = dst / (src.stem + ".hwbank.json")
        convert(str(src), str(dst), args.bank)
