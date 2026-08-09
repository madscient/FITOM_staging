#!/usr/bin/env python3
"""
DX27/DX100 VMEM SysEx → FITOM_X hwbank.json + swbank.json (OPZ2グループ) 変換ツール

対応フォーマット:
  F0 43 0n 04 20 00 [4096 bytes] CS F7
  32音色 × 128バイト VMEM形式

VMEM構造 (128バイト/音色):
  P0-9:   OP4パラメータ (→ OPM M1 → ops[0])
  P10-19: OP2パラメータ (→ OPM M2 → ops[2])
  P20-29: OP3パラメータ (→ OPM C1 → ops[1])
  P30-39: OP1パラメータ (→ OPM C2 → ops[3])
    VMEMの格納順はOPMのレジスタスロット順(M1,M2,C1,C2)。DX21/DX27/DX100の
    パネル表記OP1-4はOPMのチェーン順(op1=M1..op4=C2)と逆順のため、
    OP4=M1 / OP3=C1 / OP2=M2 / OP1=C2 に対応する。
  各OP10バイト:
    P+0: ATTACK RATE (0-31)
    P+1: DECAY 1 RATE (0-31)
    P+2: DECAY 2 RATE (0-31)
    P+3: RELEASE RATE (0-15)
    P+4: DECAY 1 LEVEL (0-15、15=減衰なし) → OPM SL = 15 - D1L
         VMEMはパネル上の「レベル」(大きいほど大音量)を格納するが、OPMの
         D1Lレジスタは「減衰量」(0=減衰なし)であり極性が逆のため反転する。
    P+5: KEYBOARD SCALING LEVEL (0-99) ← DX21/DX100固有のソフトパラメータ。
         FITOM_X hwbank.schema.jsonに対応フィールドが存在しないため出力しない。
    P+6: [AM:1][EG_BIAS_SENS:3][KEY_VEL:2][?:2]
         AM/EG_BIAS_SENSはhw.ops[].AM / hw.ext.EGSに変換する。
         KEY_VELは対応フィールドが存在しないため出力しない。
    P+7: OUTPUT LEVEL (0-99)
    P+8: [0:2][COARSE:4][DT2:2]
         上位2bitは実データ(dx21/dx100/dx11/tx81z 全2560オペレータ)で常に0。
         旧実装はbit7をFIXED(固定周波数)としてext.FIXへ出力していたが、
         常に0の死んだフィールドだったため廃止した。
    P+9: [0:3][RS:2][DETUNE:3]  RS=0-3, DETUNE=0-6(中央3、パネル表記-3〜+3)
         実データ全2560オペレータで最大値30(0b11110)・bit7-5が常に0・
         下位3bitに7が出現しないことから確定したビット配置。
  P40: [LFO_SYNC:1][NOISE:1][FB:3][ALG:3]
       bit3はノイズ有効フラグ(機種依存、DX11の一部パーカッション/効果音系音色で
       使用を確認)。FITOM_X側の実装に合わせ、検出時はhw.ext.ALG_EXTにマッピング
       する。LFO_SYNCはハードウェアLFO用のため変換しない(下記参照)。

  [TODO] NoiseFrequency(hw.NFQ, 0-31)未対応:
       FITOM_XではNEビット有効時にNFQ(Noise Frequency)も設定される想定だが、
       VMEM128バイト中にNFQ専用と確認できるバイト位置が未特定(2026-07時点)。
       ノイズ有効8パッチ(prog 43,49,98,99,106,121,122,126)とそれ以外で全128
       バイトを比較したが、既知フィールド(OP×4/FB・ALG/LFO/TRANSPOSE/
       PITCH_BEND_RANGE/音色名)以外に0-31の範囲で明確に分離できる位置が
       見つからなかった。DX11の正式なVMEMフォーマット仕様書が入手でき次第、
       NFQマッピングを追加すること。現状はNFQ未設定(スキーマのデフォルト値)
       のまま出力している。
  P40 bit7 / P41-P45: ハードウェアLFO用パラメータ ← 変換しない
       LFO SYNC / LFO SPEED / LFO DELAY / PITCH MOD DEPTH / AMP MOD DEPTH /
       LFO WAVE、および P45 の PMS/AMS(チャンネル単位のHW LFO感度)は、いずれも
       DX/TX実機の**内蔵(ハードウェア)LFO**を駆動するパラメータである。
       FITOM_XはHW LFOを使用せず(`COPM::updateVoice`がレジスタ$38+chに0を
       書いてHW LFOを無効化する)、swbankの`sw.*`は別機構である**ソフトLFO**の
       設定である(`swbank.schema.json`の`sw`説明: 「HW LFOはボイスパラメータから
       切り離され、CC#1 Modulationとして別途実装されている」)。
       さらに`sw.LFR>0`の音色はCC#1(モジュレーションホイール)が作用しなくなる
       仕様(`ISoundDevice.h`の`setCC1Modulation`)のため、HW LFO設定を`sw.*`へ
       流し込むと「常時ビブラートが掛かりモジュレーションが効かない」状態になる。
       よってこれらは意図的に破棄する。
  P46: TRANSPOSE (0-48, 中央=24) → swbank fine_transpose (半音→セント、±1200で
       クリップ。HW LFOとは無関係の演奏パラメータなので変換対象)
  P47: PITCH BEND RANGE (0-12)   ← 対応フィールドなし、出力しない
  P57-66: VOICE NAME (10文字 ASCII)

パラメータ変換 (VMEM → OPM/OPZ2, hwbank.schema.json準拠フラット構造):
  AR:   0-31 → OPM AR 0-31 (直接)
  D1R:  0-31 → OPM DR 0-31 (直接)
  D2R:  0-31 → OPM SR 0-31 (直接)
  RR:   0-15 → OPM RR 0-15 (直接)
  D1L:  0-15 → OPM SL = 15 - D1L (極性反転)
  OL:   0-99 → OPM TL = OL 20-99 は `99 - OL`、OL 0-19 はルックアップテーブル
    さらにキャリアのTLには A_alg(キャリア本数による音量正規化: 1本=0/2本=8/
    3本=13/4本=16) を加算する。モジュレータは対象外。
  COARSE: P8[5:2] (4bit) → OPM MUL = 直接 (0-15)
  DT2:   P8[1:0] (2bit) → OPM DT2 = 直接 (0-3)
  DETUNE: 0-6(中央3) → OPM DT1 (3bit、bit2が符号、0と4はいずれも無デチューン)
    DETUNE=3→DT1=0, 4/5/6→1/2/3(+), 2/1/0→5/6/7(-)
  KSR:  P9[4:3] (2bit) → OPM KSR 0-3 (直接、VMEMの"RS"フィールドに対応)
  AM:   0-1 → OPM AM 0-1 (直接)
  FB:   0-7 → OPM FB 0-7 (直接)
  ALG:  0-7 → OPM ALG 0-7 (直接)
  PMS:  0-7 → OPM PMS 0-7 (直接、レジスタ$38+chのHW LFO感度)
  AMS:  0-3 → OPM AMS 0-3 (直接、同上)
  EG_BIAS_SENS(0-7,3bit) → hw.ext.EGS (下位3bitにそのまま格納する近似実装。
    OPZ実機レジスタ(0xC0+slot)の正確なビット割付が不明なため要検証。)

注意: `hw.PMS`/`hw.AMS`は実機レジスタ値として忠実に格納するが、FITOM_Xの
`COPM::updateVoice`はレジスタ$38+chに0を書く(HW LFO無効化)ため、OPM/OPZでは
実際には参照されない。変換元の情報を保持する目的で出力している。

注意: VMEMのKEYBOARD SCALING LEVEL(0-99)は、OPMレジスタのKSR(Key Scale
Rate, 0-3)とは全く別の概念(DX21/DX100固有のソフトウェア的スケーリング)で
あり、混同しないこと。現状FITOM_Xにこれを表現するフィールドが無いため
変換時に破棄する(KEY_VELも同様)。PITCH BEND RANGEも対応するswbank
フィールドが存在しないため破棄する。
"""

