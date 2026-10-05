"""Small vectorised DSP kit for writing music without scipy or librosa.

Everything here is pure numpy.  Two rules shaped the design:

1.  No per-sample Python loops.  A 4:24 stereo track at 44.1 kHz is 11.7 M
    samples per channel; a one-pole IIR written as a for-loop takes seconds
    *per pass* and the composition needs dozens of passes.  So filters are
    spectral (multiply the FFT) where the response is static, and block-wise
    with a crossfade where it moves.  Envelope followers are boxcar smoothers
    built on cumsum, which is exact and fully vectorised.

2.  Zero-phase is the default.  A static `lowpass` here means "multiply by
    |H(f)|", so the output is not delayed relative to the input.  That makes
    layering predictable -- a hit placed at bar 52 lands at bar 52 -- at the
    cost of a little pre-ringing on sharp transients.  For pads, drones and
    bus shaping that trade is free; percussion is shaped in the time domain
    by its own envelope instead, so it never sees a zero-phase filter.
"""

import numpy as np

TAU = 2.0 * np.pi


# ============================== basic shape ==============================

def t_axis(dur, sr):
    """Time in seconds.  `endpoint=False` so that n = dur * sr exactly."""
    return np.arange(int(round(dur * sr))) / sr


def sine(freq, dur, sr, phase=0.0):
    """Sine at a constant frequency.  For sweeping pitch use `chirp`."""
    return np.sin(TAU * freq * t_axis(dur, sr) + phase)


def chirp(freq, dur, sr, phase=0.0):
    """Sine whose frequency is an array (or a callable of t).

    Phase is the integral of frequency -- done by cumsum rather than by
    writing sin(2*pi*f*t), because f*t is only correct when f is constant,
    and a pitch envelope that is *actually* exponential is the whole point
    of a kick drum.
    """
    t = t_axis(dur, sr)
    f = freq(t) if callable(freq) else np.asarray(freq, dtype=float)
    if f.ndim == 0:
        f = np.full(t.shape, float(f))
    ph = TAU * np.cumsum(f) / sr
    return np.sin(ph + phase)


def noise(dur, sr, seed=0):
    rng = np.random.default_rng(seed)
    return rng.standard_normal(int(round(dur * sr)))


def env(dur, sr, attack=0.01, decay=None, curve=2.0, sustain=0.0, release=None,
        hold=None):
    """Attack / decay envelope.  Returns values in [0,1], same length as dur.

    attack, decay, hold, release are seconds.  `curve` shapes the decay:
    higher is a snappier fall.  A tail that is not consumed by release is
    filled with `sustain` (default 0), so a percussive sound is just
    env(0.3, sr, attack=0.002, decay=0.28).
    """
    n = int(round(dur * sr))
    a = max(1, int(round(attack * sr)))
    if decay is None:
        decay = max(0.0, dur - attack)
    d = max(1, int(round(decay * sr)))
    h = int(round((hold or 0.0) * sr))
    e = np.zeros(n)

    def put(start, length, values):
        if length <= 0:
            return
        end = min(n, start + length)
        if end <= start:
            return
        e[start:end] = values[:end - start]

    if a == 1:
        e[0] = 1.0
    else:
        put(0, a, np.linspace(0.0, 1.0, a) ** 0.35)  # slightly convex attack
    put(a, h, np.ones(h))
    dl = min(d, n - a - h)
    if dl > 0:
        # Decay runs 1.0 -> sustain, not 1.0 -> 0.  Falling to zero and then
        # jumping back up to `sustain` is a step discontinuity in the middle
        # of a pad, which is a click, not a decay.
        put(a + h, dl, np.linspace(1.0, sustain, dl) ** curve)
    r = None
    if release is not None:
        r = max(1, int(round(release * sr)))
    if r:
        put(a + h + max(0, dl), r, np.linspace(sustain, 0.0, r) ** curve)
    else:
        tail = a + h + max(0, dl)
        if sustain and tail < n:
            e[tail:] = sustain
    return e


def fade(x, sr, in_s=0.0, out_s=0.0):
    """Linear fades at both ends.  Applied in place-safe fashion (returns a view-safe copy)."""
    y = x.copy()
    a = int(round(in_s * sr))
    b = int(round(out_s * sr))
    if a > 0:
        y[:a] *= np.linspace(0.0, 1.0, min(a, len(y)))
    if b > 0:
        n = min(b, len(y))
        y[len(y) - n:] *= np.linspace(1.0, 0.0, n)
    return y


