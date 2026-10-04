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

### 0.6 【2026-10-04 更正】这台机器**有** Node.js，而且不止它

原文说「node / npx / npm -> NOT FOUND，`@6xvl/robloxstudio-mcp` 跑不起来」——
**是错的**。Node 在 `D:\nodejs\node`，`claude mcp list` 里那两个 server
（`robloxstudio`、`vision-bridge`）本来就是 `cmd /c npx -y …` 起着的。
**当初是拿 `command -v node` 判的，而它只探 PATH。**

实测装着的（2026-10-04）：

| 工具 | 位置 | 备注 |
|---|---|---|
| Node.js | `D:\nodejs\node`（**不在 PATH**） | 两个 MCP server 靠它 |
| Python 3.14.7 | `C:\Python314\python` + `Scripts\pip` | 整个 `_tools/` 靠它 |
| Blender 5.1.2 | `D:\Blender 5.1\blender.exe` | 无头 `--background --python` 可用 |
| **没有** | `uv` / `uvx` / `pipx` / `winget` / `choco` / `scoop` | 装包走 `pip` |

**Blender 那条路**（Phase 79 起）：脚本在 `_tools/blender/`（`trg.py` 是共用件 +
`chamber_grate` / `radiation_scrubber` / `laser_port`），跑法
`"D:\Blender 5.1\blender.exe" --background --factory-startup --python <脚本>`，
产物落操作员自己的交接夹 `D:\BlenderRobloxTestProjects` —— **现在一个资产一个子目录**
（`ChamberGrate\` / `RadiationScrubberUnit\` / `LaserPort\`），
**他自己那份进了 `Misc\`**（`DMR.*` / `Ball.*` / `NeonBox.fbx` / `Test1.fbx`，
外加他挪过去的那份 `README.md`）。**别把它们搬回根** —— `DMR.blend` 引用的
`Part1_*.png` 就在同一个 `Misc\` 里。**最后一公里我走不通**：`upload_asset` 要
`ROBLOX_OPEN_CLOUD_API_KEY`（`asset:write`）+ creator id，**两个都没设** →
fbx/glb 得他自己拖进 Studio。教训同 §0.2：**探条只探它探的那件事**。

**Blender 侧的证据规则**（Phase 82，**与 Studio 侧 §0.2 同源**）：构建循环**不是证据** ——
`_tools/blender/laser_port_check.py` 把导出的 **FBX 重新导入**再逐件读回（原点/尺寸/tris）
并**摆一遍姿态**，`CHECK n ok, 0 failed` 且**失败时 exit 1**。这么做的理由是有一条缺陷
**在构建侧完全不可见**：导出如果把变换烘进几何体，件的原点就塌到包围盒中心，
**摆位、尺寸、渲染全对，而它永远动不了**（取舍 **261**）。

**【2026-10-04 实测补充】那一句「失败时 exit 1」只在**走到了自己的 `sys.exit(1)`** 时成立。**
同一台 Blender 5.1.2 下：脚本**抛未捕获异常 → rc = 0**（`sys.exit(1)` / `os._exit(1)` 才是 1）。
于是「检查器崩了」与「检查器全过」在 shell 眼里**逐字节同形**，而崩溃更可能发生在**错误的那一次**
（畸形输入正是会让解析器抛异常的那种）。**所有 `--background --python` 检查器都要把主循环
包进 `try/except BaseException`（`SystemExit` 放行）→ 打 traceback + `sys.exit(1)`。**
同日翻出的第二半：空集合会说两次谎 —— `all([])` 为真、`max(())` 抛；
凡以「缺失的东西」为主语的断言先 `bool(x)`（取舍 **295/296**）。
第三半：变异必须写成 `--python s.py -- --flag`，写成 `--python s.py --flag` 时
Blender 把它当成**要打开的文件**报个错、然后**照常跑完**（取舍 **295**）。

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

> **【2026-10-04 更正】官方 `rblx_screen_capture` 现在是好的。** 四张**显式**
> `camera_position` + `look_at_position` 的调用给出四张**清晰不同且正确**的画面
> （整体 / 接缝特写 / 俯视 / 贴脸）。上面那段「两个相机逐字节相同」**今天不成立**，
> 但**不改它** —— 当时确实如此。**边界**：这只说明「渲染结果能看」，
> **不等于** Play 模式 / 玩家输入那一半能读（§0.16 未变）。

### 0.14b 【收益】能看图之后，量错的尺子会更早暴露
`Workspace.idk` 那块「46×35 的玻璃板」是**两张截图和三组读数同时**否定掉的
（§0.18 第三张脸，取舍 271）。**读数的错是安静的，图的错是响的** ——
所以能量图的形状，**先拍一张再报数**。这不能替代读实例（§0.2）：图证明「看起来对」，
读数证明「真的是那个值」，两样都要。

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

**2026-10-02 补齐反方向：`require` 工程模块只有插件 VM 能用。** 官方 `rblx_execute_luau`
跑在 Studio 自带助手的沙箱里，`SSS.ReactorBackend` 整条文件夹带着
`Capabilities = LoadUnownedAsset (and 3 more)`，于是**三种写法全被拒** ——
`Clone()` 到临时 Folder（§0.15 的现成解法）、克隆进 `ReactorBackend` 自己、直接
`require(backend.Config)`，报错分别是
`cannot reparent 'Config' to '…__StartupDemo' since '…__StartupDemo' has additional values for the Capabilities property`、
`… '…ReactorBackend' has additional values …`、
`cannot require 'Config' since 'Config' has additional values …`。
**三句话都指向「目标」，没有一句指向「沙箱」**（和第 225 行那条
`ProtectedString expected, got nil` 同一张脸）。所以：**要在活 VM 里 `require` + 驱动
`ReactorBackend`，走第三方 `mcp__robloxstudio__execute_luau`**（它允许 `Clone()` 到临时
Folder 再 require）。**两条通道各管一半** —— 一条的失败是关于那一条的，不是关于代码的；
**撞上 `Capabilities` 直接换通道，不要改写法**（这条花了三次调用）。取舍 **249**。

**顺带**：`rblx_start_stop_play(is_start=true)` 之后，官方工具的 `Edit` 数据模型就没了
（`Edit datamodel is not available in Play mode`），所以**推源码的顺序是：停 → 推 → 起**。

**反过来说，运行时的东西现在有一条真出路（§0.16 的正面解法）：**
不要去「读」运行中的游戏，让**跑在游戏里的脚本自己**把要看的写成文件、推到本机 HTTP sink
（`_tools/receive.py`），字节不进上下文。这条路上还多一条纪律 ——
**这个脚本必须自己报告自己的死因**：它跑在 `task.spawn` 出来的线程里，没人 await、没人 catch，
**「在跑但没事发生」和「第一拍就崩了」从外面长得一模一样**。
`room_watch.luau` 的 `scan()` 因此套着 `pcall`，出错就写一份 `error.txt` 到 sink。

### 0.18 【坑】量一个**旋转过的**件，不能用 `Position ± Size/2`

`Size` 是**局部轴**上的尺寸。`PowerExtractionAssembly.ThermalOutline` 的 `Size` 是
`8.4 × 39.6 × 39.6` 而它**平躺着**（局部 X 竖直，8.4 就是厚度）——
「位置加减半尺寸」把局部 Y 当世界 Y，凭空造出一个 39.6 高的圆柱，
把这个堆芯的顶从 **y 270.4** 报成 **286.0**。我照着这把虚高的尺子建了一版，
**高了 16 stud**，回头才发现。**错的量法不报错，它只安静地给你一个数。**

正确的有向包围盒（OBB）逐轴投三根基向量：

```lua
local R, U, L = cf.RightVector, cf.UpVector, cf.LookVector
local ex = math.abs(R.X)*s.X + math.abs(U.X)*s.Y + math.abs(L.X)*s.Z
local ey = math.abs(R.Y)*s.X + math.abs(U.Y)*s.Y + math.abs(L.Y)*s.Z
local ez = math.abs(R.Z)*s.X + math.abs(U.Z)*s.Y + math.abs(L.Z)*s.Z
```

两条随附纪律：**① 「逐位相同」作为「两个 place 之间的比较」仍然有效**（同一个错方法量两边，
一起错、差还是 0），但**那些数字不是包围盒，不能当尺寸用**；
**② 分组汇总会把错的东西压得很合理** —— 我直到把 `ThermalOutline` 单独拉出来
（一个 `n=1` 的行）才看见 `8.4` 是厚度。取舍 **253**。

**第三次换脸（2026-10-04，取舍 271）：`Shape` 不是 `Block` 的时候，`Size` 连"局部尺寸"都不是。**
`Ball` 的直径是 `min(Size)`，`Cylinder` 的直径是另两个分量的 `min` —— 于是
`Size=(0.5, 46, 35)` 的 Ball 是**一颗 0.5 stud 的弹珠**，46 与 35 是**死数字**，渲染器不看。
我照着这套算出一块 46×35 的「玻璃板」，**两张截图和三组实例读数同时在否定它**，
而我先去怀疑了模型。**量之前先看 `Shape`；`Block` 以外一律走形状规则。**
顺带：**`Size` 不随 `Shape` 变** —— 那对死数字是**改形状的化石**，从它能反推原设计，是线索不是噪声。

**第四个面孔是「问错了面」（Phase 88，取舍 290）：** 我量「rho 62 落在 collar 的顶面上」，
而那个顶面**处处被带盖住** —— **错的问题也会得到一个响亮的数**。

**第五个面孔是「基准」（Phase 89，取舍 293）：** 用户说「依据 18 那个 part 的**最外围**来扩」，
我把 `最外围` 读成**面平面**（63.7114），而它其实是**角**（64.6951）——
**同一个几何量在那个词下面有两个候选**（平面/角、内/外、局部/世界）。
那一版的 5040 条射线 0 条漏**看不见这件事**，因为射线量的是「半径对不对」，
而错的是「**用哪一个**半径」。**一个词如果替你做了选择，你读到的就不是测量。**

### 0.19 【坑】插件 VM **会答应等，却不跑你给它的回调** —— 别把每帧的工作藏在连接里

实测（2026-10-04）：插件 VM 里 `RunService.Heartbeat:Wait()` **正常返回**（0.0190 s），
而**同一个 VM 里 `Heartbeat:Connect` 注册的回调，3 拍跑了 0 次**，`conn.Connected` 还是 **true**。
两者同时成立，所以**「Wait 回来了」推不出「我的回调跑了」**。

**这是 §0.2 换了张脸**：任何**只活在 `Connect` 里面**的东西，从唯一能驱动的那个 VM 里
**看不见** —— 而「看不见」和「没写」在盘上长得一模一样。

**规矩**：每帧的活儿写成**公开函数**（`M.stepBeam(rig)`），**连接里调用的就是它**。
测的是**同一段代码**而不是副本；连接缩成一行，一眼能读完。
这不是为测试开的口子 —— **要等下一帧才知道的东西**本来就应该有一个名字。

**顺带同一天翻出来的第二个**：`Instance.new("Part")` 出生在世界原点。所以一条
`Size=(120, 0.16, 0.16)` 的光束在**第一次被摆之前**是**一根横穿地图的橙色杆子**，
而它只在「创建」和「第一拍 Heartbeat」之间出现 —— **代码里读起来完全正常**。
**创建即可见的东西必须同帧摆好**；`Transparency=1` 的同族部件只是没人管。

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
- **空报告不写。** 2026-10-04 原话「**questiom没条目就不用说了**」——
  `QUESTIONS.md` **只有真的有新条目时才在汇报里提**，没有就一个字都不说。
  同一条适用于任何「本次没有变化」的收尾句（「没验的」那类**不是**空话，继续写）。

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
| The Reactor Game Wiki | `_tools/trgwiki_pull.py` → `D:\RobloxAssetsDownloader\TRGWiki.json` | 拉 ns 0 **∪ 14** |

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
外加一台只读的房间监视器**（`_tools/room_watch.luau`，43 根）。
细节与 run 1..15 的数字**已整段搬到 `PROGRESS.md` Phase 53 尾部**。这里只留一句：**它只读、
不写世界，抑制是「扣在手里不写」而不是「先写后擦」**；**两个实例已于 2026-09-27 删除**（D11 答 B），
`_tools/` 里源码没丢，重新注入就回来。

**当前在跑的活是「原版游戏的三份注入脚本」** —— 不是这个工程里的代码，而是注入到
**原版游戏**（placeId `17596243941`）里、由 Solara V3 用 `loadstring` 执行的单文件脚本：
采集器 `_tools/TRG_original_recorder.luau`（`r60`）、监视器 `_tools/TRG_original_watch.luau`
（`w61`，见 Phase 54）、开机采集器 `_tools/TRG_original_boot.luau`（Phase 70）。
它们**不依赖** `ReactorBackend` / `Config` / `Engine`，只读实例状态；**只记有变化的键**，
**三份都不按任何东西**（驱动器的删除见 Phase 62）。用法：`docs/RECORDER_HOWTO.md`
（开机那份 `docs/BOOT_HOWTO.md`）；测试 `bash _tools/run_tests.sh`。

**Phase 71/72（2026-10-02）—— 开机采集器两趟真机：`b1`→`b2` 否掉两个假设，`b2`→`b3` 又翻出第三条。**
两份产物 `Data/originalboot/261002-{133048,140017}/` 的 `meta.txt` 各自带 `build=`，数字能对回代码。
`b1` 否掉的两个假设：**午夜是开盘不是收盘**（那一按在 11:51 PM，t≈95 s 封存时核心**正在点火**；
现在只留一行 `# MARK midnight`、**不封存** —— 注释行是行格式冻结下唯一安全的加法）；
**只挂 `DescendantAdded` 不够**（出生时的值被当基线播掉，面板**文本 0 行**；现在有**出生记录**）。
`b2`（`reason=hotkey` / 428.82 s / 25007 行）逐个判决：午夜那条**成立**（`# MARK` 恰好一行
`at 14:02:10`，捕获越过它继续记到 `14:07:44`）；出生记录**只成立一半** —— `Text` 从 0 涨到 **3**，
正好是日志面板**每格的第一条**，然后 **6 分 41 秒**再没有一条，而同一趟的 `r60` 从**同一个
`LogsFrame`** 记到 **35 条不同消息**（含 `START-UP COMPLETED`）、`w61` 数到那三格被**销毁 47 次**。
**根因在交付的源码里：键是路径，不是实例** —— `keys[key] == nil` 让同路径的第二个实例整段跳过，
而活下来的连接指着**已被 `Destroy()` 的旧行**。`b3` 的改法：`born` 且 `ownerOf[key] ~= obj` →
**先断旧连接、再重指键**（不断就会往一条它已不占的路径写，产物就会报出面板**从没显示过**的消息）；
`keys`/`writes` **故意保留**（预算是按**路径**记的，`suppressed.txt` 认的就是路径）。
4 倍量下仍是 `dropped_chunks=0` / `suppressed_keys=0` / `sink_error=none`。
**我自己另有一处更正**：按「8.75 s/表盘分钟」外推到正午的「≈105 分钟」是错的 ——
午夜之后**恰好 1 表盘分钟/真秒**，`5:08 AM` 收尾。`run_tests.sh` **rc=0**
（**37 / 6 / 6 / 38+1SKIP / 34**，`verify_boot_capture` **6132 行 0 不合格**，`selftest_boot` **12/12**）。
`b3` = **45200 / 941 / `172416deb2073c9d22417a47833687ef`**，**它自己还没在原版跑过**
（跑完第一件事：`grep -c TemplateLogFrame` 看是不是从 3 涨到几十）。细节 `PROGRESS.md` 71/72，
取舍 **243..248**；`docs/BOOT_HOWTO.md` §1.2/§1.3/§6/§8 已按实测重写。

