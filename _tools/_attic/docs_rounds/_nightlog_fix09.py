# -*- coding: utf-8 -*-
"""Update the round-9 NIGHT_LOG block for the retired 0.9 rule.

Three targeted edits. Only the round-9 block is touched: the earlier rounds' 0.9 lines are
historical records of what those rounds actually did, and rewriting them would falsify the log.
"""
import io
import sys

P = r"D:\rblxTRGproject\NIGHT_LOG.md"

EDITS = [
    (
        "CLAUDE     body=56310   hash=559f6b8e\n",
        "CLAUDE     body=56454   hash=1b7ede6e\n",
    ),
    (
        "> 吃过不止一次「文档里的计数是快照、不是不变量」的亏。\n",
        "> 吃过不止一次「文档里的计数是快照、不是不变量」的亏。\n"
        "\n"
        "> **补记（同一轮，收口之后）**：用户说「我已经开了自动保存，你无需担心内容丢失」，\n"
        "> 于是 §0.9 被作废，`CLAUDE` 又同一步长了 144 字节：\n"
        "> `56310 / 559f6b8e` → **`56454 / 1b7ede6e`**。**上表已按新值更新**，两边仍逐哈希一致。\n"
        "> 恰好又演示了一遍本条在说什么 —— **这两个数是快照，不是不变量。**\n",
    ),
    (
        "**§0.9：改完提醒用户 Ctrl+S。** 本轮改动 = `ControlVisuals` + `GameCoreControlTest`\n"
        "两个脚本，加**四个文档 ModuleScript**，**全在内存里，不 Ctrl+S 就丢。**\n",
        "**§0.9 在本轮收口之后被用户作废了。** 原话：「我已经开了自动保存，你无需担心内容丢失」，\n"
        "所以 §0.9 从「每次改完都要提醒 Ctrl+S」改成了「**不要**每次改完都提醒」。\n"
        "本轮改动 = `ControlVisuals` + `GameCoreControlTest` 两个脚本，加**四个文档 ModuleScript** ——\n"
        "**当时确实只在内存里**，这一句作为历史记录保留，但**以后的轮次不要再念了。**\n",
    ),
]

text = io.open(P, "rb").read().decode("utf-8")

for old, new in EDITS:
    n = text.count(old)
    if n != 1:
        print("*** anchor occurs %d times, expected 1 -- ABORT ***\n%r" % (n, old[:60]))
        sys.exit(1)

for old, new in EDITS:
    if new in text:
        print("*** replacement already present -- ABORT (idempotent) ***")
        sys.exit(1)
    text = text.replace(old, new)

raw = io.open(P, "rb").read()
io.open(P + ".bak09", "wb").write(raw)
out = text.encode("utf-8")
io.open(P, "wb").write(out)
print("NIGHT_LOG.md %d -> %d (delta %+d)" % (len(raw), len(out), len(out) - len(raw)))
