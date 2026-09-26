# Codex — 项目交接文档

> 交接目标：Roblox 游戏《反应堆游戏》的开发工作。
> 上一任 AI 助手（deepseek-v4-flash + Roblox Studio MCP）已完成仿真核心、控制系统、
> 监视器与视觉基础层。本文档记录全部上下文，供无缝接手。
>
> 生成时间：2026-09-21

---

## 0.0 文档同步规则（磁盘专属，不要写回 Studio 的 ModuleScript）

> 下面这一节只存在于磁盘上的 `.md`，**不属于**游戏里的 `Codex` / `PROGRESS` /
> `DECISIONS` / `README` ModuleScript。写回游戏时请删掉本节。

**磁盘 `.md` ↔ 游戏内 ModuleScript 的对应：**

| 磁盘文件 | 游戏内来源 |
|---|---|
| `AGENTS.md` + `docs/SYSTEMS.md` + `docs/TODO.md` + `docs/SNIPPETS.md` | `game.ServerScriptService.GameCore.Codex` |
| `PROGRESS.md` | `game.ServerScriptService.GameCore.PROGRESS` |
| `DECISIONS.md` | `game.ServerScriptService.GameCore.DECISIONS`（条目 1..74） |
| `DECISIONS_2.md` | `game.ServerScriptService.GameCore.DECISIONS_2`（条目 75..） |
| `README.md` | `game.ServerScriptService.GameCore.README` |

**为什么 `DECISIONS` 也拆成了两份（2026-09-23）：** 跟 `AGENTS.md` 那次**不是同一类问题**。
`ModuleScript.Source` 有**引擎硬上限 200000 字节**，写入 202893 的那次是**直接被拒绝**的
（`Provided string length (202910) ... max length (200000)`），没有预算可调，只能拆。
边界定在**条目 75** —— 是条目号，不是字节偏移，所以它是文档的性质而不是当天长度的性质。
**这两个磁盘文件不是 `docs/` 卫星文件，没有磁盘专属前言**，各自**逐字节等于**自己模块的镜像；
拼回来的规则是 `DECISIONS.md` 去掉尾部换行 + 一个空行 + `DECISIONS_2.md`，校验脚本会断言这条缝。
**`DECISIONS.md` 里含 2 个反斜杠**（早期条目里 Lua 代码片段中的「反斜杠 + n」），
因此这一份**只能在 Studio 内部从已有文本搬移出来，不能通过工具调用传文本**（见 §0.10）。
详见 `DECISIONS` 123。

**为什么 `AGENTS.md` 拆成了四份（2026-09-23）：** Codex 只会自动把 `AGENTS.md`
塞进每轮上下文，**超过 40.0K 字符就报警**。整份是 45,050 字符，报警就是这么来的。
现在只留每轮都要看的，其余按需读：

| 章节 | 在哪 | 什么时候读 |
|---|---|---|
| §0.0 本节 / §0 血泪教训 / §1 项目概述 / §4 用户偏好 / §6 不能碰 / §7 参考 / §8 总结 | **`AGENTS.md`**（自动加载） | 每轮 |
| §2 已完成的系统 | `docs/SYSTEMS.md` | 动代码 / 场景之前 |
| §3 待办 / 下一步 | `docs/TODO.md` | 决定做什么之前 |
| §5 关键代码片段 | `docs/SNIPPETS.md` | 抄 / 改任何一段实现之前 |

**章节号一律没动** —— `PROGRESS` / `DECISIONS` 里那几百处 `§2.6`、`§5.9`、`§0.13`
之类的引用继续有效，只是那个「章节」现在落在目录下的另一份文件里。

**硬性规则：任何一次改动之后，同一步就要把文档补齐，不要攒着。**
1. 在 Studio 里改了代码 / 场景 / 配置 → 立刻更新对应的 ModuleScript
   （新阶段进 `PROGRESS`，新的取舍进 `DECISIONS`，结构变化进 `README`）。
2. 同一步把改动镜像到磁盘的 `.md`，两边保持一致。
   **改的是 §2 / §3 / §5 → 镜像进 `docs/` 下对应那份，不是 `AGENTS.md`。**
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
- **拆开之后 `Codex` 的校验方式跟着变，但没有变松：** 脚本按**章节号**把
  `AGENTS.md`（剥掉本节）+ `docs/SYSTEMS.md` + `docs/TODO.md` + `docs/SNIPPETS.md`
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
- **校验器自己也被验过，不是「看起来能跑」就完事：** `_tools/selftest_verify_docs.py`
  故意改坏一个字节、跑一次、再还原，断言 `rc 0 → 1 → 0`。它顺带把「比哈希不比字节数」
  这条现场演示了一遍 —— 那个改动**总长度一模一样**（`body=62580` 不变），
  只有哈希从 `2b6be228` 掉到 `425080bf`；只比长度的校验器在这里会全绿。
