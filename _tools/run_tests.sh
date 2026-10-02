#!/usr/bin/env bash
# Rebuild and run every harness the recorder has, and gate on the exit code.
#
# All six harnesses extract their subject from the SHIPPED recorder by text, so
# a change to _tools/TRG_original_recorder.luau is a change to all six tests.
# That is the point of building them here rather than checking in the generated
# files: there is no copy of snapshot, endReason, readGui, the flow boundary or
# the core gate that can drift from the one that gets injected.
#
# THERE WAS A SIXTH, AND IT IS GONE WITH ITS SUBJECT. build_driver_test.py built a
# harness for `driveStep`, the state machine that worked the two switches by itself.
# The operator removed the requirement on 2026-09-30 ("不需要什么driver，只需要seal"),
# so driveStep is not in the recorder any more and a harness that extracts it can
# only fail. The three files are kept in _tools/_attic/driver/ rather than deleted:
# the scenarios in them are measurements about this game's two switches, and they
# are the whole of what is known there if the driver is ever wanted back.
#
# build_gui_test is the odd one out in a different way: it takes its input and
# output paths as arguments, because selftest_gui.py has to point the SAME
# extraction at a deliberately broken copy of the recorder. A mutation test run
# through a second builder would be testing the builder.
#
# end_reason is the odd one out -- it extracts a REGION rather than a function,
# because endReason closes over the counters declared above it. Those counters are
# the state under test, so a copy of them here would be a test agreeing with
# itself (see the builder's docstring).
#
# The second subject is the WATCHER (TRG_original_watch.luau), which has no builder
# because nothing is extracted from it -- watch_harness.luau runs the shipped file
# itself, under a stubbed Roblox API. Its own suite has never been enough on its
# own either: a harness that has only ever gone green cannot be told apart from one
# whose checks are all `true`, so selftest_watch.py breaks the watcher twenty-five
# ways and requires the matching check to be the one that turns red.
#
#   bash _tools/run_tests.sh
#
# The generated _*.luau files this writes are NOT the source of truth -- edit the
# builders beside them, never the _*.luau.
set -e

cd "$(dirname "$0")/.."
LUA=/d/Lua/5.1/lua.exe

# Parse the WHOLE shipped file first, before extracting anything from it. The
# three harnesses below each compile one region of the recorder and leave the
# rest unchecked -- so a syntax error in the SINK, the click hooker, the main
# loop or the new readEndScreens would be found by the executor in the game
# instead of here. The recorder is written in a Lua 5.1 compatible subset by
# construction (that is why the harnesses can run its regions under 5.1 at all),
# so this is a real gate and not a stub: it is a 5.1 parse, not a Luau compile,
# and it is worth being exact about which of those it proves.
"$LUA" -e "
local f, err = loadfile('_tools/TRG_original_recorder.luau')
if not f then io.stderr:write('recorder does not parse: ' .. tostring(err) .. string.char(10)) os.exit(1) end
print('recorder parses: ' .. _VERSION)
"

# Same gate for the watcher, and for the same reason: the harness only compiles
# what it walks through, and the parts it never reaches are exactly the ones a
# start-up in the original game would find first -- the census, the sink, the
# hotkeys. A 5.1 parse of the whole file covers them all.
"$LUA" -e "
local f, err = loadfile('_tools/TRG_original_watch.luau')
if not f then io.stderr:write('watcher does not parse: ' .. tostring(err) .. string.char(10)) os.exit(1) end
print('watcher parses: ' .. _VERSION)
"

# gate is the newest, and it exists for the rule the operator added on 2026-09-30:
# nothing about the reactor is written until the core is fully on. It is the one
# region here whose subject is what the recorder REFUSES to write, and it is also
# the one whose failure is least visible in its output -- a gate implemented as a
# filter writes byte-identical files to one implemented as a hold, right up to the
# poll where the ignition reading equals the pre-boot one. See its builder.
for h in build_panel_test build_end_test build_clock_test build_gui_test build_flow_test build_gate_test; do
	python "_tools/$h.py"
done

for h in panel end clock gui flow gate; do
	echo "=== $h ==="
	# print(), not a bare call: `lua -e` discards the chunk's return value, so the
	# report would be invisible on success and the run would look like a silent
	# no-op. On FAIL the chunk writes its own report to stderr and exits 1, so the
	# gate below still bites without this.
	"$LUA" -e "print(assert(loadfile('_tools/_${h}_states.luau'))())"
	echo "$h rc=$?"
done

