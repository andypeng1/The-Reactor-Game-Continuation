# -*- coding: utf-8 -*-
"""Apply the 0.9 auto-save update to the disk CLAUDE.md and print the stripped body hash.

The old 0.9 text told every round to nag the user for Ctrl+S. The user has now enabled
Studio auto-save, so that rule is retired and is replaced in place. Same edit is applied to
the ModuleScript separately; this script only touches the disk mirror.
"""
import io
import sys

D = r"D:\rblxTRGproject"
P = D + r"\CLAUDE.md"

OLD = (
    "### 0.9 让用户保存\n"
    "**每次改完都要提醒 Ctrl+S。** 124k 部件的改动只在内存里，不保存全丢。"
)
NEW = (
    "### 0.9 保存\n"
    "**用户已开启 Studio 自动保存，不要每次改完都提醒 Ctrl+S。**\n"
    "（2026-09-22 用户原话：「我已经开了自动保存，你无需担心内容丢失」。\n"
    "旧版本这条写的是「每次改完都要提醒」，已作废。）"
)


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


raw = io.open(P, "rb").read()
text = raw.decode("utf-8")

n = text.count(OLD)
print("occurrences of the old 0.9 text: %d" % n)
if n != 1:
    print("*** expected exactly 1 -- ABORT, file untouched ***")
    sys.exit(1)

if NEW in text:
    print("new text already present -- ABORT (idempotent)")
    sys.exit(1)

out = text.replace(OLD, NEW).encode("utf-8")
io.open(P + ".baksec09", "wb").write(raw)
io.open(P, "wb").write(out)

body = out[:327] + out[1653:]
print("CLAUDE.md %d -> %d (delta %+d)" % (len(raw), len(out), len(out) - len(raw)))
print("stripped body = %d  hash = %s" % (len(body), roll(body)))
