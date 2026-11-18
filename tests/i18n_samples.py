"""Примеры строк интерфейса для проверки перевода: литералы status/confirm/prompt/title из index.html
и f-строки ошибок из app.py с подставленными значениями."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _fill(tpl):
    """`…${x}…` → пример: условные вставки (с ?) убираем, остальные — «3» или «X» в кавычках."""
    out, i, depth, start = [], 0, 0, None
    s = tpl
    res = ""
    j = 0
    while j < len(s):
        if s.startswith("${", j):
            k, d = j + 2, 1
            while k < len(s) and d:
                d += {"{": 1, "}": -1}.get(s[k], 0)
                k += 1
            expr = s[j + 2:k - 1]
            before = res[-1:] if res else ""
            if "join(" in expr or "map(" in expr:
                val = "1, 2"
            elif " ? " in expr or re.search(r"[^?.]\?[^.?]", expr):   # условие (не «?.») — первая ветка
                sep = " ? " if " ? " in expr else "?"
                branch = expr.split(sep, 1)[1].rsplit(":", 1)[0].strip()
                if branch[:1] in "\"'`" and branch[-1:] == branch[:1]:
                    val = _fill(branch[1:-1])
                elif "." in branch or "(" in branch:
                    val = "3"
                else:
                    val = "3"
            elif before in ('"', "“", "«") or re.search(r"name|label|base|rel|path|title|when|msg|message|err", expr, re.I):
                val = "Xname"
            else:
                val = "3"
            res += val
            j = k
        else:
            res += s[j]
            j += 1
    return res.replace("\\n", "\n").replace('\\"', '"')


def ui_samples():
    src = (ROOT / "static" / "index.html").read_text("utf-8")
    script = src[src.index("<script>\n"):]
    out = set()
    for m in re.finditer(r"\b(?:status|confirm|prompt|ask|askText)\(\s*(`(?:[^`\\]|\\.)*`|\"(?:[^\"\\]|\\.)*\")", script):
        out.add(_fill(m.group(1)[1:-1]))
    for m in re.finditer(r'class="hint"[^>]*>([^<$`]{20,})', src):     # абзацы-подсказки
        out.add(m.group(1))
    for m in re.finditer(r'\btitle="([^"]+)"', src):
        if "${" not in m.group(1):
            out.add(m.group(1))
    clean = set()
    for s in out:
        s = re.sub(r"[ \t]+", " ", s).strip()
        # начинается с подставленной переменной или обрывается на кавычке — сборку не угадать, проверяется отдельно
        if re.match(r"^(3|:)", s) or s.endswith('"'):
            continue
        if re.search(r"[A-Za-z]{3}", s) and not re.fullmatch(r"[\w .:/-]*Xname[\w .:/-]*", s):
            clean.add(s)
    return sorted(clean)
