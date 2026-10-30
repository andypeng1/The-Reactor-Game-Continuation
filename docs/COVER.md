# COVER —— 那块 1:1 的封面怎么做的（Phase 132 建；主体 133 换掉；要素 134 砍到四样）

> **Phase 149 起这份文件里有三张图**：1:1 的封面（§1–§6）、**16:9 的游戏页面宣传图**
> （**§7**，`cover/page.html` → `cover/THE_REACTOR_GAME_page.png`）和
> **The Reactor Game - Continuation 的图标**（**§8**，`cover/continuation.html` →
> `cover/THE_REACTOR_GAME_continuation_icon.png`）。三张共用一份语言、
> 一份渲染器和大部分仪器，**版面判据是三份**（`cover_judge.js` / `page_judge.js` /
> `continuation_judge.js`）—— 规则的对象换了，问题不能换。

> 一句话：`cover/index.html` 是一张 **1080×1080 的静止画**，
> 由 `_tools/intro_render.js`（和 `intro` / `promo` **共用**的那台渲染器）拍成一个 PNG，
> 再由 `_tools/cover_judge.js`（**没有浏览器**）判它的版面，
> 由 `_tools/cover_layers.sh`（**逐像素**）保证它的每一层装饰真的在画上。

**画上现在只有四样东西**：外框 / 六边 + 厂标 / 标题 + `AIREMAKE` 徽章 / 页脚。
2026-10-15 操作员原话「**要素太多了，不需要这么复杂**」，砍掉的列在 §5。

---

## 1. 文件都在哪

| 文件 | 是什么 |
|---|---|
| `cover/index.html` | **画本身**。1080×1080，一个 `render(t)` 决定它长什么样（`t` 被忽略） |
| `cover/THE_REACTOR_GAME_cover.png` | **成品**。1080×1080，**496559 B / md5 `5bd615a7…`**。Phase 134 连渲 12 次**字节完全一致**（Phase 132/133 那阵子是 10/2 两个形态、只差 1 个像素，见 §4 末） |
| `_tools/intro_render.js` | 渲染器（共用）。封面用到了它的 `--w` `--h` `--shot` 三个参数 |
| `_tools/cover_judge.js` | **判定**（A0..A10，**没有 A8**，见 §3）。只读一份 JSON，不碰浏览器 |
| `_tools/cover_layers.sh` | **逐层关掉再渲染**，比像素：哪一层其实没画上（现在是四层） |
| `_tools/cover_layer_probe.py` | 上面那个脚本的比对器；顺带打素材极性表 |
| `_tools/cover_mark_check.py` | 六边里那枚厂标**是不是这张素材**（对着素材自己的 alpha；吐一张阈值扫描表） |
| `cover_judge.js --selftest` 用的报告 | `_tools/_attic/scratch/cover_report.txt`（gitignore） |

**没有第二条运输线。** 封面和两部片子服从**同一份契约**：一个固定的设计空间 `#stage`、
一个全局的 `render(t)`、一个按视口缩放的 `fit()`。所以它不需要自己的渲染器 ——
只是比片子多一个 `--shot`，因为**静止页面有一个要交付的帧**，而默认落点
`_attic/_frames` 是 gitignore 的垃圾堆。

---

## 2. 四条命令

```bash
# 1) 拍成品帧，同时把版面读数倒出来
D:/nodejs/node _tools/intro_render.js --page cover/index.html --at 0 \
    --w 1080 --h 1080 --shot cover/THE_REACTOR_GAME_cover.png \
    --eval 'layoutReport()' > _tools/_attic/scratch/cover_report.txt

# 2) 判（exit 1 = 有红）
D:/nodejs/node _tools/cover_judge.js _tools/_attic/scratch/cover_report.txt
D:/nodejs/node _tools/cover_judge.js --selftest _tools/_attic/scratch/cover_report.txt

# 3) 每一层装饰到底改了几个像素（会重拍一次成品帧）
bash _tools/cover_layers.sh

# 4) 六边里那枚厂标是不是这张素材（对着素材自己的 alpha；吐扫描表）
python -X utf8 _tools/cover_mark_check.py        # 默认 t=120，也可以给 t
```

`--w 1080 --h 1080` **不是可选的**：视口必须钉成页面自己的舞台，否则 `fit()` 会把
方舞台缩进一个 1920×1080 的视口、截图上带黑边，**而报告里每一个坐标都是错的空间里的**。
这条是检查器的第一句（A0），因为它是"后面十条全都在量错的东西"的那种错。

---

## 3. 版面规则（A0..A10，缺 A8）

判定只读 `layoutReport()` 吐出来的 JSON。**10 ok / 0 failed**，**突变 12/12**。

| | 断言 | 读数（Phase 134） |
|---|---|---|
| A0 | 设计空间是 1080×1080 且填满视口 | stage 1080×1080 / viewport 1080×1080 |
| A1 | **非真空**：四样东西**按名字**在场且**有尺寸** | title + badge + 两行页脚都在；六边宽 499px、厂标 420px |
| A2 | 每个文字块都在外框以内 | 4 blocks inside [26..1054] |
| A3 | 没有两块撞上，**且**最近的一对不到 40px | 0 colliding；最近 14.00px |
| A4 | 标题放得下内宽、让开下面的细线 | w=901.0 of 1036，bottom 870 vs rule 906 |
| A5 | 六边主体在外框与标题**自己的盒子**之间 | x[290.58..789.41] y[116..692]（下界 = 标题 top−6 = 755.00） |
| A6 | 面板盒子比例正好 `2/(2cos30)` | 1.154706 vs 1.154701 |
| A7 | CSS 百分比六边形 == SVG 像素六边形 | 逐顶点最差 0.012 px |
| A9 | 每一层装饰都声明极性，且 `filter` 与声明一致 | 4 层（white+gradient），全对上 |
| A10 | 六边里的厂标不捅出六边的边线 | 到最近那条边还剩 39.4 px |

**A1 和 A3 是"非真空"那一半**（§0.20：空集合会说两次谎）："没有两块相撞"在只画了
两块的页面上一文不值，所以 A1 先要求**有东西可撞**，A3 再要求"最近的一对**确实很近**"。
**A1 在 Phase 134 换了形状**：原来是数数（"至少 12 个文字块、4 个格子"），
现在**按名字点这四样**。页面越空，这条越该重 —— 数数在四样东西的版面上只会变成一个
比真实需求更小的门槛（取舍 **572**）。

**两条规则跟着对象一起退场**（§0.31：宾语没了，留着就是恒红/噪音，两种都是噪音）：

- **A8 退场** —— "读数条每一格的值都在自己那格里"，而四格读数条本身被砍了。
- **A9 里那条"黑、白两种极性都要在场"的自检退场** —— 页面上仅有的两处黑素材
  （标题斜纹带、底边警示带）被砍了，`black` 那一半没有对象，那条自检**只能恒红**。
  A9 本体留下：`white ⟺ 不许 invert`、`gradient ⟺ 更不许 invert`，
  外加"至少要有一层声明了真的素材极性"，两句都还亮得起来（突变里各有一条打它）。

**突变 12/12**，每一条至少点亮它瞄准的那一条（`--selftest`）。最真实的一条不是编的：
**忘了 `--w/--h`**，于是舞台被信箱化、报告里全是错空间的坐标。

---

## 4. 四个装饰层