**Phase 73（2026-10-02）—— 你问「那你开机能写吗」，答案在 remake 里，两半都当场跑了一遍。**
**开机链** = `Config.Shift.StartupSteps`（**16 条** hold 表，和 **113.4 s**）+ `LogPanel`
（`engine.events` 的第一个真读者）；**开机屏** = `Config.Shell.BootScreen.Reveals`（**7 条**）
+ `BootPanel`（**14 s**）。这一轮只**驱动**它们、读实例、写盘，没改代码。当场数字：
`boot → Ready at 14 s`、`Running at t=114 s`、逐条比对 **16/16 mismatches=0**、
面板画出**最新四条**（3 红 `TemplateLogFrame3` + 1 青 `TemplateLogFrame1`）；
开机屏 t=0..13 的可见集合与 7 条 reveals **逐条对上**（含 t=5 那条「清空 diag + 只亮 log 6」的怪条目），
t=14 翻 `Ready` 时整屏收掉（那是 `RoomShell` 换脸）。**`BootFrame` 只在 3/7 台**控制室监视器上
（`Main` / `Power` / `Thermal`），且它在**主控室**监视器上、**不在**日志监视器上。
世界逐位还原（`LogsFrame` 1→1，`BootFrame` 下 authored-visible 69→69，靠**快照写回**而不是
「再 refresh 一次清干净」）。**通道**：官方 `rblx_execute_luau` 在 `ReactorBackend` 上被
Capabilities 全拒 → 见 §0.17。**没做的还是老那一半**：世界侧逐段视觉（E-VENT 真排气、
激光真打）—— 原版那 110 秒里玩家能看到的只有那块日志面板。细节 `PROGRESS.md` 73，取舍 **249**。

