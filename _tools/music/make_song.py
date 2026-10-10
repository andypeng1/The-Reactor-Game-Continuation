"""Compose an original track to a specification measured off the reference.

The reference (asstes/music/ReactorStartup.mp3) is a piano arrangement of the
Portal 2 OST cue "Reconstructing More Science", credited to Aperture Science
Psychoacoustic Laboratories -- the operator's own identification of the source
(2026-10-11):
`[WIP] (Piano) Portal 2 OST - Reconstructing More Science - Aperture Science
Psychoacoustic Laboratories`.  It is therefore somebody else's recording of
somebody else's composition, and the repo is public, so it is not committed
(see .gitignore).  It is used for
exactly one purpose here: as a *target spec*.  Every number in TARGET below is
a measurement of that file (ReactorStartup.report.txt, made by
_tools/music/analyze.py); none of it is a genre label typed in from memory.
No material is transcribed from it -- the shape is reproduced, not the music.

Measured target spec:
  duration  263.90 s            tempo  89.25 bpm
  key       F major r=+0.837    pitch core {F,G,A,C,D} = 61.3% of chroma
  form      0-10 drone | 10-20 build | 20-30 pulse | 30-40 first peak |
            40-90 groove | 90-110 breakdown | 110-140 rebuild |
            140-150 climax | 150-220 groove | 220-240 outro | 240-264 final
  loudness  -15.10 dBFS mean RMS over 50 ms frames, p5..p95 range 13.76 dB
            (music frames only.  Measured over ALL frames the same numbers read
            -13.43 / 14.56, because the file opens on 2 s of exact digital
            silence -- a rip artifact, and one the reference must not be
            credited with.  Both bases are quoted so the 1.7 dB gap can never
            be mistaken for a mix change.)
  texture   2-8 kHz frame RMS: median -28.36, p90 -22.09, spread 6.26 dB,
            77.5% of frames within 6 dB of the floor.  See REF_TEX_* below --
            this is the spec that catches a continuous floor, which band power
            cannot.
  stereo    side/mid 0.116, L/R corr +0.792 (nearly mono)

  octave profile, dB re the 40-80 Hz band -- the most distinctive single thing
  about the reference, and the thing the master chain closes a loop on.
  Measured at 44100 Hz / n=8192:
      20-40 -10.2 | 40-80 0.0 | 80-160 -3.8 | 160-320 -6.6 | 320-640 -11.4
      640-1.28k -10.0 | 1.28k-2.56k -10.6 | 2.56k-5.12k -11.2
      5.12k-10.24k -17.1 | 10.24k-20k -27.1
  So: a narrow sub peak, a low-mid shoulder, a plateau about 11 dB down to
  2.5 kHz, then a cliff.  That contour is a shape, not a style, and it is the
  reason this piece will not sound like the reference's melody but should sit
  in the same sonic space.

Two of these are a CHOICE between two measurements, not a reading, and the
choice is recorded rather than hidden because the estimator returned both:

  tempo  89.25 bpm (autocorrelation strength 0.710, n=2048, 93 ms window) vs
         92.25 bpm (0.700, n=8192, 186 ms window).  Near-tied, and each is
         the other's double at 178.25/184.50.  I take 89.25 because onset
         timing wants a short window -- a 186 ms window averages across the
         transient it is supposed to be finding.  TARGET says 89.25; the
         runner-up is 3.4% away and would also be defensible.
  key    93 ms windows: F major r=+0.837, A minor +0.758, C major +0.719,
         D minor +0.678.  186 ms windows: D minor +0.693, F major +0.685 --
         a three-way tie inside 0.011.  Both agree the pitch core is
         {F,G,A,C,D} (61.3% of chroma at the short window, 53.2% at the long
         one); they disagree about which of those five is home, and the
         disagreement is a property of the analyser, not the audio.  The
         piece uses the pentatonic set, which is the part both measurements
         agree on, and does not assert a root.

Tonality is measured too: the five pitch classes carrying 61% of the
reference's chroma energy are, in measured order, C > A > F > D > G -- exactly
F major pentatonic.  The whole piece therefore uses those five notes and
nothing else (E measures 6.4% and Bb 6.4%, both near noise; they are excluded
on purpose, not by accident).

Output: asstes/music/ReactorShift.{ogg,mp3} (the .wav is intermediate).
Run:    python _tools/music/make_song.py [--stems] [--reuse] [--probe]
          --stems   render the mono stems and cache them, then stop (~6 min)
          --reuse   assemble + master from the cache instead of re-rendering
          --probe   print the raw profile and the per-term width budget
"""

import os
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp                                    # noqa: E402
from analyze import stft                      # reuse the measuring stick  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(ROOT, "asstes", "music")
FFMPEG = os.environ.get("FFMPEG", r"D:\Bot\ffmpeg\bin\ffmpeg")
NAME = "ReactorShift"

SR = 44100
BPM = 89.25
BEAT = 60.0 / BPM
BAR = 4 * BEAT
N_BARS = 97
TAIL = 3.0
TOTAL = N_BARS * BAR + TAIL
N = int(round(TOTAL * SR))

# ============================== notes ==============================

_PC = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
       "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(name):
    """'F1' -> 43.65 Hz.  Scientific pitch, A4 = 440."""
    cut = 2 if len(name) > 2 and name[1] == "#" else 1
    midi = (int(name[cut:]) + 1) * 12 + _PC[name[:cut]]
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


F1 = hz("F1")      # 43.65 -- sits inside the measured 40-80 Hz peak band
F2 = hz("F2")
F3 = hz("F3")
A4 = hz("A4")
C5 = hz("C5")
G4 = hz("G4")


def at(bar, beat=0.0):
    """Bar/beat position -> seconds."""
    return (bar + beat / 4.0) * BAR


# ============================== harmony ==============================

# An 8-bar cycle.  Chord tones are drawn only from {F,G,A,C,D}.  Roots sit at
# 55-88 Hz so the moving bass stays under the drone rather than beside it.
PROG = [
    ("F",  "F2", ["F3", "A3", "C4", "G4"]),
    ("F",  "F2", ["F3", "A3", "C4", "G4"]),
    ("Dm", "D2", ["D3", "F3", "A3", "C4"]),
    ("Dm", "D2", ["D3", "F3", "A3", "C4"]),
    ("C",  "C2", ["C3", "G3", "C4", "D4"]),
    ("C",  "C2", ["C3", "G3", "C4", "D4"]),
    ("Dm", "D2", ["D3", "F3", "A3", "C4"]),
    ("As", "A1", ["A2", "G3", "C4", "D4"]),
]

# The lead material lives in ONE place, further down: see "the lead" after
# level_curve(), which also explains why it moved.  What used to stand here was
# a single three-note motif scheduled identically on every even bar from 16 to
# 96 -- the whole tune, 97 bars of it -- and that is literally what the
# operator reported hearing.  The motif survives intact as theme A; it is no
# longer the whole piece.

# ---------------------------- the melody's level ----------------------------
# The operator's second report was "I can hardly hear the melody", and the
# first version of this file had it at 0.085 / 0.16 -- written, never tuned.
#
# It was not merely wet or masked.  Measured per note window (105 of them),
# as 10log10(melody / everything-else-sounding-at-that-instant):
#
#   narrow = +-1/6 octave around the note's fundamental (the pitch carrier)
#   wide   = that fundamental out to 4x (the harmonics)
#
#       scale             narrow     wide     | whole-mix s/mid, corr
#       shipped  1.0x      -11.8     -1.3     | 0.116  +0.799
#       dry 10x  2.5x       +5.4     +15.9    | 0.115  +0.801
#       dry 12x  2.5x       +6.9     +17.4    | 0.115  +0.801
#       dry 16x  1.0x       +9.3     +19.7    | 0.114  +0.803
#
# ---- [CORRECTION] that table was wrong, and the third report found it out. ----
#
# Those rows were not measurements of the raised lead; they were an
# extrapolation: the isolated buffer's bandpower multiplied by dry^2.  The
# multiplier is right (the mix is linear) but the baseline it multiplied was
# not, so the whole column overstates the melody.  Re-measured against a rest
# that genuinely contains no lead -- which at the time did not exist, because
# the only stem set available still had the lead in it -- the SAME old motif at
# the SAME 12x/2.5x sits at -4.5 dB narrow over 105 windows, not +6.9.  An
# 11.4 dB error, and it went unnoticed because the number was plausible.
#
# The real state all along: the lead ran 3 to 4.5 dB UNDER its own accompaniment
# in its own critical band.  That is exactly what "I can hardly hear the melody"
# describes, and it is why raising it did not fix the complaint.
#
# So +6 dB IS a chosen criterion and the level below is set by MEASURING the
# shipped line against a lead-free rest at each level (lead_margin.py):
#
#       1x  -3.1 |  2x  +1.3 |  3x  +4.5 |  4x  +6.8 |  6x +10.2 |  8x +12.6
#
# 4x is the first point that clears it.  The two lessons are worth more than
# the number: a margin must be measured against an accompaniment that has no
# melody in it, and an extrapolation is not a measurement no matter how
# plausible its output.
#
# Shipped was 11.8 dB UNDER its own accompaniment in its own critical band --
# below the masking threshold, which is why it read as texture rather than as a
# tune, while its harmonics sat at parity (-1.3 dB) and gave the impression
# that "something" was there.
#
# +6 dB in the critical band is a CHOSEN criterion (the usual "clearly audible,
# not merely present"), not a measurement; the margins above are the
# measurements.  12x / 2.5x is the first tested point that meets it.  Two
# things the sweep settled rather than assumed:
#
#   * the SEND barely moves the margin (dry 10x: +5.2 at send 1x vs +6.2 at
#     send 5x) -- only 1 dB for five times the reverb.  The dry is the lever.
#     The shipped lead was wet-dominant (send/dry 1.88); this makes it dry-
#     dominant (0.39), which is also what articulation wants.
#   * a five-times send does NOT make the mix wetter overall: s/mid stays
#     0.115 and corr +0.801 at every point above.  The shared reverb returns
#     are dominated by every other instrument's send, so this one cannot move
#     them.  That was a guess, and it was wrong.
#
# It is on top WHEN IT SPEAKS, not loud overall, and the two are different
# measurements.  As the lead's share of the 320-640 Hz band's average power over
# the whole file, it runs -26.7 dB at 1x and -14.9 dB at 4x -- a +11.8 dB step
# for a +12.0 dB level, i.e. the square law holds -- and it sounds in only 22%
# of the track.  Sparse, and present while it is there.  To step it back,
# 10x / 2.5x measures +5.4 dB narrow.
LEAD_DRY = 4.08         # 0.085 * 48 = the 12x above, times the 4x that the
LEAD_SEND = 1.60        # re-measurement says is needed to clear +6 dB narrow


