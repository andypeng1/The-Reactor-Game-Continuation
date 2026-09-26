# -*- coding: utf-8 -*-
"""Apply the section-3 edits to docs/TODO.md (the disk half of the CLAUDE module's section 3).

Three edits, each located by a key that must appear EXACTLY once:
  A  insert a new bullet after the line containing 4.78   (the CBL second pass, done)
  B  insert a new bullet after the line containing **未开始：**  (the console second pass, next)
  C  replace the four-line bullet containing 'vision sidecar' with the corrected version

The same three edits are applied to the CLAUDE ModuleScript by hand with execute_luau, which
uses the same keys and the same assertions. If the two copies ever differ, verify_docs.py goes
red -- section 3 is one of the sections it reassembles, so a one-byte drift cannot hide.
"""
import io

P = r"D:\rblxTRGproject\docs\TODO.md"

BULLET_A = """- [x] **三台 CBL 激光二次重做**（`PROGRESS` Phase 39 / `DECISIONS` 108-110）—— `Rebuild.LaserFrame`，
      **加件不换壳**：每台 +125 件（肋 56 / 螺栓 28 / 侧轨 8 / 风管 8 / 灯带 8 / 危险条 16 / 铭牌 1）
      外加 4 个 `PointLight` 和 1 个 `SurfaceGui`（`CBL-1/2/3`），全部落在新建的 `Mk2Frame` 文件夹里。
      **为什么不重建外壳**：每台 2,655 件作者手打的壳（210 MeshPart / 100 Union / 485 Wedge /
      251 个活 Texture·Decal）没有程序化替代品，按 §1.4 不能删；而拿一个素箱子盖住细节机是**更差**的
      轮廓，只是又多一种风格。第一次翻新（`LaserKit`）只改颜色，**桶还是圆的**，跟控制室里方正、
      带黄铜箍的 Mk2 台子并排就是别扭 —— 这一轮把方正的观感做在**外壳之外的框架**上。
      半径全部**射线实测**（肋角落在实测壳面外 1.70）；**8 点扫描改 16 点**抓到了真问题：
      肋 7 从 9.78 跳到 10.52，通风凸包正好落在 22.5° 的采样盲区里。
      线圈舱与枪口舱**故意不上侧轨**（12.7 studs 的站点拉直线要半径 14，会读成一个圈），
      而且这条由**测试强制**而非靠注释：中段射线超过端头 1.00 就拒绝该舱。
      幂等、可逆（`DeleteFrame` / `RevertAll`）；名字、标签、`ClickDetector` 一个没动，
      全部 `CanCollide/CanQuery/CanTouch = false`。"""

BULLET_B = """- [ ] **控制台二次重做（含冷却液校准）** —— 用户 2026-09-23 指定：排在 CBL 二次重做之后、
      其余任务之前。Mk2 台子被评价「太丑」，而**冷却液校准**（`coolant_recalibrate`，
      Wiki 记该传感器设备「有不可靠的倾向」、需要「手动干预校准」）需要一个像样的实体交互点。
      **动手前必须先量**：六台现状件数（433 / 376 / 334 / 370 / 327 / 61）、控件在台面上的分布、
      以及 `coolant_recalibrate` 此刻绑在哪个部件上 —— 不凭印象改。"""

BULLET_C = """- [x] **Studio 截图可以直达 —— 上一条记录是错的，已更正（2026-09-23）。** 原记录说
      `capture_screenshot` 只把图片**内联**返回、不落盘，而 sidecar 只认「路径 / URL / data URL」，
      「两边接不上」。**实测：`rblx_screen_capture` 返回的图在本会话里直接可见** ——
      不需要 sidecar、不需要落盘，本轮 CBL 二次重做的两张验收图就是这么看的。
      仍然成立的两点：`describe_image` 确实只认路径/URL；
      `PreloadAsync` 的逐资源回调在命令栏 VM 里确实不触发（70 个全 `NO-CALLBACK`），别指望它。"""


def find_unique(raw, key):
    n = raw.count(key)
    if n != 1:
        raise SystemExit("*** key %r occurs %d times ***" % (key, n))
    return raw.find(key)


def insert_after_line(raw, key, text):
    """Insert `text` as a new line immediately after the line containing key."""
    pos = find_unique(raw, key)
    nl = raw.find(b"\n", pos)
    if nl < 0:
        raise SystemExit("*** no newline after key %r ***" % key)
    return raw[:nl + 1] + text.encode("utf-8") + b"\n" + raw[nl + 1:]


def replace_lines(raw, key, n, text):
    """Replace the n lines starting with the one containing key."""
    pos = find_unique(raw, key)
    start = raw.rfind(b"\n", 0, pos) + 1
    end = start
    for _ in range(n):
        nxt = raw.find(b"\n", end)
        if nxt < 0:
            raise SystemExit("*** ran off the end of the file ***")
        end = nxt + 1
    return raw[:start] + text.encode("utf-8") + b"\n" + raw[end:]


def main():
    raw = io.open(P, "rb").read()
    before = len(raw)
    raw = insert_after_line(raw, b"4.78", BULLET_A)
    raw = insert_after_line(raw, "**未开始：**".encode("utf-8"), BULLET_B)
    raw = replace_lines(raw, b"vision sidecar", 4, BULLET_C)
    io.open(P, "wb").write(raw)

    h = 0
    for b in raw:
        h = (h * 31 + b) & 0x7FFFFFFF
    print("docs/TODO.md %d -> %d bytes" % (before, len(raw)))
    print("sections:", sorted(set(l[:5] for l in raw.split(b"\n") if l.startswith(b"## "))))


if __name__ == "__main__":
    main()
