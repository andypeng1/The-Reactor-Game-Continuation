# -*- coding: utf-8 -*-
"""Dump the disk window around the 1,593-byte gap so it can be read as text."""
import io

D = r"D:\rblxTRGproject"
raw = io.open(D + r"\CLAUDE.md", "rb").read()
body = raw[:327] + raw[1653:]

seg = body[26072:27900]
io.open(D + r"\_tools\_disk31.txt", "wb").write(seg)
print("disk window %d bytes -> _tools/_disk31.txt" % len(seg))
