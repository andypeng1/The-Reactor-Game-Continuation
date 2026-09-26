# CLAUDE — 项目交接文档

> 交接目标：Roblox 游戏《反应堆游戏》的开发工作。
> 上一任 AI 助手（deepseek-v4-flash + Roblox Studio MCP）已完成仿真核心、控制系统、
> 监视器与视觉基础层。本文档记录全部上下文，供无缝接手。
>
> 生成时间：2026-09-21

---

## 0.0 文档同步规则（2026-09-26 起：**不再往 Studio 里放文档**）

> **【这条规矩变了，先看这里】** 用户 2026-09-26 明确指示：
> 「以后不再需要把 decision 那些东西放到 studio 里面了」、
> 「SS 里面的东西我们的工作文件夹有了，就不用在 studio 里面放着了」。
>
> **现在的规矩只有一条：改完同一步把磁盘 `.md` 补齐。** 没有镜像、没有「以游戏内为准」，
> 盘上写什么就是什么。下面的内容保留下来当**历史**（它解释了为什么这些文件长成
> 现在这样、为什么有些地方被拆成两半），**不要再照着它去推 Studio**：
> - `_tools/verify_docs.py` + `selftest_verify_docs.py` **已归档**到 `_tools/_attic/mirror/`
>   （2026-09-26）。不用修、也不用再跑：它钉的是 Studio 里那个 `CLAUDE` 模块的哈希，
>   而 Studio 那边已经没有可比对的东西了 —— **作废的是整个校验器，不只是它的钉子**。
>   它在归档前就已经**永远红**（本节横幅比它写死的 `SEC00_LEN = 6071` 多了 980 字节，
>   它那句 `rc 0 → 1 → 0` 自证再也成立不了）。永远红的检查就是噪音，同 §0.13；
> - 游戏内 `GameCore` 里那几份旧文档是**历史副本**，删或留都不影响记录；
> - §0.10 那条「文本进 Studio 会被解码一次」的坑**依然有效**，
>   因为脚本本体（`TRG_original_recorder.luau`）还是要注入游戏，只是文档不用了。

> 下面这一节只存在于磁盘上的 `.md`，**不属于**游戏里的 `CLAUDE` / `PROGRESS` /
> `DECISIONS` / `README` ModuleScript。写回游戏时请删掉本节。

**磁盘 `.md` ↔ 游戏内 ModuleScript 的对应：**

| 磁盘文件 | 游戏内来源 |
|---|---|
| `CLAUDE.md` + `docs/SYSTEMS.md` + `docs/TODO.md` + `docs/SNIPPETS.md` | `game.ServerScriptService.GameCore.CLAUDE` |
| `PROGRESS.md` | `game.ServerScriptService.GameCore.PROGRESS` |
| `DECISIONS.md` | `game.ServerScriptService.GameCore.DECISIONS`（条目 1..74） |
| `DECISIONS_2.md` | `game.ServerScriptService.GameCore.DECISIONS_2`（条目 75..） |
| `README.md` | `game.ServerScriptService.GameCore.README` |

**为什么 `DECISIONS` 也拆成了两份（2026-09-23）：** 跟 `CLAUDE.md` 那次**不是同一类问题**。
`ModuleScript.Source` 有**引擎硬上限 200000 字节**，写入 202893 的那次是**直接被拒绝**的
（`Provided string length (202910) ... max length (200000)`），没有预算可调，只能拆。
边界定在**条目 75** —— 是条目号，不是字节偏移，所以它是文档的性质而不是当天长度的性质。
**这两个磁盘文件不是 `docs/` 卫星文件，没有磁盘专属前言**，各自**逐字节等于**自己模块的镜像；
拼回来的规则是 `DECISIONS.md` 去掉尾部换行 + 一个空行 + `DECISIONS_2.md`，校验脚本会断言这条缝。
**`DECISIONS.md` 里含 2 个反斜杠**（早期条目里 Lua 代码片段中的「反斜杠 + n」），
因此这一份**只能在 Studio 内部从已有文本搬移出来，不能通过工具调用传文本**（见 §0.10）。
详见 `DECISIONS` 123。

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
6. **文档即代码**：`PROGRESS` / `DECISIONS` / `README` / `CLAUDE`
   都是 `ModuleScript`，内容用长字符串返回：
   ```lua
   return [=[
   # 标题
   ...
   ]=]
   ```
   **（2026-09-26 已废止，见 §0.0）** 用户说「以后不再需要把 decision 那些东西
   放到 studio 里面了」，所以文档现在只住在磁盘上；游戏里那份是历史副本。
   下面这条格式约定仍然适用于**任何**要写成 Lua 长字符串的东西（比如采集器里的报错文本）。

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
**几何体重做已撤销**（用户 2026-09-26 原话：「不需要重做建模，请删除」）——
`docs/TODO.md` §3.1 里那两条未开始的几何条目（设施外壳/房间内部的装饰与英雄资产、
堆芯外壳与拉杆握把的 `generate_mesh` 重做）已删掉，该节剩下的只是已完成的施工记录。