**Phase 54（2026-09-27）—— 监视器 `_tools/TRG_original_watch.luau`：对准的是原版，不是 AIRemake。**
（你原话「我说的整个控制室+核心腔室+音频监听是监听原游戏的，又不是现在的」，
目的也说明了：`你根本不会做开机`，所以产物要能回答「开机到底做了什么」）。
**它和 `room_watch.luau` 最大的结构差别：根不是写死的** —— 猜错**是静默的**
（根不存在 = 零行 = 和「没事发生」同形），所以它**先普查、再选根**，并把**选择过程本身**
写进 `rooms.txt`（谁进了、谁没进、**为什么**）。产物九份含 `audio.txt` / `error.txt`，只读。
本机 `watch_harness` **45 PASS**、`selftest_watch` **15/15**。
**2026-09-30 那趟有 11 份产物、无 `error.txt`**，并翻出两个**跑起来才看得见**的缺陷
（hook 晚装 28 秒、`MaxQueue` 太小 → 修在 `w60`/`w61`）。**跑法**：起 8766，
原版里 `loadstring(game:HttpGet(...))`；sink 8765 已在跑；**要抓开机就趁开机前注入**
（开局就响着的声音**永远不会**发 `Played`，DECISIONS 157，晚注入 = 让掉开盘那段）。
**三份可以同时注入**（全局变量、输出路径、热键都对过）；热键 **`RightAlt` = 推/冲、
`RightControl` = 停/封存**，**`RightShift` 只属于采集器**（曾经撞过，各 harness 有检查守着）。
**D11 已执行**：AIRemake 那边 Phase 53 的 `SSS.MCP_RoomWatch` + `MCP_RoomWatchRunner` 已删。
细节 `PROGRESS.md` 54 / 57.10，取舍 **160..165**；`QUESTIONS.md` P8 已由产物回答。

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
- **md5 与字节数一律在 `docs/RECORDER_HOWTO.md` §2**（`r60` / `w61` / 探针），**注入前核那个**。
  细节 `PROGRESS.md` 62，取舍 **201..205**。（HOWTO 以前教人按一个已不存在的按钮 ——
  **散文说的谎和代码说的谎一样贵**。）