`#coreMark` `#smMark` `#scan` `#vig` 是四个**靠 opacity / 混合模式活着**的层：
它们没有文字、不落在任何几何断言上。Phase 134 量的（每一层关掉再渲染，比像素）：

| 层 | 素材 | 关掉 vs 开着 |
|---|---|---|
| `#coreMark` | `sm-core.png`（**白** 255，无 invert） | 188752 px，Δ228（含 `drop-shadow` 撑出去的那圈） |
| `#smMark` | `sm-logo.png`（**白** 228，**没有** invert） | 542 px，Δ57 |
| `#scan` / `#vig` | 纯 CSS | 147910 px，Δ48 / 663604 px，Δ122 |

**四层**每一个都改变像素，`ok: 0 layer(s) changed nothing`。

**为什么这条跑道存在**（Phase 132 的真实缺陷，层已经不在页面上，纪律留下）：
一版封面里**五层装饰有四层是坏的，而十条规则里的九条全绿**。两种机制，都不报错：

| 层（Phase 132） | 旧写法 | 旧 vs 关掉 |
|---|---|---|
| `#titleBand` / `#hazard` | `stripes.png`（**黑**）+ `mix-blend-mode:screen`，无 invert | **0 px，Δ0 / Δ2** |
| `#hexes` / `#smMark` | `nested-hex.png`（**白** 235）/ `sm-logo.png`（**白** 228）+ `invert(1)` | 8480 px，**Δ3**（修好 Δ24）/ 138 px，**Δ35**（修好 Δ54） |

**`screen` 对黑是恒等**（`screen(底,0)=底`，所以黑素材喂给 screen 的层**逐像素为 0**）；
**`invert` 作用在近白线稿上是把它转成黑**（层还在，振幅塌到 1%–14%）。
"层不在"和"层在但读不出来"是**两个失败**，混成一句就两件都没说清（取舍 565）。

**`#coreMark` 另外还对着素材自己的 alpha 量过一次** —— 不满足于"关掉有变化"，因为
**一个平铺的白色方块也能让那一层全绿**。命令 `python -X utf8 _tools/cover_mark_check.py`：
把素材自己的 alpha 缩进页面给它的那个 420×420 盒子，再给成品帧取阈值，**两个方向都数**。
输出**不是一对数、是一张扫描表**，因为**在这一页上没有干净的一刀**：

```
  t     bright      tp      fp      fn   precision   recall
   60     49906   44663    5243       0     0.8949    1.0000
   80     46656   44663    1993       0     0.9573    1.0000
  100     45854   44659    1195       4     0.9739    0.9999
  120     45068   44555     513     108     0.9886    0.9976
  150     43958   43950       8     713     0.9998    0.9840
  180     42372   42372       0    2291     1.0000    0.9487
  200     31387   31387       0   13276     1.0000    0.7028
  220     20476   20476       0   24187     1.0000    0.4585
  240         0       0       0   44663        nan    0.0000
```

**为什么没有干净的一刀**：厂标的墨（1% 分位 **142**、中位 217）和**盒子里不是墨的东西**
（最亮的那个非墨像素 **159**）**在亮度上重叠** —— 盒子里那圈东西是六边自己的实线、
以及厂标自己的投影。所以 `precision` 在这一页上的分母里坐着**不是被测对象的东西**
（§0.21 那一族的浅版）。**能站得住的两句**：

1. **整份墨都在画上**：t≤80 时 **44663 个墨像素里有 44663 个是亮的**。
   这一句把"画的是这张素材"和"画了个亮的方块"分开了。
2. **最外圈也是满的**：按半径分档（t=120），**r 0.0 到 r 1.0 每一档都是 99.7%–100%**。
   Phase 133 那一版在这最后一档只有 **80.7%**，而**这一轮它回到 99.7%**（取舍 **573**）。

> **那 80.7% 的原因，这一轮被拆开重量了，而老解释的形状是错的。**
> 老写法（Phase 133 本文件 §4、取舍 570，以及 `cover_mark_check.py` 的 docstring）
> 说的是"**两条 HUD 读数正坐在那个外环上**"。把它拆开量（6×6 暗墨占据格 + 回头读
> Phase 133 的 CSS）之后：
>
> | 读数 | Phase 133 | Phase 134 |
> |---|---|---|
> | 盒子里墨的亮度 p1 / 中位 | **95 / 189** | **142 / 217** |
> | 最外一档（r 0.9–1.0，15478 个墨像素）亮着的比例 | **80.7%** | **99.7%** |
> | 墨的集合 | 44663 px | 44663 px（**逐集合不变** —— 盒子、`contain`、素材都没动） |
>
> 暗墨**不是绕一圈的**：它落在**下缘一条带**（盒内 y 350..420、x 70..350）、
> 上缘一条轻的（y 0..70、x 70..350），而圆环 **3 点 / 9 点方向是干净的**。
> 下缘那条带正是居中的那行 `CHAMBER ATMOSPHERE > SEALED`；而当时的 CSS 里
> **`.hud` / `.hudv` 各自都带黑色 `text-shadow`**（8 px / 10 px），
> **`#hexTint` 自己还带一条 180° 的 `linear-gradient`（顶 42% 黑 → 中透明 → 底 55% 黑）**，
> `#coreMark` 的 opacity 当时是 **.88**（现在 .92）。**三样同向，各占多少没拆开量。**
> 所以能写的只有两句：**"四周压暗"的形状是错的**（暗在上下两条带，不在四周）；
> **谁贡献了多少没量**（§0.21 第 3 条：算过的和量过的在盘上逐字同形）。
> **规矩**：读数偏低而你已经有一个**说得通**的解释时，先问"是不是**别人的东西正压在上面**"——
> "被别人遮挡"和"自己变暗"在盘上长得一样，而**遮挡会随别人的东西一起消失**。

> **更早的那一对（precision 0.9972 / recall 0.7371）作废，不许再用。**
> 它来自一次**没有记下参数**的临时量法，换成上面这个仪器之后**复现不出来**（取舍 **570**）。
> 现在参数写在仪器里、也打在输出上（盒子位置、阈值、alpha 门槛、整张扫描表）——
> **复现不出来的数不是懒，是它本来就是一次"挑出来的数"，不是量出来的数**（同 §0.22 ⑤）。
> 顺带：第一版仪器把素材 `convert("L")`，而它是 **LA**、**每个像素的 RGB 都是白的** ——
> 于是"墨"变成整个盒子（precision 1.0000 / recall 0.27）。**那个读数不是错的，
> 它是另一个问题的答案**：先量"画在哪一个通道"，再写比对器。

**A9 只抓得住样式那一半。** 素材的极性量不到（`file://` 下 canvas 读背景图会被污染），
所以每一层用 `data-art` **声明**极性，A9 断言"声明和 `filter` 一致"。
**量出极性的命令写在声明的注释里** —— 这条断言检的是"声明自洽"，而声明的出处可复查。

**字节稳定这件事，Phase 134 变成了一个正结果**：连渲 12 次，**12/12 逐字节相同**
（496559 B）。Phase 132/133 那阵子它会分成两个形态（10/2）、差 1 个像素
（六边右边缘抗锯齿那一列）。**机制没有被证明过** —— 这一轮只是它不再出现，
所以判据仍然是**像素不是哈希**：`_tools/cover_layers.sh` 自己比的就是像素。

---

## 5. 画上有什么，每一项的出处

