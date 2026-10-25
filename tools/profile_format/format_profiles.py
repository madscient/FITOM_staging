#!/usr/bin/env python3
"""config/profiles/*.profile.json を、FITOM_X の GUI が保存するときと同じ形
(キーを辞書順に並べ、インデント2、CRLF)に揃える。

GUI はプロファイルを保存するたびにファイル全体をこの形で書き直す。別の形で
コミットしておくと、MIDI ポートを設定しただけでファイル全体の整形差分が出る。

内容は変えない。書き直す前と後を JSON として読んで一致することを確かめ、
重複したキー(読み込むと黙って片方が消える)があるファイルは書き直さずに止める。

使い方:
    python tools/profile_format/format_profiles.py            # 揃える
    python tools/profile_format/format_profiles.py --check    # 揃っていないファイルを挙げ、あれば終了コード1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parents[2]
PROFILES = STAGE / "config" / "profiles"


def _reject_duplicates(pairs):
    keys = [k for k, _ in pairs]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        raise ValueError(f"duplicate keys: {dup}")
    return dict(pairs)


def gui_format(data) -> str:
    # 索引上は eol=crlf の checkin 変換で LF になる。作業ツリーは GUI と同じ CRLF。
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return text.replace("\n", "\r\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    bad = []
    for path in sorted(PROFILES.glob("*.profile.json")):
        raw = path.read_bytes().decode("utf-8")
        try:
            data = json.loads(raw, object_pairs_hook=_reject_duplicates)
        except ValueError as e:
            print(f"ERROR {path.name}: {e}", file=sys.stderr)
            return 2
        text = gui_format(data)
        if raw.replace("\r\n", "\n") == text.replace("\r\n", "\n"):
            continue
        bad.append(path.name)
        if args.check:
            continue
        if json.loads(text) != data:
            print(f"ERROR {path.name}: content changed by reformatting", file=sys.stderr)
            return 2
        path.write_bytes(text.encode("utf-8"))

    label = "not in GUI format" if args.check else "reformatted"
    for name in bad:
        print(f"{label}: {name}")
    print(f"{len(bad)} file(s) {label}")
    return 1 if (args.check and bad) else 0


if __name__ == "__main__":
    sys.exit(main())
