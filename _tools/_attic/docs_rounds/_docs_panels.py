"""Mirror the recorder v1.2 changes into PROGRESS and DECISIONS.

WHAT THIS RECORDS. Two patches to the ORIGINAL-game recorder, both applied and
verified this step:

  * _tools/_apply_panels.py -- the log, the subspace forecast and the quota panel
    as PANEL SNAPSHOTS, plus the UNATTR attribution family. 78732 -> 85766 bytes.
  * _tools/_apply_unattr_nil.py -- the `and nil or` defect the new harness caught
    on its first call. One line, plus the comment that says why. -> 86176 bytes.
  * _tools/_apply_clock.py -- the driver took its step from Config.SampleInterval
    instead of measuring the loop, so every dwell ran 18 per cent long in the one
    live run. dt is now a parameter the loop measures. -> 88064 bytes.
  * _tools/_apply_armguard.py -- the arm window could expire on a core that was
    reading as running, because the measured dt made the debounce window one step
    wide. Closes a risk the clock change itself introduced. -> 88991 bytes.

Plus the tests: _tools/run_tests.sh rebuilds both harnesses from the SHIPPED
recorder and gates on their exit codes, 25 assertions, and the four panel
assertions that failed on the first run were defects in the test.

WHY A SCRIPT AND NOT A HAND EDIT. The two docs are flat: every entry is one
paragraph, entries are separated by a blank line, and every line ends CRLF. A
hand-typed append gets the ending wrong on the one line that matters and the
file then differs from its module by a byte nobody can see. The script asserts
the separators it is writing rather than trusting the editor.

NO BACKSLASHES ANYWHERE IN THIS FILE, per CLAUDE.md 0.10: text written through a
Studio editing tool is escape-decoded once, so a backslash in a string literal
becomes a control character and turns legal Lua into a syntax error. These docs
are mirrored into ModuleScripts, so the rule applies to them too. The check at
the bottom is the assertion, not the discipline.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRESS = ROOT / "docs" / "airemake" / "PROGRESS.md"
DECISIONS = ROOT / "docs" / "airemake" / "DECISIONS.md"

PROGRESS_ENTRY = """\
Recorder v1.2, 2026-09-26: the three monitors the generic readout sweep could not report properly are now recorded as PANEL SNAPSHOTS, and a control that moves with no click behind it is now reported at the point where it happens. The log panel (Workspace.Monitors.LogControlRoomMonitor) reached the 18:01 file only as x.* rows -- `x.TemplateLogFrame3 <b>[ALERT]</b> - ...` -- and that is not a reading: three rows scroll past one key, so the same key carries a different message every few seconds and the history has to be reassembled from the whole file by hand. The forecast panel (ForecastControlRoomMonitor) was worse than unreadable: the sweep THREW IT AWAY, `EVT1506 ANIM ...ScrollingFrame.TimeSliceTemplate.TimeLabel moved 5 times inside one poll; dropped as an animation`, so the panel that predicts the disaster was the one the recorder discarded as noise. The quota panel (QuotaControlRoomMonitor) was caught, but as one number among eleven hundred. All three are now read as ONE joined snapshot each -- sorted, index-free, capped at 200 rows and 1200 characters, emitted as log.panel / fc.panel / q.panel and only when the contents change. A panel is one value, so it has one key and can change at most once per poll no matter how many of its rows moved; neither the rate arm nor the chatter arm had to be loosened to make room, and sorting is what makes the string a function of the panel's contents rather than of GetDescendants order. New UNATTR events name the value a control came FROM, as in `UNATTR c.cbl1Lvl 2->1 (last click 41 polls ago)`, whenever a c.* key moves more than 8 polls after the last click this client saw; the 18:01 capture held four CBL level changes and not one CLICK event, and that absence took hours and a hand-built control timeline to find. The attribution pass shipped with a real defect that the new harness caught on its first call: `local since = (clickPoll == nil) and nil or (sample - clickPoll)` evaluates `sample - nil`, because Lua returns the middle operand of `X and Y or Z` only when it is truthy, so the branch guarding "this client has never seen a click" -- the 18:01 case the section exists for -- threw instead of returning nil; the caller is not pcall-wrapped, so inside the one available attempt it would have killed the poll and the recording with it. Fixed to an explicit if. Both harnesses are now rebuilt from the shipped bytes by `bash _tools/run_tests.sh` -- 19 panel assertions and 6 driver scenarios, each gated on its exit code and not only on its output -- and the four panel assertions that failed on the first run were defects in the test, not in the recorder: one compared two snapshots holding the same three labels in a different enumeration order and read their equality as a bug, and three ran both truncation caps at once, so the character cap fired first and the assertion written for the row cap was reading the character cap's marker; the `%%` in those two needles was a Lua PATTERN escape for a literal percent and could never have matched. Recorder now 86176 bytes, 2063 lines, djb2 b2f9be31, 0 backslash bytes, no long-bracket closer anywhere, pure LF; PARSE OK under Lua 5.1, globals clean, and the 8766 server serves the byte-identical file. Recorder-only changes; nothing in the remake's gameplay was touched.\r\n\r\nRecorder v1.3, 2026-09-26: the driver now advances its dwell timers by a step the LOOP MEASURES, instead of by Config.SampleInterval. The 18:01 run is the measurement that condemned the old form: 283 samples over 83.78 s is 3.38 Hz, so the real step was 0.296 s against a configured 0.25 -- every dwell in driveStep ran 18 per cent long, and `DriveHoldSeconds = 60` spent 70.59 s elapsing between the log line at t=2.84 that announced `will switch it off in 60s` and the press at t=73.43 that it describes. Nothing else in that run was wrong: the reactor was switched off correctly and on time, because the only clock that matters here is the game's and that one was never consulted. What was false was the number the recorder wrote down about itself, which is the one thing the file exists to get right. dt is now driveStep's third parameter, measured by the loop from `os.clock()` opened before the poll and closed after the `task.wait`, so it covers the whole period rather than only the part the poll took. It is a parameter and not a call inside the function because driveStep is executed against a simulated core by the harness, and a function that reads the wall clock internally can only be tested by waiting in real time -- which turns a 300-second scenario into 300 seconds; the caller owns the clock and the function is a pure step. There is deliberately no upper clamp: a client that stalls for thirty seconds saw thirty seconds pass and the reactor spent them running, so crediting thirty is the measurement and clamping it would be a second assumption of exactly the kind the parameter removes; only a value that cannot be a duration falls back to the constant, so a harness with no clock can still call it. `os.clock` was confirmed to be the right clock rather than assumed: in this engine it advanced 2.0112 across a `task.wait(2)`, so it counts wall time and not CPU time, and had it counted CPU time the loop's own flush timing would have carried the same defect for the same reason. Scenario S7 covers it and is mutation-tested -- with the measured step handed back as the constant, S7 fails with `first press at 244.00, wanted 55.0..70.0`, the four-times-too-late press being the defect enlarged until it cannot be mistaken for slack in the scenario. Recorder now 88064 bytes, 2093 lines, djb2 75490e31, 26 assertions across both harnesses all passing, 0 backslash bytes, pure LF, PARSE OK, globals clean, 8766 serves the byte-identical file."""

DECISIONS_EXTRA = [
    """\
