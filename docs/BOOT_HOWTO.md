# 开机采集器使用说明 — `TRG_original_boot.luau`

> 这份是**原版游戏**（placeId `17596243941`）开机屏的采集器，由你在 Solara V3 里
> `loadstring(game:HttpGet(...))` 注入。它**不是**这个工程里的代码，也不依赖
> `ReactorBackend` / `Config` / `Engine`。它只读实例状态。
>
> 它是**你原来那份脚本**（`C:\Users\andypeng1NB\AppData\Local\SolaraTab\Test.lua`，
> 159 行，md5 `b682bdc41e49ef57ae152eecb185c35a`）的优化版：**保留它的做法，去掉它的四个缺陷**。
> 逐条对照见 §1。

---

## 0. 一句话

**开机之前注入，按开机键，它从那一按开始记；12:00 PM（或你按 RightControl）封存。**

和采集器（`TRG_original_recorder.luau`）不同：那份记一整班，这份只记**开机那一屏**。

---

## 1. 它和你那份 `Test.lua` 的差别（逐条，带数字）

你那份的产物是 `Data/auxcollection/startup/ScreenChanges.txt`：
**1,162,737 行 / 179,788,590 字节 / 158 秒**。下面每一条都对着它量出来的。

| # | 你那份的缺陷（从你自己的源码和产物读出来的） | 这一份怎么处理 |
|---|---|---|
| a | `WatchProperties` 按 ClassName 挂，`Position`/`Size` 也在表里，于是 `…MonitorUI.GlitchEffect.GlitchFrame` 每帧都在写 → **99.4% 的行是这一个装饰的位移** | `GeometrySkip = {'.GlitchEffect'}`：**路径含这段的实例不挂几何属性**。位移/尺寸在源头就不产生，不是事后过滤。**但它照旧记 `Visible`**（见 §1.1） |
| b | `appendfile` 且从不先 `writefile` 复位 → **两次注入会串成一个文件**（这正是 Phase 66 里「文件顺序不是时间顺序」的来源） | 每个产物**第一次写是覆盖、之后才追加**；本地文件名带时间戳（`TRG/ScreenChanges_<stamp>.txt`） |
| c | 没有 `DescendantAdded` → **运行期克隆出来的开机帧永远看不见** | 挂 `Monitors.DescendantAdded`，运行期新建的实例立刻登记 |
| d | 没有传输层 → 你得手工搬 180 MB | POST 到 `http://127.0.0.1:8765/originalboot/…`（和监视器同一套 sink） |
| e | 没有体积上限（实测 **1.14 MB/s**） | 每键上限 2000 行、全局上限 24 MB、每 2 秒或 64 KB 冲一次 |
| f | 每个变化都调一次 `GetFullName()` | `GetFullName` 在**登记时**算一次，之后每行复用 |
| g | 属性表少了 `Image` / `ImageTransparency` / `TextTransparency` / 颜色 / `ZIndex` | 补进白名单 |
| h | 停止条件 `"12:00 AM"` 和班次开盘**撞车**（表盘开盘就是 12:00 AM），且**没有手动停止键** | 改成等 **11:59 AM → 12:00 PM 的交接**；`RightControl` 手动封存 |
| i | 没有自报死因 | `alive.txt` / `hello.txt` / `boot.txt` / `meta.txt` / `error.txt`（见 §4） |

### 1.1 追加上去的两个**代价**，写在这里而不是藏在注释里

1. **合并（coalescer）**：信号里只记账，**4 Hz 的 tick 才写行**。所以
   **在一个 tick 内改了又改回去的值，不会被记下来**。这是去掉 99.4% 噪音必须付的钱
   ——你原来那份是在**事件**里写的，所以它记得住，也所以它 1.16 M 行。
   （登记时会把当前值**播种**成基线，所以「一直是 false」的键不会在第一次 tick 冒出一行。）
2. **`.GlitchEffect` 这段路径的几何属性**一律不记。**只有几何**：它的
   `Visible` / `Image` / 颜色照记。这条粒度是 Phase 66 逼出来的——开机屏自己那 0.2%
   才是你要的，而它和那 99.4% 在**同一个文件、同一个 ClassName** 里，
   所以只能按**路径**分，不能按类型分。

---

## 2. 服务器（两个端口，缺一不可，和监视器一样）