def chord_bar(bar):
    return PROG[bar % 8]


def chord_spans():
    """Consecutive bars sharing a chord become one pad note, so the pad
    breathes every 2 bars instead of re-attacking every bar."""
    out = []
    start = 0
    for bar in range(1, N_BARS + 1):
        prev = PROG[(bar - 1) % 8][0]
        cur = PROG[bar % 8][0] if bar < N_BARS else None
        if cur != prev:
            out.append((start, bar, PROG[start % 8]))
            start = bar
    return out


# ============================== arrangement ==============================

# (name, start_bar, end_bar, per-layer gain).  Bar times: 1 bar = 2.689 s, so
# the reference's form in seconds maps onto these boundaries directly --
# 34 bars = 91.4 s (its breakdown at 90), 52 bars = 139.8 s (its climax at
# 140), 82 bars = 220.5 s (its outro at 220).  Measured against the
# arrangement timeline in ReactorStartup.report.txt.
LAYERS = ["drone", "hum", "throb", "kick", "perc", "bass", "pad", "arp",
          "lead", "tick", "air"]

SECTIONS = [
    ("cold",      0,  4, dict(drone=1.00, hum=0.30, air=0.55)),
    ("pressure",  4,  8, dict(drone=1.00, hum=0.45, throb=0.35, kick=0.25,
                              perc=0.12, air=0.60)),
    ("ignition",  8, 12, dict(drone=1.00, hum=0.58, throb=0.65, kick=0.65,
                              perc=0.35, bass=0.45, pad=0.15, tick=0.15,
                              air=0.70)),
    ("firstpeak", 12, 15, dict(drone=1.00, hum=0.70, throb=0.80, kick=0.90,
                               perc=0.55, bass=0.70, pad=0.60, arp=0.35,
                               tick=0.40, air=0.80)),
    ("groove",    15, 34, dict(drone=1.00, hum=0.75, throb=0.90, kick=1.00,
                               perc=0.80, bass=0.85, pad=0.80, arp=0.70,
                               lead=0.45, tick=0.55, air=0.90)),
    ("breakdown", 34, 41, dict(drone=1.00, hum=0.42, throb=0.40, kick=0.10,
                               perc=0.15, bass=0.28, pad=0.45, tick=0.05,
                               air=0.62)),
    ("rebuild",   41, 52, dict(drone=1.00, hum=0.68, throb=0.80, kick=0.80,
                               perc=0.60, bass=0.80, pad=0.70, arp=0.45,
                               lead=0.28, tick=0.45, air=0.85)),
    ("climax",    52, 56, dict(drone=1.00, hum=0.85, throb=1.00, kick=1.00,
                               perc=1.00, bass=1.00, pad=1.00, arp=0.90,
                               lead=0.85, tick=0.90, air=1.00)),
    ("groove2",   56, 82, dict(drone=1.00, hum=0.75, throb=0.90, kick=0.95,
                               perc=0.80, bass=0.85, pad=0.80, arp=0.70,
                               lead=0.45, tick=0.55, air=0.90)),
    ("outro",     82, 90, dict(drone=1.00, hum=0.40, throb=0.28, kick=0.08,
                               perc=0.12, bass=0.22, pad=0.42, arp=0.12,
                               air=0.60)),
    ("final",     90, 97, dict(drone=1.00, hum=0.62, throb=0.70, kick=0.80,
                               perc=0.58, bass=0.70, pad=0.70, arp=0.48,
                               lead=0.35, tick=0.45, air=0.85)),
]


def bar_gains(key, ramp_bars=2):
    """Per-bar gain for one layer, with the section steps smoothed into ~1-bar
    ramps.  A hard step would read as an edit; a 2.7 s ramp reads as a fade."""
    g = np.zeros(N_BARS)
    for _, s, e, v in SECTIONS:
        g[s:min(e, N_BARS)] = float(v.get(key, 0.0))
    return dsp.smooth(g, ramp_bars)


def bar_env(gb):
    """Per-bar gains -> a per-sample envelope, interpolated between bar
    centres so continuous layers swell instead of stepping."""
    centres = (np.arange(len(gb)) + 0.5) * BAR * SR
    return np.interp(np.arange(N), centres, gb)


# Section LEVEL, dB relative to the loud body.  Cut to the reference's MEASURED
# loudness arc, which disagrees with the form map above -- and the measurement
# wins.  10 s frame-RMS blocks of the reference run:
#   -40.8 | -19.5 -18.4 -18.5 -16.5 | -13.0 -12.5 -12.2 -12.4 -13.7 -13.0 -12.4
#   -12.4 | -22.8 -22.5 | -17.8 -17.0 -17.7 | -12.5 -12.5 -12.1 -12.2 -14.4
#   -13.1 -12.6 -12.6
# so: intro fade -> -18 dB build -> -12.4 dB body -> a DEEP -22.6 dB patch at
# 130-150 s -> -17.5 dB rebuild -> body to the end.  The form map called 90-110 s
# the "breakdown" (measured -13.0, as loud as the body) and 140-150 s the
# "climax" (measured -22.5, the QUIETEST patch in the piece).  Those labels came
# from the band-share timeline, which reports the spectral MIX and says nothing
# about level -- a mid-heavy section can be quiet.  Reading level off a shape
# measurement is CLAUDE.md 0.18's family: a real measurement answering a question
# nobody asked.
LEVELS = [
    (0,   4,  -13.0),   # intro, 0-10.8 s: a swell, not a fade from silence
    (4,  19,   -8.0),   # build, 10.8-51 s
    (19, 47,   -0.6),   # body, 51-127.8 s
    (47, 56,  -15.5),   # the real breakdown, 127.8-150.6 s
    (56, 67,   -9.2),   # rebuild, 150.6-180 s
    (67, 82,   -0.6),   # body, 180-220.5 s
    (82, 85,   -2.2),   # brief pull-back, 220.5-228.6 s
    (85, 97,   -0.6),   # final body, 228.6-260.9 s
]
# The depths were corrected against the delivered-vs-reference block table
# (arc_compare.py), which is the only view that can see WHERE the arc is wrong
# rather than how wide it is -- and they had to be corrected AGAIN when the
# master's pre-gain ceiling moved (see PRE_CEIL_DB), because for as long as the
# limiter was writing part of the shape the table was tuned against a value the
# master owned.  That is the second-writer problem in its purest form: the arc
# is LEVELS' value, and a master that squashes the loud sections owns part of it.
#    rebuild  -11.6 -> -10.2 -> -9.2   delivered 150-180 s sat 1.4 dB, then
#                                      1.8 dB, under the reference's -17.5 dB.
#    pullback  -4.0 ->  -3.1 -> -2.2   delivered 220-230 s sat 0.9, then 1.3 dB
#                                      low against the reference's -13.1 dB dip.
#    edge      48 -> 47                the reference's deep patch starts at
#                                      130 s; bar 48 is 130.6 s.
#    body    0.0 -> -0.6               every body block sat ~1.1 dB hot once the
#                                      limiter stopped pulling the peaks down.
#    build   -8.5 -> -8.0              the 20-30 s block ran 2.3 dB cold.
#    intro  -24.0 -> -13.0             the opening 10 s was a fade from near
#                                      silence 16 dB below the reference's own
#                                      opening, which is why the delivered p5
#                                      was set by the fade rather than by the
#                                      breakdown.  It is still a 12 dB swell.
# Left alone on the same evidence: the build's internal bump (the delivered
# 30-40 s block is loud for its position) is an arrangement property -- the
# build is one continuous ramp here and not there -- so pulling that block
# down would have been faking a shape the music does not have.


def level_curve():
    """Per-sample linear gain from LEVELS, smoothed like every other section
    step.  A single common gain over the whole mix, so it moves the piece's
    loudness WITHOUT touching any balance: side/mid is a ratio of two terms that
    both get the same multiplier, and every layer's own section gain is applied
    inside the layer.  That is why this is the cheap way to buy dynamics -- it
    cannot unbalance the octave profile the way re-gating individual layers
    would."""
    g = np.zeros(N_BARS)
    for s, e, db in LEVELS:
        g[s:min(e, N_BARS)] = 10.0 ** (db / 20.0)
    return bar_env(dsp.smooth(g, 2))