echo "=== watch ==="
"$LUA" _tools/watch_harness.luau
# The self-report scenario, run separately because the main one's claim is that
# error.txt is ABSENT. If this ever stops going red on a broken watcher, the
# watcher stops reporting its own death and every other check here reads as
# "quiet" instead of "dead" -- which is the failure mode the whole file exists to
# avoid, so it is gated rather than left as a thing to remember to try.
"$LUA" _tools/watch_harness.luau --boom
# And the start-up death, which is the third reading the operator needed and did not
# have: a shift where the sink got nothing at all.  With the census made to throw,
# hello.txt must still arrive (so "injected" is answered by bytes), error.txt must
# say it was the start-up that died (not a scan), and tree.txt must be absent so its
# absence is never read as "there was nothing to watch".  Same gate as --boom: the
# watcher's own self-report is a feature, and an untested feature is a claim.
"$LUA" _tools/watch_harness.luau --boot
# The recording window's four edges, and each one is a way the operator loses the shift
# he cannot restart: the lever is there but carries no ClickDetector (--nolever), the
# lever's part is not there at all (--nopath) -- both must still record, on the game's
# own flag, and window.txt has to say WHICH of the two happened -- nothing opens the
# window at all (--nowindow), where the timeline still has to reach the sink under a
# marker rather than arriving as an empty file that reads like "the watcher was never
# injected"; and the dial reaching 12:00 (--closewin), which is half of the rule and
# the only thing in the watcher that ends a run by itself.
"$LUA" _tools/watch_harness.luau --nolever
"$LUA" _tools/watch_harness.luau --nopath
"$LUA" _tools/watch_harness.luau --nowindow
"$LUA" _tools/watch_harness.luau --closewin
echo "watch rc=$?"

echo "=== watch slicing differential ==="
# MaxBlockMs bounds the longest uninterrupted walk, so a census over ~92k instances
# cannot freeze the client for its whole duration. That fix puts a clock-dependent
# branch inside a fixture that drives its mutation timeline by COUNTING waits, and
# the first version of it made this suite flaky -- the same unmodified watcher passed
# and failed between runs, because how many yields landed before the lever depended
# on machine load. The fixture no longer counts untimed yields (see the task.wait
# comment in watch_harness.luau); this is the other half of that argument. A yield
# budget is allowed to change WHEN the watcher works, never WHAT it records, and that
# is measurable: run the shipped file, then a copy whose budget is forced to zero
# (yield every SLICE_CHECK instances), and require the two logs to agree line for
# line apart from the wall clock, which is the only column that may differ.
SLICE0=_tools/_slice0.luau
SLICEA=_tools/_slice_a
SLICEB=_tools/_slice_b
rm -rf "$SLICEA" "$SLICEB"
# Anchor by construction and ASSERT it before substituting: MaxBlockMs is named in
# several comments in the watcher, so a looser pattern could rewrite prose instead of
# the config and still look green.
SLICE_ANCHOR=$(grep -c '^    MaxBlockMs = 25,$' _tools/TRG_original_watch.luau)
if [ "$SLICE_ANCHOR" != "1" ]; then
    echo "slicing: FAIL -- the MaxBlockMs anchor matches $SLICE_ANCHOR line(s), not 1."
    echo "         The budget was renamed or reformatted; update this sed before trusting it."
    exit 1
fi
sed 's/^    MaxBlockMs = 25,$/    MaxBlockMs = 0,/' _tools/TRG_original_watch.luau > "$SLICE0"
"$LUA" _tools/watch_harness.luau --out="$SLICEA" >/dev/null 2>&1
"$LUA" _tools/watch_harness.luau "$SLICE0" --out="$SLICEB" >/dev/null 2>&1
# The wall clock is the one column allowed to differ; it is the second field of every
# changes.log line, between the run-relative t= and the first pipe.
no_clock() { sed -E 's/ [0-9]{2}:[0-9]{2}:[0-9]{2} / TIME /' "$1"; }
SLICE_LINES=$(wc -l < "$SLICEA/changes.log")
if [ "$SLICE_LINES" -lt 5 ]; then
    echo "slicing: FAIL -- the baseline log has only $SLICE_LINES line(s);"
    echo "         two empty files are trivially identical and this test would prove nothing."
    exit 1
fi
if diff <(no_clock "$SLICEA/changes.log") <(no_clock "$SLICEB/changes.log") > _tools/_slice.diff 2>&1; then
    echo "slicing: PASS -- $SLICE_LINES log line(s) identical with the yield budget at 0"
else
    echo "slicing: FAIL -- what the watcher records depends on how the walk was sliced"
    cat _tools/_slice.diff
    exit 1
fi
rm -rf "$SLICEA" "$SLICEB" "$SLICE0" _tools/_slice.diff

echo "=== watch mutations ==="
python _tools/selftest_watch.py