```bash
# 终端 A —— 收数据的（8765）。脚本把字节 POST 到这里。
python _tools/receive.py --port 8765 --dir Data
#   产物落在 Data/originalboot/<…>（Prefix 就是 originalboot/）

# 终端 B —— 给脚本的（8766）。执行器从这里取脚本本体。
python -m http.server 8766 --bind 127.0.0.1 --directory _tools
```

---

## 3. 注入（**开机之前**，这是唯一有时序要求的步骤）

在 Solara V3 的执行器里，一行：

```lua
loadstring(game:HttpGet('http://127.0.0.1:8766/TRG_original_boot.luau'))()
```

**必须在按开机键之前注入。** 整个捕获的 `t=0` **就是那一按**（和 Phase 67 里
你那支 hook 钉住的同一个事件）。开机之后才注入 = 没有 `t=0`，前面那段让掉了。

**和监视器可以同时注入。** 两边没有全局变量冲突，产物路径不重叠
（`originalboot/` 对 `originalwatch/`）。**唯一撞的是热键**，见 §5。

**注入前核这三个数**（不要核时间）：

| | 值 |
|---|---|
| 字节 | **38609** |
| 行数 | **835** |
| md5 | **`243adb577f1442a069144f0bbb6df8f0`** |

> 这三个数比另外两份**更硬**：采集器/监视器是经 Studio 编辑器层搬进游戏的，
> 而这一份是你自己从 8766 上 `HttpGet` 下来的——**盘上就是这个字节**，
> 中间没有一层会改文本。所以 md5 对得上 = 注进去的就是我验过的那个文件。

---

## 4. 产物（都在 `Data/originalboot/`）

| 文件 | 什么时候出现 | 说什么 |
|---|---|---|
| `alive.txt` | 加载即写 | 它活着、选了哪条传输（`transport=http_request`），以及**加载后几秒内的自检** |
| `hello.txt` | 紧接其后 | 已布防、在等哪一按；`root_visible_at_inject=true/false` = **注入的那一刻 `Workspace.Monitors` 在不在**（回答「我是不是注入太早了」） |
| `boot.txt` | 按下开机键 | `t0=` 那一按的墙上时间。**这个文件在 = 按到了** |
| `ScreenChanges.txt` | 按下之后 | **正文**。行格式冻结（见 §7） |
| `notice.txt` | 视情况 | 只能说「办不到」的事，例如找不到 `TimeLabel`（午间封存失效，但要**说出来**而不是静默） |
| `suppressed.txt` | 有键被截断时 | **账本**：哪个 `路径\|属性` 写满 2000 行被切了、切在第几行、什么时候 |
| `meta.txt` | 封存时 | 封存原因（`noon` / `hotkey` / `ceiling` / `error`）、行数、字节、sink 与本地各发了多少、`dropped_chunks=` |

**读了 `meta.txt` 才有全部**：它一定在正文之后写（`flush()` 先跑），
所以「有 meta 就说明正文齐了」。

---

## 5. 热键 —— 和监视器**共用**两个键，这是有意的

| 键 | 这一份 | 监视器（`w61`） |
|---|---|---|
| `RightAlt` | **立刻冲一次缓冲** | 立刻推文件 |
| `RightControl` | **封存这一趟**（写 meta） | 停 |

两个键在两边**意思一样**（推/停），所以同时注入时按一下两边一起动，
这就是你要的。**`RightShift` 仍然只属于采集器**（`TRG_original_recorder.luau`），
这一份**不碰**它——测试台里有一条检查专门钉这件事
（`the recorder's seal key is not bound here`），而且有一条变异测试证明它**会变红**。

---

## 6. 它什么时候会自己停

| 原因（`meta.txt` 里 `reason=`） | 触发 |
|---|---|
| `noon` | 表盘读到 **`12:00 PM`**（`Monitors.QuotaControlRoomMonitor.…MainMonitorFrame.TimeFrame.TimeLabel`） |
| `wrap` | 表盘**倒退**回 `12:00 AM`（已经离开过开盘值之后） |
| `ceiling` | 全文到了 24 MB |
| `error` | 结构性问题（没有 `Workspace.Monitors`、没有那个 `ClickDetector`） |
| `hotkey` | 你按了 `RightControl` |

注意 **开盘的 `12:00 AM` 不会结束这一趟**——你原来那份会，因为两条规则撞在同一串文本上。
这一份要的是 **11:59 AM → 12:00 PM 的正午交接**。

