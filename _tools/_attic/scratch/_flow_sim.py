# -*- coding: utf-8 -*-
"""Offline replica of Engine:Step's Running branch, used to TUNE the collector's
autopilot before it is written into Studio. Not a source of truth: every constant
below is copied from ServerScriptService.ReactorBackend.Config as read on
2026-09-26, and the arithmetic is a transcription of Engine:Step lines 204..244.
Its only job is to answer "does this policy reach `shutdown` before it melts,
stalls or overloads", which is a question about a policy, not about the engine.
"""
import math

C = dict(
    ReferenceTick=2.5, Ambient=20, StartupTemperature=9420, StartupPressure=5000,
    CBLHeat=65, PumpCooling=120, FanPressure=70, PressureDivisor=50,
    NoiseMin=-50, NoiseMax=49, State1=5600, State2=17500, State3=29500,
    State3Heat=700, State2Pressure=200, State3Pressure=300, StallPressure=2200,
    StallCooling=750, HighPressure=13500, HighPressureDivisor=100,
    StallTemperature=2000, MeltdownTemperature=39000,
    OutputDivisors=[250, 160, 120, 45], OutputOffsets=[50, 100, 250, 400],
    ExtractionFraction=0.25, QuotaDivisor=60, StressPerLevel=4,
    StressOutputDivisor=500, StressPumpRelief=1.5, StressPassiveRelief=6,
    StressPressureBonus=2,
    PumpWearPerLevel=0.06, CBLPressurePerLevel=0.6, CBLStressThreshold=75,
    CBLStressGain=0.4, CBLPurgeStressRelief=25, CBLPurgeCooldown=4,
    EquinoxSeconds=720, EquinoxMultiplier=3, EquinoxWearMultiplier=2,
    AtmosphereDrop=3000, VentCooldown=26,
    Quotas=[512, 1024, 3072], ShutdownLimit=17000,
)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# The shipped controller: proportional demand, gain 0.03, no band. These two
# defaults MUST match MCP_FlowCollector.luau's `policy()`, because the whole point
# of this file is to be a rehearsal of that pilot -- a second controller is a
# different pilot, exactly as a second dispatcher is a different engine. `--ab`
# sweeps them; the values here are the ones the sweep selected.
#
# The error gain is a POSITION dead zone in disguise: the ±200/-45 clamp is a rate
# limit, so the core may drift ±200/gain C before the pilot asks for a reversal.
# At the original 0.1 that was ±2000 C, which the pilot then corrected at full
# slope -- a sawtooth. Lower gain, narrower zone. See the sweep for the cliff.
HYST = 0
GAIN = 0.03