# Same argument as the watcher's, and a stronger one here: PlayerGui is
# client-only and does not replicate, so the player-GUI reader can only ever run
# inside a script injected into the ORIGINAL game -- one shot per shift, and the
# operator can only start the game once. A green harness is the whole of the
# evidence available before that shot is spent, which is why the harness has to be
# shown to be capable of failing before it is believed.
echo "=== gui mutations ==="
python _tools/selftest_gui.py

# The end-of-shift rule and the flow boundary are ONE POLICY -- "what is allowed to
# end a run" -- split across two regions of the recorder by where the code lives.
# They were also the two things that produced the 12:32 seal, and until that run the
# end suite had never made its own down-backstop arm fire. Both suites are gated
# here: selftest_flow_test.py mutates the recorder once and rebuilds BOTH harnesses
# against each mutant, so a mutation of either half is caught by whichever file owns
# the check. selftest_end_test.py is a separate run because it was written first and
# covers the arms the flow suite does not touch.
# The transport probe is the odd one out here in one way that matters: it is the
# only file in _tools that is meant to be injected into the ORIGINAL game by itself,
# as a diagnostic that costs an injection and no shift.  A wrong answer from it is
# therefore expensive in a different currency -- it would send the next real run down
# a transport that does not exist.  So it gets the same treatment as everything else:
# a harness with 23 checks, and a mutation run that proves those 23 can go red.  The
# first version of the probe called every transport with the wrong argument shape and
# the first version of its harness stayed green through it -- which is why both exist.
echo "=== transport probe ==="
"$LUA" _tools/transport_probe_test.lua
echo "transport_probe rc=$?"
python _tools/selftest_transport_probe.py

echo "=== end mutations ==="
python _tools/selftest_end_test.py

echo "=== flow mutations ==="
python _tools/selftest_flow_test.py

# Same argument as the gui suite's, and the sharpest version of it: the core gate
# ships into a game the operator can start ONCE per shift. If the harness has no
# opinion, the next thing that finds out is a wasted run -- so the six mutations
# here are each a bug somebody would plausibly write, and each has to turn the
# specific check that guards it red. Two more are meant to stay GREEN and are
# asserted to, because a suite that only ever goes red cannot tell a working
# harness from one whose checks are all `true`.
echo "=== gate mutations ==="
python _tools/selftest_gate_test.py

# The third injected file, and the one whose subject appears EXACTLY ONCE per
# shift: the boot screen can be pressed one time, so a broken boot capture is a
# wasted run. That is the same argument as gui's and gate's, one step stronger,
# because this file has never been injected at all -- its harness is the whole of
# the evidence available before the operator spends the shift.
#
# Three gates, and the middle one is the one that matters:
#   1. a whole-file 5.1 parse. The harness only walks the regions it reaches, and
#      the regions it skips are the ones a real start-up hits first.
#   2. the five scenarios, in the order a run meets them: an injection with no
#      root or no button must still report its OWN death, a sink that refuses
#      everything must still land every chunk on the disk, and the two hotkeys
#      must do what RECORDER_HOWTO says they do. "SKIP" is printed rather than
#      scored as a pass where the scenario makes a check unmeasurable.
#   3. verify_boot_capture.py, which takes the line pattern out of the SEVEN
#      archived readers' own source and requires every data line to match it. The
#      pattern is READ, not retyped: a re-typed copy would keep passing after the
#      readers changed, which is the drift it is here to catch.
"$LUA" -e "
local f, err = loadfile('_tools/TRG_original_boot.luau')
if not f then io.stderr:write('boot recorder does not parse: ' .. tostring(err) .. string.char(10)) os.exit(1) end
print('boot recorder parses: ' .. _VERSION)
"

echo "=== boot scenarios ==="
for s in default nobutton noroot nosink rightcontrol; do
	"$LUA" _tools/boot_harness.luau _tools/TRG_original_boot.luau "$s"
	echo "boot $s rc=$?"
done

echo "=== boot capture readability ==="
# Only the three scenarios that reach the end write a capture. nobutton and noroot
# stop at the death report, which is the whole point of them.
python _tools/verify_boot_capture.py 	_tools/_harness_out/boot_default_ScreenChanges.txt 	_tools/_harness_out/boot_nosink_ScreenChanges.txt 	_tools/_harness_out/boot_rightcontrol_ScreenChanges.txt
echo "verify_boot_capture rc=$?"

echo "=== boot mutations ==="
python _tools/selftest_boot.py

echo
echo "recorder: $(wc -c < _tools/TRG_original_recorder.luau) bytes, $(wc -l < _tools/TRG_original_recorder.luau) lines"
echo "watcher:  $(wc -c < _tools/TRG_original_watch.luau) bytes, $(wc -l < _tools/TRG_original_watch.luau) lines"
