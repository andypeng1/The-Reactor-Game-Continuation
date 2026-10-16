
---

## R13 — 你贴的压力递推里**没有 PEA 项**：是漏写，还是这台控制台不该有 PEA？（2026-10-16，Phase 140）

你这次贴的：

```
fan_pressure_drop = fans * 60
p_base = {s == 1: 110, s == 2: 350, s == 3: 800}
p_temp_mult = {s == 1: 0.01, s == 2: 0.0075, s == 3: 0.005}
dP = p_base + (T * p_temp_mult) - fan_pressure_drop
P_next = P + dP
```

**这四个数一个都不差地就是这台控制台从第一版就在跑的那一行** ——
`calculation.luau:34` 写的是

```
current.Pressure += PressureBenefitState[current.State]
                  + PressureBenefitPreTemp[current.State] * current.Temperature
                  + PressureBenefitPEA[current.PEALevel]
                  - 60 * current.ActiveFan
```

也就是 `p = g[State] - 60·n + s[State]·T + d[PEA]`。**你这一份是它去掉最后那一项 `d`。**

**关键一点：`PressureBenefitPEA = {1: 0, 2: 0, 3: 75, 4: 150}`，第 1 档就是 0** ——
所以你这一份式子**正好是 PEA = 1 档的情形**。两版**在 PEA 关着的时候逐字相同**，
只在把 PEA 拨到 3 档或 4 档时才分开（3 档 +75/拍、4 档 +150/拍）。
PEA 的四个档不是我们编的：`Data/TRGWeb.luau:131-137` 那两个函数
（`increasePEAextractionrate` / `decrease…`）就把档位夹在 **1..4**。

**我按 A 办的（现状）：PEA 留着。** 理由：这一项有**独立来源**
（`calculation.luau` —— 你确认过"那个是准确的" —— 和 `TRGWeb.luau` 的 1..4 档），
而**缺的那一项是缺在你这一份里，不是缺在权威那一行里**；
你这次通篇是在讲**温度**（`dT`、`pure_cbl`、`passive`、冷却），压力那四行看起来是**顺带写一遍**，
所以我把它读成"**PEA = 1 档时的压力递推**"，而不是"把 PEA 从模型里删掉"。

**你要哪一种：**

- **A.（现状）PEA 留着**，你这一份读作 PEA = 1 档的压力递推（两版关着 PEA 时逐字相同）。
- **B. 压力就是这四行** —— 那这台控制台不该有 PEA 项。
  那我要顺带知道**那个滑杆怎么办**（从控制台上拿掉？还是留着但不再进递推）。
  **注意**：`PEA_GAIN` 那三个非零档（75/150）会一起失去读者，
  而它们和 `calculation.luau` 是同一份东西 —— 这一条**不是**我们 remake 里那个
  `Config` 的事，游戏本体一行都不会动（§1.4 第 1 条）。

两条我都能改，改 B 是十分钟的事。你要是没意见，就按 **A** 挂着。
