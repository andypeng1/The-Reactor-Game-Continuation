# -*- coding: utf-8 -*-
"""Append the session-close status note to NIGHT_LOG.md (disk-only doc, no module mirror).

The round-10 entry already records the freeze and the staged SpawnKit. What changed AFTER it
was written is the Studio state itself: it went from "one instance listed but its Luau channel
is wedged" to "no instance connected at all". That is a different state with a different
meaning, and the next session should not have to rediscover which one it inherited.
"""
import io
import sys

P = r"D:\rblxTRGproject\NIGHT_LOG.md"

SENTINEL = "会话收尾时的状态"

BLOCK = r"""
### 10. 会话收尾时的状态（2026-09-23）

**Studio 现在是「完全未连接」，不再是「连着但卡死」。**

```
rblx_list_roblox_studios  ->  {"studios":[]}
```

这是**新的状态**，与上面 §4–§5 记的那种「1 个实例、能列出来、但 `rblx_execute_luau`
永远 `Target is not reachable`」**不是同一回事**，别把两者混为一谈。它有两种来源：

- 用户**已经关掉** Studio —— 那 §5 那段「要不要强行 close」的判断自然作废，卡死的线程随进程消失；
- 用户**正在重启**，place 还没载入完 —— 这个 place 有 127,111 个部件，载入要几分钟。

**两种都不需要我这边做任何事**：桥等的是「一个 place 被打开」这个事件，
不是我能推的。所以本轮到此停手。

**本轮（第十轮之后到收尾为止）没有任何新的磁盘产物。** 逐项点清：

| 东西 | 谁写的 | 本轮动了吗 |
|---|---|---|
| `_tools/SpawnKit.lua` | 上一段 | 没有 |
| `NIGHT_LOG.md` 第十轮 | 上一段 | 只加了本条 §10 |
| `PROGRESS` / `DECISIONS` / `README` / `CLAUDE` 及其磁盘镜像 | 更早 | **一个字节都没动** |
| 场景 | —— | **一个字节都没写** |

本轮的净输出 = **对 Studio 状态的若干次探测 + 若干次等待**。
**没有任何场景改动处于风险中**（理由同 §5：能写进场景的要么是只读探针、
要么是两次 Play，而 Play 的写入是运行时副本、停止即丢）。

**桥恢复后第一件事，清单与 §8 完全一致，没有变化：**
装 `SpawnKit` → `Scan()`（顺便读出版权属的 `Enabled`，它回答 §3 的「三种读法」哪一种是真）
→ `ApplyAll()` → `Verify()`（期望 `usableInRoom = 4`、`strayUsable = 0`）
→ Play 实测角色是否出现在**控制室里、正对控制台排**。
然后**同一步**补 `PROGRESS` 一个新 phase + `DECISIONS` 一条（§1.4）。
**不要直接跳到 `ApplyAll()`** —— `SpawnKit.lua` 从来没被执行过、也没被语法检查过
（这台机器没有任何 Lua 解释器）。
"""

raw = io.open(P, "rb").read()
old = raw.decode("utf-8")

if SENTINEL in old:
    print("close-note already present -- ABORT")
    sys.exit(1)

if not old.endswith("\n"):
    old += "\n"

out = (old + BLOCK).encode("utf-8")
io.open(P + ".bak10c", "wb").write(raw)
io.open(P, "wb").write(out)
print("NIGHT_LOG.md %d -> %d (delta %+d), backup NIGHT_LOG.md.bak10c"
      % (len(raw), len(out), len(out) - len(raw)))