# ============================== the lead ==============================
# The operator's third report was "I listened and it is just one melody
# playing, with no climax".  He is describing the code that used to be here: a
# single three-note figure, the same notes in the same order on every even bar
# from 16 to 96.  The level architecture (SECTIONS, LEVELS) did have a shape --
# a measured arc, a deep patch, a rebuild -- but shape in LEVEL is not shape in
# MATERIAL, and a tune that never changes cannot have a climax.  A climax is a
# change; if every bar is the same bar, there is nothing for it to be a
# departure from.
#
# What is measurable here and what is not has to be kept apart, because this is
# the third round in which the operator's ear found something the panel could
# not:
#
#   MEASURABLE, and measured (see _tools/music/lead_margin.py): each note's
#   margin over the accompaniment sounding at that instant -- "is it audible".
#   That is the same per-note ruler the previous round used, and it must stay
#   green here too, or the new material is inaudible and the development is
#   academic.  It is re-run below.
#
#   NOT MEASURABLE HERE: whether the development READS as development.  "Is it
#   varied" has no meter -- there is no number that says "enough variation".
#   So what is guaranteed is only the mechanical part: the notes are not the
#   same notes twice, the line climbs where a climax needs it to, and a second
#   voice moves against it.  Whether that is a tune is the operator's call, and
#   it will be stated as his call, not dressed up as a measurement.
#
# The vocabulary: F major pentatonic -- the five notes both key estimates
# agreed on (module docstring) -- written as scale STEPS so a phrase can be
# transposed by moving an index and never leaves the set.
SCALE = ["F4", "G4", "A4", "C5", "D5", "F5", "G5", "A5", "C6"]

# Theme A -- the machine's own signal tone, unchanged from the first version.
# Three syncopated notes that fall back to where they started.  It is the
# piece's identity and it is deliberately the plainest material here: the
# point of a recognisable cell is that it can be quoted, answered and climbed.
A_STEPS = [3, 2, 1]              # C5 A4 G4
A_BEATS = [0.0, 1.5, 2.5]
A_DURS = [0.50, 0.50, 0.75]

# Theme B -- the contrast A cannot provide.  A ends where it began; B ASCENDS
# and stays up, which is the shape a climax is made of.  Eight beats (two
# bars) climbing the set to a held top note.  This is the only material in the
# piece that finishes higher than it starts.
B_STEPS = [1, 2, 3, 4, 5, 7]     # G4 A4 C5 D5 F5 A5 -- up to a held A5
B_BEATS = [0.0, 1.0, 2.0, 3.0, 4.5, 6.0]
B_DURS = [0.85, 0.85, 0.85, 1.30, 1.45, 2.30]
# B2 is B moved up one scale step, so it tops out on C6, the ceiling of the
# set.  Used for the last statement, so the piece finishes its climb at the top
# rather than just below it.
B2_STEPS = [2, 3, 4, 5, 6, 8]    # A4 C5 D5 F5 G5 C6

# The counter-line: a slow sustained answer that runs against the plucked
# motif in the second body.  It DESCENDS while A is a repeated upward cell, so
# the two voices move in contrary motion and neither is "the tune, again".
CTR_STEPS = [7, 6, 5, 4, 3]      # A5 G5 F5 D5 C5

# Voice per role.  All three are the same `pluck` generator so the lead stays
# ONE instrument -- the octave profile was matched with it, and changing the
# timbre family would move a number already pinned.  Only the partial count
# moves: the motif is bright and short, the climax rounder, the counter a swell.
VOICE = {"a": dict(bright=5), "b": dict(bright=4), "ctr": dict(bright=2)}


def section_of(bar):
    for name, s, e, _g in SECTIONS:
        if s <= bar < e:
            return name
    return "final"


