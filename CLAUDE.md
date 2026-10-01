# CLAUDE — 项目交接文档

> 交接目标：Roblox 游戏《反应堆游戏》的开发工作。
> 上一任 AI 助手（deepseek-v4-flash + Roblox Studio MCP）已完成仿真核心、控制系统、
> 监视器与视觉基础层。本文档记录全部上下文，供无缝接手。
>
> 生成时间：2026-09-21

---

## 0.0 文档同步规则（2026-09-26 起：**不再往 Studio 里放文档**）

> **【先看这条】** 用户 2026-09-26：「以后不再需要把 decision 那些东西放到 studio 里面了」、
> 「SS 里面的东西我们的工作文件夹有了，就不用在 studio 里面放着了」。
>
> **现在的规矩只有一条：改完同一步把磁盘 `.md` 补齐。** 没有镜像、没有「以游戏内为准」，
> **盘上写什么就是什么。** 游戏内 `GameCore` 里那几份旧文档是**历史副本**，删或留都不影响记录。
> §0.10 那条「文本进 Studio 会被解码一次」的坑**依然有效** ——
> 因为脚本本体（`TRG_original_recorder.luau`）还是要注入游戏，只是文档不用了。

**2026-09-27 又收了一次：** 本节原来带着整套镜像时代的细节（磁盘↔Studio 对照表、
`verify_docs.py` 怎么拼哈希、`split_claude.py` 的无损证明、`DECISIONS` 为什么拆成两份）。
那些**规则全部作废**（校验器已归档到 `_tools/_attic/mirror/`，且在归档前就永远红 ——
它钉的 `SEC00_LEN` 早对不上了，**永远红的检查就是噪音**，同 §0.13），
所以从每轮都要进上下文的这一份里搬走，全文仍在 `PROGRESS.md` / `DECISIONS` 96 / 123。
**只留两条还会复发的教训**（它们的现代版本是 `DECISIONS_2` **183**）：
**绝不能用磁盘算出来的哈希去校验磁盘**（同义反复，两边同时错也 PASS，`DECISIONS` 95）；
**比哈希、不比字节数**（字节数相同而内容不同是**真实发生过**的，只比长度必漏）。

**磁盘 `.md` 的分工（这条是活的）：**

| 章节 | 在哪 | 什么时候读 |
|---|---|---|
| §0.0 本节 / §0 血泪教训 / §1 项目概述 / §4 用户偏好 / §6 不能碰 / §7 参考 / §8 总结 | **`CLAUDE.md`**（自动加载） | 每轮 |
| §2 已完成的系统 | `docs/SYSTEMS.md` | 动代码 / 场景之前 |
| §3 待办 / 下一步 | `docs/TODO.md` | 决定做什么之前 |
| §5 关键代码片段 | `docs/SNIPPETS.md` | 抄 / 改任何一段实现之前 |
| 采集器/监视器怎么跑 | `docs/RECORDER_HOWTO.md` | 注入前后 |
| 阶段记录 / 取舍 | `PROGRESS.md` / `DECISIONS.md`(1..74) + `DECISIONS_2.md`(75..) | 动手前后按需 |

**章节号一律没动** —— `PROGRESS` / `DECISIONS` 里那几百处 `§2.6`、`§5.9`、`§0.13`
之类的引用继续有效，只是那个「章节」现在落在目录下的另一份文件里。

**硬性规则：任何一次改动之后，同一步就要把文档补齐，不要攒着。**
改了代码 / 场景 / 配置 → 同一步写盘：新阶段进 `PROGRESS.md`，新取舍进 `DECISIONS_2.md`，
结构变化进 `README.md`，改的是 §2 / §3 / §5 就进 `docs/` 下对应那份。
**`CLAUDE.md` 每轮都进上下文，所以它只留「需要每轮看到」的东西**：
新的 Phase 段写**能直接用的那几句**，细节写进 `PROGRESS.md`，别在两边各写一份全文。

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

### 0.14 【坑】`workspace.Camera` 是点号查找，这个 place 里有**两个** Model 叫这个名字

`workspace.Camera` **不是** `CurrentCamera` 的别名 —— 它是普通的子物体查找，返回**叫这个名字的
子物体**。这个 place 里有**两个 `Model` 叫 `Camera`**（`(310.4, 136.7, 8.5)` 和
`(310.4, 136.7, −9.8)`，各 14 个部件，是场景里的**道具摄像机**），真正的相机是第三个同名子物体
（一个 `Camera` 实例）。

