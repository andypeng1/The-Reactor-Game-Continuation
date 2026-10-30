#!/usr/bin/env python
"""rebuild_pieces_check.py -- read the Rebuild icon's claims off the INK.

The layout judge (_tools/rebuild_judge.js) reads the SVG paths the page built:
the ring sweeps 304 deg, the part sweeps 56 deg, the part sits 54 px further out.
Those are readings of the *drawing instructions*.  This file reads the
*delivered PNG* and holds no geometry constant from cover/rebuild.html at all --
so the two can disagree, and disagreeing is the only reason to have two.

Four questions, all answered from pixels:

  1. RING RADIUS.  The brand asset's ring radius, measured from
     intro/assets/sm-core.png, vs the drawn ring's radius, measured from the
     shot.  Same method as _tools/continuation_ring_check.py, so the icons'
     numbers stay comparable.
  2. HOW MANY BAYS.  Angular runs inside the ring band with no ink.  A ring that
     closes reads 0; a ring cut twice reads 2; a ring cut once reads 1.
  3. THE PART.  Found by COLOUR, not by radius -- it is amber and everything else
     out there is grey or cyan -- so a part that was carried to the wrong radius,
     or pasted back into its slot, is still FOUND and still measured.  Then: is
     it outside the ring, is it as thick as the ring, is it as wide as the bay,
     is it aimed at the bay.
  4. THE COLOURS.  The ring's mean colour is neutral; the part's mean colour is
     amber.  This is the independent half of the judge's R13 (DECISIONS_2 655: a
     rule's two halves need two sources, or "both files moved together" stays
     green).

Bands are dimensionless wherever they can be: the air between ring and part in
ring widths, the part's thickness against the ring's own thickness.  The one
absolute band is the ring radius, and its width is the antialiasing that
produced it.

Two measurement notes, both of which cost a round:

  * The box the page gives the EMBLEM only locates the centre.  The scan covers
    the whole canvas: the part is deliberately carried OUTSIDE that box.  (First
    version cropped to it and reported "the part is not on the picture" on a
    picture that plainly has it -- CLAUDE.md 0.18, a wrong measurement does not
    report an error.  The part's leftmost ink is x~208; the emblem box starts at
    x=262.)
  * Angular extent is measured by SAMPLING RAYS, never by binning each pixel's
    angle.  Binning left an empty 0.125 deg bin at exactly 180 deg -- at the
    arc's leftmost point the raster puts pixels at 179.90 and 180.10 and nothing
    at 180.00 -- so one 56 deg arc came back as two runs of 19.6 and 35.6
    (CLAUDE.md 0.20 (2): a boundary that lands on the data splits a run in a way
    that looks exactly like a real gap).

  python -B _tools/rebuild_pieces_check.py
  SHOT=cover/THE_REACTOR_GAME_rebuild_icon.png python -B _tools/rebuild_pieces_check.py

Environment (defaults are cover/rebuild.html's build):
  SHOT ART BOX_X BOX_Y BOX

Exit 0 when every reading is inside its band, 1 otherwise -- including a crash
(CLAUDE.md 0.6: an uncaught exception here can leave rc = 0, and then "the
checker crashed" looks byte-for-byte like "all clear").
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


SHOT  = path_of("SHOT",  os.path.join("cover", "THE_REACTOR_GAME_rebuild_icon.png"))
ART   = path_of("ART",   os.path.join("intro", "assets", "sm-core.png"))
BOX_X = int(os.environ.get("BOX_X") or 262)
BOX_Y = int(os.environ.get("BOX_Y") or 165)
BOX   = int(os.environ.get("BOX")   or 500)

ALPHA       = 128     # "this asset pixel is ink"
T           = 120     # "this rendered pixel is ink" (grey ring ~217, amber part ~225)
RAYS        = 2880    # 0.125 deg
ASSET_COVER = 0.90    # the asset's ring is closed; 0.90 leaves its antialiasing room
DRAW_COVER  = 0.70    # the drawn ring is OPEN on purpose (see continuation_ring_check.py)

# Amber, as Config.Visual.Amber = (255,128,1) survives being rendered over a near
# black background: the arc reads ~(220,112,2).  A cone, not an equality, because
# the arc has a blurred drop-shadow under it and antialiased edges.  It has to
# separate amber from the ring's neutral grey (~217,218,218) and from the cyan
# glow (~82,218,226) -- both by a wide margin, which is what the printed means
# are for.
AMBER = dict(r_min=110, r_minus_b=70, r_minus_g=40)

# A radius belongs to the part if it carries this many amber pixels.  The part is
# an ARC: at its radii a 56 deg sweep at r~296 is ~290 px.  The guide line is the
# same colour but runs radially, so it contributes 2-3 px at any one radius, and
# it is dashed on top of that.  30 is an order of magnitude from the guide and
# another from the part.
PART_RUN = 30

# Every band is "how far off can a correct build be", never "what did this build
# read".  Measured margins on this build are printed next to each one.
BAND = {
    "radius_asset_px": 3.0,      # the ring's own antialiasing, ~1 px a side (measured 0.22)
    "bays": 1,                   # a ring with nothing missing is a finished badge
    "bay_deg": (40, 70),         # the drawn bay is 56; leaves room for the drop-shadow's edge
    # The part and the ring carry the same stroke, so their measured thicknesses
    # should be the same -- but each is found by a different edge criterion (the
    # ring by a 0.70 coverage threshold, the part by an amber mask that includes
    # some of its drop-shadow), and that bias is an absolute ~2 OUTPUT pixels at
    # either scale.  So the reading is the DIFFERENCE, not the ratio.  (First
    # version used a ratio and passed on the 1024 master at 1.143 but failed the
    # 512 at 1.286 -- the ring shrank with the file and the +2 px did not.
    # CLAUDE.md 0.21: the denominator had the scale in it.)
    "thickness_delta_px": 3.0,   # part px - ring px (measured +2.0 at 1024 AND at 512)
    "air_in_ring_widths": 1.5,   # air between ring and part (measured ~2.8) -- 1.0 is "touching"
    "sweep_diff_deg": 2.0,       # part width vs bay width
    "aim_diff_deg": 1.5,         # part mid-angle vs bay mid-angle
    "ring_neutral": 20,          # max-min channel spread of the ring's mean (measured 1)
    "part_r_minus_b": 100,       # amber-ness of the part's mean (measured ~216)
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
            if 0 <= y < pixels.shape[0] and 0 <= x < pixels.shape[1] and is_ink(x, y):
                hit += 1
        out.append(hit / float(RAYS))
    return out


def longest_band(prof, lo_floor, cover):
    """The longest contiguous run of radii whose coverage >= cover, above lo_floor."""
    best, start = None, None
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


def ray_ink(shape, is_ink, cx, cy, r_in, r_out):
    """One bool per ray: is there ink anywhere between r_in and r_out on it.

    Sampling rays rather than binning pixel angles is deliberate -- see the
    module docstring.  It also costs nothing: RAYS * (r_out - r_in) lookups.
    """
    h, w = shape
    out = []
    for i in range(RAYS):
        a = 2 * math.pi * i / RAYS
        ca, sa = math.cos(a), math.sin(a)
        any_ink = False
        for r in range(int(r_in), int(r_out) + 1):
            x = int(round(cx + r * ca))
            y = int(round(cy + r * sa))
            if 0 <= y < h and 0 <= x < w and is_ink(x, y):
                any_ink = True
                break
        out.append(any_ink)
    return out


def angular_runs(hit, want=True):
    """Every maximal run of bins equal to `want`, as [(width_deg, mid_deg), ...].

    `want` is not a convenience.  The ring's bay is a run of NO ink and the
    part is a run of amber ink, and the same helper measuring both with the same
    polarity returns one right answer and one inverted one -- which is how this
    file first reported the part as "160 deg at 80 deg": that was the largest
    EMPTY stretch of the ring's orbit, read out as if it were the part.
    (CLAUDE.md 0.18 第五张脸: the function said "runs" and the caller heard
    "ink".  The number was 160 deg where 56 was expected, so it was loud; had
    the gap happened to be 56 deg it would have been silent.)

    Returns ALL runs: "how many bays" cannot be answered by the longest one.  The
    scan starts on a bin that is NOT `want`, so a run that straddles 0 deg is one
    run and not two halves that each look small.
    """
    n = len(hit)
    if all(h == want for h in hit):
        return [(360.0, 0.0)]
    if not any(h == want for h in hit):
        return []
    start_i = next(i for i in range(n) if hit[i] != want)
    runs, run = [], 0
    for k in range(n + 1):          # +1 so the closing bin flushes the last run
        if hit[(start_i + k) % n] == want:
            run += 1
        else:
            if run:
                a_lo = start_i + k - run
                runs.append((run * 360.0 / n, ((a_lo + run / 2.0) / n * 360.0) % 360.0))
            run = 0
    return runs


def main():
    # ---- 1. the asset's own ring
    art = np.array(Image.open(ART).convert("LA"))
    alpha = art[:, :, 1].astype(np.int16)
    ah, aw = alpha.shape
    # `lo_floor` is a FRACTION of the radius being searched, never a design-pixel
    # number: the first version hardcoded 200, which is right in the 1024 master
    # and above the ring entirely in the 512 upload file ("nothing is drawn out
    # there" on a picture that is the master's own downscale).  Every band here
    # has to survive the file being measured at a different scale -- CLAUDE.md
    # 0.26 (1): a decision that can fail for a reason other than the one it is
    # asking about is not a measurement.
    prof_a = profile(alpha, (aw - 1) / 2.0, (ah - 1) / 2.0, min(258, aw // 2),
                     lambda x, y: alpha[y, x] >= ALPHA)
    band_a = longest_band(prof_a, int(0.80 * min(258, aw // 2)), ASSET_COVER)
    if not band_a:
        raise RuntimeError("no ring band in %s -- the asset changed" % ART)
    r_art = (band_a[0] + band_a[1]) / 2.0
    w_art = band_a[1] - band_a[0] + 1

    # ---- the shot.  The emblem box only locates the centre; the scan is the
    # whole canvas, because the part is carried outside that box on purpose.
    rgb = np.array(Image.open(SHOT).convert("RGB")).astype(np.int16)
    H, Wd = rgb.shape[:2]
    if H < BOX_Y + BOX or Wd < BOX_X + BOX:
        raise RuntimeError("the box %dx%d at (%d,%d) does not fit a %dx%d image"
                           % (BOX, BOX, BOX_X, BOX_Y, Wd, H))
    bright = rgb.max(axis=2)
    cx = BOX_X + (BOX - 1) / 2.0
    cy = BOX_Y + (BOX - 1) / 2.0
    scale = BOX / float(aw)                       # asset px -> design px
    R_MAX = BOX // 2                              # how far out the ring can be
    R_PART = R_MAX + 90                           # how far out the part can be

    # ---- 2. the drawn ring's band
    prof_s = profile(bright, cx, cy, R_MAX, lambda x, y: bright[y, x] >= T)
    band_s = longest_band(prof_s, int(0.80 * R_MAX), DRAW_COVER)
    if not band_s:
        raise RuntimeError("no ring band in %s -- nothing is drawn out there" % SHOT)
    r_draw = (band_s[0] + band_s[1]) / 2.0
    w_draw = band_s[1] - band_s[0] + 1

    ink = lambda x, y: bright[y, x] >= T

    # ---- 3. how many bays, and where
    bay_runs = sorted(angular_runs(ray_ink(bright.shape, ink, cx, cy,
                                           band_s[0] - 1, band_s[1] + 1),
                                   want=False),
                      key=lambda t: -t[0])

    # ---- 4. colours.  Ring first: excluding the bay, so the mean is the ring.
    yy, xx = np.mgrid[0:H, 0:Wd]
    rr = np.hypot(xx + 0.5 - (BOX_X + BOX / 2.0), yy + 0.5 - (BOX_Y + BOX / 2.0))
    ring_mask = (rr >= band_s[0] + 1) & (rr <= band_s[1] - 1)
    if bay_runs:
        aa = (np.degrees(np.arctan2(yy - cy, xx - cx)) + 360) % 360
        off = np.abs(((aa - bay_runs[0][1] + 180) % 360) - 180)
        ring_mask &= off > bay_runs[0][0] / 2.0 + 2.0
    ring_mean = rgb[ring_mask].mean(axis=0)

    # ---- 5. the part: found by colour, outside the ring, anywhere
    amber = ((rgb[:, :, 0] >= AMBER["r_min"]) &
             (rgb[:, :, 0] - rgb[:, :, 2] >= AMBER["r_minus_b"]) &
             (rgb[:, :, 0] - rgb[:, :, 1] >= AMBER["r_minus_g"]))
    n_amber = int(amber.sum())
    if n_amber == 0:
        raise RuntimeError("no amber pixel anywhere in %s -- the part is not on the picture" % SHOT)
    amb = lambda x, y: bool(amber[y, x])
    part_runs = sorted(angular_runs(ray_ink((H, Wd), amb, cx, cy,
                                            band_s[1] + 1, R_PART)),
                       key=lambda t: -t[0])

    # thickness: radial extent of the radii that carry a real arc's worth of amber.
    # Measured over the whole circle, so it does not assume where the part is.
    rad = np.rint(rr).astype(int)
    counts = np.bincount(rad[amber], minlength=R_PART + 2)
    radii = np.nonzero(counts >= PART_RUN)[0]
    radii = radii[(radii > band_s[1]) & (radii <= R_PART)]
    part = None
    if radii.size:
        band_p = (int(radii.min()), int(radii.max()))
        pmask = amber & (rr >= band_p[0]) & (rr <= band_p[1])
        part = dict(r_in=float(band_p[0]), r_out=float(band_p[1]),
                    mean=rgb[pmask].mean(axis=0),
                    span=part_runs[0][0] if part_runs else 0.0,
                    mid=part_runs[0][1] if part_runs else 0.0)

    # ---- report
    print("%s" % SHOT)
    print("  emblem box %dx%d at (%d,%d) -> centre (%.1f, %.1f), asset scale %.4f design px per asset px"
          % (BOX, BOX, BOX_X, BOX_Y, cx, cy, scale))
    print("")
    print("  asset %dx%d: ring band r %d..%d -> centre %.1f, width %d  (asset px)"
          % (aw, ah, band_a[0], band_a[1], r_art, w_art))
    print("  drawing:     ring band r %d..%d -> centre %.2f design / %.1f asset px, width %d design"
          % (band_s[0], band_s[1], r_draw, r_draw / scale, w_draw))
    print("  bays:        %d gap(s) in the band: %s"
          % (len(bay_runs),
             ", ".join("%.2f deg at %.2f deg" % (w, m) for w, m in bay_runs) or "none"))
    print("  amber:       %d px; %d run(s) outside the ring band: %s"
          % (n_amber, len(part_runs),
             ", ".join("%.2f deg at %.2f deg" % (w, m) for w, m in part_runs) or "none"))
    if part:
        print("  part:        %.2f deg wide at %.2f deg, radius %.0f..%.0f design "
              "(= %.1f thick in asset px)"
              % (part["span"], part["mid"], part["r_in"], part["r_out"],
                 (part["r_out"] - part["r_in"] + 1) / scale))
        print("  means:       part rgb(%s)   ring rgb(%s)"
              % (", ".join("%.0f" % v for v in part["mean"]),
                 ", ".join("%.0f" % v for v in ring_mean)))
    else:
        print("  part:        NOT FOUND outside the ring band")
    print("")

    ok = {}
    d_r = r_draw / scale - r_art
    ok["radius"] = abs(d_r) <= BAND["radius_asset_px"]
    print("  radius    drawn %.1f - asset %.1f = %+.2f asset px   (band +-%.1f)   %s"
          % (r_draw / scale, r_art, d_r, BAND["radius_asset_px"], "ok" if ok["radius"] else "FAIL"))

    ok["bays"] = len(bay_runs) == BAND["bays"]
    print("  bays      %d, expecting %d                                       %s"
          % (len(bay_runs), BAND["bays"], "ok" if ok["bays"] else "FAIL"))

    if len(bay_runs) == 1:
        bw = bay_runs[0][0]
        ok["bay_width"] = BAND["bay_deg"][0] <= bw <= BAND["bay_deg"][1]
        print("  bay       %.2f deg  (band %.0f..%.0f)                            %s"
              % (bw, BAND["bay_deg"][0], BAND["bay_deg"][1], "ok" if ok["bay_width"] else "FAIL"))
    else:
        ok["bay_width"] = False

    if part is not None:
        ring_w = float(w_draw)
        part_w = part["r_out"] - part["r_in"] + 1.0
        air = part["r_in"] - band_s[1]

        ok["air"] = air >= BAND["air_in_ring_widths"] * ring_w
        print("  air       %.2f px between the ring's outer edge and the part "
              "= %.2f ring widths  (band >= %.1f)   %s"
              % (air, air / ring_w, BAND["air_in_ring_widths"], "ok" if ok["air"] else "FAIL"))

        d_w = part_w - ring_w
        ok["thickness"] = abs(d_w) <= BAND["thickness_delta_px"]
        print("  thickness part %.1f px - ring %.1f px = %+.1f  (band +-%.1f px)        %s"
              % (part_w, ring_w, d_w, BAND["thickness_delta_px"],
                 "ok" if ok["thickness"] else "FAIL"))

        if len(bay_runs) == 1:
            d_span = part["span"] - bay_runs[0][0]
            ok["span"] = abs(d_span) <= BAND["sweep_diff_deg"]
            print("  width     part %.2f - bay %.2f = %+.2f deg  (band +-%.1f)         %s"
                  % (part["span"], bay_runs[0][0], d_span, BAND["sweep_diff_deg"],
                     "ok" if ok["span"] else "FAIL"))
            d_aim = abs(((part["mid"] - bay_runs[0][1] + 180) % 360) - 180)
            ok["aim"] = d_aim <= BAND["aim_diff_deg"]
            print("  aim       part at %.2f deg, bay at %.2f deg, %.2f deg apart  (band %.1f)   %s"
                  % (part["mid"], bay_runs[0][1], d_aim, BAND["aim_diff_deg"],
                     "ok" if ok["aim"] else "FAIL"))
        else:
            ok["span"] = ok["aim"] = False

        pr = part["mean"]
        ok["part_colour"] = (pr[0] - pr[2] >= BAND["part_r_minus_b"]) and pr[0] >= 150
        print("  part hue  R-B = %.0f  (band >= %.0f), R = %.0f  (band >= 150)      %s"
              % (pr[0] - pr[2], BAND["part_r_minus_b"], pr[0],
                 "ok" if ok["part_colour"] else "FAIL"))
    else:
        ok["air"] = ok["thickness"] = ok["span"] = ok["aim"] = ok["part_colour"] = False

    spread = float(ring_mean.max() - ring_mean.min())
    ok["ring_colour"] = spread <= BAND["ring_neutral"] and ring_mean.max() >= 150
    print("  ring hue  channel spread %.0f  (band <= %.0f), max %.0f  (band >= 150)   %s"
          % (spread, BAND["ring_neutral"], ring_mean.max(), "ok" if ok["ring_colour"] else "FAIL"))

    print("")
    print("  The geometry here is read from the ink and knows nothing about the page's")
    print("  R_RING / SLOT_FROM / SLOT_TO / LIFT / RING_W; the layout judge reads the")
    print("  paths.  Two instruments, one picture -- that is what lets them disagree.")
    bad = [k for k, v in ok.items() if not v]
    print("  %d readings, %d failed%s" % (len(ok), len(bad), (": " + ", ".join(bad)) if bad else ""))
    return 0 if not bad else 1


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
