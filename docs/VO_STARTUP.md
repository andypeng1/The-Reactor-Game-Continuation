# 开机序列 —— 配音台本

> Phase 153（2026-10-31）。操作员原话：「**我要开始配音了，先来个反应堆开机的
> （先来个开机序列启动**」。
>
> 这里面有**两份台本**：
> **A 是系统播报**（16 句，逐字就是游戏自己的日志，英文）—— 这是"开机序列"本身；
> **B 是画外音旁白**（8 段，英文 + 中文各一版）—— 这是给视频配的解说。
>
> **时间码不是写的，是算的**：全部从 `src/ReactorBackend/Config.luau` 的
> `Shift.StartupSteps` 推出来，`_tools/startup_vo_timing.py` 生成、并且能反过来校验这份文档。
> 改了 Config 而没改这里，`--check` 会红。

---

## 0. 三十秒版

1. **先录台本 A**，16 句，一句一个文件。整条链 **113.4 秒**，但真正要说的话只有 **29.6 秒** ——
   剩下的时间是机器在动，**留白是内容**。
2. **三处必须一口气念**：第 1+2+3 句、5+6+7 句、13+14 句在原版里是**同一拍写进日志的**（时间戳逐位相同）。
   把它们拆成三个节拍念，是在发明面板没做过的事；三组各自后面都有 11.7–29.4 秒的空，
   **一口气念完、然后晾着**才是对的形状。
3. **要中文就录台本 B**。B 不是逐字翻译，是画外音，8 段、约 30 秒话。

---

## 1. 时间码

`t` 是这一行**写进日志**的时刻，`window` 是它到下一行之间的空档，`est. read` 是念完这句
**按 2.5 词/秒估算**要多久（**这是假设，不是测量** —— 仓库里一句都还没录过）。

下面是生成块，**不要手改**；要改就改 `Config.luau` 再跑一遍工具。

<!-- VO-TIMELINE:BEGIN -->
| # | t (s) | window (s) | kind | words | est. read (s) | spoken line |
|---:|---:|---:|---|---:|---:|---|
| 1 | 0.0 | 0.0 | ALERT | 5 | 2.0 | SUBSPACE REACTOR START-UP SEQUENCE INITIATED |
| 2 | 0.0 | 0.0 | WARN | 8 | 3.2 | ALL PERSONNEL ARE TO VACATE THE CHAMBER IMMEDIATELY |
| 3 | 0.0 | 29.4 | WARN | 4 | 1.6 | ACTIVATING POWER EXTRACTION ASSEMBLY |
| 4 | 29.4 | 4.0 | INFO | 5 | 2.0 | PRIMING ISOTOPE E COOLANT NETWORK |
| 5 | 33.4 | 0.0 | INFO | 4 | 1.6 | CALIBRATING REACTOR SENSOR NETWORK |
| 6 | 33.4 | 0.0 | INFO | 3 | 1.2 | E-VENT STRUCTURES PRIMED |
| 7 | 33.4 | 11.7 | WARN | 5 | 2.0 | SUBSPACE RIFT ACTIVE, RADIATION WARNING |
| 8 | 45.1 | 1.5 | INFO | 5 | 2.0 | PRIMING CHAMBER ATMOSPHERIC REGULATORY SYSTEM |
| 9 | 46.6 | 8.8 | WARN | 4 | 1.6 | INITIATING DEEP SCAN PROCEDURE |
| 10 | 55.4 | 14.2 | INFO | 4 | 1.6 | DEEP SCAN PROCEDURE COMPLETED |
| 11 | 69.6 | 1.5 | ALERT | 4 | 1.6 | PRIMING ALL COMBUSTION LASERS |
| 12 | 71.1 | 11.1 | INFO | 3 | 1.2 | M.E.T.U DIAGNOSTICS ACCEPTABLE |
| 13 | 82.2 | 0.0 | ALERT | 6 | 2.4 | ALL SYSTEMS READY, CORE IGNITION IMMINENT |
| 14 | 82.2 | 27.2 | ALERT | 3 | 1.2 | COMBUSTION LASERS FIRING |
| 15 | 109.4 | 4.0 | ALERT | 2 | 0.8 | START-UP COMPLETED |
| 16 | 113.4 | -- | INFO | 9 | 3.6 | PLEASE REFER TO [DIGITAL REACTOR MANUAL] FOR FURTHER INSTRUCTIONS |

Same-tick bursts (the order inside a burst is not in the captures -- see PROGRESS.md 65.2):

| burst | t (s) | est. read (s) | air after (s) |
|---|---:|---:|---:|
| 1+2+3 | 0.0 | 6.8 | 29.4 |
| 5+6+7 | 33.4 | 4.8 | 11.7 |
| 13+14 | 82.2 | 3.6 | 27.2 |
<!-- VO-TIMELINE:END -->