---

## 7. 行格式 —— **冻结的，别改**

```
Time:[HH:MM:SS]<-O:[完整实例路径]<-C:[属性名]<-V:[新值]
```

**两端都锚定**（`^Time:\[…\]$`）。这不是风格问题：`_tools/_attic/scratch/` 里
**七个旧分析器** 编译的是**逐字节相同的**这一个正则，而且**行尾加字段不是向后兼容的**
——`V` 那组是贪婪的 `(.*)`，任何追加的字段都会被吞进 `V` 里，正是行尾的 `$` 在告诉读者「这行完了」。

所以这一份**新的东西一行都不往这个格式里塞**：要么是新的一行、**以 `#` 开头**
（读者全都跳过），要么是新文件。

这条不是靠我记着的：`_tools/verify_boot_capture.py` 会在回归里**从七个分析器自己的源码里
把这个正则读出来**，并要求它们**七个完全一致**，再拿它逐行验捕获。
重抄一份在这里的副本会在读者改掉之后**继续绿**，那正是它要抓的东西。

---

## 8. 验证状态（**哪些验了、哪些没验，分开说**）

**验过的（本机，不进游戏）：**

- `bash _tools/run_tests.sh` **rc=0**，里面新加的三道门全绿：
  - 整文件 **Lua 5.1 解析**（不是 Luau 编译）；
  - `boot_harness.luau` **五个场景**：`default` 29 PASS / `nobutton` 6 / `noroot` 6 /
    `nosink` 30 + 1 SKIP / `rightcontrol` 28，**0 FAIL**；
  - `verify_boot_capture.py`：三个捕获共 **6015 行，0 行不合法**，
    用的正则是**从七个读者源码里读出来的**（顺便把「七个一致」变成一条会失败的检查）；
  - `selftest_boot.py`：**8 个变异，8 个都被抓住**（去掉合并、清空几何过滤、
    取消播种、拆掉 `DescendantAdded`、抬高预算、绑 `RightShift`、让正午不封存、
    把表头写到世界检查之前）。
- 测试台自己**修掉的四个 bug** 值得一提，因为它们都是「测试在说谎」那一类：
  `nosink` 场景**声明了却从来没真拒过**（四条红线对着一个一直在工作的 sink）；
  `noroot` 断言的是「加载时就报死」，而文件的契约是「按下才解析世界」；
  `dump` 里 `string.gsub` 的**第二个返回值被写进了文件**变成一行 `0`；
  以及测试台自己的缓冲相位依赖（Phase 64 那个硬币）。

**没验的（必须说清楚）：**

- **它一次都没在原版游戏里跑过。** 上面全部是**本机**证据。
- 因此以下三条**是设计意图而不是观测**：`GeometrySkip` 的粒度够不够
  （会不会把开机屏自己某段几何也吃掉）、每键 2000 行的预算切在不在正确的位置、
  开机峰值下 `MaxPendingLines = 20000` 够不够。**跑完第一件事是读 `suppressed.txt` 和
  `meta.txt` 的 `dropped_chunks=`**——如果非零，说明上面的数和真实峰值不匹配。
- 原版**控制室/腔室/音频**不在它的范围里，那是监视器（`TRG_original_watch.luau`）的活。
  这一份只看 `Workspace.Monitors`（**和你自己那份的根一模一样**：
  `workspace:FindFirstChild("Monitors")`）。

---

## 9. 出问题时先看哪

| 症状 | 先看 |
|---|---|
| 什么都没有 | `alive.txt` 有没有？没有 = 注入就没跑起来（或者 `HttpGet` 失败）。有 `alive.txt` 没 `hello.txt` = 加载后崩在模块体里 |
| 有 `hello.txt`，按了键没反应 | `boot.txt` 在不在。不在 = **没按到那一个 `ClickDetector`**（路径写死在 §1 的 `BootButtonPath`） |
| 文件很小、很多键只出现几次 | `suppressed.txt` 的账本 + `meta.txt` 的 `dropped_chunks=` |
| 内容不完整 | `meta.txt` 的 `reason=`：`ceiling` 就是撞了 24 MB |
| 行数暴涨 | 有**第二个**每帧变的东西没进 `GeometrySkip`。读 `ScreenChanges.txt` 里出现次数最多的 `O:`，把它加进 `GeometrySkip`（**先量再改，别猜**） |
