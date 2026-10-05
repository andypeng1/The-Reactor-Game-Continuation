#!/usr/bin/env python3
"""intro_mutants.py -- prove the intro's checks can go red.

WHY.  _tools/intro_check.js reports 24 ok / 0 failed.  A green run is only
worth something if the assertions are capable of failing -- "a check that has
never been red is decoration" (DECISIONS_2 298, the Phase 84 `--twist` lesson).
So each mutant below puts ONE of the four real defects (or a structural
stand-in for it) back into a copy of the shipped file and names the assertion
that must catch it.  A mutant that stays green is reported as a hole.

Every mutant is a defect that was ACTUALLY WRITTEN during this Phase and then
fixed -- not a synthetic typo.  The structural ones (noprop, filmmarker) stand
in for a structural fix that cannot be expressed as a numeric tweak.

Run:  python _tools/intro_mutants.py       (from the repo root)
Exit: 0 all mutants caught / 1 a mutant escaped, or the baseline was not green
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

WHOLE = "S1 the boot command is whole by t=1.4, and still solid"
CLEARED = "S4 panel, grid and HUD have all cleared by t=16.2"
BLACK = "S9 the screen is black at t=35.0"
ROWS = "G2 diagnostic rows reveal whole, never half-typed"
NOPROP = "G1b the controls stop click propagation to #stage"
SIBLING = "G1 #player is a sibling of #film, not inside it"

# (name, find, replace, which assertion must go red, what the defect was)
MUTANTS = [
    ("typed-delay",
     "bootTyped:     0.35,", "bootTyped:     0.55,",
     WHOLE, "the 55 ms/char draft: still writing when the panel covered it"),
    ("typed-rate",
     "clamp((p-T.bootTyped)*1000/34, 0, full.length)",
     "clamp((p-T.bootTyped)*1000/55, 0, full.length)",
     WHOLE, "same defect, the other half of it -- the divisor"),
    ("panel-off",
     "const panelOff = ramp(p, T.fadeOut+0.6, T.fadeOut+1.1);",
     "const panelOff = ramp(p, T.fadeOut+0.9, T.fadeOut+1.5);",
     CLEARED, "the pane frame was still half lit when the black hold began"),
    ("hud-stays",
     "$('hud').style.opacity = ramp(p, T.panelIn, T.panelIn+0.6) * (1-ramp(p, T.fadeOut+0.4, T.fadeOut+0.9));",
     "$('hud').style.opacity = ramp(p, T.panelIn, T.panelIn+0.6);",
     CLEARED, "the HUD used to survive into the title, reading as a video player"),
    ("black-past-end",
     "const black = ramp(p, T.off-0.05, T.off+0.08);",
     "const black = ramp(p, T.off+0.05, T.off+0.35);",
     BLACK, "the fade-out ended at 35.25, past the 35.0 film, so it never went black"),
    ("rows-typed",
     "    node.style.opacity = on*(1-off);\n    node.classList.toggle('live', i===newest && p>=at);",
     "    node.style.opacity = on*(1-off);\n"
     "    node.textContent = DIAGNOSTIC.rows[i][0].slice(0, Math.max(0, Math.floor((p-at)/0.040)));\n"
     "    node.classList.toggle('live', i===newest && p>=at);",
     ROWS, "typing 45 rows at 0.155 s/row leaves two dozen half-written"),
    ("no-stop-prop",
     "$('player').addEventListener('click', stop);", "",
     NOPROP, "without it, pressing Play also toggles the stage -- it pauses itself"),
    ("film-marker",
     "</div><!-- /film -->", "</div><!-- film -->",
     SIBLING, "stands in for the structural fix: the marker ordering is the check"),
]


def run_check(path):
    """Returns (rc, list of FAIL labels). Output is taken as bytes: this
    console is GBK and text=True would corrupt any non-ASCII (CLAUDE.md 0.6)."""
    p = subprocess.run([NODE, CHECK, path], capture_output=True)
    out = p.stdout.decode("utf-8", "replace")
    fails = [ln[len("FAIL "):].split("   [")[0].strip()
             for ln in out.splitlines() if ln.startswith("FAIL ")]
    return p.returncode, fails, out


def main():
    src = open(SRC, encoding="utf-8").read()

    print("baseline ... ", end="", flush=True)
    rc, fails, out = run_check(SRC)
    n_ok = sum(1 for ln in out.splitlines() if ln.startswith("ok   "))
    if rc != 0 or fails:
        print("NOT GREEN")
        print(f"   the unmutated file is already failing rc={rc}: {fails}")
        print("   fix the film before trusting any mutant below.")
        return 1
    print(f"green ({n_ok} ok, 0 failed)")

    escaped = []
    for name, find, repl, expect, defect in MUTANTS:
        if src.count(find) != 1:
            print(f"HOLE {name}: anchor matched {src.count(find)}x, not 1 -- "
                  f"the mutant was never applied")
            escaped.append(name)
            continue
        with open(TMP, "w", encoding="utf-8", newline="") as fh:
            fh.write(src.replace(find, repl))
        try:
            rc, fails, _ = run_check(TMP)
            caught = expect in fails
            mark = "ok  " if caught else "HOLE"
            print(f"{mark} {name}: {len(fails)} red"
                  + (f" -> {fails[0][:46]!r}" if fails else "")
                  + ("" if caught else f"   expected {expect!r}"))
            if not caught:
                escaped.append(name)
        finally:
            if os.path.exists(TMP):
                os.remove(TMP)

    print()
    if escaped:
        print(f"{len(MUTANTS) - len(escaped)}/{len(MUTANTS)} mutants caught; "
              f"ESCAPED: {', '.join(escaped)}")
        return 1
    print(f"{len(MUTANTS)}/{len(MUTANTS)} mutants caught -- every check above can go red.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
