#!/usr/bin/env python
"""continuation_ring_check.py -- measure the drawn ring IN THE PIXELS, against the
brand asset's own ring.

WHY THIS EXISTS.  The layout judge (continuation_judge.js) decides C6 from a
number the page reports and a number this module would otherwise also hold as a
literal -- and a constant that appears in both the producer and the checker goes
red when either one moves, but stays GREEN when both move together, which is
exactly the shape of "the drawn ring is at the brand ring's radius" being false
for a whole redesign (CLAUDE.md 0.31 (6): a check that compares a result to the
constant that produced it).

So this instrument holds no radius constant at all.  It reads:

  * the ASSET's ring radius out of intro/assets/sm-core.png -- alpha >= 128,
    1440 rays per radius, take the longest band whose coverage is >= 90%;
  * the DRAWN ring's radius out of the delivered PNG -- brightness >= T, same
    rays, inside the box the page gives the emblem;
  * and the DRAWN ring's OPENING, again from pixels: the angular run inside that
    band that has no ink.

The two radii have to agree.  That is a statement about the picture, made
without either file's constants.

It also doubles as the reading for the operator's half of the Phase 150 request
("你TRG也要有一定体现"): the ink INSIDE the clip radius is the asset's own
drawing, and cover_mark_check.py proves it is the asset pixel-for-pixel.

  python -B _tools/continuation_ring_check.py
  SHOT=cover/THE_REACTOR_GAME_continuation_icon.png python -B _tools/continuation_ring_check.py

Environment (defaults are cover/continuation.html's values):
  SHOT   delivered PNG
  ART    brand asset
  BOX_X BOX_Y BOX   the box the page gives the emblem, in design pixels

Exit 0 when every reading is inside its band, 1 otherwise.  The bands are
stated in BAND below with the reason for each width.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path_of(env, default):
    p = os.environ.get(env) or default
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


SHOT  = path_of("SHOT",  os.path.join("cover", "THE_REACTOR_GAME_continuation_icon.png"))
ART   = path_of("ART",   os.path.join("intro", "assets", "sm-core.png"))
BOX_X = int(os.environ.get("BOX_X") or 262)
BOX_Y = int(os.environ.get("BOX_Y") or 165)
BOX   = int(os.environ.get("BOX")   or 500)

ALPHA   = 128      # "this asset pixel is ink"
T       = 120      # "this rendered pixel is ink"
RAYS    = 1440     # 0.25 deg
SCAN    = (200, 252)   # radius window, in design px, where the ring can be
# A radius belongs to the ring if this much of it is inked.  TWO thresholds,
# because the two rings are not the same thing: the asset's ring is closed, so a
# radius inside it is inked all the way round (0.90 leaves room for the asset's
# own antialiasing); the DRAWN ring is open on purpose, and a closed ring is
# 1.0 at the same radius -- so asking the drawn ring for 0.90 would be a check
# that only a FAILED design can pass once the gap is past 36 degrees.  (First
# run of this file did exactly that: "nothing is drawn out there" on a ring that
# is plainly on the picture.  The opening has its own measurement below, so a
# lower threshold here costs nothing.)
ASSET_COVER = 0.90
DRAW_COVER  = 0.70

# Every band is "how far off can a correct build be", never "what did this build
# read".  Measured margins on the Phase 150 build are printed next to each one.
BAND = {
    "radius_px": 3.0,        # the ring's own antialiasing is ~1 px each side (measured 0.22 off)
    "opening_deg": (25, 80), # the CLEAR opening: the path's 56 minus the head's 15.6 (measured 39.4).
                             # A closed ring reads 0 and a head that fills the gap reads 0 too.
}


def profile(pixels, cx, cy, rmax, is_ink):
    """For each integer radius, the fraction of RAYS that are ink at that radius."""
    out = []
    for r in range(0, rmax + 1):
        hit = 0
        for i in range(RAYS):
            a = 2 * math.pi * i / RAYS
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            if 0 <= y < pixels.shape[0] and 0 <= x < pixels.shape[1] and is_ink(pixels, x, y):
                hit += 1
        out.append(hit / RAYS)
    return out


def longest_band(prof, lo_floor, cover):
    """The longest contiguous run of radii whose coverage >= cover, above lo_floor."""
    best = None
    start = None
    for r, c in enumerate(prof):
        if r < lo_floor:
            start = None
            continue
        if c >= cover:
            if start is None:
                start = r
        elif start is not None:
            if best is None or (r - start) > (best[1] - best[0]):
                best = (start, r - 1)
            start = None
    if start is not None and (best is None or (len(prof) - 1 - start) > (best[1] - best[0])):
        best = (start, len(prof) - 1)
    return best


def clear_opening(pixels, cx, cy, r_in, r_out, is_ink):
    """The longest run of angles with NO ink anywhere between r_in and r_out, in degrees.

    This is NOT the path's gap, and the difference is not noise: the arrowhead is
    ink, and its base sits on the ring, so it eats its own arc length out of the
    opening.  On the Phase 150 build the path's gap is 56 deg and this reads
    39.4 -- 56 minus the head's 66 px, which at r=242.2 is 15.6 deg, minus about
    1 deg of antialiasing at the band's edges.  Two instruments, two numbers,
    and the arithmetic between them is stated rather than smoothed over.

    (The run is measured on a DOUBLED array so an opening that straddles 0 deg
    is one run, not two halves that each look small.)"""
    n = 2880                       # 0.125 deg, finer than the band we can resolve
    hit = []
    for i in range(n):
        a = 2 * math.pi * i / n
        any_ink = False
        for r in range(int(r_in), int(r_out) + 1):
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            if 0 <= y < pixels.shape[0] and 0 <= x < pixels.shape[1] and is_ink(pixels, x, y):
                any_ink = True
                break
        hit.append(any_ink)
    if all(hit):
        return 0.0
    if not any(hit):
        return 360.0
    best = 0
    run = 0
    for i in range(2 * n):         # doubled: a run that wraps is still one run
        if not hit[i % n]:
            run += 1
            if run > best:
                best = run
        else:
            run = 0
    return min(best, n) * 360.0 / n


def main():
    art = np.array(Image.open(ART).convert("LA").getchannel("A")).astype(np.int16)
    ah, aw = art.shape
    prof_a = profile(art, (aw - 1) / 2.0, (ah - 1) / 2.0, min(258, aw // 2),
                     lambda p, x, y: p[y, x] >= ALPHA)
    band_a = longest_band(prof_a, 200, ASSET_COVER)
    if not band_a:
        raise RuntimeError("no ring band found in %s -- the asset changed" % ART)
    r_art = (band_a[0] + band_a[1]) / 2.0
    w_art = band_a[1] - band_a[0] + 1

    shot = np.array(Image.open(SHOT).convert("RGB")).astype(np.int16).max(axis=2)
    box = shot[BOX_Y:BOX_Y + BOX, BOX_X:BOX_X + BOX]
    if box.shape != (BOX, BOX):
        raise RuntimeError("the box %dx%d at (%d,%d) does not fit a %dx%d image"
                           % (BOX, BOX, BOX_X, BOX_Y, shot.shape[1], shot.shape[0]))
    scale = BOX / float(aw)                       # asset px -> design px
    prof_s = profile(box, (BOX - 1) / 2.0, (BOX - 1) / 2.0,
                     min(SCAN[1], BOX // 2 - 1), lambda p, x, y: p[y, x] >= T)
    band_s = longest_band(prof_s, int(SCAN[0]), DRAW_COVER)
    if not band_s:
        raise RuntimeError("no ring band found in %s -- nothing is drawn out there" % SHOT)
    r_draw_px = (band_s[0] + band_s[1]) / 2.0
    w_draw_px = band_s[1] - band_s[0] + 1
    r_draw_art = r_draw_px / scale                # report both in ASSET pixels
    w_draw_art = w_draw_px / scale

    gap_deg = clear_opening(box, (BOX - 1) / 2.0, (BOX - 1) / 2.0,
                            band_s[0] - 1, band_s[1] + 1,
                            lambda p, x, y: p[y, x] >= T)

    print("%s" % SHOT)
    print("  box %dx%d at (%d,%d), asset scale %.4f design px per asset px"
          % (BOX, BOX, BOX_X, BOX_Y, scale))
    print("")
    print("  asset %dx%d: ring band r %d..%d  -> centre %.1f, width %d  (asset px)"
          % (aw, ah, band_a[0], band_a[1], r_art, w_art))
    print("  drawing:     ring band r %d..%d in the box -> %.2f canvas / %.1f asset px"
          % (band_s[0], band_s[1], r_draw_px, r_draw_art))
    print("")

    d_r = r_draw_art - r_art
    d_w = w_draw_art - w_art
    ok_r = abs(d_r) <= BAND["radius_px"]
    ok_w = abs(d_w) <= BAND["radius_px"]
    ok_g = BAND["opening_deg"][0] <= gap_deg <= BAND["opening_deg"][1]

    print("  radius   drawn %.1f - asset %.1f = %+.2f asset px   (band +-%.1f)   %s"
          % (r_draw_art, r_art, d_r, BAND["radius_px"], "ok" if ok_r else "FAIL"))
    print("  width    drawn %.1f - asset %.1f = %+.2f asset px   (band +-%.1f)   %s"
          % (w_draw_art, w_art, d_w, BAND["radius_px"], "ok" if ok_w else "FAIL"))
    print("  opening  %.2f deg of the drawn ring has no ink  (band %.0f..%.0f)   %s"
          % (gap_deg, BAND["opening_deg"][0], BAND["opening_deg"][1], "ok" if ok_g else "FAIL"))
    print("")
    print("  The opening is measured from pixels and knows nothing about the page's")
    print("  GAP_FROM/GAP_TO; the layout judge measures the path.  Two instruments,")
    print("  one number each -- that is what makes them able to disagree.")
    print("  They measure DIFFERENT quantities on purpose: this one is the opening a")
    print("  viewer sees, and the head is ink, so it reads gap-minus-head.  A closed")
    print("  ring reads 0 here no matter what the path says.")
    return 0 if (ok_r and ok_w and ok_g) else 1


if __name__ == "__main__":
    try:
        rc = main()
    except SystemExit:
        raise
    except BaseException:            # noqa: BLE001 -- CLAUDE.md 0.6: an uncaught
        import traceback             # exception here can leave rc = 0, and then
        traceback.print_exc()        # "the checker crashed" looks byte-for-byte
        sys.exit(1)                  # like "all clear".
    sys.exit(rc)