后果：官方 `rblx_screen_capture` **在给相机定位之前就死了** ——
`CameraType is not a valid member of Model "Workspace.Camera"`。

**改一个不够。** 我改了 `FindFirstChild` 拿到的那个，第二个立刻顶上，`workspace.Camera` 还是 Model
（`GetFullName()` 才会告诉你搬走的是哪一个）。要**先枚举、把所有同名的都挪开**，再断言
`workspace.Camera.CameraType` 读得到，才算改对。**改完记得改回原名** —— 全 DataModel 126 个脚本
只有 1 处注释提到 `.Camera`，没有任何东西绑定它，**搬动是安全的**，但它是**世界的一部分**，不是我的。

**顺带（同一天量到的，两个都是负结果）：** 这台机器上**两个**截图工具
（第三方 `capture_screenshot`、官方 `rblx_screen_capture`）都**不认我给的相机** —— 两次不同的
相机位给出**逐字节相同**的画面（暗底 + 角落一个小图标），而那个画面显然不是世界。
所以「开灯前后拍两张图对比」这条路**现在走不通**，验证只能靠**读实例属性**
（§4.4 本来要求的也正是这个）。`capture_device_matrix` 同样是坏的
（`device simulator get failed … missing argument #1`）。

### 0.15 【坑】过期的 `require` 递给你的是**少键的表**，报错落在**消费者**身上

§0.3 说「编辑 Source 后 require 缓存不失效」。这一轮它换了一张比 §0.3 更难认的脸：
插件 VM 里 `require(Config)` 拿到的 `Shell` 表键是
`[MonitorPowerOff, RoomLightOff, RoomLightOn]`，**没有 `EmitterTransparency`**，
于是崩在 **`RoomShell` 的第 126 行** —— 而 `#Config.Source` 是 **8975**，和磁盘**逐字节相同**，
源码那边一个字都没错。

**报错的位置和出错的位置隔着一个模块。** 所以：看到「消费者里某个 config 字段是 nil」，
**先怀疑缓存里的模块是旧版**，不要先去改消费者 —— 改消费者等于给一个**不存在的旧版本**打补丁。

现成解法（比 §0.3 的 `loadstring` 稳，插件 VM 里 `loadstring` 未必可用）：
**`Clone()` 一份到临时 Folder 再 `require`** —— 新实例 = 新缓存项 = 重新编译；用完 `Destroy()`。

### 0.16 【坑】「游戏真的跑起来之后」那一半，现在读不到

- `solo_playtest start` / `start_playtest` **能起来**（`solo_playtest state` 回 `isRunning: true`），
  但这个插件**不注册 server / client peer** —— `get_connected_instances` 永远只有 `edit`。
  于是 `eval_server_runtime` 和 `execute_luau target='server'` 一律 `No "server" peer answered`。
- 日志也不行：`get_playtest_output` 只回资产报错（§0.8 那一类），
  `get_output_log` 回的是 **edit** 那份（时间戳还是早先 probe 的）—— **playtest 里的 `print` 读不到**。
- **停得掉 playtest 的是官方 `rblx_start_stop_play(is_start=false)`**，不是 `solo_playtest stop`
  （它只「发信号」，之后 `start_playtest` 仍报 `A test is already running`）。

**结论（2026-09-27 部分推翻，见 §0.17）：用这套**读**的工具，「跑起来的游戏里发生了什么」依然读不到**
—— 上面三条**全部仍然成立**。但**有了一条出路**：让**脚本自己**把运行时的东西写出来
（`_tools/room_watch.luau` 那套）。能验的仍然是**实例状态**和**源码** ——
而 §4.4 要求的**本来**就是前者（模拟点击 → 检查部件位置/颜色）。别把「读不到运行日志」当成
「功能没做」，也别反过来把「源码看起来对」当成「验证过了」。**哪一半验了、哪一半没验，分开写。**

### 0.17 【通道】两个工具链的 VM 不一样：`GetAsync` 在插件 VM 里是**桩**

**同一个 `HttpService`，两个 VM 行为不同**，而这一点没有任何报错会告诉你：

