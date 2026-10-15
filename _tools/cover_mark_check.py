#!/usr/bin/env python
"""cover_mark_check.py -- is the hero mark actually DRAWN in the hexagon, or is it a blob?

Phase 133 replaced the cover's in-game screenshot with a manufacturer's mark
(intro/assets/sm-core.png).  cover_layers.sh already proves the new layer changes
pixels; that is a different question from "are the pixels the ASSET".  A layer that
painted one flat white square over the box would pass every other instrument on this
runway -- the layout judge never looks at pixels, and the layer probe only asks
whether switching the layer off changes anything.

So: rasterise the asset's own alpha into the box the page gives it, threshold the
delivered render, and count both directions.

WHAT THIS MEASURES, AND WHAT IT CANNOT
  The output is a SWEEP, not a pair, because on this page there is no threshold that
  makes both directions clean -- and that is a fact about the page, not about the
  checker.  The asset draws white ink on transparency, so ink comes out bright; but
  the box also carries the hero hexagon's own outline and the mark's drop-shadow.
  Measured on the Phase 134 build: the mark's dimmest ink is 142 and the brightest
  non-ink pixel is 159, so the two populations OVERLAP in brightness and no single
  cut separates them.  Precision therefore has a denominator this instrument cannot
  clean.

  (Phase 133 ran the same instrument on a busier page and the whole mark read dimmer
  -- ink p1/median 95/189 against 142/217 here -- with the outermost radial band at
  80.7%.  The first write-up blamed the two HUD readouts sitting on the outer ring.
  That is not the shape the darkening has: measured on Phase 133's own frame, the dark
  ink falls in two BANDS (box y 350..420 and y 0..70, x 70..350) while the ring's 3- and
  9-o'clock sides are clean -- so it was #hexTint's own 180deg gradient (42% black at the
  top, 55% at the bottom), the black text-shadow on each .hud/.hudv line, and that
  build's opacity .88, all pushing the same way, and how much each contributed was NOT
  separated.  See docs/COVER.md section 4 and DECISIONS_2 573.)

  What survives, and is what the docs quote:
    * recall -> "the whole mark is on the picture".  At t<=80 every one of the
      44663 ink pixels in the box came out bright (recall 1.0000; 4 px short at 100).
      That is the claim that separates "the art is drawn" from "a bright blob is".
    * the radial table -> WHERE any ink went dim.  At t=120 every band from r 0.0 to
      r 1.0 reads 99.7%-100%: the drawing is present all the way out to the outer
      ring.  Phase 133's build read 80.7% in that outermost band; removing the elements
      that were stacked over this box is what paid for the reading coming back.
    * precision is printed too, but it is a reading about the BOX, not about the mark.

  python -X utf8 _tools/cover_mark_check.py [threshold]     (default 120)

Numbers quoted in docs/COVER.md section 4 and PROGRESS.md Phase 133 / 134.
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT = os.path.join(ROOT, "cover", "THE_REACTOR_GAME_cover.png")
ART = os.path.join(ROOT, "intro", "assets", "sm-core.png")

BOX = 420                      # MARK_D in cover/index.html
BOX_X = 330                    # HEX_CX(540) - BOX/2
BOX_Y = 194                    # HEX_CY(404) - BOX/2
ALPHA = 128                    # "this pixel is ink" in the asset
SWEEP = (60, 80, 100, 120, 150, 180, 200, 220, 240)
DEFAULT_T = 120


def load():
    shot = np.array(Image.open(SHOT).convert("RGB")).astype(np.float64)
    crop = shot[BOX_Y:BOX_Y + BOX, BOX_X:BOX_X + BOX]
    # the page draws a white line drawing, so "bright" == any channel above the
    # threshold; luminance reads the same here but is one more thing to trust.
    return crop.max(axis=2)


def asset_ink():
    """The asset's drawing lives in ALPHA (LA image; every pixel is rgb(255,255,255)).

    Converting it to "L" throws the drawing away and hands back a white square --
    which reads as "the entire box is ink" (precision 1.0000, recall 0.27).  That
    reading is not wrong about the file, it answers a different question.
    """
    a = Image.open(ART).convert("LA").getchannel("A")
    return np.array(a.resize((BOX, BOX), Image.BILINEAR)).astype(np.float64) > ALPHA


def radial(hit, ink):
    """Of the ink in each radial bucket, how much came out bright."""
    n = ink.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx - (n - 1) / 2.0, yy - (n - 1) / 2.0) / ((n - 1) / 2.0)
    rows = []
    for i in range(10):
        band = (r >= i / 10.0) & (r < (i + 1) / 10.0)
        # numerator must be a SUBSET of the denominator: "bright AND ink" over ink.
        # Dividing the whole band's bright count by its ink count gave >100% buckets
        # the first time this ran -- an instrument that reports 201% of a subset.
        tot = int((band & ink).sum())
        if tot:
            rows.append((i / 10.0, (i + 1) / 10.0, float((hit & band & ink).sum()) / tot, tot))
    return rows


def main(t=DEFAULT_T):
    mx = load()
    ink = asset_ink()
    print("%s  box %dx%d at (%d,%d)  ink alpha>%d" % (SHOT, BOX, BOX, BOX_X, BOX_Y, ALPHA))
    print("ink %d px (%.2f%% of the box)\n" % (ink.sum(), 100.0 * ink.sum() / ink.size))

    print("  t     bright      tp      fp      fn   precision   recall")
    for tt in SWEEP:
        b = mx > tt
        tp = int((b & ink).sum())
        fp = int((b & ~ink).sum())
        fn = int((~b & ink).sum())
        print("  %3d  %8d  %6d  %6d  %6d     %.4f    %.4f"
              % (tt, int(b.sum()), tp, fp, fn,
                 tp / (tp + fp) if tp + fp else float("nan"),
                 tp / (tp + fn) if tp + fn else float("nan")))

    print("\nwhy no threshold is clean:")
    print("  ink     brightness  1%%/5%%/50%%/95%%/99%% = %s"
          % np.percentile(mx[ink], [1, 5, 50, 95, 99]).round(0).astype(int).tolist())
    print("  not-ink brightness    50%%/90%%/99%%/max  = %s"
          % np.percentile(mx[~ink], [50, 90, 99, 100]).round(0).astype(int).tolist())
    ys, xs = np.nonzero((mx > 200) & ~ink)
    if len(ys):
        rows = sorted(set((ys // 20).tolist()))
        print("  the brightest non-ink object: %d px above 200, in y-bands %s of the box"
              % (len(ys), rows))

    b = mx > t
    print("\nat t = %d (the default):" % t)
    print("  ink that is bright, by radius from the box centre:")
    for lo, hi, frac, tot in radial(b, ink):
        print("    r %.1f-%.1f  %5.1f%%   (%d ink px)" % (lo, hi, 100.0 * frac, tot))
    return 0


if __name__ == "__main__":
    try:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_T)
    except SystemExit:                  # let a deliberate exit through untouched
        raise
    except BaseException:               # noqa: BLE001 -- see CLAUDE.md 0.6: an
        import traceback                # uncaught exception can leave rc = 0, and
        traceback.print_exc()           # "the checker crashed" then looks
        sys.exit(1)                     # byte-for-byte like "all clear".
    sys.exit(0)
