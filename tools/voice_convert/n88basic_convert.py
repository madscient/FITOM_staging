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
    各OP行10カラムはパラメータごとの列方向格納(necopn.binと同じグループ順):
    [0] AR  ← 1's complement (実値 = 31 - 生値)
    [1] DR  ← 1's complement (実値 = 31 - 生値)
    [2] SR  ← 1's complement (実値 = 31 - 生値)
    [3] RR  ← 1's complement (実値 = 15 - 生値)
    [4] SL  ← 1's complement (実値 = 15 - 生値)
    [5] TL  ← 1's complement (実値 = 127 - 生値)
    [6] KSR (生値のまま、2bit)
    [7] MUL (生値のまま、4bit)
    [8] DT1/AM合成 (生値が負の場合のみ、DT1が[9]側へ退避されAM情報は失われる。
        詳細は下記)
    [9] [8]が負の場合のDT1退避先、[8]が非負の場合はAM(0/1)

  [8]/[9]の関係(実データとの照合により判明、2026-07-27):
    [8] >= 0 の場合: DT1 = [8]、AM = ([9] != 0)
    [8] <  0 の場合: DT1 = [9]、AM = 0
    (N88-BASIC側の内部表現で、DT1/AMを1バイトに合成する際に符号付き扱いで
    オーバーフローしたと見られる古いエディタの挙動。実際に変換済みだった
    dev/fmvoice/VOICE/OPNA/n88preset.fmbをopn2ini.plでデコードした結果と
    全82音色・全フィールドが一致することを確認済み)。

  参考: https://madscient.hatenablog.jp/entry/2013/07/08/051133

出力:
  FITOM_X hwbank.json (voice_patch_type: OPN2)
  ops[] 格納順: [M1, C1, M2, C2]
"""

import json, os, sys, argparse
from pathlib import Path

# OPN(3bit ALG)のキャリアオペレータ対応(necopn_convert.pyと同一、
# docs/manuals/swbank.mdのprog24-31対応表参照。ops[]添字: 0=M1,1=C1,2=M2,3=C2)
CARRIER_OPS_BY_ALG = {
    0: [3], 1: [3], 2: [3], 3: [3],
    4: [1, 3],
    5: [1, 2, 3],
    6: [1, 2, 3],
    7: [0, 1, 2, 3],
}

def normalize_carrier_tl(alg, ops):
    """キャリアオペレータのTLを正規化する(necopn_convert.pyと同じ規則)。

    単一キャリアならそのTLを0に、複数キャリアなら最もTLが小さい
    (最も音量が大きい)オペレータのTLを0にし、他のキャリアのTLからも
    同じ量を減算して相対バランスを保つ。モジュレータのTLは変更しない。
    """
    carriers = CARRIER_OPS_BY_ALG[alg]
    min_tl = min(ops[i]["TL"] for i in carriers)
    for i in carriers:
        ops[i]["TL"] -= min_tl


def parse_op(row):
    """1OP行(10値リスト) → FmHwOp dict
    ADSR/TL は 1's complement で格納されているため反転してレジスタ値に変換する。
    """
    ar, dr, sr, rr, sl, tl, ksr, mul, c8, c9 = row[:10]
    if c8 < 0:
        dt1, am = c9, 0
    else:
        dt1, am = c8, (1 if c9 != 0 else 0)
    return {
        "DT1": dt1,
        "MUL": mul,
        "TL":  0x7F - tl,   # 7bit 反転
        "KSR": ksr,
        "AR":  0x1F - ar,   # 5bit 反転
        "AM":  am,
        "DR":  0x1F - dr,   # 5bit 反転
        "SR":  0x1F - sr,   # 5bit 反転
        "SL":  0x0F - sl,   # 4bit 反転
        "RR":  0x0F - rr,   # 4bit 反転
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

        ops = [op_m1, op_c1, op_m2, op_c2]
        normalize_carrier_tl(alg, ops)

        name = names[i] if names else fname
        patches.append({
            "prog": i,
            "name": name,
            "FB":   fb,
            "ALG":  alg,
            "AMS":  ams,
            "PMS":  fms,
            "ops":  ops,
        })

    hwbank = {
        "name":             bank_name,
        "voice_patch_type": "OPN2",
        "source":           str(src_dir),
        "note":             "N88-BASIC(86)のOPN音色テキストデータ。"
                            "ADSR/TLはN88-BASIC格納値(1's complement)からレジスタ値に変換済み。"
                            "キャリアオペレータのTLはALGに応じて正規化済み"
                            "(normalize_carrier_tl()、necopn_convert.pyと同じ規則)。"
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
