#!/usr/bin/env python3
"""VALSOUNDライブラリ(*.opn テキスト形式)→ FITOM_X hwbank.json 変換ツール

フォーマット(カンマ区切りテキスト、Shift-JIS):
  1音色 = 可変行数のテキストブロック、ブロック間は "-" の連続行(区切り線)。
    行0: パッチ名
    行1: "AL, FB,"                          (Algorithm, Feedback)
    行2-5: OP1(M1),OP2(C1),OP3(M2),OP4(C2) の各10カラム:
      AR, DR, SR, RR, SL, OL(TL), KS(KSR), ML(MUL), DT1, AMS

  値域を全パッチにわたって走査した結果(2026-07-27)、AR<=31/DR<=31/SR<=31/
  RR<=15/SL<=15/OL<=127/KS<=3/ML<=15/DT1<=7の範囲に収まり、かつキャリア
  オペレータのTLが素の状態で概ね0付近(122パッチ中114パッチで既に最小
  キャリアTL=0)であることから、N88-BASIC(86)テキスト形式(1の補数格納、
  n88basic_convert.py参照)とは異なり、**生のレジスタ値がそのまま**格納
  されていると判断した(1の補数と仮定すると代表的なベース/パーカッシブ
  系パッチのARが最遅設定になってしまい、パッチ名の傾向と矛盾する)。

  末尾列(AMS)は全122パッチ・488オペレータ行にわたって値が常に0であり、
  実質的に未使用。n88basic_convert.py/necopn_convert.pyの同一列位置に
  あるAM(0/1、LFO AM有効フラグ)と同じ位置であるため、ops[].AMへ
  マッピングする(値は常に0)。このフォーマットにはチャンネル単位の
  AMS/PMSを格納する列が無いため、hwbank側のAMS/PMSは0固定とする。

  128パッチを超える場合は複数バンクに分割し "VALSOUND Library N" として
  出力する(prog番号は各バンク内で0起点に振り直す)。

  パッチ名にマルチバイト文字を含むものは NAME_OVERRIDES で個別に
  ASCII表記へ置き換える。
"""

import json
from pathlib import Path

# OPN(3bit ALG)のキャリアオペレータ対応(necopn_convert.py/n88basic_convert.pyと同一、
# docs/manuals/swbank.mdのprog24-31対応表参照。ops[]添字: 0=M1,1=C1,2=M2,3=C2)
CARRIER_OPS_BY_ALG = {
    0: [3], 1: [3], 2: [3], 3: [3],
    4: [1, 3],
    5: [1, 2, 3],
    6: [1, 2, 3],
    7: [0, 1, 2, 3],
}

# マルチバイト名 → ASCII表記の手動対応表(元データ中12件、意味を保ちつつ
# 英数字記号のみへ置き換える)。
NAME_OVERRIDES = {
    "もわ〜": "Mowa~",
    "B.D.(要Bend)": "B.D.(ReqBend)",
    "BD808_2(要Bend)": "BD808_2(ReqBend)",
    "Heavy BD2 堅め": "Heavy BD2 Hard",
    "S.Effect 要Detune o2c(ぎゅいー〜んﾜﾜﾜﾜ)": "S.Effect ReqDetune o2c(GyuinWawawawa)",
    "アコーディオン1": "Accordion1",
    "アコーディオン2": "Accordion2",
    "アコーディオン3": "Accordion3",
    "Clarinet #2 (#1より明るい)": "Clarinet #2 (Brighter than #1)",
    "三味線 2": "Shamisen 2",
    "三味線 1": "Shamisen 1",
    "Synth 三味線": "Synth Shamisen",
}


def normalize_carrier_tl(alg, ops):
    """キャリアオペレータのTLを正規化する(n88basic_convert.py/necopn_convert.pyと同じ規則)。

    単一キャリアならそのTLを0に、複数キャリアなら最もTLが小さい
    (最も音量が大きい)オペレータのTLを0にし、他のキャリアのTLからも
    同じ量を減算して相対バランスを保つ。モジュレータのTLは変更しない。
    """
    carriers = CARRIER_OPS_BY_ALG[alg]
    min_tl = min(ops[i]["TL"] for i in carriers)
    for i in carriers:
        ops[i]["TL"] -= min_tl