**当前唯一在跑的活是「原版游戏数据采集器」** —— 不是这个工程里的代码，而是一份
注入到**原版游戏**（placeId `17596243941`）里、由 Solara V3 用 `loadstring` 执行的
单文件脚本 `_tools/TRG_original_recorder.luau`。它**不依赖** `ReactorBackend` /
`Config` / `Engine`，只读实例状态；写文件时**只记有变化的键**。
用法看 `docs/RECORDER_HOWTO.md`；测试跑 `bash _tools/run_tests.sh`。

**悬着的（2026-09-26 更正）：** ~~查清 `TempLabel` 的第二个写入者~~ —— 这条**早就不成立了**，
`PROGRESS.md` Phase 24 的标题就是 `The TempLabel second writer  [DONE]`。
~~O4 / O5~~ 当天也答了：**根 `PROGRESS.md` 算数**（`docs/airemake/` 留在磁盘上当参考，
不再追加），**`ShutdownEndsShift = false` 留着**当「另一种配置」的文档（`docs/RECORDER_HOWTO.md`
本来就写着它的两个独有信号）。**`QUESTIONS.md` 的「等你拍板」那节是空的** ——
但「等你回答」那节现在有**一条 P1**（要不要再注入一次去抓冷启动那半场，见下）。

**2026-09-26 做了四件活，编号按做事的先后（mtime）而不是补号的顺序：Phase 45 拉杆反馈
（12:51）、Phase 46 灯矩阵（13:59）、Phase 47 整理 Workspace 与工作文件夹（约 21:00）、
Phase 48 采集器读文件 + 两处措辞修正（约 23:15）。**
45/46 本来两边都没落，已按 **O4:A** 回填进 `PROGRESS.md`，对应取舍补进 `DECISIONS_2.md`
**131..134**；整理那节因此从我先前写的 45 **改号为 47**。Phase 48 的取舍是 **135..137**。

**Phase 48 —— 采集器第一份完整「冷启动 → Equinox → 熔毁」的文件，和它暴露的两处假话。**
`Data/flow/original_260926-230049`（1357508 字节，完整 `## RECEIPT`，
`postfails=0 spilled=0 dropped=0`）**抓全了 Equinox 整条链**：12:00 PM 触发
（`INGAME_MANUAL` 114/148 原文「12PM marks the beginning of the Equinox Event」）→
两个 CBL 掉到 10% → 压力 2542→1070 → `MAINFRAME CONNECTION LOST` →
`s.MainframeMeltdown=true tempF=7978` 封存。顺手确认 **B2 已修**。
改了两处**只改措辞、不删读数**：① `CLOCK` 事件在中途注入时会把「表盘绕回正午」说成
「班次开始」—— 两句只隔 60 秒而 `m.temp` 那一刻 12865→12979 F，**两句都是假的**；
现在按注入那一拍的状态（`clockStartedUp`）分开记。② 封存那句
`the operator shut it down: s.MainframeMeltdown=true` 把机器的锅记在人头上；
现在措辞跟旗标走。裁决名 `user-shut` **没动**。
新增 `_tools/build_clock_test.py` + `_tools/selftest_clock_test.py`
（3 个变异改坏，各自在**指定断言**上红，`clock: 10 PASS, 0 FAIL`）；
采集器 126009 → **128612 字节**，无事件种类改名、无收据字段移动。

**Phase 48 更正（2026-09-26 23:40）：** 上面那节原来写的是「**中途注入**」「**缺**冷启动
半场」「`flow=false` 因为注入时核心已开着」—— **全错**，用户当场纠正过
（`我就是先注入才开的核心啊`）。文件站在用户那边：`B 1 t=1.34` 三个 `s.Core.*` 全 0、
风扇/冷却/CBL 全 0，`EVT2072–2078 CLICK StartUpLever` ×7 就是开机，
`s.Core.TemperatureVal` 0→9420 爬了 96.6 s。**我错在把 `m.temp` 当成了堆芯温度** ——
它是监视器标签，而监视器到 t≈99 都在读 `ERR F`：**监视器最瞎的时候正是堆芯最冷的时候**。
`flow` 只能答「有没有见它掉下来」；**冷启动的一趟在结构上永远给不出 `flow=true`**。
`EVT2017` 那句 `the core is up` 的**依据**（`q.up = q.clock > 0`）也是错的 ——
表盘自由走，冷堆时 710→715 照走。另外「Equinox 把 CBL 打到 10%」这份文件**不支持**
（同样的 25→10 在 t=188.71 / t=548.75 也出现过，没有 Equinox）。

