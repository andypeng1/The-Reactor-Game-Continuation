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
| §0.0 本节 / §0 血泪教训 / §1 项目概述 / §4 用户偏好 / §6 不能碰 / §7 参考 / §8 总结（薄） | **`CLAUDE.md`**（自动加载） | 每轮 |
| Phase 摘要（原 §8 下 Phase 47..107 的压缩段） | `docs/PHASES.md` | 按 Phase 号回看时 |
| §2 已完成的系统 | `docs/SYSTEMS.md` | 动代码 / 场景之前 |
| §3 待办 / 下一步 | `docs/TODO.md` | 决定做什么之前 |
| §5 关键代码片段 | `docs/SNIPPETS.md` | 抄 / 改任何一段实现之前 |
| 采集器/监视器怎么跑 | `docs/RECORDER_HOWTO.md` | 注入前后 |
| 阶段记录 / 取舍 | `PROGRESS.md` / `DECISIONS.md`(1..74) + `DECISIONS_2.md`(75..) | 动手前后按需 |

> **2026-10-10 拆分**（用户：「把那个CLAUDE.md精简一下，拆成多个文件什么的」）：
> 原 §8 底下 Phase 47..107 的压缩摘要（**1155 行 = 原文件 1725 行的 67%**）搬到了 **`docs/PHASES.md`**；
> 顺手把 **§0.13..0.22 那十条教训**从 `## 1. 项目概述` 标题底下挪回了 **§0**（它们本来就被
> `## 1` 的标题框在错误的章节里 —— 这正是 §0.13 那条「按子串锚定会落进错误的块」的同族）。
> CLAUDE.md 现在只剩：§0.0 规则 / §0 血泪教训 / §1 概述 / §4 偏好 / §6 不能碰 / §7 参考 /
> §8 一句总结 + 动手前规则。**章节号一个都没动**，所有 `§2.6` / `§5.9` / `§0.13` 之类的引用继续有效。

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
**Phase 105 —— 这 58 px 不是工具的毛病，是**两个坐标空间**的差**：`GuiObject.AbsolutePosition` 和 `PlayerGui:GetGuiObjectsAtPosition` 量的是 **CoreUISafe 空间**（y 从顶栏下面量），`VirtualInputManager` 和 `UIS:GetMouseLocation()` 量的是**屏幕空间**（y 算上顶栏），差 `GuiService:GetGuiInset().Y`。所以「GUI 上的矩形 → 像素」一律 `+ GetGuiInset()`，**而 `ScreenGui.IgnoreGuiInset` 不改变这件事**（它只挪 ScreenGui 自己的矩形，不挪子件所在的空间）。细节见本文件 Phase 105 与 `DECISIONS_2` **422**。

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

### 0.20 【坑】「数出来多少个」先问**数的是谁** —— 同一份网格，两个格式给出两个答案

两条，都是 2026-10-04 量出来的，**都属于 §0.18「错的量法不报错」那一族**：

**① 按**边数**给面分类，回答的是**文件格式**，不是资产。** 我用 `len(f) == 3` 认「桥接三角形」，
于是在 `.glb` 里把 22 + 16 个**端面**三角形一起数进去，「42 个桥接三角形」读出 **80**，
「闭合」读出 80 个面。**同一份源码、同一次构建，换个格式就换个数** —— 这就是问题问错了的信号。
改用 **material slot** 分类（两个格式都有，而且它本来就是规格在说的那件事），
面数改成**三角化后的** `Σ(len(f)−2)`。**实测 FBX 保留 n-gon（1 + 1），glTF 三角化（16 + 22）**
—— 「两种格式交付的不是一个东西」这是第二次遇到（第一次 Phase 89）。

**② 分区的边界**正好落在数据上**时，`//` 和 `round()` 都会错，而且**只错一半**。**
把角按 60° 分成 6 组：24 边形的 **15° 间距整除 60°**，所以角**正落在边界上**，
`atan2` 对「标称 60°」的角回 **59.999999**（`//` 丢进下面一格），
而 Python 的 `round()` 是**银行家舍入**（`round(1.5) == 2`、`round(2.5) == 2`，边界角忽上忽下）。
实测读出 `[3,4,5,3,5,4]`，**而同一次检查里 18 边形那一半是全对的**（20° 间距碰不到边界）
—— **一个错是线索，两个都错才算错**。
**修法：先把值吸附到它自己的格**（`round(azim / (360/n)) % n`），再分类。吸附留 ~10° 余量，浮点是 ~1e-5。
**副作用是断言更强**：从「每格几个」升级成「第 g 组 = 环的 `3g..3g+2` 和大环的 `4g..4g+3`」。

### 0.21 【坑】「余量」「差值」「占比」的分母里，往往就坐着被测对象

电平、掩蔽、曲线比较这一类量，全是**两个东西相减或相除**，而**分母是选出来的**。
2026-10-06 我量「旋律比伴奏响多少」，减掉的是 `mix - lead_isolated` ——
而那个 `mix` **已经把 lead 混进去了**，于是减掉的不是伴奏，**是同一段旋律的第二份拷贝**，
读数偏高 **11.4 dB**（自称 +6.9，实测 -4.5）。

**「余量」这个词本身就替你做完了选择**（§0.18 第五张脸：一个词如果替你做了选择，
你读到的就不是测量 —— 在那份文件里词是「最外围」，在这里词是「伴奏」）。
**在一个已经含有被测对象的混合里，「其余的一切」不是一个可以减出来的集合。**

三条可复用的形态：

