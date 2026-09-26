"""One-shot: Phase 51 (version control + push) + DECISIONS 142 + QUESTIONS P5.

Same discipline as patch_docs_50.py: every anchor is resolved and asserted up
front, and nothing is written until all of them have been found.
"""
import sys
from pathlib import Path

ROOT = Path(r'D:\rblxTRGproject')


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def write(path, text, before):
    (ROOT / path).write_text(text, encoding='utf-8', newline='\n')
    print('%-26s %7d -> %7d chars' % (path, before, len(text)))


def append(path, block):
    text = read(path)
    before = len(text)
    if not text.endswith('\n'):
        text += '\n'
    write(path, text + block, before)


PROGRESS_APPEND = """
---

## Phase 51 — 上版本控制，推到 GitHub（`The-Reactor-Game-Continuation`）[DONE]

**日期：** 2026-09-27 00:05。**触发：** 用户给了仓库地址并说「既然你能 git，那 push 吧」。
**对象：** 工作文件夹本身，不是游戏。

### 51.1 之前是什么都没有

`D:\\rblxTRGproject` **从来没有过 `.git`**（`/c/Users/andypeng1NB/BloxBot` 和 `D:\\BloxBot` 也没有）。
远端 `https://github.com/andypeng1/The-Reactor-Game-Continuation` 是 **public**、MIT、
只推过一次（`e299752`，2026-09-17），里面**只有 3 个文件**：
`LICENSE` / `README.md` / `reactor_telemetry.txt`。

### 51.2 做了什么

| 步骤 | 结果 |
|---|---|
| `git init -b main` | — |
| 初始提交 | `3ed1dd4`，**173 个文件 / 9.04 MB** |
| 与 `origin/main` 合并 | `--allow-unrelated-histories`（两边没有共同祖先），只有 `README.md` 冲突（add/add） |
| 冲突解决 | **取本地那份** —— 它已经把远端那段「This project was inspired by…」前言抄进去了，所以两边的内容都在 |
| 推送 | `e299752..3461509  main -> main` |
| 远端核对 | 树里 **191 项**，`LICENSE` 和 `reactor_telemetry.txt` 原样保留 |

最终 **175 个文件**在版本控制里。

### 51.3 故意没进去的四个东西

`.gitignore` 里每一条都写了理由 —— 因为**忽略文件是以后唯一会有人去看的地方**：

| 排除 | 大小 | 为什么 |
|---|---|---|
| `_tools/models/` | **5986 MB** | whisper 模型缓存，可重建 |
| `TRG Sounds & Images pack/` + `.zip` | **426 MB** | 原版游戏的拆包资产；zip 另外还超 GitHub 单文件 **100 MB 硬限** |
| `Videos/` | **104 MB** | 三个**第三方 YouTube 攻略视频**，只是拿来本地转写的 |
| `.ai/`、`.claude/settings.local.json`、`scheduled_tasks.lock` | <1 MB | 机器本地缓存 / 本地权限状态 |

**总盘子 6527 MB → 进仓库 9.04 MB。** 排除的 99.9% 是模型缓存；
**但排除清单不只是关于大小** —— 资产包 214 MB、视频 104 MB 都在 GitHub 限额以内，
它们被排掉是因为**不是我们的东西**，这个判断文件大小替你做不了。

**保留的：** `src/`（ReactorBackend 本体）、全部 `.md` 文档、`docs/`、
`Data/`（含 7 份 `flow/original_*` 采集文件 + `DataCollection.Log`）、
`_tools/`（去掉 `models/`）、`baseline/`、`Addition/`、`Run.ps1`。

### 51.4 顺带定了一件以前没有的事：行尾

全局 `core.autocrlf=true` 会在 checkout 时**把每一份 `.md` 改写成 CRLF** ——
而这个工程的文档是**按字节当工件**的（`DECISIONS` 96 就是「长度相同、内容不同」
那个真出过的 bug）。所以加了 `.gitattributes` 钉成 `* text=auto eol=lf`，
并把这个 repo 的 `core.autocrlf` 设成 `false`。仓库里存 LF，工作区那份下次
checkout 才会跟着变。

### 51.5 留了一条给用户拍板

`Data/TRGWeb.luau`（357 行）、`Data/DataCollection.luau`（489 行）、
`Data/Summary01.luau`（37 行）是**原版游戏 ModuleScript 的逐字副本**，
现在跟着 public 仓库公开了。已进 `QUESTIONS.md` **P5**。
"""