- **下一次三份都要重注**：`r60` 字节没变，监视器换成 `w61`，开机那份首次注入（Phase 70）。

**悬着的还是那两件**（`QUESTIONS.md` 无新条目）：**P4:A 冷却泵 2/3 档**、**P6:A 的 187 键探针**。
**信标补不上的那一格**：顶层代码在信标**之前**抛错时与「从没注入」在盘上逐字节一样；
补它要放到文件第一行（那时 `CONFIG` 没读完），**代价大于收益，不做**。

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
你那段 hook 钉死了 t=0 = `MonitorBootButton` 被按 → **§66.5「抓取开始时就已在开机中」是错的**，
原地划掉更正。由它量出并实现：`BootSeconds` 3 → **14**、`BootScreen.Reveals` **7 条**、
新模块 **`BootPanel`**（写 `BootFrame` **里面** 51 个 label 的 `Visible`，与 `RoomShell` 写
`BootFrame.Visible` **属性不相交**）。**只建模布尔、不重建曲线** —— 捕获里那 99.7% 的位移行是
「变化才写」，**布尔活得过采样，曲线活不过**。细节 `PROGRESS.md` 67，取舍 **230..232**。

**Phase 68（2026-10-01）—— 镜像追平；`run_tests.sh` 不是并发安全的。**
**① 判据看 `N of M detected`，不看 rc** —— `selftest_watch.py` 写死固定路径并 `rmtree`，
**同时跑两遍互删产物 → 报成「NOT DETECTED」**（17/29 和 25/29 两数 = 污染指纹，其中一遍 rc 还是 **0**）。
**② `src/ReactorBackend/`** 漂了 4 个 Phase（3 改 / 2 无 / 5 相同 —— **半新半旧最难认**），
已按 §0.17 通道 + 两侧 **CRC-32** 追平复验 10/10；**它没有写入者**，会再旧。取舍 **233/234**。

**Phase 70（2026-10-02）—— 优化操作员自己那份开机采集脚本 → 新文件 `_tools/TRG_original_boot.luau`。**
原话「优化一下我写的那个开机（主要是采集，然后我注入）」——「我写的那个」= 他
`%LOCALAPPDATA%\SolaraTab\Test.lua` 里那份**开机屏逐属性采集器**；**那个文件一个字没改**，
优化落在仓库新文件，他从 8766 `HttpGet` 下来注入。
**靶子是量出来的**：他那份产物 **1,162,737 行 / 179.8 MB / 158 秒**，其中 **99.4% 是
`…MonitorUI.GlitchEffect.GlitchFrame` 的 Position/Size** → `GeometrySkip = {'.GlitchEffect'}`
**按路径不挂几何属性**（`Visible`/`Image`/颜色照记 —— 开机屏自己那 0.2% 才是要的，
同文件同 ClassName，只能按路径分）；另修 `appendfile` 串档、缺 `DescendantAdded`、无传输层。
**根没动**：`RootName = 'Monitors'` 与他自己那行 `FindFirstChild` 逐字相同。**行格式冻结** ——
`V` 是贪婪 `(.*)` 且两端锚定，**行尾加字段不是向后兼容的**；新东西一律新行（`#` 开头）或新文件。
字节 **38609** / **835** 行 / md5 **`243adb577f1442a069144f0bbb6df8f0`**（**HttpGet 直取，
盘上就是注入进去的字节**）—— **这是 Phase 70 交出去的那一版，也就是第一趟真机的 `build=b1`；
同一个路径现在装着 `b3`，当前身份看 Phase 71/72 那段，别把这两个数当成同一份文件。** 本机五场景
**99 PASS / 0 FAIL / 1 SKIP**、变异 **8/8**。用法 `docs/BOOT_HOWTO.md`，取舍 **236..242**。

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

