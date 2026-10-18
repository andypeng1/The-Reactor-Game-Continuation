#!/usr/bin/env bash
# cover_layers.sh -- "does each decorative layer change any pixel?"  (Phase 132)
#
# The layout judge (cover_judge.js A9) reads the layers' COMPUTED STYLES and
# asserts that each one's filter matches the polarity its markup declares.  This
# script asks the harder question the same defect demanded: render the cover once
# per layer with that one layer switched off, and diff the pixels.  A layer whose
# removal changes nothing was never on the picture.  Measured on the first build,
# two of the five were exactly that:
#
#   black art under mix-blend-mode:screen, no invert -> screen(base, 0) == base
#     titleBand 0 px / max delta 0,  hazard 0 px / max delta 2
#   near-white art under filter:invert(1) -> amplitude collapses to 1%-14%
#     hexes 8480 px / delta 3 (now 24),  smMark 138 px / delta 35 (now 54)
#
# PHASE 134 CUT THE LIST, NOT THE QUESTION.  Four of the six layers Phase 132/133
# watched (grid, hexes, coreGlow, titleBand, hazard -- and the noise layer) were
# removed from the page when the cover went down to four elements, so LAYERS below
# is what is actually left.  The two zero-contribution defects above are no longer
# representable on this page: there is no black line art left to feed `screen`.
# That is the *object* going away, not the instrument being satisfied (CLAUDE.md
# 0.31) -- so A9 lost its "both polarities must be present" guard and this script
# keeps running over the survivors.
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

# PHASE 144: the 16:9 page (_tools/page_judge.js) has the same four decorative
# layers, so the question "did this layer change any pixel" is the same question
# about a different picture.  Rather than a second copy of this file -- which is
# how two instruments drift until the docs cite one and the runs use the other --
# the four numbers below became overridable.  Defaults are the cover's, so every
# command written before Phase 144 still means what it meant.
#
#   PAGE=cover/page.html W=1920 H=1080 TAG=page \
#   SHOT=cover/THE_REACTOR_GAME_page.png bash _tools/cover_layers.sh
PAGE="${PAGE:-cover/index.html}"
W="${W:-1080}"
H="${H:-1080}"
TAG="${TAG:-cover}"
SHOT="${SHOT:-cover/THE_REACTOR_GAME_cover.png}"
LAYERS="coreMark smMark scan vig"

cd "$ROOT"
mkdir -p "$SCRATCH/layers_$TAG"

render () {                       # $1 = --eval body, $2 = output path (relative)
  rm -f "$2"
  if ! "$NODE" _tools/intro_render.js --page "$PAGE" --at 0 \
          --w "$W" --h "$H" --eval "$1" --shot "$2" > /dev/null || [ ! -s "$2" ]; then
    echo "cover_layers.sh: the renderer produced no $2 (eval: $1)" >&2
    exit 1
  fi
}

render "'full'" "$SHOT"

OFFS=()
for L in $LAYERS; do
  # 每个页面一个子目录：两次跑的临时帧同名，混在一起时探针会拿 page 的整帧
  # 去减 cover 的层关帧 —— 尺寸不同会报 SIZE MISMATCH，而尺寸相同就**不报**。
  render "document.getElementById('$L').style.opacity='0'; 'off $L'" \
         "_tools/_attic/scratch/layers_$TAG/off_$L.png"
  OFFS+=("$SCRATCH/layers_$TAG/off_$L.png")
done

python -X utf8 "$ROOT/_tools/cover_layer_probe.py" "$ROOT/$SHOT" "${OFFS[@]}"
