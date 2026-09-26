# -*- coding: utf-8 -*-
r"""One-off: cut CLAUDE.md's sections 2 / 3 / 5 out into docs/, proving the cut is lossless.

Why a script and not hand-editing: the seams have to be exact in BOTH directions. A hand-cut
that drops or doubles one blank line at a seam still reads fine, still parses as markdown, and
still looks right -- the only thing that changes is the reassembled hash, which nobody would
notice until the next Studio round-trip. So: cut, put it back together, compare bytes against
what went in, and only then write.

Reads the pristine pre-split copy (_tools/CLAUDE.md.orig, taken on the first run) so it can be
re-run freely; writes CLAUDE.md and the three satellites.

RE-RUNNING IS DESTRUCTIVE TO LATER HAND-EDITS TO SECTION 0.0. Section 0.0 is the only part of
CLAUDE.md this script authors outright, and the text is baked in below -- so if you edit 0.0 on
disk and then re-run this, the edit is gone. Change SEC00 here and re-run, or do not re-run.

The standing check lives in _tools/verify_docs.py, which reassembles the same way and compares
against the (length, hash) the ModuleScript itself reports.
"""
import io
import os
import re
import shutil
import sys

D = r"D:\rblxTRGproject"
SRC = os.path.join(D, "CLAUDE.md")
BACKUP = os.path.join(D, "_tools", "CLAUDE.md.orig")
DOCS = os.path.join(D, "docs")

# The module image length, as reported by game.ServerScriptService.GameCore.CLAUDE and carried
# in verify_docs.py's EXPECT. Asserted here so a disk that has already drifted from the module
# cannot be "successfully" split -- the split would bake the drift in.
MODULE_LEN = 62580

SEC = re.compile(r"(?m)^## (\d+)\.\s")
HEAD = re.compile(r"(?m)^## ")

KEEP = (0, 1, 4, 6, 7, 8)
MOVE = (2, 3, 5)

PREAMBLE = """# {title}

> 磁盘专属前言 —— 不属于游戏内的 `CLAUDE` ModuleScript，校验脚本按「第一个 `## ` 之前
> 整段丢掉」剥掉，长度写死在 `_tools/verify_docs.py` 里。
>
> 本文是从 `CLAUDE.md` 拆出来的 **{sec}**。权威副本仍然是游戏里的
> `game.ServerScriptService.GameCore.CLAUDE`，改完同一步镜像回模块。
> `CLAUDE.md` 只留每轮都要看的章节；拆的理由与分工见它开头的 §0.0。

"""

PARTS = {
    2: ("docs/SYSTEMS.md", "CLAUDE §2 已完成的系统", "§2 已完成的系统"),
    3: ("docs/TODO.md", "CLAUDE §3 待办事项 / 下一步计划", "§3 待办事项 / 下一步计划"),
    5: ("docs/SNIPPETS.md", "CLAUDE §5 所有关键代码片段", "§5 所有关键代码片段"),
}

