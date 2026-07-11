#!/usr/bin/env python3
"""
Yamaha FB-01 RAW dump (.dmp) → FITOM_X hwbank.json (OPMグループ) 変換ツール

ファイル形式:
  32バイト バンクヘッダ (バンク名8バイト + 0パディング24バイト)
  64音色 × 48バイト voice data

Voice Data ($00-$2F, 48バイト):
  $00-$06: 音色名 (7バイト ASCII)
  $07:     LFO Speed (8bit)
  $08:     %xyyyyyyy  x=enable_lfo_load, y=AMD(7bit)
  $09:     %xyyyyyyy  x=sync_lfo_at_note_on, y=PMD(7bit)
  $0A:     (%xyyyyyyy 未使用 or 追加パラメータ)
  $0B:     %0wxyz000  w=OP#3_en, x=OP#2_en, y=OP#1_en, z=OP#0_en
  $0C:     %00xxxyyy  x=FB(3bit), y=ALG(3bit)
  $0D:     %0xxxxx00  x=PMS(3bit) + y=AMS(2bit) → %0xxxyyZZ: PMS[6:4] AMS[3:2]
  $0E:     %0xx00000  x=LFO wave(2bit)
  $0F:     transpose (signed byte, 100 cents resolution)
  $10-$17: OP#0 block (→ OPM M1 → ops[0])
  $18-$1F: OP#1 block (→ OPM M2 → ops[2])
  $20-$27: OP#2 block (→ OPM C1 → ops[1])
  $28-$2F: OP#3 block (→ OPM C2 → ops[3])

Operator Block (8バイト):
  $00: %0xxxxxxx  TL(7bit)
  $01: %xyyy0000  x=KLS_type_bit0, y=vel_sens_TL(3bit)
  $02: %xxxxyyyy  x=KLS_depth(4bit), y=TL_adjust(4bit)
  $03: %xyyyzzzz  x=KLS_type_bit1, y=DT1(3bit), z=MUL(4bit)
  $04: %xx0yyyyy  x=KRS(2bit), y=AR(5bit)
  $05: %xyyzzzzz  x=C/M_AM(1bit), y=vel_AR(2bit), z=D1R(5bit)
  $06: %xx0yyyyy  x=DT2(2bit), y=D2R(5bit)
  $07: %xxxxyyyy  x=SL(4bit), y=RR(4bit)

OP番号→OPMスロット→FITOM_X ops[]対応:
  FB-01 OP#0 → OPM M1 → ops[0]
  FB-01 OP#2 → OPM C1 → ops[1]
  FB-01 OP#1 → OPM M2 → ops[2]
  FB-01 OP#3 → OPM C2 → ops[3]
"""

import json, argparse
from pathlib import Path

HEADER_SIZE  = 32
VOICE_SIZE   = 48
VOICE_COUNT  = 64

# FB-01 OP格納順 → FITOM_X ops[M1,C1,M2,C2] へのインデックス
# ops[0]=M1=OP#0, ops[1]=C1=OP#2, ops[2]=M2=OP#1, ops[3]=C2=OP#3
OP_SLOT_ORDER = [0, 2, 1, 3]  # OP#インデックス順: [M1,C1,M2,C2]

def is_valid_name(name_bytes):
    """音色名が有効(ASCII印刷可能で最初の文字がアルファベット/数字)か判定"""
    if not name_bytes:
        return False
    first = name_bytes[0]
    if not (0x41 <= first <= 0x5A or 0x61 <= first <= 0x7A or 0x30 <= first <= 0x39):
        return False
    return all(0x20 <= b <= 0x7E for b in name_bytes)

def parse_op_block(b8):
    """8バイトのOP blockを解析してhwbank.schema.json準拠フラットop辞書を返す"""
    return {
        "TL":  b8[0] & 0x7F,
        "MUL": b8[3] & 0x0F,
        "DT1": (b8[3] >> 4) & 0x07,
        "DT2": (b8[6] >> 6) & 0x03,
        "KSR": (b8[4] >> 6) & 0x03,
        "AR":  b8[4] & 0x1F,
        "DR":  b8[5] & 0x1F,
        "SR":  b8[6] & 0x1F,
        "SL":  (b8[7] >> 4) & 0x0F,
        "RR":  b8[7] & 0x0F,
        "AM":  (b8[5] >> 7) & 0x01,
        "VIB": 0,
        "EGT": 0,
        "WS":  0,
        # VEL_TL/VEL_AR/KLS_type/KLS_depth/TL_adjは対応フィールドがないため破棄
    }

def parse_voice(vbytes):
    """48バイトのvoice dataを解析"""
    name = vbytes[:7].decode('ascii', errors='replace').rstrip()

    lfo_speed    = vbytes[7]
    enable_lfo   = (vbytes[8] >> 7) & 1
    amd          =  vbytes[8] & 0x7F
    sync_lfo     = (vbytes[9] >> 7) & 1
    pmd          =  vbytes[9] & 0x7F

    op_enable = [(vbytes[11] >> (3 + i)) & 1 for i in range(4)]  # OP#0-3

    fb          = (vbytes[12] >> 3) & 0x07
    alg         =  vbytes[12] & 0x07
    pms         = (vbytes[13] >> 4) & 0x07
    ams         = (vbytes[13] >> 2) & 0x03
    lfo_wave    = (vbytes[14] >> 1) & 0x03
    transpose   =  vbytes[15] if vbytes[15] < 128 else vbytes[15] - 256

    # 4OP blocks: OP#0=$10, OP#1=$18, OP#2=$20, OP#3=$28
    raw_ops = [parse_op_block(vbytes[16 + i*8 : 24 + i*8]) for i in range(4)]

    # FITOM_X ops[M1,C1,M2,C2] 順に並べ替え
    # OP#0=M1→[0], OP#2=C1→[1], OP#1=M2→[2], OP#3=C2→[3]
    ops = [raw_ops[OP_SLOT_ORDER[i]] for i in range(4)]

    return {
        "name": name,
        "FB":   fb,
        "ALG":  alg,
        "AMS":  ams,
        "PMS":  pms,
        "ops":  ops,
        "sw": {
            "lfo_speed":  lfo_speed,
            "amd":        amd,
            "pmd":        pmd,
            "transpose":  transpose,
            "op_enable":  op_enable,
            "lfo_wave":   lfo_wave,
            "lfo_sync":   sync_lfo,
            "lfo_enable": enable_lfo,
        },
    }