DECISIONS_APPEND = """
142. A PUBLIC REPO IS A DIFFERENT ARTIFACT FROM A WORKING FOLDER, AND WHAT IT LEAVES OUT IS THE DECISION.

    WHAT HAPPENED. The working folder had never been a git repo. Turning it into one and pushing it
    to a public GitHub repo needed a judgement per top-level entry rather than a single `git add
    -A`, because the folder held 6527 MB whose only sensible destination was 9.04 MB of it.

    WHY NOT JUST ADD EVERYTHING. Three of the four exclusions are not about size at all, which is
    the part a size threshold would have got wrong. 5986 MB of whisper model cache is merely
    wasteful -- rebuildable, and no repo wants it. But 426 MB of unpacked game assets and 104 MB of
    third-party YouTube guides are *within* GitHub's limits and were excluded because they are
    someone else's work, and a rule of "ignore files over N MB" would have published them. The
    fourth, the machine-local vision and permission caches, is excluded because it is state that
    would only ever conflict.

    AND ONE THING THAT WOULD HAVE BEEN LOST SILENTLY. `core.autocrlf` was true, which rewrites
    every .md on checkout. In most repos that is cosmetic. Here the documentation is the artifact
    -- DECISIONS 96 is a bug that turned on two files of equal byte length and different content,
    and the whole doc-verification apparatus of that era was built to notice exactly that class of
    drift. A VCS quietly re-encoding every document would have defeated it at the storage layer
    while every check stayed green. So line endings are pinned in .gitattributes and the repo's
    autocrlf is off, rather than trusting a global Windows default that was set for someone else's
    C# project.

    HOW TO APPLY. Sort every candidate by "is this ours to publish", then "can it be rebuilt", then
    by hard limits -- in that order, because the size filter runs last and only catches the
    cheapest mistakes. Write the reason into .gitignore itself rather than into a commit message:
    the commit message scrolls away, and the ignore file is the one place a future reader looks
    when they wonder why something is missing. And when the artifact is bytes you are on record
    about, pin the encoding instead of inheriting a global default.

    THE PART THAT IS NOT MINE TO DECIDE. Three files under Data/ are verbatim copies of the
    original game's ModuleScript source, and they are now public. That is a legal exposure rather
    than a technical one, so it is recorded as a question for the operator (QUESTIONS P5) rather
    than settled here.
"""


CLAUDE_P51 = """

**Phase 51 —— 上版本控制，推到 GitHub（`The-Reactor-Game-Continuation`）。**
工作文件夹以前**从来没有 `.git`**。远端 public、MIT、原本只有 `LICENSE` / `README.md` /
`reactor_telemetry.txt` 三个文件。本地初始提交 `3ed1dd4`，与 `origin/main` 的 `e299752`
**无关历史合并**成 `3461509` 推上去，最终 **175 个文件**在版本控制里。
**6527 MB → 9.04 MB**：`.gitignore` 排掉 **5986 MB** whisper 模型缓存、
**426 MB** 原版拆包资产（zip 另超 100 MB 硬限）、**104 MB** 三个第三方 YouTube 视频、
本地缓存。**排除清单不只是关于大小** —— 资产和视频都在限额以内，排掉是因为**不是我们的东西**。
顺带把行尾钉成 LF（`.gitattributes` + `core.autocrlf=false`）：全局 autocrlf 会在 checkout 时
改写每一份 `.md`，而这个工程的文档**按字节当工作**（`DECISIONS` 96）。
**留了一条**：`Data/TRGWeb.luau` / `DataCollection.luau` / `Summary01.luau` 是原版源码的
逐字副本，现在公开了 —— 见 `QUESTIONS.md` **P5**。"""