class Sim:
    def __init__(self, noise):
        self.noise = noise
        self.time = 0.0
        self.elapsed = 0.0
        self.equinox = False
        self.temp = C["StartupTemperature"]
        self.press = C["StartupPressure"]
        self.energy = 0.0
        self.stress = 0.0
        self.output = 0.0
        self.core = 0
        self.vent_until = 0.0
        self.fans = [True] * 6
        self.cbl = [dict(level=2, press=0.0, stress=0.0, active=True, purge=0.0, fault=False)
                    for _ in range(3)]
        self.pumps = [dict(level=1, on=False, integ=100.0) for _ in range(3)]
        self.extraction = 2
        self.emg = [False, False, False]
        self.mass = [dict(on=False, level=1) for _ in range(2)]
        self.failed = None

    def set_cbl(self, i, v):
        if not self.cbl[i]["fault"]:
            self.cbl[i]["level"] = v

    def purge(self, i):
        d = self.cbl[i]
        if self.time < d["purge"]:
            return
        d["press"] = 0.0
        d["stress"] = max(0, d["stress"] - C["CBLPurgeStressRelief"])
        d["purge"] = self.time + C["CBLPurgeCooldown"]

    def vent(self):
        if self.equinox or self.time < self.vent_until:
            return
        self.press = max(0, self.press - C["AtmosphereDrop"])
        self.vent_until = self.time + C["VentCooldown"]

    def emergency(self, i):
        """E-VENT. Unlike the AVB it has NO equinox gate, which makes it the
        only pressure instrument that still works once the equinox is on."""
        if self.emg[i]:
            return False
        self.emg[i] = True
        self.press = max(0, self.press - 7000)
        return True

    def step(self, dt=1.0):
        if self.failed:
            return
        self.time += dt
        self.elapsed += dt
        if not self.equinox and self.elapsed >= C["EquinoxSeconds"]:
            self.equinox = True
        scale = dt / C["ReferenceTick"]
        heat = cool = fans = 0
        for p in self.pumps:
            if p["on"] and p["integ"] > 0:
                cool += p["level"]
                p["integ"] = max(0, p["integ"] - C["PumpWearPerLevel"] * p["level"] * dt
                                 * (C["EquinoxWearMultiplier"] if self.equinox else 1))
                if p["integ"] == 0:
                    p["on"] = False
        for d in self.cbl:
            if d["active"] and not d.get("fault", False):
                lvl = 1 if self.press < C["StallPressure"] else d["level"]
                heat += lvl
                d["press"] = clamp(d["press"] + (lvl - 1) * C["CBLPressurePerLevel"] * dt, 0, 100)
                if d["press"] >= C["CBLStressThreshold"]:
                    d["stress"] = min(100, d["stress"] + C["CBLStressGain"] * dt)
                if d["stress"] >= 100:
                    d["fault"] = True
                    d["active"] = False
                    self.fail("CBL overloaded")
        fans = sum(1 for f in self.fans if f)
        self.temp += (heat * C["CBLHeat"] - cool * C["PumpCooling"] + self.noise) * scale
        if not self.equinox:
            self.press += (math.floor(self.temp / C["PressureDivisor"]) - fans * C["FanPressure"]) * scale
        if self.temp > C["State2"]:
            self.press += C["State2Pressure"] * scale
        if self.temp > C["State3"]:
            self.temp += C["State3Heat"] * scale
            self.press += C["State3Pressure"] * scale
        if self.press < C["StallPressure"]:
            self.temp -= C["StallCooling"] * scale
        if self.press > C["HighPressure"]:
            self.temp += math.floor(self.press / C["HighPressureDivisor"]) * scale
        self.temp = max(C["Ambient"], self.temp)
        self.press = max(0, self.press)
        self.core = 3 if self.temp > C["State3"] else (2 if self.temp > C["State2"]
                                                       else (1 if self.temp >= C["State1"] else 0))
        # Lua indexes OutputDivisors[coreState+1], i.e. the table is 1-based and
        # this list is not. Indexing it with core+1 here reads one cell too far
        # and roughly DOUBLES the output of states 1 and 2 -- which is what made
        # the offline sim meet the quota at a cold core and report SHUTDOWN-OK
        # for a policy that actually plunges 21674 -> stallout in 56 ticks.
        net = math.floor(self.temp / C["OutputDivisors"][self.core]) + C["OutputOffsets"][self.core]
        mass = sum(d["level"] for d in self.mass if d["on"])
        self.output = net * self.extraction * C["ExtractionFraction"] * (1 - mass * 0.025) \
            * (C["EquinoxMultiplier"] if self.equinox else 1)
        self.energy = min(C["Quotas"][self.shift - 1], self.energy + self.output * dt / C["QuotaDivisor"])
        self.stress = clamp(self.stress + (self.extraction * C["StressPerLevel"]
                                           + math.floor(self.output / C["StressOutputDivisor"])
                                           - math.floor(cool * C["StressPumpRelief"])
                                           - C["StressPassiveRelief"]
                                           + (C["StressPressureBonus"] if self.press > C["HighPressure"] else 0)) * scale,
                            0, 100)
        if self.temp >= C["MeltdownTemperature"]:
            self.fail("Reactor meltdown")
        elif self.temp < C["StallTemperature"]:
            self.fail("Reactor stallout")
        elif self.stress >= 100:
            self.fail("Power extraction assembly overload")

    def fail(self, why):
        if not self.failed:
            self.failed = why


def split3(total):
    """Split a CBL heat total (3..15) into three integer levels of 1..5, and a
    pump cooling total (0..9) into three levels of 0..3. Balanced, because equal
    levels keep the device pressures equal and therefore the purges together."""
    lv = max(1, min(5, round(total / 3.0)))
    out = [lv] * 3
    for i in range(3):
        while sum(out) < total and out[i] < 5:
            out[i] += 1
        while sum(out) > total and out[i] > 1:
            out[i] -= 1
    return out