**`kind` 怎么用**：它不是给人看的，是**语气**。`ALERT` 平、硬、往前顶；
`WARN` 同一副嗓子、低半步、念之前留半拍气；`INFO` 更轻更快，是"不重要那条通道"。
面板的 `<b>` 标记是它自己的富文本，**不念出来**（"bracket alert bracket" 是错的）。

---

## 2. 台本 A —— 系统播报（逐字，游戏原话）

### 2.1 两句题外话，录音前先知道

- **这些字是游戏的，不是我的**。逐字出自 `docs/ORIGINAL_UI_TEXT.md` §1，只去掉了
  `<b>[ALERT]</b> - ` / `<b>[WARN]</b> - ` 这类面板标记。**一个字都不要改** ——
  它不是文案，是这台机器的日志。
- **三组 burst 之内没有"顺序"这回事**。录像把同拍的行按字符串排过序再写盘
  （`PROGRESS.md` §65.2），所以"先 CALIBRATING 还是先 E-VENT"**不在字节里**。
  念的时候挑一个顺口的次序不算改设定，**但别在成片里声称那是原版的次序**。

### 2.2 提词器版（照着念，`|` 是换气）

左边那个数字是**段号**（= §6 的 `A01..A11`），**不是 §1 的行号**：
一段可能装两到三行，因为那几行在原版里是同一拍。

```
1  SUBSPACE REACTOR START-UP SEQUENCE INITIATED |
   ALL PERSONNEL ARE TO VACATE THE CHAMBER IMMEDIATELY |
   ACTIVATING POWER EXTRACTION ASSEMBLY.

2  PRIMING ISOTOPE E COOLANT NETWORK |

3  CALIBRATING REACTOR SENSOR NETWORK |
   E-VENT STRUCTURES PRIMED |
   SUBSPACE RIFT ACTIVE, RADIATION WARNING |

4  PRIMING CHAMBER ATMOSPHERIC REGULATORY SYSTEM |

5  INITIATING DEEP SCAN PROCEDURE |

6  DEEP SCAN PROCEDURE COMPLETED |

7  PRIMING ALL COMBUSTION LASERS |

8  M.E.T.U DIAGNOSTICS ACCEPTABLE |

9  ALL SYSTEMS READY, CORE IGNITION IMMINENT |
   COMBUSTION LASERS FIRING.

10 START-UP COMPLETED |

11 PLEASE REFER TO THE DIGITAL REACTOR MANUAL FOR FURTHER INSTRUCTIONS.
```

**两处念法**：第 11 句面板写的是 `[DIGITAL REACTOR MANUAL]`，方括号是它自己的引用样式，
**念 "the digital reactor manual"**，不念括号。`START-UP` 念一个词（"startup"），不是一个词一个词蹦。

### 2.3 中文对照（知道自己在念什么）

| # | 中文 |
|---:|---|
| 1 | 子空间反应堆开机序列已启动 |
| 2 | 全体人员立即撤离反应舱 |
| 3 | 正在启动能量提取组件（PEA） |
| 4 | 正在灌注同位素 E 冷却网络 |
| 5 | 正在校准反应堆传感器网络 |
| 6 | 紧急排气结构已就绪 |
| 7 | 子空间裂隙已激活，辐射警告 |
| 8 | 正在灌注舱内大气调节系统 |
| 9 | 开始深扫程序 |
| 10 | 深扫程序完成 |
| 11 | 正在给全部燃烧激光充能 |
| 12 | M.E.T.U 诊断结果可接受 |
| 13 | 全系统就绪，堆芯点火在即 |
| 14 | 燃烧激光发射中 |
| 15 | 开机完成 |
| 16 | 请参阅《数字反应堆手册》获取后续指示 |

---

## 3. 台本 B —— 旁白

这一版**不是翻译 A**，是画外音：A 是机器在说话，B 是有人在讲这台机器。
每一句都踩在一个真实的时间码上，**§3.3 那张表写着它踩在什么事件上、依据是什么**。
**30 秒左右的话，铺在 113 秒的画面上** —— 留白比 A 还多。

### 3.1 英文

```
@0:00  This is a subspace reactor. There are no control rods in this machine.
       There never were.

@0:29  Coolant network primed: three Isotope E loops.
       They will drift, and they will not tell you.

@0:45  The chamber is being emptied.
       Everything after this point happens behind the hull.

@0:55  Deep scan running.

@1:09  Three combustion lasers, charging. Five power levels each.
       They are the only heat this core has — and the fastest way to lose it.

@1:22  All systems ready. Ignition imminent.

@1:49  Start-up complete.

@1:56  From here, how long it runs is entirely up to you.
```

### 3.2 中文