SEC00 = """## 0.0 文档同步规则（磁盘专属，不要写回 Studio 的 ModuleScript）

> 下面这一节只存在于磁盘上的 `.md`，**不属于**游戏里的 `CLAUDE` / `PROGRESS` /
> `DECISIONS` / `README` ModuleScript。写回游戏时请删掉本节。

**磁盘 `.md` ↔ 游戏内 ModuleScript 的对应：**

| 磁盘文件 | 游戏内来源 |
|---|---|
| `CLAUDE.md` + `docs/SYSTEMS.md` + `docs/TODO.md` + `docs/SNIPPETS.md` | `game.ServerScriptService.GameCore.CLAUDE` |
| `PROGRESS.md` | `game.ServerScriptService.GameCore.PROGRESS` |
| `DECISIONS.md` | `game.ServerScriptService.GameCore.DECISIONS` |
| `README.md` | `game.ServerScriptService.GameCore.README` |

**为什么 `CLAUDE.md` 拆成了四份（2026-09-23）：** Claude Code 只会自动把 `CLAUDE.md`
塞进每轮上下文，**超过 40.0K 字符就报警**。整份是 45,050 字符，报警就是这么来的。
现在只留每轮都要看的，其余按需读：

| 章节 | 在哪 | 什么时候读 |
|---|---|---|
| §0.0 本节 / §0 血泪教训 / §1 项目概述 / §4 用户偏好 / §6 不能碰 / §7 参考 / §8 总结 | **`CLAUDE.md`**（自动加载） | 每轮 |
| §2 已完成的系统 | `docs/SYSTEMS.md` | 动代码 / 场景之前 |
| §3 待办 / 下一步 | `docs/TODO.md` | 决定做什么之前 |
| §5 关键代码片段 | `docs/SNIPPETS.md` | 抄 / 改任何一段实现之前 |

**章节号一律没动** —— `PROGRESS` / `DECISIONS` 里那几百处 `§2.6`、`§5.9`、`§0.13`
之类的引用继续有效，只是那个「章节」现在落在目录下的另一份文件里。

**硬性规则：任何一次改动之后，同一步就要把文档补齐，不要攒着。**
1. 在 Studio 里改了代码 / 场景 / 配置 → 立刻更新对应的 ModuleScript
   （新阶段进 `PROGRESS`，新的取舍进 `DECISIONS`，结构变化进 `README`）。
2. 同一步把改动镜像到磁盘的 `.md`，两边保持一致。
   **改的是 §2 / §3 / §5 → 镜像进 `docs/` 下对应那份，不是 `CLAUDE.md`。**
3. 镜像时剥掉 Lua 包装（`return [==[` … `]==]`）。
4. 写回游戏时注意 §5.9：内容里不能出现 `]==]` 序列。

**方向约定：** 游戏内的 ModuleScript 是权威（source of truth），磁盘 `.md` 是镜像。
若两边冲突，以游戏内为准，并把差异报告给用户。

**镜像规则（实测出来的，不是推测的，见 `DECISIONS` 96）：**
磁盘文件 = ModuleScript 字符串体「去掉首尾换行、再补回恰好一个换行」，逐字节相等。
模块自己报出 `(长度, 哈希)` 作为基准，校验脚本是 `_tools/verify_docs.py`。

- **绝不能用磁盘算出来的哈希去校验磁盘** —— 那是同义反复，两边同时错也会 PASS。
  `DECISIONS` 95 就是这么踩进去的，而且被吃过两次句号都没发现。
- 校验一律**比哈希、不比字节数**。字节数相同而内容不同是**真实发生过**的
  （PROGRESS 与 DECISIONS 各差一个字符），只比长度必漏。
- **拆开之后 `CLAUDE` 的校验方式跟着变，但没有变松：** 脚本按**章节号**把
  `CLAUDE.md`（剥掉本节）+ `docs/SYSTEMS.md` + `docs/TODO.md` + `docs/SNIPPETS.md`
  **重新拼回整份模块镜像**，再比模块报出的那一对 `(62580, 2b6be228)`。
  三个 part **不需要各自单独的基准哈希** —— 拼回来对不上就是错。这比「逐文件各比一次」
  更强：逐文件比对漏掉的那类漂移（两处同时改错、总长度还凑得巧）在这里必然暴露成
  一个整体哈希不符。脚本另外断言章节集合恰好是 0..8，不重不漏。
- 拆分本身也是量出来的，不是靠眼睛读：`_tools/split_claude.py` 断言
  「拆完再拼 == 拆之前的整份镜像（含 `## 0.0 ` 之前那 327 字节的文档头）」，
  逐字节相等才落盘。**第一次跑它就是在这里翻的车**：那个脚本把自己的前缀一起丢了，
  而它的「无损证明」是在两边都丢了同一段 327 字节的前提下比对的，于是照样 PASS ——
  把丢失范围排除在证明之外的证明，就是本节警告的那个同义反复换了个样子。
  现在的证明含前缀，并额外断言拼回来的长度 = 模块报出的 62580。
  看文件名就知道它是**一次性**的；留下它是因为再拆一次时还要用。
- **`docs/*.md` 开头那段磁盘专属前言**按「第一个 `## ` 之前全部丢掉」剥离，
  长度写死在脚本里，所以改前言会让校验变红 —— 这是有意的，不是麻烦。
"""


def strip_section_00(text):
    """(prefix, rest, block). The verifier's rule, kept in one place.

    Drops ONLY the '## 0.0 ' block. Everything before it -- the document title and the handover
    blurb -- is real module content and has to survive.
    """
    i = text.find("## 0.0 ")
    if i < 0:
        raise SystemExit("no '## 0.0 ' heading -- refusing to touch the file")
    j = text.find("\n## 0. ", i + 5)
    if j < 0:
        raise SystemExit("'## 0.0 ' section never ends -- refusing to touch the file")
    return text[:i], text[j + 1:], text[i:j + 1]


