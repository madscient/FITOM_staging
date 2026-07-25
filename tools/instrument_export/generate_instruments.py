#!/usr/bin/env python3
"""FITOM_X の config/profiles/*.profile.json から、MIDIシーケンサー用の
インストゥルメント定義ファイル(Cakewalk/Sekaiju用 .ins、DOMINO用 .xml)を
生成する汎用変換スクリプト。

対応するCC#0(Bank Select MSB)の意味は docs/CLAUDE.md 3.2節、
docs/manuals/README.md の対応表を参照。

使い方:
    python3 generate_instruments.py                     # 全プロファイルを変換
    python3 generate_instruments.py --profile config/profiles/unified_preset.profile.json
    python3 generate_instruments.py --out-dir docs/instruments
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape_text


def xml_escape(s: str) -> str:
    """XML属性値として安全な文字列に変換する(属性値中の " も含めてエスケープ)。"""
    return _xml_escape_text(s, {'"': "&quot;"})

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILES_DIR = REPO_ROOT / "config" / "profiles"
DEFAULT_OUT_DIR = REPO_ROOT / "docs" / "instruments"

# docs/CLAUDE.md 3.2節 VoicePatchType(CC#0直接モード値)。
# "OPN"/"OPM"/"OPL2"は統合前の旧プロファイル(emulator_*/hw_*)が使う旧称で、
# 参照先hwbank.jsonの実体は同一ファイルが新プロファイルでOPN2/OPZ/OPL3_2として
# 参照されていることを確認済み(2026年7月26日、本スクリプト作成時に照合)。
GROUP_CC0_HW = {
    "OPN2": 17, "OPN": 17,
    "OPZ": 26, "OPM": 26,
    "OPL3_2": 34, "OPL2": 34,
    "OPL_RHY": 35,
    "OPLL": 40,
    "OPL3": 48,
    "SSG": 64,
    "AWM": 84,
}
# pcm_banks[] 経由(ADPCM系、hw_banksとは別配列)
GROUP_CC0_PCM = {
    "ADPCMB": 81,
    "ADPCMA": 82,
}
CC0_NORMAL = 0     # patch_banks[] (通常モード)
CC0_RHYTHM = 112   # drum_banks[] (ドラムキット)


@dataclass(frozen=True)
class Entry:
    cc0: int
    cc32: int
    prog: int
    name: str


@dataclass(frozen=True)
class DrumKit:
    cc32: int
    name: str
    notes: "list[tuple[int, str]] | None"  # None = type:direct (個別ノート名なし)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as f:
        return json.load(f)


def resolve(base_dir: Path, rel: str) -> Path:
    return (base_dir / rel).resolve()


def fallback_name(prefix: str, num: int) -> str:
    return f"{prefix} {num}"


def resolve_pcm_entries(data: dict, bank_dir: Path) -> list[tuple[int, str]]:
    """pcmbank.json から (entry_no, name) の一覧を得る。
    entries[]を直接持つ場合はそれを使い、adpcm_json参照形式の場合は
    参照先JSONのentries配列インデックスをentry_noとして自動採番する
    (PatchManagerの実装に合わせる。banks/PCM/common/*.pcmbank.json参照)。
    """
    if "entries" in data:
        return [
            (e["entry_no"], e.get("name") or fallback_name("Entry", e["entry_no"]))
            for e in data["entries"]
        ]
    if "adpcm_json" in data:
        ref_path = resolve(bank_dir, data["adpcm_json"])
        ref = load_json(ref_path)
        return [
            (i, e.get("name") or fallback_name("Entry", i))
            for i, e in enumerate(ref.get("entries", []))
        ]
    return []


def collect_melodic_entries(profile: dict, profile_dir: Path, warn) -> list[Entry]:
    entries: list[Entry] = []
    banks = profile.get("banks", {})

    for pb in banks.get("patch_banks", []):
        path = resolve(profile_dir, pb["file"])
        data = load_json(path)
        for p in data.get("patches", []):
            entries.append(Entry(CC0_NORMAL, pb["bank"], p["prog"],
                                  p.get("name") or fallback_name("Patch", p["prog"])))

    for hb in banks.get("hw_banks", []):
        if hb.get("role") == "builtin_swpatch_meta":
            continue  # ユーザーが音色として直接選べないメタバンク(docs/CLAUDE.md 3.6)
        group = hb["group"]
        if group not in GROUP_CC0_HW:
            warn(f"未知のhw_banks group '{group}' (bank={hb.get('bank')}) をスキップしました")
            continue
        cc0 = GROUP_CC0_HW[group]
        path = resolve(profile_dir, hb["file"])
        data = load_json(path)
        for p in data.get("patches", []):
            entries.append(Entry(cc0, hb["bank"], p["prog"],
                                  p.get("name") or fallback_name("Patch", p["prog"])))

    for pb in banks.get("pcm_banks", []):
        group = pb["group"]
        if group not in GROUP_CC0_PCM:
            warn(f"未知のpcm_banks group '{group}' (bank={pb.get('bank')}) をスキップしました")
            continue
        cc0 = GROUP_CC0_PCM[group]
        path = resolve(profile_dir, pb["file"])
        data = load_json(path)
        for entry_no, name in resolve_pcm_entries(data, path.parent):
            entries.append(Entry(cc0, pb["bank"], entry_no, name))

    return entries


def collect_drum_kits(profile: dict, profile_dir: Path) -> list[DrumKit]:
    kits: list[DrumKit] = []
    for db in profile.get("banks", {}).get("drum_banks", []):
        path = resolve(profile_dir, db["file"])
        data = load_json(path)
        name = db.get("name") or data.get("name") or fallback_name("Drum Kit", db["prog"])
        notes = None
        if data.get("type") == "routed":
            notes = [
                (n["note"], n.get("name") or fallback_name("Note", n["note"]))
                for n in data.get("notes", [])
            ]
        kits.append(DrumKit(db["prog"], name, notes))
    return kits


# ---------------------------------------------------------------------------
# Sekaiju / Cakewalk .ins 出力
# ---------------------------------------------------------------------------

def _ins_sanitize(name: str) -> str:
    return name.replace("[", "(").replace("]", ")").replace("\r", "").replace("\n", " ").strip()


GM_CONTROLLER_NAMES = [
    (0, "Bank Select MSB"), (1, "Modulation Depth"), (5, "Portamento Time"),
    (6, "Data Entry MSB"), (7, "Channel Volume"), (10, "Pan"), (11, "Expression"),
    (32, "Bank Select LSB"), (38, "Data Entry LSB"), (64, "Hold1"),
    (65, "Portamento On/Off"), (66, "Sostenuto"), (67, "Soft"),
    (91, "Reverb Send Level"), (93, "Chorus Send Level"),
    (100, "RPN LSB"), (101, "RPN MSB"),
    (120, "All Sound Off"), (121, "Reset All Controller"), (123, "All Note Off"),
]
GM_RPN_NAMES = [
    (0, "Pitch Bend Sensitivity"), (1, "Channel Fine Tune"), (2, "Channel Coarse Tune"),
]


def build_ins(profile_key: str, profile_display_name: str,
              melodic: list[Entry], drums: list[DrumKit]) -> str:
    lines: list[str] = []
    lines.append(";")
    lines.append(f"; FITOM_X - {_ins_sanitize(profile_display_name)}")
    lines.append(f"; Auto-generated by tools/instrument_export/generate_instruments.py")
    lines.append(f"; source: config/profiles/{profile_key}.profile.json")
    lines.append(";")
    lines.append("")
    lines.append("; ----------------------------------------------------------------------")
    lines.append("")
    lines.append(".Patch Names")
    lines.append("")

    # メロディ系: (cc0,cc32)ごとにグループ化
    by_bank: dict[tuple[int, int], list[Entry]] = {}
    bank_display: dict[tuple[int, int], str] = {}
    for e in melodic:
        key = (e.cc0, e.cc32)
        by_bank.setdefault(key, []).append(e)

    def bank_section_name(cc0: int, cc32: int) -> str:
        return f"{profile_key} CC0={cc0} CC32={cc32}"

    def drum_section_name(cc32: int, name: str) -> str:
        return f"{profile_key} Drum CC32={cc32} {_ins_sanitize(name)}"

    for (cc0, cc32), items in sorted(by_bank.items()):
        lines.append(f"[{bank_section_name(cc0, cc32)}]")
        for e in sorted(items, key=lambda x: x.prog):
            lines.append(f"{e.prog}={_ins_sanitize(e.name)}")
        lines.append("")

    # ドラムキットは1キット=1Patchとして扱うため、Patch Namesは「0=キット名」の1件のみ
    for kit in drums:
        lines.append(f"[{drum_section_name(kit.cc32, kit.name)}]")
        lines.append(f"0={_ins_sanitize(kit.name)}")
        lines.append("")

    lines.append("; ----------------------------------------------------------------------")
    lines.append("")
    lines.append(".Note Names")
    lines.append("")

    for kit in drums:
        if not kit.notes:
            continue
        lines.append(f"[{drum_section_name(kit.cc32, kit.name)}]")
        for note, name in sorted(kit.notes):
            lines.append(f"{note}={_ins_sanitize(name)}")
        lines.append("")

    lines.append("; ----------------------------------------------------------------------")
    lines.append("")
    lines.append(".Controller Names")
    lines.append("")
    lines.append(f"[{profile_key} Controllers]")
    for num, name in GM_CONTROLLER_NAMES:
        lines.append(f"{num}={name}")
    lines.append("")

    lines.append("; ----------------------------------------------------------------------")
    lines.append("")
    lines.append(".RPN Names")
    lines.append("")
    lines.append(f"[{profile_key} RPN]")
    for num, name in GM_RPN_NAMES:
        lines.append(f"{num}={name}")
    lines.append("")

    lines.append("; ----------------------------------------------------------------------")
    lines.append("")
    lines.append(".Instrument Definitions")
    lines.append("")

    for (cc0, cc32), _items in sorted(by_bank.items()):
        section = bank_section_name(cc0, cc32)
        patch_index = (cc0 << 7) | cc32
        lines.append(f"[{section}]")
        lines.append(f"Control={profile_key} Controllers")
        lines.append(f"RPN={profile_key} RPN")
        lines.append(f"Patch[{patch_index}]={section}")
        lines.append("Patch[*]=1..128")
        lines.append("")

    for kit in drums:
        section = drum_section_name(kit.cc32, kit.name)
        patch_index = (CC0_RHYTHM << 7) | kit.cc32
        lines.append(f"[{section} Inst]")
        lines.append(f"Control={profile_key} Controllers")
        lines.append(f"RPN={profile_key} RPN")
        lines.append(f"Patch[{patch_index}]={section}")
        lines.append("Key[*,*]=0..127")
        if kit.notes:
            lines.append(f"Key[{CC0_RHYTHM},0]={section}")
        lines.append("Drum[*,*]=1")
        lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# DOMINO .xml 出力
# ---------------------------------------------------------------------------

def build_domino_xml(profile_key: str, profile_display_name: str,
                      melodic: list[Entry], drums: list[DrumKit]) -> str:
    by_prog: dict[int, list[Entry]] = {}
    for e in melodic:
        by_prog.setdefault(e.prog, []).append(e)

    out: list[str] = []
    out.append('<?xml version="1.0" encoding="Shift_JIS"?>')
    out.append("")
    out.append(
        f'<ModuleData Name="{xml_escape(profile_display_name)}" Folder="FITOM_X" '
        f'Priority="100" FileCreator="FITOM_staging/tools/instrument_export" '
        f'FileVersion="1.0">'
    )
    out.append('\t<RhythmTrackDefault Gate="1" />')
    out.append("")
    out.append("\t<InstrumentList>")
    out.append(f'\t\t<Map Name="{xml_escape(profile_key)}">')
    for prog in sorted(by_prog):
        items = by_prog[prog]
        pc_name = f"Program {prog + 1}"
        out.append(f'\t\t\t<PC Name="{xml_escape(pc_name)}" PC="{prog + 1}">')
        for e in sorted(items, key=lambda x: (x.cc0, x.cc32)):
            out.append(
                f'\t\t\t\t<Bank Name="{xml_escape(e.name)}" '
                f'MSB="{e.cc0}" LSB="{e.cc32}" />'
            )
        out.append("\t\t\t</PC>")
    out.append("\t\t</Map>")
    out.append("\t</InstrumentList>")
    out.append("")

    kits_with_notes = [k for k in drums if k.notes]
    if kits_with_notes:
        out.append("\t<DrumSetList>")
        out.append(f'\t\t<Map Name="{xml_escape(profile_key)}">')
        out.append('\t\t\t<PC Name="Drum Kits" PC="1">')
        for kit in kits_with_notes:
            out.append(
                f'\t\t\t\t<Bank Name="{xml_escape(kit.name)}" '
                f'MSB="{CC0_RHYTHM}" LSB="{kit.cc32}">'
            )
            for note, name in sorted(kit.notes):
                out.append(f'\t\t\t\t\t<Tone Name="{xml_escape(name)}" Key="{note}" />')
            out.append("\t\t\t\t</Bank>")
        out.append("\t\t\t</PC>")
        out.append("\t\t</Map>")
        out.append("\t</DrumSetList>")
        out.append("")

    out.append("</ModuleData>")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

def convert_profile(profile_path: Path, out_dir: Path) -> None:
    profile_dir = profile_path.parent
    profile_key = profile_path.stem.replace(".profile", "")
    profile = load_json(profile_path)
    display_name = profile.get("profile_name") or profile_key

    warnings: list[str] = []
    melodic = collect_melodic_entries(profile, profile_dir, lambda m: warnings.append(m))
    drums = collect_drum_kits(profile, profile_dir)

    for w in warnings:
        print(f"  [警告] {profile_key}: {w}", file=sys.stderr)

    sekaiju_dir = out_dir / "sekaiju"
    domino_dir = out_dir / "domino"
    sekaiju_dir.mkdir(parents=True, exist_ok=True)
    domino_dir.mkdir(parents=True, exist_ok=True)

    ins_text = build_ins(profile_key, display_name, melodic, drums)
    (sekaiju_dir / f"{profile_key}.ins").write_text(ins_text, encoding="cp932", errors="replace")

    xml_text = build_domino_xml(profile_key, display_name, melodic, drums)
    (domino_dir / f"{profile_key}.xml").write_text(xml_text, encoding="cp932", errors="replace")

    print(f"{profile_key}: melodic={len(melodic)} patches, "
          f"banks={len({(e.cc0, e.cc32) for e in melodic})}, "
          f"drum_kits={len(drums)} -> {sekaiju_dir / (profile_key + '.ins')}, "
          f"{domino_dir / (profile_key + '.xml')}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, action="append",
                         help="変換するprofile.jsonのパス(複数指定可、省略時は全件)")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                         help=f"出力先ディレクトリ(既定: {DEFAULT_OUT_DIR})")
    args = parser.parse_args()

    if args.profile:
        profile_paths = [p.resolve() for p in args.profile]
    else:
        profile_paths = sorted(PROFILES_DIR.glob("*.profile.json"))

    for path in profile_paths:
        convert_profile(path, args.out_dir)


if __name__ == "__main__":
    main()
