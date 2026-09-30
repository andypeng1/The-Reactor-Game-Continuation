#!/usr/bin/env python3
"""Break the watcher on purpose, one thing at a time, and check that the SPECIFIC
assertion which should notice is the one that turns red.

WHY THIS IS NOT PARANOIA.  watch_harness.luau went 40/40 on the first run it was
ever executed.  A suite that has never failed is indistinguishable from a suite
that cannot fail -- every check in it could be `check('x', true)` and the output
would be identical.  The only way to tell those apart is to make a known-bad
watcher and confirm the right check objects, which is what this does.

The discipline it enforces on itself (same as build_clock_test.py and the other
builders): every edit anchors on a string that must occur EXACTLY ONCE.  That rule
is not decoration -- an anchor that matched twice once wrote an entire function
into the wrong block and the module stopped exporting it, with no symptom at all
until a pcall failed silently every tick.  So a non-unique anchor here is reported
as a failure of the TEST, not skipped.

Each mutation also names a check that must STAY green.  Without that, a mutation
that simply destroys the watcher would satisfy "the target check went red" while
proving nothing about whether the check is measuring the right thing.

  python _tools/selftest_watch.py

Prints one line per mutation and exits 1 if any of them was not detected.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(ROOT, "_tools", "TRG_original_watch.luau")
MUTANT = os.path.join(ROOT, "_tools", "_watch_mutant.luau")
HARNESS = os.path.join("_tools", "watch_harness.luau")
LUA = "D:/Lua/5.1/lua.exe"


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


# name, anchor, replacement, must go red, must stay green, diff_file
#
# diff_file is for a mutation whose effect is real but has no absolute invariant to
# grep for.  Dropping the release sort reorders changes.log, but "changes.log is
# non-decreasing in t=" is NOT a property the watcher actually guarantees: a line
# released at tick 31 can carry a tick as old as 26, and a report drain at tick 30
# may already have written a stamp of 30.  Asserting it anyway would be a check that
# is right about this fixture and wrong about the program.  So that one is asserted
# DIFFERENTIALLY against the baseline instead -- always true when the sort is doing
# something, never an invented invariant.
MUTATIONS = [
    (
        "the quiet release never fires",
        "        if #list > 0 and lastTick[j] and tick - lastTick[j] > CONFIG.QuietScans then",
        "        if #list > 0 and lastTick[j] and tick - lastTick[j] > 999999 then",
        ["suppressed.txt counts the keys released on quiet"],
        ["the discrete key reached changes.log"],
    ),
    (
        "the hold ring never overflows",
        "    if #list > CONFIG.NoisyAfter then",
        "    if #list > 999999 then",
        ["the noisy key was judged ambient"],
        ["the discrete key reached changes.log"],
    ),
    (
        "a duplicate path stops getting a suffix",
        "        suffix = string.format(' ~(%.1f, %.1f, %.1f)', pos.X, pos.Y, pos.Z)",
        "        suffix = ''",
        ["a duplicate GetFullName got a path suffix"],
        ["the click detector is watched"],
    ),
    (
        "the audio walk registers anything propsFor knows",
        "        if inst:IsA('SoundGroup') or inst:IsA('SoundEffect') then",
        "        if propsFor(inst) ~= nil then",
        ["a template in ReplicatedStorage did NOT become a watched key"],
        ["the sound group is watched as a bus"],
    ),
    (
        "DescendantAdded is connected but does nothing",
        "            register(d, r.name)\n        end)",
        "            local _ = d\n        end)",
        ["a ValueBase ADDED mid-run is watched"],
        ["the stats values are watched"],
    ),
    (
        "a sound already playing at attach is not read",
        "    if ok and playing then",
        "    if ok and false then",
        ["ALREADY-PLAYING was read off the instance"],
        ["a hooked play was caught"],
    ),
    (
        "the playback poll is never called",
        "    pollAudio()\n    scanMs = (os.clock() - t0) * 1000",
        "    -- pollAudio()\n    scanMs = (os.clock() - t0) * 1000",
        ["an unhookable sound was caught by the poll"],
        ["a hooked play was caught"],
    ),
    (
        "the poll does not latch on the transition",
        "            local was = rec and rec.playing or false",
        "            local was = false",
        ["the poll did not repeat itself while it stayed playing"],
        ["an unhookable sound was caught by the poll"],
    ),
    (
        "the skip reason stops naming the budget",
        "            r.skipped = string.format('over PerRootBudget (%d)', CONFIG.PerRootBudget)",
        "            r.skipped = 'over budget'",
        ["census names the skip reason"],
        ["census drilled into the skipped root"],
    ),
    (
        "the total budget shrinks to nothing",
        "    TotalBudget = 80000,",
        "    TotalBudget = 10,",
        ["the smaller roots were taken"],
        ["the giant is absent from the watch"],
    ),
    (
        "the pin is dropped, so the root it names is at the budget's mercy",
        "    Pinned = {'Alarms', 'Monitors', 'MonitorsFacility'},",
        "    Pinned = {},",
        ["rooms.txt names the root pinned by name"],
        ["the giant is absent from the watch"],
    ),
    (
        "the pin exempts the roots it does NOT name",
        "    Pinned = {'Alarms', 'Monitors', 'MonitorsFacility'},",
        "    Pinned = {'Facility'},",
        ["the giant is absent from the watch"],
        ["census counted the giant"],
    ),
    (
        "the destroyed line is built but not logged",
        "            logLines[#logLines+1] = string.format('%s | %-18s | %s | DESTROYED',",
        "            local _dead = string.format('%s | %-18s | %s | DESTROYED',",
        ["a destroyed instance is reported"],
        ["the discrete key reached changes.log"],
    ),
    (
        "a newline inside a value is allowed through",
        "    return string.gsub(string.gsub(s, NL, ' '), string.char(13), ' ')",
        "    return s",
        ["a newline inside a value did not split the log line"],
        ["the discrete key reached changes.log"],
    ),
    (
        # THE RELEASE SORT -- releaseQuiet's `batch`, not drainHeld's `pending`.  Which
        # one this is took a run to establish: the first version of this mutation was
        # paired with a fixture whose only interleaved rings were still held when the
        # run ended, so the lines went out through drainHeld and the mutation came back
        # NOT DETECTED while the suite looked like it had covered the sort.  Two sorts
        # with identical bodies need two witnesses, and the harness now carries the
        # 100..103 pair (released in one batch at tick 109) for this one and the
        # 116..119 pair (still pending at Report) for the next one.
        "the held lines are appended without being sorted",
        "    table.sort(batch, function(a, b)\n        if a.tick ~= b.tick then return a.tick < b.tick end\n        return a.key < b.key\n    end)\n",
        "",
        None,
        ["the discrete key reached changes.log"],
        "changes.log",
    ),
    (
        # The other sort, in the end-of-run drain.  Same body, different function, and
        # the failure it guards is the one that was actually shipped first: sorting
        # whole RINGS by their first move keeps each ring intact but interleaves the
        # keys wrongly, so an early-starting key's late lines land above a later key's
        # early ones.
        "the end-of-run drain is appended without being sorted",
        "    table.sort(pending, function(a, b)\n        if a.tick ~= b.tick then return a.tick < b.tick end\n        return a.key < b.key\n    end)\n",
        "",
        None,
        ["the discrete key reached changes.log"],
        "changes.log",
    ),
    # ---- streamed or dumped (the 2026-09-27 "write the start-up down" order) ----
    (
        # The strongest mutation in this file, and the reason it exists: holding the
        # timeline until the end produces the SAME FILE -- same lines, same order, all
        # the same substrings -- so every content check above stays green while the
        # product is destroyed.  The operator's instruction was that the changes have
        # to reach a file so the start-up can be read afterwards; a log that arrives
        # only after the run has no use for that.  Nothing but the arrival clock can
        # see the difference, so this pairing is what proves the clock is doing work.
        #
        # AND IT IS THE ONLY MUTATION THAT MAY CLAIM THE STREAMING CHECK.  The
        # obvious second candidate -- disarming the quiet release -- was tried here
        # first and the suite refused it: with releaseQuiet dead the log is still
        # streamed, by every key that is not being held, so the streaming check
        # legitimately stays green.  "Every line reaches the file" and "every line
        # reaches the file WHILE IT IS HAPPENING" are two different claims, and only
        # forcing `and force` collapses the second without touching the first.
        "the timeline is held until the end instead of streamed",
        "    if recording and #logLines > 0 then\n        post('changes.log', table.concat(logLines, NL) .. NL, true)",
        "    if recording and #logLines > 0 and force then\n        post('changes.log', table.concat(logLines, NL) .. NL, true)",
        ["changes.log was written to while the run was still going"],
        ["changes.log was written"],
    ),
    (
        "the audio track is held until the end instead of streamed",
        "    if recording and #audioLines > 0 then\n        post('audio.txt', table.concat(audioLines, NL) .. NL, true)",
        "    if recording and #audioLines > 0 and force then\n        post('audio.txt', table.concat(audioLines, NL) .. NL, true)",
        ["audio.txt was streamed rather than held to the end"],
        ["a hooked play was caught"],
    ),
    # ---- the boot line and the start-up guard (the 2026-09-27 lost shift) ----
    (
        "the boot line is never written",
        "    post('hello.txt', bootReport(), false)\n",
        "    -- the boot line was removed by the mutation\n",
        ["hello.txt was written"],
        ["tree.txt was written"],
    ),
    (
        # The guard is what turns an unreadable run into a diagnosable one, and it
        # cannot be tested by a check that merely reads a file: with the pcall gone
        # the census throws inside task.spawn, nothing is written, and the harness
        # only survives because the boot scenario swallows the raise.  So the
        # pairing is the two halves of the same reading -- the artefact that proves
        # the watcher WAS injected stays green while the one that proves it DIED
        # goes red, which is precisely the distinction the shift was missing.
        "the start-up walk is not guarded",
        "        local booted, bootErr = pcall(bootWalk)\n",
        "        bootWalk()\n        local booted, bootErr = true, nil\n",
        ["error.txt WAS written when the census threw"],
        ["hello.txt WAS written even though the census threw"],
        None,
        ["--boot"],
    ),
    (
        "the start-up death is reported as a scan death",
        "                '# the watcher died during its start-up, before anything was watched' ..\n",
        "                '# the watcher died on tick 0' ..\n",
        ["error.txt names the START-UP as the phase it died in"],
        ["error.txt WAS written when the census threw"],
        None,
        ["--boot"],
    ),
    # ---- the recording window (「按下开机拉杆开始记录，游戏时间到12：00结束记录」) ----
    (
        # The bug this mutation restores is the one the wiring actually shipped with:
        # openWindow counted `#logLines` and cleared it, but a key that was still MOVING
        # when the lever went down has its lines in a held ring, not in logLines -- so
        # the count said 0 and the rings went on to release t=1 and t=2 lines into a
        # file whose own OPEN marker was stamped t=3.  A number that denies what the
        # file beneath it shows is the whole failure, and only the stamp comparison can
        # see it: the string the first version searched for (`QUICK BOOT UP INITIALIZED`)
        # is ALSO the `from` value of a legitimate post-window line, so that check both
        # missed the real leak and cried wolf on a correct file.
        "the held rings are neither counted nor dropped at the open",
        "    local ringed = 0\n    for j, list in pairs(held) do\n        ringed = ringed + #list\n        held[j] = {}\n    end\n",
        "    local ringed = 0\n",
        ["no recorded line is stamped before the OPEN marker"],
        ["the discrete key reached changes.log"],
    ),
    (
        # The other half, and a different mechanism for the same break: here the lines
        # ARE counted, and then kept -- so the arithmetic in window.txt would be honest
        # and the file would still be wrong.  Counting and dropping are two separate
        # acts and the suite must be able to see either one fail alone.
        "the pre-window lines are counted but not dropped",
        "    logLines, audioLines = {}, {}\n    windowMark('OPEN'",
        "    windowMark('OPEN'",
        ["no recorded line is stamped before the OPEN marker"],
        ["the discrete key reached changes.log"],
    ),
    (
        # The fallback is what keeps a shift whose lever cannot be reached from being a
        # shift with no recording at all, and nothing in the main run exercises it --
        # the lever is there and it fires.  So the scenario travels with the mutation,
        # the way the boot-death ones do.
        "the flag no longer opens the window",
        "            if ok and v == true then\n                flagOpened = true\n",
        "            if ok and v == 'never' then\n                flagOpened = true\n",
        ["the window opened even though the lever could not be resolved"],
        ["window.txt says the lever hook did NOT take"],
        None,
        ["--nolever"],
    ),
    (
        # THE HOOK MUST NOT WAIT FOR THE CENSUS, and this is the shipped regression
        # restored.  attachWindow() used to sit after `pcall(bootWalk)`, so on the
        # first real run it arrived at t=48s for a lever thrown at t=20s: the
        # connection took, window.txt said `lever_hooked=true`, and it said that
        # beside `opened_at=not yet` -- which reads exactly like a typo in LeverPath,
        # and cost the whole power-up, which the operator can spend ONCE.
        #
        # Expressed against `ents` rather than by moving the call, because `ents` is
        # empty until the census registers its first instance: `if #ents > 0` IS
        # "after the census" in one predicate.  That matters because it leaves every
        # other scenario green -- the main run's census completes, so the single
        # witness is the scenario whose census throws.  That scenario is also the
        # right one on the merits: a hook that survives a census which never finishes
        # provably did not depend on it.
        "the lever hook is taken only after the census",
        "    attachWindow()",
        "    if #ents > 0 then attachWindow() end",
        ["the lever hook was taken even though the census threw"],
        ["error.txt WAS written when the census threw"],
        None,
        ["--boot"],
    ),
    (
        "the dial no longer ends the run",
        "    if wrapFrom ~= nil and mins < wrapFrom then",
        "    if wrapFrom ~= nil and mins < -99999 then",
        ["the run ended by itself when the dial reached 12:00"],
        ["the closewin run still produced a timeline"],
        None,
        ["--closewin"],
    ),
    (
        # The other half of the same rule, and the one that says the rule is a FALL
        # rather than a value: with the threshold out of reach no reading can ever
        # latch, so a run that closes on the wrap must stop closing.  Without this
        # mutation, `WrapDropMins` could be raised to a number no shift can produce
        # and every check above would still pass, because they all feed the fixture a
        # fall that is large by construction.
        "the wrap is never latched",
        "    if prevClockMins ~= nil and (prevClockMins - mins) >= CONFIG.Window.WrapDropMins then",
        "    if prevClockMins ~= nil and (prevClockMins - mins) >= 99999 then",
        ["the run ended by itself when the dial reached 12:00"],
        ["the closewin run still produced a timeline"],
        None,
        ["--closewin"],
    ),
    (
        # The beacon's whole value is WHERE it is, not that it arrives: posted after
        # the load-time work it is meant to bracket, it still arrives and still reads
        # correctly, and only the arrival ORDER can tell the two apart.  Moving the
        # beacon itself is not expressible as one string replace, so this models the
        # same regression from the other side -- something else reaching the sink
        # first -- which is what a late beacon looks like from the reading end.  The
        # existence check must stay green, or this would be measuring "the beacon was
        # deleted" instead of "the beacon was second".
        "another file reaches the sink before the beacon",
        "    local sent = sendOnce({",
        "    sendOnce({ Url = CONFIG.Sink .. PREFIX .. 'first.txt',\n"
        "        Method = 'POST', Body = 'x' })\n"
        "    local sent = sendOnce({",
        ["alive.txt was the FIRST thing at the sink"],
        ["alive.txt was written"],
    ),
    (
        "the beacon carries a build tag that is not the shipped one",
        "        'build=' .. CONFIG.Build,",
        "        'build=' .. 'w0',",
        ["alive.txt carries the build tag, so a stale copy is visible as stale"],
        ["alive.txt was the FIRST thing at the sink"],
    ),
]


def run_harness(path, out=None, extra=None):
    """Returns (ok_names, fail_names, rc, stdout).

    `extra` carries the harness's own scenario flags.  A mutation that changes what
    happens when the census throws can only be seen by the scenario that makes the
    census throw -- the main run has no death in it at all -- so the flag is part of
    the mutation's evidence and travels with it rather than being assumed.
    """
    args = [LUA, HARNESS, path]
    if out:
        args.append("--out=" + out)
    for a in (extra or []):
        args.append(a)
    proc = subprocess.run(args, cwd=ROOT, capture_output=True)
    # Bytes then decode: this console is GBK and a text=True read dies on any
    # non-ASCII the child happens to emit.
    out = proc.stdout.decode("utf-8", "replace")
    oks, fails = set(), set()
    for line in out.splitlines():
        if line.startswith("  ok   "):
            oks.add(line[7:].strip())
        elif line.startswith("  FAIL "):
            fails.add(line[7:].split("  -- ")[0].strip())
    return oks, fails, proc.returncode, out


STAMP_RE = re.compile(r"^t=[0-9.]+ [0-9:]+ ")


def stripped(path):
    """The artifact with the wall-clock stamp removed from each line.

    The elapsed-time field is real output but it is not the thing under test, and
    two runs of the same watcher never share it -- so comparing raw bytes would call
    every mutation detected.
    """
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as fh:
        return [STAMP_RE.sub("", ln) for ln in fh.read().splitlines()]


def differential(diff_file):
    """Run baseline and mutant, and require the named artifact to differ."""
    basedir = os.path.join(ROOT, "_tools", "_mut_base")
    mutdir = os.path.join(ROOT, "_tools", "_mut_out")
    shutil.rmtree(basedir, ignore_errors=True)
    shutil.rmtree(mutdir, ignore_errors=True)

    run_harness("_tools/TRG_original_watch.luau", out="_tools/_mut_base")
    run_harness("_tools/_watch_mutant.luau", out="_tools/_mut_out")

    base = os.path.join(basedir, diff_file)
    mut = os.path.join(mutdir, diff_file)
    if not (os.path.exists(base) and os.path.exists(mut)):
        return False, "could not produce both %s to compare" % diff_file
    if stripped(base) == stripped(mut):
        return False, "NOT DETECTED (%s is unchanged once stamps are stripped)" % diff_file
    return True, "differs from the baseline in %s, as it should" % diff_file


def main():
    source = open(SHIPPED, "r", encoding="utf-8", newline="").read()
    before = digest(SHIPPED)

    print("baseline: ", end="")
    oks, fails, rc, _ = run_harness("_tools/TRG_original_watch.luau")
    if fails or rc != 0 or not oks:
        print("RED -- %d ok, %d fail. Fix the watcher before mutating it." % (len(oks), len(fails)))
        for name in sorted(fails):
            print("   failing: " + name)
        return 1
    print("GREEN (%d checks)" % len(oks))

    bad = 0
    basedir = os.path.join(ROOT, "_tools", "_mut_base")
    for entry in MUTATIONS:
        name, anchor, replacement, must_fail, must_pass = entry[:5]
        diff_file = entry[5] if len(entry) > 5 else None
        scenario = entry[6] if len(entry) > 6 else None

        count = source.count(anchor)
        if count != 1:
            # The discipline from the project notes: an anchor is either unique by
            # construction or it is asserted unique before anything is written.
            print("  ANCHOR %-52s found %d times -- test is broken" % (name, count))
            bad += 1
            continue

        with open(MUTANT, "w", encoding="utf-8", newline="") as fh:
            fh.write(source.replace(anchor, replacement, 1))

        if diff_file:
            ok, why = differential(diff_file)
            print("  %-56s %s" % (name, why))
            if not ok:
                bad += 1
            continue

        moks, mfails, mrc, mout = run_harness("_tools/_watch_mutant.luau",
                                              extra=scenario)

        missing = [c for c in must_fail if c not in mfails]
        broke = [c for c in must_pass if c not in moks]

        if not moks and not mfails:
            print("  %-56s the mutant did not run at all" % name)
            bad += 1
        elif missing:
            print("  %-56s NOT DETECTED (no red on: %s)" % (name, "; ".join(missing)))
            bad += 1
        elif broke:
            print("  %-56s OVER-BROAD (also killed: %s)" % (name, "; ".join(broke)))
            bad += 1
        else:
            print("  %-56s red as expected: %s" % (name, must_fail[0]))

    shutil.rmtree(basedir, ignore_errors=True)
    shutil.rmtree(os.path.join(ROOT, "_tools", "_mut_out"), ignore_errors=True)

    if os.path.exists(MUTANT):
        os.remove(MUTANT)

    after = digest(SHIPPED)
    if before != after:
        print("the SHIPPED watcher changed during the run -- that must never happen")
        return 1

    print()
    total = len(MUTATIONS)
    print("watch mutations: %d of %d detected, shipped file untouched (md5 %s)"
          % (total - bad, total, after))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