| 内容 | 出处 |
|---|---|
| 配色（void / ready / amber / plasma 四档） | `Config.Visual`，逐字抄自 `intro/index.html` 的 `:root`。**一个新颜色都不许发明** |
| `THE REACTOR GAME` | `intro/` 与 `promo/` 的品牌字 |
| `AIREMAKE`（琥珀徽章） | 见 `QUESTIONS.md` R7（**这一条留给你改**） |
| 六边里的厂标 | `intro/assets/sm-core.png`（片头留下的副本；**页脚 `#smMark` 用的是同一份资产**） |
| 页脚两行 + 小厂标 | 同上（`sm-logo.png`；**原 pack 被 gitignore 排除**） |

**Phase 133：六边里原来那张实拍被换掉了。** 操作员 2026-10-15 原话
「**好吧，不用实拍图片**」—— 指的是上一轮汇报里那句「中间一个六边形框，里面塞的是
我们自己游戏里实拍的那张点火照」。换成**厂标**（`sm-core.png`：外圈 + 两个同心六边 +
三根辐条），一张线稿、不是照片，而且它本来就在 `intro/assets/*` 清单里 ——
**所以这一页现在一次都不再引用 `promo/` 下面任何东西**。
（`promo/` 里那些实拍仍然属于片子和 store page，**没有删、没有动**。）

**Phase 134：砍掉的是这些**（原话「要素太多了，不需要这么复杂」）——
顶栏三行小字与顶部细线、压在六边上的两条 HUD 读数（`9420 °F` / `5000 CHAMBER PSI`）、
副题与 specs 两行、四格读数条（`NODE / CORE / QUOTA / CONTROL RODS`）、标题上那条斜纹带、
背景的透视网格与六边纹、堆芯后面那团光晕、底边的警示斜纹、六边的两圈外虚线与六个顶点
刻线、CRT 三条里的噪点层。**它们只活在 git 历史里**，不在这份文件里重建。
留下来的四样是：外框、六边 + 厂标、标题 + 徽章、页脚。

**许可边界**：只引用**已经在版控里**的文件，不新拷、不新增暴露面。复制禁止（取舍 562）
—— 复制会造出第二份可以漂移的真相，"引用"不会。

---

## 6. 验了 / 没验

**验了：** 版面 A0..A10 **十条**全绿（10 ok / 0 failed）；**突变 12/12**；
**连渲 12 次逐字节相同**（判据仍是像素不是哈希，§4 末）；
四层装饰每层都改变像素，`0 layer(s) changed nothing`；
`#coreMark` 另对着素材自己的 alpha 量过一次（§4 那张**扫描表**：整份墨都在画上、
最外那一档 99.7%）；**读图一次**（`glm-4.5v`）—— 它读出的是"四样东西、无重叠、
无裁切、**稀疏而平衡**"，与版面读数一致（§0.14b：图证明"看起来对"，读数证明"真的是那个值"）。

**没验（不许外推）：**

- **全程没进 Studio、没进 Play、没上传过任何地方**（§0.16 边界不变）。纯磁盘产物。
- **没有做"砍之前 / 砍之后并排"读图**，也没有请人评过哪一版好看。这一轮能验的只是
  "四样东西都在、位置都对、每一层都真的画上去了"。**"砍完更好看"是操作员的判断，
  不是测量**（同 Phase 133 那条）。
- **缩略图这一版没重看**：Phase 133 量过 480/256（大字读得出、六边+厂标认得出、
  小字读不出），而这一版**删掉了那些小字**，所以那次读数对这一版**只是不再适用，
  不是被推翻**。商店页真会怎么裁/怎么压，从来没进过测量。
- 读图用的是兜底模型，**它是"看起来对不对"的证人，不是尺子** ——
  它的每一句判断都要和读数对上才算数（§0.14b）。它在小尺寸下会**编字**（Phase 133
  实测：报出过 `CZB2-8A`、`CAUTION`、`0224 W` 这些页面里根本不存在的字符串），
  所以它的**负**结论可用、**具体字符串**不可用。

---

## 7. 16:9 的游戏页面图（Phase 144，2026-10-18/19）

> 操作员贴了 Roblox「Game details」页的截图：图标那格写着「**这个是游戏图标，我已经上传了
> （你做的）**」，空的背景宣传图那格写着「**这个是游戏主界面的那种背景宣传图 / 还没有做，
> 交给你了**」。

| 文件 | 是什么 |
|---|---|
| `cover/page.html` | **画本身**。1920×1080，同一个 `render(t)` 契约（`t` 被忽略） |
| `cover/THE_REACTOR_GAME_page.png` | **成品**。1920×1080，**640006 B / md5 `baec1380…`** |
| `_tools/page_judge.js` | **判定**（W0..W10，**没有缺号**）。只读一份 JSON，不碰浏览器 |
| `cover_layers.sh` / `cover_layer_probe.py` | 同一个逐层像素检查，用环境变量指到这一页（见下） |
| `cover_mark_check.py` | 同一个厂标检查，`SHOT/BOX/BOX_X/BOX_Y` 指到这一页的 430 px 盒子 |

**它不是把 1080 方图居中塞进 1920。** 那样左右各留 420 px 黑边，放进 Roblox 的缩略图
就是一页**没做完的图**。共享的是**语言**，不是版面：

| 共享 | 变了 |
|---|---|
| 四样东西：外框 / 六边 + 厂标 / 标题 + `AIREMAKE` 徽章 / 页脚 | 六边**左置**、字**右置**（方画面里字只能在六边下面） |
| 调色板四档（void / ready / amber / plasma），一个新颜色都没发明 | 外框内缩 22 → **26**；页脚边距 44 → **56** |
| 素材 `sm-core.png` / `sm-logo.png`（一个字节都没新拷） | 标题**两行**、字号 96 → **116**（见下） |
| `#stage` 固定像素 + 全局 `render(t)` + `layoutReport()` 分工 | — |
| 装饰层四层（coreMark / smMark / scan / vig）、同一批 `data-art` 声明 | — |

### 标题为什么是两行，为什么判据量行距不量字号

右边那一列只有 **864 px** 宽（`1030..1894`）。一行 `THE REACTOR GAME` 在这台机器上
（`Arial Narrow` 不在，落到 `Impact` 一族）116 px 要 **1088 px**，装不下；缩到 92 px
装得下，但在 1/5 的缩略图上只剩一行细字。**两行 116 px** 每行都撑满，缩略图上还读得出。
代价是锁印和封面不同形 —— 这是**排版决定**，不是测量结论（取舍 **624**）。

> **【2026-10-31 更正】** 上面那句「`Arial Narrow` 不在」**归因错了**（读数是对的）。
> Phase 149 把字体栈**量**了一遍：同字号同字距的 `THE REACTOR GAME` 在 116 px 下，
> **Arial Narrow 1088.7** / Impact 976.4 / Franklin Gothic Medium 1127.9 / sans-serif 1196.6
> —— 那天量到的右边缘 **1088.55** 正是 Arial Narrow 的宽度，所以那一版画的就是 Arial Narrow。
> **两行这个决定不受影响**：四个候选里最窄的 Impact 也要 976 > 864。
> 量法：同一串字在每个候选家族里各量一次宽度，没装的家族会和 fallback 给出**同一个数**。
> 见 §8 的 `font.probe`、`PROGRESS.md` Phase 149、取舍 **648**、CLAUDE.md §0.42。

