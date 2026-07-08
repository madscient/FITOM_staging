#!/usr/bin/env python3
"""
N88-BASIC(86) OPN音色テキストファイル → FITOM_X hwbank.json 変換ツール

フォーマット（N88-BASIC(86)テキスト版）:
  1音色 = 1ファイル (ファイル名が16進2桁のプログラム番号)
  5行 × 10カラム のカンマ区切りテキスト、末尾 0x1A(EOF)

  行0 (チャンネル行):
    [0] FB/ALG packed  (D5-3=FB, D2-0=ALG)
    [1] AMS/FMS packed (D5-4=AMS, D2-0=FMS/PMS)
    [2-9] 未使用 (0固定)

  行1〜4 (OP行): OP1(M1), OP2(C1), OP3(M2), OP4(C2)
    バイナリと同一のバイト値をカンマ区切りで展開したもの:
    [0] DT1/MUL packed  (D6-4=DT1, D3-0=MUL)
    [1] TL              (D6-0) ← 1's complement (反転値で格納)
    [2] KSR/AR packed   (D7-6=KSR, D4-0=AR) ← AR は 1's complement
    [3] AM/DR packed    (D7=AM, D4-0=DR) ← DR は 1's complement
    [4] SR              (D4-0) ← 1's complement
    [5] SL/RR packed    (D7-4=SL, D3-0=RR) ← SL/RR ともに 1's complement

  N88-BASIC(86)はADSR/TLをユーザー向け値（OPNレジスタ値の1's complement）で
  格納しているため、読み出し時にビット反転してレジスタ値に変換する必要がある。
  DT1/MUL/KSR/AMは方向が同じなので反転不要。

  参考: https://madscient.hatenablog.jp/entry/2013/07/08/051133

出力:
  FITOM_X hwbank.json (voice_patch_type: OPN2)
  ops[] 格納順: [M1, C1, M2, C2]
"""

import json, os, sys, argparse
from pathlib import Path


def parse_op(row):
    """1OP行(10値リスト) → FmHwOp dict
    ADSR/TL は 1's complement で格納されているため反転してレジスタ値に変換する。
    """
    b0, b1, b2, b3, b4, b5 = row[0], row[1], row[2], row[3], row[4], row[5]
    return {
        "DT1":  (b0 >> 4) & 0x07,          # 反転不要
        "MUL":   b0 & 0x0F,                 # 反転不要
        "TL":   (~b1) & 0x7F,               # 7bit 反転
        "KSR":  (b2 >> 6) & 0x03,           # 反転不要
        "AR":   (~b2) & 0x1F,               # 5bit 反転
        "AM":   (b3 >> 7) & 0x01,           # 反転不要
        "DR":   (~b3) & 0x1F,               # 5bit 反転
        "SR":   (~b4) & 0x1F,               # 5bit 反転
        "SL":   (~(b5 >> 4)) & 0x0F,        # 4bit 反転 (上位4bit)
        "RR":   (~b5) & 0x0F,               # 4bit 反転 (下位4bit)
    }


def parse_file(path):
    """1音色ファイルを読み込んで行リストを返す"""
    data = Path(path).read_bytes().rstrip(b'\x1a').decode('ascii')
    rows = []
    for line in data.replace('\r\n', '\n').strip().split('\n'):
        vals = [v.strip() for v in line.split(',') if v.strip()]
        if vals:
            rows.append([int(v) for v in vals])
    assert len(rows) == 5, f"{path}: expected 5 rows, got {len(rows)}"
    return rows


def convert(src_dir, dst_path, names=None, bank_name="N88-BASIC Preset"):
    src_dir = Path(src_dir)
    fnames = sorted(f for f in os.listdir(src_dir) if not f.startswith('.'))

    if names is not None:
        assert len(names) == len(fnames), \
            f"names count {len(names)} != file count {len(fnames)}"

    patches = []
    for i, fname in enumerate(fnames):
        rows = parse_file(src_dir / fname)

        fb_alg  = rows[0][0]
        ams_fms = rows[0][1]
        alg =  fb_alg & 0x07
        fb  = (fb_alg >> 3) & 0x07
        fms =  ams_fms & 0x07
        ams = (ams_fms >> 4) & 0x03

        op_m1 = parse_op(rows[1])  # OP1 = M1
        op_c1 = parse_op(rows[2])  # OP2 = C1
        op_m2 = parse_op(rows[3])  # OP3 = M2
        op_c2 = parse_op(rows[4])  # OP4 = C2

        name = names[i] if names else fname
        patches.append({
            "prog": i,
            "name": name,
            "FB":   fb,
            "ALG":  alg,
            "AMS":  ams,
            "PMS":  fms,
            "ops":  [op_m1, op_c1, op_m2, op_c2],
        })

    hwbank = {
        "name":             bank_name,
        "voice_patch_type": "OPN2",
        "source":           str(src_dir),
        "note":             "N88-BASIC(86)のOPN音色テキストデータ。"
                            "ADSR/TLはN88-BASIC格納値(1's complement)からレジスタ値に変換済み。"
                            "ops格納順は [M1, C1, M2, C2]。",
        "patches": patches,
    }

    Path(dst_path).write_text(
        json.dumps(hwbank, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8'
    )
    print(f"Converted {len(patches)} patches -> {dst_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="N88-BASIC(86) OPN音色テキスト -> FITOM_X hwbank.json"
    )
    parser.add_argument("src_dir",  help="音色ファイルが入ったディレクトリ")
    parser.add_argument("dst_path", help="出力 .hwbank.json ファイルパス")
    parser.add_argument("--names",  help="パッチ名一覧テキストファイル (1行1名)")
    parser.add_argument("--bank-name", default="N88-BASIC Preset",
                        help="バンク名 (default: 'N88-BASIC Preset')")
    args = parser.parse_args()

    names = None
    if args.names:
        names = Path(args.names).read_text(encoding='utf-8').splitlines()

    convert(args.src_dir, args.dst_path, names=names, bank_name=args.bank_name)