**Phase 74（2026-10-02）—— 「为啥机房这么容易坏掉」：「机房」= `s.MainframeMeltdown`（你 D9 的原话），
而它的规格**不用猜、原版把说明书放进了世界里**。**
`Workspace.Consoles.ElectricGridConsole.DRMScreen.SurfaceGui.MainFrame.MainframeFrame.OperationsFrame.TextLabel`
就是 Digital Reactor Manual 的 MAINFRAME 段，flow 产物逐条抓到了 —— **逐字全文已抄进 `PROGRESS.md` 74.1**
（必须抄：`Data/` 是 gitignored，不抄等于没抓过）。答案四条：**① 它按 uptime 磨损、不是故障**
（Tesseract 是全设施唯一一台，算 CBL+控制台+传送门+医疗机，**天生超频**）；**② 起火是唯一加速器**
（「fires … cause QPUs to degrade at a much **faster** rate」，所以手册叫**带着灭火器**去换 QPU）；
**③ Shift 1 豁免**（维基：不掉 QPU），掉点「usually occur at the **middle and end of Shift 2**」；
**④ 它是配额不是故障**（6 个 QPU，前五次只是监视器蓝屏，第六次才瘫，**换 QPU 就修**）。
那段说明自己盖着 **`{wip system}`** 的章 —— 原版这系统**本来就没做完**。
**实测**（11 趟里只有 2 趟真的翻起）：`t=719.86` 与 `t=868.94`（开机后 ~12–14.5 分钟），
后者那一刻温度**只有 7978 °F** —— 离 `MeltdownF=39000` 差五倍，**所以它从来不是「堆芯要炸」**。
**remake 这边不是「容易坏」，是根本没装**：`MainframeMeltdown` 全 DataModel 零命中，
`StateBridge` 第 57 行 `set(stats,'ActiveQPUs',6)` **焊死**。**要接不接 → `QUESTIONS.md` `P10`**，
**我没动**（§1.4 第一条）。细节 `PROGRESS.md` 74，取舍 **250**。

**Phase 77（2026-10-03）—— 整间腔室重建成 `Workspace.RebuildChamber`（1377 件）。**
原版 `ChamberWalls`(2267) 的结构：**外壳格栅在 r≈100**（2002 件薄板 = 72 竖肋 × 12 段 + 横带；
**不是实心筒**）+ **混凝土内环 D175** + **内筒 D135.6**（下半橙 Neon / y152 中隔 / **上半竖管伸到
y503.4，比外壳 y347 还高 156**）+ 顶部倒角（y260 r105 → y310 r60）+ 中段加厚环（y204–263）。
实测 `216.0 × 503.5 × 216.0` vs 原版 `220.3 × 503.4 × 226.4`（**Y 逐位吻合**，半径差 4–5%，
原版半径不对称，**没去凑**）。**两个新坑**：**分组包围盒会把两条分开的弧形观察窗带
（θ ±89–152，y287–294）合成一块不存在的 106×206 平板**（取舍 **255** —— 汇总只能用来「找」，
不能用来「读」）；**对称性是免费探测器**（腔室对称而我的包围盒不对称 = 位置读错了，
`Union` 的 r 从 87.4 读成 104，x 立刻从 108 变 118）。`Core`(21) **没重建**（全 `Transparency=1`，
纯 FX 架）。mesh 用近似几何代替、**并且写出来**（取舍 **256**）。细节 `PROGRESS.md` 77。

**Phase 75/76（2026-10-03）—— Rebuild 里重建反应堆腔室（第一、二刀：搬运 + 堆芯那一摞）。**
**Rebuild 的 placeId = `131274481205639`**（第三方 instanceId `9600b305-e366-4c12-bab6-204a748a32aa`）。
**75**：把 AIRemake 的 `ChamberWalls`(2267) / `Core`(21) / `PowerExtractionAssembly`(1921)
用 Ctrl+C/Ctrl+V 搬进 Rebuild，**并且摆回原版自己的世界坐标**（`Δ = target − current`，
`ChamberWalls` 本来就在位、`Core`/`PEA` 各偏 193.7/146.3 —— **一次粘贴不保证一个偏移**）。
**76**：`Core` 是**纯 FX 架**（21 件全 `Transparency=1.00`；看得见的「堆芯那一摞」是 `PEA`）。
**`RebuildColumn_v2`** 258 件 @ `(140.125, −0.603)` = 原版**正东 150 stud**，实测
`89.8 × 54.1 × 101.4` vs 原版 `90.9 × 54.0 × 98.1`，底/顶 `216.4 / 270.5` 对 `216.4 / 270.4`。
三座**宽舱段**（不是细柱！径向 16–44.5、切向 49、高 30.5，反解自包围盒）+
36 片六角砖 + 两段法兰盘 + 中心镀层筒 + 38 片光伏板带 + 顶部排气盘/橙 `ThermalOutline` 盘。
**Z 深 3.4% 是已知偏差，没修** —— 缩顶盖能让 Z 好但 X 坏，总误差 4.6→4.9（取舍 **254**）。
**这一轮最重要的是 §0.18**：那把量错 15.6 stud 的尺子。细节 `PROGRESS.md` 75/76，
取舍 **251..254**。**下一步**：`ReactorCBLs`(8291) / `METU`(1612)，然后是**删掉被复制的三份原件**
（`ChamberWalls` / `Core` / `PowerExtractionAssembly`，尺子用完再拆）。