判定因此量的是**行距**（`titleLines[1].top - titleLines[0].top` = **110.19 px**），
因为缩略图上读者拿到的是这个数（1/5 → **22.04 px**），不是 CSS 里的字号。
读数行把这个折算数直接打出来。

### 五条命令

```bash
# 1) 拍成品帧 + 倒出版面读数（--w/--h 必须钉成 1920x1080，理由同 §2）
D:/nodejs/node _tools/intro_render.js --page cover/page.html --at 0 \
    --w 1920 --h 1080 --shot cover/THE_REACTOR_GAME_page.png \
    --eval 'layoutReport()' > _tools/_attic/scratch/page_report.txt

# 2) 判（exit 1 = 有红）与自检（17 条突变）
D:/nodejs/node _tools/page_judge.js _tools/_attic/scratch/page_report.txt
D:/nodejs/node _tools/page_judge.js --selftest _tools/_attic/scratch/page_report.txt

# 3) 四层装饰逐层关掉再比像素（会重拍一次成品帧）
PAGE=cover/page.html W=1920 H=1080 TAG=page \
SHOT=cover/THE_REACTOR_GAME_page.png bash _tools/cover_layers.sh

# 4) 六边里那枚厂标是不是这张素材
SHOT=cover/THE_REACTOR_GAME_page.png BOX=430 BOX_X=425 BOX_Y=325 \
python -X utf8 _tools/cover_mark_check.py
```

**共用仪器是用环境变量指过去的，不是复制一份新的**（取舍 **623**）。复制会让两台仪器
慢慢分开，最后文档引用一台、运行用的是另一台。默认值一律是封面那一套，
所以 Phase 144 之前写进文档的每一条命令**仍然是原来的意思**；改完当场跑了一遍封面，
**逐字节相同**（`5bd615a7…` / 496559 B，四层计数 188752/542/147910/663604 一个没变）。

### 版面规则（W0..W10）

判定只读 `layoutReport()` 的 JSON。**11 ok / 0 failed**，**突变 17/17**。

| 号 | 断言 | 这一页上的读数 |
|---|---|---|
| W0 | 设计空间是 1920×1080 且填满视口 | stage 1920×1080 / viewport 1920×1080 |
| W1 | 四样东西在场且有尺寸（**按名字点**，不数数） | 六边宽 554 px、厂标 430 px |
| W2 | 每一块字都在框内 | 4 块，全部在 `[30..1890]×[30..1050]` |
| W3 | 没有两块字相撞，**且有一对靠得够近**（近失报告 15.00 px） | 0 相撞 |
| W4 | 标题是**两行**、每行都在右框内、行距 ≥100 px、压在线上面 | 最宽 1767.4 / 限 1890；行距 110.19；底 670.19 < 线 704 |
| W5 | 六边在字的**左边**且留余量、在框内 | 六边右沿 917.1 < 字列左沿 1030 |
| W6 | 面板盒是尖顶六边的比例 2/(2cos30) | 1.154714 vs 1.154701 |
| W7 | CSS 的裁切与 SVG 的实线是**同一个六边形** | 逐顶点最大差 0.017 px |
| W8 | 每层装饰声明素材极性且 `filter` 与声明一致；没有 `opacity 0` | 4 层（white+gradient） |
| W9 | 厂标不捅出六边的六条边线（有符号距离 ≥8 px） | 最紧 #1 边剩 **62.1 px** |
| W10 | 六边**垂直居中**（±8 px）且细线在标题下方 20..90 px | 中心 540.0；线在下方 33.8 px |

**W5 是封面的 A5 换了一根轴**：封面的六边被"上面是框、下面是标题"夹住，
这一页它被"右边是字列"夹住。直接拿 A5 改个名字会变成一条**看起来一样、量的不是一件事**的规则。

**W4 有两条互相独立的牙**：一条突变只动 `titleLines`（行盒子），另一条动整个文字块 ——
否则"每行都在框内"这一句的牙从来没被单独证明过（DECISIONS_2 **592** 的同族）。

### 验了 / 没验

**验了：**
- 版面 **11 ok / 0 failed**；**突变 17/17**（每条至少红一条规则；两条各红两条）。
- **两次独立渲染逐字节相同**（`baec1380…`），像素差 0 —— 但判据仍然是像素不是哈希。
- 四层装饰：`coreMark 195354 px / Δ227`、`smMark 543 / Δ61`、`scan 203788 / Δ48`、
  `vig 1112794 / Δ119`，`0 layer(s) changed nothing`。
- 厂标**就是这张素材**：`t≤80` 时 **46656 个墨像素全部亮**（recall 1.0000），
  `t=120` 时每一档半径 **99.7%–100%**。这一页的墨/非墨亮度**不重叠**（墨最暗 141，
  非墨最亮 163 —— 比封面好一点，但仍然不是干净的一刀）。
- **读图两次**：整图（四样都在、无重叠、无裁切、徽章与标题是一个视觉单元）；
  384×216 缩略图（`THE REACTOR` / `GAME` **两行都读得出**；`AIREMAKE` 徽章在 1/5 下
  **读不出**，模型把它编成了 `PRESENTS` —— 这正是它"小尺寸下会编字"的老毛病，
  所以那个字符串**不是读数**）。

**没验（不许外推）：**
- **没上传过任何地方。** 上传要 API key（`asset:write` + creator id，两个都没设），
  所以这张图是**他自己拖进 Roblox 的**。
- **Roblox 侧怎么裁、怎么压、放在哪个槽**：没测过。1920×1080 是缩略图的标准尺寸，
  但这不等于他那个槽用的就是这一档；**也没有拿真实页面截一张对照**。
- **"两行比一行好看"是判断，不是测量。** 能验的是四样都在、位置都对、每层都画上去了。
- 缩略图只看了 384×216 一档；640×360 拍了但没读。



## 8. The Reactor Game - Continuation 的图标（Phase 149，2026-10-31）

> 操作员原话：「帮我设计个The Reactor Game - Continuation的图标（1：1的）
> 然后还是别太复杂，要体现Continuation」

**这张图说的是：同一个六边，但它不闭合 —— 缺口那一端走出一枚箭头。**
闭合的六边说「一座建好的设施」，缺口 + 顺着圈走出来的箭头说「它还在走」。
中心的实心青六边是**芯**（没有它，缺口圆环 + 箭头读作洗衣机的「再洗一次」）。

| 文件 | 是什么 |
|---|---|
| `cover/continuation.html` | **画本身**。1024×1024，同一个 `render(t)` 契约（`t` 被忽略） |
| `cover/THE_REACTOR_GAME_continuation_icon.png` | **母版**。1024×1024，**606769 B / md5 `a0baba54…`**，同一次机器状态内 **9/9** 逐字节相同（跨状态见 8.5） |
| `cover/THE_REACTOR_GAME_continuation_icon_512.png` | **上传件**。512×512，**153156 B / md5 `72a5987e…`**，母版的 LANCZOS 降采样（`optimize=True`） |
| `_tools/continuation_judge.js` | **判定**（C0..C11）。只读一份 JSON，不碰浏览器；`--selftest` 24 条突变 |

