#!/usr/bin/env python3
"""reimagine_pieces_check.py -- the ink half of the Reimagine icon's check.

WHAT THIS FILE IS FOR
=====================
cover/reimagine.html claims one thing above all others: **the two halves are the
same drawing**.  That claim cannot be tested from the page's own report --
layoutReport() would be comparing the numbers it was handed.  So this instrument
holds NO design constant and reads only the pixels:

  1. It FINDS the geometry.  The centre and the ring's outer radius come from a
     circle fitted to the ring's own outer edge; the seam comes from the leftmost
     amber pixel; the amber's radius from the farthest amber pixel from that
     centre.  Nothing is passed in.
  2. It checks the amber fills the core right up to the ring's inner wall.
  3. It measures the ring's inner/outer ratio in the DELIVERED PNG and the same
     ratio inside intro/assets/sm-core.png, and compares the two RATIOS -- a
     scale-free comparison, so no "what size was it drawn at" constant is needed
     and the same file runs unchanged on the 512 upload.
  4. It measures the ink coverage per radius separately on the two sides of the
     seam.  The word and the mark both cross the seam, so if the right half were
     a different drawing -- a different size, a flipped copy, a second asset --
     these two curves would separate.

WHY THE CENTRE COMES FROM THE RING AND NOT FROM THE AMBER (measured 2026-10-31,
first version of this file).  The mark's own arms and its two hexagons are drawn
ON TOP of the amber, so the amber's boundary is the arc only where no ink touches
it.  A hexagon chord running nearly tangentially hides a whole stretch: the worst
row's rightmost amber pixel sat 113px inside the true arc.  A circle fitted to
those points came out at r=274 instead of 291 with a 90px residual, and every
reading built on it was confidently wrong.  The ring's OUTER edge has nothing
beyond it but the background, so the rightmost white pixel of each row is always
on it -- residual 0.65px over 577 rows.

WHY THE BRIGHTNESS FLOOR IS 120 (measured on the same render): the amber is
rgb(255,128,1) dimmed only by the scanline overlay (x0.68) and the vignette, so
the dimmest amber anywhere inside the disc is r=173.  Chrome's text rendering
leaves warm pixels on the edge of white glyphs -- 39 of them across the subtitle,
values like (71,44,8), brightest r=94 -- which pass any hue test.  The floor sits
in the measured gap 94..173, and it is what makes "nothing amber left of the
seam" come back as a literal zero rather than as 39.

--selftest proves every reading can go red by damaging the picture itself (nine
mutations, each naming what it expects to light).  A reading that cannot fail is
noise (CLAUDE.md 0.31), and this is the half of the pair that has no browser to
blame.

Usage:
    python -B _tools/reimagine_pieces_check.py
    python -B _tools/reimagine_pieces_check.py --selftest
    SHOT=cover/THE_REACTOR_GAME_reimagine_icon_512.png python -B _tools/reimagine_pieces_check.py
"""
import math
import os
import sys
import traceback

SHOT = os.environ.get("SHOT", "cover/THE_REACTOR_GAME_reimagine_icon.png")
ART = os.environ.get("ART", "intro/assets/sm-core.png")

# ---- ink predicates -------------------------------------------------------
# Colour is read as a RATIO, not an absolute value: the scanline overlay and the
# vignette both multiply the whole picture by something < 1, so the amber stays
# (r, 0.50r, 0.00r) at any depth.  An absolute threshold would have read the
# amber as "not amber" on every dark scanline.
AMBER_R_MIN = 120          # the gap between the fringes (94) and the ink (173)
AMBER_G_LO, AMBER_G_HI = 0.35, 0.62
AMBER_B_HI = 0.15
WHITE_MIN = 110            # the dimmest white ink: glyph bottoms under the vignette
WHITE_SPREAD = 26          # neutrals only -- the cyan frame is (82,218,226)

# ---- what counts as a mass ------------------------------------------------
# 30 px at the master's amber radius (~291); it scales with the disc's area so the
# 512 file is judged by the same rule rather than a looser one (CLAUDE.md 0.44).
MIN_BLOB_R2 = 3.5e-4       # 3.5e-4 * 291^2 = 29.6 px
CORNER = 60                # the frame's corner brackets are white-ish; ignore them.
                           # In master pixels: scaled with the file (see corner()).

