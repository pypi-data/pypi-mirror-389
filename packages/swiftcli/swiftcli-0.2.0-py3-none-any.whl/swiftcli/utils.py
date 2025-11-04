from __future__ import annotations

import re


def strip_indent(s: str | None) -> str | None:
    if s is None:
        return None
    pattern = re.compile(r"^[ \t]*(?=\S)", re.MULTILINE)
    indent = min(len(spaces) for spaces in pattern.findall(s))

    if not indent:
        return s

    return re.sub(re.compile(rf"^[ \t]{{{indent}}}", re.MULTILINE), "", s)