- **`docs/*.md` 开头那段磁盘专属前言**按「第一个 `## ` 之前全部丢掉」剥离，
  长度写死在脚本里，所以改前言会让校验变红 —— 这是有意的，不是麻烦。

## 0. 先读这个（血泪教训，能省你几小时）

### 0.1 Studio MCP 的 studio_id 每次会话都会变
```
先调用 list_roblox_studios，用返回的 id。
不要用 set_active_studio。每个 Studio 相关调用都要带 studio_id。
```
历史上出现过这些 id（都已失效，仅作识别参考）：
`fbc8fbb2-…` → `6de56428-…` → `02ed5559-…` → `1c795da0-…` → `f1fb4960-…`

### 0.2 【最重要的坑】命令栏的 require ≠ 运行脚本的 require
Studio 的 `execute_luau`（Server 数据模型）跑在**独立的 Luau VM** 里。
在那里 `require(GameState)` 会拿到一个**全新的空实例**：
```
GameState.Time = 0        ← 明明游戏在跑
SystemManager.Systems = 0 ← 明明注册了 25 个系统
```
**我因为不知道这点，连续误判了三次「温度没跑」「拉杆没动」，全是假阴性。**

**正确做法：读实例状态，不要读模块状态。**
- 读监视器上的 `TextLabel.Text`
- 读部件的 `CFrame` / `Material` / `Color`
- 读 `ChangeHistoryService`、属性、标签
- 或直接看 `get_console_output` 里的自检输出

### 0.3 编辑 Source 后 require 缓存不会失效
在 Edit 模式改完 `ModuleScript.Source` 后再 `require`，拿到的还是**旧字节码**。
想立刻验证新代码，用：
```lua
local CV = loadstring(modScript.Source)()
```
（Play 模式重新加载脚本时会读新源码，正常。）

### 0.4 在 Play 模式下改 Source 不会保存到工程
我在 Play 期间通过 Server 数据模型改的 `Source`，**只改了运行时副本**，
停止 Play 后全部丢失，必须在 **Edit 模式**重新应用。已踩过这个坑。

### 0.5 Studio 需要「Allow HTTPS」
否则 Play 模式会卡死（`start_stop_play` 一直返回 "hasn't finished yet"）。
用户已经开好了，如果 Play 又卡，先让他确认这个开关。

### 0.6 这台机器没有 Node.js
```
node / npx / npm / bun / pnpm  -> NOT FOUND
winget / choco / scoop          -> NOT FOUND
```
`@6xvl/robloxstudio-mcp` 是 Node CLI，跑不起来。已在项目根写了 `opencode.json`
但需要 Node + 重启 opencode 才生效。

### 0.7 MCP 插件的无害报错
```
loadstring() is not available
Script 'user_MCPPlugin-release.rbxmx.MCPPlugin', Line 5
```
是插件自身问题，不影响游戏逻辑，忽略。

### 0.8 控制台被音效错误刷屏
几百条 `Failed to load sound rbxassetid://…: User is not authorized`。
`get_console_output` 会截断，但**保留的是尾部**。
需要干净输出时先 `game:GetService("LogService"):ClearOutput()`。

### 0.9 保存
**用户已开启 Studio 自动保存，不要每次改完都提醒 Ctrl+S。**
（2026-09-22 用户原话：「我已经开了自动保存，你无需担心内容丢失」。
旧版本这条写的是「每次改完都要提醒」，已作废。）

### 0.10 【坑】编辑层会解码 Lua 转义
通过 Studio 编辑工具写进去的文本会**先被解码一次**：短字符串里的
「反斜杠 + n」两字符会变成真正的换行，转义过的双引号会变成真正的引号 ——
两者都会把合法的 Lua 变成语法错误，而报错指向字符串、不指向工具。
`ControlTrigger` 因此**故意一个反斜杠都不写**：换行用 `local NL = string.char(10)`，
需要内嵌双引号的字符串改用单引号 Lua 语法。这是约定，不是待清理的临时手段。

### 0.11 【坑】官方鼠标工具的 y 不是视口坐标
视口 1020×550 时，请求 `y=275`，读回 `UserInputService:GetMouseLocation()` 得到
**(510, 333)** —— **y 有 +58 px 偏移**，x 没有。请求 `y=217` 读回正好 275.0，据此确认。
这就是头两次物理点击「打在空气上」的原因。
同一工具第二个小坑：`instance_path` **只接受 GuiObject**，对 `Part` 必须自己算像素
（`Camera:WorldToViewportPoint`）。

---

### 0.12 【约定】RS / SS / SSS 的缩写（用户明确定下）

