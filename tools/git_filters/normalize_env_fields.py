#!/usr/bin/env python3
"""git clean フィルタ: config/profiles/配下のJSONにある環境依存フィールド
(MIDI入力デバイス名・実機シリアルポート名)をプレースホルダーへ正規化する。

対象は正規表現によるテキスト置換のみで、それ以外のJSONフォーマット
(インデント・改行コード・キー順序等)には一切触れない。フルパース→
再ダンプ方式は、単一行に詰めて書かれたオブジェクト(例:
hw_plugins/fitom_hw_*.profile.jsonのslots配列)を複数行に展開して
しまい無関係な差分を生むため採用しない。

.gitattributes側で `config/profiles/**/*.json filter=envlocal` を
指定し、`git config filter.envlocal.clean "python tools/git_filters/
normalize_env_fields.py"` / `filter.envlocal.smudge cat` をローカルに
登録して使う(setup.ps1/setup.shが自動登録する)。
"""
import os
import re
import sys

if sys.platform == "win32":
    # Windows上ではsys.stdin/stdout.bufferでもOSレベルの改行変換
    # (テキストモード)がかかる場合があり、CRLFがLFに化けてしまう。
    # gitのclean/smudgeフィルタはパイプ経由でバイナリのまま渡す
    # 前提のため、明示的にバイナリモードへ固定する。
    import msvcrt

    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

PLACEHOLDER = "__LOCAL__"

_STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"')
_MIDI_INPUTS_RE = re.compile(r'("midi_inputs"\s*:\s*\[)(.*?)(\])', re.DOTALL)
_PORT_RE = re.compile(r'("port"\s*:\s*)"(?:[^"\\]|\\.)*"')


def _normalize_midi_inputs(text: str) -> str:
    def repl(m: "re.Match[str]") -> str:
        head, body, tail = m.group(1), m.group(2), m.group(3)
        body = _STRING_RE.sub(f'"{PLACEHOLDER}"', body)
        return head + body + tail

    return _MIDI_INPUTS_RE.sub(repl, text)


def _normalize_port(text: str) -> str:
    return _PORT_RE.sub(rf'\1"{PLACEHOLDER}"', text)


def normalize(text: str) -> str:
    text = _normalize_midi_inputs(text)
    text = _normalize_port(text)
    return text


def main() -> None:
    data = sys.stdin.buffer.read().decode("utf-8")
    sys.stdout.buffer.write(normalize(data).encode("utf-8"))


if __name__ == "__main__":
    main()
