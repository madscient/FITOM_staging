#!/usr/bin/env python3
"""各プロファイルで、通常モードのパッチバンクの音色とドラムキットのノートのうち、
解決できる(鳴る)ものを数える。

デバイスの一覧は launch_all.ps1 が退避した logs/launch_check/<name>.log の
"Device added" 行から取る(複合チップを展開した後の種別が出ている)。先に
launch_all.ps1 を実行しておくこと。

解決の規則は FITOM_X b7c1e4c の PatchManager::resolveTriple() /
resolveBuiltinRhythm() / resolveOpllRomVoice() と DeviceFactory::acceptsFallback()
を読んで写したもの。FITOM_X 側でこれらが変わったら、この表と関数も直す。
数えるのは解決の成否で、音は確かめない。

使い方:
    python tools/launch_check/coverage.py                       # 全プロファイルの集計
    python tools/launch_check/coverage.py emu_opm emu_msx       # 名前で絞る
    python tools/launch_check/coverage.py --markdown emu_opm    # docs/manuals/emu_profiles.md の表
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parents[2]
PROFILES = STAGE / "config" / "profiles"
LOGS = STAGE / "logs" / "launch_check"

GROUP_VPT = {"OPN": 16, "OPN2": 17, "OPM": 25, "OPZ": 26, "OPL": 32, "OPL2": 33,
             "OPL3_2": 34, "OPL_RHY": 35, "OPLL": 40, "OPLLP": 41, "OPLLX": 42,
             "VRC7": 43, "OPLLEX": 44, "OPL3": 48, "SSG": 64, "ADPCMB": 81,
             "ADPCMA": 82, "AWM": 84, "SSGS_ADPCM": 85}

# FITOMConfig::deviceTypeToVoicePatchType()。内蔵リズム部のうちOPL系だけが
# VoicePatchType(OPL_RHY)を持ち、OPNA/OPLL/DSGのリズム部は持たない。
DEVICE_VPT = {}
for _types, _vpt in [((2, 31), 16), ((3, 32, 33, 4, 10, 11, 34, 35, 36), 17), ((5, 26), 25),
                     ((27,), 26), ((7, 24), 32), ((8, 65), 33), ((25,), 34), ((6, 30), 40),
                     ((29,), 41), ((39,), 42), ((46,), 43), ((64,), 44), ((9, 37), 48),
                     ((61,), 84), ((135, 193), 35), ((1, 15, 21, 22, 19, 63, 14, 67), 64),
                     ((20,), 65), ((16,), 66), ((12,), 67), ((13,), 68), ((17, 18, 68), 72),
                     ((117, 60, 59, 66), 81), ((118,), 82), ((62,), 85)]:
    for _t in _types:
        DEVICE_VPT[_t] = _vpt

# 複合チップでない行は種別を出さないので、ラベルの先頭で判定する。
# 長い名前を先に置く(SCC+ と SCC、OPN2 と OPN)。
LABEL_DEVICE = [("SCC+", 18), ("SCCEX", 68), ("SCC", 17), ("SSGEX", 67), ("SSGS3", 14),
                ("SSG", 1), ("EPSG", 20), ("DCSG", 16), ("SAA", 12), ("VRC7", 46),
                ("OPN2", 3), ("OPN", 2), ("OPM", 5), ("OPZ", 27)]

OPLL_FAMILY = {40, 41, 42, 43, 44}
PSG_FAMILY = {64, 65, 66, 67, 72}
SAMPLE_BASED = {81, 82, 84, 85}
RHYTHM_DEVICES = {17: {0x84}, 40: {0x86, 0xC0}, 68: {0x8D}}
OPLL_ROM_VARIANT = {0: 40, 1: 42, 2: 41, 3: 43}
SOUNDS = ("ok", "fallback")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def devices_of(name: str) -> list[int]:
    log = LOGS / f"{name}.log"
    if not log.exists():
        sys.exit(f"{log} がありません。先に launch_all.ps1 を実行してください")
    out = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(r"Device added: (.*)$", line)
        if not m:
            continue
        label = m.group(1)
        t = re.search(r"type=0x([0-9a-f]+)\)", label)
        if t:
            out.append(int(t.group(1), 16))
        elif not label.startswith("SF2"):
            dev = next((d for key, d in LABEL_DEVICE if label.startswith(key)), None)
            if dev is None:
                sys.exit(f"{name}: 種別の分からないデバイス {label!r}。LABEL_DEVICE に足すこと")
            out.append(dev)
    return out


def merged_banks(profile: dict) -> dict:
    base = load(PROFILES / "unified.bankset.json")
    key_of = {"hw_banks": lambda e: (e["group"], e["bank"]),
              "pcm_banks": lambda e: (e["bank"], e.get("chip")),
              "drum_banks": lambda e: e["prog"]}
    for kind, entries in profile.get("bank_overrides", {}).items():
        if kind.startswith("_"):
            continue
        key = key_of.get(kind, lambda e: e["bank"])
        current = base.setdefault(kind, [])
        for e in entries:
            for i, c in enumerate(current):
                if key(c) == key(e):
                    current[i] = e
                    break
            else:
                current.append(e)
    return base


def bank_file(rel: str) -> Path:
    return (PROFILES / rel).resolve()


class Profile:
    def __init__(self, name: str):
        self.name = name
        self.banks = merged_banks(load(PROFILES / f"{name}.profile.json"))
        self.devices = devices_of(name)
        self.vpts = {DEVICE_VPT.get(d) for d in self.devices}
        self.hw = {}
        for e in self.banks["hw_banks"]:
            vpt = GROUP_VPT[e["group"]]
            if e.get("role") or vpt in SAMPLE_BASED:
                continue
            patches = load(bank_file(e["file"])).get("patches", [])
            self.hw[(vpt, e["bank"])] = {p["prog"]: p for p in patches if "prog" in p}
        # offsets_only のバンクはチップ向けのオフセット表で、FITOM_X は音色を作らない
        self.sample = {(GROUP_VPT[e["group"]], e["bank"])
                       for e in self.banks["hw_banks"] + self.banks["pcm_banks"]
                       if GROUP_VPT[e["group"]] in SAMPLE_BASED and not e.get("offsets_only")}
        self.layered = {e["bank"]: {p["prog"]: p for p in load(bank_file(e["file"]))["patches"]}
                        for e in self.banks["patch_banks"]}

    def accepts_fallback(self, device: int, source: int, patch: dict) -> bool:
        ops = patch.get("ops", [])

        def op(i, key):
            return ops[i].get(key, 0) if i < len(ops) else 0
        if device in (2, 31):
            return source == 17
        if device in (3, 32, 33, 4, 10, 11, 34, 35, 36):
            return source == 16
        if device in (5, 26):
            return source == 26 and not any(op(i, k) for i in range(4)
                                            for k in ("REV", "EGS", "DT3", "WS"))
        if device == 27:
            return source == 25
        if device in (7, 24):
            return source in (33, 34) and op(0, "WS") == 0 and op(1, "WS") == 0
        if device in (8, 65):
            return source == 32 or (source == 34 and op(0, "WS") < 4 and op(1, "WS") < 4)
        if device in (6, 30, 29, 39, 46, 64):
            return (source != DEVICE_VPT[device] and source in OPLL_FAMILY
                    and (patch.get("ext", {}).get("ALG_EXT", 0) & 1) == 0)
        return False

    def triple(self, vpt: int, bank: int, prog: int) -> str:
        """"ok" / "fallback" / "silent"(無音のプレースホルダ) / 失敗の理由"""
        if vpt == 127:
            return "silent"
        if vpt == 112:
            return "ok" if RHYTHM_DEVICES.get(bank, set()) & set(self.devices) else "no-device"
        if vpt == 68:
            return "ok" if 68 in self.vpts else "no-device"
        if bank == 0 and vpt in OPLL_FAMILY:
            if prog & 15 == 0:
                return "rom-empty"
            if vpt == 44:
                return "ok" if 44 in self.vpts else "no-device"
            if OPLL_ROM_VARIANT.get((prog >> 4) & 7) in self.vpts:
                return "ok"
            return "fallback" if 44 in self.vpts else "no-device"
        if vpt in SAMPLE_BASED:
            if (vpt, bank) not in self.sample:
                return "no-bank"
            return "ok" if vpt in self.vpts else "no-device"
        patches = self.hw.get((64 if vpt in PSG_FAMILY else vpt, bank))
        if patches is None:
            return "no-bank"
        patch = patches.get(prog)
        if patch is None:
            return "no-patch"
        if vpt in PSG_FAMILY:
            target = patch.get("ext", {}).get("target_voice_patch_type", 0) or 64
            return "ok" if target in self.vpts else "no-device"
        if vpt in self.vpts:
            return "ok"
        if any(self.accepts_fallback(d, vpt, patch) for d in self.devices):
            return "fallback"
        return "no-device"

    def layered_patch(self, bank: int, prog: int) -> str:
        patches = self.layered.get(bank)
        if patches is None or prog not in patches:
            return "no-layered-patch"
        results = [self.triple(l["voice_patch_type"], l["hw_bank"], l["hw_prog"])
                   for l in patches[prog]["layers"] if l.get("enabled", True)]
        if "ok" in results:
            return "ok"
        if "fallback" in results:
            return "fallback"
        if results and all(r == "silent" for r in results):
            return "silent"
        return results[0] if results else "no-layer"

    def drum_note(self, note: dict) -> str:
        bank, prog = note.get("patch_bank", 0), note.get("patch_prog", 0)
        if note.get("voice_patch_type"):
            return self.triple(note["voice_patch_type"], bank, prog)
        return self.layered_patch(bank, prog)

    def patch_banks(self):
        """(bank, 名前, 鳴る数, 全数, 内訳) を鳴るものだけ"""
        for bank in sorted(self.layered):
            counts = collections.Counter(self.layered_patch(bank, p) for p in self.layered[bank])
            good = sum(counts[s] for s in SOUNDS)
            if good:
                entry = next(e for e in self.banks["patch_banks"] if e["bank"] == bank)
                yield bank, load(bank_file(entry["file"])).get("name"), good, len(self.layered[bank]), counts

    def drum_kits(self):
        """(prog, 名前, 鳴る数, 音のあるノート数, 内訳, ノート範囲) を鳴るものだけ"""
        for e in sorted(self.banks["drum_banks"], key=lambda e: e["prog"]):
            kit = load(bank_file(e["file"]))
            if kit.get("type") == "direct":
                r = self.triple(kit["voice_patch_type"], kit.get("patch_bank", 0),
                                kit.get("patch_prog", 0))
                if r in SOUNDS:
                    n = kit["note_max"] - kit["note_min"] + 1
                    yield e["prog"], kit["name"], n, n, {r: n}, (kit["note_min"], kit["note_max"])
                continue
            counts = collections.Counter(self.drum_note(n) for n in kit["notes"])
            good = sum(counts[s] for s in SOUNDS)
            if good:
                yield e["prog"], kit["name"], good, len(kit["notes"]) - counts["silent"], counts, None


def count_text(good: int, total: int) -> str:
    return f"全{total}" if good == total else f"{good}/{total}"


def print_summary(p: Profile) -> None:
    print(f"== {p.name}")
    for bank, name, good, total, counts in p.patch_banks():
        print(f"  patch bank {bank:3d} {name:32s} {good:3d}/{total} {dict(counts)}")
    for prog, name, good, total, counts, _ in p.drum_kits():
        print(f"  drum prog  {prog:3d} {name[:32]:32s} {good:3d}/{total} {dict(counts)}")


def print_markdown(p: Profile) -> None:
    print(f"<!-- {p.name} -->")
    print("| CC#32 | パッチバンク | 鳴る音色 |\n|---|---|---|")
    for bank, name, good, total, _ in p.patch_banks():
        print(f"| {bank} | {name} | {count_text(good, total)} |")
    print("\n| prog | ドラムキット | 鳴るノート |\n|---|---|---|")
    for prog, name, good, total, _, span in p.drum_kits():
        text = count_text(good, total)
        if span:
            text += f"(ノート{span[0]}-{span[1]})"
        print(f"| {prog} | {name} | {text} |")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*", help="プロファイル名(.profile.json を除く)。省略時は全部")
    ap.add_argument("--markdown", action="store_true", help="マニュアル用の表を出す")
    args = ap.parse_args()
    names = args.names or sorted(f.name[:-len(".profile.json")]
                                 for f in PROFILES.glob("*.profile.json"))
    for name in names:
        (print_markdown if args.markdown else print_summary)(Profile(name))


if __name__ == "__main__":
    main()
