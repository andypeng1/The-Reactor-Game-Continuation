
## 5.37 接一台「静态美术」的屏：格式从录像读、写回自己验、梯子才算证据（Phase 130）

模块 `src/ReactorBackend/ReadoutPanel.luau`（23956 B）、配置 `Config.Readouts`。
取舍 `DECISIONS_2` 549..554，系统说明 `docs/SYSTEMS.md` §2.25。
**这一套适用于任何「原作者用空脚本驱动、实现不可恢复」的界面件。**

**① 格式不是发明的 —— 原版自己的录像就是规格。**

`Data/originalwatch/*/changes.log` 每一行都是 `旧值 | 新值`，逐字记着**每个 label 观察到
的值**。所以 `'%.0f F'`、`'%.0f PSI'`、`'%.0f GW/H'` 这些**形状**是抄的：

```bash
grep -h 'TempLabel.Text' Data/originalwatch/*/changes.log | head -20
```

顺手能读出**那两个不明显的谓词**：`Target` 什么时候跨进 `TW`（阈值 1000）、
配额条什么时候是 0.01 什么时候是 1。

**② 证据钉不死的数，集中进 Config，不要就地糊。**

```lua
Config.Readouts = {
    Clock = { StartMinute = 710, MinutesPerSecond = 1 },   -- 五份录像的起步/速率
    Format = { Temperature = '%.0f F', Pressure = '%.0f PSI', ... },
    LevelPercent = 25,        -- 引擎给的提取率是「档位」，label 是百分比
    CblPrimingStep = 11,      -- StartupSteps[11] = 'PRIMING ALL COMBUSTION LASERS'
}
```

**每一个数后面写一句它钉在哪份证据上** —— 不然半年后没人知道哪个是量的、哪个是挑的。

**③ 【本轮的坑】`UDim2.Offset` 是整数：写 0.5 读回 0。**

第一版读数停在作者摆的值上，看着像「没写」。**定位它的动作只有一个**：

```lua
p.Size = UDim2.new(1, 0, 0, 0.5)   -- 活写一次
print(p.Size)                       -- 读回 {1, 0}, {0, 0}  -> Offset 被截断
```

0.25 / 0.75 同样归零。**`Scale` 是浮点，照收。**
**所以要写小数，只能骑 `Scale`。** 这条坑安静在：**被截断的 0 和没写过的 0 是同一个数。**

**④ 条驱的是哪一半，从录像读，不从「轴」推。**

三族条**骑的不是同一半**（储液条 `Y.Scale`、CBL 图 `Y.Offset`、配额条 `X.Scale`），
所以配置里声明的是**分量**而不是轴：

```lua
Bars = {
    CblGraph   = { Component = 'YOffset', DisplayFull = 100 },  -- 整数 0..100
    Reservoir  = { Component = 'YScale',  DisplayFull = 1 },
    Energy     = { Component = 'XScale',  DisplayFull = 1 },
},
```

```lua
-- 驱动轴的两半都写，另一根轴整根保留 —— 录像里作者摆的 Y.Scale 会被按回 0
local function barSize(base, component, value, displayFull)
    local f = math.clamp(value, 0, 1) * displayFull
    if component == 'XScale' then return UDim2.new(f, 0, base.Y.Scale, base.Y.Offset) end
    if component == 'YScale' then return UDim2.new(base.X.Scale, base.X.Offset, f, 0) end
    return UDim2.new(base.X.Scale, base.X.Offset, 0, f)
end
```

**⑤ 签名闸按渲染值做，不按状态做摘要。**

```lua
local parts = {}
for _, row in ipairs(textRows) do parts[#parts+1] = string.format(formats[row.kind], row.read(...)) end
for _, row in ipairs(barRows)  do parts[#parts+1] = tostring(barSize(...)) end
local key = table.concat(parts, '|')
if key == lastSignature then return end   -- 安静的一拍一个属性都不写
```

**签名就是那些字符串本身**，所以两个不同的状态**不可能撞在同一个签名上**；
拿 `state.temperature` 之类做摘要就会漏（两个状态可以有同一个摘要）。

**⑥ 故意不接的，`Initialize` 打印出来。**

```lua
print('[ReadoutPanel] tints left alone this phase, no predicate in the evidence: '
    .. 'CBLImageLabel, CPumpImageLabel, FanImageLabel, ...')
print('[ReadoutPanel] driven bars left alone this phase, no map in the evidence: '
    .. 'FanFrame NET C-PUMP FLOW RATE (corpus 0..75, engine 0..9), ...')
```

**一条「量出来的数」和一个「挑的数」在盘上逐字同形**（§0.18）——
把 9 缩到 75 就是给挑的数穿上量出来的数的衣服。**清单不打印就等于不存在**（§0.13）。
**同理，`grep` 出来发现模块头里原来那句「这里没有数据可驱动」是错的，就当场改掉** ——
**一句自信的假话比没有这句更坏**，它会让下一个接手的人放心地不动它。

**⑦ 梯子才是证据，一个「恰好对得上」的值不算。**

CBL 状态标签第一拍读出 `OFFLINE`，和 `Config` 里的词逐字相同 —— **这什么都没证明**
（作者本来就可能摆了那个词）。真正的证据是**走一遍梯子**：

```
t=  0.0  OFFLINE    ph=Ready
t= 72.7  POWERING
t= 85.8  FIRING
t=117.8  ACTIVE     ph=Running
```

**后三个词只有这个模块会发。** 停在与初始值相同的那个值上 = 没有证据。

**⑧ 真机点击证「它是活的」。** 储液条那一下：真点 `C-PUMP 1 ON BUTTON`，
`ControlBinder` 的 oracle 行 `-> C-PUMP 1 ON BUTTON`（**后面没有 `rejected:`**）
+ 读回 `{1, 0}, {0.333333343, 0}` —— **小数**，旧写法写不出来的那种数。
**值本身同时否掉「没写」和「写错那一半」两件事。**

**⑨ 别用 `GetDescendants()[1]` 兜底。** 我读 Main 的图用
`FindFirstChild('BarFrame') or e:GetDescendants()[1]`，拿回一个**合法但无关**的
`{1, 0}, {1, 0}` 并当成证据。**遍历序不是语义序**；
**兜底会把「我找不到」伪装成「我找到了一个」**（§0.26 ② `and/or` 同族）。
找不到就报找不到。
