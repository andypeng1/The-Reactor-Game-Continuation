"""Contact sheet of every image the cover could draw from, with the name burned in.

Why a sheet and not ten separate looks: the vision bridge answers one question per
call, and the question this round is *relative* -- which of these reads as the
game's mark, which is a texture, which is a photo.  Seeing them side by side at a
common height is what answers that; ten crops at ten scales do not.

Background is mid-grey on purpose: these assets are white-on-transparent line art
(inverted to white by the CSS), so on black they vanish and on white a white line
vanishes too.  Mid-grey is the only plate where every one of them is legible.
"""
import os
from PIL import Image, ImageDraw

ROOT = r"D:\rblxTRGproject"
OUT = os.path.join(ROOT, "_tools", "_attic", "scratch", "contact_sheet.png")

ITEMS = [
    ("intro/assets/sm-logo.png", "sm-logo"),
    ("intro/assets/sm-core.png", "sm-core"),
    ("intro/assets/nested-hex.png", "nested-hex"),
    ("intro/assets/ring.png", "ring"),
    ("intro/assets/stripes.png", "stripes"),
    ("intro/assets/hex.png", "hex"),
    ("intro/assets/alert.png", "alert"),
    ("promo/shots/ig4_core.jpg", "ig4_core"),
    ("promo/shots/ig2_chamber_on.jpg", "ig2_chamber_on"),
    ("Data/startup_shots/3_lit_ignition.jpg", "3_lit_ignition"),
]

CELL_W, CELL_H = 420, 300
PAD, LABEL = 12, 22
COLS = 4
ROWS = (len(ITEMS) + COLS - 1) // COLS
W = COLS * (CELL_W + PAD) + PAD
H = ROWS * (CELL_H + LABEL + PAD) + PAD

sheet = Image.new("RGB", (W, H), (96, 100, 104))
d = ImageDraw.Draw(sheet)

for i, (rel, name) in enumerate(ITEMS):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    cx = PAD + (i % COLS) * (CELL_W + PAD)
    cy = PAD + (i // COLS) * (CELL_H + LABEL + PAD)
    if not os.path.exists(p):
        d.text((cx + 6, cy + 6), name + " MISSING", fill=(255, 60, 60))
        continue
    im = Image.open(p)
    im.load()
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        # alpha -> checkerboard so "is this a cutout" is visible
        plate = Image.new("RGB", im.size, (70, 74, 78))
        for y in range(0, im.size[1], 24):
            for x in range(0, im.size[0], 24):
                if (x // 24 + y // 24) % 2 == 0:
                    plate.paste((118, 122, 126), (x, y, min(x + 24, im.size[0]), min(y + 24, im.size[1])))
        plate.paste(im, (0, 0), im)
        im = plate
    else:
        im = im.convert("RGB")
    im.thumbnail((CELL_W, CELL_H), Image.LANCZOS)
    ox = cx + (CELL_W - im.size[0]) // 2
    oy = cy + (CELL_H - im.size[1]) // 2
    sheet.paste(im, (ox, oy))
    d.rectangle([cx - 1, cy - 1, cx + CELL_W, cy + CELL_H], outline=(30, 32, 34))
    d.text((cx, cy + CELL_H + 4), "%s  (%dx%d)" % (name, im.size[0], im.size[1]), fill=(255, 255, 255))

sheet.save(OUT)
print("wrote", OUT, sheet.size)