**Phase 49 —— 温度是怎么算的（用户问「温度计算什么的能搞出来的吗？」）。**
**结构定死了，增益只到量级，公式拿不到。**
① **`m.fluct` 就是那一 tick 的温度增量**：393 次 `m.temp` 变化里 391 次满足
`temp(下一拍) − temp(这一拍) == m.fluct`，逐字节相等 —— `m.temp` 是它的累加。
tick ≈ **1.8 s**。**温度是积分器不是惯性环节**（t=560.78–610.97，cool=0/fan=3，
增量在时间和温度上都是平的：6625→13224 F）。
② 拟合（391 tick，目标 `m.fluct`）：`ΣcblPct` **+5.05/%**、冷却泵 **−58**、
风扇 **−33**、**温度项 ≈ 0**（−0.0068 ± 0.0044，与 0 无法区分），R² 0.33，
残差 sd 146 F/tick —— **解释了漂移，没解释波动**。
③ **拿不到的原因**：操作员每一次动控制都是对温度的回应，所以回归量共线
（`coolSum·T` 的系数符号是反的）；增益**不可外推**（冷启动 CBL 300%，实测 +180 F/tick
而模型给 +1104，差 6 倍，饱和）；回正项在固定设置内部互相矛盾
（`(75,2,4)` 跨 4600 F 是**平的** corr +0.01，`(75,1,3)` 是 −40.4/1000F corr −0.52），
**τ 定不下来**；噪声 lag-1 自相关 **0.655**，不是白噪声。
④ **冷启动半场一直在文件里**，而且和监视器接得上：`s.Core.TemperatureVal` 0→9420 F /
96.6 s ≈ **98 F/s**，最后一拍 t=97.90 的 9420 对上 `m.temp` 第一拍 t=98.77 的 9330
（103 F/s，同速）。

**Phase 50 —— 压力：一个风扇 = −60 PSI/tick（用户给的数，文件验过）。**
用户主动给了常数 `一个风扇每tick降低60PSI`，当场拿文件验：**12 次风扇拨动 12 次方向全对**，
中位 |Δ| = 58 PSI/tick；最干净的一段（cblPct=75、coolSum=0 按住不动，只拨 fan 1↔2 四趟）
斜率**精确在 +58 和 −2 之间跳，差正好 60** —— **用户是对的**，fan=0 基线 +118 PSI/tick。
**边界一并记下：线性只验到 3 个风扇**（fan=4 那个窗口是衰减瞬态，不是稳态斜率，
`−30→−14` 朝 0 收敛）；**而且这条不能推广到冷却泵**（五次 coolSum 拨动的 Δ 是
+0/+11/+4/−102/−4，没有常数）。
**顺带：这条数从文件外面锁死了 tick** —— 用户说的「每 tick」和压力变化的间隔
**1.79 s** 一致，和温度的 1.79 s 也一致，这是第一次有外部见证确认 tick ≈ 1.8 s。

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
逐字副本，现在公开了 —— 见 `QUESTIONS.md` **P5**。
**推送通道（同一天补的）：** `git push` 在这台机器上连不上 —— **`github.com:443` 21 s 超时**，
但**同分钟 `api.github.com` 200 / 0.43 s**；两个域名是分开的。于是用
`_tools/_attic/scratch/api_push.py` 走 Git Data API 把**同一棵树**写上去，动 ref 之前
**断言服务器算出的 tree sha == 本地 `HEAD^{tree}`**（tree sha 是内容哈希，对上就是逐字节相同），
写完再把 176 个 blob 读回来逐一比对，0 处不同。远端那笔是 **`1109d362`**、不是本地的
`f1aadb6`（内容相同，作者被换成 GitHub 身份），所以**下一次 `git push` 会是 non-fast-forward** ——
网络通时 `git fetch origin && git reset --hard origin/main` 一行解决，**不丢内容**。

**Phase 47 —— 整理 Workspace 与工作文件夹。**
779 个已证惰性的散件进了 `Workspace.Geometry`（该夹 23 → **802**），19 个散落 `Sound` 进了
`Workspace.Sounds`，根目录直接子物体 1802 → **999**，Part 总数 **91905 不变**，
回滚记录是 `ServerStorage.OrganizeRollback20260926` 里**一个 197602 字节的 `StringValue`**。
数字在 `baseline/organize_20260926.md`。
**代价我记在这里：多删了 6 个东西** —— `CreepySounds` 的 6 个子物体跟着脚本一起没了、找不回来，
理由和错在哪见 Phase 47 的 DISCLOSURE 段。

**动手前记住：** 先 `list_roblox_studios`（§0.1），验证读实例状态而不是模块状态（§0.2）。
自动保存已开（§0.9），**不要**提醒用户 Ctrl+S —— 旧版 §8 那句「改完提醒用户 Ctrl+S」已作废。

**文档只写磁盘（2026-09-26 起）：** 见 §0.0 —— 不再镜像回 Studio，
盘上的 `.md` 就是**唯一副本**，`_tools/verify_docs.py` 已归档到 `_tools/_attic/mirror/`。
「改完同一步把文档补齐」这条**继续有效**。
