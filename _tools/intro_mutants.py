#!/usr/bin/env python3
"""intro_mutants.py -- prove the intro's checks can go red.

WHY.  _tools/intro_check.js reports 24 ok / 0 failed.  A green run is only
worth something if the assertions are capable of failing -- "a check that has
never been red is decoration" (DECISIONS_2 298, the Phase 84 `--twist` lesson).
So each mutant below puts ONE of the real defects (or a structural stand-in for
it) back into a copy of the shipped file and names the assertion that must
catch it.  A mutant that stays green is reported as a hole.

Every mutant is a defect that was ACTUALLY WRITTEN during this phase and then
fixed -- not a synthetic typo.  The structural ones (no-stop-prop, film-marker)
stand in for a structural fix that cannot be expressed as a numeric tweak.

There are TWO harnesses, because they can see different things:

  dom     _tools/intro_check.js     a stub DOM: time and logic, no layout.
                                    Fast, no browser, checks the film's intent.
  layout  _tools/intro_render.js --check
                                    a real headless Chrome: the only one that
                                    can see layout at all.

The distinction is not decoration.  The Phase 92 defect (#diagList anchored to
`bottom:0` inside a 630px window, so all 45 rows sat ABOVE the pane and the pane
stayed empty for the first seven seconds) was 100% green in the dom harness --
every row really was opacity:1.  A stub DOM has no layout to be wrong about, so
that defect was structurally invisible to it.  Hence the second harness.

Run:  python _tools/intro_mutants.py       (from the repo root)
Exit: 0 all mutants caught / 1 a mutant escaped, or a baseline was not green
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "intro", "index.html")
TMP = os.path.join(HERE, "_mutant.html")
# node is not on PATH on this machine (CLAUDE.md 0.6); the MCP servers reach it
# by full path and so must we.
NODE = os.environ.get("TRG_NODE", r"D:\nodejs\node")
CHECK = os.path.join(HERE, "intro_check.js")
RENDER = os.path.join(HERE, "intro_render.js")

WHOLE = "S1 the boot command is whole by t=1.4, and still solid"
CLEARED = "S4 panel, grid and HUD have all cleared by t=16.2"
BLACK = "S9 the screen is black at t=35.0"
ROWS = "G2 diagnostic rows reveal whole, never half-typed"
NOPROP = "G1b the controls stop click propagation to #stage"
SIBLING = "G1 #player is a sibling of #film, not inside it"
ONSCREEN = "L1 lit rows are on screen (up to a full pane)"
PANE_BOTTOM = "L3 the newest row rides the bottom once full"

# (name, harness, find, replace, assertion that must go red -- or None to
#  require the mutant STAYS green, which is how we show a check has real
#  discrimination instead of just always failing, defect)
MUTANTS = [
    ("dom", "typed-delay",
     "bootTyped:     0.35,", "bootTyped:     0.55,",
     WHOLE, "the 55 ms/char draft: still writing when the panel covered it"),
    ("dom", "typed-rate",
     "clamp((p-T.bootTyped)*1000/34, 0, full.length)",
     "clamp((p-T.bootTyped)*1000/55, 0, full.length)",
     WHOLE, "same defect, the other half of it -- the divisor"),
    ("dom", "panel-off",
     "const panelOff = ramp(p, T.fadeOut+0.6, T.fadeOut+1.1);",
     "const panelOff = ramp(p, T.fadeOut+0.9, T.fadeOut+1.5);",
     CLEARED, "the pane frame was still half lit when the black hold began"),
    ("dom", "hud-stays",
     "$('hud').style.opacity = ramp(p, T.panelIn, T.panelIn+0.6) * (1-ramp(p, T.fadeOut+0.4, T.fadeOut+0.9));",
     "$('hud').style.opacity = ramp(p, T.panelIn, T.panelIn+0.6);",
     CLEARED, "the HUD used to survive into the title, reading as a video player"),
    ("dom", "black-past-end",
     "const black = ramp(p, T.off-0.05, T.off+0.08);",
     "const black = ramp(p, T.off+0.05, T.off+0.35);",
     BLACK, "the fade-out ended at 35.25, past the 35.0 film, so it never went black"),
    ("dom", "rows-typed",
     "    node.style.opacity = on*(1-off);\n    node.classList.toggle('live', i===newest && p>=at);",
     "    node.style.opacity = on*(1-off);\n"
     "    node.textContent = DIAGNOSTIC.rows[i][0].slice(0, Math.max(0, Math.floor((p-at)/0.040)));\n"
     "    node.classList.toggle('live', i===newest && p>=at);",
     ROWS, "typing 45 rows at 0.155 s/row leaves two dozen half-written"),
    ("dom", "no-stop-prop",
     "$('player').addEventListener('click', stop);", "",
     NOPROP, "without it, pressing Play also toggles the stage -- it pauses itself"),
    ("dom", "film-marker",
     "</div><!-- /film -->", "</div><!-- film -->",
     SIBLING, "stands in for the structural fix: the marker ordering is the check"),

    # ---- layout: only the browser can see these ----
    ("layout", "diag-anchor",
     "#diagList{position:absolute;left:0;right:0;top:0}",
     "#diagList{position:absolute;left:0;right:0;bottom:0}",
     ONSCREEN, "the real Phase 92 defect: bottom-anchored 1215px block inside a "
               "630px window put every early row above the pane"),
    ("layout", "diag-noscroll",
     "$('diagList').style.transform = `translateY(${-Math.max(0, shown*rowH - scrollH)}px)`;",
     "$('diagList').style.transform = 'translateY(0px)';",
     PANE_BOTTOM, "without the transform the newest line runs off the bottom "
                  "instead of staying on the pane's bottom edge"),
]

# A mutant that MUST stay green.  .drow's line-height is the same 27 the scroll
# arithmetic needs; the film now MEASURES it (offsetHeight) instead of writing
# it twice.  If someone puts the literal back, this stops being free and
# diag-rowsize starts failing L1/L3 -- which is the whole point of measuring.
FOLLOW = [
    ("layout", "diag-rowsize",
     ".drow{\n  font-size:19px;line-height:27px;white-space:nowrap;",
     ".drow{\n  font-size:19px;line-height:40px;white-space:nowrap;",
     "row height is measured, not assumed"),
]


def run(harness, path):
    """Returns (rc, list of FAIL labels). Output is taken as bytes: this console
    is GBK and text=True would corrupt any non-ASCII (CLAUDE.md 0.6)."""
    cmd = ([NODE, CHECK, path] if harness == "dom"
           else [NODE, RENDER, "--check", "--page", path])
    p = subprocess.run(cmd, capture_output=True)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    # Labels are everything before the first '['. Spacing differs between the
    # two harnesses (they were written a phase apart) and parsing on a fixed
    # run of spaces would silently return the detail text as the label.
    fails = [ln[len("FAIL "):].split("[")[0].strip()
             for ln in out.splitlines() if ln.startswith("FAIL ")]
    return p.returncode, fails, out


def baseline(harness):
    rc, fails, out = run(harness, SRC)
    n_ok = sum(1 for ln in out.splitlines() if ln.startswith("ok"))
    if rc != 0 or fails:
        print(f"baseline {harness}: NOT GREEN (rc={rc}) {fails}")
        print("   fix the film before trusting any mutant below.")
        return False
    print(f"baseline {harness}: green ({n_ok} ok, 0 failed)")
    return True


def apply_and_run(src, find, repl, harness):
    if src.count(find) != 1:
        return None, [], f"anchor matched {src.count(find)}x, not 1 -- never applied"
    with open(TMP, "w", encoding="utf-8", newline="") as fh:
        fh.write(src.replace(find, repl))
    try:
        rc, fails, _ = run(harness, TMP)
        return rc, fails, None
    finally:
        if os.path.exists(TMP):
            os.remove(TMP)


def main():
    src = open(SRC, encoding="utf-8").read()

    for h in ("dom", "layout"):
        if not baseline(h):
            return 1

    escaped = []
    print()
    for harness, name, find, repl, expect, defect in MUTANTS:
        rc, fails, err = apply_and_run(src, find, repl, harness)
        if err:
            print(f"HOLE {name}: {err}")
            escaped.append(name)
            continue
        caught = expect in fails
        print(f"{'ok  ' if caught else 'HOLE'} {name} [{harness}]: {len(fails)} red"
              + (f" -> {fails[0][:44]!r}" if fails else "")
              + ("" if caught else f"   expected {expect!r}"))
        if not caught:
            escaped.append(name)

    # FOLLOWs: these must NOT go red. A check that fires on everything is as
    # useless as one that never fires.
    for harness, name, find, repl, why in FOLLOW:
        rc, fails, err = apply_and_run(src, find, repl, harness)
        if err:
            print(f"HOLE {name}: {err}")
            escaped.append(name)
            continue
        clean = not fails
        print(f"{'ok  ' if clean else 'HOLE'} {name} [{harness}] FOLLOW: "
              + ("stayed green" if clean else f"fired on {fails[0][:40]!r}")
              + f"   ({why})")
        if not clean:
            escaped.append(name)

    total = len(MUTANTS) + len(FOLLOW)
    print()
    if escaped:
        print(f"{total - len(escaped)}/{total} accounted for; ESCAPED: {', '.join(escaped)}")
        return 1
    print(f"{len(MUTANTS)}/{len(MUTANTS)} mutants caught, "
          f"{len(FOLLOW)}/{len(FOLLOW)} follows stayed green -- every check can go red.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