import json, sys, argparse, struct
from pathlib import Path

# VMEMはオペレータをOPMのレジスタスロット順(M1,M2,C1,C2 = パネル表記OP4,OP2,OP3,OP1)
# で格納するが、FITOM_Xのops[]はチェーン順[M1,C1,M2,C2]。P10とP20を入れ替える。
VMEM_OP_BASES = [0, 20, 10, 30]   # ops[0]=P0(M1), ops[1]=P20(C1), ops[2]=P10(M2), ops[3]=P30(C2)

# 汎用デフォルトのベロシティ→TL感度 (banks/sw/performance_presets.swbank.json の
# "VelScale Mid" と同値)。VCEDのKVSは変換しないため全パッチ一律で与える。
DEFAULT_VTL = 80

# OUTPUT LEVEL (0-99) → OPM TL(減衰量) 変換テーブル (実機ルックアップ)
# 参考: https://nornand.hatenablog.com/entry/2020/11/21/201911
# OL 20-99 は Aol = 99 - OL の線形域。OL 0-19 のみ非線形に減衰量が加速する。
OL_TO_TL_NONLINEAR = [
    127, 122, 118, 114, 110, 107, 104, 102, 100, 98,
     96,  94,  92,  90,  88,  86,  85,  84,  82,  81,
]

def ol_to_tl(ol):
    """OUTPUT LEVEL (0-99) → OPM TL (0-127, 0=最大音量)"""
    ol = max(0, min(99, ol))
    return OL_TO_TL_NONLINEAR[ol] if ol < 20 else 99 - ol

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
# (同記事はDXパネル表記のop番号で「ALG5はop1,3が8」等と記載しているが、
#  OP1=C2/OP2=M2/OP3=C1/OP4=M1で読み替えるとキャリア集合と完全に一致する)
A_ALG_BY_CARRIER_COUNT = {1: 0, 2: 8, 3: 13, 4: 16}

