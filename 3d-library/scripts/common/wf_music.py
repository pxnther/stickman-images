"""Generic What-If music bed: sections = list of (t0, t1, mood); silences = list of (t0, t1). Writes music.wav for /tmp/gv/<vid>."""
import numpy as np, json, sys
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
SR = 48000
def lp(x, c, o=2): return sosfilt(butter(o, c, 'low', fs=SR, output='sos'), x)
MOODS = {
 'curious': dict(chords=[(130.8, 196, 261.6, 329.6), (110, 164.8, 220, 261.6), (87.3, 130.8, 174.6, 220), (98, 146.8, 196, 246.9)], pad=0.12, kick=0.14, pl=0.07, mel=[523.3, 659.3, 784, 659.3, 587.3, 698.5, 880, 698.5], pd=0.5),
 'dark': dict(chords=[(73.4, 110, 146.8, 174.6), (65.4, 98, 130.8, 155.6), (58.3, 87.3, 116.5, 146.8), (65.4, 98, 130.8, 155.6)], pad=0.17, kick=0.24, pl=0.035, mel=[880, 784, 659.3, 587.3], pd=1.5),
 'deep': dict(chords=[(41.2, 61.7, 82.4, 98), (36.7, 55, 73.4, 87.3), (32.7, 49, 65.4, 82.4), (36.7, 55, 73.4, 92.5)], pad=0.2, kick=0.28, pl=0.03, mel=[329.6, 293.7, 246.9, 220], pd=2.0),
 'airy': dict(chords=[(110, 164.8, 220, 277.2), (98, 146.8, 196, 246.9)], pad=0.11, kick=0.0, pl=0.05, mel=[659.3, 587.3, 523.3, 493.9], pd=2.0),
 'space': dict(chords=[(55, 82.4, 110, 164.8), (49, 73.4, 98, 146.8), (43.7, 65.4, 87.3, 130.8)], pad=0.16, kick=0.0, pl=0.04, mel=[1318.5, 987.8, 1174.7, 880], pd=2.5),
}
def make(dur, sections, silences, bpm, out):
    N = int(SR * dur); mu = np.zeros(N); beat = 60 / bpm
    def add(sig, t, g=1.0):
        i = int(t * SR); n = min(len(sig), N - i)
        if n > 0 and i >= 0: mu[i:i + n] += sig[:n] * g
    def pad(freqs, a, b, g, fi=0.6, fo=0.5, cut=1500):
        n = int((b - a) * SR); tt = np.arange(n) / SR; s = np.zeros(n)
        for f in freqs:
            for det in (-0.8, 0.8): s += np.sin(2 * np.pi * (f + det) * tt) * 0.3
        e = np.clip(tt / fi, 0, 1) * np.clip((b - a - tt) / fo, 0, 1); add(lp(s, cut) * e, a, g)
    def kick(t, g):
        n = int(0.25 * SR); tt = np.arange(n) / SR
        add(np.sin(2 * np.pi * (50 + 60 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.12), t, g)
    def pluck(f, t, g, dec=0.22):
        n = int(0.8 * SR); tt = np.arange(n) / SR
        add((np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt / dec), t, g)
    for (a, b, m) in sections:
        M = MOODS[m]; x = a; ci = 0
        while x < b - 0.05:
            pad(M['chords'][ci % len(M['chords'])], x, min(x + 4 * beat, b), M['pad'], fi=0.05 if x == 0 else 0.5); x += 4 * beat; ci += 1
        if M['kick']:
            k = a
            while k < b - 0.2: kick(k, M['kick']); k += beat
        k = a + 0.1; i = 0
        while k < b - 0.2: pluck(M['mel'][i % len(M['mel'])], k, M['pl'], 0.25 if M['pd'] < 1 else 0.5); k += beat * M['pd']; i += 1
    for (a, b) in silences: mu[int(a * SR):int(b * SR)] *= 0.0
    mu = mu / np.max(np.abs(mu)) * 0.8
    wavfile.write(out, SR, (np.stack([mu, mu], 1) * 32767).astype(np.int16))