| 工具 | `HttpService:GetAsync` | 后果 |
|---|---|---|
| 第三方 `mcp__robloxstudio__execute_luau` | **打成了桩**：`pcall` 回 `ok=true, type=nil`，而 `serve.py` 那边**真的**记了 `SENT <name> <bytes>` | `m.Source = src` 死在 `ProtectedString expected, got nil`，**报错指向赋值、不指向网络** |
| 官方 `rblx_execute_luau` + `datamodel_type:"Edit"` | **走真 HTTP**（`ok=true type=string len=31691`） | 正常 |

**规矩：所有 Studio → Studio 的源码搬运，走官方 `rblx_execute_luau`。**
（`HttpService:PostAsync` 在两边**都**能用，所以 Studio → 磁盘的读回不受影响。）

**顺带**：`rblx_start_stop_play(is_start=true)` 之后，官方工具的 `Edit` 数据模型就没了
（`Edit datamodel is not available in Play mode`），所以**推源码的顺序是：停 → 推 → 起**。

**反过来说，运行时的东西现在有一条真出路（§0.16 的正面解法）：**
不要去「读」运行中的游戏，让**跑在游戏里的脚本自己**把要看的写成文件、推到本机 HTTP sink
（`_tools/receive.py`），字节不进上下文。这条路上还多一条纪律 ——
**这个脚本必须自己报告自己的死因**：它跑在 `task.spawn` 出来的线程里，没人 await、没人 catch，
**「在跑但没事发生」和「第一拍就崩了」从外面长得一模一样**。
`room_watch.luau` 的 `scan()` 因此套着 `pcall`，出错就写一份 `error.txt` 到 sink。

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
| `LeverUnion` | 拉杆唯一的移动件 | 41（旧记 32） |
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

**Phase 53（2026-09-27）—— 卷帘门收在 `ControlRoom{L/M/R}Shutter`（向下 10.58 世界空间），
外加一台只读的房间监视器**（`_tools/room_watch.luau`，43 根 / 30,142 实例 / 235,038 属性，
产物 `rooms.txt` / `inventory.txt` / `summary.txt` / `changes.log` / `suppressed.txt`）。
全部细节、run 1..15 的数字、音频 hook 的探针判决（`Pitch=0.00` 那 15 个、0.73 s 的片段）
**已整段搬到 `PROGRESS.md` Phase 53 尾部**，标题是「Phase 53 的 §8 摘要原文」——
逐字未改，只是换了个住处，因为这一节是跑动细节而 `CLAUDE.md` 每轮都要进上下文。
本文件只留一句：**它只读、不写世界，抑制是「扣在手里不写」而不是「先写后擦」**。
**它的两个实例已于 2026-09-27 从数据模型删除**（D11 答 B，理由见下 Phase 54）——
`_tools/` 里那两份源码没丢，重新注入就回来。

**当前唯一在跑的活是「原版游戏的两份注入脚本」** —— 不是这个工程里的代码，而是
注入到**原版游戏**（placeId `17596243941`）里、由 Solara V3 用 `loadstring` 执行的
单文件脚本：采集器 `_tools/TRG_original_recorder.luau` 和监视器
`_tools/TRG_original_watch.luau`（后者见 Phase 54）。它们**不依赖** `ReactorBackend` /
`Config` / `Engine`，只读实例状态；写文件时**只记有变化的键**。
**两份都不按任何东西** —— 采集器 `r60` 起连「只观察不按」的那台驱动器也没有了（Phase 62）。
用法看 `docs/RECORDER_HOWTO.md`；测试跑 `bash _tools/run_tests.sh`。