def lead_plan():
    """The whole lead line, as (bar, beat, note, dur, tag) events.

    Built in one place on purpose: the renderer and the margin ruler both read
    THIS list, so a ruler cannot end up measuring its own private copy of the
    schedule while believing it is measuring the piece.

    The arc, in bar numbers (1 bar = 2.689 s; section names from SECTIONS):

      15-34  groove    A stated, then answered a step out -- call and response
      41-52  rebuild   A cut to its two-note head, climbing a step per group,
                       closing on a rising run into the drop
      52-55  climax    B, then B2 -- the ascent, over the quiet bed, right
                       after the riser: the melodic lift
      56-82  groove2   A returns under a descending counter-line (contrary
                       motion); the last four bars restate B2 over A -- the
                       final peak, landing on the loud body
      82-90  outro     the melody drops out entirely -- the release
      90-97  final     A augmented (notes ~twice as long), winding down
    """
    ev = []

    def play(bar, steps, beats, durs, tag, shift=0):
        """Place a phrase at (bar, beat 0), folding beats past 4 into the
        following bars so a two-bar phrase is written as one list.  `shift`
        transposes by scale steps, clamped to the set."""
        for s, b, d in zip(steps, beats, durs):
            i = min(max(int(s) + shift, 0), len(SCALE) - 1)
            ev.append((bar + int(b // 4), float(b % 4), SCALE[i],
                       float(d), tag))

    # -- groove 15-34 (lead 0.45): A, answered out of phase -----------------
    # Statements land on even bars -- the motif has always been on even bars
    # and its syncopation needs the space after it.  Alternating the
    # transposition 0/+1/0/-1 gives the call-and-response the first version did
    # not have, using the same three notes, so the identity survives the
    # development instead of being replaced by it.
    seq = [0, 1, 0, -1, 0, 1, 0, -1]
    for k, bar in enumerate(range(16, 34, 2)):
        play(bar, A_STEPS, A_BEATS, A_DURS, "a", shift=seq[k % len(seq)])

    # -- rebuild 41-52 (lead 0.28): a two-note cell climbing ----------------
    # The cell is A's head (C5 A4).  Raising it one step every two bars lifts
    # the tension across the whole rebuild; the last group is a run that lands
    # on the downbeat of the climax instead of merely stopping.
    for k, bar in enumerate(range(42, 52, 2)):
        play(bar, A_STEPS[:2], [0.0, 1.5], [0.45, 0.60], "a", shift=k)
    play(51, [2, 3, 4, 5], [0.0, 1.0, 2.0, 3.0], [0.40, 0.40, 0.40, 0.55], "a")

    # -- climax 52-55 (lead 0.85): the ascent -------------------------------
    play(52, B_STEPS, B_BEATS, B_DURS, "b")
    play(54, B2_STEPS, B_BEATS, B_DURS, "b")

    # -- groove2 56-82 (lead 0.45): A over a descending counter-line --------
    seq2 = [0, 0, 1, 0, -1, 0, 1, -1, 0, 0]
    for k, bar in enumerate(range(58, 78, 2)):
        play(bar, A_STEPS, A_BEATS, A_DURS, "a", shift=seq2[k % len(seq2)])
    # one long note every four bars, two bars long, so it is a swell and not a
    # hit; it descends while the motif repeats, which is the contrary motion.
    for k, bar in enumerate(range(59, 78, 4)):
        play(bar, [CTR_STEPS[k % len(CTR_STEPS)]], [0.0], [2.0 * BAR], "ctr")

    # -- final peak 78-81: B2 over A, both at once --------------------------
    # The last four bars of the loud body.  Two statements together -- the
    # rising theme on top, the returning motif beneath -- so the peak is the
    # densest moment as well as the loudest, and the drop into the outro has
    # something to fall from.
    play(78, B2_STEPS, B_BEATS, B_DURS, "b")
    for bar in (78, 80):
        play(bar, A_STEPS, A_BEATS, A_DURS, "a", shift=1)

    # -- final 90-97 (lead 0.35): A, augmented ------------------------------
    # The same three notes at roughly twice the duration: recognised, but
    # slowed, which is how a machine winds down rather than stops.
    play(92, A_STEPS, [0.0, 3.0, 5.0], [1.00, 1.00, 1.60], "a")
    play(95, [3], [0.0], [3.00], "b")     # C5 held, the signal fading out

    return ev


def render_lead(gb, dry=None, send=None):
    """The lead voice alone, as (dry, send), so it can be measured apart from
    the rest of the mix.

    Split out of render_stems for two reasons.  First, the margin ruler has to
    hear THIS lead against the rest of the piece, and the only honest way to do
    that is to render the same plan through the same code -- not to re-derive
    the notes from a private copy of the schedule, which would measure the
    copy.  Second, the per-note dry/send split is what makes the wet/dry ratio
    tunable, because the assembly is linear in the two.

    Levels default to the shipped constants, so calling this with no arguments
    gives the lead as it is actually heard; render_stems calls it at UNIT level
    and caches that, so the level stays a knob (see with_lead)."""
    d = LEAD_DRY if dry is None else dry
    s = LEAD_SEND if send is None else send
    dm = np.zeros(N)
    sm = np.zeros(N)
    for bar, beat, note, dur, tag in lead_plan():
        gl = gb["lead"][bar] if 0 <= bar < N_BARS else 0.0
        if gl <= 0.01:
            continue
        p = dsp.pluck(hz(note), dur, SR, **VOICE[tag])
        add(dm, p, at(bar, beat), d * gl)
        add(sm, p, at(bar, beat), s * gl)
    return dm, sm


def add(buf, sig, start_s, gain=1.0):
    i = int(round(start_s * SR))
    if i < 0:
        sig = sig[-i:]
        i = 0
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[:j - i] * gain


# ============================== extra instruments ==============================

def klaxon(dur, f_a=hz("F5"), f_b=hz("G5"), rate=5.5):
    """Two-tone industrial alarm.  Alternating by the sign of a sine rather
    than by a duty cycle, so the tone flips cleanly with no ramp between."""
    t = dsp.t_axis(dur, SR)
    gate = 0.5 * (1.0 + np.sign(np.sin(dsp.TAU * rate * t)))
    tone = (np.sin(dsp.TAU * f_a * t) * (1 - gate)
            + np.sin(dsp.TAU * f_b * t) * gate)
    tone += (0.35 * np.sin(dsp.TAU * f_a * 2 * t) * (1 - gate)
             + 0.28 * np.sin(dsp.TAU * f_b * 2 * t) * gate)
    e = dsp.env(dur, SR, attack=0.02, decay=max(0.01, dur - 0.35), curve=1.0,
                sustain=0.85, release=0.35)
    return dsp.bandpass(tone * e, SR, 300, 4500)


def impact(f_hi=95.0, f_lo=31.0, tau=0.09, dur=2.6, seed=31):
    """Section-boundary hit: a sub that drops into the floor plus a noise
    crash.  Lands the ear on the downbeat of a new part."""
    t = dsp.t_axis(dur, SR)
    f = f_lo + (f_hi - f_lo) * np.exp(-t / tau)
    body = dsp.chirp(f, dur, SR) * dsp.env(dur, SR, attack=0.002, decay=1.1,
                                           curve=2.0)
    cr = dsp.bandpass(dsp.noise(dur, SR, seed=seed), SR, 200, 6000)
    cr = cr * dsp.env(dur, SR, attack=0.001, decay=0.9, curve=2.2)
    return body + 0.45 * cr


def bass_note(root_hz, dur):
    """Short, dark, and slightly detuned so it reads as a machine under load
    rather than a bass guitar."""
    body = dsp.additive(root_hz, dur, SR,
                        [(1, 1.00, dur * 0.75), (2, 0.34, dur * 0.5),
                         (3, 0.11, dur * 0.35), (5, 0.04, dur * 0.25)],
                        detune=0.35)
    body *= dsp.env(dur, SR, attack=0.006, decay=dur - 0.05, curve=1.6,
                    sustain=0.4, release=0.06)
    return dsp.lowpass(body, SR, 420)


# ============================== air bed ==============================
# The reference carries energy up to 10 kHz; the raw mix has a CLIFF above
# 640 Hz (measured deltas -9.6, -22.2, -27.6, -24.4, -21.3 dB).  That is not a
# tilt an EQ can lift -- the pad is a pure sine stack and the drone/hum are
# additive sines, so there is simply no harmonic content up there to lift.  The
# missing octaves have to be written, which is what this bed is.
#
# The contour is read off the measured deficit as spectral DENSITY, not band
# power, because the octave bands double in width going up: a per-band target
# that is flat is already -3 dB/octave in density.  The points sit at each
# band's GEOMETRIC CENTRE, because a contour that is linear in log-frequency
# has a mean over a log-symmetric interval equal to its midpoint value -- so a
# point at the centre sets that band's power exactly:
#     power_dB = density(centre) + 10*log10(bandwidth)
# Every value below is that identity solved backwards from a measurement, which
# is why none of them are round numbers.
#
# MEASURED AGAINST THE ASSEMBLED MIX, NOT THE DRY CORE.  The first version of
# this table was solved against `mono` alone, and it came out 6 dB hot in the
# 640-1280 band -- because the reverb, the ping-pong delay and the pad chorus
# already put energy there and the dry core does not show it.  What the bed has
# to supply is "what the mix still needs AFTER the wet path", so the reference
# is the assembly with air_amt=0.  That measurement also says the bed must sit
# in a broad DIP around 900 Hz (the wet path's own content is strongest there)
# while the octaves above 2.5 kHz need the full pink plateau.
AIR_PTS = [(200, -92.0), (400, -72.0), (560, -58.0), (905, -44.6),
           (1810, -41.7), (3620, -45.3), (7240, -54.2), (14300, -67.0),
           (19000, -82.0)]
# Absolute offset applied to the contour.  The contour fixes SHAPE only; this
# number places it against the rest of the mix, and it was SOLVED rather than
# picked: for each octave band, take the power the band must reach, subtract
# the power the mix already has there, and what remains is what the bed has to
# supply.  Measured against the assembled mix (air_amt=0) that comes out
# 40.39 / 40.23 / 40.26 / 39.66 / 39.49 dB for the five bands from 640 Hz up --
# a spread of 0.90 dB, which is the residual of the shape fit.  The bands below
# 640 Hz need nothing: the wet path puts them ABOVE target on its own, which is
# why the master EQ loop attenuates there rather than the bed propping it up.
# Note the unit is the rfft's own arbitrary scale, so it is empirical to this
# code path and not a level in dBFS.
AIR_DB = 40.0
# How wide the bed is, as the multiplier on its own difference part.  This is
# the ONE free width knob in the piece: the reverb's width is a measurement of
# the reference's reverb (rev_diff, at side/mid 0.125) and the core is a dense
# mono mix, so widening the mix without moving either of those means widening
# the layer that was added last.  Measured: side/mid is linear in air_wid^2
# (0.45 -> 0.0783, 0.70 -> 0.1055, 0.95 -> 0.1446) because the difference part
# is pure side and the common part pure mid.  The chain then narrows what it is
# given by about 0.90x (the soft-clip and limiter act per channel), so the
# number is set to land the DELIVERED file, not the assembled buffer:
# 0.85 -> assembled 0.129 -> delivered ~0.116.
AIR_WID = 0.85

# ---------------------------------------------------------------------------
# THE BED IS A HIT, NOT A FLOOR  (2026-10-05)
#
# Every number above was solved on octave-band POWER, and the bed satisfied all
# of them while being the worst thing in the piece -- the operator's report was
# "why is there that rain-like white noise, it's very noisy and I can hardly hear
# the melody".  That is what a continuous floor does: it masks.  Band power
# cannot see the difference, because a hiss at the right power and the hits it
# stands in for ARE the same number to an octave-band meter.
#
# Measured on the 2-8 kHz band as 50 ms frame RMS (one ruler, 44100/2):
#
#              median     p90    spread
#   reference  -28.36  -22.09      6.26    <- the target
#   bed on     -25.75  -22.71      3.03    <- floor 2.6 dB HOT, peaks 0.6 short
#   bed off    -30.96  -24.71      6.26    <- texture EXACT, everything 2.6 cold
#
# "spread" is p90 - median: how far the hits stand above the floor.  With the bed
# on it collapses from 6.26 to 3.03; the bed buys 2.6 dB of band power by lifting
# the floor 5.2 dB and the peaks only 2.0 dB.  With the bed off the texture is
# the reference's to 0.01 dB -- so the CONTENT already has the right shape, and
# the bed only has to stop being a floor.  Hence the gate.
#
# The gate rides the tick grid (8th notes), the same grid the tick layer uses,
# so the bed lands with the hits that are already there instead of between them.
# It is normalised to unit mean, which is the property that keeps every AIR_*
# number above valid: the gate moves energy in TIME and leaves band power alone,
# so the octave-band fit still holds.  DEPTH 0 reproduces the old continuous bed
# exactly, which is what makes the sweep in _tools a real A/B and not a rewrite.
AIR_GATE_MS = 130.0     # decay of one hit; short enough to clear the next 8th
# Swept on the 2-8 kHz spread, with the accent phase matched to the tick layer
# (`idx % 2 == 1`, the same odd 8ths the ticks accent):
#
#   depth  spread  median    p90   within      vs reference 6.26 / -28.36 / -22.09
#   0.00     3.10  -25.71  -22.61   77.4%      the old continuous bed
#   0.35     4.55  -26.67  -22.12   80.3%
#   0.45     5.34  -27.25  -21.91   81.4%
#   0.55     6.03  -27.78  -21.75   81.8%
#   0.65     6.77  -28.36  -21.60   81.4%
#
# 0.60 is the crossing: spread lands ~0.1 dB over the reference's and the floor
# ~0.3 dB over it, where 0.55 leaves the floor 0.6 hot and 0.65 overshoots the
# contrast.  Note that band power, side/mid and correlation do not move anywhere
# in that sweep (worst band +0.65 -> +0.66 dB, s/mid 0.122 -> 0.123) -- that is
# the mean-1 normalisation, and it is the reason this could be tuned at all.
AIR_GATE_DEPTH = 0.60   # 0 = old continuous bed, 1 = fully gated
AIR_ACCENT = 0.45       # level of the unaccented 8ths, vs 1.0 on the accent


def air_gate(depth=AIR_GATE_DEPTH, decay_ms=AIR_GATE_MS, accent=AIR_ACCENT):
    """Per-8th decay envelope, normalised to mean 1.

    Mean 1 is the whole point: it means turning the gate on cannot move any band's
    power, so AIR_PTS/AIR_DB -- which were solved to match the reference's octave
    profile -- stay solved.  Only the placement in time changes."""
    t = dsp.t_axis(N / SR, SR)
    p = 0.5 * BEAT                              # the tick grid
    ph = (t % p) / p
    hit = np.exp(-ph * p / (decay_ms * 1e-3))
    idx = np.floor(t / p).astype(np.int64)
    # Odd 8ths are the accented ones -- the tick layer's own accent is
    # `1.0 if e8 % 2 else 0.55`, so accenting these puts the bed ON the hits
    # that are already there instead of in the gaps between them.  That is what
    # makes this a top end rather than a second, off-grid rhythm.
    g = hit * np.where(idx % 2 == 1, 1.0, accent)
    g = g / g.mean()
    return (1.0 - depth) + depth * g


def air_bed(seed=77, depth=AIR_GATE_DEPTH, decay_ms=AIR_GATE_MS):
    """Shaped noise: the octaves above 640 Hz, written rather than EQ'd in.

    Breathes on two incommensurate slow swells (34 s and 13 s) so it reads as a
    live ventilation stack rather than a loop, is gated by the same section
    table as every other layer so it swells into the climax and pulls back in
    the breakdown beside them, and is chopped into hits by air_gate() so it is
    a struck top rather than a continuous one (see the note above)."""
    dur = N / SR
    w = dsp.contour_db(dsp.noise(dur, SR, seed=seed), SR, AIR_PTS)
    t = dsp.t_axis(dur, SR)
    swell = (0.55 + 0.30 * (0.5 + 0.5 * np.sin(dsp.TAU * t / 34.0))
             + 0.15 * (0.5 + 0.5 * np.sin(dsp.TAU * t / 13.0 + 1.3)))
    return (10 ** (AIR_DB / 20.0) * w * swell * air_gate(depth, decay_ms)
            * bar_env(bar_gains("air")))


# ============================== the piece ==============================

def render_stems():
    """Render the mono core and the two things that feed the wet returns.

    Deliberately split from the stereo assembly.  The assembly is where the
    width is set, and width is a number I have to converge on by measuring --
    at six minutes a render that convergence is unaffordable, and a knob I
    cannot afford to turn is a knob I will end up guessing at.  Cached to
    out/stems.npz so `--reuse` assembles in seconds."""
    n = N
    dur_total = n / SR
    gb = {k: bar_gains(k) for k in LAYERS}
    mono = np.zeros(n)
    send = np.zeros(n)

    # ---------- continuous: drone, hum, throb ----------
    # The sub pedal.  F1 = 43.65 Hz is the measured peak of the reference's
    # spectrum, so the drone is tuned to put its fundamental exactly there.
    d = (dsp.sine(F1, dur_total, SR)
         + 0.90 * dsp.sine(F1 + 0.06, dur_total, SR)
         + 0.22 * dsp.sine(F1 * 2, dur_total, SR)
         + 0.07 * dsp.sine(F1 * 3, dur_total, SR))
    mono += 0.30 * d * bar_env(gb["drone"])

    # Facility hum: a stack on F2 with a bump near 180 Hz so it has a body
    # rather than being pure rumble.
    h = (dsp.additive(F2, dur_total, SR, [(k, 1.0 / k, 0.0) for k in range(1, 13)],
                      detune=0.5)
         + 0.55 * dsp.additive(F3, dur_total, SR,
                               [(k, 1.0 / k, 0.0) for k in range(1, 9)], detune=0.7)
         + 0.35 * dsp.additive(hz("C3"), dur_total, SR,
                               [(k, 1.0 / k, 0.0) for k in range(1, 7)], detune=0.6))
    h = dsp.lowpass(dsp.peak(h, SR, 180.0, 1.2, 5.0), SR, 1400)
    h *= bar_env(gb["hum"])
    mono += 0.115 * h
    send += 0.30 * h

    # The throb: the pedal pulsing at the beat rate.  This is the pulse the
    # whole piece is measured against, so it is gated by an exactly periodic
    # envelope rather than by hand-placed hits.
    t = dsp.t_axis(dur_total, SR)
    pulse = np.exp(-(((t % BEAT) / BEAT) / 0.16) ** 2)
    accent = 0.78 + 0.22 * np.cos(dsp.TAU * t / (2.0 * BAR))
    th = (dsp.sine(F1, dur_total, SR)
          + 0.30 * dsp.sine(F1 * 2, dur_total, SR)) * pulse * accent
    mono += 0.30 * th * bar_env(gb["throb"])

    # ---------- pad ----------
    pad = np.zeros(n)
    for s, e, (_name, _root, tones) in chord_spans():
        span = (e - s) * BAR
        dur = span + 1.6
        v = dsp.pad_chord([hz(x) for x in tones], dur, SR,
                          detune_hz=0.85, attack=1.15)
        v *= dsp.env(dur, SR, attack=1.15, decay=max(0.02, dur - 1.15 - 1.3),
                     curve=1.0, sustain=0.88, release=1.3)
        add(pad, v, at(s), 1.0)
    pad *= bar_env(gb["pad"])
    mono += 0.052 * pad
    send += 0.55 * pad

    # ---------- per-bar events ----------
    for bar in range(N_BARS):
        _name, root, tones = chord_bar(bar)
        tones_hz = [hz(x) for x in tones]

        # kick: beats 1 and 3, plus a pickup on the last bar of every 4
        gk = gb["kick"][bar]
        if gk > 0.01:
            k = dsp.kick(0.95, SR)
            add(mono, k, at(bar, 0.0), 0.95 * gk)
            add(mono, k, at(bar, 2.0), 0.88 * gk)
            if bar % 4 == 3:
                add(mono, k, at(bar, 3.5), 0.52 * gk)

        # metal hits: a struck-casing backbeat, alternating pitch
        gp = gb["perc"][bar]
        if gp > 0.01:
            pit = 196.0 if bar % 2 == 0 else 233.08
            m = dsp.metal_hit(0.85, SR, pit, seed=7 + (bar % 3))
            add(mono, m, at(bar, 1.5), 0.30 * gp)
            add(mono, m, at(bar, 3.0), 0.22 * gp)
            add(send, m, at(bar, 1.5), 0.09 * gp)

        # closed tick on every 8th, accented off-beat
        gt = gb["tick"][bar]
        if gt > 0.01:
            for e8 in range(8):
                acc = 1.0 if e8 % 2 else 0.55
                tk = dsp.tick(0.07, SR, seed=40 + e8)
                add(mono, tk, at(bar, e8 * 0.5), 0.055 * gt * acc)
                add(send, tk, at(bar, e8 * 0.5), 0.05 * gt * acc)

        # bass: root on the downbeat, a second push under the climax
        gba = gb["bass"][bar]
        if gba > 0.01:
            bn = bass_note(hz(root), 1.55 * BEAT)
            add(mono, bn, at(bar, 0.0), 0.30 * gba)
            if gb["kick"][bar] > 0.5:
                add(mono, bn, at(bar, 2.5), 0.20 * gba)

        # 16th arpeggio over the chord tones
        ga = gb["arp"][bar]
        if ga > 0.01:
            for i in range(16):
                note = tones_hz[(i // 2) % len(tones_hz)] * 2.0
                p = dsp.pluck(note, 0.22, SR)
                pan = -0.25 if i % 2 == 0 else 0.25
                add(mono, p, at(bar, i * 0.25), 0.048 * ga)
                add(send, p, at(bar, i * 0.25), 0.06 * ga)

        # (the lead is deliberately NOT scheduled here any more.  See the pass
        # after this loop: a per-bar hook cannot carry theme B, which is two
        # bars long, and it left the melody's description split between the
        # loop and the ruler that measures it.)

    # ---------- lead: a developed line, scheduled as a whole ----------
    # Cached at UNIT level, NOT mixed in here.  See with_lead: the level is
    # applied once, at assembly, so that changing it is a knob rather than a
    # six-minute render followed by a silent chance to ship the old level.
    lm, ls = render_lead(gb, dry=1.0, send=1.0)

    # ---------- fills: the bar before each drop, accelerating ----------
    # A climax has to be ARRIVED at.  Without a fill the densest bar is just a
    # step, which is part of what "no climax" points at.  The roll doubles its
    # rate across the bar (8ths then 16ths) and swells into the downbeat.
    for fbar in (51, 77):
        for i in range(16):
            b = i * 0.5 if i < 8 else 4.0 + (i - 8) * 0.25
            g = 0.030 + 0.055 * (i / 15.0)
            tk = dsp.tick(0.055, SR, seed=95 + i)
            add(mono, tk, at(fbar, b), g)
            add(send, tk, at(fbar, b), 0.7 * g)

    # ---------- section markers ----------
    for bar in (12, 34, 52, 90):
        add(mono, klaxon(1.7 * BEAT), at(bar, 0.0), 0.055)
    for bar in (34, 52):
        add(mono, impact(), at(bar, 0.0), 0.30 if bar == 52 else 0.16)
    for bar in (41, 90):
        add(mono, impact(), at(bar, 0.0), 0.20)
    for bar in (8, 12, 41, 82):
        add(mono, dsp.steam(3.2, SR, seed=bar), at(bar, 0.0), 0.10)

    # riser: 4 bars into the climax, noise + a sub that doubles in pitch
    r_start, r_dur = at(48), 4 * BAR
    rn = dsp.sweep_filter(dsp.noise(r_dur, SR, seed=21), SR, 180.0, 5200.0,
                          q=1.4, curve=1.6)
    rn *= np.linspace(0.05, 1.0, len(rn)) ** 1.5
    add(mono, rn, r_start, 0.10)
    sub = dsp.chirp(lambda tt: 33.0 * 2.0 ** (np.clip(tt, 0.0, r_dur) / r_dur),
                    r_dur, SR)
    sub *= np.linspace(0.1, 1.0, len(sub)) ** 2
    add(mono, sub, r_start, 0.16)

    # ---------- air bed ----------
    # Two independent seeds give a common part and a difference part, so the
    # bed's width is a single measurable multiplier (AIR_WID) instead of an
    # accident.  Deliberately kept OUT of `send`: the reverb's own width is
    # already at target, and smearing a 2.9 s tail over a diffuse noise bed
    # would only move a number I have already matched.
    a1 = air_bed(seed=77)
    a2 = air_bed(seed=78)
    return dict(mono=mono, send=send, pad=pad, leadD=lm, leadS=ls,
                airC=0.5 * (a1 + a2), airD=0.5 * (a1 - a2))


def with_lead(stems, dry=None, send=None):
    """Fold the cached unit-level lead into mono/send at the current level.

    This exists because of a trap that cost two rounds.  The lead used to be
    mixed into the cached mono/send at whatever LEAD_DRY was when the cache was
    built, so changing the level and running `--reuse` shipped the OLD level
    and said nothing -- the §0.15 family of failure, except that this one
    renders, masters, measures and plays back perfectly.  Kept out of the
    cache, the level is a knob again: a sweep costs one assembly per point
    instead of a six-minute render, which is the difference between measuring a
    level and guessing at one.

    `dry=0, send=0` is the exact accompaniment with no lead in it, which is
    what a margin has to be measured against.

    Idempotent: the result carries an empty lead, so assemble() -- which calls
    this itself -- cannot fold the same lead in a second time.  Without that,
    every caller that prepared stems by hand would silently get double lead."""
    d = LEAD_DRY if dry is None else dry
    s = LEAD_SEND if send is None else send
    return dict(stems, mono=stems["mono"] + d * stems["leadD"],
                send=stems["send"] + s * stems["leadS"],
                leadD=np.zeros(len(stems["mono"])), leadS=np.zeros(len(stems["mono"])))


# Width knobs.  The first version used two fully independent reverbs, one per
# channel, which is a maximally decorrelated wet path: it measured side/mid
# 0.266 on its own core-and-wet sum against the reference's 0.116.  The
# useful construction is mid/side, not left/right -- ONE shared return that
# lands in the centre plus a second return that is added to one side and
# subtracted from the other.  Width is then a single multiplier on the
# difference term, which is a number I can measure and move.
ASSEMBLE = dict(core=0.95, rev_amt=0.30, rev_diff=0.32, dly_amt=0.055,
                pad_amt=0.028, air_amt=1.0, air_wid=AIR_WID)


def assemble(stems, core=None, rev_amt=None, rev_diff=None, dly_amt=None,
             pad_amt=None, air_amt=None, air_wid=None, ret_diff_ir=False,
             lead_dry=None, lead_send=None):
    """Stereo assembly.  Returns (L, R), or the raw returns when
    ret_diff_ir, which is how the width budget is measured term by term.

    The lead level enters HERE, from with_lead, not from the cache."""
    stems = with_lead(stems, lead_dry, lead_send)
    p = dict(ASSEMBLE)
    for k, v in (("core", core), ("rev_amt", rev_amt), ("rev_diff", rev_diff),
                 ("dly_amt", dly_amt), ("pad_amt", pad_amt),
                 ("air_amt", air_amt), ("air_wid", air_wid)):
        if v is not None:
            p[k] = v

    mono, send, pad = stems["mono"], stems["send"], stems["pad"]
    n = len(mono)

    wc = dsp.comb_reverb(send, SR, rt60=2.9, predelay_ms=18.0, damp=4800.0, seed=1)
    wd = dsp.comb_reverb(send, SR, rt60=2.9, predelay_ms=27.0, damp=5200.0, seed=2)
    n2 = max(len(wc), len(wd))
    wc = np.pad(wc, (0, n2 - len(wc)))
    wd = np.pad(wd, (0, n2 - len(wd)))
    wl = wc + p["rev_diff"] * wd
    wr = wc - p["rev_diff"] * wd

    dl, dr = pingpong(send, 0.75 * BEAT, feedback=0.42, mix=0.55)
    dl = np.pad(dl, (0, max(0, n2 - len(dl))))
    dr = np.pad(dr, (0, max(0, n2 - len(dr))))

    # pad width: three chorus voices, outer two toward the sides
    ch = dsp.chorus(np.pad(pad, (0, max(0, n2 - len(pad)))), SR,
                    depth_ms=9.0, rate_hz=0.19, voices=3)
    pl = 0.55 * ch[0] + 0.45 * ch[2]
    pr = 0.55 * ch[1] + 0.45 * ch[2]

    mono_p = np.pad(mono, (0, n2 - len(mono)))

    # air: common part in the centre, difference part spread by AIR_WID
    airC = np.pad(stems["airC"], (0, n2 - len(stems["airC"])))
    airD = np.pad(stems["airD"], (0, n2 - len(stems["airD"])))
    al = p["air_amt"] * (airC + p["air_wid"] * airD)
    ar = p["air_amt"] * (airC - p["air_wid"] * airD)

    if ret_diff_ir:
        return dict(wl=wl[:n], wr=wr[:n], dl=dl[:n], dr=dr[:n],
                    pl=pl[:n], pr=pr[:n], mono=mono_p[:n],
                    al=al[:n], ar=ar[:n])
    L = (p["core"] * mono_p + p["pad_amt"] * pl + p["rev_amt"] * wl
         + p["dly_amt"] * dl + al)
    R = (p["core"] * mono_p + p["pad_amt"] * pr + p["rev_amt"] * wr
         + p["dly_amt"] * dr + ar)
    # Section LEVEL goes LAST and hits BOTH channels identically: one common
    # multiplier over the whole mix.  It is applied here rather than baked into
    # the cached stems so the table can be re-tuned with --reuse (seconds) --
    # the same reason the stereo knobs live here and not in render_stems.  A
    # common gain cannot move side/mid or L/R correlation, because both are
    # ratios of two terms that receive the same multiplier, so this buys the
    # piece's dynamics without disturbing either width number.
    lv = level_curve()
    return L[:n] * lv, R[:n] * lv


def pingpong(x, t_s, feedback=0.42, mix=0.5):
    """Alternating-tap delay: odd taps left, even taps right."""
    n = len(x)
    d = max(1, int(round(t_s * SR)))
    L = np.zeros(n)
    R = np.zeros(n)
    g = mix
    k = 1
    while d * k < n and g > 1e-3:
        off = d * k
        src = x[:n - off]
        if k % 2:
            L[off:] += g * src
        else:
            R[off:] += g * src
        g *= feedback
        k += 1
    return L, R


# ============================== master ==============================

# Octave bands and the reference's measured levels in each, dB re the 40-80 Hz
# band.  The master chain measures the mix against this and corrects, rather
# than trusting that the instruments came out balanced.
#
# These numbers are from analyze.py run on the reference AT 44100 Hz.  The
# first set was taken at the tool's default 22050 Hz, and that was wrong in a
# way that mattered: ffmpeg's downsample puts a 22 kHz low-pass in front of
# the measurement, so "10240-20000" was really "10240-11025" and the whole top
# octave read ~10 dB darker than it is.  The EQ loop then faithfully forced my
# mix onto the low-passed curve -- a correction obeying a target that was
# itself an artifact.  The ruler is part of the measurement: both sides are
# now measured at the same rate with the same window.
OCT_EDGES = [20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10240, 20000]
TARGET_DB = [-10.2, 0.0, -3.8, -6.6, -11.4, -10.0, -10.6, -11.2, -17.1, -27.1]
# Loudness target = the reference's MEAN frame RMS, not its MEDIAN.  This line
# used to carry -13.43, which is the reference's MEDIAN (-13.62) and not its
# mean at all -- and normalizing a mean onto a median is exactly why the piece
# shipped as a flat -13.5 bed.  A flat piece has mean == median, so the number
# silently asserted "no dynamics"; the reference's mean sits 2.98 dB BELOW its
# median precisely because it has an arc (a quiet intro, a deep breakdown), and
# matching the mean is what a loudness match is supposed to hold.  Measured
# over 50 ms frames.
#
# -- and measured over MUSIC frames only.  The reference is bookended by 66
# frames (45 at 0.00-2.25 s, 21 at 262.80-263.85 s) that sit at exactly -119
# or -120 dBFS: 3.30 s of digital silence, a rip artifact (check_song already
# records that its opening is not a fade but an artifact).  Including them
# measured -16.41 and held this piece 1.31 dB quieter than the music it is
# supposed to match; over the 5211 frames that are actually music the
# reference measures -15.10.  The rule is reproducible: frames <= -100 dBFS in
# the reference are the artifact, and their locations were checked rather than
# assumed -- the two runs are contiguous, at the two ends, and every value is
# -119/-120, which is what a rip looks like and not what a fade looks like.
TARGET_RMS = -15.10
TARGET_SIDE_MID = 0.116
TARGET_CORR = 0.792
# Dynamic range = p95 - p5 of the 50 ms frame RMS.  The mean above places the
# piece's loudness; this places its SHAPE, and the two are independent: a loud
# flat piece and a quiet dynamic one can share a mean.  Over the same MUSIC
# frames the reference measures p5 -23.86, p95 -10.10 -> 13.76 dB, and the
# whole point of LEVELS is to write that arc back.  (Over all frames, artifact
# included, the same measurement reads 14.56 -- the 0.8 dB difference is the
# silence moving p5, which is why both targets are quoted on one basis.)
# Without this check the panel was blind to the piece shipping as a 4.5 dB
# slab -- every other number in it is a level or a balance, and a slab has all
# of those right.
TARGET_RANGE_DB = 13.76

# ---------------------------- top-end texture ----------------------------
# Band POWER cannot tell a continuous hiss from the hits it stands in for: an
# octave-band meter reads the same number for both.  That blind spot is the
# whole defect here.  Every band check below was green while the piece sounded,
# in the operator's words, like rain -- "why is there that rain-like white
# noise, it is very noisy and I can hardly hear the melody".  A floor masks; a
# rhythm does not, at identical power.
#
# These four numbers are the ones that CAN see it, measured as the 50 ms frame
# RMS of the 2-8 kHz band (one ruler: 44100 Hz, 2 ch, the same frames as
# TARGET_RMS):
#
#              median     p90   spread   within 6 dB
#   reference  -28.36  -22.09     6.26        77.5%
#
# "spread" = p90 - median is how far the hits stand above the floor, and
# "within 6 dB" is how much of the time sits near that floor.  A bed and a
# rhythm can share band power but not these: the original continuous bed
# measured median -25.71, p90 -22.61, spread 3.10 -- 2.6 dB hot on the floor,
# 0.5 dB cold on the peaks.  That asymmetry IS the masking, and it is exactly
# what band power is blind to.
TEX_BAND_HZ = (2000.0, 8000.0)
REF_TEX_MED_DB = -28.36
REF_TEX_P90_DB = -22.09
REF_TEX_WITHIN = 0.775


def texture_stats(x):
    """(median, p90, spread, within6dB) of the frame RMS in TEX_BAND_HZ."""
    f = frame_rms_db(dsp.bandpass(x, SR, TEX_BAND_HZ[0], TEX_BAND_HZ[1]))
    f = f[f > -100.0]
    med = float(np.median(f))
    p90 = float(np.percentile(f, 90.0))
    return med, p90, p90 - med, float((f > med - 6.0).mean())


def octave_profile(x, n=8192, hop=2048):
    """Mean power spectrum summed into octave bands, dB re the 40-80 Hz band.

    n is 8192 (5.4 Hz at 44.1 kHz) to match the reference measurement.  At
    n=2048 the 20-40 Hz band is a single 21.5 Hz bin sitting one bin under the
    43.65 Hz sub, so the band's "level" is mainlobe leakage from its louder
    neighbour and no EQ can move it -- the answer was about the window, not
    the audio.  hop is a quarter of n for memory only; the quantity is an
    average over the file, so fewer frames estimate the same mean."""
    S = stft(x, n, hop)
    freqs = np.fft.rfftfreq(n, 1.0 / SR)
    P = (S ** 2).mean(axis=1)
    lv = []
    for a, b in zip(OCT_EDGES[:-1], OCT_EDGES[1:]):
        m = (freqs >= a) & (freqs < b)
        lv.append(float(P[m].sum()) if m.any() else 1e-30)
    lv = np.array(lv)
    return 10.0 * np.log10(lv / max(lv[1], 1e-30) + 1e-30)   # band 1 (40-80) = 0


def frame_rms_db(x, ms=50.0):
    h = int(round(ms * 1e-3 * SR))
    fr = x[:len(x) // h * h].reshape(-1, h)
    r = np.sqrt((fr ** 2).mean(axis=1) + 1e-12)
    return 20.0 * np.log10(r + 1e-12)


# De-click fade at both ends of the delivered file.  Not a musical fade -- the
# piece starts on a drone and ends on one -- but a boundary one: without it the
# first sample is at full amplitude (measured 0.076 on an earlier render), and
# anything that starts or stops a buffer at a non-zero sample produces a step
# discontinuity, which is a click.  The reference gets away with starting on a
# hard edge only because it opens with 2 s of EXACT digital silence (-160 dBFS),
# which is a property of how it was ripped, not of the composition.  20 ms is
# long enough to be inaudible as a fade and short enough to cost nothing.
EDGE_FADE_MS = 20.0


# Saturation drive.  The knee scales with the ceiling below; this is the one
# number that sets how hard the quiet material is pushed (the small-signal gain
# of dsp.soft_clip is drive/tanh(drive), independent of the ceiling).
SOFT_DRIVE = 1.15

# Headroom the PRE-GAIN stages are allowed to use, dBFS.  This is the knob the
# crest factor lives on, and the reason it exists is a sign error in the old
# layering: soft_clip's asymptote sat at +1.74 dBFS and the EQ loop's limiter
# at -1.0, while the loudness stage afterwards applies a NEGATIVE gain (it is
# -4 dB here).  So every transient was being flattened 4 dB ABOVE where it
# needed to be, and then the whole piece was turned down -- which is exactly
# where dynamic range goes.  Measured: the body's crest collapsed from 15.12 dB
# in the raw mix to 7.90 dB delivered, against the reference's 12.63 dB, i.e.
# the piece was shipping ~5 dB denser than the thing it is matched to.
#
# The final limiter (ceiling -1.0 dBFS, after the gain) is the only stage that
# has to hold the ceiling; everything before it is character and shaping, so it
# should not be the binding constraint.  Kept BELOW the raw mix peak on purpose
# -- the saturation is still doing its job on the loudest hits; it just is not
# re-drawing the top of every one of them.
#
# NOT free: the delivered peak rises as this rises, and the codecs overshoot it
# (measured +0.91 dB on the mp3, +1.40 on the ogg).  PEAK_MAX_DB in
# check_song.py is -0.50 dBFS, so the in-memory peak cannot be pushed past about
# -2.0 without the ogg failing its own headroom check.
PRE_CEIL_DB = 4.0


def master(L, R, iters=3, cap=(-12.0, 6.0), pre_ceiling_db=PRE_CEIL_DB):
    """Close the loop on the spectrum: measure, correct, re-measure.

    Order matters and the first version had it backwards.  It ran the EQ loop
    to convergence and THEN compressed, soft-clipped and limited -- three
    non-linear, level-dependent stages that re-shape the spectrum after the
    loop has declared victory.  The loop could not converge because its work
    was being undone behind it (the log showed it pinned at +2.7 dB for three
    straight passes); what it was really reporting was the gap between the
    spectrum and the spectrum-after-the-dynamics.  Now the dynamics run first
    and the loop closes on the finished signal, so the number it prints is the
    number that ships.

    The contour is renormalised to preserve RMS after each pass, so correcting
    the shape cannot quietly walk the loudness target, and the correction is
    capped -- a +20 dB air boost amplifies the noise floor and reads as a fix.
    A band that needs more than the cap is content I failed to write, not
    something EQ should paper over, so the cap is printed."""
    log = []
    # Glue, not levelling.  The previous -20 dB / 2.5:1 sat BELOW the body's own
    # detector level (a 50 ms frame RMS near -13 puts the 150 ms mean of |x| near
    # -15 dB), so every loud section was compressed by ~4 dB while the quiet
    # breakdown was untouched -- and that difference IS dynamic range being eaten.
    # Raising the threshold above the body leaves the arc alone and squeezes only
    # the transients that actually poke over it.  DYNAMICS COME FROM THE
    # ARRANGEMENT (LEVELS) AND THE MASTER ONLY GLUES THEM; a compressor setting
    # the piece's loudness shape would be a second writer of a value LEVELS owns.
    # -9.5, not -13.0.  The body's 50 ms frame RMS lands near -13.4, and the
    # detector is a 150 ms mean of |x| which reads roughly 2 dB below that, so
    # -13.0 was still sitting UNDER the body and shaving it -- measured: the
    # delivered p95 sat 2.29 dB above the median against the reference's 3.51,
    # i.e. the loud end was the whole of the arc deficit.  A glue compressor
    # that touches the body's steady state is a second writer of the shape
    # LEVELS owns.  Five dB of headroom above it is honest: the finished peak is
    # -6.08 dBFS, so nothing here is being asked to hold the ceiling.
    L = dsp.compress(L, SR, thresh_db=-9.5, ratio=1.6, win_ms=150.0)
    R = dsp.compress(R, SR, thresh_db=-9.5, ratio=1.6, win_ms=150.0)
    # soft_clip's asymptote is ceiling/tanh(drive); set the ceiling so the
    # asymptote lands on pre_ceiling_db rather than on full scale.
    sc_ceil = 10.0 ** (pre_ceiling_db / 20.0) * float(np.tanh(SOFT_DRIVE))
    L = dsp.soft_clip(L, drive=SOFT_DRIVE, ceiling=sc_ceil)
    R = dsp.soft_clip(R, drive=SOFT_DRIVE, ceiling=sc_ceil)

    centres = [np.sqrt(a * b) for a, b in zip(OCT_EDGES[:-1], OCT_EDGES[1:])]
    for it in range(iters):
        M = (L + R) * 0.5
        prof = octave_profile(M)
        corr = np.clip(TARGET_DB - prof, cap[0], cap[1])
        log.append("  eq pass %d: pre %+6.2f dB mean rms, correction %s"
                   % (it + 1, dsp.rms_db(M),
                      " ".join("%+.1f" % c for c in corr)))
        # np.interp clamps outside the point range, so below the lowest band
        # centre and above the highest the contour holds its end value.
        pts = list(zip(centres, corr))
        # Each channel is renormalised back to its OWN pre-correction RMS.
        # Correcting shape must not move level: the loudness match below owns
        # level, and if both stages move it neither number can be traced to a
        # cause.  Per-channel rather than per-mono keeps the L/R balance
        # untouched too, which matters because the width is also being tuned.
        rL, rR = dsp.rms_db(L), dsp.rms_db(R)
        L2 = dsp.contour_db(L, SR, pts)
        R2 = dsp.contour_db(R, SR, pts)
        L = L2 * 10.0 ** ((rL - dsp.rms_db(L2)) / 20.0)
        R = R2 * 10.0 ** ((rR - dsp.rms_db(R2)) / 20.0)
        L, R = dsp.limiter_stereo(L, R, SR, ceiling_db=pre_ceiling_db)

    resid = TARGET_DB - octave_profile((L + R) * 0.5)
    log.append("  eq residual (after limiter): worst %+5.2f dB in %d-%d Hz"
               % (float(np.abs(resid).max()),
                  OCT_EDGES[int(np.argmax(np.abs(resid)))],
                  OCT_EDGES[int(np.argmax(np.abs(resid))) + 1]))

    cur = float(frame_rms_db((L + R) * 0.5).mean())
    # +/-12 dB, not the old +/-6.  The clamp is a runaway guard, not a second
    # target: at 6 it BOUND on the first arc render and reported -15.68 when it
    # had been asked for -16.41, i.e. the loudness stage quietly stopped
    # reaching its own number and nothing said so.  A guard that binds on
    # ordinary material is a target pretending to be a guard.
    g = max(-12.0, min(12.0, TARGET_RMS - cur))
    L = L * (10 ** (g / 20.0))
    R = R * (10 ** (g / 20.0))
    log.append("  loudness: measured %+6.2f dBFS mean RMS, applied %+5.2f dB"
               % (cur, g))

    L, R = dsp.limiter_stereo(L, R, SR, ceiling_db=-1.0)
    log.append("  after limiter: peak %.4f (%.2f dBFS), mean RMS %+6.2f dBFS"
               % (max(np.abs(L).max(), np.abs(R).max()),
                  20 * np.log10(max(np.abs(L).max(), np.abs(R).max()) + 1e-12),
                  float(frame_rms_db((L + R) * 0.5).mean())))

    # De-click the boundaries.  Last, because the limiter is non-linear and a
    # fade applied before it would be re-shaped by it.
    h = int(round(EDGE_FADE_MS * 1e-3 * SR))
    ramp = np.linspace(0.0, 1.0, h)
    for x in (L, R):
        x[:h] *= ramp
        x[-h:] *= ramp[::-1]
    log.append("  edge fade: %.0f ms each end (first sample %.6f)"
               % (EDGE_FADE_MS, float(L[0])))
    return L, R, log


def measure(L, R):
    M = (L + R) * 0.5
    mid = M
    side = (L - R) * 0.5
    e_m = float((mid ** 2).mean())
    e_s = float((side ** 2).mean())
    return dict(
        dur=len(L) / SR,
        peak=float(max(np.abs(L).max(), np.abs(R).max())),
        rms=float(frame_rms_db(M).mean()),
        side_mid=e_s / (e_m + 1e-12),
        corr=float(np.corrcoef(L, R)[0, 1]),
        profile=octave_profile(M),
    )


# ============================== output ==============================

def write_wav(path, L, R):
    x = np.clip(np.stack([L, R], axis=1), -1.0, 1.0)
    pcm = (x * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def encode(wav_path, out_dir):
    made = []
    for ext, args in (("ogg", ["-c:a", "libvorbis", "-q:a", "6"]),
                      ("mp3", ["-c:a", "libmp3lame", "-b:a", "192k"])):
        out = os.path.join(out_dir, "%s.%s" % (NAME, ext))
        r = subprocess.run([FFMPEG, "-y", "-v", "error", "-i", wav_path] + args + [out],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            raise RuntimeError("ffmpeg %s failed: %s"
                               % (ext, r.stderr.decode("utf-8", "replace")))
        made.append(out)
    return made


STEMS = os.path.join(HERE, "out", "stems.npz")


def cache_stems(stems):
    os.makedirs(os.path.dirname(STEMS), exist_ok=True)
    np.savez(STEMS, **{k: v.astype(np.float32) for k, v in stems.items()})
    return STEMS


def load_stems():
    """Cached CORE stems, with the air bed recomputed from the current constants.

    The cache exists to skip the six-minute core render, and the bed is the one
    layer that is cheap to rebuild and expensive to have stale.  Caching it too
    would pin whatever gate depth the cache was built at, so a sweep over depth
    would report the SAME bed at every point and look like a null result -- the
    kind of failure that reads as "the knob does nothing" rather than as an
    error.  Everything else in the file is a pure function of the section table,
    which is not being tuned."""
    z = np.load(STEMS)
    stems = {k: z[k].astype(np.float64) for k in z.files}
    # A cache from before the lead was split out has no leadD/leadS, and the
    # failure would otherwise be an opaque KeyError deep inside assemble -- or,
    # worse, if it were silently tolerated, a track with no melody in it that
    # renders and masters perfectly.  Say what is wrong and how to fix it.
    if "leadD" not in stems:
        raise SystemExit(
            "the cache at %s predates the lead/level split (no leadD key).\n"
            "Re-render it: python make_song.py --stems" % STEMS)
    a1 = air_bed(seed=77)
    a2 = air_bed(seed=78)
    return dict(stems, airC=0.5 * (a1 + a2), airD=0.5 * (a1 - a2))


def side_mid(L, R):
    m = float((((L + R) * 0.5) ** 2).mean())
    s = float((((L - R) * 0.5) ** 2).mean())
    return s / (m + 1e-12), float(np.corrcoef(L, R)[0, 1])


def probe(stems):
    """Where the width actually comes from, term by term.

    Tuning the width by re-listening is not available to me and tuning it by
    reading the final number only says which way to turn the screw, not which
    screw.  So each contributor is measured on its own."""
    print("== profile, dry mono core (no air, no EQ, no dynamics) ==")
    mp = octave_profile(with_lead(stems)["mono"])
    for i, (a, b) in enumerate(zip(OCT_EDGES[:-1], OCT_EDGES[1:])):
        print("    %5d-%-5d  %+6.1f  target %+6.1f  delta %+5.1f"
              % (a, b, mp[i], TARGET_DB[i], mp[i] - TARGET_DB[i]))

    L, R = assemble(stems)
    print("")
    print("== profile, assembled mix (air in, no EQ, no dynamics) ==")
    ap = octave_profile((L + R) * 0.5)
    for i, (a, b) in enumerate(zip(OCT_EDGES[:-1], OCT_EDGES[1:])):
        print("    %5d-%-5d  %+6.1f  target %+6.1f  delta %+5.1f"
              % (a, b, ap[i], TARGET_DB[i], ap[i] - TARGET_DB[i]))
    print("  assembled side/mid %.3f  corr %+.3f  rms %+.1f dB"
          % (side_mid(L, R)[0], np.corrcoef(L, R)[0, 1], dsp.rms_db((L + R) * 0.5)))

    print("")
    print("== width budget: each stereo term measured alone ==")
    r = assemble(stems, ret_diff_ir=True)
    core = r["mono"]
    terms = [("core   (dry, mono)", core, core),
             ("reverb (wc +- k*wd)", r["wl"], r["wr"]),
             ("delay  (pingpong)", r["dl"], r["dr"]),
             ("pad    (chorus)", r["pl"], r["pr"]),
             ("air    (bed)", r["al"], r["ar"])]
    for name, a, b in terms:
        sm, c = side_mid(a, b)
        print("  %-22s side/mid %.3f  corr %+.3f  rms %+6.1f dB"
              % (name, sm, c, dsp.rms_db(a)))
    print("")
    print("  target                 side/mid %.3f  corr %+.3f"
          % (TARGET_SIDE_MID, TARGET_CORR))
    return 0


def main(argv):
    if "--stems" in argv:
        print("== rendering stems: %d bars at %.2f bpm = %.2f s =="
              % (N_BARS, BPM, N_BARS * BAR))
        stems = render_stems()
        print("  cached %s (%d bytes)" % (cache_stems(stems),
                                          os.path.getsize(STEMS)))
        return 0

    if "--probe" in argv:
        return probe(load_stems() if os.path.exists(STEMS) else render_stems())

    if "--reuse" in argv:
        if not os.path.exists(STEMS):
            print("no cache at %s -- run --stems first" % STEMS)
            return 2
        stems = load_stems()
        print("== assembling from cached stems ==")
        L, R = assemble(stems)
    else:
        print("== rendering %d bars at %.2f bpm = %.2f s =="
              % (N_BARS, BPM, N_BARS * BAR))
        stems = render_stems()
        cache_stems(stems)
        L, R = assemble(stems)

    print("  raw mix: peak %.3f  rms %+.2f dB  side/mid %.3f"
          % (max(np.abs(L).max(), np.abs(R).max()), dsp.rms_db((L + R) * 0.5),
             side_mid(L, R)[0]))
    L, R, log = master(L, R)
    for line in log:
        print(line)

    os.makedirs(ASSETS, exist_ok=True)
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    wav_path = os.path.join(out_dir, NAME + ".wav")
    write_wav(wav_path, L, R)
    made = encode(wav_path, ASSETS)

    m = measure(L, R)
    print("")
    print("== final ==")
    print("  duration  %.3f s (%.1f s per bar x %d bars + %.1f s tail)"
          % (m["dur"], BAR, N_BARS, TAIL))
    print("  peak      %.4f (%.2f dBFS)" % (m["peak"], 20 * np.log10(m["peak"] + 1e-12)))
    print("  rms       %+.2f dBFS mean over 50 ms frames (target %+.2f)"
          % (m["rms"], TARGET_RMS))
    print("  side/mid  %.3f (target %.3f)   L/R corr %+.3f (target %+.3f)"
          % (m["side_mid"], TARGET_SIDE_MID, m["corr"], TARGET_CORR))
    print("  octave profile (dB re 40-80 Hz) vs target:")
    for i, (a, b) in enumerate(zip(OCT_EDGES[:-1], OCT_EDGES[1:])):
        print("    %5d-%-5d  %+6.1f  target %+6.1f  delta %+5.1f"
              % (a, b, m["profile"][i], TARGET_DB[i], m["profile"][i] - TARGET_DB[i]))
    print("  duration target %.2f vs %.2f" % (263.90, m["dur"]))
    print("")
    for p in made:
        print("  wrote %s (%d bytes)" % (p, os.path.getsize(p)))
    print("  wrote %s (%d bytes) [intermediate, not delivered]"
          % (wav_path, os.path.getsize(wav_path)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except BaseException:
        import traceback
        traceback.print_exc()
        sys.exit(1)