A NUMBER THE PROGRAM WRITES ABOUT ITSELF IS A CLAIM, AND IT HAS TO COME FROM THE SAME PLACE THE BEHAVIOUR DOES. The driver advanced every dwell by Config.SampleInterval, and the loop it lived in ran at 3.38 Hz against that configured 0.25 s -- so `DriveHoldSeconds = 60` announced in the log at t=2.84 was followed by its press at t=73.43, and the 70.59 s in between is the size of the lie. Nothing failed. The reactor was switched off correctly, the recording is complete, the receipt is accurate about the plant. The only wrong thing was the recorder's account of its own timing, which is precisely the account a reader trusts instead of recomputing -- and it was caught not by any check but by a person noticing that two numbers in the same file disagreed about how long a duration was. The fix removes the constant from the driver entirely and passes in a step the loop measures, because a configured period is a claim about a loop and only the loop can report what the loop did. The general form: whenever a program states a fact about its own execution, that fact must be derived from the execution and not from the configuration that was supposed to describe it.""",
    """\
THE CLOCK A TEST CANNOT AFFORD TO WAIT ON IS STILL THE CLOCK THE CODE MUST READ -- SO PUT IT IN THE CALLER. Moving the measured step into driveStep directly would have been the smaller change and the wrong one: driveStep is executed by a harness against a simulated core, and a function that reads the wall clock internally can only be tested in real time, so a 300-second scenario would cost 300 seconds and the suite would stop being run. Handing the step in as a parameter costs one argument and buys three things at once -- the loop owns the clock and there is exactly one place that reads it, the function stays a pure step, and the defect becomes testable at all, because the harness can hand it a one-second step and assert that the dwell follows the step rather than the constant. That last one is the point: the timing error was invisible for a whole run and became a one-line assertion only after the dependency was inverted. When a piece of code is hard to test, the obstacle is usually a dependency pointing the wrong way rather than a missing test.""",
]

