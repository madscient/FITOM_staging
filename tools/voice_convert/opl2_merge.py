#!/usr/bin/env python3
"""
OPL2 (2OP) バンク 2本 → OPL3 (4OP) バンク 1本 合成ツール

2つの OPL2 hwbank.json (フラット構造, voice_patch_type=OPL3_2) を組み合わせて
OPL3 の 4OP 音色(voice_patch_type=OPL3)を生成します。
Bank-A の Mod/Car (M1/C1) と Bank-B の Mod/Car (M2/C2) を
指定した CON4 (4OP 接続モード) と FB でひとつの 4OP バンクに合成します。

使用例:
  python3 opl2_merge.py \\
      MicroComputerNormalBank.hwbank.json \\
      DigitalNormalBank.hwbank.json \\
      MicroComputer_x_Digital.hwbank.json \\
      --con4 1

OPL3 4OP 接続モード (CON4):
  0: M1→C1→M2→C2  完全直列 (最大変調深度)
  1: (M1→C1) + (M2→C2)  2OP×2 独立並列 ← バンク合成時の推奨
  2: M1→(C1 + M2→C2)  C1と第2ペアが並列合流
  3: M1→C1 + M2 + M2→C2  3出力混合

FITOM_X hwbank.schema.json (フラット構造) フィールド対応:
  ALG   : 3bit統合 (bit0=CON1前半ペア接続, bit1=CON2後半ペア接続,
          bit2=ConnectionSEL(常に1、4OPモード有効化))
  FB    : 1stペア(M1C1)独立FB (Bank-A から取得)
  FB2   : 2ndペア(M2C2)独立FB (Bank-B から取得)
  (実機OPL3は前半・後半ペアそれぞれ独立したFBレジスタを持つため、
   FBを6bitに詰め込む旧方式ではなく、FB/FB2の2フィールドに素直に対応させる)

入力バンクのops[]は、変換元(vma_convert.py等)で既にEGT/SR/RR変換規則を
適用済みの前提とする(このツール自体はSR/RR/EGTの再変換は行わない)。
"""

import json, argparse, sys
from pathlib import Path

DEFAULT_CON4 = 1

def load_opl2_bank(path):
    d = json.load(open(path))
    if d.get('op_count', 2) != 2:
        raise ValueError(f"{path}: OPL2 (op_count=2) バンクが必要です (got op_count={d.get('op_count')})")
    vpt = d.get('voice_patch_type')
    if vpt not in ('OPL', 'OPL2', 'OPL3_2'):
        raise ValueError(f"{path}: OPL2系バンクが必要です (got voice_patch_type={vpt})")
    return d

def merge_banks(bank_a, bank_b, alg_a, alg_b):
    """bank_a (M1/C1ペア) と bank_b (M2/C2ペア) を合成する。
    両バンクの同一prog番号を対応させる。片方に存在しないprogはスキップ。
    """
    patches_a = {p['prog']: p for p in bank_a['patches']}
    patches_b = {p['prog']: p for p in bank_b['patches']}

    progs = sorted(set(patches_a.keys()) & set(patches_b.keys()))
    if not progs:
        raise ValueError("共通するプログラム番号がありません")

    patches_out = []
    for prog in progs:
        pa = patches_a[prog]
        pb = patches_b[prog]

        ops_a = pa['ops']  # [Mod, Car] = [M1, C1]
        ops_b = pb['ops']  # [Mod, Car] = [M2, C2]

        fb_a = pa.get('FB', 0)
        fb_b = pb.get('FB', 0)

        name_a = pa.get('name', f'Prog{prog}')
        name_b = pb.get('name', f'Prog{prog}')
        name = f"{name_a[:8].rstrip()}x{name_b[:8].rstrip()}" if name_a != name_b else name_a

        cnt0 = alg_a & 1
        cnt1 = alg_b & 1
        # hw.ALG: bit0=CON1(前半ペア接続)/bit1=CON2(後半ペア接続)のみ。bit2は未使用。
        # ConnectionSEL(4OP結合有効化)はext.ALG_EXTに分離して持つ(2026年7月訂正)。
        # OPL2バンク2本の単純合成では、前半・後半が独立してキーオン制御される
        # 旧FITOM互換動作(ConnectionSEL=0)が正しい。
        alg_enc = (cnt1 << 1) | cnt0

        patch = {
            "prog": prog,
            "name": name[:24],
            "FB":   fb_a & 7,   # 前半ペア(M1/C1)独立FB
            "FB2":  fb_b & 7,   # 後半ペア(M2/C2)独立FB
            "ALG":  alg_enc,
            "ext":  {"ALG_EXT": 0},  # ConnectionSEL=0(前半・後半独立キーオン、合成パッチの標準)
            "ops": [
                ops_a[0],   # ops[0] = M1 (Bank-A の Mod)
                ops_a[1],   # ops[1] = C1 (Bank-A の Car)
                ops_b[0],   # ops[2] = M2 (Bank-B の Mod)
                ops_b[1],   # ops[3] = C2 (Bank-B の Car)
            ],
        }
        # sw_bank/sw_progはBank-Aを優先して引き継ぐ
        if 'sw_bank' in pa and 'sw_prog' in pa:
            patch['sw_bank'] = pa['sw_bank']
            patch['sw_prog'] = pa['sw_prog']

        patches_out.append(patch)

    return patches_out