# ============================== spectra ==============================

def _rff(freqs, sr, n):
    return np.fft.rfftfreq(n, 1.0 / sr)


def _apply(x, gain_curve):
    """Multiply the signal's spectrum by a real gain curve.  Zero-phase."""
    n = len(x)
    X = np.fft.rfft(x)
    return np.fft.irfft(X * gain_curve, n=n)


def lowpass(x, sr, fc, order=2):
    fr = _rff(None, sr, len(x))
    return _apply(x, 1.0 / np.sqrt(1.0 + (fr / max(fc, 1e-6)) ** (2 * order)))


def highpass(x, sr, fc, order=2):
    fr = _rff(None, sr, len(x))
    r = (fr / max(fc, 1e-6))
    return _apply(x, r ** order / np.sqrt(1.0 + r ** (2 * order)))


def bandpass(x, sr, f1, f2, order=2):
    return lowpass(highpass(x, sr, f1, order), sr, f2, order)


def peak(x, sr, fc, q, gain_db):
    """One resonant bell.  Used to put a bump exactly where a measurement
    said the energy should be (40-80 Hz for this project) instead of hoping
    a broad tilt lands there."""
    fr = _rff(None, sr, len(x))
    bw = fc / max(q, 0.01)
    g = 1.0 + (10 ** (gain_db / 20.0) - 1.0) * np.exp(-0.5 * ((fr - fc) / bw) ** 2)
    return _apply(x, g)


def tilt(x, sr, anchor_hz, db_per_octave):
    """Straight spectral tilt about an anchor frequency.  This is how the
    -10 dB shelf from 320 Hz to 5 kHz in the reference gets reproduced."""
    fr = _rff(None, sr, len(x))
    with np.errstate(divide="ignore"):
        octs = np.log2(np.maximum(fr, 1e-6) / anchor_hz)
    g = 10 ** ((db_per_octave * octs) / 20.0)
    g[0] = g[1] if len(g) > 1 else 1.0
    return _apply(x, g)


def shelf_db(x, sr, f_lo, f_hi, db_lo, db_hi, smooth_oct=0.5):
    """Piecewise-linear spectral contour read at a handful of points, with
    cosine smoothing between them.  Convenient for saying "match this octave
    table" in one call."""
    fr = _rff(None, sr, len(x))
    pts = np.array([max(1.0, f_lo * 0.5), f_lo, f_hi, min(sr * 0.49, f_hi * 8)])
    vals = np.array([db_lo, db_lo, db_hi, db_hi], dtype=float)
    with np.errstate(divide="ignore"):
        lo = np.log2(np.maximum(fr, 1e-6))
    db = np.interp(lo, np.log2(pts), vals)
    return _apply(x, 10 ** (db / 20.0))


def contour_db(x, sr, pts):
    """Arbitrary spectral contour read off a list of (Hz, dB) points, with
    linear interpolation in log-frequency.  This is the tool the master chain
    uses to close the loop: measure the octave profile, subtract it from the
    target, and feed the difference straight in here."""
    fr = _rff(None, sr, len(x))
    f = np.array([max(float(p[0]), 1e-6) for p in pts], dtype=float)
    d = np.array([float(p[1]) for p in pts], dtype=float)
    db = np.interp(np.log2(np.maximum(fr, 1e-6)), np.log2(f), d)
    return _apply(x, 10 ** (db / 20.0))


