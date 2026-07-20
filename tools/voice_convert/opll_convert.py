#!/usr/bin/env python3
"""
YM2413(OPLL)実機レジスタダンプ(8byte/音色) → FITOM_X hwbank.json 変換ツール

対応入力:
  --pss140 <patches.txt> --pss140-names <names.txt>
    PSS-140ダンプ。1行8byte、"$XX $XX ... $XX"形式(16進2桁、$プレフィックス)。
    行順=プログラム番号順。名前は同じ行順の1行1名前のテキストファイルで別途与える。
    (https://github.com/plgDavid/misc/blob/master/OPLL%20Synth%20Patches/
     pss140_patches.txt + pss140_patches_names.txt)
  --shs10 <patches.txt>
    SHS-10ダンプ。C配列風 "/*NN*/ {0xXX,0xXX,...,0xXX},//名前" 形式。
    "//名前"コメントから名前を取得。ファイル末尾の"last christmas demo"以降の
    重複エントリ(コメントなし/インデックスなしの再掲プロック)は無視する。
    (https://github.com/plgDavid/misc/blob/master/OPLL%20Synth%20Patches/
     shs10_patches.txt)

YM2413カスタム音色レジスタ(R#0-R#7、8byte)フォーマット:
  R#0: AM1[7]|VIB1[6]|EGT1[5]|KSR1[4]|MULT1[3:0]   (モジュレータ)
  R#1: AM2[7]|VIB2[6]|EGT2[5]|KSR2[4]|MULT2[3:0]   (キャリア)
  R#2: KSL1[7:6]|TL1[5:0]                          (モジュレータ)
  R#3: KSL2[7:6]|(bit5未使用)|DC[4]|DM[3]|FB[2:0]  (DM=モジュレータ波形,DC=キャリア波形。
                                                    bit5は実データ解析で常に未使用と確認)
  R#4: AR1[7:4]|DR1[3:0]                           (モジュレータ)
  R#5: AR2[7:4]|DR2[3:0]                           (キャリア)
  R#6: SL1[7:4]|RR1[3:0]                           (モジュレータ)
  R#7: SL2[7:4]|RR2[3:0]                           (キャリア)

FITOM_X hwbank.schema.json (フラット構造)へのマッピング:
  ops[0]=モジュレータ、ops[1]=キャリア。MULT→MUL、KSR/VIB/AM/KSL直接対応。
  DM/DC → ops[i].WS(0/1)。FB → hw.FB(3bit)。hw.ALG=0固定(YM2413は音色ごとの
  接続切替が無く、常にモジュレータ→キャリアのFM接続のみ)。
  AR/DR/TLは実機レジスタ値(4bit/4bit/6bit)をそのまま格納すると、FITOM_X
  ランタイム側の読み出し(OPLL_new.cpp、格納値を>>1して5bit/5bit/7bit相当の
  「上位ビット表現」から実際のレジスタ幅を切り出す設計)によって値が半分に
  なってしまうため、<<1して格納する(OPL系と同じ規約、docs/CLAUDE.md 3.17)。

  SR/RR/実機EGTビットの変換規則(OPLはCOPL::updateVoiceのみで完結する静的な
  一度きりの書き込みだが、OPLLはupdateVoice+updateKeyの2段階書き込みで、
  キーオン中とキーオフ時でRRレジスタへ書く値が動的に切り替わる点が異なる。
  docs/voice-parameter-reference.md「OPLL系」節参照):
    - キーオン中、SR>0(実機EGTビット=0/パーカッシブ)ならSRの値(4bit変換)を
      RRレジスタに書く。
    - キーオフ時は常に実機EGTビット=1にして、FITOMのRRの値をそのまま
      RRレジスタに書く(SRが何であったかに関わらず、RRは常にキーオフの
      挙動を決める)。
  したがって、OPL系とは異なりFITOMの`RR`フィールドはEGTビット/SR分岐に
  関わらず常に実機で参照されるため、変換元の実機EGTビット値に関係なく、
  常に`RR = 変換元RRレジスタ値`(シフトなし)を格納しなければならない
  (`SR`のみ実機EGTビットに応じて0または変換元RRレジスタ<<1)。
  2026年7月20日、既存のbanks/OPLL/opll_presets.hwbank.jsonが、この
  OPLL特有の規則を無視してOPL系と同じ「EGTビット=0(パーカッシブ)ならRR=0」
  規則で変換されていたためRRが失われ、パーカッシブ側に倒れた音色が
  キーオフで消音しないバグを修正した(該当スクリプトは元々このリポジトリに
  存在せず、由来不明だったため、hwbank.json自身のsourceフィールドが指す
  実機レジスタダンプから本スクリプトで再変換した)。

  なお、変換元のRRレジスタ自体が0の音色も存在し(実機データそのものが
  そうなっている)、この場合はキャリアが`SR=0`かつ`RR=0`のまま(=実機でも
  事実上消音しない)になる。モジュレータ側はそのまま(音声出力に寄与しない
  ため実害なし)、キャリア側のみ`MIN_CARRIER_RR`へ補正する
  (2026年7月20日追加)。
"""