**Phase 83（2026-10-04）—— LaserPort 进 Studio：上色、点一下转云台、真的打出激光。**
三句能直接用的：**① Roblox 的 glTF 导入读 10 studs/文件单位**，而 FBX 那条路认
`STUDS_PER_UNIT = 5.902` —— 所以同一个 `.glb` 进 Studio 是**设计尺寸的 1.6943 倍**
（十一个件独立拟合、误差 ≤0.0007；**均匀**，所以装配关系没错，只是大了 70%）；
**② 导入器会把每个 MeshPart 重新原点化**，于是 `Position` 既不是节点原点也不是它自己的
包围盒中心，而 `Model:GetPivot()` 在导入模型上**直接不可用**（轭臂和头回了**逐字节相同**的
pivot）→ 转轴只能**重建**：`origin = part.CFrame * CFrame.new(-row.off * k)`，
**同一节点的每一件都是同一个原点的独立估计**，一致就是免费检查（实测 3/3、3/3、**5/5**）；
**③ 交付成 `Script` 不是 ModuleScript**（ModuleScript 自己不会跑，ClickDetector 只在
Play 模式存在），而**测试要 require 交付物自己的字节** → 把 `Script.Source` 读出来塞进临时
ModuleScript 再 require（§0.15 的路线用在 Script 上）。实测：底座**位移 0.000000**、
到 pan 轴距离漂移 **4e-6**、到 tilt 销 **3e-6**、光束轴·镜片 −X **1.000000**、
打空/打中**两个分支都跑到**、摆头后光束跟了 **59.32 studs**；Studio 那份与盘上
`_tools/laser_port_gimbal.luau` **逐字节相同**（19590 字节）。**没验的**：真实鼠标点击
（没玩家点不了，§0.16）、TweenService 补间、接收端（没导入）。细节 `PROGRESS.md` 83，
取舍 **263..266**，两条新通用坑在 **§0.19**。

**Phase 84（2026-10-04）—— `TransitionPillar`：18 边圆柱接 24 边圆柱，Bridge Edge Loops。**
四句能直接用的：**① 这类形状只能在这边做** —— Roblox 的 MeshPart 是做完的三角形汤，
那一侧**没有**算子能缝两条**边数不同**的开环（要手算 n+m 个三角形），**不是更难，是不可达**；
**② 删端面必须 `context="FACES_ONLY"`** —— 默认会把棱和点一起带走，带走的就是要桥的那条环，
而失败长得像「Bridge Edge Loops 什么都没做」；**③ 两条环之间的空隙不是余量，它就是桥** ——
共面则 42 个三角形全部**退化**（零面积、看不见，而「42 个面」**照样成立**）；
**④ 跨格式比较前先按位置焊接** —— glTF 没地方放多边形，把每个角拆成独立顶点
（`.glb` 读回 504 顶点，焊完 **126**，与 `.fbx` 逐位相同），不焊就会把
「`open_edges=504`／`components=128`」当成文件坏了，而那是**关于问法的**。
**变异三条**：`--no-bridge` **10 红**；`--twist`（翻转绕向）**全绿 —— 负结果**，
`recalc_face_normals` 抹掉翻转且 `bridge_loops` 按**几何**推对应关系，绕向传不到带子；
`--cross`（手工对侧相接）**只有 twist 那一行红**（质心半径 0.5898 vs 门槛 1.8900 vs 正确的 2.1837）——
**一条从没红过的断言是装饰**，所以补了第三种变异把它逼红。
两种格式各 **20 项全绿**（`CHECK 20 ok, 0 failed`），248 面、126 顶点手核过。
**没验的**：没进 Studio（进就导 `.fbx`，glTF 那条 1.6943 倍）、材质没验、倒角 0.06 是我挑的数。
细节 `PROGRESS.md` 84，取舍 **267..270**，片段 `docs/SNIPPETS.md` **§5.15**。

**Phase 85（2026-10-04）—— 看 `Workspace.idk`：一次我自己造出来的尺寸，和一条要交代的写入。**
用户原话「**看下Workspace.idk**」（+ 一句「要不要我导出 obj 给你看」）。三句能直接用的：
**① `idk` 是一台 1 stud 见方的小台座**（Rebuild 里，`(-63.15, ·, 8.02)`）：`Part` **Cylinder**
底座 + `Union` 机身 + 十字拉杆/叶片 + **两个套在一起的球**（白 `Glass` 直径 0.5 套黑 `Neon` 直径 0.45）
+ 一片 `Transparency=2.00` 的 `Glass` MeshPart（`Script` 用 `BindToRenderStep` 每帧
`CFrame.lookAt(anchor, cam.Position)` 让它正对相机）扛一个 `Highlight`（红填充 / 白描边 / AlwaysOnTop）。
**② `Ball` 的 `Size` 不是尺寸** —— `(0.5, 46, 35)` 的球**直径只有 0.5**，46 与 35 是死数字；
我据此报过一块「46×35 的玻璃板」，**两张截图和三组读数同时在否定它**（见 **§0.18** 第三张脸，取舍 **271**）。
那对死数字是**改过 Shape 的化石** —— 原来多半就是那两块板（用户写的「有明显的方格子」很可能出自它们）。
**③ 「光照上去会有反射」= `Material=Glass`**（Roblox 的 Glass 透明度再高也留着高光）。
**这一条我原来给的处方是错的，已作废：不要改成 `Plastic`** —— 用户当天就驳回了，
原话「**不对啊，你改成plastic就没有那种扭曲的效果了啊**」。Glass 的**折射就是他要的扭曲**，
那个高光不是另一个可以关掉的图层，**它就是这个材质本身**；换 `Plastic` 等于拿功能换 bug。
**两个 `Glass` 件的 `Reflectance` 本来就已经是 0**，所以「关掉反射层」这条路根本不存在。
要「不反光而有折射」只有 `MaterialVariant`（`BaseMaterial = Glass` + 白 `RoughnessMap`
和／或黑 `MetalnessMap`），**但两张图都要上传的 `ContentId`，本机没凭据 → 走不通**。
不装任何东西的三条替代：`Lighting.EnvironmentSpecularScale` 1 → 0（**全局**）、
`Material = Water`、或把 `Glass` 染黑。细节 `PROGRESS.md` 86.7，取舍 **278**。
**要交代的**：为看清画面做过一次**染色实验**（底座染蓝、`Neon` 染红），**已逐项还原**，
但底座的 **`Material` 改前没读**，按同族 22 件推定还原成 `Metal` —— 这是本轮唯一说不准的地方；
另调过一次 Studio `undo`，它**什么都没撤销**且**不告诉你改了什么** → **`undo` 是盲写，不能当清理工具**（取舍 **272**）。
细节 `PROGRESS.md` 85。`QUESTIONS.md` **无新条目**。