**Phase 54（2026-09-27）—— 第二份注入原版的脚本：`_tools/TRG_original_watch.luau`。**
起因是用户的一次更正：「**我说的整个控制室+核心腔室+音频监听是监听原游戏的，又不是现在的**」
—— Phase 53 那台做在了 **AIRemake** 上，方向错了；目的也说明了：`你根本不会做开机`，
所以产物要能回答**「开机到底做了什么」**，三个监控对象全部重新对准**原版**。
**和 `room_watch.luau` 最大的结构差别：根不是写死的。** 原版的树我一次都没看过，
写死根名 = 把猜测当事实，而猜错**是静默的**（根不存在 = 零行 = 和「没事发生」同形），
所以它**先普查、再选根**（按实例数**从小到大**取到预算 80000 为止），
并把**选择过程本身**写进 `rooms.txt`（谁进了、谁没进、**为什么**）。
产物九份含 `audio.txt` / `error.txt`，热键 `RightAlt` 催 / `RightControl` 停，**只读**。
**本机验过**：`watch_harness.luau` **45 PASS / 0 FAIL**、`--boom` **4 PASS / 0 FAIL**、
`selftest_watch.py` **15 个变异 15 个按预期变红**；`bash _tools/run_tests.sh` 全绿。
**它当时一次都没在原版里跑过**（2026-09-27 追加：用户说他那一轮 `watch` 和 `record` 都开了，
**但盘上只有采集器的字节** —— `Data/originalwatch/` 不存在，而 `hello.txt` 是设计上
第一个该出现的路径。所以「跑过」这件事**当时仍然没有字节支持**，
两种解释在盘上同形，见 `PROGRESS.md` 57.10 / `QUESTIONS.md` **P8**。
**2026-09-30 已被它自己的产物推翻**：Phase 61 那趟它有 11 份产物、没有 `error.txt` ——
跑起来了，而且是**跑起来才看得见**的两个缺陷（hook 晚装 28 秒、`MaxQueue` 太小），修在 `w60`。）
—— 预算够不够、选出的根对不对，**都是设计意图不是观测**，
跑完**第一件事读 `rooms.txt`**。验的过程翻出四个错，其中三个只有变异测试看得见
（`judged` 只写不读而文档在替它说话；删掉整个静默放行规则产物逐字节不变；
`--dump` 判了两次所以静默不写文件）—— 细节 `PROGRESS.md` 54，取舍 `DECISIONS_2.md` **160..163**。
**跑法**（全文见 `docs/RECORDER_HOWTO.md`）：起 8766，在原版里 `loadstring(game:HttpGet(...))`
那份监视器；sink（8765）**已在跑**。**要抓开机就趁开机前注入** —— 开局就响着的声音
**永远不会**发 `Played`（DECISIONS 157），晚注入等于把开盘那段让掉。
**它和采集器可以同时注入**（全局变量、输出路径、热键三处都对过，见 54.6）——
**但热键曾经撞过：两边都绑 `RightShift`，而采集器那边它是「封存并结束这一趟」。**
监视器已让路到 **`RightAlt` = 立刻推文件**、`RightControl` = 停；
**`RightShift` 现在只属于采集器**，别在跑的时候按它。harness 有一条检查
（`the watcher does not steal the recorder's seal key`）守着不再撞回去 —— 45 PASS。
**D11 已执行（2026-09-27）：** AIRemake 那边 Phase 53 的 `SSS.MCP_RoomWatch` +
`MCP_RoomWatchRunner` **已删**（你原话「不用吧，采集的是原游戏里面的」）；两个 MCP 探针留着。
删前把磁盘那两份读回同一个 VM **逐字符**比过、并 grep 全 DataModel 确认无第三方绑定。
细节 `PROGRESS.md` 54.7，取舍 `DECISIONS_2` **165**。

**Phase 55/56/57/58 —— 已搬到 `PROGRESS.md` 的历史，这里只留能直接用的那几句。**
- **55**：GUI 采集（`g.<key>`）**只在客户端**存在；`GuiObject` 答 `Visible`、`LayerCollector`
  答 `Enabled`，**问错的那个是 error 不是 nil**；实测轮询 **1.66 Hz**（标称 4 Hz，被**饿着**）；
  **187 个重复键** → `QUESTIONS.md` **P6**。
- **56**：监视器 `Pinned = {'Alarms'}` —— pin **同时豁免两个预算上限**、**不取代普查**；
  **8765 的 `--dir` 必须是 `Data`**。
- **57**：监视器的**记录窗口**（拉杆开、12:00 关）只挡「记录」不挡「观察」；低温失速那一趟
  底下是**三处**（边界把「停堆又起来」塞进 UP → 新增 `RECOVER`；兜底挂在**边**上于是穿过
  恢复继续数；`everRan` 门）；热端熔毁改读**温度**不借 `s.MainframeMeltdown`。
- **58**：冷跳闸那臂**一次没到过**（`m.temp` 窗口内最低 **4316 F**），结束它的是
  `SealDownSamples=40` 兜底 → **P7 是正确但无关的更正**；监视器零字节的嫌疑锁在**传输层**，
  `transport_probe.luau` 是「不花班次的第一步」（**request 族要请求表**）。
细节 `PROGRESS.md` 55..58，取舍 `DECISIONS_2.md` **166..186**。