# ---- geometry tolerances --------------------------------------------------
TOL_FIT = 1.5              # px, worst residual of the circle fitted to the ring
TOL_RATIO = 0.012          # ring inner/outer, render vs asset (scale-free)
TOL_HALVES = 0.035         # L1 / total ink between the two halves' coverage curves.
                           # Measured 2026-10-31: the delivered drawing reads 0.01459 at
                           # 1024 and 0.01479 at 512 (the statistic is scale-free to 3
                           # figures); erasing a 24-degree wedge -- one arm -- off the
                           # right half reads 0.045 / 0.082 / 0.115 depending which arm.
                           # 0.035 is 2.4x above the baseline and below the faintest
                           # defect measured.  A per-radius MAX was the first rule here
                           # and it went red on the correct 512 file (0.283 vs 0.219 at
                           # 1024): raster noise, not a different drawing.

# Filled in by measure(); only --selftest reads it, so it can place its damage.
GEO = {}


def load(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    return im, im.size[0], im.size[1]


def build_masks(px, W, H):
    """One pass, two masks.  Corners are skipped: the corner brackets are #ebebeb
    at 50% over black, which is 'white' by any luminance test and would drag the
    white bbox out to the frame.  The margin scales with the file so the 512
    upload is judged by the same rule rather than by a looser one."""
    k = W / 1024.0
    corner = max(4, int(round(CORNER * k)))
    amber = [[False] * W for _ in range(H)]
    white = [[False] * W for _ in range(H)]
    for y in range(H):
        in_corner_y = y < corner or y > H - 1 - corner
        for x in range(W):
            if in_corner_y and (x < corner or x > W - 1 - corner):
                continue
            r, g, b = px[x, y]
            amber[y][x] = (r >= AMBER_R_MIN and AMBER_G_LO * r <= g <= AMBER_G_HI * r
                           and b <= AMBER_B_HI * r)
            white[y][x] = (min(r, g, b) >= WHITE_MIN and max(r, g, b) - min(r, g, b) <= WHITE_SPREAD)
    return amber, white


def solve3(A, v):
    """Cramer's rule on a 3x3.  Small enough that a written-out determinant is
    shorter than a Gaussian elimination and easier to read."""
    def det(m):
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
              - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
              + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    d = det(A)
    if abs(d) < 1e-12:
        raise ValueError("circle fit is singular -- the boundary points are collinear")
    out = []
    for i in range(3):
        M = [row[:] for row in A]
        for k in range(3):
            M[k][i] = v[k]
        out.append(det(M) / d)
    return out


def fit_circle(pts):
    """Algebraic least-squares circle: x^2 + y^2 = A x + B y + C."""
    n = len(pts)
    Sx = sum(p[0] for p in pts);          Sy = sum(p[1] for p in pts)
    Sxx = sum(p[0] * p[0] for p in pts);  Syy = sum(p[1] * p[1] for p in pts)
    Sxy = sum(p[0] * p[1] for p in pts)
    Sxz = sum(p[0] * (p[0] ** 2 + p[1] ** 2) for p in pts)
    Syz = sum(p[1] * (p[0] ** 2 + p[1] ** 2) for p in pts)
    Sz = sum(p[0] ** 2 + p[1] ** 2 for p in pts)
    A, B, C = solve3([[Sxx, Sxy, Sx], [Sxy, Syy, Sy], [Sx, Sy, n]], [Sxz, Syz, Sz])
    cx, cy = A / 2.0, B / 2.0
    R = math.sqrt(C + cx * cx + cy * cy)
    resid = max(abs(math.hypot(p[0] - cx, p[1] - cy) - R) for p in pts)
    return cx, cy, R, resid


def blobs(mask, W, H, min_px):
    """4-connected components, kept only if big enough to be a drawing rather than
    a fringe.  An explicit stack -- no recursion."""
    seen = [[False] * W for _ in range(H)]
    out = []
    for sy in range(H):
        for sx in range(W):
            if not mask[sy][sx] or seen[sy][sx]:
                continue
            stack = [(sx, sy)]
            seen[sy][sx] = True
            xs = []
            while stack:
                x, y = stack.pop()
                xs.append(x)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and mask[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if len(xs) >= min_px:
                out.append((len(xs), min(xs), max(xs)))
    return out


def profile(mask, W, H, cx, cy, rmax, half=None, n_rays=720):
    """Fraction of rays that find ink, per integer radius.
    Rays, not angle bins: binning pixel angles leaves an empty bin exactly at a
    raster boundary (CLAUDE.md 0.44 (2), the Rebuild lesson)."""
    out = []
    step = 2.0 * math.pi / n_rays
    for r in range(0, int(rmax) + 1):
        hit = n = 0
        for i in range(n_rays):
            a = i * step
            c = math.cos(a)
            if half == "left" and c >= 0:
                continue
            if half == "right" and c < 0:
                continue
            x = int(round(cx + r * c))
            y = int(round(cy + r * math.sin(a)))
            if 0 <= x < W and 0 <= y < H:
                n += 1
                if mask[y][x]:
                    hit += 1
        out.append(hit / n if n else 0.0)
    return out


def band(prof, lo, hi, cover=0.85):
    """The longest run of radii inside [lo, hi] whose coverage stays >= cover."""
    best = None
    start = None
    for r in range(int(lo), min(int(hi), len(prof) - 1) + 1):
        if prof[r] >= cover:
            if start is None:
                start = r
        else:
            if start is not None and (best is None or r - start > best[1] - best[0]):
                best = (start, r - 1)
            start = None
    if start is not None and (best is None or len(prof) - start > best[1] - best[0]):
        best = (start, len(prof) - 1)
    return best


# ==========================================================================
def measure(px, W, H):
    rows = []

    def check(label, ok, detail):
        rows.append((label, bool(ok), detail))
        return ok

    amber, white = build_masks(px, W, H)

    # ================= 1. where everything is, found without being told ====
    ys = [y for y in range(H) if any(amber[y])]
    if not ys:
        check("an amber mass exists at all", False,
              "no pixel reaches the amber predicate anywhere in the picture")
        return rows
    # The disc and the half of the word that is amber are two separate row bands;
    # the disc is the upper one.  Split at the widest empty run -- no constant.
    seps = [(ys[i + 1] - ys[i], ys[i]) for i in range(len(ys) - 1)]
    gy = max(seps)[1] if seps else ys[-1]
    band_rows = [y for y in ys if y <= gy]

    # The ring's outer edge: nothing but the background is beyond it, so the
    # rightmost white pixel of each row is on it.  See the header.
    arc = [(max(x for x in range(W) if white[y][x]), y) for y in band_rows
           if any(white[y])]
    if len(arc) < 20:
        check("the mark's ring is drawn at all", False,
              "%d rows of the disc band contain any white ink" % len(arc))
        return rows
    cx, cy, r_out, resid = fit_circle(arc)
    check("the white ring is a circle (the arc closes on itself)",
          resid <= TOL_FIT,
          "circle fitted to %d rows of the ring's outer edge: centre (%.2f, %.2f), "
          "r %.2f, worst residual %.2f px (allowed %.1f)"
          % (len(arc), cx, cy, r_out, resid, TOL_FIT))

    # THE AXIS IS NOT DERIVED FROM THE AMBER.  The first version of this file
    # took the seam to be the leftmost amber pixel and then checked "nothing
    # amber is left of the seam" -- which is a tautology: paint amber 40px to the
    # left and the seam simply moves with it, so the mutation lit four readings
    # and the one it was aimed at stayed green.  The axis now comes from the
    # WHITE ink (the ring's fitted centre, which is the mark's own vertical
    # axis), and the amber's left edge is measured against it: two independent
    # sources, so the rule can fail (DECISIONS_2 655).
    seam = cx
    left_edge = float(min(x for y in band_rows for x in range(W) if amber[y][x]))
    R = max(math.hypot(x - cx, y - cy) for y in band_rows
            for x in range(W) if amber[y][x])
    bulge = max(x for y in band_rows for x in range(W) if amber[y][x]) - seam
    check("the amber starts on the mark's own axis and nowhere left of it",
          abs(left_edge - seam) <= 2.0,
          "leftmost amber x %.0f, the ring's axis at %.2f (delta %.2f, allowed 2.0)"
          % (left_edge, seam, abs(left_edge - seam)))
    GEO.update(cx=cx, cy=cy, r_out=r_out, seam=seam, R=R, W=W, H=H)
    check("the amber is a half disc: it reaches the radius along two different directions",
          abs(bulge - R) <= max(2.0, 0.02 * R),
          "outward bulge %.2f px, farthest amber pixel %.2f px from the centre "
          "(delta %.2f, allowed %.2f)" % (bulge, R, abs(bulge - R), max(2.0, 0.02 * R)))

    # ================= 2. the ring, from the white ink =====================
    prof = profile(white, W, H, cx, cy, r_out * 1.08)
    rb = band(prof, 0.90 * r_out, 1.05 * r_out)
    if not rb:
        check("a white ring surrounds the amber", False,
              "no white band >= 0.85 coverage between r=%.0f and r=%.0f"
              % (0.90 * r_out, 1.05 * r_out))
        return rows
    r_in, r_out_meas = rb
    check("the amber fills the core right up to the ring's inner wall",
          abs(r_in - R) <= max(2.0, 0.010 * R),
          "amber reaches r=%.2f, ring band r=%d..%d (gap %.2f px, allowed %.2f)"
          % (R, r_in, r_out_meas, r_in - R, max(2.0, 0.010 * R)))

    # ================= 3. the drawn ring is the brand's ring ===============
    # The asset is LA: the ink lives in alpha.  Same profile, same definition.
    from PIL import Image
    art = Image.open(ART).convert("LA")
    aw, ah = art.size
    ap = art.load()
    amask = [[ap[x, y][1] >= 128 for x in range(aw)] for y in range(ah)]
    aprof = profile(amask, aw, ah, aw / 2.0, ah / 2.0, aw * 0.52)
    aband = band(aprof, aw * 0.44, aw * 0.51)
    if not aband:
        check("the brand asset has a ring to compare against", False,
              "%s: no ring band found" % ART)
        return rows
    a_in, a_out = aband
    k_art = a_in / a_out
    k_img = r_in / r_out_meas
    check("the drawn ring is the brand's ring (inner/outer, scale-free)",
          abs(k_art - k_img) <= TOL_RATIO,
          "asset %d/%d = %.4f, PNG %d/%d = %.4f (delta %.4f, allowed %.3f)"
          % (a_in, a_out, k_art, r_in, r_out_meas, k_img, abs(k_art - k_img), TOL_RATIO))

    # ================= 4. the two halves are the same drawing ==============
    pl = profile(white, W, H, cx, cy, R * 0.99, half="left")
    pr = profile(white, W, H, cx, cy, R * 0.99, half="right")
    diffs = [abs(a - b) for a, b in zip(pl, pr)]
    l1 = sum(diffs)
    tot = sum(a + b for a, b in zip(pl, pr))
    ratio = l1 / tot if tot else float("inf")
    check("the ink on the two halves is the same drawing",
          ratio <= TOL_HALVES,
          "L1/total coverage %.5f (allowed %.3f); per radius mean %.4f, worst %.3f at "
          "r=%d, total ink %.1f"
          % (ratio, TOL_HALVES, sum(diffs) / len(diffs), max(diffs),
             diffs.index(max(diffs)), tot))

    check("both halves actually carry ink (the rule above is not vacuous)",
          sum(pl) > 8 and sum(pr) > 8,
          "summed coverage left %.1f, right %.1f" % (sum(pl), sum(pr)))

    # ================= 5. one side is lit, the other is not ================
    def frac(half):
        lit = n = 0
        for y in range(int(cy - R * 0.8), int(cy + R * 0.8)):
            for x in range(int(cx - R * 0.8), int(cx + R * 0.8)):
                if (x - cx) ** 2 + (y - cy) ** 2 > (R * 0.8) ** 2:
                    continue
                if (half == "left") != (x < cx):
                    continue
                n += 1
                if amber[y][x]:
                    lit += 1
        return lit / n if n else 0.0
    fr = frac("right")
    fl = frac("left")
    check("the core is filled on one side and empty on the other",
          fr >= 0.55 and fl <= 0.02,
          "amber inside the core: right %.1f%%, left %.1f%% (needs >= 55%% / <= 2%%)"
          % (fr * 100, fl * 100))

    # Two readings: no amber PIXEL may sit left of the seam, and no amber MASS
    # either.  The first is the strict one; the second survives a future renderer
    # that reintroduces glyph fringing brighter than this threshold.
    stray = [(x, y) for y in range(H) for x in range(int(seam) - 4) if amber[y][x]]
    min_px = max(8, int(MIN_BLOB_R2 * R * R))
    left_masses = [b for b in blobs(amber, W, H, min_px) if b[2] < seam - 4]
    check("nothing amber is drawn on the left of the seam",
          not stray and not left_masses,
          "%d amber px at x < %.0f%s; %d amber masses >= %d px entirely on that side"
          % (len(stray), seam - 4, (" e.g. %s" % (stray[0],)) if stray else "",
             len(left_masses), min_px))

    # ================= 6. the word is cut on the same axis =================
    # Below the RING, not below the amber: the ring's lowest row is ~18px lower
    # than the disc's (the first run of this file read the ring's bottom as white
    # text and reported "white ends at 588").
    row_horizon = int(cy + r_out) + 12
    t_amber = [(x, y) for y in range(row_horizon, H) for x in range(W) if amber[y][x]]
    t_white = [(x, y) for y in range(row_horizon, H) for x in range(W) if white[y][x]]
    if not t_amber or not t_white:
        check("the word is drawn in both treatments", False,
              "amber px below the mark: %d, white px: %d" % (len(t_amber), len(t_white)))
        return rows
    w_right = max(x for x, _ in t_white)
    a_left = min(x for x, _ in t_amber)
    check("the word changes treatment across the same axis, in one letter gap",
          w_right < seam < a_left and (a_left - w_right) <= 40,
          "white ends at %d, amber starts at %d, axis at %.0f (gap %d px, allowed 40)"
          % (w_right, a_left, seam, a_left - w_right))

    # ================= 7. vertical rhythm ==================================
    rowslit = sorted(set(y for y in range(row_horizon, H) if any(white[y]))
                     | set(y for y in range(row_horizon, H) if any(amber[y])))
    bands = []
    for y in rowslit:
        if bands and y - bands[-1][1] <= 6:
            bands[-1][1] = y
        else:
            bands.append([y, y])
    check("the subtitle and the word are two separate bands, both clear of the mark",
          len(bands) == 2 and bands[0][0] - (cy + r_out_meas) >= 20 and bands[1][0] - bands[0][1] >= 20,
          "%d bands %s; gap from the mark %.0f px, gap between them %.0f px"
          % (len(bands), " ".join("%d..%d" % (a, b) for a, b in bands),
             bands[0][0] - (cy + r_out_meas) if bands else -1,
             bands[1][0] - bands[0][1] if len(bands) > 1 else -1))

    edge = 20.0 * W / 1024.0            # #frame's inset, in this file's pixels
    check("everything drawn stays inside the frame",
          seam - R > edge and seam + R < W - edge and cy - R > edge and cy + R < H - edge
          and bands and bands[-1][1] < H - edge,
          "disc x %.0f..%.0f y %.0f..%.0f, word bottom %d (frame inner edge %.0f)"
          % (seam - R, seam + R, cy - R, cy + R, bands[-1][1] if bands else -1, H - edge))
    return rows


# ==========================================================================
# Mutations.  Each damages the PICTURE, not the page, and each names the reading
# it is meant to light.  A reading that cannot go red is noise (CLAUDE.md 0.31);
# this is the half of the pair with no browser to blame.
def _paint(px, x, y, rgb):
    px[x, y] = rgb


BG = (7, 8, 10)
AMBER = (255, 128, 1)
READY = (235, 235, 235)


def mut_leak_left(px):
    """Amber spilling across the seam into the drawn half."""
    for y in range(int(GEO["cy"] - 100), int(GEO["cy"] + 100)):
        for x in range(int(GEO["seam"] - 40), int(GEO["seam"])):
            _paint(px, x, y, AMBER)


def mut_short_of_ring(px):
    """The amber stopping well inside the ring instead of reaching its wall."""
    cx, cy, R, seam = GEO["cx"], GEO["cy"], GEO["R"], GEO["seam"]
    for y in range(int(cy - R) - 1, int(cy + R) + 2):
        for x in range(int(seam), int(cx + R) + 2):
            if math.hypot(x - cx, y - cy) <= R:
                if math.hypot(x - cx, y - cy) >= 0.80 * R:
                    _paint(px, x, y, BG)


def mut_ring_too_wide(px):
    """The drawn ring made thicker outward: same inner wall, different ratio.
    Contiguous with the old edge (ro, not ro+1) -- the first version left a
    one-pixel gap at the antialiased edge, band() split there, kept the original
    17px run and reported the picture as clean."""
    cx, cy, ro = GEO["cx"], GEO["cy"], GEO["r_out"]
    for y in range(int(cy - ro - 14), int(cy + ro + 15)):
        for x in range(int(cx - ro - 14), int(cx + ro + 15)):
            d = math.hypot(x - cx, y - cy)
            if ro <= d <= ro + 12:
                _paint(px, x, y, READY)


def mut_ring_bitten(px):
    """A quarter of the ring missing."""
    cx, cy, ro = GEO["cx"], GEO["cy"], GEO["r_out"]
    for y in range(int(cy - ro - 4), int(cy + ro + 5)):
        for x in range(int(cx), int(cx + ro + 4)):
            d = math.hypot(x - cx, y - cy)
            if 0.88 * ro <= d <= 1.02 * ro and abs(math.degrees(math.atan2(y - cy, x - cx))) <= 45:
                _paint(px, x, y, BG)


def mut_erase_right_ink(px):
    """The right half drawn as a second, different picture."""
    cx, cy, R = GEO["cx"], GEO["cy"], GEO["R"]
    for y in range(int(cy - R) - 1, int(cy + R) + 2):
        for x in range(int(cx) + 1, int(cx + R) + 2):
            if math.hypot(x - cx, y - cy) <= R:
                r, g, b = px[x, y]
                if min(r, g, b) >= WHITE_MIN and max(r, g, b) - min(r, g, b) <= WHITE_SPREAD:
                    _paint(px, x, y, AMBER)


def mut_arm_rubbed_out(px):
    """One arm of the right half rubbed out -- a localised difference the
    normalised L1 is meant to catch (it reads 0.115 here)."""
    cx, cy, R = GEO["cx"], GEO["cy"], GEO["R"]
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx) + 1, int(cx + R) + 1):
            d = math.hypot(x - cx, y - cy)
            a = math.degrees(math.atan2(y - cy, x - cx))
            if d <= 0.9 * R and abs(((a - 30 + 180) % 360) - 180) <= 12:
                r, g, b = px[x, y]
                if min(r, g, b) >= WHITE_MIN and max(r, g, b) - min(r, g, b) <= WHITE_SPREAD:
                    _paint(px, x, y, AMBER)