import json, re, argparse
from pathlib import Path

SW_BANK = 0
SW_PROG = 27   # 2op ALG=0(モジュレータ+キャリア)固定、既存データの値を踏襲
MIN_CARRIER_RR = 1  # SR=0かつRR=0(実機で事実上消音しない)になるキャリアに適用する最小値


def parse_op(byte01, byte23, byte45, byte67, op_index):
    """op_index: 0=モジュレータ, 1=キャリア"""
    b0 = byte01[op_index]
    egt = (b0 >> 5) & 1
    ksl = (byte23[op_index] >> 6) & 3
    tl_or_fb = byte23[op_index] & 0x3F if op_index == 0 else 0
    ar = (byte45[op_index] >> 4) & 0xF
    dr = byte45[op_index] & 0xF
    sl = (byte67[op_index] >> 4) & 0xF
    rr_reg = byte67[op_index] & 0xF

    sr = (rr_reg << 1) if egt == 0 else 0
    rr = rr_reg   # OPLLはキーオフ時に常にRRレジスタへ直接反映されるため、
                  # 実機EGTビットの値に関わらず常に変換元RRレジスタ値を格納する

    op = {
        "MUL":  b0 & 0xF,
        "VIB":  (b0 >> 6) & 1,
        "EGT":  0,   # OPL系では無関係、常に0
        "KSR":  (b0 >> 4) & 1,
        "SR":   sr,
        "RR":   rr,
        "DR":   dr << 1,
        "AR":   ar << 1,
        "SL":   sl,
        "TL":   tl_or_fb << 1,
        "KSL":  ksl,
        "AM":   (b0 >> 7) & 1,
        "WS":   0,  # DM/DCで後から上書き
    }
    return op


def parse_instrument(b):
    """8byte(list[int])のYM2413カスタム音色レジスタ → (mod_op, car_op, fb)"""
    byte01 = (b[0], b[1])
    byte23 = (b[2], b[3])
    byte45 = (b[4], b[5])
    byte67 = (b[6], b[7])

    mod = parse_op(byte01, byte23, byte45, byte67, 0)
    car = parse_op(byte01, byte23, byte45, byte67, 1)

    # OPLLはALG=0固定(モジュレータ→キャリアのFM接続のみ)でキャリアは常にcar側。
    # 変換元RRレジスタが0の場合、SRの値に関わらずキーオフ時に実機へ
    # RR=0が書き込まれ事実上消音しなくなるため、キャリアに限りRRへ
    # 最小値を補う(モジュレータ側は音声出力に寄与しないため対象外。
    # 2026年7月20日追加・7月20日SR分岐を撤廃、docs/CLAUDE.md 3.24参照)。
    if car.get("AR", 0) > 0 and car["RR"] == 0:
        car["RR"] = MIN_CARRIER_RR

    dm = (b[3] >> 3) & 1
    dc = (b[3] >> 4) & 1
    mod["WS"] = dm
    car["WS"] = dc
    fb = b[3] & 0x7

    return mod, car, fb


def make_patch(prog, name, mod, car, fb):
    return {
        "prog": prog,
        "name": name,
        "FB":   fb,
        "ALG":  0,
        "ops":  [mod, car],
        "sw_bank": SW_BANK,
        "sw_prog": SW_PROG,
    }


