# -*- coding: utf-8 -*-
"""Same interior anchors as the Studio read-back, disk side, to pin the §3.1 divergence."""
import io

D = r"D:\rblxTRGproject"
MARKS = ["- [x] 灯光大修", "- [x] 控制台几何体", "- [x] `SurfaceGui`",
         "- [x] **圆按钮改为平放**", "- [x] **整机就位**", "- [x] **七台监视器就地重建**",
         "- [x] **Log / Forecast 屏接上**", "- [x] **三台 CBL 激光翻新**",
         "**未开始：**", "- [ ] 监视器**屏幕内容**", "- [ ] 设施外壳", "- [ ] 英雄资产用",
         "- [x] **常态氛围 VFX", "- [~] 材质分区的细化", "- [x] **整体调子转向更暗**",
         "- [x] **主监视器示意图接上实时数据**", "**回退手段：**"]

MOD = [x.split() for x in """23988 6e555a5e | 24032 5d8acd67 | 24212 0d22869b | 24314 20dc5a5a | 24461 61c07fb9 | 24778 583e7268 | 24908 7e45354c | 24996 7a0b5cf1 | 26056 44f9a233 | 26073 448ec5de | 26278 5a82bc6d | 28004 66579fc6 | 28079 0c3f0650 | 28942 5d4a6af9 | 29947 75e1e25c | 30934 6b7233a2 | 31306 5c982d09""".replace(" | ", "|").split("|")]


def roll(bs):
    h = 0
    for b in bs:
        h = (h * 31 + b) & 0x7FFFFFFF
    return h


raw = io.open(D + r"\CLAUDE.md", "rb").read()
body = raw[:327] + raw[1653:]

print("%-40s %-10s %-10s" % ("anchor", "module", "disk"))
for k, m in enumerate(MARKS):
    i = body.find(m.encode("utf-8"))
    moff, mh = int(MOD[k][0]), MOD[k][1]
    if i < 0:
        print("%-40s %s @%d  DISK MISS" % (m, mh, moff))
        continue
    dh = roll(body[:i])
    tag = "ok" if (dh == int(mh, 16)) else "**DIFF**"
    print("%-40s %s @%-6d %08x @%-6d %s" % (m, mh, moff, dh, i, tag))