def mut_word_amber_to_white(px):
    """The amber copy's clip slipped 46px left: it starts inside the white half.
    (Repainting the whole amber half grey would also go red -- on "the word is
    drawn in both treatments" -- but that is the vacuity guard, not the rule.
    This mutation keeps both treatments present and misaligns them.)"""
    for y in range(int(GEO["cy"] + GEO["r_out"]) + 20, GEO["H"]):
        for x in range(int(GEO["seam"]) - 46, int(GEO["seam"])):
            r, g, b = px[x, y]
            if min(r, g, b) >= WHITE_MIN and max(r, g, b) - min(r, g, b) <= WHITE_SPREAD:
                _paint(px, x, y, AMBER)


def mut_band_bridge(px):
    """A mark drawn in the air between the emblem and the subtitle."""
    for y in range(int(GEO["cy"] + GEO["r_out"]) + 6, int(GEO["cy"] + GEO["r_out"]) + 36):
        for x in range(200, 260):
            _paint(px, x, y, READY)


def mut_outside_frame(px):
    """Ink outside the frame, where Roblox's crop would eat it.  Positions are
    fractions of the file, not master pixels -- the first version used 480..520
    and threw an IndexError on the 512."""
    W, H = GEO["W"], GEO["H"]
    for y in range(int(H * 0.986), int(H * 0.996)):
        for x in range(int(W * 0.46), int(W * 0.50)):
            _paint(px, x, y, READY)