P5_NEW = """## P5 — 🟡 `Data/` 里三份「原版源码逐字副本」现在跟着 public 仓库公开了，要不要撤

**仓库是 public 的**，MIT，署名是你。这三份是**原版游戏 ModuleScript 的逐字副本**：

| 文件 | 行数 |
|---|---|
| `Data/TRGWeb.luau` | 357 |
| `Data/DataCollection.luau` | 489 |
| `Data/Summary01.luau` | 37 |

它们**已经推上去了**（`3461509`）。

| 选项 | 意思 |
|---|---|
| **P5:A** | **留着。** 整个项目本来就是「原版没了，把它续下去」，仓库自己的 README 就是这么写的；而且 `DECISIONS` 里几百处引用这三个文件。 |
| **P5:B** | **撤掉。** `git rm` 三份 + 一个 commit 就完事（约一分钟），`DECISIONS` 里的引用改成「见原版 place 的对应模块」的说明。 |

**我倾向 A**，理由：项目目的写在它自己的 README 里，而且你之前就把 `reactor_telemetry.txt`
公开了 —— 那不是巧合，是你已经在做同一个判断。
**但这是版权风险，不是技术风险，只有你能拍板。** 说一句 `P5:B` 我就撤。

"""


def find(lines, pred, what):
    for i, ln in enumerate(lines):
        if pred(ln):
            return i
    sys.exit('QUESTIONS.md: no line matching %s' % what)


def splice_questions():
    """Insert P5 between P4 and B2.

    Anchoring on the `---` before B2 (which is what the Phase 50 splice did) is
    wrong here: that script walked back over the blank lines ABOVE the `---`, so
    the rule it left behind sits above P4, not below it.  Anchor on `## B2`
    itself and supply the separator, rather than trusting a `---` to be where
    the name says it is.
    """
    path = 'QUESTIONS.md'
    before = len(read(path))
    lines = read(path).split('\n')
    i_p4 = find(lines, lambda s: s.startswith('## P4 —'), '## P4')
    i_b2 = find(lines, lambda s: s.startswith('## B2 —'), '## B2')
    if i_p4 >= i_b2:
        sys.exit('QUESTIONS.md: B2 does not follow P4')

    head = lines[:i_b2]
    while head and head[-1].strip() == '':
        head.pop()
    out = head + [''] + P5_NEW.split('\n')[:-1] + ['', '---', ''] + lines[i_b2:]

    # tidy the seams: at most one blank line anywhere, and a blank line before
    # every heading and after every rule
    tidy = []
    for ln in out:
        if ln.strip() == '' and tidy and tidy[-1].strip() == '':
            continue
        if ln.startswith('#') and ln.lstrip('#').startswith(' ') and tidy and tidy[-1].strip() != '':
            tidy.append('')
        if ln.startswith('## ') and tidy and tidy[-1].strip() != '':
            tidy.append('')
        if ln.strip() == '---' and tidy and tidy[-1].strip() != '':
            tidy.append('')
        if tidy and tidy[-1].strip() == '---' and ln.strip() != '':
            tidy.append('')
        tidy.append(ln)

    text = '\n'.join(tidy)
    for needle in ('## P4 — 🟡', '## P5 — 🟡', '## B2 — ✅', '## P3 — 📌'):
        if text.count(needle) != 1:
            sys.exit('QUESTIONS.md: %r appears %d times after the splice'
                     % (needle, text.count(needle)))
    if text.count('\n---\n') != sum(1 for l in tidy if l.strip() == '---'):
        sys.exit('QUESTIONS.md: a rule ended up adjacent to another line')
    write(path, text, before)


def splice_claude():
    path = 'CLAUDE.md'
    text = read(path)
    before = len(text)
    anchor = '这是第一次有外部见证确认 tick ≈ 1.8 s。'
    n = text.count(anchor)
    if n != 1:
        sys.exit('CLAUDE.md: the Phase 50 tail matched %d times' % n)
    i = text.index(anchor) + len(anchor)
    write(path, text[:i] + CLAUDE_P51 + text[i:], before)


def main():
    q = read('QUESTIONS.md')
    for needle in ('## P4 —', '## B2 —'):
        if q.count(needle) != 1:
            sys.exit('QUESTIONS.md: %r appears %d times' % (needle, q.count(needle)))
    c = read('CLAUDE.md')
    if c.count('这是第一次有外部见证确认 tick ≈ 1.8 s。') != 1:
        sys.exit('CLAUDE.md: the Phase 50 anchor is not unique')
    if 'Phase 51' in read('PROGRESS.md'):
        sys.exit('PROGRESS.md already has a Phase 51 -- not running twice')

    splice_questions()
    splice_claude()
    append('PROGRESS.md', PROGRESS_APPEND)
    append('DECISIONS_2.md', DECISIONS_APPEND)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
