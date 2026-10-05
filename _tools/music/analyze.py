"""Measure a piece of audio well enough to compose against it.

Why this exists: I cannot hear.  So the only way to write "in the style of X"
is to turn X into numbers -- tempo, key, section boundaries, band balance,
dynamic shape, stereo width -- and then compose to those numbers.  Every
number this prints is a measurement of the file on disk; none of it is a
genre label typed in from memory.

Usage:  python _tools/music/analyze.py <file> [--sr 44100]
Output: stdout (ASCII only -- the console here is GBK, see CLAUDE.md) and
        a .report.txt beside the input.

The default sample rate is 44100, the rate the piece was composed at, and the
reason is a measurement trap this tool fell into itself.  Asking ffmpeg for
22050 puts swresample's 22 kHz low-pass in FRONT of the measurement, so the
10240-20000 band is really 10240-11025 and reads about 10 dB darker than the
file is -- a ruler artifact that looks exactly like a dark mix.  Measured on
the same file: the top band is -26.9 dB at 44100 and -36.8 dB at 22050.  --sr
is still there for a fast look, but any number it gives above 10 kHz is about
the resampler and not about the audio.

Requires ffmpeg on PATH (D:\\Bot\\ffmpeg\\bin here) and numpy.
"""

import os
import subprocess
import sys

import numpy as np

FFMPEG = os.environ.get("FFMPEG", r"D:\Bot\ffmpeg\bin\ffmpeg")
FFPROBE = os.environ.get("FFPROBE", r"D:\Bot\ffmpeg\bin\ffprobe")


def _pcm(path, sr, channels):
    """Raw float32 PCM at the asked-for channel count, straight from ffmpeg."""
    cmd = [FFMPEG, "-v", "error", "-i", path,
           "-f", "f32le", "-ac", str(channels), "-ar", str(sr), "-"]
    raw = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if raw.returncode != 0:
        # The console codec is GBK and ffmpeg's stderr is UTF-8; decode by hand
        # rather than letting subprocess do it (CLAUDE.md, console codec).
        raise RuntimeError("ffmpeg failed: " + raw.stderr.decode("utf-8", "replace"))
    return np.frombuffer(raw.stdout, dtype="<f4").astype(np.float64)


def _src_channels(path):
    """Channel count of the first audio stream; 2 if ffprobe cannot say."""
    cmd = [FFPROBE, "-v", "error", "-select_streams", "a:0",
           "-show_entries", "stream=channels", "-of", "default=nw=1:nk=1", path]
    out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        return int(out.stdout.decode("utf-8", "replace").strip().split()[0])
    except (ValueError, IndexError):
        return 2


def decode(path, sr, channels=1):
    """Decode to float32 PCM in [-1,1] via ffmpeg.  Reads any format ffmpeg can.

    Mono is the plain channel MEAN, computed here rather than by ffmpeg.  Asking
    ffmpeg for `-ac 1` does NOT give (L+R)/2: swresample's stereo->mono matrix
    carries a 1/sqrt(2) gain, so its mono comes out 3.01 dB hotter than the mean
    and its peaks saturate.  Measured on the delivered track -- manual mean peak
    0.7068 / rms 0.2119 against ffmpeg mono 0.9996 / 0.2996, a ratio of exactly
    1.414213.  The tell is structural: a mean can never peak above the louder
    channel, and R peaks at 0.7369, yet ffmpeg's mono reported 0.9996.

    The gain is on the MATRIX, not on the mono: asking for 2 channels from a
    mono source applies the same 1/sqrt(2) in reverse (measured 0.7068 -> 0.4998),
    so any requested count that differs from the source's carries a hidden gain.
    Hence the downmix decodes at the source's OWN count -- where the matrix is
    the identity -- and averages here.  The multi-channel path is unchanged.
    """
    if channels == 1:
        src = _src_channels(path)
        x = _pcm(path, sr, src)
        if src == 1:
            return x
        n = x.size // src
        return x[:n * src].reshape(-1, src).mean(axis=1)
    x = _pcm(path, sr, channels)
    n = x.size // channels
    return x[:n * channels].reshape(-1, channels).T


