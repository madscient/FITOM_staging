#!/usr/bin/env python3
"""FITOM_X の config/profiles/*.profile.json から、MIDIシーケンサー用の
インストゥルメント定義ファイル(Cakewalk/Sekaiju用 .ins、DOMINO用 .xml)を
生成するスクリプト。

対応するCC#0(Bank Select MSB)の意味は docs/CLAUDE.md 3.2節、
docs/manuals/README.md の対応表を参照。

対象は統合設計プロファイル(TARGET_PROFILES参照)のみ。統合前の個別
プロファイル(旧emulator_*/hw_*)は誰もメンテナンスしておらず統合後の
構成と矛盾していたため2026年7月26日に削除済み(docs/CLAUDE.md 3.30節)。

実機音源の実例(Sekaiju8.3/instrument/KORG_KROME.ins・Roland_SC-8850.ins)
に倣い、Sekaiju上で1プロファイル=1機材として認識されるよう、
全対象プロファイルを1つの.Instrument Definitionsセクション群として
1つの.ins/.xmlファイルにまとめて出力する(プロファイルごとに別ファイルには
分けない)。

使い方:
    python3 generate_instruments.py                     # 既定の出力先に生成
    python3 generate_instruments.py --out-dir docs/instruments
"""
from __future__ import annotations

import argparse
import functools
import json
import struct
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
OUTPUT_STEM = "FITOM_X"

# 生成対象プロファイル(profile_key -> セクション見出し用ASCII表示名)。
# Sekaiju/CakewalkのInstrument Definitionセクション名にマルチバイト文字は
# 使えないため、config/profiles/*.profile.jsonの日本語profile_nameは使わず
# ここで別途ASCII名を割り当てる。
TARGET_PROFILES: dict[str, str] = {
    "unified_preset": "FITOM_X Unified Profile",
    "emu_opn": "FITOM_X OPN Emulator",
    "emu_fmgen_opn": "FITOM_X OPN Emulator (FmGen)",
    "emu_opl": "FITOM_X OPL Emulator",
    "emu_opm": "FITOM_X OPM Emulator",
    "emu_opll": "FITOM_X OPLL Emulator",
    "fmall": "FITOM_X FM All",
}

# 2026年7月29日、banksセクションが外部ファイル参照(文字列)+
# bank_overrides(部分上書き)方式に変わった(docs/CLAUDE.md 3.32/3.33節)。
# 識別キーはセクションごとに異なる(profile.schema.json bank_overrides説明文参照):
#   hw_banks: (group, bank) / pcm_banks: (bank, chip) / drum_banks: prog
#   それ以外(sw_banks/patch_banks/sf2_banks/scc_wave_banks): bank
def _override_key(section: str, entry: dict):
    if section == "hw_banks":
        return (entry.get("group"), entry.get("bank"))
    if section == "pcm_banks":
        return (entry.get("bank"), entry.get("chip"))
    if section == "drum_banks":
        return entry.get("prog")
    return entry.get("bank")


# 通常モード(CC#0=0,CC#32=0)のレイヤードバンク0(patch_banks bank=0)・
# ドラムキット0(drum_banks prog=0)は、bank_overridesにより実際に鳴る
# ファイルがプロファイルごとに異なる(docs/CLAUDE.md 3.33節)。
# インストゥルメントリスト上はプロファイル固有の内容を反映せず、GM標準
# (GM128メロディ名・GM2標準ドラムマップ)で統一表示する(ユーザー判断、
# 2026年7月31日)。
GM_STANDARD_MELODIC_FILE = "../../banks/patches/necopn_gm.patchbank.json"
GM_STANDARD_DRUM_FILE = "../../banks/drums/gm2_standard.drumkit.json"