def mut_no_amber(px):
    """Nothing amber anywhere -- every rule below would be vacuously green."""
    for y in range(GEO["H"]):
        for x in range(GEO["W"]):
            r, g, b = px[x, y]
            if r >= AMBER_R_MIN and AMBER_G_LO * r <= g <= AMBER_G_HI * r and b <= AMBER_B_HI * r:
                _paint(px, x, y, READY)


MUTANTS = [
    ("amber leaks across the seam", mut_leak_left, "starts on the mark's own axis"),
    ("the amber stops short of the ring", mut_short_of_ring, "amber fills the core right up"),
    ("the ring is drawn too thick outward", mut_ring_too_wide, "the drawn ring is the brand's"),
    ("a quarter of the ring is missing", mut_ring_bitten, "the white ring is a circle"),
    ("the right half's line art is erased", mut_erase_right_ink, "the two halves is the same drawing"),
    ("one arm of the right half is rubbed out", mut_arm_rubbed_out, "the two halves is the same drawing"),
    ("the amber copy's clip slips 46px left", mut_word_amber_to_white, "changes treatment across the same axis"),
    ("a bar bridges the emblem and the subtitle", mut_band_bridge, "two separate bands"),
    ("ink is painted outside the frame", mut_outside_frame, "everything drawn stays inside the frame"),
    ("nothing is amber at all", mut_no_amber, "an amber mass exists at all"),
]


