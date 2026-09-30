"""One-shot surgery on _tools/TRG_original_recorder.luau.

Two changes, both from the operator's 2026-09-30 message:

  A1  the reactor's own readings are not written until the core is fully on
  A2  the DRIVER section is gone: "不需要什么driver，只需要seal"

Every cut is made by LINE RANGE with an assertion on the first and last line,
because the ranges were read off the shipped file rather than derived, and a
range that has drifted by one line would cut the wrong `end`.  The script is
idempotent in the sense that it refuses to run twice: if the first cut's
assertion fails it exits before writing anything.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "TRG_original_recorder.luau"

raw = SRC.read_bytes()
# A CR anywhere means the file is not the LF-only file every harness here parses,
# and the two writers in this project have disagreed about that before. Checked in
# BYTES, before the decoder can normalise the difference away.
if b"\r" in raw:
    sys.exit("recorder has CR bytes in it -- refusing to edit a file whose line "
             "endings are not LF")
src = raw.decode("utf-8")
lines = src.split("\n")


def at(n):
    """1-indexed line, for reading the assertions out loud."""
    return lines[n - 1]


def cut(lo, hi, expect_lo, expect_hi, what, repl=()):
    """Delete lines lo..hi inclusive, replacing with `repl`.

    Asserted at both ends: `expect_lo`/`expect_hi` are substrings that MUST be
    on those lines.  A near-miss here is a silent corruption two hundred lines
    up the file, which is the one kind of mistake this project keeps making.
    """
    if expect_lo not in at(lo):
        sys.exit("%s: line %d is %r, expected it to contain %r"
                 % (what, lo, at(lo), expect_lo))
    if expect_hi not in at(hi):
        sys.exit("%s: line %d is %r, expected it to contain %r"
                 % (what, hi, at(hi), expect_hi))
    return lo, hi, list(repl), what


EDITS = []

# ---- descending, so no earlier index is disturbed ------------------------

EDITS.append(cut(
    3258, 3265,
    "'drop %d  spill %d  evt %d'", "drive.startIdx - 1, #startCandidates)",
    "refreshLoop drops the driver line",
    [
        "\t\t\t\t'drop %d  spill %d  evt %d',",
        "\t\t\t\tphaseName, sample, lines, segNo, bufBytes, postFails,",
        "\t\t\t\tdropped, spilled, evtNo)",
    ]))

EDITS.append(cut(
    3191, 3226,
    "-- The driver switches a live reactor off by itself", "buoy.drvBtn = drvBtn",
    "the DRIVER on-screen button"))

EDITS.append(cut(
    3130, 3130,
    "pollDt = os.clock() - iterStart", "pollDt = os.clock() - iterStart",
    "the pollDt assignment (its only reader was driveStep)"))

EDITS.append(cut(
    2760, 2770,
    "-- The driver reads the same two numbers", "",
    "the driveStep call site"))

# `tempF` and `isRunning` are computed immediately above the call site and the
# flow boundary below consumes BOTH, so the cut must stop before them. This is
# the one edit whose failure mode is a silently dead boundary rather than a
# syntax error: the boundary reads `isRunning`, and if that line went too the
# file would still parse and the flow would never arm.
for n, want, label in [
        (2757, "local tempF = last['m.temp']", "the temperature read"),
        (2758, "local isRunning = (tempF ~= nil", "the running test"),
        (2771, "if not flowArmed then", "the flow boundary")]:
    if want not in at(n):
        sys.exit("call-site cut: line %d is %r, expected it to contain %r (%s)"
                 % (n, at(n), want, label))

EDITS.append(cut(
    1588, 2163,
    "", "end",
    "the DRIVER section"))

# The DRIVER cut is the only one whose two boundary lines are unremarkable (a
# blank and a bare `end`), so it gets checked against its NEIGHBOURS as well.
# Both must still be what they were: the section above must still end in the
# console-walk's `end`, and the section below must still open with the click
# hooker's comment -- because the one thing this cut must not do is take the
# CLICK hook with it, which is now the ONLY way the operator's own presses reach
# the file.
for n, want, label in [
        (1587, "end", "the console walk's closing end"),
        (1589, "========== DRIVER ", "the DRIVER banner"),
        (2164, "", "the blank after the DRIVER section"),
        (2165, "The user s own clicks are half of the experiment", "the click hooker")]:
    if want not in at(n):
        sys.exit("DRIVER cut: line %d is %r, expected it to contain %r (%s)"
                 % (n, at(n), want, label))

EDITS.append(cut(
    1482, 1487,
    "-- The driver s verdict belongs in the receipt", "' drive=' .. tostring(drive.state)",
    "the receipt's drive= field"))

EDITS.append(cut(
    356, 407,
    "-- The driver s state, forward declared", "",
    "the drive table"))

EDITS.append(cut(
    323, 330,
    "-- How long the previous poll really took", "local pollDt = Config.SampleInterval",
    "the pollDt declaration"))

EDITS.append(cut(
    243, 272,
    "-- ---- end of shift", "\tShutdownEndsShift = true,",
    "the ShutdownEndsShift config block",
    [
        "\t-- ---- end of shift -------------------------------------------------------",
        "\t-- A shift ends the moment the core goes down, and the recorder is what has to",
        "\t-- notice: the client does not wait to be told. The 18:35 run is the",
        "\t-- measurement -- s.GameActive went false on the very last sample the script",
        "\t-- ever took, the loop had no rule that looked at it, and the task.wait that",
        "\t-- followed never returned, so 1.4 MB of good data arrived with no receipt.",
        "\t-- The rule that reads it lives in `endReason`, which is where every other end",
        "\t-- condition lives too.",
        "\t--",
        "\t-- `ShutdownEndsShift` sat here because it told the DRIVER to stop, and the",
        "\t-- driver told the recorder how long to wait after its own press. Both are gone",
        "\t-- with the DRIVER section (2026-09-30, the operator: \"不需要什么driver，只需要seal\"),",
        "\t-- so the flag went with them rather than being left as a constant nothing",
        "\t-- reads -- a config key with no reader is a claim about behaviour that no",
        "\t-- longer exists.",
    ]))

EDITS.append(cut(
    193, 242,
    "-- ---- driver", "",
    "the driver config block"))

EDITS.append(cut(
    28, 48,
    "-- SCOPE: exactly one shutdown -> startup flow", "",
    "the header's SCOPE and DRIVER paragraphs",
    [
        "-- SCOPE: the recorder runs from the instant it is injected, and it seals on",
        "--   exactly the two conditions the operator named (2026-09-30: \"SEAL的情况是1：",
        "--   手动关机，2：核心自动关机如熔毁，温度过低等\") -- a manual shutdown, or an automatic one",
        "--   the reactor does to itself. The boundary is detected from the core state",
        "--   (see the FLOW section), with a manual seal key and an on-screen button as",
        "--   the human's own way out.",
        "--",
        "-- NOTHING ABOUT THE REACTOR IS WRITTEN UNTIL THE CORE IS FULLY ON. See THE CORE",
        "--   GATE, where the signal is named and the two runs that bracket it are cited.",
        "--   The short version: a shift opens with the core COLD, a cold core's readouts",
        "--   are zeroes and error text rather than low numbers, and a file that records",
        "--   them from the first poll cannot show the ignition at all.",
        "--",
        "-- THE RECORDER PRESSES NOTHING. A DRIVER section used to work the two switches",
        "--   on its own, through the injector's `fireclickdetector`; it is gone, because",
        "--   the operator does not want one (\"不需要什么driver，只需要seal\") and because a",
        "--   press it did not need is a press it must not invent on a shift he cannot",
        "--   restart. The replacement is his own hand, and every press of it is still",
        "--   recorded: the CLICK hook below is untouched and hooks every ClickDetector",
        "--   and ProximityPrompt in the world, named or not. The trade-off is written up",
        "--   in DECISIONS_2.",
    ]))

# ---- apply, descending ---------------------------------------------------
for lo, hi, repl, what in EDITS:
    lines[lo - 1:hi] = repl
    print("cut %-52s %5d..%-5d -> %d line(s)" % (what, lo, hi, len(repl)))

text = "\n".join(lines)

# ---- A1: the core gate --------------------------------------------------
GATE = '''-- ==================== THE CORE GATE =======================================
-- NOTHING ABOUT THE REACTOR IS WRITTEN UNTIL THE GAME SAYS THE CORE IS ON.
--
-- The operator's rule (2026-09-30): "注入后立刻开始（注意在核心完全开启前不要采集温度、
-- 压力等）". A shift opens with the core COLD, and a cold core's readouts are not low
-- numbers, they are NOTHING: `s.Core.TemperatureVal` sits at 0, the pressure at its
-- resting value, and the monitor prints its own error text. A file that records
-- those from the first poll is a file whose opening third is a stream of zeroes
-- and `ERR F` that describes no reactor state at all -- and, worse, it hides the
-- one thing the opening is for. The interesting fact is the moment the reading
-- STARTS, and a reading already being written at 0 cannot show it.
--
-- THE SIGNAL IS `Stats.GameActive`, AND IT IS A MEASUREMENT RATHER THAN A GUESS.
-- Two runs on disk bracket it from both sides:
--
--   * original_260930-200834 -- the lever WAS pressed (EVT3170 CLICK StartUpLever)
--     and the boot banner ran all the way to `ALL SYSTEMS PRIMED`, and the core
--     still never lit: four state transitions in the whole file, all at t=5.28, and
--     not one `s.GameActive=true`. So GameActive does not fire at the lever, and it
--     does not fire when the banner finishes either.
--   * original_260926-230049 -- `s.Core.TemperatureVal` 0 at t=1.34, then 510 F at
--     t=88.53, 9420 F at t=97.90, and `s.GameActive=true` at t=98.47. It goes true
--     at the TOP of the ignition ramp, which is exactly "the core is fully on".
--
-- IT LATCHES, AND THE LATCH IS NOT AN OPTIMISATION. The readers gated here are the
-- same readers that have to keep working AFTER the shutdown -- the cold-trip arm
-- reads `m.temp` under LowTripF for `SealColdSamples` polls -- so a gate that
-- closed again when GameActive went false would silence the very readings the seal
-- rule is made of. Once open it stays open for the rest of the run.
--
-- WHAT IT DOES NOT COVER, on purpose: the generic readout walk (`t.*`) and the
-- facility panels. Those are where the BOOT SEQUENCE itself gets recorded, and
-- gating them would throw away the thing this recorder was pointed at. The gate is
-- about the reactor's own readings -- the ReactorFrame labels and `Stats.Core` --
-- and nothing else.
local coreLive = false

-- Opens the gate if the game says the core is up, and answers whether it is open.
-- Read from the game's own flag and not from a temperature, because the
-- temperature is the thing being gated: deriving the gate from it would make the
-- recorder's first reading depend on a value it has already decided not to trust.
local function coreGateOpen()
	if coreLive then return true end
	local flag = MainData and MainData:FindFirstChild('GameActive')
	if flag == nil or not flag:IsA('ValueBase') then return false end
	if flag.Value ~= true then return false end
	coreLive = true
	-- Announced as an event, so the file itself carries the fact that the readings
	-- below this point are the live ones. A reader who finds the batch that
	-- follows can now tell "the core came on here" from "the core was on before
	-- the recorder arrived" without re-deriving it from a temperature.
	emitEvt('COREGATE', 'Stats.GameActive went true; the core is fully on and the'
		.. ' reactor readings start from this poll')
	return true
end

-- Whether a Stats path is one of the reactor's own readings. The test is on the
-- container `Core` rather than on a list of leaf names, because a list is a thing
-- a rename escapes silently: TemperatureVal, PressureVal, RadiationVal, OutputVal,
-- HDEFVal and BreachVal all live under it, and anything added there later is
-- covered without this file being edited.
local function isCoreStat(path)
	return path == 'Core' or path:sub(1, 5) == 'Core.'
end

local function readReactor()
	if not coreGateOpen() then return end
	if ReactorFrame == nil then return end'''

old_reactor_head = """local function readReactor()
\tif ReactorFrame == nil then return end"""
assert text.count(old_reactor_head) == 1, "readReactor head not unique"
text = text.replace(old_reactor_head, GATE)

old_stats_head = """local function readStats()
\tif MainData == nil then MainData = Workspace:FindFirstChild('Stats') end
\tif MainData == nil then return end"""
new_stats_head = """local function readStats()
\tif MainData == nil then MainData = Workspace:FindFirstChild('Stats') end
\tif MainData == nil then return end
\t-- Called here as well as in readReactor even though pollOnce always runs
\t-- readReactor first. The gate is idempotent and latches, so the second call is
\t-- free; what it buys is that neither reader depends on the other having run,
\t-- and this file has lost a day to exactly that kind of ordering assumption.
\tcoreGateOpen()"""
assert text.count(old_stats_head) == 1, "readStats head not unique"
text = text.replace(old_stats_head, new_stats_head)

old_stat_write = """\t\t\tif d:IsA('ValueBase') then
\t\t\t\tlocal v = d.Value
\t\t\t\tlocal t = type(v)
\t\t\t\tif t == 'number' or t == 'boolean' then
\t\t\t\t\tput('s.' .. path, v)
\t\t\t\telseif v ~= nil then
\t\t\t\t\t-- A StringValue, or a type with no space-free rendering.
\t\t\t\t\tputText('s.' .. path, tostring(v))
\t\t\t\tend
\t\t\tend"""
new_stat_write = """\t\t\tif d:IsA('ValueBase') then
\t\t\t\t-- HELD BACK until the core is on, and "held back" means not written at
\t\t\t\t-- all: `last` is not touched either, so the first sample after the gate
\t\t\t\t-- opens arrives as a NEW key and the ignition shows up in the file as
\t\t\t\t-- its own batch. Writing the pre-boot zero into `last` and then letting
\t\t\t\t-- the real reading differ from it would record the same fact as one
\t\t\t\t-- line of noise inside a run of changes, which is how it gets missed.
\t\t\t\t--
\t\t\t\t-- The traversal is NOT gated: `seen[path]` is set above either way, so a
\t\t\t\t-- held-back key is still a key the STATADD/STATDEL announcement knows
\t\t\t\t-- about and the goings and comings of the container are still recorded
\t\t\t\t-- exactly as before.
\t\t\t\tif coreLive or not isCoreStat(path) then
\t\t\t\t\tlocal v = d.Value
\t\t\t\t\tlocal t = type(v)
\t\t\t\t\tif t == 'number' or t == 'boolean' then
\t\t\t\t\t\tput('s.' .. path, v)
\t\t\t\t\telseif v ~= nil then
\t\t\t\t\t\t-- A StringValue, or a type with no space-free rendering.
\t\t\t\t\t\tputText('s.' .. path, tostring(v))
\t\t\t\t\tend
\t\t\t\tend
\t\t\tend"""
assert text.count(old_stat_write) == 1, "readStats write block not unique"
text = text.replace(old_stat_write, new_stat_write)

# ---- the build tag ------------------------------------------------------
old_build = "\tBuild           = 'r58',"
new_build = """\t-- r60: the DRIVER section is gone (no driver; the operator's hand does the
\t-- pressing) and the reactor readings are gated on the core being fully on.
\t-- r58: the low-trip line is 1000 F, which is a MEASUREMENT and not a new
\t-- number, and every artifact now carries its build tag.
\tBuild           = 'r60',"""
assert text.count(old_build) == 1, "Build tag not unique"
text = text.replace(old_build, new_build)

out = text.encode("utf-8")
if b"\r" in out:
    sys.exit("edit introduced CR bytes")

SRC.write_bytes(out)
print("wrote %s: %d bytes, %d lines" % (SRC, len(text.encode("utf-8")), text.count("\n") + 1))
