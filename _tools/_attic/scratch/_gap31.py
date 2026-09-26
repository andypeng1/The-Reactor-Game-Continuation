# -*- coding: utf-8 -*-
"""Confirm the exact bounds and length of the missing 控制室外壳 block."""
import io

D = r"D:\rblxTRGproject"
raw = io.open(D + r"\CLAUDE.md", "rb").read()
body = raw[:327] + raw[1653:]

A = "      且那一层是绑定关键的，留到专门重启内容时做\n".encode("utf-8")
B = "- [ ] 设施外壳 / 房间内部 —— **控制室已完成；".encode("utf-8")

a = body.find(A)
b = body.find(B)
print("anchorA @%d  anchorB @%d" % (a, b))
block = body[a + len(A):b]
print("block bytes = %d" % len(block))
io.open(D + r"\_tools\_block31.txt", "wb").write(block)
print("wrote _tools/_block31.txt")