> **【2026-10-31 更正，Phase 150】** 上面那一节记的是 Phase 149 那一版的**六边**图标，
> 数字是那一版的（母版 **606769 B / `a0baba54…`**、上传件 **153156 B / `72a5987e…`**、
> 6 个部件 72883 / 8981 / …）。同一天下午操作员说「有点奇怪啊改一下，而且是trg的
> continuation，你TRG也要有一定体现」，于是**主体整个换掉**：现在画的是游戏自己的厂标
> `intro/assets/sm-core.png`，六边、芯、`loop`/`coreDot` 两个部件都不在了。
> **现行数字见 §8.7**；本节原文保留（当时确实那么写）。§8.4（字体）、§8.5（渲染确定性）
> 两条**不受影响**，Phase 150 复量过同一个结论。

### 8.1 图上只有三样东西

外框 / 六边 + 缺口箭头 + 芯 / 一行大字 `CONTINUATION` + 一行小字 `THE REACTOR GAME`。
**没有徽章、没有页脚、没有厂标** —— 封面的四样去掉两样，主体换成这个项目自己的记号。
四个几何常数是唯一的来源（`HEX_R 245`、`GAP_A .74`、`GAP_B .32`、`HEAD_LEN 54`），
HTML 里一条 path 都没手写；`layoutReport()` 把写进 DOM 的 `points` 读回来
再和解析值比一次（C6：最差 0.004 px）。

### 8.2 规则

| | 断言 | 读数 |
|---|---|---|
| C0 | 设计空间 1024×1024 且填满视口 | stage 1024 / viewport 1024 |
| C1 | **非真空**：两行字 + 三个部件**按名字**在场 | 缺口 102.9 px / 头 54 px / 芯 r 44 |
| C2 | 每个文字块都在外框以内 | 2 blocks inside [24..1000] |
| C3 | 没有两块撞上，**且**最近的一对不到 40 px | 0 colliding；最近 31.00 px |
| C4 | 大字放得下内宽、在 1/5 上还读得出 | 814.2 / 968；字高 134 px → 26.80 px at 1/5 |
| C5 | 主体在框内**且**给大字留出 24 px | 离大字 42.0 px |
| C6 | 画出来的圈 == 解析六边 | 逐角最差 0.004 px |
| C7 | **圈是开着的**：缺口有界、箭头在缺口里、箭头在那条边线上 | 缺 42.0% R；tip-to-start 48.9 px；离线 0 px |
| C8 | **箭头顺着圈走**、尺寸读得出 | 点积 1.0；54 × 76 |
| C9 | 主体 / 大字 / 小字一条竖轴 | 512 / 512.00 / 511.99 |
| C10 | 每层装饰声明极性、filter 与声明一致、没有关掉的层 | 3 层（gradient） |
| C11 | 芯在圈里、而且是"芯"的比例 | 18.0%（带 10%..30%） |

**C7/C8 是这张图的意义**，也是两条只有突变器才证明得了的规则：
闭合的六边、翻转的箭头，在 64 px 上都还像一个好好的图标。
**C7 量的是 tip-to-start，不是缺口本身** —— 箭头可以长到把缺口填满，而缺口读数一动不动（取舍 646）。

**12 ok / 0 failed；突变 24/24**（`--selftest`）。每条至少点亮一条规则；
C4 的宽度与高度**各有一条**（第一版宽度那条没有牙：它的突变先把字推出了框，红的是 C2/C9）。

### 8.3 命令

```bash
# 1) 拍母版 + 倒出版面读数（--w/--h 必须钉成 1024x1024）
D:/nodejs/node _tools/intro_render.js --page cover/continuation.html --at 0     --w 1024 --h 1024 --shot cover/THE_REACTOR_GAME_continuation_icon.png     --eval 'layoutReport()' > _tools/_attic/scratch/continuation_report.txt

# 2) 判（exit 1 = 有红）+ 突变
D:/nodejs/node _tools/continuation_judge.js _tools/_attic/scratch/continuation_report.txt
D:/nodejs/node _tools/continuation_judge.js --selftest _tools/_attic/scratch/continuation_report.txt

# 3) 六个部件逐个关掉再比像素（圈 / 箭头 / 芯 / 光晕 / 扫线 / 暗角）
PAGE=cover/continuation.html W=1024 H=1024 TAG=continuation SHOT=cover/THE_REACTOR_GAME_continuation_icon.png LAYERS="loop head coreDot glow scan vig" ASSETS="" bash _tools/cover_layers.sh

# 4) 512 上传件 = 判定过的母版的 LANCZOS 降采样
python -X utf8 -c "from PIL import Image; Image.open('cover/THE_REACTOR_GAME_continuation_icon.png').convert('RGB').resize((512,512), Image.LANCZOS).save('cover/THE_REACTOR_GAME_continuation_icon_512.png', optimize=True)"
```

**为什么 512 是降采样、不是直接渲一张 512**：判据跑在 1024 上；降采样是那一帧的确定性
变换，所以 512 继承那 12 条绿。原生 512 渲染字更锐（平均差 **1.40/255**，3.1% 的像素差 > 8，
都在字的边缘），但**它没有过判据**（取舍 647）。

**六个部件 6/6 都改变像素**（72883 / 8981 / 15223 / 445592 / 157587 / 647354 px，
最大差 205 / 232 / 156 / 33 / 36 / 122；连跑两次读数相同）——
这条跑道第一次伸到**主体**上，不只是装饰层。这一页没有位图素材，所以 `ASSETS=""`
打印「这一页没有位图素材，没有可量的」，而不是把封面的两张素材表再打一遍（取舍 649）。

### 8.4 字体：`--cond` 解析到哪一个字，是量出来的

`layoutReport()` 的 `font.probe` 把同一串字在六个候选家族里各量一次宽度：

| 家族 | 100 px 宽（`MMMMM CONTINUATION`） |
|---|---|
| Arial Narrow | **982.38** |
| Haettenschweiler | 1156.94 |
| Impact | 952.89 |
| Franklin Gothic Medium | 1069.64 |
| Arial | 1197.95 |
| sans-serif | 1156.94 |

`var(--cond)` = **982.38**，逐位等于 Arial Narrow ⇒ 这一页的大字就是 Arial Narrow。
这条读数顺带更正了 §7 那句「Arial Narrow 不在」（见那里的带日期更正，取舍 648）。

### 8.5 渲染的确定性：一次机器状态内逐字节，跨状态只到像素

同一份 `cover/continuation.html`（mtime 00:24:37，之后没动过）、同一条命令、同一排 flag，**两次测量**：

| | 文件 | 批内 |
|---|---|---|
| 00:24–00:26 | 535110 B / md5 `2a3a83db…` | 2/2 相同 |
| 00:29 以后（交付的是这一版） | 606769 B / md5 `a0baba54…` | **9/9 相同** |

跨状态差：mean **0.705/255**、max **57**、**2191 个像素 Δ>8**（0.21%，Δ>16 658 个）；
这一对图缩到 64 px：mean 0.268、max **3**、**0 个像素 Δ>8**。

**机制没定，所以写没定**：强制软件（`--disable-gpu`）与强制 GPU
（`--enable-gpu-rasterization --ignore-gpu-blocklist --use-angle=d3d11`）**都给现在这一版**，
旧那一版要不到。能说的是形状 —— 差异铺在渐变与 `drop-shadow` 的大面积低振幅处，
加上描边/字形的抗锯齿边缘（max 57 落在小字的一个边上），也就是**渲染管线那一侧**；
几何没动（C6 的 0.004 px 两次都成立，判据读的是 DOM）。

所以：**md5 认这一次落盘的文件，像素认这张画**，而且像素复核要带量级（取舍 651）。

### 8.6 没验的那一半

