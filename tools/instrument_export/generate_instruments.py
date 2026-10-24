#!/usr/bin/env python3
"""全プロファイルが共有するバンクセット config/profiles/unified.bankset.json から、
MIDIシーケンサー用のインストゥルメント定義ファイル(Cakewalk/Sekaiju用 .ins、
DOMINO用 .xml)を生成するスクリプト。

対応するCC#0(Bank Select MSB)の意味は CLAUDE.md「CC#0とVoicePatchType」節、
docs/manuals/README.md の対応表を参照。

出力は機材1つ(FITOM_X)だけ。全プロファイルが同じバンクセットを読むため、
CC#0/CC#32/Program Changeと音色名の対応はプロファイルによらない。プロファイルの
チップ構成によって鳴らない音色があるだけで、名前が別の音を指すことはない。
プロファイルごとに違うレイヤードバンク0・ドラムキット0(bank_overrides)は、
GM標準の名前で載せる(GM_STANDARD_*_FILE)。

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
BANKSET_FILE = PROFILES_DIR / "unified.bankset.json"
DEFAULT_OUT_DIR = REPO_ROOT / "docs" / "instruments"
OUTPUT_STEM = "FITOM_X"
# Sekaiju/CakewalkのInstrument Definitionセクション名にマルチバイト文字は使えない
MACHINE_NAME = "FITOM_X"

# レイヤードバンク0・ドラムキット0は、プロファイルごとにbank_overridesで別の
# ファイルが敷かれる(共有バンクセット側は空)。敷かれるのはどれもGM配列の
# 音色・キットなので、GM標準の名前で載せる(ユーザー判断)。
GM_STANDARD_MELODIC_FILE = "../../banks/patches/necopn_gm.patchbank.json"
GM_STANDARD_DRUM_FILE = "../../banks/drums/gm2_standard.drumkit.json"

# VoicePatchType(CC#0直接モード値)。CLAUDE.md「CC#0とVoicePatchType」節の対応表に加え、
# 2026年8月のステレオ化プロファイル追加(OPM/OPZ分離、同種チップの
# フォールバックルート新設)で新規に使われるようになったgroup(OPN/OPM/
# OPL/OPL2/OPLLP/OPLLX/VRC7)を、`../FITOM_X/core/include/fitom/
# FITOMdefine.h`のVOICE_PATCH_*定数から追加(2026年8月11日確認)。
GROUP_CC0_HW = {
    "OPN": 16,      # VOICE_PATCH_OPN (YM2203等)
    "OPN2": 17,     # VOICE_PATCH_OPN2 (YM2612/YM2608等)
    "OPM": 25,      # VOICE_PATCH_OPM (YM2151等)
    "OPZ": 26,      # VOICE_PATCH_OPZ (YM2414)
    "OPL": 32,      # VOICE_PATCH_OPL (YM3526等)
    "OPL2": 33,     # VOICE_PATCH_OPL2 (YM3812)
    "OPL3_2": 34,   # VOICE_PATCH_OPL3_2 (YMF262の2opモード)
    "OPL_RHY": 35,
    "OPLL": 40,     # VOICE_PATCH_OPLL (YM2413/OPLL2)
    "OPLLP": 41,    # VOICE_PATCH_OPLLP (YMF281)
    "OPLLX": 42,    # VOICE_PATCH_OPLLX (YM2423)
    "VRC7": 43,     # VOICE_PATCH_VRC7 (FS1001)
    "OPLLEX": 44,   # VOICE_PATCH_OPLLEX (Y8960拡張OPLL部)
    "OPL3": 48,
    "SSG": 64,
    "AWM": 84,
}
# pcm_banks[] 経由(ADPCM系、hw_banksとは別配列)
GROUP_CC0_PCM = {
    "ADPCMB": 81,
    "ADPCMA": 82,
    "SSGS_ADPCM": 85,  # VOICE_PATCH_SSGS_ADPCM (YMZ705/YMZ732)
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
# 調査の上追加。docs/worklog/2026-07.md 3.31節参照)。

# core/src/PatchManager.cpp initOpllRomPatches() のROM音色名(kNames[4][16])。
# hw_bank=0固定、hwProg = (variant<<4)|instIndex
# (variant: 0=OPLL/OPLL2, 1=OPLLX, 2=OPLLP, 3=VRC7)。instIndex=0は各variant
# 共通で無音のダミーのため未収録(1-15のみ)。出典はソースコメントによれば
# https://github.com/plgDavid/misc/wiki/Copyright-free-OPLL(x)-ROM-patches
# (非公式・耳コピ由来の近似データである旨、本体側コメントに明記あり)。
#
# voice_patch_type(CC#0)は40(VOICE_PATCH_OPLL)/41(VOICE_PATCH_OPLLP)/
# 42(VOICE_PATCH_OPLLX)/43(VOICE_PATCH_VRC7)/44(VOICE_PATCH_OPLLEX)の
# 5値が定義されている。`PatchManager::resolveTriple()`はhw_bank==0で
# このいずれかが来ると`resolveOpllRomVoice()`へ委譲するが、標準4チップ
# (40-43)についてはCC#0の値そのものが捨てられ、実際の発音・モニター
# 名前解決はhwProg内のvariantSel(bit4-6)だけで再決定される。このため
# ランタイム上はCC#0=40/41/42/43のどれを選んでも同じProgに対して常に
# 同じ結果になる(docs/worklog/2026-08.md 3.41節)。CC#0=44(OPLLEX)だけは例外で
# CC#0の値が意味を持つ(OPLLEX_BANK_LABELS定義部のコメント参照)。
#
# 一方、FITOM_X本体・FITOM_patch_editorのパッチピッカーGUIは、
# `PatchManager::getOpllRomPatches(voicePatchType)`(gui/bridge/
# FITOMBridge.cpp)経由でCC#0ごとに対応するvariantの音色のみに絞り込んで
# 表示している。MIDIシーケンサー側でも同じ体験(CC#0でチップを選んでいる
# ように見せる)にするため、このGUIの絞り込みロジックに倣う
# (2026年8月4日、ユーザー指示。docs/worklog/2026-08.md 3.42節)。
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
# Y8960拡張OPLL部(VOICE_PATCH_OPLLEX)のROM音色。OPLLEXはOPLL/OPLL-X/
# OPLL-P/VRC7の4バンク分のROMを1チップに内蔵しており、hwProgの上位3bitは
# 「どのチップへ迂回するか」ではなく「OPLLEX自身のどのBANKか」を選ぶ
# (`PatchManager::resolveOpllRomVoice()`のVOICE_PATCH_OPLLEX分岐。実機
# レジスタ0x40-0x48のチャンネル別BANK選択に対応する)。したがってCC#0=44
# だけは他の4値のようにvariantで絞り込まず、4バンク60音色すべてを
# 1バンク(CC#32=0)に並べる。同一バンク内で同名の音色(Vibraphone等)が
# 衝突するため、音色名にはBANK名を前置して区別する(PSG系の共有CC#0で
# パッチ名の[EPSG]等プレフィックスにより区別しているのと同じ方式)。
# BANK名はFITOMdefine.hのDEVICE_OPLLEX説明にある実機BANK値の呼称に合わせる。
CC0_OPLLEX_BUILTIN = 44   # VOICE_PATCH_OPLLEX (0x2c)
OPLLEX_BANK_LABELS = {0: "OPLL", 1: "OPLL-X", 2: "OPLL-P", 3: "VRC7"}

# gui/bridge/FITOMBridge.cpp kOpllRhythmNames/kOpnaRhythmNames。
# CC#0=112(内蔵リズム音源モード)でCC#32=40(OPLL)/17(OPNA)を選んだときの
# 楽器(物理チャンネル)名。Prog(patch_prog)がそのまま楽器番号になる
# (通常のドラムキット選択(CC#32=0固定+Progでキット選択)とは別の軸、
# docs/manuals/builtin_rhythm.md参照)。
OPLL_RHYTHM_NAMES = ["Hi-Hat", "Top Cymbal", "Tom", "Snare Drum", "Bass Drum"]
OPNA_RHYTHM_NAMES = ["Bass Drum", "Snare Drum", "Top Cymbal", "Hi-Hat", "Tom", "Rim Shot"]
CC32_OPLL_RHYTHM = 40
CC32_OPNA_RHYTHM = 17

# core/src/PatchManager.cpp initDsgBuiltinPatches() のビルトイン音色。
# DSG(YM2163)はユーザー音色を一切持たず、ROM固定の「波形5種×エンベロープ
# 4種」の20音色がProgram Changeだけで選ばれる。CC#32(hw_bank)は
# `resolveDsgBuiltinVoice()`が値を読まずに捨てるため意味を持たない
# (OPLL ROM音色がbank=0のみ予約領域なのとは異なる)が、リスト上は0に固定
# して掲載する。
# prog = 波形index*4 + エンベロープindex、音色名は"<波形名>.<エンベロープ名>"。
DSG_WAVE_NAMES = ["St", "Or", "Cl", "Pf", "Hc"]
DSG_ENV_NAMES = ["Percussive", "Wind", "Sustain", "Plateau"]
CC0_DSG_BUILTIN = 68   # VOICE_PATCH_DSG (0x44)

# gui/bridge/FITOMBridge.cpp kDsgRhythmNames。パート番号はリズムトリガー
# (reg 0x90)のビット位置そのもの(core/src/DSG_new.cpp CDSGRhythm::kTriggerBit
# と同じ並び)。HHO/HHDは実機で同一の発振器・同一のレベルレジスタを共有する。
DSG_RHYTHM_NAMES = ["Bass Drum", "Hi Conga", "Snare Drum",
                    "Hi-Hat Open", "Hi-Hat Close"]
CC32_DSG_RHYTHM = 68   # 内蔵リズムモードのCC#32はチップ選択値=VoicePatchType


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


def put_gm_standard_bank0(banks: dict) -> None:
    patch_banks = [pb for pb in banks.get("patch_banks", []) if pb.get("bank") != 0]
    drum_banks = [db for db in banks.get("drum_banks", []) if db.get("prog") != 0]
    banks["patch_banks"] = [{"bank": 0, "file": GM_STANDARD_MELODIC_FILE}] + patch_banks
    # nameを書かず、ファイル自身のname("GM2 Standard Kit")を使わせる
    banks["drum_banks"] = [{"prog": 0, "file": GM_STANDARD_DRUM_FILE}] + drum_banks


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
            continue  # ユーザーが音色として直接選べないメタバンク(CLAUDE.md「ビルトイン音色用メタバンク」節)
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
        # offsets_onlyのバンクは特定チップ向けのオフセット表で、FITOM_Xは
        # ここから音色を作らない(CC#32で選んでも鳴らない)ため載せない。
        if pb.get("offsets_only"):
            continue
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
    """OPLLビルトイン音色バンク(OPLLEXの4バンク分を含む)・DSGビルトイン
    音色バンク・OPLL/OPNA/DSGビルトインリズムは、ファイルを持たず
    FITOM_X本体にハードコードされているため、プロファイルJSONの走査だけ
    では拾えない。

    全プロファイルが共通の`unified.bankset.json`を参照し、実際の
    デバイス構成(搭載チップ)に含まれないバンクエントリも変わらず表示
    する(単に発音しないだけで実害がない)という設計原則(docs/worklog/2026-07.md
    3.32節)に合わせ、当初実装していた「実際に搭載されているチップで
    絞り込む」判定は撤廃し、他のhw_banks[]由来エントリ(例: OPLL専用
    チップを持たないunified_presetでも通常のOPLLプリセットバンクは
    表示される)と同じく、全プロファイル共通で常に追加する
    (2026年8月8日、ユーザー指摘「Unified presetに登録されていない」
    により訂正。docs/worklog/2026-08.md 3.43節)。"""
    entries: list[Entry] = []
    # ランタイム上はCC#0(voicePatchType)に関わらずhwProgだけで結果が
    # 決まるが(OPLL_BUILTIN_CC0_TO_VARIANT定義部のコメント参照)、GUIの
    # パッチピッカーに倣い、CC#0ごとに対応するvariantの音色のみを載せる
    # (MIDIシーケンサー側でチップが選択されているように見せるため)。
    for cc0, variant in sorted(OPLL_BUILTIN_CC0_TO_VARIANT.items()):
        for idx, name in enumerate(OPLL_ROM_NAMES[variant], start=1):
            entries.append(Entry(cc0, 0, (variant << 4) | idx, name))
    # OPLLEXだけは自分自身が4バンク分のROMを内蔵しているため、CC#0=44の
    # 1バンクに全variantを並べる(OPLLEX_BANK_LABELS定義部のコメント参照)。
    for variant, label in sorted(OPLLEX_BANK_LABELS.items()):
        for idx, name in enumerate(OPLL_ROM_NAMES[variant], start=1):
            entries.append(Entry(CC0_OPLLEX_BUILTIN, 0, (variant << 4) | idx,
                                 f"[{label}] {name}"))
    for wave, wave_name in enumerate(DSG_WAVE_NAMES):
        for env, env_name in enumerate(DSG_ENV_NAMES):
            prog = wave * len(DSG_ENV_NAMES) + env
            entries.append(Entry(CC0_DSG_BUILTIN, 0, prog, f"{wave_name}.{env_name}"))
    for prog, name in enumerate(OPLL_RHYTHM_NAMES):
        entries.append(Entry(CC0_BUILTIN_RHYTHM, CC32_OPLL_RHYTHM, prog, name))
    for prog, name in enumerate(OPNA_RHYTHM_NAMES):
        entries.append(Entry(CC0_BUILTIN_RHYTHM, CC32_OPNA_RHYTHM, prog, name))
    for prog, name in enumerate(DSG_RHYTHM_NAMES):
        entries.append(Entry(CC0_BUILTIN_RHYTHM, CC32_DSG_RHYTHM, prog, name))
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


def load_machines(warn) -> list[Profile]:
    banks = load_json(BANKSET_FILE)
    put_gm_standard_bank0(banks)
    data = {"banks": banks}
    base_dir = BANKSET_FILE.parent

    melodic = collect_melodic_entries(data, base_dir, warn)
    melodic += collect_builtin_entries()
    melodic += collect_sf2_entries(data, base_dir, warn)
    drums = collect_drum_kits(data, base_dir)
    return [Profile(MACHINE_NAME, MACHINE_NAME, melodic, drums)]


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
    lines.append("; source: config/profiles/unified.bankset.json")
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
    # 機材ごとに1つのセクションにまとめる。
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
    profiles = load_machines(lambda m: warnings.append(m))
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
    print(f"{len(profiles)} machine(s): melodic={total_melodic} patches, "
          f"drum_kits={total_drums} -> {ins_path}, {xml_path}")


if __name__ == "__main__":
    main()