def split_pump(total):
    lv = max(0, min(3, round(total / 3.0)))
    out = [lv] * 3
    for i in range(3):
        while sum(out) < total and out[i] < 3:
            out[i] += 1
        while sum(out) > total and out[i] > 0:
            out[i] -= 1
    return out


def policy(s, quota, hold=20000):
    """The autopilot under test -- a CLOSED-LOOP controller, not a ladder.

    dTemp/dt is exactly (65*H - 120*K + noise) / 2.5, i.e. 26*H - 48*K C/s,
    where H is the sum of the three CBL levels (3..15) and K the sum of the
    three pump levels (0..9). That is a linear plant in two integers, so there
    is no need to hand-tune bands: pick the pair whose rate is nearest the rate
    we want, preferring the hotter pair on a tie because heat is output.

    A static ladder was tried first and it died. With a constant noise bias of
    +49 the -2 C/s band (H=11,K=6) becomes +17.6 C/s, the core drifts from
    24000 to 29000 over 400 ticks, and above HighPressure 13500 the engine's
    own `temp += floor(press/100)*scale` term feeds back and runs away to
    meltdown. Closing the loop on the measured temperature absorbs any bias,
    which is what a static band cannot do.

    Two modes, because the shift has two halves. While the quota is unmet we
    hold ~20000 (below State2 17500 the +200*scale pressure term is absent and
    above it pressure needs the fans, AVB and the high-pressure relief to share
    the load). Once the quota is met, `shutdown` refuses unless the core is
    BELOW ShutdownLimit 17000 -- so the endgame is a deliberate, GENTLE descent
    and the rate is clamped at -45 C/s. Clamping matters: the fastest pair
    available is -354 C/s (H=3,K=9), which sails past 17000 and stalls the core
    at 2000 before shutdown can be called. Cooling is cheap in both halves; it
    is the HEAT that keeps the descent survivable, so the clamp keeps H=15 and
    asks for only a little less heat.
    """
    t = s.temp
    endgame = s.energy >= quota
    # EQUINOX: the pressure loses every sink it has. Engine:Step guards the
    # whole `pressure += (floor(temp/50) - fans*70)*scale` line with
    # `if not equinox`, AND atmosphere_vent refuses during it -- so the only
    # surviving pressure term is `temp > State2 -> +200*scale`, a pure +80/s
    # ratchet with no relief, which then feeds `temp += floor(press/100)*scale`
    # back into the core and runs away to meltdown. That ratchet is gated on the
    # temperature too, so below State2 17500 the pressure during the equinox is
    # EXACTLY frozen -- and below 17000 `shutdown` is already legal. The equinox
    # is therefore not a hotter shift, it is a colder one: the design is telling
    # the operator to get under 17500 and leave.
    target = 15500 if s.equinox else (16000 if endgame else hold)
    # Proportional demand, no band, no state. Two designs were tried and measured
    # here and in Data/flow/, and both were worse than this one:
    #
    # 1. Hold the last solved pair while |error| <= 600. With want = err * 0.1, at
    #    the band edge (600) the demand is 60 C/tick -- exactly the size of the big
    #    pairs (26*10-48*4 = +68, 26*14-48*9 = -68). So the controller solved AT the
    #    edge and never at the centre, and rode +68/-66 for tens of ticks. On the
    #    real engine that cut CBL 2093 -> 282 and took mean |dTemp| from 15.43 to
    #    63.63: a quieter command stream on a 4.7x less steady core.
    # 2. Demand ZERO inside the band (a relay). Worse again, on BOTH axes: leaving
    #    the band demands 200/gain, which slams the core across to the far edge.
    #
    # The reason neither works: the grid's smallest slope is 2 C/tick (26*11-48*6 =
    # -2, 26*13-48*7 = +2) while the engine's own noise is +/-20 C/tick. Re-solving
    # cannot cancel noise 10x larger than the finest step it can apply -- so the
    # commands are not churn to be suppressed, they ARE the control. The only real
    # lever is the GAIN, which narrows the position dead zone described below.
    err = target - t
    if abs(err) <= HYST:
        want = 0.0
    else:
        want = clamp(err * GAIN, -45 if endgame else -200, 200)
    H, K = 3, 9
    best = None
    for h in range(3, 16):
        for k in range(0, 10):
            score = (abs((26 * h - 48 * k) - want), -h)
            if best is None or score < best[0]:
                best = (score, h, k)
    H, K = best[1], best[2]
    # Stress is (extraction*4 + floor(output/500) - floor(cooling*1.5) - 6)
    # per second, so high extraction is only safe on top of high cooling.
    ex = 3 if K >= 8 else 2
    cmds = []
    for i, (lv, pl) in enumerate(zip(split3(H), split_pump(K))):
        d = s.cbl[i]
        if d["level"] != lv:
            cmds.append(("cbl", i + 1, lv))
        if d["press"] >= 60:
            cmds.append(("cbl_purge", i + 1, None))
        p = s.pumps[i]
        if pl == 0 and p["on"]:
            cmds.append(("pump_off", i + 1, None))
        if pl > 0:
            if not p["on"]:
                cmds.append(("pump_on", i + 1, None))
            if p["level"] != pl:
                cmds.append(("pump_level", i + 1, pl))
        # Pump integrity is a FINITE per-shift budget: wear is
        # PumpWearPerLevel * level per second (doubled in equinox), so 100
        # integrity at level 2 buys ~830 s and then the pump switches ITSELF
        # off -- and pump_on refuses at integrity 0. Cooling that vanishes
        # mid-shift turns H=15 into +390 C/s, i.e. an instant meltdown. The
        # only way back is Engine:Repair (RepairPerSecond 10), so an operator
        # who intends to survive a long shift has to spend attention on it.
        if p["integ"] < 60:
            cmds.append(("repair_pump", i + 1, None))
    want_fan = True if s.press > 11000 else (False if s.press < 8000 else None)
    if want_fan is not None:
        for i, f in enumerate(s.fans):
            if f != want_fan:
                cmds.append(("fan", i + 1, None))
    if s.press > 12000:
        cmds.append(("atmosphere_vent", None, None))
    # Above HighPressure 13500 the engine adds floor(press/100)*scale of HEAT
    # back into the core, so an E-VENT here is not just pressure relief, it is
    # the only way to break a runaway the AVB cannot break alone -- and during
    # the equinox it is the only instrument left at all.
    if s.press > 13000:
        for i in range(3):
            if not s.emg[i]:
                cmds.append(("emergency_vent", i + 1, None))
                break
    if s.extraction != ex:
        cmds.append(("extraction", None, ex))
    return cmds