def run(args):
    bank_a = load_opl2_bank(args.bank_a)
    bank_b = load_opl2_bank(args.bank_b)

    name_a  = Path(args.bank_a).stem
    name_b  = Path(args.bank_b).stem
    src_name = args.name or f"{name_a} x {name_b}"

    alg_a_default = bank_a['patches'][0].get('ALG', 0) if bank_a['patches'] else 0
    alg_a = args.alg_a if args.alg_a is not None else alg_a_default

    alg_b_default = bank_b['patches'][0].get('ALG', 0) if bank_b['patches'] else 0
    alg_b = args.alg_b if args.alg_b is not None else alg_b_default

    patches = merge_banks(bank_a, bank_b, alg_a, alg_b)

    out = {
        "name":             src_name,
        "voice_patch_type": "OPL3",
        "op_count":         4,
        "source":           (f"{Path(args.bank_a).name} [M1/C1]"
                             f" + {Path(args.bank_b).name} [M2/C2]"),
        "note": (
            f"OPL2バンク2本の合成による4OPパッチ。CON4={args.con4}相当"
            f"(ALG: cnt1={alg_b & 1}(後半ペア), cnt0={alg_a & 1}(前半ペア))。"
            f"ext.ALG_EXT(ConnectionSEL)=0固定"
            f"(旧FITOM互換動作: 前半・後半ペアが独立してキーオン制御される)。"
            f"FB/FB2は各patchごとにBank-A/Bから独立設定。"
            f"ops[0/1]=Bank-A(M1/C1), ops[2/3]=Bank-B(M2/C2)。"
            f"各opsのSR/RR/EGTは合成元バンクの変換結果をそのまま引き継ぐ"
            f"(このツール自体はEGT/SR/RRの再変換を行わない)。"
        ),
        "patches": patches,
    }

    dst = Path(args.output)
    if dst.is_dir():
        dst = dst / (src_name.replace(' ', '_') + '.hwbank.json')
    dst.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"OK: {len(patches)}音色 → {dst}")
    print(f"    M1/C1: {name_a}  (FB=Bank-Aから)")
    print(f"    M2/C2: {name_b}  (FB2=Bank-Bから)")
    print(f"    CON4={args.con4}, 前半ペアALG={alg_a}, 後半ペアALG={alg_b}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OPL2 バンク 2本 → OPL3 4OP バンク 合成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python3 opl2_merge.py \\
      banks/OPL2/ma2_vma/MicroComputerNormalBank.hwbank.json \\
      banks/OPL2/ma2_vma/DigitalNormalBank.hwbank.json \\
      banks/OPL3/MicroComputer_x_Digital.hwbank.json

CON4 接続モード:
  0 : M1→C1→M2→C2  完全直列
  1 : (M1→C1) + (M2→C2)  独立並列 [デフォルト / バンク合成推奨]
  2 : M1→(C1+M2→C2)  C1とM2→C2の並列合流
  3 : M1→C1 + M2 + M2→C2  3出力混合
        """)
    parser.add_argument("bank_a",  help="Bank-A (M1/C1ペア用) OPL2 hwbank.json")
    parser.add_argument("bank_b",  help="Bank-B (M2/C2ペア用) OPL2 hwbank.json")
    parser.add_argument("output",  help="出力先 .hwbank.json (ディレクトリも可)")
    parser.add_argument("--con4",  type=int, default=DEFAULT_CON4,
                        choices=[0,1,2,3],
                        help=f"4OP 接続モード (デフォルト: {DEFAULT_CON4}=独立並列)")
    parser.add_argument("--alg-a", dest="alg_a", type=int, default=None,
                        choices=[0,1],
                        help="前半ペア(M1→C1)の接続 0=FM 1=AM (デフォルト: Bank-Aから引き継ぎ)")
    parser.add_argument("--alg-b", dest="alg_b", type=int, default=None,
                        choices=[0,1],
                        help="後半ペア(M2→C2)の接続 0=FM 1=AM (デフォルト: Bank-Bから引き継ぎ)")
    parser.add_argument("--name",  type=str, default=None,
                        help="出力バンク名 (デフォルト: 'BankA x BankB')")
    args = parser.parse_args()
    run(args)