def run_selftest():
    im, W, H = load(SHOT)
    base = measure(im.load(), W, H)
    bad = 0
    print("baseline: %d readings, %d failed" % (len(base), sum(1 for r in base if not r[1])))
    if any(not r[1] for r in base):
        print("BASELINE IS RED -- fix the picture first")
        return 1
    # measure() writes the geometry it found into GEO, so without this snapshot
    # each mutation is applied at the PREVIOUS mutant's idea of where the centre
    # is -- and a mutant that breaks the ring (the bitten one) poisons the two
    # after it.  That is how this selftest first reported three false failures.
    baseline_geo = dict(GEO)
    for name, fn, expect in MUTANTS:
        GEO.clear(); GEO.update(baseline_geo)
        victim = im.copy()
        fn(victim.load())
        res = measure(victim.load(), W, H)
        red = [r[0] for r in res if not r[1]]
        hit = any(expect in r for r in red)
        if not hit:
            bad += 1
        print("%s  mutant '%s' -> %d red%s"
              % ("ok  " if hit else "FAIL", name, len(red),
                 ("" if hit else "  -- expected the reading containing %r" % expect)))
        for r in red:
            print("        red: %s" % r)
    print("%d of %d mutants lit the reading they were aimed at"
          % (len(MUTANTS) - bad, len(MUTANTS)) if bad
          else "%d/%d mutants lit the reading they were aimed at" % (len(MUTANTS), len(MUTANTS)))
    return 1 if bad else 0


def main():
    im, W, H = load(SHOT)
    rows = measure(im.load(), W, H)
    bad = 0
    for label, ok, detail in rows:
        bad += 0 if ok else 1
        print("%s  %s\n      %s" % ("ok  " if ok else "FAIL", label, detail))
    print("%d readings, %d failed" % (len(rows), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        code = run_selftest() if "--selftest" in sys.argv else main()
    except BaseException as exc:                      # CLAUDE.md 0.6: a crash must
        if isinstance(exc, SystemExit):               # not read as a pass
            raise
        traceback.print_exc()
        print("CRASHED -- this is a failure, not a pass")
        sys.exit(1)
    sys.exit(code)
