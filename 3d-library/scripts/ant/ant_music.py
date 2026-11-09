import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
SR = 48000; DUR = 46.02; N = int(SR * DUR)
def lp(x, c, o=2): return sosfilt(butter(o, c, 'low', fs=SR, output='sos'), x)
def add(buf, sig, t, g=1.0):
    i = int(t * SR); n = min(len(sig), len(buf) - i)
    if n > 0 and i >= 0: buf[i:i + n] += sig[:n] * g
mu = np.zeros(N); bpm = 104; beat = 60 / bpm
def pad(freqs, a, b, g=0.2, fi=1.0, fo=0.6, cut=1600):
    n = int((b - a) * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for f in freqs:
        for det in (-0.8, 0.8): s += np.sin(2 * np.pi * (f + det) * tt) * 0.3
    e = np.clip(tt / fi, 0, 1) * np.clip((b - a - tt) / fo, 0, 1); add(mu, lp(s, cut) * e, a, g)
def kick(t, g):
    n = int(0.25 * SR); tt = np.arange(n) / SR
    add(mu, np.sin(2 * np.pi * (50 + 60 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.12), t, g)
def pluck(f, t, g, dec=0.22):
    n = int(0.7 * SR); tt = np.arange(n) / SR
    add(mu, (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) + 0.1 * np.sin(6 * np.pi * f * tt)) * np.exp(-tt / dec), t, g)
# 1) curious, light (tiny world): plucked pizzicato over soft pads, 0 - 14.3
T_RAIN, T_QUIET0, T_QUIET1, T_COLD, T_BACK = 14.28, 31.05, 32.7, 35.22, 41.76
light = [(130.8, 196, 261.6, 329.6), (110, 164.8, 220, 261.6), (87.3, 130.8, 174.6, 220), (98, 146.8, 196, 246.9)]
x = 0; ci = 0
while x < T_RAIN:
    pad(light[ci % 4], x, min(x + 4 * beat, T_RAIN), 0.12, fi=0.05 if x == 0 else 0.6); x += 4 * beat; ci += 1
mel = [523.3, 659.3, 784, 659.3, 587.3, 698.5, 880, 698.5, 523.3, 659.3, 784, 1046.5, 493.9, 587.3, 784, 587.3]
k = 0.0; i = 0
while k < T_RAIN - 0.2: pluck(mel[i % 16], k, 0.07); k += beat / 2; i += 1
k = beat * 4
while k < T_RAIN - 0.2: kick(k, 0.14); k += beat
# 2) rain: darker minor pads, steady pulse, 14.3 - 31.0
dark = [(73.4, 110, 146.8, 174.6), (65.4, 98, 130.8, 155.6), (58.3, 87.3, 116.5, 146.8), (65.4, 98, 130.8, 155.6)]
x = T_RAIN; ci = 0
while x < T_QUIET0:
    pad(dark[ci % 4], x, min(x + 4 * beat, T_QUIET0), 0.17, fi=0.3); x += 4 * beat; ci += 1
k = T_RAIN
while k < T_QUIET0 - 0.2: kick(k, 0.24); k += beat
drip = [880, 784, 659.3, 587.3]; k = T_RAIN + 0.3; i = 0
while k < T_QUIET0 - 0.3: pluck(drip[i % 4], k, 0.035, 0.12); k += beat * 1.5; i += 1
# 3) silence on 'Nobody hears you', then a thin high tone for the voice line
pad((1046.5, 1568), T_QUIET1, T_COLD, 0.035, fi=0.4, fo=0.3, cut=4000)
# 4) cold: sparse, airy, soft
cold = [(110, 164.8, 220, 277.2), (98, 146.8, 196, 246.9)]
x = T_COLD; ci = 0
while x < T_BACK:
    pad(cold[ci % 2], x, min(x + 4 * beat, T_BACK), 0.11, fi=0.8, fo=0.5, cut=1100); x += 4 * beat; ci += 1
bell = [659.3, 587.3, 523.3, 493.9]; k = T_COLD + 0.6; i = 0
while k < T_BACK - 0.3: pluck(bell[i % 4], k, 0.05, 0.6); k += beat * 2; i += 1
# 5) back to the coffee: the curious theme returns (flows into the loop)
x = T_BACK; ci = 0
while x < DUR:
    pad(light[ci % 4], x, min(x + 4 * beat, DUR), 0.12, fi=0.4, fo=0.05); x += 4 * beat; ci += 1
k = T_BACK + 0.2; i = 0
while k < DUR - 0.1: pluck(mel[i % 16], k, 0.07); k += beat / 2; i += 1
mu[int(T_QUIET0 * SR):int(T_QUIET1 * SR)] *= 0.0
mu = mu / np.max(np.abs(mu)) * 0.8
wavfile.write('/tmp/gv/ant/music.wav', SR, (np.stack([mu, mu], 1) * 32767).astype(np.int16)); print('ok')