**Phase 86（2026-10-04）—— 把 `Workspace…Folder.18` 那圈 18 边环往外扩成 24 边墙，并真的接上。**
用户原话「**wokspace子文件夹下面有个文件夹叫18，我需要你往外扩展为24边形墙壁，并且要正确衔接**」。
**靶子先在 Rebuild 里量出来**（placeId `131274481205639`）：`Workspace.Folder.Folder.Folder.18`
是 19 件的 18 边环，**apothem 63.712**、**顶点落在 +X**、平台顶面 **y = 47.400** ——
三个数分别由「从外面 720 条向内射线（rmin 63.711 / rmax 64.695，零漏，剖面在 0/20/40° 折断）」、
「`64.695 = 63.712/cos(10°)` 是**外接圆**不是 apothem」和「垂直落点探针」得到。
**六句能直接用的：① 这件形状 Roblox 侧做不了**（MeshPart 是做完的三角形汤，
18 接 24 要手算 84 个三角形，**不是更难是不可达**，同 Phase 84）；
**② 两条环的半径从 apothem 反解**（`r = a / cos(π/n)`），`annulus` 每段 4 条四边形带
（`trg.revolve` 每端只盖**一个 n 边形**，做不出有洞的环端面）；**③ 删端面必须
`context="FACES_ONLY"`**；**④ 桥之前先断言**（环数 + 半径；`bridge_loops` 会**配错环还给你一个合法 mesh**）；
**⑤ 量出来的数和挑的数要在代码里长得不一样**（取舍 **274**）—— 63.712/相位/47.400 是**读数**，
24 边 apothem 68.000 和三个高度是**挑的**，13.2 stud 因此是个**矮墙**、往外悬 3.3 stud；
**⑥ 归一化各自除以自己**（取舍 **275**，见下）。
**验证**：`.fbx` 和 `.glb` 各 16 项 **32 ok / 0 failed / rc=0**（闭合流形、单壳、四条环的边数与半径、
带子 84 个三角形**两端与两条环逐条对齐**、内外各 42、不扭、无退化面、0..13.20）；
三个变异各自红在自己的断言上（`--wrong-pair` 最干净：28 ok / 4 红）。**`--no-bridge` 是负结果** ——
twist 那行也红了，但**因为带子是空的**而不是因为扭，那行在没有带子时没有区分力。
**`apply_chamber_wall_materials.luau` 第一版有个真 bug**：把**两边**都除以**场景里最宽的件**，
那只在导入恰好是设计尺寸时才抵消 —— 设计尺度过、**整体 ×1.6943 那轮全军覆没**
（比例打印得和设计**一模一样**，判据全错）。改成**每件除以自己的最大边**。
**收货**：`D:\BlenderRobloxTestProjects\ChamberWall24\`（`.fbx` 是唯一该导的那个 ——
glTF 那条路 **1.6943 倍** = 10/5.902）；手动落地到底面中心 `(-12.200, 47.400, -85.362)`、
**scale 1.0**、不旋转，期望 `137.17 × 13.20 × 137.17`，**相位不用补**（18/24 两套顶点集都对 180° 镜像不变，
取舍 **277**）。**没做的**：没进 Studio（无上传凭据）、材质没在 Studio 验。
细节 `PROGRESS.md` 86，取舍 **274..278**，片段 `docs/SNIPPETS.md` **§5.17**，待办 `docs/TODO.md` **§3.5**。

**Phase 87（2026-10-04）—— 24 边墙**在 Studio 里建好了**：用户那句「你自己在 studio 里面做」的落地。**
四句能直接用的：**① 没有上传凭据也能建 MeshPart** —— `AssetService:CreateEditableMesh()` +
`Content.fromObject` + `CreateMeshPartAsync`，网格作为**对象**存在 place 里（不要凭据），
**而且不重新原点化**（`MeshSize == Size`，局部 (0,0,0) 就是 pivot —— 比导入器好用）。片段 `docs/SNIPPETS.md` **§5.18**。
**② 代价写在这里**：这条路出来的 MeshPart，`CollisionFidelity` **写不进去**（Default/Hull/Precise/Box 四个值
全部 `pcall` ok、全部读回 `Default`；邻座 `SourceType=Uri` 的导入件**同一个写立刻生效** —— **对照才是证据**），
所以碰撞面**永远是凸包**，而环面的凸包是**实心圆盘**（137.17 stud，会把腔室封死）→
交付态 `CanCollide=false` + `CanQuery=false`（取舍 **279/280**；**这条交付态已被 Phase 88 取代**）。
**③ 射线量 MeshPart 量的是碰撞体，不是渲染网格** —— 「同一个网格，一面对一面错」**本身就是尺子错了的信号**；
验形状只能靠 `MeshContent` → `CreateEditableMeshAsync` → **逐顶点读回**。结果 **32 项全绿**，
接缝 `delta 0.0006`、角相位误差 `0.0000°`。
**④ 用户手动拖进来的那份**（`Workspace.Wall24`）**整体是设计的 1.0769 倍、偏 0.873、内面差 3 stud 没接上**
（均匀缩放 → 指向导出链）—— 已按他选的搬进 `ServerStorage.Wall24_import_20261004`（**没删**）。
`docs/TODO.md` §3.5 已重写，**「手动拖 fbx」那条路作废**，并留了一条待办：
同一套导出链的 `LaserPort` / `TransitionPillar` **要按设计重量一遍尺寸**。
细节 `PROGRESS.md` 87，取舍 **279..285**，片段 **§5.18**。

**Phase 88（2026-10-04）—— 那面墙改成 66 个 Part 拼的：外形与碰撞同源，而且「正确衔接」终于能被射线量。**
四句能直接用的：**① 触发它的是一个测出来的事实** —— MeshPart 那条路交付的墙是整个邻里**唯一不参与物理**
的一件（延续的那圈环 **19/19** `CanCollide`、与墙重叠的 **60/60** 全是实心），
「保守地 `CanCollide=false`」在这里等于「**玩家能穿过去的那道墙**」。用户选了**三条路里的第三条**：
**由同一批 Part 同时负责外形与碰撞**，代价是件数 1 → 66、几何重做一遍（原 MeshPart **没删**，
存档为 `ServerStorage.ChamberWall24_mesh_20261004`）。取舍 **286**。
**② 构造是精确的，且这件事不显然**：正 n 边形壳的一个面 = **一个 Box**，弦取满 `2a·tan(π/n)` ——
两个半弦正好够到**顶点**，相邻面板在顶点恰好相接、内侧轻微重叠，**一圈的并集精确等于壳，角也在内**。
不用楔形补角、没有缝、也不外凸。斜接带是同一种盒子斜 55°，**厚度是垂直厚度 `WALL·cos(lean)`**
（4.00 → **2.2930**），不是水平间距。片段 `docs/SNIPPETS.md` **§5.19**。
**③ 交付数字一律实测**：接缝台肩**手算 0.434、实测 0.3002** —— 手算错在拿**多边形顶点**相减，
而面板是**盒子**，角上有**切向悬出**；同一份手算里的另一项（0.5153 vs 0.520）却几乎全对。
**手算用来定形状，交付数字用实测，错的那个也写在实测旁边。** 取舍 **289**。
**④ 换载体的收益是射线** —— MeshPart 时代射线只打到那个 137 stud 的凸包盘，**形状根本量不了**；
现在**几何体就是碰撞体**：**7 高度 × 720 方位 = 5040 条射线 0 条漏**，collar 停在 63.7120、
wall 停在 68.0000、墙顶 y 60.6000、**rho 55 仍然 MISS**（腔室没被堵死）、66/66/66 三个标志。
接缝在**两侧各量一次**：环 63.7114 / 新件 63.7120 → **delta 0.0006**。验证 **117 项 0 失败**。
**顺手更正两条**：§0.14 的「截图逐字节相同」今天不成立（四张显式机位都正）—— 见 §0.14 的新更正块；
我还在验证器里**问错了一个面**（「rho 62 落在 collar 的顶面上」，而那个顶面**处处被带盖住**）——
**错的问题也会得到一个响亮的数**，§0.18 至此四个面孔。细节 `PROGRESS.md` 88，取舍 **286..292**。

**Phase 89（2026-10-04）—— 交付物改口：环进 Blender，衔接在那边做；`最外围`是一个**半径**，而这个环有**两个**。**
用户原话「**你把那个18边形搞到blender然后再衔接，我直接作为参考自己做**」——
把 Phase 86..88 的落点整个换掉（那三轮是**我在 Studio 里建**，Phase 88 的 66 个 Part 已被驳回）。
四句能直接用的：**① 环有两个半径** —— 面平面 `RING_A` **63.7114**、角 `RING_R` **64.6951**
（1440 条向内射线 0.25° 零漏），**最外围是角那个**；Phase 88 把 collar 外面放在**面平面**上，
于是环的 18 个角从墙里戳出来 —— **它自己量到了 0.3002 并把它当成了故意的台肩**（§0.18 第五张脸，取舍 **293**）。
**② 修法是可证最小的**：墙的内面平面放在 `RING_R`，因为外接 m 边形（inradius `R`）包含环
（circumradius `R′`）**当且仅当 `R ≥ R′`**，`R = R′ = 64.6951` 在 6 个方位 `0+60k` **恰好碰到**环的角
（把 24 边形的**顶点**对到环的角上会戳出 0.48 stud，那条路不成立）。
**③ 转半格的壳过掉每一个半径检查**（apothem/弦/面积/轮廓半径全不变），所以相位只能锚在**被接的那件**上
（取舍 **294**）；apothem 拟合要按**壳自己的相位**取**面法线**（`phase + 180/n`），
拿顶点方向投影量回来的是 circumradius。
**④ 交付**：`D:\BlenderRobloxTestProjects\ChamberWall24\` 的 **`.fbx`**（glTF 那条路进 Studio **1.6943 倍** =
10/5.902），底面中心 `(-12.200, 47.400, -85.362)`、**scale 1.0**、不旋转，期望 `138.58 × 13.85 × 138.58`，
**相位不用补**。四条接缝实测：**J1 顶点间隙 0.00000**、**J2 = 64.6951**、
**J3 最坏 `r·cos` 64.6327 ≤ 64.6951**、**J4 60° 扇区 环 3 / collar 3 / 墙 4**；检查器 **76 ok / 0 failed**，
四个变异各红在自己那条上。**两个通用检查器坑已进 §0.6**（崩溃 rc=0、空集合、`-- --flag`）。
细节 `PROGRESS.md` 89，取舍 **293..296**，片段 `docs/SNIPPETS.md` §5.20。

**动手前记住：** 先 `list_roblox_studios`（§0.1），验证读实例状态而不是模块状态（§0.2）。
自动保存已开（§0.9），**不要**提醒 Ctrl+S。
**自动 `add`+`commit` 也已开**（2026-10-01 原话 `AUTO COMMIT+ADD PERMANENTLY ON`）：
每轮改完**直接 `git add -A` + commit**（带 `Co-Authored-By:`），**不再问**。
**`push` 也已永久授权**（2026-10-04 原话「**始终允许自动push**」，推翻此前「push 不在授权里」）：
每轮 commit 完**直接 push**，不再问。**但 §0.6/Phase 51 那些坑还在** ——
`github.com:443` **间歇不通**，`git push` 会 non-fast-forward：**先比 `^{tree}` 再
`git rebase origin/main`，不要 `reset --hard`**；直连连不上时走 Git Data API
（`_tools/_attic/scratch/api_push.py`），**动 ref 前断言服务器 tree sha == 本地 `HEAD^{tree}`**。

**文档只写磁盘（2026-09-26 起）：** 见 §0.0 —— 不再镜像回 Studio，
盘上的 `.md` 就是**唯一副本**，`_tools/verify_docs.py` 已归档到 `_tools/_attic/mirror/`。
「改完同一步把文档补齐」这条**继续有效**。