def apply_alg_attenuation(alg, ops):
    """キャリアのTLにA_alg(キャリア本数による音量正規化)を加算する。
    モジュレータのTLは変調指数を決めるもので合成後の音量に寄与しないため対象外。"""
    carriers = CARRIER_OPS_BY_ALG[alg & 7]
    att = A_ALG_BY_CARRIER_COUNT[len(carriers)]
    if not att:
        return
    for i in carriers:
        ops[i]["TL"] = min(127, ops[i]["TL"] + att)

def detune_to_dt1(detune):
    """DETUNE (0-6, 中央=3) → OPM DT1 (3bit、bit2が符号)"""
    diff = detune - 3
    if diff == 0:
        return 0
    elif diff > 0:
        return diff          # +1〜+3
    else:
        return -diff + 4     # -1〜-3 → 5〜7

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
        mul    = (p[8] >> 2) & 0xF
        dt2    =  p[8] & 0x03
        ksr    = (p[9] >> 3) & 3
        detune =  p[9] & 0x07

        tl  = ol_to_tl(ol)
        dt1 = detune_to_dt1(detune)

        ops.append({
            "AR": ar, "DR": d1r, "SR": d2r, "RR": rr, "SL": 15 - d1l,
            "TL": tl, "KSR": ksr, "MUL": mul, "DT1": dt1, "DT2": dt2, "AM": am,
            "EGS": eg_bias,   # EG bias(7bit、OPZのみ、オペレータ単位): DX21/DX100の
                              # EG_BIAS_SENS(3bit)をそのまま格納(範囲0-7は0-127の部分集合)
        })

    p40 = vbytes[40]
    fb       = (p40 >> 3) & 0x07   # 3bit(0-7)
    noise    = ((p40 >> 3) & 0x08) != 0   # bit3: ノイズ有効フラグ(機種依存)
    alg      =  p40 & 7

    apply_alg_attenuation(alg, ops)

    p45 = vbytes[45]
    pms      = (p45 >> 4) & 7
    ams      = (p45 >> 2) & 3

    # P40 bit7(LFO SYNC)・P41(LFO SPEED)・P42(LFO DELAY)・P43(PMD)・P44(AMD)・
    # P45下位2bit(LFO WAVE)はHW LFO用のためswbankへ変換しない(冒頭コメント参照)
    transpose = vbytes[46]
    # pitch_bend_range = vbytes[47]  # 対応フィールドなし、破棄

    name = ''.join(
        chr(vbytes[57+i]) if 32 <= vbytes[57+i] <= 126 else ' '
        for i in range(10)
    ).rstrip()

    return {
        "name": name,
        "FB": fb, "ALG": alg, "AMS": ams, "PMS": pms,
        "ops": ops,
        "ext": {
            "ALG_EXT": 1 if noise else 0,  # ノイズ有効フラグ
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
            # 変換元のKVS(ベロシティ感度)は変換しないため、パフォーマンス情報を
            # 持たない変換元と同じ扱いで汎用デフォルトのVTLのみを与える。
            # 他のフィールドはFmSwOpの既定値(0)のまま = 未設定。
            "ops": [{"VTL": DEFAULT_VTL} for _ in range(4)],
            "fine_transpose": voice["fine_transpose"],
        })

    hw_out = {
        "name":             src_name,
        "voice_patch_type": "OPZ2",
        "op_count": 4,
        "source":  f"{Path(src_path).name} (DX27/DX100 VMEM SysEx)",
        "note":    "OPM系最上位(OPZ2)として宣言。ops[]=[M1,C1,M2,C2]順。"
                    "VMEM格納順(OP4,OP2,OP3,OP1=M1,M2,C1,C2)から並び替え済み。"
                    "sw_bank/sw_progで対になるswbank(同名.swbank.json)を参照。"
                    "KEYBOARD SCALING LEVEL/KEY_VEL/PITCH_BEND_RANGEは対応"
                    "フィールドが存在しないため破棄。hw.PMS/AMSは実機レジスタ値"
                    "として格納しているが、FITOM_XはHW LFOを無効化するため"
                    "実際には参照されない。ext.EGSはEG_BIAS_SENSからの近似変換"
                    "(実機の正確なビット割付は未検証)。",
        "patches": hw_patches,
    }
    sw_out = {
        "name": f"{src_name} (Performance)",
        "bank": bank_no,
        "note": "VMEMのTRANSPOSEをfine_transpose(セント)へ変換したもの。"
                f"opsのVTL={DEFAULT_VTL}はパフォーマンス情報を持たない変換元向けの"
                "汎用デフォルト(VCEDのKVSは変換しない)。"
                "VMEMのLFO SYNC/WAVE/SPEED/DELAY/PMD/AMDはDX実機の"
                "ハードウェアLFO用パラメータであり、FITOM_XはHW LFOを使用せず、"
                "swbankのsw.*は別機構のソフトLFO設定であるため変換しない"
                "(sw.LFR>0にするとCC#1モジュレーションが効かなくなる)。",
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
