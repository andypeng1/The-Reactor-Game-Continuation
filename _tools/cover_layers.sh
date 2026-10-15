#!/usr/bin/env bash
# cover_layers.sh -- "does each decorative layer change any pixel?"  (Phase 132)
#
# The layout judge (cover_judge.js A9) reads the layers' COMPUTED STYLES and
# asserts that each one's filter matches the polarity its markup declares.  This
# script asks the harder question the same defect demanded: render the cover once
# per layer with that one layer switched off, and diff the pixels.  A layer whose
# removal changes nothing was never on the picture.  Measured on the first build,
# two of the five were exactly that (coreMark is the sixth layer, added Phase 133
# when the hexagon's photo was replaced by the manufacturer's mark):
#
#   black art under mix-blend-mode:screen, no invert -> screen(base, 0) == base
#     titleBand 0 px / max delta 0,  hazard 0 px / max delta 2
#   near-white art under filter:invert(1) -> amplitude collapses to 1%-14%
#     hexes 8480 px / delta 3 (now 24),  smMark 138 px / delta 35 (now 54)
#
#   bash _tools/cover_layers.sh
#
# It re-renders cover/THE_REACTOR_GAME_cover.png first, so the full frame and the
# layer-off frames always come from the same build.
#
# The comparer is _tools/cover_layer_probe.py, next to this script -- not in the
# scratch pile the off_*.png renders land in.  The renders regenerate from this
# file; the thing three documents cite as the command to re-run does not.
#
# TWO THINGS THIS SCRIPT REFUSES TO DO QUIETLY (both found by one run of it
# printing a number the other five could not reproduce):
#
#   1. It cd's to the repo root before rendering.  Every path below -- the page,
#      the two --shot targets -- is relative, so run from anywhere else the
#      renders would land next to whoever called it, and the probe would diff a
#      full frame against frames that are not there.
#   2. render() deletes its target first and fails if the renderer did not put a
#      file back.  The first version swallowed the exit code and the output, so a
#      render that died left the PREVIOUS frame on disk and the diff reported it
#      as this build's reading.  That is CLAUDE.md 0.26 (1): a check that can
#      fail for a reason other than the thing under test is not an experiment.
#      The reading it printed was `#grid 12493 px, max delta 171`; five other
#      runs and the previous session all say 12461 px / delta 16.  The stale file
#      is a mechanism, not a proof -- see docs/COVER.md section 3.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NODE="${NODE:-D:/nodejs/node}"
SCRATCH="$ROOT/_tools/_attic/scratch"
SHOT="cover/THE_REACTOR_GAME_cover.png"
LAYERS="grid hexes coreGlow coreMark titleBand hazard"

cd "$ROOT"

render () {                       # $1 = --eval body, $2 = output path (relative)
  rm -f "$2"
  if ! "$NODE" _tools/intro_render.js --page cover/index.html --at 0 \
          --w 1080 --h 1080 --eval "$1" --shot "$2" > /dev/null || [ ! -s "$2" ]; then
    echo "cover_layers.sh: the renderer produced no $2 (eval: $1)" >&2
    exit 1
  fi
}

render "'full'" "$SHOT"

OFFS=()
for L in $LAYERS; do
  render "document.getElementById('$L').style.opacity='0'; 'off $L'" \
         "_tools/_attic/scratch/off_$L.png"
  OFFS+=("$SCRATCH/off_$L.png")
done

python -X utf8 "$ROOT/_tools/cover_layer_probe.py" "$ROOT/cover/THE_REACTOR_GAME_cover.png" "${OFFS[@]}"