def sweep_filter(x, sr, f_start, f_end, q=6.0, gain_db=0.0, block=2048, curve=1.0):
    """Resonant bandpass whose centre frequency moves with time.

    Per-sample IIR is out (see the module docstring), so this filters in
    blocks with a raised-cosine crossfade between neighbours: each 2048-sample
    block gets its own static response and the overlap hides the seams.
    """
    n = len(x)
    hop = block // 2
    out = np.zeros(n)
    wsum = np.zeros(n)
    win = np.hanning(block)
    i = 0
    idx = 0
    steps = int(np.ceil(n / hop)) + 1
    while i < n:
        frac = min(1.0, i / max(1, n - block))
        fc = f_start * (f_end / f_start) ** (frac ** curve)
        seg = x[i:i + block]
        if len(seg) < block:
            seg = np.pad(seg, (0, block - len(seg)))
        fr = _rff(None, sr, block)
        bw = fc / max(q, 0.01)
        g = np.exp(-0.5 * ((fr - fc) / bw) ** 2) * (10 ** (gain_db / 20.0))
        y = np.fft.irfft(np.fft.rfft(seg) * g, n=block)
        # The final block is shorter than `block`; slice both sides to the
        # region that actually exists, or win (2048) and the target (1092)
        # are not broadcastable.
        m = min(block, n - i)
        out[i:i + m] += y[:m] * win[:m]
        wsum[i:i + m] += win[:m]
        i += hop
        idx += 1
    return out / np.maximum(wsum, 1e-9)


# ============================== instruments ==============================

def additive(f0, dur, sr, partials, detune=0.0, seed=0):
    """Sum of sines.  `partials` is a list of (ratio, amplitude, decay_s).

    Additive rather than a naive saw/square on purpose: the harmonics stop
    where the list stops, so nothing aliases above Nyquist and no filter is
    needed to make it usable.  `detune` (Hz) splits each partial into two
    copies a hair apart, which is what makes a "chorus" instead of a buzz.
    """
    n = int(round(dur * sr))
    out = np.zeros(n)
    t = np.arange(n) / sr
    for ratio, amp, dec in partials:
        f = f0 * ratio
        if f >= sr * 0.45:
            continue
        e = np.exp(-t / max(dec, 1e-4)) if dec else np.ones(n)
        if detune:
            out += amp * e * np.sin(TAU * f * t)
            out += amp * e * np.sin(TAU * (f + detune) * t + 0.7)
            out += amp * e * np.sin(TAU * (f - detune) * t + 1.9)
            out /= 1.0
        else:
            out += amp * e * np.sin(TAU * f * t)
    return out


SAW = [(k, 1.0 / k, 0.0) for k in range(1, 25)]


def kick(dur, sr, f_hi=118.0, f_lo=43.65, tau=0.045, attack=0.002, decay=0.42,
         click=0.25):
    """Reactor-thump kick.  The pitch envelope is exponential, so the body
    lands on the tone centre (F1 = 43.65 Hz by default) -- the same note the
    drone pedals, which is why the low end does not fight itself."""
    t = t_axis(dur, sr)
    f = f_lo + (f_hi - f_lo) * np.exp(-t / tau)
    body = chirp(f, dur, sr) * env(dur, sr, attack=attack, decay=decay, curve=2.4)
    c = noise(dur, sr, seed=11) * env(dur, sr, attack=0.0004, decay=0.012, curve=3.0)
    return body + click * bandpass(c, sr, 900, 4200)


def metal_hit(dur, sr, f0=196.0, seed=7, bright=1.0):
    """Inharmonic partial set -> a clang that reads as struck steel rather
    than as a played note.  Ratios are deliberately non-integer."""
    ratios = [(1.00, 1.00), (1.71, 0.62), (2.41, 0.48), (3.13, 0.33),
              (4.62, 0.22), (5.87, 0.15), (7.31, 0.10)]
    parts = [(r, a, 0.30 / (1.0 + 2.2 * i)) for i, (r, a) in enumerate(ratios)]
    body = additive(f0, dur, sr, parts)
    n = noise(dur, sr, seed=seed)
    n = bandpass(n, sr, 1800 * bright, 7000 * bright)
    return body + 0.35 * n * env(dur, sr, attack=0.0005, decay=0.02, curve=2.5)


def steam(dur, sr, f_lo=500, f_hi=6000, seed=3):
    """Noise whose band opens upward as it decays -- a vent, not a cymbal."""
    n = noise(dur, sr, seed=seed)
    body = sweep_filter(n, sr, f_lo, f_hi, q=1.6, gain_db=0.0)
    return body * env(dur, sr, attack=0.02, decay=dur * 0.85, curve=1.6)


def tick(dur, sr, seed=5, lo=6000, hi=12000):
    n = noise(dur, sr, seed=seed)
    return bandpass(n, sr, lo, hi) * env(dur, sr, attack=0.0002, decay=0.018, curve=3.0)