用户原话：「注意:RS=ReplicatedStorage，SS = ServerStorage，SSS = ServerScriptService
（这就是我们约定好的）」。**这是约定，不要再猜、也不要混用。**

| 缩写 | 服务 | 关键性质 |
|---|---|---|
| **RS** | `ReplicatedStorage` | **复制给每个客户端**，但**不渲染、不参与物理** |
| **SS** | `ServerStorage` | 仅服务端；**里面的脚本永远不运行** |
| **SSS** | `ServerScriptService` | 服务端；**脚本在这里运行** |

**三条由此推出的硬结论**（本轮踩过）：
1. 把东西塞进 RS **省不掉客户端的负担** —— 它照样复制过去。真要卸载给客户端，终点是 **SS**。
2. 放在 SS 里的脚本是**惰性**的。统计「谁引用了这个容器」时**必须排除 SS**，
   否则会把死引用算成活引用（`DECISIONS` 91）。
3. RS 里的部件**本来就不渲染**，所以「RS → SS」这种搬迁**画面零变化**，可以直接做；
   而 Workspace 里的部件**正在渲染**，搬走就改变世界，必须先问用户。


## 1. 项目概述

### 0.13 【坑】按子串锚定的编辑会落进错误的块

用 `return CoreKit` 当锚点插代码，而它在文件里第一次出现是在 `return CoreKit.Verify()` 里面
（Build 的尾部），于是整段 —— 连 `function CoreKit.Glow` 一起 —— 被写进了 **Build 的函数体**，
模块从此不导出 Glow，`pcall(CoreKit.Glow, ...)` 每 tick 静默失败一整场。**没有任何症状**：
控制台、灯、七台监视器全部正常，只有「缺失」。

两条纪律：**锚点要么按构造唯一，要么写之前先断言唯一**；**插完要量块深度，不要用眼睛读**
—— 两种情况下文本都长得对：能解析、名字在、错的只有嵌套。量深度的检查器**必须先剥字符串、再剥注释**
—— 反过来会吃掉那行含 `--` 的字符串的收尾引号，给出「Build 从未闭合」这种自信但错误的结论。

顺带：`pcall(f, ...)` 里的 `f` 可能是 `nil`。pcall 是给**会抛错**的被调方用的，不是「可能不存在」
的许可证。名字先查、缺了 warn 一次，pcall 只留给抛错 —— **与成功无法区分的错误路径不是错误处理**。

### 1.1 基本信息
| 项 | 值 |
|---|---|
| 游戏名 | 反应堆游戏（The Reactor Game 的复刻 / 重构） |
| placeId | 114398686378058 |
| 类型 | 科幻反应堆设施维护模拟 |
| 平台 | Roblox / Roblox Studio |
| 工作目录 | `C:\Users\andypeng1NB\BloxBot` |
| 用户语言 | 中文（技术术语夹英文） |

### 1.2 核心玩法
玩家扮演反应堆设施的操作员，在一个**没有控制棒**的反应堆上工作。
（这一点经过 Wiki 反复确认：The Reactor Game 里**不存在控制棒**，
玩家只能通过三个间接手段控制反应堆。）

**三大控制手段：**
1. **环境压力** — AVB（大气排放阀）/ E-VENT（紧急排气）
2. **CBL 强度** — 化学泵浦激光，PW1..PW5 五档
3. **Isotope E 冷却回路** — 3 台冷却泵，每台 0..3 档

**核心循环：**
维持堆芯温度与压力在安全窗口内 → 产生电力 → 完成班次配额 → 应对随机事件 → 撑到交班。

### 1.3 目标受众
- 喜欢**硬核系统管理 / 灾难模拟**的玩家（类似《The Reactor Game》《Barotrauma》受众）
- 享受「读懂仪表 → 判断 → 操作 → 承担后果」的玩家
- 不是休闲玩家：有真实的停堆、熔毁、超压失败状态

### 1.4 绝对约束（用户明确下达，不可违反）
1. **永远不要改现有玩法机制**（NEVER CHANGE EXISTING GAMEPLAY MECHANICS）
2. **不要在没有替代品的情况下删除功能**
3. 每完成一个阶段，更新 `PROGRESS` / `DECISIONS` / `README`
4. 不要停下来假装完成（"不要停在那里谎称做完了"）
5. 改完要做**真实验证**（模拟点击、检查位置与颜色）

---

## 4. 用户的个人偏好

### 4.1 沟通风格
- **说中文**，技术术语夹英文（"拉杆"、"堆芯"、"LeverUnion"、"detach"）
- **极简、直接、有时急躁**。典型发言：
  - 「bro在胡搞，拉杆移动的部分是LeverUnion其他部分都不动啊！！！」
  - 「哎算了你整个游戏重新建模把我看不下去了」
  - 「全部重做，特效与图片资产可使用」
