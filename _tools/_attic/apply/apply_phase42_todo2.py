# -*- coding: utf-8 -*-
"""Phase 42 follow-up on docs/TODO.md: two live references that Phase 42 invalidated.

WHY THIS FILE EXISTS. Neither of these is a retraction of a claim; both are places where a LIVE
reference in the to-do list stopped being true the moment Phase 42 was written, and section 0.0
requires the same step to carry them.

  (a) line 226 gave DECISIONS_2's entry range and size as "75..123, 102387 bytes". Entry 124 makes
      both halves wrong. The byte counts are dropped rather than corrected: they go stale every
      phase, and the sentence immediately after already says the boundary is an entry number and not
      a byte offset, so the counts were contradicting their own paragraph. PROGRESS Phase 41 keeps
      the split-day numbers, which is where a historical figure belongs.
  (b) the coolant station's three LEDs show no pump level and never have. DECISIONS 124 closed the
      flash bug and deliberately did NOT answer which control should own those LEDs, because that is
      a design question. An open design question that is only recorded inside a decisions entry is
      not on anyone's list, so it goes here too.

Anchors are asserted to occur exactly once (DECISIONS 124's own lesson, and section 0.13).
Run with 'check' to see the deltas without writing.
"""
import io
import os
import sys

D = r"D:\rblxTRGproject"
REL = os.path.join("docs", "TODO.md")

A_OLD = """      现在拆成 **`DECISIONS`（条目 1..74，103355 字节）+ `DECISIONS_2`（条目 75..123，102387 字节）**，
"""
A_NEW = """      现在拆成 **`DECISIONS`（条目 1..74）+ `DECISIONS_2`（条目 75..124）**，
"""

# Inserted immediately before section 3.3, i.e. at the end of the open-items part of 3.2.
B_OLD = """### 3.3 测试覆盖缺口
"""
B_NEW = """- [ ] **冷却液站的三盏灯不显示泵档位 —— `DECISIONS` 124 的遗留项，故意没顺手改。**
      `RebuildKit` 把它们描述成「三盏灯显示泵的档位」，而 `lampState` 对 `coolant_pump_level`
      没有分支，所以档位**从来没有被显示过**（不是 Phase 40 之后坏的）。
      档位本身是**四态**（`off / 1 / 2 / 3`，实测该拉杆 `detent=4`），三盏灯正好够做条状或三位的读数，
      所以「三盏灯」这个设计未必错。不知道的是**谁该拥有它们**：原版把灯留在站上
      （`OnButton`/`OffButton` 自己没灯），而现在先绑上的 `coolant_pump_on` 拿走了它们。
      调换两行绑定顺序就能改观，但那等于拿测试场景去猜 —— 先记下来，不当场答。

### 3.3 测试覆盖缺口
"""

EDITS = [(A_OLD, A_NEW), (B_OLD, B_NEW)]


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return "%08x" % h


def main():
    dry = "check" in sys.argv
    path = os.path.join(D, REL)
    raw = io.open(path, "rb").read()
    text = raw.decode("utf-8")
    before = roll(raw)
    rc = 0
    for old, new in EDITS:
        n = text.count(old)
        label = old.strip().splitlines()[0][:52]
        if n != 1:
            print("*** anchor occurs %d times: %s ***" % (n, label))
            rc = 1
            continue
        text = text.replace(old, new)
        print("replaced (%+d bytes): %s" % (len(new.encode()) - len(old.encode()), label))
    if rc:
        print("*** nothing written ***")
        return rc
    out = text.encode("utf-8")
    if not dry:
        io.open(path, "wb").write(out)
    print("%s -> %s  hash %s -> %s%s" % (len(raw), len(out), before, roll(out),
                                         "  (dry run)" if dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