def pluck(f, dur, sr, seed=0, bright=6):
    """Short additive tone with a fast, per-partial decay (higher partials die
    first) -- the standard way to get "plucked" out of sines."""
    parts = [(k, 1.0 / (k ** 1.2), 0.55 / (1.0 + 0.55 * k)) for k in range(1, bright + 1)]
    return additive(f, dur, sr, parts) * env(dur, sr, attack=0.003, decay=dur * 0.9, curve=2.0)


def pad_chord(freqs, dur, sr, detune_hz=0.9, attack=1.6, seed=0):
    """Detuned additive stack.  Each voice is a saw-limited stack plus two
    slightly-offset copies; the slow beating between them is what keeps a
    long chord from sounding like an organ."""
    out = np.zeros(int(round(dur * sr)))
    for i, f in enumerate(freqs):
        v = additive(f, dur, sr, [(k, 1.0 / (k ** 1.35), 0.0) for k in range(1, 10)],
                     detune=detune_hz * (1.0 + 0.13 * i), seed=seed + i)
        out += v
    out /= max(1, len(freqs))
    return out * env(dur, sr, attack=attack, decay=dur - attack, curve=1.2, sustain=0.75)


# ============================== time effects ==============================

def delay(x, sr, time_s, feedback=0.35, mix=0.3, pingpong=False):
    """Feedback delay written as successive taps, so cost is O(taps * n)
    instead of a sample loop.  0.9999 guards a runaway `feedback`."""
    n = len(x)
    taps = max(1, int(np.log(1e-4) / np.log(max(1e-4, min(0.9999, abs(feedback))))))
    d = int(round(time_s * sr))
    out = np.zeros(n)
    g = 1.0
    for k in range(taps):
        off = d * (k + 1)
        if off >= n:
            break
        out[off:] += g * x[:n - off]
        g *= feedback
    return (1.0 - mix) * x + mix * out


def comb_reverb(x, sr, rt60=2.6, predelay_ms=18.0, damp=5200.0, seed=1,
                tail_s=None):
    """Wet tail only -- the caller sets the level, as on a send bus.

    The IR is decaying noise, lowpass-damped, with an early-reflection
    cluster; two channels decorrelate for free when `seed` differs.
    Convolution is done in the frequency domain, so one 2.6 s IR over a 4.4
    min signal costs a couple of FFTs instead of 3e8 multiply-adds.

    The IR is normalised to unit ENERGY, and that choice is the point: it is
    what makes the return level track the input, so a quiet send produces a
    quiet tail.  An earlier version normalised by peak instead, which forces
    every return to exactly the same loudness whatever went into it -- a
    levelling bug that reads as a reverb right up until it is measured.
    """
    tail_s = tail_s or rt60 * 1.15
    m = int(round(tail_s * sr))
    rng = np.random.default_rng(seed)
    ir = rng.standard_normal(m) * np.exp(-np.arange(m) / (rt60 * sr / 6.907755))
    ir = lowpass(ir, sr, damp)
    for t_ms, g in ((11.0, 0.5), (19.0, 0.4), (29.0, 0.32), (43.0, 0.25)):
        i = int(round(t_ms * 1e-3 * sr))
        if i < m:
            ir[i] += g
    ir *= np.sqrt(1.0 / max(1e-9, (ir ** 2).sum()))

    pre = int(round(predelay_ms * 1e-3 * sr))
    n = len(x) + m
    Y = np.fft.irfft(np.fft.rfft(x, n=n) * np.fft.rfft(ir, n=n), n=n)
    wet = np.zeros(n + pre)
    wet[pre:] = Y
    return wet


def chorus(x, sr, depth_ms=7.0, rate_hz=0.23, voices=3, spread=1.0):
    """Fractional-delay chorus by linear interpolation of the whole buffer.
    Stereo spread is done by returning a list of slightly different pitches."""
    outs = []
    n = len(x)
    i = np.arange(n)
    for v in range(voices):
        r = rate_hz * (1.0 + 0.37 * v)
        d = depth_ms * 1e-3 * sr * (0.5 + 0.5 * np.sin(TAU * r * i / sr + v * 2.1))
        pos = i - d - (v * 13.0 * spread)
        pos = np.clip(pos, 0, n - 1)
        i0 = np.floor(pos).astype(np.int64)
        i1 = np.minimum(i0 + 1, n - 1)
        frac = pos - i0
        outs.append(x[i0] * (1 - frac) + x[i1] * frac)
    return outs