**Phase 61（2026-09-30）—— 三个注入脚本第一次真的在原版里跑起来了（窗口没开）。**
**这一趟第一次有字节支持「脚本真的跑过」**（以前「跑过」和「没注入」在盘上同形）：
探针答出 `winner=http_request`（`request`/`http`/`getgenv` 也能用，`syn`/`fluxus`/`krnl` 不在），
监视器 11 份产物**没有 `error.txt`**（71236 件 / 557548 属性普查完），采集器抓全整条开机链
（`RoomLight → MonitorPower → Shutters → MonitorBoot → **StartUpLever** → HDEF-PowerLever`，
然后 `CORE IGNITION IMMINENT`）。**但 `window.txt` 同时写着 `lever_hooked=true` 和
`opened_at=not yet`** —— 两个缺陷，都已修：① **开窗口的 hook 装晚了 28 秒**（普查实测占
**48 秒**，而拉杆 **t≈20 秒**按的；`attachWindow()` 在 `pcall(bootWalk)` **之后**，
原注释「the census finishes in seconds」**被自己的产物否掉**）→ 挪进 `Start()` 同步装；
② **`MaxQueue` 4000 < 开机峰值** → `dropped=794`（`flush()` 在窗口关着时什么都不投，
而截断每拍照跑 → **窗口关着 = 队列只进不出 = 上限吃队头**）→ 4000 → **20000**。

**Phase 62（2026-09-30）—— 采集器：driver 整个删掉，反应堆读数加一道核心闸。**
你三条原话（全文 `PROGRESS.md` 62）：探针 **不变**；采集器「**注入后立刻开始**（核心完全开启前
不采温度压力），**不需要 driver，只需要 seal**（1 手动关机、2 自动关机如熔毁/温度过低）」；
监视器「按下开机按钮时开始监听控制室+腔室+警报+音频（**所有监视器的 GUI 也要**），**12PM 结束**」。
- **① DRIVER 整段删除**（`DECISIONS_2` 202）。**删得下去的前提**是那条 hook 从来**不在**
  DRIVER 段里：点击钩子遍历全世界 1019 个 `ClickDetector`，你按的每一个照旧全进文件。
  三个文件归档在 `_tools/_attic/driver/`（是**测量**，不是活代码）。
- **② 核心闸（`COREGATE`）**：判据是**游戏自己的 `s.GameActive`**，不是温度（温度的错在
  「开了但还没热」和「关了但还很热」，而这两个区间**正好就是开机和关机**）。它**锁存**
  （关机后低温那臂还要读 `m.temp`，每拍重判会把温度掐在关机那一拍）；它**扣住不写、
  不是过滤**（闸关着时那个键**根本不进 `last`**，否则闸开那一拍的值正好等于开机前的值时
  会被判成「没变化」而永远不出现）。**故意不管** `t.*` 走查和设施面板：**开机流程本身在那里面**。
- **③ 窗口的终点改成中午** —— `EndMins = 720`（半夜）**作废**（`DECISIONS_2` 201）。
  **`EndMins` 这个名字替我回答了问题**：配置项的名字替你回答了问题，那你读到的就不是测量。
  现在等的是 **11:59 AM → 12:00 PM 的交接**（表盘 1439 → 0，正午是**下降**不是阈值）
  → `WrapDropMins = 60` + `EndPolls = 2`。
- **④ 闸的测试台**：6 个变异各自红在指定检查上、**2 个 FOLLOW 必须留绿**（「闸默认开着」是
  **结构性盲点** —— 写下来 + 一行断言，**变成已知的盲点而不是一个洞**，**205**）。它翻出一个
  **真代码缺陷**（`coreGateOpen` 不重取 `Stats`，文件夹晚到就永远打不开）。
- **`run_tests.sh` rc=0**（**133 条 ok**）。
- **三个 md5（注入前核这个，别核时间）：** 采集器 **121202 / 2644 / `48f2c155b7d6342f07cafcfb4404e9e8`**（`r60`）、
  监视器 **147930 / 2699 / `32bba692e0e078f416789972aecd192a`**（`w61`，Phase 64 的卡顿修复）、
  探针 **10752 / 217 / `5acde17d2bccfa65949c9a4b2bec9a90`**（未改）。
  细节 `PROGRESS.md` 62，取舍 **201..205**。**`docs/RECORDER_HOWTO.md` 已按 `r60` 全文改过**
  （它以前教人按一个已不存在的按钮 —— **散文说的谎和代码说的谎一样贵**）。