```
@0:00  这是一台子空间反应堆。它没有控制棒 —— 从来就没有。

@0:29  冷却网络已灌注：三条同位素 E 回路。
       它们会漂，而且不会告诉你。

@0:45  反应舱正在清空。
       接下来的一切，都发生在舱壁的另一侧。

@0:55  深扫进行中。

@1:09  三台燃烧激光充能中，每台五档。
       它们是这座堆芯唯一的热源 —— 也是最快弄丢它的方式。

@1:22  全系统就绪，点火在即。

@1:49  开机完成。

@1:56  从现在开始，它能跑多久，完全取决于你。
```

### 3.3 每一句的依据（怕下一轮有人当成我编的）

| @ | 句 | 依据 |
|---|---|---|
| 0:00 | no control rods | `CLAUDE.md` §1.2：Wiki 反复确认过，这个游戏里**不存在控制棒**，玩家只有三个间接手段 |
| 0:29 | three Isotope E loops | `Config` 的 `pumps` 三台、`Core.pumps` 0..3 档（`docs/SYSTEMS.md` §2.28） |
| 0:29 | they will drift, and they will not tell you | Wiki：冷却传感器设备「有不可靠的倾向」、需要「手动干预校准」（`CLAUDE.md` §7） |
| 0:45 | the chamber is being emptied | 游戏自己的第 2 行 `ALL PERSONNEL ARE TO VACATE THE CHAMBER IMMEDIATELY` |
| 0:55 | Deep scan running | 第 9 / 10 行 `INITIATING DEEP SCAN PROCEDURE` / `DEEP SCAN PROCEDURE COMPLETED` |
| 1:09 | three combustion lasers, five power levels | `off/PW1..PW5`；`Engine:Command` 的 `cbl` 收 `value 1..5` |
| 1:09 | the fastest way to lose it | CBL 是**唯一**的热源，也是过热的来源（`docs/SYSTEMS.md` §2.27 那三条控制手段） |
| 1:22 | All systems ready. Ignition imminent. | 第 13 行逐字（只去掉了 `[ALERT]` 标记） |
| 1:49 | Start-up complete. | 第 15 行逐字 |
| 1:56 | how long it runs is entirely up to you | 没人管的开机在 `Running` 之后 **143.3 秒**走到 `Failed`（Phase 127 实测） |

---

## 4. 三条从实测里来的约束

这三条不是风格建议，是这条链自己的性质。**违反了不会报错，只会在成片上看着不对。**

### 4.1 三组同拍 —— 见 §1 的 burst 表

`1+2+3` 落在 0.0 秒，`5+6+7` 落在 33.4，`13+14` 落在 82.2。**面板在同一拍写了三行**，
所以它从来没有"一句一句"过。三组各自后面有 29.4 / 11.7 / 27.2 秒的空 ——
**一口气念完，然后让画面自己走**。

### 4.2 这一趟可能是 91 秒，也可能是 152 秒

四趟跑完的端到端是 **91.4 / 112.6 / 114.3 / 151.7 秒**（`PROGRESS.md` §65.1），中位 **113.44**。
`Config` 里那串 hold 是**中位数**，不是机器规则 —— 这也正是 `StartupSeconds` 不能写成常数、
只能逐段留 hold 的原因。

**对录音的意思**：每句前后各留 1 秒干净的气，后期随便推。**别写任何必须在某一秒切的话** ——
你要贴的那条画面，多半不是中位数那一趟。

### 4.3 面板是流水，不是旁白

原版那块 `SYSTEM LOGS` 只有四行、轮着滚、同一条消息会重复；有一趟的 `TemplateLogFrame3`
里还留着**上一次会话滚剩下的半行** `E INITIATED`（`PROGRESS.md` §65.1）。
所以：**跟顺序，不要跟面板的节奏**。面板不负责讲故事。

---

## 5. 发音表

标 **[拼写]** 的是这个词在游戏里只以拼写出现过，读法是照英文走；
标 **[选择]** 的是**两个都对、但你得自己定一个** —— 整份片子要统一。