# docs/CLAUDE.md 3.2節 VoicePatchType(CC#0直接モード値)
GROUP_CC0_HW = {
    "OPN2": 17,
    "OPZ": 26,
    "OPL3_2": 34,
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
CC0_NORMAL = 0        # patch_banks[] (通常モード)
CC0_DRUM_KIT = 120    # drum_banks[] (通常ドラムキット、GM2 Percussion Bank相当)
CC0_BUILTIN_RHYTHM = 112  # OPNA/OPLL内蔵リズム音源の直接選択専用(ドラムキットとは別軸、
                          # docs/manuals/README.md「1.音源選択モードの概要」参照)
CC0_SF2 = 127         # sf2_banks[] (FitomSf2IF/FluidSynth、CC#0規約上未使用の値を便宜的に割当)

# 以下3種類は「ファイルを持たない機械合成バンク」のため、hw_banks[]/
# drum_banks[]には現れず、プロファイルJSONの走査だけでは拾えない。
# 実際の名前はFITOM_X本体(../FITOM_X)のC++ソースにハードコードされて
# いるため、ここに転記する(2026年8月4日、ユーザー指摘によりFITOM_X本体
# 調査の上追加。docs/CLAUDE.md 3.31節参照)。

# core/src/PatchManager.cpp initOpllRomPatches() のROM音色名(kNames[4][16])。
# hw_bank=0固定、hwProg = (variant<<4)|instIndex
# (variant: 0=OPLL/OPLL2, 1=OPLLX, 2=OPLLP, 3=VRC7)。instIndex=0は各variant
# 共通で無音のダミーのため未収録(1-15のみ)。出典はソースコメントによれば
# https://github.com/plgDavid/misc/wiki/Copyright-free-OPLL(x)-ROM-patches
# (非公式・耳コピ由来の近似データである旨、本体側コメントに明記あり)。
#
# voice_patch_type(CC#0)は40(VOICE_PATCH_OPLL)/41(VOICE_PATCH_OPLLP)/
# 42(VOICE_PATCH_OPLLX)/43(VOICE_PATCH_VRC7)の4値が定義されている。
# `PatchManager::resolveTriple()`はhw_bank==0でこの4値のいずれかが来ると
# `resolveOpllRomVoice(hwProg, ...)`を呼ぶだけで、voicePatchType自体は
# 引数として渡さない(実際の発音・モニター名前解決はhwProg内の
# variantSel(bit4-6)だけで再決定される)ため、ランタイム上はCC#0=40/41/
# 42/43のどれを選んでも同じProgに対して常に同じ結果になる(docs/CLAUDE.md
# 3.41節)。
#
# 一方、FITOM_X本体・FITOM_patch_editorのパッチピッカーGUIは、
# `PatchManager::getOpllRomPatches(voicePatchType)`(gui/bridge/
# FITOMBridge.cpp)経由でCC#0ごとに対応するvariantの音色のみに絞り込んで
# 表示している。MIDIシーケンサー側でも同じ体験(CC#0でチップを選んでいる
# ように見せる)にするため、このGUIの絞り込みロジックに倣う
# (2026年8月4日、ユーザー指示。docs/CLAUDE.md 3.42節)。
# CC#0(voicePatchType) -> variant番号(OPLL_ROM_NAMESのキー)。
# `resolveOpllRomVoice`のkVariantMap/`getOpllRomPatches`と同じ対応で、
# `tests/test_config.cpp`のユニットテストでも検証済み。CC#0の数値順
# (40,41,42,43=OPLL,OPLLP,OPLLX,VRC7)とvariant番号順(0,1,2,3=OPLL,OPLLX,
# OPLLP,VRC7)でOPLLPとOPLLXの順序が入れ替わっている点に注意。
OPLL_BUILTIN_CC0_TO_VARIANT = {40: 0, 41: 2, 42: 1, 43: 3}
OPLL_ROM_NAMES: dict[int, list[str]] = {
    0: ["Violin", "Guitar", "Piano", "Flute", "Clarinet", "Oboe", "Trumpet",
        "Organ", "Horn", "Synthesizer", "Harpsichord", "Vibraphone",
        "Synthesizer Bass", "Acoustic Bass", "Electric Guitar"],
    1: ["Strings", "Guitar", "Electric Guitar", "Electric Piano 2", "Flute",
        "Marimba", "Trumpet", "Harmonica", "Tuba", "Synth Brass 2",
        "Short Saw", "Vibraphone", "Electric Guitar 2", "Synth Bass 2",
        "Sitar"],
    2: ["Electric Strings", "Bow Wow", "Electric Guitar", "Organ", "Clarinet",
        "Saxophone", "Trumpet", "Street Organ", "Synth Brass",
        "Electric Piano", "Bass", "Vibraphone", "Chime", "Tom Tom 2",
        "Noise and Tone"],
    3: ["Buzzy Bell", "Guitar", "Wurly", "Flute", "Clarinet", "Synth",
        "Trumpet", "Organ", "Bells", "Vibes", "Vibraphone", "Tutti",
        "Fretless", "Synth Bass", "Sweep"],
}
# gui/bridge/FITOMBridge.cpp kOpllRhythmNames/kOpnaRhythmNames。
# CC#0=112(内蔵リズム音源モード)でCC#32=40(OPLL)/17(OPNA)を選んだときの
# 楽器(物理チャンネル)名。Prog(patch_prog)がそのまま楽器番号になる
# (通常のドラムキット選択(CC#32=0固定+Progでキット選択)とは別の軸、
# docs/manuals/builtin_rhythm.md参照)。
OPLL_RHYTHM_NAMES = ["Hi-Hat", "Top Cymbal", "Tom", "Snare Drum", "Bass Drum"]
OPNA_RHYTHM_NAMES = ["Bass Drum", "Snare Drum", "Top Cymbal", "Hi-Hat", "Tom", "Rim Shot"]
CC32_OPLL_RHYTHM = 40
CC32_OPNA_RHYTHM = 17


@dataclass(frozen=True)
class Entry:
    cc0: int
    cc32: int
    prog: int
    name: str


@dataclass(frozen=True)
class DrumKit:
    # drum_banks[].prog はCC#32(Bank Select LSB)ではなくProgram Change値。
    # CC#0=112・CC#32=0固定の1バンク内で、Progによってキットが切り替わる
    # (docs/manuals/README.md「バンクマップ」表・drumkits.mdの「Prog」列、
    # profile.schema.jsonのdrum_banks[]が「常にbank0固定でprogのみで選択」
    # である設計に対応)。
    prog: int
    name: str
    notes: "list[tuple[int, str]] | None"  # None = type:direct (個別ノート名なし)


@dataclass(frozen=True)
class Profile:
    key: str
    display_name: str
    melodic: "list[Entry]"
    drums: "list[DrumKit]"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as f:
        return json.load(f)


def resolve(base_dir: Path, rel: str) -> Path:
    return (base_dir / rel).resolve()


def resolve_banks_dict(value, profile_dir: Path) -> dict:
    """banks/bank_overridesの値(オブジェクト直書き、または外部参照ファイル
    パスの文字列)を解決してオブジェクトにする。"""
    if isinstance(value, str):
        return load_json(resolve(profile_dir, value))
    return value or {}


def apply_bank_overrides(banks: dict, overrides: dict) -> dict:
    """bank_overridesをbanksへマージする。識別キーが一致するエントリは
    置換、一致しなければ追加(profile.schema.json bank_overrides説明文の
    仕様通り)。"""
    merged = {k: list(v) for k, v in banks.items() if isinstance(v, list)}
    for section, ov_items in overrides.items():
        if section == "_comment" or not isinstance(ov_items, list):
            continue
        items = merged.setdefault(section, [])
        for ov in ov_items:
            key = _override_key(section, ov)
            idx = next((i for i, e in enumerate(items)
                        if _override_key(section, e) == key), None)
            if idx is not None:
                items[idx] = ov
            else:
                items.append(ov)
    return merged


def force_gm_standard_bank0(banks: dict) -> None:
    for pb in banks.get("patch_banks", []):
        if pb.get("bank") == 0:
            pb["file"] = GM_STANDARD_MELODIC_FILE
    for db in banks.get("drum_banks", []):
        if db.get("prog") == 0:
            db["file"] = GM_STANDARD_DRUM_FILE
            db.pop("name", None)  # ファイル自身のname("GM2 Standard Kit")を使わせる


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


@functools.lru_cache(maxsize=None)
def parse_sf2_presets(path: Path) -> tuple[tuple[int, int, str], ...]:
    """SF2(SoundFont2、RIFF形式)ファイルの`pdta`チャンク内`phdr`
    (Preset Headers)を読み、(bank, preset, name)のタプル一覧を返す。
    サウンドフォント本体はサイズが大きい(数十MBに及ぶ)ため、必要な
    ヘッダ部分のみを読み、複数の`sf2_banks[]`エントリで同じファイルを
    参照する場合に備えてlru_cacheでファイル単位にキャッシュする。

    sfPresetHeader構造体(SoundFont 2.0仕様、38byte固定長):
        achPresetName[20] (ASCII, NUL終端) / wPreset(u16) / wBank(u16) /
        wPresetBagNdx(u16) / dwLibrary(u32) / dwGenre(u32) / dwMorphology(u32)
    配列の最終要素は常に"EOP"ダミーレコードのため除外する。
    """
    with path.open("rb") as f:
        data = f.read()
    if data[0:4] != b"RIFF" or data[8:12] != b"sfbk":
        raise ValueError(f"{path} はSF2(RIFF/sfbk)形式ではありません")
    presets: list[tuple[int, int, str]] = []
    pos = 12
    end = len(data)
    while pos < end:
        chunk_id = data[pos:pos + 4]
        chunk_size = struct.unpack_from("<I", data, pos + 4)[0]
        body_start = pos + 8
        if chunk_id == b"LIST" and data[body_start:body_start + 4] == b"pdta":
            sub_pos = body_start + 4
            sub_end = body_start + chunk_size
            while sub_pos < sub_end:
                sub_id = data[sub_pos:sub_pos + 4]
                sub_size = struct.unpack_from("<I", data, sub_pos + 4)[0]
                sub_body = sub_pos + 8
                if sub_id == b"phdr":
                    for i in range(sub_size // 38):
                        rec = data[sub_body + i * 38: sub_body + (i + 1) * 38]
                        name = rec[0:20].split(b"\x00", 1)[0].decode("ascii", errors="replace")
                        preset, bank = struct.unpack_from("<HH", rec, 20)
                        presets.append((bank, preset, name))
                sub_pos = sub_body + sub_size + (sub_size & 1)  # 奇数長チャンクは1byteパディング
        pos = body_start + chunk_size + (chunk_size & 1)
    return tuple(presets[:-1])  # 末尾のEOPダミーレコードを除外


def collect_sf2_entries(profile: dict, profile_dir: Path, warn) -> list[Entry]:
    entries: list[Entry] = []
    for sb in profile.get("banks", {}).get("sf2_banks", []):
        path = resolve(profile_dir, sb["file"])
        try:
            presets = parse_sf2_presets(path)
        except (FileNotFoundError, ValueError) as e:
            warn(f"sf2_banks bank={sb.get('bank')} '{path.name}' の読み込みに失敗: {e}")
            continue
        target_bank = sb["sf2_bank"]
        for bank, preset, name in presets:
            if bank == target_bank:
                entries.append(Entry(CC0_SF2, sb["bank"], preset,
                                      name or fallback_name("Preset", preset)))
    return entries


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


def collect_builtin_entries() -> list[Entry]:
    """OPLLビルトイン音色バンク・OPLLビルトインリズム・OPNAビルトイン
    リズムは、ファイルを持たずFITOM_X本体にハードコードされているため、
    プロファイルJSONの走査だけでは拾えない。

    全プロファイルが共通の`unified.bankset.json`を参照し、実際の
    デバイス構成(搭載チップ)に含まれないバンクエントリも変わらず表示
    する(単に発音しないだけで実害がない)という設計原則(docs/CLAUDE.md
    3.32節)に合わせ、当初実装していた「実際に搭載されているチップで
    絞り込む」判定は撤廃し、他のhw_banks[]由来エントリ(例: OPLL専用
    チップを持たないunified_presetでも通常のOPLLプリセットバンクは
    表示される)と同じく、全プロファイル共通で常に追加する
    (2026年8月8日、ユーザー指摘「Unified presetに登録されていない」
    により訂正。docs/CLAUDE.md 3.43節)。"""
    entries: list[Entry] = []
    # ランタイム上はCC#0(voicePatchType)に関わらずhwProgだけで結果が
    # 決まるが(OPLL_BUILTIN_CC0_TO_VARIANT定義部のコメント参照)、GUIの
    # パッチピッカーに倣い、CC#0ごとに対応するvariantの音色のみを載せる
    # (MIDIシーケンサー側でチップが選択されているように見せるため)。
    for cc0, variant in sorted(OPLL_BUILTIN_CC0_TO_VARIANT.items()):
        for idx, name in enumerate(OPLL_ROM_NAMES[variant], start=1):
            entries.append(Entry(cc0, 0, (variant << 4) | idx, name))
    for prog, name in enumerate(OPLL_RHYTHM_NAMES):
        entries.append(Entry(CC0_BUILTIN_RHYTHM, CC32_OPLL_RHYTHM, prog, name))
    for prog, name in enumerate(OPNA_RHYTHM_NAMES):
        entries.append(Entry(CC0_BUILTIN_RHYTHM, CC32_OPNA_RHYTHM, prog, name))
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


def load_profiles(warn) -> list[Profile]:
    profiles: list[Profile] = []
    for key, display_name in TARGET_PROFILES.items():
        path = PROFILES_DIR / f"{key}.profile.json"
        profile_dir = path.parent
        data = load_json(path)

        banks = resolve_banks_dict(data.get("banks"), profile_dir)
        overrides = data.get("bank_overrides")
        if overrides:
            banks = apply_bank_overrides(banks, resolve_banks_dict(overrides, profile_dir))
        force_gm_standard_bank0(banks)
        data = {**data, "banks": banks}

        melodic = collect_melodic_entries(data, profile_dir, lambda m, k=key: warn(f"{k}: {m}"))
        melodic += collect_builtin_entries()
        melodic += collect_sf2_entries(data, profile_dir, lambda m, k=key: warn(f"{k}: {m}"))
        drums = collect_drum_kits(data, profile_dir)
        profiles.append(Profile(key, display_name, melodic, drums))
    return profiles


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
CONTROLLERS_SECTION = f"{OUTPUT_STEM} Controllers"
RPN_SECTION = f"{OUTPUT_STEM} RPN"


def _bank_section_name(profile_key: str, cc0: int, cc32: int) -> str:
    return f"{profile_key} CC0={cc0} CC32={cc32}"


def _drum_patch_names_section(profile_key: str) -> str:
    """CC#0=112・CC#32=0固定の1バンク内、Prog(Program Change)ごとの
    ドラムキット名一覧(GM1_GM2.insの[General MIDI Level 2 Drumsets]と
    同じ構造)。"""
    return f"{profile_key} Drum Kits"


def _drum_note_section_name(profile_key: str, prog: int, name: str) -> str:
    return f"{profile_key} Drum Prog={prog} {_ins_sanitize(name)}"


def build_ins(profiles: list[Profile]) -> str:
    lines: list[str] = []
    lines.append(";")
    lines.append(f"; {OUTPUT_STEM} - MIDI Instrument Definitions")
    lines.append(f"; Auto-generated by tools/instrument_export/generate_instruments.py")
    lines.append("; source: config/profiles/*.profile.json")
    lines.append(";")
    lines.append("")
    lines.append("; ----------------------------------------------------------------------")
    lines.append("")
    lines.append(".Patch Names")
    lines.append("")

    by_bank_per_profile: dict[str, dict[tuple[int, int], list[Entry]]] = {}
    for prof in profiles:
        by_bank: dict[tuple[int, int], list[Entry]] = {}
        for e in prof.melodic:
            by_bank.setdefault((e.cc0, e.cc32), []).append(e)
        by_bank_per_profile[prof.key] = by_bank

        for (cc0, cc32), items in sorted(by_bank.items()):
            lines.append(f"[{_bank_section_name(prof.key, cc0, cc32)}]")
            for e in sorted(items, key=lambda x: x.prog):
                lines.append(f"{e.prog}={_ins_sanitize(e.name)}")
            lines.append("")

        # ドラムキットはCC#0=112・CC#32=0固定の1バンク内でProgram Changeに
        # よって切り替わる(drum_banks[].progはCC#32ではなくProg)。そのため
        # Patch Namesも1バンク分のセクションにProg->キット名の一覧としてまとめる。
        if prof.drums:
            lines.append(f"[{_drum_patch_names_section(prof.key)}]")
            for kit in sorted(prof.drums, key=lambda k: k.prog):
                lines.append(f"{kit.prog}={_ins_sanitize(kit.name)}")
            lines.append("")

    lines.append("; ----------------------------------------------------------------------")
    lines.append("")
    lines.append(".Note Names")
    lines.append("")

    for prof in profiles:
        for kit in prof.drums:
            if not kit.notes:
                continue
            lines.append(f"[{_drum_note_section_name(prof.key, kit.prog, kit.name)}]")
            for note, name in sorted(kit.notes):
                lines.append(f"{note}={_ins_sanitize(name)}")
            lines.append("")

    lines.append("; ----------------------------------------------------------------------")
    lines.append("")
    lines.append(".Controller Names")
    lines.append("")
    lines.append(f"[{CONTROLLERS_SECTION}]")
    for num, name in GM_CONTROLLER_NAMES:
        lines.append(f"{num}={name}")
    lines.append("")

    lines.append("; ----------------------------------------------------------------------")
    lines.append("")
    lines.append(".RPN Names")
    lines.append("")
    lines.append(f"[{RPN_SECTION}]")
    for num, name in GM_RPN_NAMES:
        lines.append(f"{num}={name}")
    lines.append("")

    lines.append("; ----------------------------------------------------------------------")
    lines.append("")
    lines.append(".Instrument Definitions")
    lines.append("")

    # 実機音源の.ins実例(KORG_KROME.ins、Roland_SC-8850.ins)は、1機材=1つの
    # Instrument Definitionセクションであり、その中で持つ全バンクをPatch[]で
    # 列挙する構成になっている(バンクごとに別セクションを作ると、Sekaiju上で
    # バンクの数だけ別々の「機材」として扱われてしまう)。これに倣い、
    # プロファイルごとに1つのセクションにまとめる(複数プロファイルは
    # 同じ1ファイルの中に複数の機材として並ぶ)。
    for prof in profiles:
        by_bank = by_bank_per_profile[prof.key]
        lines.append(f"[{_ins_sanitize(prof.display_name)}]")
        lines.append(f"Control={CONTROLLERS_SECTION}")
        lines.append(f"RPN={RPN_SECTION}")
        for (cc0, cc32), _items in sorted(by_bank.items()):
            patch_index = (cc0 << 7) | cc32
            lines.append(f"Patch[{patch_index}]={_bank_section_name(prof.key, cc0, cc32)}")
        # ドラムキットはCC#0=120(GM2 Percussion Bank相当)・CC#32=0固定の
        # 1バンクのみ(Patch[]添字は1個だけ)。CC#0=112はOPNA/OPLL内蔵リズム
        # 音源の直接選択専用であり、通常ドラムキットとは別軸なので使わない。
        # GM1_GM2.insの[General MIDI Level 2 Drumsets](Patch[15360]=120<<7)
        # と同じく、Key[]の第二引数(PC)でキットの種類を切り替える。
        drum_patch_index = (CC0_DRUM_KIT << 7) | 0
        if prof.drums:
            lines.append(f"Patch[{drum_patch_index}]={_drum_patch_names_section(prof.key)}")
        lines.append("Patch[*]=1..128")
        lines.append("Key[*,*]=0..127")
        # Key[]の第一引数は対応するPatch[]添字の値と一致させる(KORG_KROME.ins/
        # Roland_SC-8850.insの実例に倣う)。第二引数はProgram Change値
        # (drum_banks[].prog、0-indexed)。
        # メロディ音色と同一セクション内にドラムキットも列挙するため、
        # Drum[*,*]のようなワイルドカード指定はできない(メロディ側まで
        # ドラムトラック扱いになってしまう)。ドラムキットのPatch[]添字にのみ
        # 個別に立てる。
        for kit in prof.drums:
            if kit.notes:
                lines.append(f"Key[{drum_patch_index},{kit.prog}]="
                              f"{_drum_note_section_name(prof.key, kit.prog, kit.name)}")
        if prof.drums:
            lines.append(f"Drum[{drum_patch_index},*]=1")
        lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# DOMINO .xml 出力
# ---------------------------------------------------------------------------

def build_domino_xml(profiles: list[Profile]) -> str:
    out: list[str] = []
    out.append('<?xml version="1.0" encoding="Shift_JIS"?>')
    out.append("")
    out.append(
        f'<ModuleData Name="{xml_escape(OUTPUT_STEM)}" Folder="FITOM_X" '
        f'Priority="100" FileCreator="FITOM_staging/tools/instrument_export" '
        f'FileVersion="1.0">'
    )
    out.append('\t<RhythmTrackDefault Gate="1" />')
    out.append("")
    out.append("\t<InstrumentList>")
    for prof in profiles:
        by_prog: dict[int, list[Entry]] = {}
        for e in prof.melodic:
            by_prog.setdefault(e.prog, []).append(e)

        out.append(f'\t\t<Map Name="{xml_escape(prof.display_name)}">')
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

    profiles_with_drums = [p for p in profiles if any(k.notes for k in p.drums)]
    if profiles_with_drums:
        out.append("\t<DrumSetList>")
        for prof in profiles_with_drums:
            kits_with_notes = [k for k in prof.drums if k.notes]
            out.append(f'\t\t<Map Name="{xml_escape(prof.display_name)}">')
            # ドラムキットはCC#0=120(GM2 Percussion Bank相当)・CC#32=0固定の
            # 1バンク内でProgram Changeによって切り替わる(drum_banks[].prog
            # はCC#32ではなくProg)ため、キットごとに別のPCタグ(PC=prog+1)を
            # 作り、Bankは常にLSB=0固定。CC#0=112はOPNA/OPLL内蔵リズム音源の
            # 直接選択専用のため使わない。
            for kit in sorted(kits_with_notes, key=lambda k: k.prog):
                out.append(f'\t\t\t<PC Name="{xml_escape(kit.name)}" PC="{kit.prog + 1}">')
                out.append(
                    f'\t\t\t\t<Bank Name="{xml_escape(kit.name)}" '
                    f'MSB="{CC0_DRUM_KIT}" LSB="0">'
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

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                         help=f"出力先ディレクトリ(既定: {DEFAULT_OUT_DIR})")
    args = parser.parse_args()

    warnings: list[str] = []
    profiles = load_profiles(lambda m: warnings.append(m))
    for w in warnings:
        print(f"  [警告] {w}", file=sys.stderr)

    sekaiju_dir = args.out_dir / "sekaiju"
    domino_dir = args.out_dir / "domino"
    sekaiju_dir.mkdir(parents=True, exist_ok=True)
    domino_dir.mkdir(parents=True, exist_ok=True)

    ins_path = sekaiju_dir / f"{OUTPUT_STEM}.ins"
    ins_path.write_text(build_ins(profiles), encoding="cp932", errors="replace")

    xml_path = domino_dir / f"{OUTPUT_STEM}.xml"
    xml_path.write_text(build_domino_xml(profiles), encoding="cp932", errors="replace")

    total_melodic = sum(len(p.melodic) for p in profiles)
    total_drums = sum(len(p.drums) for p in profiles)
    print(f"{len(profiles)} profiles: melodic={total_melodic} patches, "
          f"drum_kits={total_drums} -> {ins_path}, {xml_path}")


if __name__ == "__main__":
    main()