def parse_op(row):
    """1OP行(10値リスト) → FmHwOp dict。生のレジスタ値のまま格納されている。"""
    ar, dr, sr, rr, sl, tl, ks, ml, dt1, ams = row[:10]
    return {
        "DT1": dt1,
        "MUL": ml,
        "TL":  tl,
        "KSR": ks,
        "AR":  ar,
        "AM":  1 if ams != 0 else 0,
        "DR":  dr,
        "SR":  sr,
        "SL":  sl,
        "RR":  rr,
    }


def split_blocks(text):
    """区切り線("-"の連続)でパッチブロックに分割する。"""
    lines = text.replace('\r\n', '\n').split('\n')
    blocks = []
    cur = []
    for line in lines:
        stripped = line.strip()
        if stripped and set(stripped) == {'-'}:
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line)
    if cur and any(l.strip() for l in cur):
        blocks.append(cur)
    return blocks


def parse_block(block):
    """1パッチ分のブロック(行リスト)を解析する。"""
    nonempty = [l for l in block if l.strip()]
    assert len(nonempty) >= 6, f"unexpected block (too few lines): {nonempty!r}"

    name = nonempty[0].strip()
    hdr = [v.strip() for v in nonempty[1].split(',') if v.strip() != '']
    assert len(hdr) == 2, f"{name}: expected 2 header fields (AL,FB), got {hdr!r}"
    alg, fb = int(hdr[0]), int(hdr[1])

    op_rows = []
    for row in nonempty[2:6]:
        vals = [v.strip() for v in row.split(',') if v.strip() != '']
        assert len(vals) == 10, f"{name}: expected 10 columns per OP row, got {vals!r}"
        op_rows.append([int(v) for v in vals])

    ops = [parse_op(r) for r in op_rows]
    normalize_carrier_tl(alg, ops)

    if name in NAME_OVERRIDES:
        name = NAME_OVERRIDES[name]

    return alg, fb, ops, name


def convert(src_path, dst_dir, bank_name_prefix="VALSOUND Library"):
    src_path = Path(src_path)
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    raw = src_path.read_bytes()
    text = raw.decode('shift_jis')
    blocks = split_blocks(text)

    patches = []
    for block in blocks:
        alg, fb, ops, name = parse_block(block)
        patches.append({"ALG": alg, "FB": fb, "ops": ops, "name": name})

    out_paths = []
    for bank_no, start in enumerate(range(0, len(patches), 128), start=1):
        chunk = patches[start:start + 128]
        bank_patches = []
        for i, p in enumerate(chunk):
            bank_patches.append({
                "prog": i,
                "name": p["name"],
                "FB":   p["FB"],
                "ALG":  p["ALG"],
                "AMS":  0,
                "PMS":  0,
                "ops":  p["ops"],
            })

        bank_name = f"{bank_name_prefix} {bank_no}"
        hwbank = {
            "name":             bank_name,
            "voice_patch_type": "OPN2",
            "source":           f"{src_path.name} (VALSOUND OPN voice text data)",
            "note":             "VALSOUNDライブラリのOPN音色テキストデータ。"
                                "ADSR/TLは生のレジスタ値のまま格納されている"
                                "(N88-BASICテキスト形式のような1の補数格納ではない、"
                                "valsound_convert.py冒頭コメント参照)。"
                                "キャリアオペレータのTLはALGに応じて正規化済み"
                                "(normalize_carrier_tl()、necopn_convert.py/"
                                "n88basic_convert.pyと同じ規則)。"
                                "チャンネルAMS/PMSは元データに格納が無いため0固定。"
                                "ops格納順は [M1, C1, M2, C2]。",
            "patches": bank_patches,
        }

        dst_path = dst_dir / f"valsound_{bank_no}.hwbank.json"
        dst_path.write_text(
            json.dumps(hwbank, indent=2, ensure_ascii=False) + '\n',
            encoding='utf-8'
        )
        out_paths.append(dst_path)
        print(f"Converted {len(bank_patches)} patches -> {dst_path} ({bank_name!r})")

    return out_paths


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="VALSOUND *.opn テキスト -> FITOM_X hwbank.json (128パッチごとに分割)"
    )
    parser.add_argument("src_path", help="VAL-SOUND.opn 等の入力ファイル")
    parser.add_argument("dst_dir",  help="出力先ディレクトリ")
    parser.add_argument("--bank-name-prefix", default="VALSOUND Library",
                         help="バンク名接頭辞 (default: 'VALSOUND Library')")
    args = parser.parse_args()

    convert(args.src_path, args.dst_dir, bank_name_prefix=args.bank_name_prefix)
