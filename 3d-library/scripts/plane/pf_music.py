import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
SR = 48000; DUR = 51.96; N = int(SR * DUR)
def lp(x, c, o=2): return sosfilt(butter(o, c, 'low', fs=SR, output='sos'), x)
def add(buf, sig, t, g=1.0):
    i = int(t * SR); n = min(len(sig), len(buf) - i)
    if n > 0 and i >= 0: buf[i:i + n] += sig[:n] * g
mu = np.zeros(N); bpm = 100; beat = 60 / bpm
def pad(freqs, a, b, g=0.2, fi=1.0, fo=0.6, cut=1600):
    n = int((b - a) * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for f in freqs:
        for det in (-0.8, 0.8): s += np.sin(2 * np.pi * (f + det) * tt) * 0.3
    e = np.clip(tt / fi, 0, 1) * np.clip((b - a - tt) / fo, 0, 1); add(mu, lp(s, cut) * e, a, g)
def kick(t, g):
    n = int(0.25 * SR); tt = np.arange(n) / SR
    add(mu, np.sin(2 * np.pi * (50 + 60 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.12), t, g)
def pluck(f, t, g):
    n = int(0.8 * SR); tt = np.arange(n) / SR
    add(mu, (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt / 0.3), t, g)
T_OUT, T_WAKE, T_STOP, T_HOPE = 9.4, 13.1, 31.24, 32.44
tense = [(73.4, 110, 146.8, 174.6), (65.4, 98, 130.8, 155.6), (69.3, 103.8, 138.6, 164.8), (61.7, 92.5, 123.5, 146.8)]
x = 0; ci = 0
while x < T_OUT:
    pad(tense[ci % 4], x, min(x + 4 * beat, T_OUT), 0.16, fi=0.05 if x == 0 else 0.8); x += 4 * beat; ci += 1
k = 0.0
while k < T_OUT - 0.2: kick(k, 0.22); k += beat
pad((55, 82.4), T_OUT, T_WAKE, 0.05, fi=0.5, fo=0.3, cut=500)        # muffled while he is passed out
x = T_WAKE; ci = 0
while x < T_STOP:
    pad(tense[ci % 4], x, min(x + 4 * beat, T_STOP), 0.17, fi=0.2); x += 4 * beat; ci += 1
k = T_WAKE
while k < T_STOP - 0.2: kick(k, 0.26); k += beat / 2 if k > 27 else beat
hope = [(110, 138.6, 164.8, 220), (98, 123.5, 146.8, 196), (87.3, 110, 130.8, 174.6), (98, 123.5, 146.8, 196)]
x = T_HOPE; ci = 0
while x < DUR:
    pad(hope[ci % 4], x, min(x + 4 * beat, DUR), 0.15, fi=0.6 if ci == 0 else 0.3, fo=0.25); x += 4 * beat; ci += 1
arp = [659.3, 554.4, 440, 554.4, 587.3, 493.9, 392, 493.9]; k = T_HOPE + 0.5; i = 0
while k < DUR - 0.3: pluck(arp[i % 8], k, 0.06); k += beat / 2; i += 1
k = 42.0
while k < DUR - 0.2: kick(k, 0.18); k += beat
mu[int(T_STOP * SR):int(T_HOPE * SR)] *= 0.0
mu = mu / np.max(np.abs(mu)) * 0.8
wavfile.write('/tmp/gv/plane/music.wav', SR, (np.stack([mu, mu], 1) * 32767).astype(np.int16)); print('ok')