def finish(stats, temps):
    """Close out a run's metrics in ONE place. Two of the three returns used to
    compute holdSpan inline, and the third did not -- which is how a metric
    silently becomes per-branch. Call it from every exit."""
    if temps:
        stats["holdSpan"] = max(temps) - min(temps)
    stats["dTemp"] = stats["dsum"] / max(1, stats["dn"])
    return stats


def lehmer(seed):
    """The collector's own rng, so the offline rehearsal and the Studio run
    consume the same noise shape."""
    s = seed
    while True:
        s = (s * 48271) % 2147483647
        yield -50 + (s % 100)


def run(shift, noise, max_ticks=6000, verbose=False, budget=900, seed=None):
    """Drive one shift to shutdown. `noise` is a constant OR an iterator.

    EVERY command dispatch lives HERE and nowhere else, and that is now a rule
    with a body count. Calling this from a harness that re-implements the
    dispatch has produced three separate false results: a one-cell output-table
    error that survived a whole tuning pass, and a churn counter that reported a
    working pilot as a stallout because its copy of the loop counted the `cbl`
    command without applying it. Use the `stats` it returns instead. A second
    dispatcher is not a convenience, it is a different engine.
    """
    gen = lehmer(seed) if seed is not None else None
    s = Sim(noise if gen is None else 0)
    s.shift = shift
    quota = C["Quotas"][shift - 1]
    s.temp = C["StartupTemperature"]
    trace = []
    stats = {"ticks": 0, "cmds": 0, "byName": {}, "holdSpan": 0.0,
             "dsum": 0.0, "dn": 0}
    temps = []
    assisted = False
    for tick in range(max_ticks):
        if gen is not None:
            s.noise = next(gen)
        if tick >= budget and s.energy < quota and not assisted:
            s.energy = quota
            assisted = True
        for a, i, v in policy(s, quota):
            stats["cmds"] += 1
            stats["byName"][a] = stats["byName"].get(a, 0) + 1
            if a == "cbl":
                s.set_cbl(i - 1, v)
            elif a == "cbl_purge":
                s.purge(i - 1)
            elif a == "pump_on":
                s.pumps[i - 1]["on"] = True
            elif a == "pump_off":
                s.pumps[i - 1]["on"] = False
            elif a == "pump_level":
                s.pumps[i - 1]["level"] = v
            elif a == "repair_pump":
                p = s.pumps[i - 1]
                p["integ"] = min(100.0, p["integ"] + 10.0)   # RepairPerSecond
            elif a == "fan":
                s.fans[i - 1] = not s.fans[i - 1]
            elif a == "atmosphere_vent":
                s.vent()
            elif a == "emergency_vent":
                s.emergency(i - 1)
            elif a == "extraction":
                s.extraction = v
        s.step(1.0)
        # Measure from the moment the core is up, never from the ramp: the
        # 9572 -> 20000 rise is ~10 000 C and would swamp anything the metric is
        # supposed to describe. Same cut the file analysis uses (first sample
        # above 19000), so the numbers are comparable across the two.
        #
        # The metric is mean |dTemp| per tick, NOT the max-min span. The span is
        # dominated by the DESIGNED setpoint moves (20000 -> 16000 at endgame,
        # 15500 in the equinox), so it reports ~4500 for every config and tells
        # you nothing about chatter. Mean |dTemp| is what actually distinguished
        # the two real runs: 15.43 for the proportional pilot at gain 0.4, 63.63
        # for the bad hysteresis port. (Both pooled over every post-ramp tick in the
        # file, so they are comparable to each other and to this metric.)
        if s.temp >= 19000 or temps:
            if temps:
                stats["dsum"] += abs(s.temp - temps[-1])
                stats["dn"] += 1
            temps.append(s.temp)
        stats["ticks"] = tick
        if s.failed:
            finish(stats, temps)
            return s.failed, tick, s.temp, s.press, s.energy, trace, stats
        if s.energy >= quota and s.temp < C["ShutdownLimit"]:
            finish(stats, temps)
            return ("SHUTDOWN-OK" if not assisted else "SHUTDOWN-ASSISTED"), tick, s.temp, s.press, s.energy, trace, stats
        if verbose and tick % 60 == 0:
            trace.append((tick, round(s.temp), round(s.press), round(s.energy), s.core,
                          [d["level"] for d in s.cbl], [d["on"] for d in s.pumps],
                          sum(1 for f in s.fans if f), s.extraction))
    finish(stats, temps)
    return "TIMEOUT", max_ticks, s.temp, s.press, s.energy, trace, stats