- **不喜欢被反复问**。能自己判断的就自己判断、自己动手。
  只有在真正会破坏东西或需要装软件时才停下来问。
- **会自己去做事**（他自己去装了 MCP server、开了 Allow HTTPS、保存了工程）
- 长时间会话，有时会离开（睡觉），期望你**持续推进**

### 4.2 代码风格偏好
- **注释要多，且解释「为什么」而不是「是什么」**
  ```lua
  -- 好：LeverOrginPart is only a 0.1^3 marker sitting at the handle's
  --     centre, so rotating about it just spins the handle in place.
  -- 坏：-- rotate the lever
  ```
- **变量命名**：小驼峰（`coolantRemoval`、`tickScale`、`perSensor`），
  常量全大写（`STATES`、`MIN_ANGLE`、`MAX_ANGLE`）
- **配置与逻辑分离**：所有魔法数字进 `Config`，代码里不写字面量
- **文档注释用英文**（与 `DECISIONS`/`PROGRESS` 一致），对话用中文
- 代码块内用 `--` 分隔小节，例如 `-- ========== TEMPERATURE ==========`
- 喜欢 `pcall` 包裹可能失败的实例操作（尤其是 CFrame 赋值）

### 4.3 常用 Roblox 设计模式（他认可的）
1. **单一真相源**：`GameState` 持有全部运行时状态，系统**不得缓存副本**，
   每次 `Update` 都通过 `R()` 取最新引用
2. **单一写入者**：一个值只能有一个系统写（例：`PowerOutput` 只由
   `PowerSystem` 写；冷却移除只由 `ReactorState` 算）。
   **曾经因为双重写入出过 bug，这是他特别在意的点**
3. **固定时间步 + 事件驱动**：`SystemManager` 按 priority 分发
4. **自愈**：`GameState.Reset()` 会清空子表，所以 CBL/Gravatron/METU/PEA
   在 `Update()` 里检测到自己的子表被清空会**重新 `Initialize()`**
5. **配置驱动**：`Config.Sim.TRGWebTick` 之类的常量集中管理，
   TRGWeb 的原值用 `dt / TRGWebTick` 换算
6. **文档即代码**：`PROGRESS` / `DECISIONS` / `README` / `Codex`
   都是 `ModuleScript`，内容用长字符串返回：
   ```lua
   return [=[
   # 标题
   ...
   ]=]
   ```

### 4.4 验证要求（他明确要求过）
- **必须真实验证**，不能只说「应该可以了」
- 验证方式：**模拟点击 → 检查部件位置 / 颜色变化**
- 例：拉杆测试要对比所有部件的 CFrame，确认**只有 `LeverUnion` 动了**
- 例：灯测试要读 `Color` 前后值
- 每次进度后**自评功能质量，太差就重写**

---

## 6. 场景里不能碰的东西（功能性绑定）

改动几何体时，以下**名字**是脚本绑定依赖，改名或删除会导致功能失效：

| 名字 | 用途 | 数量 |
|---|---|---|
| `ClickPart` | ClickDetector 宿主 | 941（旧记 1,023） |
| `LeverUnion` | 拉杆唯一的移动件 | 32 |
| `LeverOrginPart` | 0.1³ 标记，**无用**，可忽略 | — |
| `NeonPart` | 灯 | 1,145 |
| `*ControlRoomMonitor` | 监视器屏幕 | 7 |
| `Text` | 控制台上的文字部件 | — |
| `Core` / `EFEParticlePart` / `Effects` | 特效宿主 | — |

**安全做法：只改外观属性（Material / MaterialVariant / Color / Size / CFrame），
不改名字、不删部件。**

---

## 7. 有用的参考资源

| 资源 | 位置 | 说明 |
|---|---|---|
| TRGWeb | `ServerScriptService.Misc.TRGWeb` | **权威原型**，所有数值的来源 |
| Summary01 | `ServerScriptService.Misc.Summary01` | 参考 |
| DataCollection (+ `.Log`) | `ServerScriptService.Misc` | 参考 |
| The Reactor Game Wiki | 外部 | 用户多次引用，校准依据 |

**Wiki 关键结论：**
- **不存在控制棒**（反复确认过）
- 冷却传感器设备「有不可靠的倾向」，需要「手动干预校准」
- 操作员用手补充 ECC（METU 的 ECC 容器就是物理交互点）

---

## 8. 一句话总结

仿真核心、控制系统、监视器、测试、灯光、材质**都已就绪并验证通过**。
**剩下的是几何体重做**（倒角 / 凹槽 / 内嵌按钮 / 文字标签 / 英雄资产），
以及查清 `TempLabel` 的第二个写入者。

**动手前记住：** 先 `list_roblox_studios`，改完提醒用户 Ctrl+S，
验证读实例状态而不是模块状态。