def probe(path):
    cmd = [FFPROBE, "-v", "error", "-show_entries",
           "format=duration,bit_rate:stream=codec_name,sample_rate,channels",
           "-of", "default=nw=1", path]
    out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out.stdout.decode("utf-8", "replace").strip().replace("\n", "  ")


def stft(x, n=2048, hop=512):
    """Magnitude spectrogram.  Hann window; the frame count is what it is --
    a couple of dropped edge frames move nothing below by more than the
    rounding of its own print format."""
    if len(x) < n:
        x = np.pad(x, (0, n - len(x)))
    frames = 1 + (len(x) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(frames)[:, None]
    S = np.fft.rfft(x[idx] * np.hanning(n), axis=1)
    return np.abs(S).T  # (bins, frames)


def hz_to_pc(f):
    """Nearest pitch class of each frequency; -1 outside the voiced range."""
    pc = np.full(f.shape, -1)
    ok = (f > 32.0) & (f < 5000.0)
    midi = 12 * np.log2(np.maximum(f, 1e-9) / 440.0) + 69.0
    pc[ok] = np.mod(np.round(midi[ok]).astype(int), 12)
    return pc


def chroma(S, sr, n):
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    pc = hz_to_pc(freqs)
    C = np.zeros((12, S.shape[1]))
    for p in range(12):
        rows = pc == p
        if rows.any():
            C[p] = S[rows].sum(axis=0)
    return C


# Krumhansl-Schmuckler profiles.  These are a published template, not a
# measurement of the input -- the point is to correlate the measured chroma
# against them and print the residual so a bad fit is visible.
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                  2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                  2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def estimate_key(chroma_mean):
    v = chroma_mean - chroma_mean.mean()
    best = []
    for i in range(12):
        for prof, tag in ((MAJOR, "major"), (MINOR, "minor")):
            p = np.roll(prof, i)
            p = p - p.mean()
            r = float(np.dot(v, p) / (np.linalg.norm(v) * np.linalg.norm(p) + 1e-12))
            best.append((r, NAMES[i], tag))
    best.sort(key=lambda t: -t[0])
    return best


def tempo(flux, fps, lo=55.0, hi=200.0):
    """Autocorrelation of the onset envelope -> (bpm, strength) candidates.

    Strength is a normalised autocorrelation: 1.0 is a metronome, 0.2 is a
    weak pulse.  Near-duplicates (a peak at 128 also scores at 64 and 256)
    are collapsed to one entry each."""
    f = flux - flux.mean()
    ac = np.correlate(f, f, mode="full")[len(f) - 1:]
    if ac[0] <= 0:
        return []
    ac = ac / ac[0]
    out = []
    for bpm in np.arange(lo, hi, 0.25):
        lag = 60.0 * fps / bpm
        i0 = int(np.floor(lag))
        if i0 + 1 >= len(ac):
            continue
        frac = lag - i0
        val = ac[i0] * (1 - frac) + ac[i0 + 1] * frac
        out.append((float(val), float(bpm)))
    out.sort(key=lambda t: -t[0])
    picked = []
    for val, bpm in out:
        if all(abs(bpm - b) > 6.0 for _, b in picked):
            picked.append((val, bpm))
        if len(picked) == 5:
            break
    return picked


def band_energy(S, sr, n):
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    bands = [("sub 20-60", 20, 60), ("low 60-250", 60, 250),
             ("mid 250-2k", 250, 2000), ("hi 2k-8k", 2000, 8000),
             ("air 8k+", 8000, sr / 2)]
    tot = float((S ** 2).sum()) + 1e-12
    return [(name, float(((S[(freqs >= a) & (freqs < b)] ** 2).sum()) / tot))
            for name, a, b in bands]


def smooth(x, k):
    """Moving average.  A raw frame-level threshold flickers on dense music
    and drops most of the track into the 'too short' bin -- two seconds of
    smoothing is what makes the crossing mean 'the arrangement changed'."""
    if k < 2 or len(x) < k:
        return x
    c = np.cumsum(np.insert(x, 0, 0.0))
    out = (c[k:] - c[:-k]) / k
    pad = np.full(k - 1, out[0] if len(out) else 0.0)
    return np.concatenate([pad, out])


def sections(rms_db, hop_s, min_len_s=8.0, smooth_s=2.0, hyst_db=3.0):
    """Cut where *smoothed* loudness crosses the median, with hysteresis so a
    track that hovers near the level does not produce a hundred segments.

    Crude on purpose: a second opinion on where the parts are, not a claim
    about the composer's intent."""
    s = smooth(rms_db, max(1, int(round(smooth_s / hop_s))))
    med = float(np.median(s))
    hi, lo = med + hyst_db, med - hyst_db
    state = s[0] > med
    loud = np.zeros(len(s), dtype=bool)
    for i, v in enumerate(s):
        if state and v < lo:
            state = False
        elif (not state) and v > hi:
            state = True
        loud[i] = state
    edges = [0] + [i for i in range(1, len(loud)) if loud[i] != loud[i - 1]] + [len(loud)]
    segs = []
    for a, b in zip(edges[:-1], edges[1:]):
        if (b - a) * hop_s < min_len_s:
            continue
        segs.append((a * hop_s, b * hop_s,
                     "loud" if loud[a] else "quiet",
                     float(s[a:b].mean()), float(rms_db[a:b].max())))
    return segs


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    sr = 44100          # see the module docstring: 22050 low-passes the ruler
    if "--sr" in argv:
        sr = int(argv[argv.index("--sr") + 1])
    # The octave profile is only meaningful if the window resolves the bands.
    # At n=2048 / 44.1 kHz a bin is 21.5 Hz, so the 20-40 Hz band is ONE bin
    # sitting one bin under a 43 Hz sub line -- what it measures is mainlobe
    # leakage, not energy at 20-40 Hz.  n=8192 drops the bin to 5.4 Hz and
    # makes the band a band.  Default stays 2048 so every existing report
    # remains comparable; raise both n and hop together when comparing two
    # files, because the ruler is part of the measurement.
    nfft, hop = 2048, 512
    if "--nfft" in argv:
        nfft = int(argv[argv.index("--nfft") + 1])
        hop = nfft // 4

    L = []

    def say(s):
        print(s)
        L.append(s)

    say("== file ==")
    say("  path    %s" % path)
    say("  bytes   %d" % os.path.getsize(path))
    say("  probe   %s" % probe(path))

    x = decode(path, sr, 1)
    dur = len(x) / sr
    say("  decoded %.3f s @ %d Hz mono" % (dur, sr))

    n, hop = nfft, hop
    S = stft(x, n, hop)
    fps = sr / hop
    say("  stft    %d bins x %d frames (%.1f fps, %.1f Hz/bin)"
        % (S.shape[0], S.shape[1], fps, sr / n))

    hop_s = 0.05
    h = int(sr * hop_s)
    fr = x[:len(x) // h * h].reshape(-1, h)
    rms = np.sqrt((fr ** 2).mean(axis=1) + 1e-12)
    rms_db = 20 * np.log10(rms + 1e-12)
    say("")
    say("== loudness (50 ms frames) ==")
    say("  peak      %.3f (%.2f dBFS)"
        % (np.abs(x).max(), 20 * np.log10(np.abs(x).max() + 1e-12)))
    say("  rms       %.2f dBFS mean / %.2f dBFS median"
        % (rms_db.mean(), np.median(rms_db)))
    say("  range     %.2f dB (p5 %.2f .. p95 %.2f)"
        % (np.percentile(rms_db, 95) - np.percentile(rms_db, 5),
           np.percentile(rms_db, 5), np.percentile(rms_db, 95)))
    say("  active    %.1f%% of frames above -45 dBFS" % (100.0 * (rms_db > -45).mean()))

    say("")
    say("== spectrum ==")
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    P = (S ** 2).mean(axis=1)
    cen = float((P * freqs).sum() / (P.sum() + 1e-12))
    cs = np.cumsum(P) / (P.sum() + 1e-12)
    say("  centroid  %.0f Hz" % cen)
    say("  rolloff85 %.0f Hz" % freqs[np.searchsorted(cs, 0.85)])
    say("  flatness  %.4f (1.0 = white noise)"
        % float(np.exp(np.log(P + 1e-15).mean()) / (P.mean() + 1e-15)))
    for name, frac in band_energy(S, sr, n):
        say("  band %-11s %5.1f%%" % (name, 100 * frac))

    say("")
    say("== tempo ==")
    d = np.diff(S, axis=1)
    flux = np.concatenate([[0.0], np.maximum(d, 0).sum(axis=0)])
    cand = tempo(flux, fps)
    for val, bpm in cand:
        say("  %6.2f bpm  strength %.3f" % (bpm, val))
    if cand:
        say("  -> %.2f bpm is the strongest of these" % cand[0][1])

    say("")
    say("== key ==")
    C = chroma(S, sr, n)
    cm = C.mean(axis=1)
    cm = cm / (cm.sum() + 1e-12)
    say("  pitch-class histogram (% of chroma energy):")
    for i in range(12):
        say("    %-3s %5.1f%%  %s" % (NAMES[i], 100 * cm[i], "#" * int(60 * cm[i])))
    for r, root, tag in estimate_key(cm)[:4]:
        say("  %-3s %-5s  r=%+.3f" % (root, tag, r))

    say("")
    say("== structure (loudness crossings, >= 8 s) ==")
    for a, b, tag, mean, mx in sections(rms_db, hop_s):
        say("  %6.1f .. %6.1f s  %-5s  mean %6.2f dB  peak %6.2f dB"
            % (a, b, tag, mean, mx))

    say("")
    say("== arrangement timeline (10 s blocks; 3 bands as % of that block) ==")
    block = int(round(10.0 * fps))
    for i in range(0, S.shape[1], block):
        sl = S[:, i:i + block]
        if sl.shape[1] < 2:
            break
        fr = np.fft.rfftfreq(n, 1.0 / sr)
        e = float((sl ** 2).sum()) + 1e-12
        lo = float((sl[(fr < 250)] ** 2).sum()) / e
        md = float((sl[(fr >= 250) & (fr < 2000)] ** 2).sum()) / e
        hi = float((sl[(fr >= 2000)] ** 2).sum()) / e
        say("  %5.0f-%5.0f s  low %4.0f%%  mid %4.0f%%  hi %4.0f%%"
            % (i / fps, (i + sl.shape[1]) / fps, 100 * lo, 100 * md, 100 * hi))

    say("")
    say("== stereo ==")
    st = decode(path, 44100, 2)
    # st is (channels, time): average down the channel axis, not across time.
    # Getting this backwards makes mid a scalar and inflates side/mid to 1e6.
    mid = st.mean(axis=0)
    side = (st[0] - st[1]) / 2.0
    e_m = float((mid ** 2).mean())
    e_s = float((side ** 2).mean())
    corr = float(np.corrcoef(st[0], st[1])[0, 1])
    say("  channels  %d, %.2f s" % (st.shape[0], st.shape[1] / 44100.0))
    say("  side/mid  %.3f (0 = mono)" % (e_s / (e_m + 1e-12)))
    say("  L/R corr  %+.3f" % corr)

    say("")
    say("== spectrum profile (per octave band, dB re the loudest band) ==")
    edges = [20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10240, 20000]
    P = (S ** 2).mean(axis=1)
    lvl = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (freqs >= a) & (freqs < b)
        lvl.append((a, b, float(P[m].sum()) if m.any() else 1e-30))
    top = max(v for _, _, v in lvl)
    for a, b, v in lvl:
        db = 10 * np.log10(v / top + 1e-30)
        say("  %5d-%-5d Hz  %+6.1f dB  %s" % (a, b, db, "#" * int(max(0, 60 + db) / 2)))

    out = os.path.splitext(path)[0] + ".report.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\nwrote %s" % out)
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