1. **差值** —— `A - B` 里的 `B` 必须**定义上**不含被测对象。这里就是 `with_lead(stems, 0, 0)`：
   装配对电平是**线性**的，所以它是**精确**的无旋律伴奏，不是近似。
2. **功率** —— 两个**分别**量的带功率之和 ≠ **和的**带功率（相关时差 **3 dB**）。
   要量一个信号的功率，就**先把那个信号加起来再量**。**「两半不相关」是你不该假设的那件事。**
3. **外推** —— 那个 +6.9 **不是猜的**：它算过、有一条 1× 到 8× 的扫表、读数单调、
   还落在判据那侧。**算过的和量过的在盘上逐字同形**，只在**下一次被质疑**时分开。
   **外推的结论必须当场标成外推。**

### 0.22 【坑】「把同名的根合并掉」既不必要、又不可逆 —— Roblox 允许**兄弟重名**

2026-10-06 一次「给客户端减负」的 park 把 `Workspace` ≈982 个根搬进
`ServerStorage.ParkedFacility_20261006`，过程中**把同名的根合并进一个**。两条都错了。

**① 合并从来就不需要。** Lua 里给 `Parent` 赋值**从不改名**（**只有 Studio 的 UI** 会加后缀），
所以 **109 个叫 `Model` 的根**、90 多个裸 `Part` 本来就并存。
「先合并再搬」把一次**可逆的搬运**变成一次**不可逆的破坏** —— 毁掉的是**分组**，
而分组**没有名字、没有属性、没有绑定**，于是事后**没有任何东西**能拿来复原它。
**要搬就整根搬，永远不要为了搬运去改世界的形状。**

**② 房间是靠「每一个根都在」撑住的。** 搬走 Workspace 的东西 = 改变世界，
而**这条规则早就写在 §0.12 第 3 条里**。用户的原话是
「**BRO你把控制室的墙壁地板和天花板都拆了**」。**那次 park 里唯一该问的问题是
「这些东西是不是在渲染」，而它写在我自己的文档里。**

**③ 复原只能重建，因为 undo 是盲写**（取舍 272）。`ChangeHistoryService` **不会告诉你它撤了什么**，
所以复盘靠**测量**：部件总数（**91,905**）、`Workspace.Consoles` 还解析得到、以及射线。
**「撤销」落在一个不可用的 undo 上时 = 一次带不变式的重建**（取舍 334）。

**④ 空掉一个 `Model` 之后 `GetPivot()` 还在。** 45 个被清空的壳各自留着世界坐标
（取舍 336）—— 这是**合并发生过**的证据，也是唯一能指出丢了什么的东西。
**但它是证据，不是数据**：一个「最近邻分配」能给出一个**看起来完全合理**的答案
（取舍 **340**），而这些 pivot 在控制室里只隔 2–15 stud。**没有 ground truth 的拆分 =
挑的数，不是量出来的数**（同 274）。**证据不足时交付「丢了什么」，不交付替代品。**

**⑤ 两条量法上的连带**：从 y=400 往下打的「地板射线」**打到的是天花板**
（取舍 337，§0.18 第五张脸）；**会话转录里的计数不是 ground truth**
（`uniq -c` 把每条结果算两遍，诊断那一趟也打过同样的行 —— `MainHallwaySegment(456)` 出现
8 次而真实合并 3 次，取舍 339）。**能拿来「找」，不能拿来「读」。**

### 0.23 【坑】`MeshContent.SourceType = Object` 的网格**活在创建它的那个进程里** —— 别处拿到的是**单位立方体**

`Content.fromObject(editableMesh)`（用 `EditableMesh` 造出来的 MeshPart）**不跨网络**。
同一个实例、同一句 `CreateEditableMeshAsync(part.MeshContent)`：**建它的那个进程**回
**9728 顶点 / 跨 `±46`**；**另一个进程**回 **1536 顶点 / 跨 `(0,0,0)..(1,1,1)`** ——
一个**单位立方体**（新建的 `CreateEditableMesh()` 是 **0 顶点**，所以 1536 是**替代品**、不是空），
渲染器把它画成**棋盘格占位**、尺寸按部件的包围盒。**操作员那句「进测试之后变成一个小方块」量的就是这个。**

三条连带，都是 **§0.2 换了张脸**：
**① `CreateEditableMesh()` 在给不了的进程里返回 `nil`，不抛错** ——
`pcall` 回 `ok = true, em = nil`，崩在**下一个消费者**身上（同 §0.15）。
**② 从 `execute_luau` 里做的「Play 客户端」诊断，问的不是游戏那个 VM** ——
**交付路径（`StarterPlayerScripts` 里的 `LocalScript`）必须自己跑过自己**。
让**游戏 VM** 说话的办法：它自己把结论写进 **`workspace` 上的一个 `StringValue`**，插件 VM 再读那个值。
**③ 「每帧改写多少顶点会丢网格」不是已证的机制** —— 我一度这么归因（当时确实看到棋盘格），
今天 `stride = 1` 与 `stride = 4` 各跑满 4 分钟都不复现。**没复现的那一半要写成没复现**（同 §0.21 第 3 条）。

细节取舍 **449/450/451/452**，上手 `docs/SNIPPETS.md` **§5.25**。

## 1. 项目概述

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

> **Phase 47..107 的逐段压缩摘要已移出本文件** → `docs/PHASES.md`（按 Phase 号快速回看的**压缩版**）。
> **权威全文在 `PROGRESS.md` / `DECISIONS.md` / `DECISIONS_2.md`。** 移出理由：那 1155 行占了本文件 67%，
> 而本文件每轮都进上下文 —— 违反 §0.0 那条「只留需要每轮看到的东西」。

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