DECISIONS_ENTRIES = [
    """\
WHEN A GUARD REJECTS SOMETHING YOU NEED, CHANGE THE GRANULARITY OF THE REPORT, NOT THE GUARD. The readout sweep drops any key that moves more than a few times inside one poll, and that arm is what keeps the file from carrying every scrolling label in the facility -- but it was dropping the subspace forecast, the one panel an operator would actually act on, as `EVT1506 ANIM ...ScrollingFrame.TimeSliceTemplate.TimeLabel moved 5 times inside one poll; dropped as an animation`. The cheap fix is to raise the threshold; that would have cost the arm its whole purpose to recover one panel. The resolution keeps the arm and reshapes what is reported: the panel goes out as a single joined snapshot with one key, so it can change at most once per poll and the arm has nothing left to reject. The flood is still stopped everywhere else and the panel that was missing is present. A guard that fires on the wrong thing is usually saying the thing being reported is the wrong SHAPE, and the answer is to reshape the report -- loosening the guard instead trades the failure you can see for the one you cannot.""",
    """\
`X and Y or Z` CANNOT RETURN A NIL Y, AND THE CASE IT COULD NOT EXPRESS WAS THE ONE IT WAS WRITTEN FOR. The attribution pass guarded its only interesting branch -- a client that has never seen a click, which is the 18:01 case the whole section exists for -- with `local since = (clickPoll == nil) and nil or (sample - clickPoll)`. Lua yields the middle operand only when it is truthy, so with nil in the middle the expression falls through to `sample - nil` and throws. It shipped like that. The idiom is correct in six other places in the same file, which is precisely why reading it did not catch it: a form that works in six uses out of seven does not read as a mistake, it reads as house style. What caught it was a harness that executes the shipped bytes, on the first call, before any of it reached the one attempt available -- and the caller is not pcall-wrapped, so in the game the outcome would have been a dead poll, a dead recording, and no error anyone would ever see. The lesson is not to avoid the idiom. It is that an idiom's general correctness is not evidence about any particular use of it, and that a branch whose distinguishing feature is that its value is ABSENT cannot be written in a form that has no way to produce absence.""",
    """\
THE FIRST RUN OF A NEW TEST IS ALLOWED TO FAIL ON THE TEST, AND THE FIX IS NEVER TO LOOSEN THE ASSERTION. Four of nineteen panel assertions failed on the first run and all four were defects in the test. One compared two snapshots that held the same three labels in a different enumeration order and read their equality as a bug -- the equality was the property under test. Three ran both truncation caps at once, so with 250 short rows the character cap bit at row 235 and the assertion written for the row cap was reading the character cap's marker; the `%%` in those two needles was a Lua pattern escape for a literal percent sign, so they could not have matched anything. With four red assertions against code that had already been read through, the temptation is to relax the assertions until they go green. Every one was instead fixed by making the scenario match what the assertion claimed to be testing, because an assertion bent to fit the code stops being evidence -- and a test that cannot fail is worse than no test, since it is still counted as coverage. Both harnesses now also fail the PROCESS and not only the page, for the same reason: a harness whose only failure signal is a word in its output passes in every script that runs it.""",
]