def lfospeed_to_rate(speed_0_255, enabled):
    """FB-01 LFO SPEED(0-255) → swbank LFR(1-127,対数カーブ0.5-50Hz)への近似変換"""
    if not enabled or speed_0_255 <= 0:
        return 0
    return max(1, min(127, round(speed_0_255 * 127 / 255)))

def pmd_to_depth_cents(pmd_0_127):
    """FB-01 PMD(0-127) → swbank depth_cents への近似変換(0-600セント)"""
    return round(pmd_0_127 * 600 / 127)

def transpose_to_fine(transpose_signed):
    """FB-01 transpose(signed byte, 100cents単位) → fine_transpose(セント、±1200でクリップ)"""
    cents = transpose_signed * 100
    return max(-1200, min(1200, cents))

def convert(src_path, dst_hwbank_path, dst_swbank_path, bank_no=0):
    data = Path(src_path).read_bytes()
    assert len(data) == HEADER_SIZE + VOICE_COUNT * VOICE_SIZE, \
        f"Expected {HEADER_SIZE + VOICE_COUNT*VOICE_SIZE}, got {len(data)}"

    bank_name = data[:8].decode('ascii', errors='replace').rstrip()
    src_name  = Path(src_path).stem

    hw_patches = []
    sw_patches = []
    prog_no = 0
    for i in range(VOICE_COUNT):
        off    = HEADER_SIZE + i * VOICE_SIZE
        vbytes = data[off:off + VOICE_SIZE]
        name_bytes = vbytes[:7]

        if not is_valid_name(name_bytes):
            continue

        voice = parse_voice(vbytes)
        pname = voice["name"]

        hw_patches.append({
            "prog": prog_no,
            "name": pname,
            "FB":   voice["FB"],
            "ALG":  voice["ALG"],
            "AMS":  voice["AMS"],
            "PMS":  voice["PMS"],
            "ops":  voice["ops"],
            "sw_bank": bank_no,
            "sw_prog": prog_no,
        })
        sw = voice["sw"]
        sw_patches.append({
            "prog": prog_no,
            "name": pname,
            "sw": {
                "LWF": sw["lfo_wave"],
                "LFS": sw["lfo_sync"],
                "LFM": 0,
                "LFD": 0,   # FB-01データに遅延情報なし
                "LFR": lfospeed_to_rate(sw["lfo_speed"], sw["lfo_enable"]),
                "LFI": 0,
                "depth_cents": pmd_to_depth_cents(sw["pmd"]),
            },
            "fine_transpose": transpose_to_fine(sw["transpose"]),
        })
        prog_no += 1

    hw_out = {
        "name":             f"{src_name} ({bank_name})",
        "voice_patch_type": "OPZ2",
        "op_count": 4,
        "source":   f"{Path(src_path).name} (Yamaha FB-01 ROM dump)",
        "note":     "FB-01系最上位(OPZ2)として宣言。ops[]=[M1,C1,M2,C2]順"
                    "(FB-01格納順OP#0,OP#2,OP#1,OP#3から並び替え済み)。"
                    "sw_bank/sw_progで対になるswbank(同名.swbank.json)を参照。"
                    "VEL_TL/VEL_AR/KLS_type/KLS_depth/TL_adjは対応フィールドが"
                    "存在しないため破棄。",
        "patches": hw_patches,
    }
    sw_out = {
        "name": f"{src_name} (Performance)",
        "bank": bank_no,
        "note": "FB-01のLFO速度/PMD/transposeから変換。速度・深さの換算式は"
                "実機の正確なカーブが不明なため線形近似。AMDは対応フィールドなし破棄。",
        "patches": sw_patches,
    }

    Path(dst_hwbank_path).write_text(
        json.dumps(hw_out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    Path(dst_swbank_path).write_text(
        json.dumps(sw_out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"OK {src_name}: {len(hw_patches)}音色 → {dst_hwbank_path} + {dst_swbank_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Yamaha FB-01 .dmp → FITOM_X hwbank.json + swbank.json (OPZ2グループ)")
    parser.add_argument("input",  help="*.dmp ファイル (またはディレクトリ)")
    parser.add_argument("output", help="出力先ディレクトリ")
    parser.add_argument("--bank", type=int, default=0)
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    dst.mkdir(parents=True, exist_ok=True)

    def do_convert(f):
        hw_out = dst / (f.stem + ".hwbank.json")
        sw_out = dst / (f.stem + ".swbank.json")
        convert(str(f), str(hw_out), str(sw_out), args.bank)

    if src.is_dir():
        for f in sorted(src.glob("*.dmp")):
            do_convert(f)
    else:
        do_convert(src)