def blocks(text):
    """[(number, block)] split at '## N.' headings; block keeps its trailing blank line.

    '## 0.0 ' deliberately does NOT match SEC: after the '.' the next char is a digit, not
    whitespace. That is why section 0.0 has to be cut separately, and why the cut is asserted.
    """
    ms = list(SEC.finditer(text))
    if not ms:
        raise SystemExit("no '## N.' headings found")
    head = text[:ms[0].start()]
    out = []
    for i, m in enumerate(ms):
        a = m.start()
        b = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out.append((int(m.group(1)), text[a:b]))
    return head, out


def strip_preamble(t):
    """Drop the disk-only preamble: everything before the first line that STARTS with '## '.

    Anchored at the line start on purpose. The preamble's own prose mentions the heading marker
    inside backticks, so a plain find("## ") cuts in the middle of that sentence -- which is
    exactly the bug this function shipped with for one run.
    """
    m = HEAD.search(t)
    if not m:
        raise SystemExit("satellite file has no '## ' heading")
    return t[:m.start()], t[m.start():]


def reassemble(chunks):
    """Module order is the section number, so sorting by it is the whole merge."""
    return "".join(t for _, t in sorted(chunks, key=lambda kv: kv[0]))


def first_diff(got, want):
    a, b = got.encode("utf-8"), want.encode("utf-8")
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return ("first difference at byte %d\n  got : %r\n  want: %r"
                    % (i, a[max(0, i - 60):i + 60], b[max(0, i - 60):i + 60]))
    return "length differs: got %d want %d" % (len(a), len(b))


def main():
    if not os.path.exists(BACKUP):
        shutil.copyfile(SRC, BACKUP)
    root = io.open(BACKUP, "rb").read().decode("utf-8")

    prefix, rest, _ = strip_section_00(root)
    head, blks = blocks(rest)
    if head != "":
        raise SystemExit("unexpected text before the first heading:\n%r" % head[:200])
    if len(blks) != 9 or sorted(n for n, _ in blks) != list(range(9)):
        raise SystemExit("expected sections 0..8 exactly once, got %s" % sorted(n for n, _ in blks))
    bynum = dict(blks)

    want = prefix + reassemble(blks)
    if len(want.encode("utf-8")) != MODULE_LEN:
        sys.exit("*** the pre-split disk is %d bytes, module reports %d -- refusing to split a "
                 "file that has already drifted ***" % (len(want.encode("utf-8")), MODULE_LEN))

    parts = {n: PREAMBLE.format(title=PARTS[n][1], sec=PARTS[n][2]) + bynum[n] for n in MOVE}
    new_claude = prefix + SEC00 + "\n" + "".join(bynum[n] for n in KEEP)

    # ---- the lossless proof: put the pieces back together and compare with what went in ----
    _, rest2, _ = strip_section_00(new_claude)
    h2, cblks = blocks(rest2)
    if h2 != "":
        raise SystemExit("unexpected text before the first heading of the new CLAUDE.md")
    chunks = list(cblks)
    pre_len = {}
    for n in MOVE:
        pre, body_n = strip_preamble(parts[n])
        pre_len[n] = len(pre.encode("utf-8"))
        chunks.append((n, body_n))

    got = prefix + reassemble(chunks)
    if sorted(n for n, _ in chunks) != list(range(9)):
        sys.exit("*** reassembled section set is not 0..8 -- nothing written ***")
    if got != want:
        sys.exit("*** the split is NOT lossless -- nothing written ***\n" + first_diff(got, want))

    os.makedirs(DOCS, exist_ok=True)
    io.open(SRC, "wb").write(new_claude.encode("utf-8"))
    for n in MOVE:
        io.open(os.path.join(D, PARTS[n][0].replace("/", os.sep)), "wb").write(
            parts[n].encode("utf-8"))

    print("input     -> _tools/CLAUDE.md.orig  (%d bytes, prefix %d bytes)"
          % (len(root.encode("utf-8")), len(prefix.encode("utf-8"))))
    print("lossless  -> reassembled %d bytes == pre-split module image %d bytes == module's %d"
          % (len(got.encode("utf-8")), len(want.encode("utf-8")), MODULE_LEN))
    print()
    print("constants for _tools/verify_docs.py")
    print("  CLAUDE section 0.0 block length    : %d" % len(strip_section_00(new_claude)[2].encode()))
    for n in MOVE:
        print("  %-34s: %d" % (PARTS[n][0] + " preamble length", pre_len[n]))
    print()
    for p in (SRC,) + tuple(os.path.join(D, PARTS[n][0].replace("/", os.sep)) for n in MOVE):
        b = io.open(p, "rb").read()
        print("  %-24s %7d bytes %7d chars" % (os.path.relpath(p, D), len(b), len(b.decode("utf-8"))))


if __name__ == "__main__":
    main()
