"""inbox.txt に貼り付けたテキストを投稿単位に分割する。"""

import re
from dataclasses import dataclass

# Threads の1投稿あたりの文字数上限
MAX_CHARS = 500

SEPARATOR = re.compile(r"^\s*-{3,}\s*$", re.MULTILINE)
META_LINE = re.compile(r"^\s*(ジャンル|genre|アカウント|account)\s*[:：]\s*(.+?)\s*$", re.IGNORECASE)


@dataclass
class Draft:
    text: str
    genre: str | None = None
    account: str | None = None


@dataclass
class ParseError:
    index: int  # 何番目のブロックか（1始まり）
    message: str
    raw: str


def parse_inbox(raw: str) -> tuple[list[Draft], list[ParseError]]:
    """`---` 区切りのテキストを Draft のリストに変換する。

    各ブロックの先頭にある「ジャンル: xxx」「アカウント: xxx」の行はメタ情報として扱い、
    残りを投稿本文とする。
    """
    drafts: list[Draft] = []
    errors: list[ParseError] = []

    blocks = [b for b in SEPARATOR.split(raw) if b.strip()]
    for i, block in enumerate(blocks, start=1):
        lines = block.strip("\n").splitlines()
        genre = account = None

        # 先頭の空行とメタ行だけを読み取る
        while lines:
            if not lines[0].strip():
                lines.pop(0)
                continue
            m = META_LINE.match(lines[0])
            if not m:
                break
            key = m.group(1).lower()
            if key in ("ジャンル", "genre"):
                genre = m.group(2)
            else:
                account = m.group(2)
            lines.pop(0)

        text = "\n".join(lines).strip()
        if not text:
            errors.append(ParseError(i, "本文が空です", block.strip()))
            continue
        if len(text) > MAX_CHARS:
            errors.append(ParseError(i, f"{MAX_CHARS}文字を超えています（{len(text)}文字）", block.strip()))
            continue
        drafts.append(Draft(text=text, genre=genre, account=account))

    return drafts, errors
