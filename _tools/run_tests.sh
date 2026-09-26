#!/usr/bin/env bash
# Rebuild and run every harness the recorder has, and gate on the exit code.
#
# All three harnesses extract their subject from the SHIPPED recorder by text, so
# a change to _tools/TRG_original_recorder.luau is a change to all three tests.
# That is the point of building them here rather than checking in the generated
# files: there is no copy of driveStep, snapshot or endReason that can drift from
# the one that gets injected.
#
# end_reason is the odd one out -- it extracts a REGION rather than a function,
# because endReason closes over the counters declared above it. Those counters are
# the state under test, so a copy of them here would be a test agreeing with
# itself (see the builder's docstring).
#
#   bash _tools/run_tests.sh
#
# The three files this writes are generated and are NOT the source of truth --
# edit the builders beside them, never the _*.luau.
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

for h in build_panel_test build_driver_test build_end_test build_clock_test; do
	python "_tools/$h.py"
done

for h in panel driver end clock; do
	echo "=== $h ==="
	# print(), not a bare call: `lua -e` discards the chunk's return value, so the
	# report would be invisible on success and the run would look like a silent
	# no-op. On FAIL the chunk writes its own report to stderr and exits 1, so the
	# gate below still bites without this.
	"$LUA" -e "print(assert(loadfile('_tools/_${h}_states.luau'))())"
	echo "$h rc=$?"
done

echo
echo "recorder: $(wc -c < _tools/TRG_original_recorder.luau) bytes, $(wc -l < _tools/TRG_original_recorder.luau) lines"