def parse_pss140(patches_path, names_path, prog_start=0):
    lines = [l.strip() for l in Path(patches_path).read_text(encoding='utf-8').splitlines() if l.strip()]
    names = [l.strip() for l in Path(names_path).read_text(encoding='utf-8').splitlines() if l.strip()]
    assert len(lines) == len(names), f"patches({len(lines)}) != names({len(names)})"

    patches = []
    for i, (line, name) in enumerate(zip(lines, names)):
        vals = [int(tok.lstrip('$'), 16) for tok in line.split()]
        assert len(vals) == 8, f"line {i}: expected 8 bytes, got {len(vals)}: {line}"
        mod, car, fb = parse_instrument(vals)
        patches.append(make_patch(prog_start + i, name, mod, car, fb))
    return patches


SHS10_LINE_RE = re.compile(
    r'\{\s*((?:0x[0-9a-fA-F]{2}\s*,\s*){7}0x[0-9a-fA-F]{2})\s*\}\s*,\s*//\s*(.+)'
)


def parse_shs10(patches_path, prog_start):
    text = Path(patches_path).read_text(encoding='utf-8')
    # "last christmas demo" 以降は重複エントリ(コメント本文中の再掲)なので除外
    main_block = text.split('last christmas demo')[0]

    patches = []
    prog = prog_start
    for line in main_block.splitlines():
        m = SHS10_LINE_RE.search(line)
        if not m:
            continue
        vals = [int(tok.strip(), 16) for tok in m.group(1).split(',')]
        name = m.group(2).split('(')[0].strip()  # 末尾の "(CPU lowers...)" 等の注記を除去
        mod, car, fb = parse_instrument(vals)
        patches.append(make_patch(prog, name, mod, car, fb))
        prog += 1
    return patches


def convert(pss140_patches, pss140_names, shs10_patches, dst_path):
    patches = []
    patches += parse_pss140(pss140_patches, pss140_names, prog_start=0)
    patches += parse_shs10(shs10_patches, prog_start=100)

    out = {
        "name": "OPLL Presets (PSS-140 + SHS-10)",
        "voice_patch_type": "OPLL",
        "source": [
            "https://github.com/plgDavid/misc/blob/master/OPLL%20Synth%20Patches/pss140_patches.txt",
            "https://github.com/plgDavid/misc/blob/master/OPLL%20Synth%20Patches/pss140_patches_names.txt",
            "https://github.com/plgDavid/misc/blob/master/OPLL%20Synth%20Patches/shs10_patches.txt",
        ],
        "note": "PSS-140(100パッチ、prog 0-99) + SHS-10(25パッチ、prog 100-124)統合。"
                "実機EGTビット/RRレジスタをFITOMのSR/RRフィールドに変換する際、"
                "OPLLはキーオフ時に常にRRレジスタへFITOMのRR値を直接書き込む"
                "(OPL系と異なりSR分岐に関わらずRRが常に参照される)ため、"
                "実機EGTビットの値に関わらず常にRR=変換元RRレジスタ値を格納する"
                "(SRのみ実機EGTビット=0/パーカッシブの場合に変換元RRレジスタ<<1、"
                "EGTビット=1/サステインなら0)。ops[i].EGTフィールド自体はOPL系"
                "では無関係のため常に0。Carrier TLはチャンネル音量レジスタ"
                "(R$30-R$38)で制御されるため0固定。"
                f"変換元RRレジスタが0でキャリアがSR=0かつRR=0(消音しない状態)に"
                f"なる場合はRR={MIN_CARRIER_RR}へ補正(モジュレータ側は対象外)。",
        "patches": patches,
    }
    Path(dst_path).write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"OK: {len(patches)}音色 → {dst_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="YM2413(OPLL) レジスタダンプ(PSS-140+SHS-10) → FITOM_X hwbank.json")
    parser.add_argument("--pss140", required=True, help="pss140_patches.txt")
    parser.add_argument("--pss140-names", required=True, help="pss140_patches_names.txt")
    parser.add_argument("--shs10", required=True, help="shs10_patches.txt")
    parser.add_argument("output", help="出力先 hwbank.json")
    args = parser.parse_args()

    convert(args.pss140, args.pss140_names, args.shs10, args.output)