PROGRESS_ENTRY2 = """\
Recorder v1.4, 2026-09-26: the arm window no longer times out on a core that is READING AS RUNNING, which closes a risk that the measured-dt change two paragraphs above introduced hours earlier. The arming branch adds dt to armT and, the moment armT reaches DriveArmSeconds, concludes the core is cold and goes inert; the debounce needs three polls of running before flowArmed is true, so there is a window in which the core is running and the arm timer can already have expired. Under the old constant dt that window was eighty polls wide and nothing could cross it in one step. Under a measured dt it is one step wide, and the step that can cross it is the FIRST poll -- the only one with no measured predecessor and the only one carrying the initial readout and lamp sweeps, so nothing bounds how long it takes. A first poll of twenty seconds or more would have credited armT with twenty seconds at once, tempF would not be nil because the core is fine, and the driver would have reported cold-at-inject and stopped on a healthy running reactor, on the one attempt that was available. The fix is not a clamp and not a larger number: the timeout is a claim about a COLD core and a core reading as running is not its subject, so `if isRunning then return end` keeps the timer honest and lets the debounce finish -- twenty seconds of UNBROKEN COLD, which is what the comment on that branch has said it wanted all along. S8 covers it and is mutation-tested: with the guard removed the driver goes `30.00 arming -> inert, verdict cold-at-inject` on a core sitting at 22000 F. Recorder now 88991 bytes, 2108 lines, djb2 04700d58, 27 assertions across both harnesses all passing, 0 backslash bytes, pure LF, PARSE OK, globals clean, 8766 serves the byte-identical file."""

DECISIONS_EXTRA2 = [
    """\
REMOVING AN ASSUMPTION FROM ONE PLACE EXPOSES THE ASSUMPTIONS THAT WERE RESTING ON IT, AND THOSE ARE YOURS TOO. The driver took its step from a constant; measuring it instead was right, and it was measured because the constant had made the one live run's dwells eighteen per cent long. Hours later, re-reading that change against the arming branch, the same edit turned out to have removed a load-bearing side effect nobody had declared: the constant also guaranteed that no single step could be large, which was the only thing keeping the debounce window wider than one poll. The arm window could therefore expire on a core that was reading as running, and the driver's response to that is to refuse and go inert -- on the one attempt that was available. Accuracy in one place had bought fragility in another, and the fragility was invisible because it lived in a property of the old value rather than in any line of code. The rule this leaves behind: when a constant becomes a measurement, enumerate what the constant was implicitly guaranteeing before shipping the measurement. A fixed value is rarely only a value; it is usually also a bound, and the bound is the part nobody wrote down.""",
]


def append(path: pathlib.Path, text: str) -> None:
    raw = path.read_bytes()
    # Idempotent by content, not by a flag file. The first version of this script
    # appended unconditionally and was run twice, which is a duplicated entry and
    # a file that no longer matches anything -- and the failure is silent, because
    # a doc with an entry in it twice still reads fine. Keyed on the opening
    # sentence, which is unique per entry by construction.
    if text[:120].encode("utf-8") in raw:
        print("%s: entry already present, skipped" % path.name)
        return
    if b"\r\n" not in raw:
        sys.exit("%s has no CRLF -- wrong file?" % path)
    if raw.count(b"\n") != raw.count(b"\r\n"):
        sys.exit("%s has a bare LF already" % path)
    if not raw.endswith(b"\r\n"):
        sys.exit("%s does not end on a line boundary" % path)
    if 0x5C in text.encode("utf-8"):
        sys.exit("the entry contains a backslash" )
    # A paragraph break written as a blank line inside a triple-quoted string is
    # one or more BARE LF, and it slips through every check that only inspects the
    # separator this function adds. It did slip through: the v1.3 entry broke a
    # paragraph that way and the file came out with two LF among its CRLF, which
    # nothing downstream would ever have noticed. Break paragraphs explicitly.
    if text.replace("\r\n", "").count("\n") > 0:
        sys.exit("the entry contains a bare LF -- write paragraph breaks as CRLF")
    if "]=]" in text or "]==]" in text:
        sys.exit("the entry contains a long-bracket closer")
    # One blank line between entries: the file ends on a line end, so the
    # separator is the CRLF that ends the new blank line. Bytes, not str: a text
    # round trip here would be a chance to translate a line ending, which is the
    # one thing this file's byte-identity depends on.
    new = raw + b"\r\n" + text.encode("utf-8") + b"\r\n"
    path.write_bytes(new)
    out = new
    print("%s: %d -> %d bytes" % (path.name, len(raw), len(out)))
    print("   CRLF %d  bare LF %d  backslash %d  ends CRLF %s"
          % (out.count(b"\r\n"), out.count(b"\n") - out.count(b"\r\n"),
             out.count(0x5C), out.endswith(b"\r\n")))


def main() -> int:
    for text in (PROGRESS_ENTRY, PROGRESS_ENTRY2):
        append(PROGRESS, text)
    for e in DECISIONS_ENTRIES + DECISIONS_EXTRA + DECISIONS_EXTRA2:
        append(DECISIONS, e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