- **没上传**（`asset:write` / `ROBLOX_OPEN_CLOUD_API_KEY` 都没设），图标要他自己传。
- **Roblox 怎么裁没有读数**：外框与两行字到边缘的余量没有对着真实裁切量过（圆裁 / 方角都可能）。
- **512 没有单独过判据**（继承母版，见 8.3）。
- **"好看不好看"是判断不是读数**；能验的是圈开着、箭头顺着走、大字在 1/5 上 26.80 px。
- **没进 Studio、没进 Play、游戏本体 0 行改动。**

### 8.7 Phase 150 返工：主体换成厂标，环开口，箭头是**笔画自己的尖**

> 操作员原话：「有点奇怪啊改一下，而且是trg的continuation，你TRG也要有一定体现」

**三版的区别，一句话一版：**

| | 主体 | 缺口里的东西 | 操作员的读数 |
|---|---|---|---|
| v1（Phase 149） | 我画的六边 + 芯 | 一枚浮在中间的三角 | 「有点奇怪」（而且「TRG 没有体现」） |
| v2（同日，未交付） | 厂标 + 重画的环 | **贴上去的琥珀三角**，底边 68 px 而环才 13 px | 还是一顶帽子，还是"有点奇怪" |
| **v3（交付）** | 厂标 + 重画的环 | **环自己的尖**：同色、底边 30 px（环粗的两倍）、底边埋在弧端上 | —— |

v2 的问题不是颜色，是**件数**：那个三角形和环是两个物体，只是挨着。
v3 让它成为一件 —— 环用 round 线帽，笔画越过弧端半个粗，箭头的底边就压在那半个里面。
C8 里 `baseOffRing`（底边离环多远）就是为这件事写的读数：**v2 的底边中心虽然在环上，
但它的两条脚各伸出 27.5 px**，而那一版**没有任何一条规则在量"它是不是环的一部分"**。

**素材的数是量出来的**（`sm-core.png`，515×515，alpha≥128，1440 条射线逐半径扫）：

| r（素材像素） | 覆盖 |
|---|---|
| 235 / 236 / 237 | 9.5% / 3.3% / **0%** ← 三条臂到此为止 |
| **237..241** | **0%** ← clip 唯一能落的地方 |
| 242 / 243..256 / 257 | 12.4% / **100%** / 97.6% ← 环 |

所以环的中线 r=249.5、粗 15.2，臂到 236 为止，clip 取 **240**（上余 4 / 下余 2）。
这三行数是 C11 的依据，不是抄来的。

**几何常数**（`cover/continuation.html`，HTML 里一个坐标都不手写）：

| 常数 | 值 | 读数（`layoutReport()`） |
|---|---|---|
| `R_RING` | 249.5 × S | 画出来 **242.233**，素材环应是 **242.23**（差 0.00，band 2.0） |
| `RING_W` | 15.2 × S | 14.76 |
| `GAP_FROM / GAP_TO` | 348° → 292° | 缺口 **56°**（弧走 304°），弦长 227.44 px |
| `HEAD_LEN / HEAD_HALF` | 66 / 15 | **66.01 × 30**；tip-to-start **171.98**（缺口的 75.6%） |
| `CLIP_R` | 240 × S | 233.01，落在空带 **229.1..235.0** 里 |

**规则**（`_tools/continuation_judge.js`，**12 ok / 0 failed**，**突变 31/31**）：

| | 断言 | 读数 |
|---|---|---|
| C6 | 画出来的环**是一个圆**，**而且**在素材环的半径上 | 九点半径极差 **0.012 px**；242.233 对 242.23 |
| C7 | **环是开着的**：缺口 30°..90°、弧 270°..330°、箭尖到起点 ≥40 px 且不超过缺口的 85% | 56° / 304° / 171.98 px = 75.6% |
| C8 | **箭头是环自己的尖**：顺走、底边在环上、尺寸是"笔尖"不是"团块"、尖落在切线解上 | dot 1；base 离线 **0 px**；66×30；尖离线 8.83（切线解 8.83，band 0.5） |
| C11 | **主体是游戏自己的素材**，而且裁的只是素材本来就空的那一圈 | `sm-core.png` 500×500 / clip 233.01 ∈ [229.1, 235.0] |

C6/C7/C8 各有两个读数（圆 vs 半径、缺口大小 vs 箭头填满、顺走 vs 在环上），
所以各配两条突变（取舍 592）。**C8 的"底边在环上"那条是本轮新加的，它就是 v2 会红的那条。**

**新仪器 `_tools/continuation_ring_check.py` —— 因为 C6 的半径那一半原来是一句同义反复。**
判据手里的 `ASSET_RING_R = 249.5` 和页面里的 `249.5 * S` 是**同一个字面量**：改一边会红，
两边一起改就绿（§0.31 ⑥）。新仪器**一个半径常数都不持有**：

```
asset 515x515: ring band r 243..257  -> centre 250.0, width 15   (asset px)
drawing:     ring band r 236..249 in the box -> 242.50 canvas / 249.8 asset px
radius   drawn 249.8 - asset 250.0 = -0.22 asset px   (band +-3.0)   ok
width    drawn 14.4 - asset 15.0 = -0.58 asset px     (band +-3.0)   ok
opening  39.38 deg of the drawn ring has no ink       (band 25..80)  ok
```

**"opening 39.38" 和判据的 "gap 56°" 是两个量，不是两个读数打架**：像素这边**箭头也是墨**，
它吃掉自己那 15.6°（66 px / r 242.2），56 − 15.6 ≈ 40.4，实测 39.38（差的是带边抗锯齿）。
两个数都写在屏上，差值也写出来 —— 抹平它才是错（取舍 656）。

**仪器自己验过牙齿**（把页面复制一份、只改一个常数、重渲）：
把环挪到 r=262 → `radius +5.95 → FAIL`；把缺口收到 4° → `opening 0.00 → FAIL`（而半径那一行
仍然 ok，两条读数互不顶替）。

**"主体是素材"这一半靠像素**（`cover_mark_check.py` 新增 `CLIPR`，因为这份素材的环是**故意**被裁掉的）：

```
SHOT=cover/THE_REACTOR_GAME_continuation_icon.png BOX=500 BOX_X=262 BOX_Y=165 CLIPR=233
  CLIPR 233.0 px (box units): setting aside 22370 ink px outside the clip
  ink 41011 px (16.40% of the box)
  t=100 -> tp 41011, recall 1.0000    (t=120 -> 41007, 0.9999；每一条半径带都是 100%)
```

precision 0.667 是**关于这个 box** 的读数（画上去的环和箭头也在 box 里、也是亮的），不是关于素材的。

**逐层（6/6 都改变像素）**：`emblem 43550 / ring 93513 / head 7795 / glow 401997 / scan 164078 / vig 660548`
（最大差 234 / 205 / 201 / 32 / 36 / 122）。

**交付**：母版 **620594 B / md5 `ea0107d6…`**（同一次机器状态内 **3/3** 逐字节相同），
上传件 **169140 B / md5 `7adad5da…`**（母版 LANCZOS + `optimize=True`，与一次重算逐像素相同）。

