# -*- coding: utf-8 -*-
"""Cumulative-prefix hashes at section boundaries, disk side, to match the Studio read-back."""
import io

D = r"D:\rblxTRGproject"
MARKS = ["## 1.", "### 1.4", "## 2.", "### 2.1", "### 2.8", "### 2.9", "### 2.10",
         "## 3.", "### 3.1", "### 3.2", "### 3.3", "### 3.4", "## 4.", "### 4.1", "### 4.4",
         "## 5.", "### 5.1", "### 5.7", "### 5.9", "## 6.", "## 7.", "## 8."]


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return h


raw = io.open(D + r"\CLAUDE.md", "rb").read()
body = raw[:327] + raw[1653:]          # strip the disk-only 0.0 section
print("disk body = %d" % len(body))
for m in MARKS:
    i = body.find(m.encode("utf-8"))
    if i < 0:
        print("%-12s MISS" % m.encode("ascii", "replace").decode())
    else:
        print("%-12s @%-6d %08x" % (m, i, roll(body[:i])))
