"""Two measurements, both of them "open a PNG and read the numbers".

WHY THIS FILE EXISTS.  Phase 132's first cover had five decorative layers and the
page rendered fine, the layout judge was green, and two separate vision reads
said "there are no stripes" in exactly the tone they'd use if the design had
never had stripes.  Measuring the pixels instead of the styles split that into
two different failures:

  layer        old construction              vs that layer switched off
  titleBand    black art + screen, no invert 0 px, max delta 0    <- not drawn
  hazard       same                         0 px, max delta 2    <- not drawn
  hexes        white art + invert(1)         8480 px, max delta 3   (fixed: 24)
  smMark       white art + invert(1)          138 px, max delta 35  (fixed: 54)

Two of them contributed exactly nothing -- `screen(base, 0) == base`, so a black
asset under `mix-blend-mode:screen` blends the backdrop with itself.  The other
two were present but at 1%-14% of their intended amplitude, which is why the
honest description of those two is "wrong polarity", not "missing".  Nothing
errored in any of the four cases.  CLAUDE.md 0.18: the wrong measurement is quiet.

Part 1 below reads the SOURCE assets and reports each one's polarity -- because
"does this layer need invert" is a property of the asset, and it was the one
thing never measured.  Part 2 reads the RENDER and compares a layer-off render
against the full one.

PHASE 134 CUT THE COVER TO FOUR ELEMENTS, so both halves shrank with it: the
asset list is down to the two marks this page draws, and cover_layers.sh renders
four layer-off frames instead of six.  The table above stays as it was written --
it is what THAT build measured, and the two zero-contribution layers it names are
gone from the page rather than fixed in place.

  python -X utf8 _tools/cover_layer_probe.py <full.png> <off_*.png> ...

The layer-off renders are produced by _tools/intro_render.js with an --eval that
sets that one layer's opacity to 0; run it via _tools/cover_layers.sh, which
re-renders the deliverable first so both sides of every diff come from one build.

WHY IT LIVES IN _tools/ AND NOT IN _attic/scratch/.  It was written into the
scratch pile and then three documents started citing it as the command to re-run
("复量这条跑道").  A recipe that points at a throwaway is a recipe that stops
working the next time the throwaway is swept up -- and the scratch pile is
exactly where 45 other scripts sit waiting to be swept.  The renders it compares
stay in scratch, because they regenerate; the comparer does not, because it is
what the docs call.
"""
import os
import sys

from PIL import Image

# Derived, not typed: this file is what the docs cite, so it has to work from any
# working directory (`bash _tools/cover_layers.sh` runs from the repo root, but
# nothing guarantees the next caller does).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The threshold is per channel, out of 255.  A truly invisible layer differs by
# exactly 0 (same paint), so even a small threshold separates "changed nothing"
# from "changed something" -- the number printed is the max delta, so a layer
# scraping along at 3 is visible in the report rather than silently passing.
DELTA = 2


def polarity():
    print("--- source assets: is the line art white or black? ---")
    # PHASE 149: a page with NO raster assets (the continuation icon is pure
    # SVG + CSS) has nothing to measure here, and printing the cover's two rows
    # would be a table about a different picture.  ASSETS="" says so out loud
    # instead of quietly reporting two assets that are not on this page.
    #   ASSETS="" PAGE=cover/continuation.html ... bash _tools/cover_layers.sh
    if "ASSETS" in os.environ:
        assets = tuple(a for a in os.environ["ASSETS"].split(",") if a.strip())
        if not assets:
            print("  (this page draws no raster assets -- ASSETS=\"\" -- nothing to measure)")
            return []
    else:
        assets = ("intro/assets/sm-core.png", "intro/assets/sm-logo.png")
    rows = []
    # Phase 134: this list follows the LAYERS this page actually has.  stripes /
    # nested-hex / hex / px / sm-core's siblings went with the layers that used
    # them (see cover_layers.sh); what is left is the two marks.  Re-adding a
    # layer means re-adding its asset here -- the point of the list is that the
    # `data-art` declaration in cover/index.html has a command behind it.
    for rel in assets:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        im = Image.open(p).convert("RGBA")
        px = [c for c in im.get_flattened_data() if c[3] > 8]
        if not px:
            rows.append((rel, "FULLY TRANSPARENT", "", ""))
            continue
        n = len(px)
        m = tuple(sum(c[i] for c in px) / n for i in range(3))
        a = sum(c[3] for c in px) / n
        kind = "white" if min(m) > 128 else ("black" if max(m) < 64 else "MIXED")
        rows.append((rel, "rgb(%.0f,%.0f,%.0f)" % m, "alpha %.0f" % a, kind))
    w = max(len(r[0]) for r in rows)
    for rel, rgb, a, kind in rows:
        print("  %-*s  %-22s %-11s -> %s" % (w, rel, rgb, a, kind))
    return rows


def diff(full_path, off_path):
    a = Image.open(full_path).convert("RGB")
    b = Image.open(off_path).convert("RGB")
    if a.size != b.size:
        return None
    pa, pb = a.load(), b.load()
    W, H = a.size
    n = 0
    mx = 0
    bx = [W, H, -1, -1]
    for y in range(H):
        for x in range(W):
            ca, cb = pa[x, y], pb[x, y]
            d = max(abs(ca[i] - cb[i]) for i in range(3))
            if d > mx:
                mx = d
            if d > DELTA:
                n += 1
                if x < bx[0]:
                    bx[0] = x
                if y < bx[1]:
                    bx[1] = y
                if x > bx[2]:
                    bx[2] = x
                if y > bx[3]:
                    bx[3] = y
    return n, mx, bx


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    polarity()
    full = sys.argv[1]
    print("--- does each decorative layer change any pixel? ---")
    bad = 0
    for off in sys.argv[2:]:
        layer = os.path.splitext(os.path.basename(off))[0]
        if layer.startswith("off_"):
            layer = layer[4:]
        r = diff(full, off)
        if r is None:
            print("  %-10s SIZE MISMATCH" % layer)
            bad += 1
            continue
        n, mx, bx = r
        if n == 0:
            bad += 1
            print("  %-10s NO-OP: 0 pixels changed (max delta %d)" % (layer, mx))
        else:
            print("  %-10s %7d px changed (max delta %3d) in x[%d..%d] y[%d..%d]"
                  % (layer, n, mx, bx[0], bx[2], bx[1], bx[3]))
    print("  %s: %d layer(s) changed nothing"
          % ("FAIL" if bad else "ok", bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