# A module-level tally the sweep fills in, so the churn number quoted below is
# the one the SINGLE dispatcher in run() produced. Anything that recomputes it
# from the trace is a second engine wearing a report's clothes.
CHURN = {"cbl": 0, "cmds": 0, "ticks": 0, "spans": [], "dsum": 0.0, "dn": 0}


def report(tag, r):
    """One line per case, carrying the churn so a tuning change is measurable
    against the collected baseline (the recorded Studio run was cbl 2093 over
    1422 ticks across three shifts)."""
    kind, tick, temp, press, energy, _trace, stats = r
    by = stats["byName"]
    CHURN["cbl"] += by.get("cbl", 0)
    CHURN["cmds"] += stats["cmds"]
    CHURN["ticks"] += stats["ticks"]
    CHURN["spans"].append(stats["dTemp"])
    CHURN["dsum"] += stats["dsum"]
    CHURN["dn"] += stats["dn"]
    ok = kind == "SHUTDOWN-OK"
    print("  %-22s -> %-20s tick %-5d temp %8.1f press %8.1f  cmds %-5d cbl %-5d hold %7.1f%s"
          % (tag, kind, tick, temp, press, stats["cmds"], by.get("cbl", 0),
             stats["holdSpan"], "" if ok else "   <-- FAIL"))
    return ok