- **下一次两份都要重注**：`r60` 字节没变，监视器换成 `w61`。

**悬着的还是那两件**（`QUESTIONS.md` 无新条目）：**P4:A 冷却泵 2/3 档**（要等注入）、
**P6:A 的 187 键探针**（不叠在同一个注入里）。**信标补不上的那一格**：顶层代码在信标
**之前**抛错时和「从没注入」在盘上逐字节一样 —— 补它要放到文件第一行，那时 `CONFIG` 还没读完，
**代价大于收益，不做，且这条要一直写在这题的答案里**。

**Phase 64（2026-10-01）—— 「注入之后游戏贼卡」的修复：监视器让帧 + 份额上限（`w61`）。**
上一趟**监视器自报** `scan_ms=2197` 配 `Interval=1` ≈ **70% 的客户端**，采集器只 `cpu_pct=10.9`
—— **卡的是监视器**。两个旋钮：`MaxBlockMs = 25`、`DutyTarget = 0.30`（按实测 `scan_ms` 反推）。
**修没修好由下一趟产物说，不由注释说**。**测试台的坑（会复发）**：时间型让帧让「按 `task.wait`
计数驱动时间线」的 harness **变成抛硬币**（同一份未改动的文件 3 红 1 绿）→ 只让**带参数的 wait**
推进时间线，再加一条**差分测试**。
细节 `PROGRESS.md` 64，取舍 **210..213**。

**Phase 59/60（2026-09-30）—— 拉杆与百叶窗门都改成 tween。** 都没换写入者：`LeverTweenSeconds = 0.3`
（**必须短于 `RefreshSeconds = 1`**，否则 union 停在动的档位；动画**故意留在服务端**），
`ShutterTweenSeconds = 0.6`，开 = 关 **减**世界空间的 `(0,10.58,0)`，**缓动不进 `Config`**。
**量法**：Edit 模式下逐 tick 位移读不出平不平 —— 用时间桶。取舍 **192..196**。

**Phase 65（2026-10-01）—— 原版的开机链进了 remake：`Shift.StartupSteps` + `LogPanel`。**
16 步 hold 表取代占位符，和 = **113.4 s**（四趟端到端中位 113.44；**旧注释自称 96.5 s 是假的**，**215**）。
`LogPanel.Refresh` 是 `engine.events` 的**第一个真读者**，只写 `TemplateLogFrame1..3`
（**clone 模板不写模板**、四行、`CONTROL` 不上台）。**坑**：`Engine:Reset` **整张换掉 `state` 表**，
缓存它再 `while` 等 = 不 yield 死循环 = **Studio 卡死**（**224**）。细节 `PROGRESS.md` 65，取舍 **214..224**。

**Phase 66（2026-10-01）—— 你丢进来的 180 MB（`Data/auxcollection`）：原版监视器的逐属性写日志。**
1,162,737 行 / 跨度 **158 s** / 只有那 7 台 `Workspace.Monitors.*`；**99.4% 是 Position+Size**，
**能读的只有 0.2%**。**坑**：文件顺序**不是**时间顺序（恰好一次回跳），**头部统计必须先排序再算**。
**验到** `RoomShell.faceFor` 逐段吻合；**验不到** `StartupSteps`（运行期克隆的行，固定后代集合的
监视器看不见）—— **独立通道只在测同一对象时才算独立**。已 `.gitignore`。取舍 **226..229**。

**Phase 67（2026-10-01）—— 开机屏：你给的「直接证据」变成 remake 里会动的那 14 秒。**
你那段 hook（`_tools/_attic/scratch/aux_boot_hook.luau`）**钉死了 t=0 = `MonitorBootButton` 被按**
（逐字留着）—— 于是 **§66.5「抓取开始时就已在开机中」是错的**，
原地划掉更正。由它量出并实现的：`BootSeconds` 3 → **14**、`Config.Shell.BootScreen.Reveals` **7 条**、
新模块 **`BootPanel`**（写 `BootFrame` **里面** 51 个 label 的 `Visible`，与 `RoomShell` 写
`BootFrame.Visible` **属性不相交**）。**只建模布尔、不重建曲线** —— 捕获里那 99.7% 的位移行是
「变化才写」，**布尔活得过采样，曲线活不过**。**验证**：`aux_expect.py`（从捕获重放）对
`aux_compare.py`（读真部件）**14/14 秒全等**，两个变异各在预期段变红，跑完世界复原。
细节 `PROGRESS.md` 67，取舍 **230..232**。