| 词 | 念 | 备注 |
|---|---|---|
| SUBSPACE | /ˈsʌb.speɪs/ "SUB-space" | [拼写] |
| REACTOR | /riˈæk.tɚ/ | [拼写] |
| ISOTOPE E | /ˈaɪ.sə.toʊp iː/ "EYE-suh-tohp EE" | [拼写] 不是"伊索托普"那种重音 |
| **E-VENT** | /ˈiː.vent/ "**EE-vent**" | [拼写] **最容易错的一条**：它是 `Emergency Vent` 的缩写，念字母 E + vent，**不是英文单词 "event"** |
| CALIBRATING | /ˈkæl.ə.breɪ.tɪŋ/ | [拼写] |
| ATMOSPHERIC | /ˌæt.məsˈfer.ɪk/ | [拼写] |
| REGULATORY | /ˈreɡ.jə.lə.tɔːr.i/ | [拼写] |
| M.E.T.U | 逐字母 "em-ee-tee-you" 或一个词 "MET-oo" | **[选择]** 游戏从没给过读法。**推荐逐字母** —— 这个项目的点号缩写惯例就是这个意思（`docs/SRSU.md`：`S.A.M.O.S.` / `P.E.A` / `C.B.L` / `M.E.T.U`） |
| CBL | 逐字母 "see-bee-el" | [拼写] 片子别念成 "cable" |
| PEA | 逐字母 "pee-ee-ay" | [拼写] |
| DEEP SCAN | 两个词都念 | |
| START-UP | "startup" 一个词 | |
| `[DIGITAL REACTOR MANUAL]` | "the digital reactor manual" | 方括号不念 |

---

## 6. 录音参数与文件命名

- **格式**：48 kHz / 24-bit WAV，单声道。降噪、门限、压缩**全部关掉** —— 后期统一做，
  录进去的噪声可以去掉，录进去的加工去不掉。
- **电平**：峰值目标 **−6 dBFS**，别贴 0。
- **气口**：每句**前后各留 1 秒**静音。§4.2 说了为什么。
- **一版一句**，文件名按下面这张表；**另外再录一版连续的**（§2.2 一口气读完、不剪）——
  连续那版是用来抓断句的，不是用来交的。

| 文件 | 内容 |
|---|---|
| `A01_startup_initiated.wav` | §2.2 第 1 段（三句一口气） |
| `A02_priming_isotope_e.wav` | 第 2 段 |
| `A03_calibrating.wav` | 第 3 段（三句一口气） |
| `A04_atmospheric.wav` | 第 4 段 |
| `A05_deep_scan.wav` | 第 5 段 |
| `A06_deep_scan_done.wav` | 第 6 段 |
| `A07_lasers_priming.wav` | 第 7 段 |
| `A08_metu.wav` | 第 8 段 |
| `A09_systems_ready.wav` | 第 9 段（两句一口气） |
| `A10_completed.wav` | 第 10 段 |
| `A11_refer_manual.wav` | 第 11 段 |
| `B01..B08_*.wav` | 台本 B，一段一个 |

- **念的时候别看面板闪什么**，看 §1 的 `window` 那一列：句子短、空档长，**慢比快好**。
- 这套东西**没有一条自动检查**。台词对不对，只能靠 §2.3 的中文对照和你自己的耳朵。

---

## 7. 出处 / 再生成 / 校验

| 什么 | 从哪来 |
|---|---|
| 16 行的**文本** | `src/ReactorBackend/Config.luau` → `Shift.StartupSteps[].text`（逐字，含 `<b>`） |
| 16 行的 **hold** | 同一个表 `[].hold` |
| `t` 的定义 | `Engine:AdvanceStartup`：第 N 行在"第 1..N 个 hold 之和"那一刻写进日志 |
| 那些 hold 本身 | `PROGRESS.md` Phase 65：五趟录像的**中位数**，散布 §4.2 引的就是那里 |
| 逐字文本的另一份 | `docs/ORIGINAL_UI_TEXT.md` §1 |

```
python -X utf8 _tools/startup_vo_timing.py                        # 印出这张表
python -X utf8 _tools/startup_vo_timing.py --check docs/VO_STARTUP.md   # 文档 ↔ Config 对不上就 exit 1
```

`--check` 只能告诉你**文档不再等于 Config**，它不能告诉你 Config 是对的 ——
那件事的证据是五趟录像，在 `PROGRESS.md` 里，不在这条命令里。

---

## 8. 没验的

- **一句都没录过。** `est. read` 是 2.5 词/秒的**假设**，不是测量；真实语速只有你念出来才知道。
- **没有原版播报人声可参照。** 仓库里 429 个音效（`TRG Sounds & Images pack/`）按文件名找，
  没有一条像播报；唯一叫 "startup" 的 `asstes/music/ReactorStartup.mp3` 是**参考曲**
  （一份 Portal 2 的钢琴改编，`docs/SYSTEMS.md` §2.16 那份分析），**不是原版的开机音**。
  所以"这台机器听起来该是什么样"是判断，不是读数 —— 这一条不许在下游被写成"还原了原版播报"。
- **时间码是五趟的中位数**，不是机器规则（见 §4.2）。
- **台本 B 的每一句都有出处**（§3 底下那张表），但**哪些句子该留、哪些该删**是判断 ——
  我先按"每段一个事实"删到 8 句，你念着不顺就砍。
- 没进 Studio、没进 Play、**游戏代码 0 行**。