def sweep(bad):
    """The 24-case gate. `bad` is returned so __main__ can print the total."""
    print("constant extremes (a bias the real rng never produces, kept as a margin check):")
    for shift in (1, 2, 3):
        for noise in (-50, 0, 49):
            bad += not report("s%d noise %+3d" % (shift, noise), run(shift, noise))
    print()
    print("random seeds (the shape the collector actually runs):")
    for shift in (1, 2, 3):
        for seed in (20260926, 7, 999999, 1, 12345):
            bad += not report("s%d seed %-9d" % (shift, seed), run(shift, 0, seed=seed))
    print()
    spans = CHURN["spans"]
    print("churn: cbl %d / cmds %d over %d ticks = %.3f cbl per tick"
          % (CHURN["cbl"], CHURN["cmds"], CHURN["ticks"],
             CHURN["cbl"] / max(1, CHURN["ticks"])))
    # Report mean |dTemp|, not the max-min span. The span is ~4300 for EVERY
    # config because it is the designed setpoint moves (20000 -> 16000 endgame,
    # 15500 equinox), so it cannot tell a steady pilot from a sawtoothing one --
    # it gave the bad hysteresis port a clean bill of health.
    print("steadiness: mean |dTemp| per tick %.2f, worst case %.2f  (the same metric "
          "on the real file: 15.43 at gain 0.4, 13.62 at gain 0.03)"
          % (CHURN["dsum"] / max(1, CHURN["dn"]), max(spans) if spans else 0.0))
    return bad


def ab():
    """Sweep the controller's two knobs through run()'s single dispatcher, and
    judge each config on BOTH axes: command traffic (cbl/tick) and how steady the
    core actually is (holdSpan, the post-ramp temperature band).

    Scoring on traffic alone is how a quieter command stream got bolted to a less
    steady core: the first hysteresis version cut cbl/tick 2.5x in this sweep and
    still lost on the real run -- mean |dTemp| 15.43 -> 63.63 -- because the band
    edge demanded exactly the size of the big pairs and rode them. Both numbers or
    neither.

    Cross-engine comparisons do not work here either: the collected baseline
    (2093 cbl / 1422 ticks = 1.47/tick) came from the Luau policy with gain 0.4, so
    an aggregate over a different mix of shifts and seeds measures the mix, not
    the controller. The control is the same seed set inside THIS file.
    """
    global HYST, GAIN
    cases = [(s, noise) for s in (1, 2, 3) for noise in (-50, 0, 49)]
    cases += [(s, None) for s in (1, 2, 3)]          # seed-driven, the real shape
    configs = [(0.05, 0), (0.03, 0), (0.025, 0), (0.02, 0), (0.015, 0),
               (0.012, 0), (0.01, 0)]
    print("gain  band   fails   cbl   cbl/tick   mean|dTemp|   worst case")
    for gain, band in configs:
        GAIN, HYST = gain, band
        fails = cbl = ticks = dn = 0
        worst = 0.0
        dsum = 0.0
        for shift, noise in cases:
            r = run(shift, 0 if noise is None else noise,
                    seed=20260926 if noise is None else None)
            if r[0] != "SHUTDOWN-OK":
                fails += 1
            cbl += r[6]["byName"].get("cbl", 0)
            ticks += r[6]["ticks"]
            # Weight each case's mean by its sample count, so the aggregate is the
            # pooled mean and not an average of averages -- a 224-tick shift and an
            # 820-tick shift do not get equal say in what the core does.
            dsum += r[6]["dsum"]
            dn += r[6]["dn"]
            worst = max(worst, r[6]["dTemp"])
        print("  %-4.2f  %-5d  %-5d  %-4d   %.3f        %8.2f     %8.2f"
              % (gain, band, fails, cbl, cbl / max(1, ticks),
                 dsum / max(1, dn), worst))
    GAIN, HYST = 0.1, 0


if __name__ == "__main__":
    import sys as _sys
    if "--ab" in _sys.argv:
        ab()
    else:
        print("FAILURES: %d" % sweep(0))