# ============================== dynamics / mix ==============================

def smooth(x, win):
    """Boxcar moving average via cumsum.  This is the vectorised stand-in for
    a one-pole envelope follower: exact, O(n), no Python loop."""
    win = max(1, int(win))
    if win < 2 or len(x) < win:
        return x.copy()
    c = np.concatenate([[0.0], np.cumsum(x)])
    out = (c[win:] - c[:-win]) / win
    pad = np.full(win - 1, out[0] if len(out) else 0.0)
    return np.concatenate([pad, out])[:len(x)]


def compress(x, sr, thresh_db=-18.0, ratio=3.0, win_ms=120.0):
    """Feed-forward bus compressor.  The detector is a boxcar over |x|, so it
    has no attack/release asymmetry -- acceptable for glue on a 4-minute bed,
    and honest about what it is: a leveller, not a character compressor."""
    a = np.abs(x)
    e = smooth(a, int(round(win_ms * 1e-3 * sr)))
    edb = 20 * np.log10(np.maximum(e, 1e-9))
    over = np.maximum(0.0, edb - thresh_db)
    gain_db = -over * (1.0 - 1.0 / max(1.0, ratio))
    return x * (10 ** (gain_db / 20.0))


def soft_clip(x, drive=1.0, ceiling=1.0):
    return ceiling * np.tanh(drive * x / max(ceiling, 1e-9)) / np.tanh(drive)


def _lim_gain(a, sr, ceiling_db, lookahead_ms, release_ms):
    """Shared gain law for `limiter` / `limiter_stereo`.  `a` is the detection
    signal: |x| for mono, max(|L|,|R|) for a stereo-linked pair."""
    ceil = 10 ** (ceiling_db / 20.0)
    L = max(1, int(round(lookahead_ms * 1e-3 * sr)))
    need = np.minimum(1.0, ceil / np.maximum(a, 1e-9))
    pad = (-len(need)) % L
    blocks = np.concatenate([need, np.full(pad, 1.0)]).reshape(-1, L)
    me = np.repeat(blocks.min(axis=1), L)[:len(need)]
    ahead = np.concatenate([me[L:], np.ones(L)])
    g = smooth(np.minimum(me, ahead), max(1, int(round(release_ms * 1e-3 * sr))))
    return np.minimum(g, need)


def limiter(x, sr, ceiling_db=-1.0, lookahead_ms=6.0, release_ms=40.0):
    """Peak limiter with an exact sample-peak ceiling.

    The gain the signal needs is `ceil/|x|` sample by sample.  Smoothing that
    with a boxcar is wrong -- a moving average *raises* the gain back up over
    a narrow notch, which is exactly where a 2 ms transient lives, so the
    first version of this let a kick through at +4.6 dB.  A limiter needs the
    *minimum* of the needed gain over the lookahead window, so: take the
    block-wise minimum and propagate it one block backward (that is "min over
    the next L samples"), ease the release with a boxcar, then clamp against
    the exact per-sample requirement so nothing can overshoot at all.

    Sample-peak only; the mp3 step afterwards will overshoot slightly
    regardless, which is why the default ceiling is -1 dBFS and not -0.1."""
    return x * _lim_gain(np.abs(x), sr, ceiling_db, lookahead_ms, release_ms)


def limiter_stereo(left, right, sr, ceiling_db=-1.0, lookahead_ms=6.0, release_ms=40.0):
    """Stereo-linked limiter: one gain from max(|L|,|R|).

    Limiting the channels independently lets a transient in one channel duck
    only that channel, which walks the stereo image sideways once per kick.
    Linking costs a little loudness and keeps the centre where it was."""
    g = _lim_gain(np.maximum(np.abs(left), np.abs(right)), sr,
                  ceiling_db, lookahead_ms, release_ms)
    return left * g, right * g


def normalize(x, peak_db=-1.0):
    p = np.max(np.abs(x)) + 1e-12
    return x * (10 ** (peak_db / 20.0) / p)


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def pan_mono(x, pan):
    """Equal-power pan.  pan in [-1, 1] -> (left, right)."""
    th = (np.clip(pan, -1.0, 1.0) + 1.0) * 0.25 * np.pi
    return x * np.cos(th), x * np.sin(th)