```bash
# 1) 母版 + 版面读数
D:/nodejs/node _tools/intro_render.js --page cover/continuation.html --at 0 --w 1024 --h 1024 \
  --shot cover/THE_REACTOR_GAME_continuation_icon.png --eval 'layoutReport()' \
  > _tools/_attic/scratch/continuation_report.txt
# 2) 判 + 突变（12 项 / 31 条）
D:/nodejs/node _tools/continuation_judge.js _tools/_attic/scratch/continuation_report.txt
D:/nodejs/node _tools/continuation_judge.js --selftest _tools/_attic/scratch/continuation_report.txt
# 3) 像素：环的半径 / 粗细 / 开口，对素材自己的环
python -B _tools/continuation_ring_check.py
# 4) 像素：clip 以内那 41011 个墨点是不是这张素材
SHOT=cover/THE_REACTOR_GAME_continuation_icon.png BOX=500 BOX_X=262 BOX_Y=165 CLIPR=233 \
  python -B _tools/cover_mark_check.py
# 5) 六个部件逐个关掉再比像素
PAGE=cover/continuation.html W=1024 H=1024 TAG=continuation \
  SHOT=cover/THE_REACTOR_GAME_continuation_icon.png \
  LAYERS="emblem ring head glow scan vig" bash _tools/cover_layers.sh
# 6) 512 上传件
python -B -c "from PIL import Image; Image.open('cover/THE_REACTOR_GAME_continuation_icon.png').convert('RGB').resize((512,512), Image.LANCZOS).save('cover/THE_REACTOR_GAME_continuation_icon_512.png', optimize=True)"
```

**没验的那一半（Phase 150 新增的）**：
- **"不奇怪了"是操作员的一句话，不是我的读数。** 我能给的是"箭头和环是一件事"的三条断言
  （底边离线 0 px、尖落在切线解上、半径等于素材环），**好不好看仍然是判断**。
- **素材环的半径是用 100%/半覆盖的边界定的**（243..256 满、242/257 各半），
  所以"250.0"本身有 ±0.5 px 的不确定度；band 给的是 ±3。
- **两个仪器的 39.38 与 56 差 16.6°**，其中 15.6° 是算出来的箭头弧长、**1.0° 没有拆开量**。**

---

## 9. The Reactor Game - Rebuild 的图标（Phase 151，2026-10-31）

操作员原话：**「做个Rebuild的图标」**。交付：

| 文件 | 尺寸 | 字节 | md5 |
|---|---|---|---|
| `cover/THE_REACTOR_GAME_rebuild_icon.png` | 1024×1024 | **599240** | `bf2545d593a6be832908ab9d0d496463` |
| `cover/THE_REACTOR_GAME_rebuild_icon_512.png` | 512×512 | **161713** | `ac08d920dafe1d47307c81d65b556158` |

母版同一次机器状态内 **4/4 逐字节相同**；512 是母版 LANCZOS + `optimize=True`。
判据**15 ok / 0 failed**，突变 **35/35**；像素仪器 **9/9**，母版与 512 **各判一次**。

### 9.1 和 Continuation 的差别，一句话

同一套语言（外框 / 厂标 + 环 / 一个词），**让环说不同的话**：

- Continuation：环**开着**，断口**自己长出箭头** —— 它还在走。
- Rebuild：环**缺了一整段**，那一段**被端在外面**、琥珀色，一条虚线沿缺口的中半径连着它。

**"环缺了一块"本身不构成 Rebuild** —— 那和 Continuation 是一个形状。
是"**那一块真的被端出来了（54 px）且正对着槽（188° 对 188°）**"把它变成"正在装回去"。

### 9.2 几何与出处

| 量 | 值 | 出处 |
|---|---|---|
| `ASSET_PX` / `EMBLEM_S` | 515 / 500 | 素材自己的像素尺寸；素材画 500 |
| `S` | 0.9709 | `EMBLEM_S / ASSET_PX` |
| `R_RING` | **242.24** = 249.5 × S | 素材的环，1440 条射线量的（§8.7） |
| `RING_W` | **14.76** = 15.2 × S | 同上 |
| `CLIP_R` | **233.0** = 240 × S | 落在素材空的那一圈 236·S..242·S = 229.1..235.0 |
| `MARK_CX / MARK_CY` | 512 / 415 | 与 Continuation 同一处 |
| `SLOT_FROM / SLOT_TO` | 160° / 216° | 宽 56°、中线 188°：避开三根臂（24–36 / 144–156 / 264–276）与标题（49–131°） |
| `LIFT` | **54** | 那一块沿 188° 推出多远；净空 39.24 px = 2.66 个环宽 |
| `GUIDE_W` | 2.2 | 虚线宽，两端各留 6 px |

### 9.3 规则（R0..R14）

见 `docs/SNIPPETS.md` §5.54 的表和 `PROGRESS.md` Phase 151 §二。
三条是这一轮的重点，而且**三条失败的样子在 64 px 上都是一枚好图标**：

- **R8 那一块就是缺的那一段**（同宽 56°、同曲率）—— 否则它是**装饰**；
- **R9 那一块真被端出来了**（54 px、净空 2.66 环宽）—— 否则它坐进槽、环闭合、**rebuild 消失**；
- **R10 那一块正对着槽、虚线在同一条半径上** —— 否则它是**碎片**。

### 9.4 两台仪器，各量各的

| | `_tools/rebuild_judge.js` | `_tools/rebuild_pieces_check.py` |
|---|---|---|
| 读什么 | 页面上**路径**的量（`layoutReport()`） | 交付 PNG 的**墨** |
| 持有页面的常数吗 | 不持有 `R_RING`/`LIFT` 等；半径用素材的 249.5 × 从 img 框读回的 S | **一个都不持有** |
| 环 | 242.233（9 点极差 0.008） | 249.8 asset px（素材 250.0，差 −0.22） |
| 缺口 | 56°，中线 188° | 55.88°，中线 188.06° |
| 那一块 | 56°，r 296.24，端出 54.00 | 56.12°，188.06°，净空 40.00 px = 2.86 环宽 |
| 颜色 | 比 `Config.Visual` 两个 token | 量均值：块 `rgb(220,111,2)`、环 `rgb(203,204,204)` |

**两个数不必逐位相同**，而且不相同本身是有信息的（取舍 656 的同一个立场）：
判据量"设计要它多宽"，像素量"看的人看到多宽"。

### 9.5 命令

```bash
# 一条命令跑完整条链（推荐）：
bash _tools/icon_runs.sh rebuild

# 或者拆开：
D:/nodejs/node _tools/intro_render.js --page cover/rebuild.html --at 0 --w 1024 --h 1024 \
    --eval "layoutReport()" --shot cover/THE_REACTOR_GAME_rebuild_icon.png > /tmp/rb_report.json
node _tools/rebuild_judge.js /tmp/rb_report.json            # 15 ok / 0 failed
node _tools/rebuild_judge.js --selftest /tmp/rb_report.json # 35/35
python -B _tools/rebuild_pieces_check.py                    # 9/9
SHOT=cover/THE_REACTOR_GAME_rebuild_icon_512.png BOX_X=131 BOX_Y=82 BOX=250 \
    python -B _tools/rebuild_pieces_check.py                # 9/9

# 逐层关掉再比像素：
PAGE=cover/rebuild.html W=1024 H=1024 TAG=rebuild \
  SHOT=cover/THE_REACTOR_GAME_rebuild_icon.png \
  LAYERS="emblem ring piece guide glow scan vig" ASSETS="" bash _tools/cover_layers.sh

# 像素仪器的"能红"：三张真坏的图（结果在 PROGRESS.md Phase 151 §五）
sed 's/^const LIFT      = 54;/const LIFT      = 0;/' cover/rebuild.html > cover/_mut_seated.html
# 其余两条：把 #piecePath 的 stroke 改成 var(--ready)；把 SLOT_FROM 160 改成 130
```

