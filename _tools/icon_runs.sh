#!/usr/bin/env bash
# icon_runs.sh -- rebuild one 1:1 icon: master PNG, 512 upload file, both metres.
#
# Three separate commands were being typed by hand for each icon and one of them
# silently drifted (the 512 was made from a stale master twice).  This is the
# whole chain in one place, in the order that matters: render the master, prove
# the master, derive the 512 FROM the master, prove the 512 too.
#
#   bash _tools/icon_runs.sh rebuild
#   bash _tools/icon_runs.sh continuation
#
# The instruments are per icon (they encode what THAT picture claims), so the
# name picks the instrument as well as the page.  Adding a third icon means
# adding a page + a judge + a pixel check and one line below -- deliberately not
# a generic loop, because a generic loop would have to ask "which rule applies",
# and the answer differs per icon.
set -u
cd "$(dirname "$0")/.." || exit 1

NAME="${1:-}"
case "$NAME" in
  rebuild)
    PAGE=cover/rebuild.html
    JUDGE=_tools/rebuild_judge.js
    PIXEL=_tools/rebuild_pieces_check.py
    SHOT=cover/THE_REACTOR_GAME_rebuild_icon.png
    ;;
  continuation)
    PAGE=cover/continuation.html
    JUDGE=_tools/continuation_judge.js
    PIXEL=_tools/continuation_ring_check.py
    SHOT=cover/THE_REACTOR_GAME_continuation_icon.png
    ;;
  *)
    echo "usage: bash _tools/icon_runs.sh {rebuild|continuation}" >&2
    exit 2
    ;;
esac
UP512="${SHOT%.png}_512.png"
REPORT="_tools/_attic/scratch/icon_report_${NAME}.json"
mkdir -p _tools/_attic/scratch
fail=0

echo "=== render $PAGE -> $SHOT"
/d/nodejs/node _tools/intro_render.js --page "$PAGE" --at 0 --w 1024 --h 1024 \
    --eval 'layoutReport()' --shot "$SHOT" > "$REPORT" || fail=1
[ -s "$SHOT" ] || { echo "render produced no file"; exit 1; }
[ -s "$REPORT" ] || { echo "render produced no report"; exit 1; }

echo "=== judge"
/d/nodejs/node "$JUDGE" "$REPORT" || fail=1

echo "=== pixels"
python -B "$PIXEL" || fail=1

echo "=== 512 (derived from the master that was just proved)"
python -B - "$SHOT" "$UP512" <<'PY' || fail=1
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
im.resize((512, 512), Image.LANCZOS).save(dst, optimize=True)
print("  %s -> %s" % (src, dst))
PY
# The 512 gets its own reading, not a copy of the master's: every band in the
# pixel check has to survive the file being measured at a different scale.  Only
# rebuild_pieces_check.py takes a box, and only because it needs the centre.
if [ "$NAME" = rebuild ]; then
  SHOT="$UP512" BOX_X=131 BOX_Y=82 BOX=250 python -B "$PIXEL" || fail=1
fi

echo "=== md5"
md5sum "$SHOT" "$UP512"
wc -c "$SHOT" "$UP512"
exit $fail
