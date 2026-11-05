import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
SR = 48000; DUR = 63.4; N = int(SR * DUR)
rng = np.random.default_rng(3)
def lp(x, c, o=2): return sosfilt(butter(o, c, 'low', fs=SR, output='sos'), x)
def add(buf, sig, t, g=1.0):
    i = int(t * SR); n = min(len(sig), len(buf) - i)
    if n > 0 and i >= 0: buf[i:i + n] += sig[:n] * g
mu = np.zeros(N)
bpm = 92; beat = 60 / bpm
def pad(freqs, a, b, g=0.2, fade_in=1.0, fade_out=0.6):
    n = int((b - a) * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for f in freqs:
        for det in (-0.7, 0.7): s += np.sin(2 * np.pi * (f + det) * tt) * 0.3
    e = np.clip(tt / fade_in, 0, 1) * np.clip((b - a - tt) / fade_out, 0, 1)
    add(mu, lp(s, 1600) * e, a, g)
def pluck(f, t, g):
    n = int(0.9 * SR); tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt / 0.35)
    add(mu, s, t, g)
def kick(t, g):
    n = int(0.25 * SR); tt = np.arange(n) / SR
    add(mu, np.sin(2 * np.pi * (52 + 55 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.12), t, g)
T_BLIND = 37.7; T_BACK = 55.62
chords = [(110, 164.8, 220, 261.6), (87.3, 130.8, 174.6, 220), (98, 146.8, 196, 246.9), (82.4, 123.5, 164.8, 207.7)]
x = 0.0; ci = 0
while x < T_BLIND:
    pad(chords[ci % 4], x, min(x + 4 * beat, T_BLIND), 0.15, fade_in=0.05 if x == 0 else 1.0); x += 4 * beat; ci += 1
# frozen-time music box plucks (sparse, glassy) from the freeze to 'blind'
arp = [659.3, 523.3, 440.0, 523.3, 587.3, 493.9, 392.0, 493.9]
k = 1.95; i = 0
while k < T_BLIND - 0.3:
    pluck(arp[i % 8], k, 0.07); k += beat / 2 * (1 if k < 19.5 else 1); i += 1
k = 19.5
while k < T_BLIND - 0.2:
    kick(k, 0.22); k += beat
# after time restarts: warm resolve that loops back into the opening chord
pad((110, 164.8, 220, 277.2), T_BACK + 0.05, DUR, 0.16, fade_in=0.3, fade_out=0.25)
k = T_BACK + 0.4
while k < DUR - 0.3:
    kick(k, 0.2); k += beat
mu[int(T_BLIND * SR):int(T_BACK * SR)] = 0
mu = mu / np.max(np.abs(mu)) * 0.8
wavfile.write('/tmp/gv/freeze/music.wav', SR, (np.stack([mu, mu], 1) * 32767).astype(np.int16))
print('ok')