**Phase 68（2026-10-01）—— 镜像追平；`run_tests.sh` 不是并发安全的。**
**① 判据看 `N of M detected`，不看 rc** —— `selftest_watch.py` 写死 `_tools/_watch_mutant.luau`
和 `_tools/_mut_out`（收尾 `rmtree`），**同时跑两遍互删产物 → 报成「NOT DETECTED」**
（两遍给出 **17/29**、**25/29** 两个不同的数 = 污染指纹；其中一遍 rc 还是 **0**）。
单独跑 **29/29，rc=0**。
**② `src/ReactorBackend/`** 漂了 4 个 Phase（3 改 / 2 无 / 5 逐字节相同 —— **半新半旧最难认**），
已按 §0.17 通道 + 两侧 **CRC-32**（不比字节数）追平复验 10/10；**它没有写入者**，会再旧。
取舍 **233/234**。

**Phase 号按做事的先后（mtime）编，不按补号的顺序。** 2026-09-26 那四件活是 45（拉杆反馈）、
46（灯矩阵）、47（整理 Workspace）、48（采集器读文件）；45/46 本来两边都没落，已按 **O4:A**
回填，取舍 **131..137**，整理那节因此从我先前写的 45 **改号为 47**。

**Phase 48/49/50/51 —— 已搬到 `PROGRESS.md` 的历史，这里只留能直接用的那几句。**
（本节原有全文逐字存在于 `PROGRESS.md` 同名 Phase 里；压缩只是让每轮进上下文的那份小下来。）
- **48**：Equinox 整条链抓全了；两处**只改措辞、不删读数**的修正。**48 更正：`m.temp` 是
  **监视器标签**不是堆芯温度**，而监视器最瞎（`ERR F`）时堆芯最冷 —— **冷启动的一趟在结构上
  永远给不出 `flow=true`**。
- **49**：**`m.fluct` 就是那一 tick 的温度增量**（391/393 逐字节相等）→ `m.temp` 是它的累加，
  **温度是积分器不是惯性环节**，tick ≈ **1.8 s**。
- **50**：**一个风扇 = −60 PSI/tick**（你给的数，文件验过：12 次拨动方向全对、中位 |Δ|=58，
  最干净那段在 +58 和 −2 之间跳、差正好 60；fan=0 基线 +118）。**线性只验到 3 个风扇，
  且不能推广到冷却泵。**
- **51**：远端 public/MIT `The-Reactor-Game-Continuation`，**175 个文件**，**6527 MB → 9.04 MB**
  （排掉的**不是我们的东西**：whisper 缓存、拆包资产、三个第三方视频）；行尾钉 LF。
  **推送**：`github.com:443` **间歇**不通，通时走 Git Data API（`_tools/_attic/scratch/api_push.py`），
  **动 ref 前断言服务器 tree sha == 本地 `HEAD^{tree}`**；`git push` 会 non-fast-forward：
  **先比 `^{tree}` 再 `git rebase origin/main`，不要 `reset --hard`**。

**Phase 47 —— 整理 Workspace。** 779 个惰性散件进 `Workspace.Geometry`，19 个 `Sound` 进
`Workspace.Sounds`，根目录直接子物体 1802 → **999**，**Part 总数 91905 不变**；回滚记录
`ServerStorage.OrganizeRollback20260926`。**代价：多删了 6 个东西**（`CreepySounds` 的 6 个子物体，
找不回来）—— 见 `PROGRESS.md` Phase 47 的 DISCLOSURE 段。

**动手前记住：** 先 `list_roblox_studios`（§0.1），验证读实例状态而不是模块状态（§0.2）。
自动保存已开（§0.9），**不要**提醒 Ctrl+S。
**自动 `add`+`commit` 也已开**（2026-10-01 原话 `AUTO COMMIT+ADD PERMANENTLY ON`）：
每轮改完**直接 `git add -A` + commit**（带 `Co-Authored-By:`），**不再问**；**push 不在授权里**。

**文档只写磁盘（2026-09-26 起）：** 见 §0.0 —— 不再镜像回 Studio，
盘上的 `.md` 就是**唯一副本**，`_tools/verify_docs.py` 已归档到 `_tools/_attic/mirror/`。
「改完同一步把文档补齐」这条**继续有效**。