### 9.6 没验的那一半

- **"好不好看"是判断。** 我能给的是几何，和 64 / 256 px 上的**描述**。
- **256 px 上副标题读不出**（`THE REACTOR GAME` 被读成 `THE READING GAME`），没有改字号。
- **没上传**（没有 `asset:write`）；**Roblox 怎么裁这张图仍然没有读数。**
- **256 及以下的尺度没跑像素仪器**；`thickness` 用的是**绝对像素差**，
  在小尺寸上会重新变成比值问题（取舍 660 的尾巴）。

## 10. The Reactor Game - Reimagine 的图标（Phase 152，2026-10-31）

操作员原话三句：**「设计个TRG-reimagine的」** / **「可以参考所有素材」** / **「别跟之前设计的一样」**。
交付：

| 文件 | 尺寸 | 字节 | md5 |
|---|---|---|---|
| `cover/THE_REACTOR_GAME_reimagine_icon.png` | 1024×1024 | **577756** | `41b49a554486c22da15525e33fa08060` |
| `cover/THE_REACTOR_GAME_reimagine_icon_512.png` | 512×512 | **164879** | `8b08e786abfbc76345333ab85ed5c02e` |

母版同一次机器状态内 **5/5 逐字节相同**；512 是母版 LANCZOS + `optimize=True`。
判据 **17 ok / 0 failed**，突变 **32/32**；像素仪器 **12/12**，母版与 512 **各判一次**（都 12/12）。

### 10.1 "别跟之前设计的一样"落成什么

前两枚（8 / 9 节）都是**居中的厂标 + 下面一行字**，换的只是环在说什么。
第三枚换的**不是环的嘴，是整张画的说话方式**：

```
        ┌──────────────┬──────────────┐
        │  厂标 = 画的  │  厂标 = 铸的  │     一条竖轴（= 厂标自己的竖轴，x=566）
        │  白线 / 空核  │  白线 / 琥珀核│     把**同一个**厂标劈成两个状态
        ├──────────────┼──────────────┤
        │  REIMA       │  GINE        │     同一条 x 劈开标题，切口在字母缝里
        └──────────────┴──────────────┘
             THE REACTOR GAME            （副标题不分）
```

**厂标只有一份**：一个 `<img>`，620 px，跨着那条轴穿过它。琥珀不是"半个厂标"，
是它**底下**半个圆盘 —— 所以两半的白线是**同一份字节**。
这是它和"把图左右镜像"或"两个不同图标拼起来"的分界，也是像素仪器量的东西。

### 10.2 几何与出处

| 量 | 值 | 出处 |
|---|---|---|
| `ASSET_PX` / `EMBLEM_S` | 515 / **620** | 素材自己的像素尺寸；这一枚画得比上两枚大 |
| `S` | 1.20388 | `EMBLEM_S / ASSET_PX` |
| `R_RING` / `RING_W` | **300.37** / **18.30** = 249.5·S / 15.2·S | 素材的环（1440 条射线量的，§8.7） |
| `R_IN` | **291.22** = (249.5 − 15.2/2)·S | 环的内缘 = 琥珀盘的半径 |
| `MARK_CX / MARK_CY` | 566 / 400 | 轴 = 厂标方框的中心 |
| `TITLE_SIZE / TITLE_TOP` | 176 px / 800 | 词宽 897.0 = 画面的 87.6% |
| `TITLE_CUT_AFTER` | 5 | 切在 `REIMA` 后面；那个 x 是**量**出来的（Range 读字母盒） |

颜色逐字抄自 `cover/index.html`（`Config.Visual.Ready` / `.Amber`）。**一个新颜色都没有。**

### 10.3 规则（R0..R16）

全文见 `PROGRESS.md` Phase 152 §三。三条值得单独说：

- **R3 两份字的盒子逐像素相同** —— 这是"同一个词换性质"能成立的方式：**注册出来的，不是摆出来的**。
- **R14 三个 clip 都从各自元素自己的盒子重建** —— 因为 `inset()` 的量纲是元素自己的盒子
  （取舍 668），第一版按画布算，白字停在 499、琥珀从 626 起，中间空 127 px，
  **而 `clipPath` 字符串读回来逐字正确**。
- **R8 切口落在两个字母之间的缝里**（偏 0.00 / 0.02 px）—— 切在笔画上会削掉一条腿。

### 10.4 像素仪器（12 条，两个尺度）

`_tools/reimagine_pieces_check.py`。**不持有页面的任何一个常数**：

| 读数 | 母版 | 512 | 容差 |
|---|---|---|---|
| 白环外缘拟合 | (565.29, 399.63) r 310.00，残差 **0.65** | r 155.07，残差 **0.51** | 1.5 |
| 琥珀的左边在轴上 | 566 对 565.29（差 0.71） | 283 对 282.12（差 0.88） | 2.0 |
| 琥珀到环内壁 | r 290.86 / 环带起点 293（差 2.14） | 145.49 / 147（差 1.51） | 2.91 / 2.00 |
| 环是**品牌自己那条环**（内/外，尺度无关） | 0.9482 对素材 0.9531（差 0.0049） | 0.9545（差 0.0014） | 0.012 |
| **两半是同一张画**（归一化 L1） | **0.01459** | **0.01479** | 0.035 |

最后一行是这一轮唯一一个**换了统计量**的地方：原来的"任一半径的最大差"在 512 上
红在正确的成品上（0.283 对 0.219），那不是"两半不一样"，那是**光栅噪声**（取舍 673）。

### 10.5 怎么重跑

```bash
bash _tools/icon_runs.sh reimagine        # 渲染 → 判 → 像 → 512 → 再判 → md5

# 两个仪器各自的"能红"：
/d/nodejs/node _tools/reimagine_judge.js _tools/_attic/scratch/icon_report_reimagine.json --selftest
python -B _tools/reimagine_pieces_check.py --selftest                       # 1024
SHOT=cover/THE_REACTOR_GAME_reimagine_icon_512.png \
    python -B _tools/reimagine_pieces_check.py --selftest                   # 512

# 整条链的"能红"：把厂标的裁剪拿掉，琥珀就漏进左半（3 红）
sed "s|'inset(0 0 0 ' + (EMBLEM_S / 2).toFixed(2) + 'px)'|'inset(0 0 0 0px)'|" \
    cover/reimagine.html > cover/_tmp_break.html
/d/nodejs/node _tools/intro_render.js --page cover/_tmp_break.html --at 0 --w 1024 --h 1024 \
    --shot _tools/_attic/scratch/reim_break.png
SHOT=_tools/_attic/scratch/reim_break.png python -B _tools/reimagine_pieces_check.py
rm -f cover/_tmp_break.html
```

### 10.6 没验的那一半

- **"好不好看"是判断。** 512 上的一段描述在 `PROGRESS.md` Phase 152 §八。
- **没上传**（没有 `asset:write`）；**Roblox 怎么裁这张 1:1 仍然没有读数。**
- **256 / 64 px 没跑仪器、也没看**。前两枚在这些尺寸上量过，这一枚没有。
- **像素仪器的两个尺度是 1024 / 512**，其他尺寸没跑。
- **没进 Studio、没进 Play，游戏本体 0 行。**
