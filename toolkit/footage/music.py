#!/usr/bin/env python3
"""AIDESK original soundtrack engine (no samples, no third-party audio).
Modern tech/news-style track: sidechained supersaw chords, plucked arp with
ping-pong delay, sub bass, punchy drums, riser -> drop on the hook, whoosh +
impact on every scene cut. Fully synced to the Reel timeline.
usage (standalone test): python3 music.py out.wav [n_scenes]"""
import sys, numpy as np
from pedalboard import (Pedalboard, Reverb, Delay, Compressor, Limiter, HighpassFilter,
                        LowpassFilter, Gain, Chorus)

SR = 44100
BPM = 125
BEAT = 60 / BPM            # 0.48 s
BAR = BEAT * 4             # 1.92 s
HOOK_S = BAR * 2           # 3.84 s  (build + riser)
SCENE_S = BAR * 2 + BEAT * 2   # 4.80 s
END_S = BAR * 2            # 3.84 s

def midi(m): return 440.0 * 2 ** ((m - 69) / 12)
PROG = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 52, 55, 60], [55, 59, 62, 67]]  # Am F C G
ROOTS = [45, 41, 36, 43]

rng = np.random.default_rng(11)

def saw(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * t + phase) % 1.0) - 1

def adsr(n, a, d, s, r):
    e = np.full(n, s, dtype=float)
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    A = min(A, n); e[:A] = np.linspace(0, 1, A, endpoint=False) if A else e[:A]
    D2 = min(D, n - A)
    if D2 > 0: e[A:A + D2] = np.linspace(1, s, D2)
    if R > 0 and n > R: e[-R:] *= np.linspace(1, 0, R)
    return e

def onepole_lp(x, cutoff):
    """time-varying one-pole lowpass; cutoff: array (Hz) same length as x"""
    a = 1 - np.exp(-2 * np.pi * np.asarray(cutoff) / SR)
    y = np.empty_like(x); z = 0.0
    a = np.broadcast_to(a, x.shape)
    for i in range(len(x)):
        z += a[i] * (x[i] - z); y[i] = z
    return y

def fx(x, board): return board(x.astype(np.float32)[None, :], SR)[0].astype(float)
def fx_st(x, board): return board(x.astype(np.float32), SR).astype(float)

def place(buf, sig, start):
    s = int(start * SR)
    if s >= len(buf): return
    e = min(len(buf), s + len(sig)); buf[s:e] += sig[:e - s]

# ---------------- instruments ----------------
def kick():
    n = int(0.42 * SR); t = np.arange(n) / SR
    f = 46 + 130 * np.exp(-t * 38)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = rng.standard_normal(n) * np.exp(-t * 400) * 0.35
    return np.tanh((body + click) * 1.6) * 0.9

def clap():
    n = int(0.35 * SR); t = np.arange(n) / SR; nz = rng.standard_normal(n)
    env = np.zeros(n)
    for o in (0, 0.011, 0.022):
        k = int(o * SR); env[k:] += np.exp(-(t[:n - k]) * 60)
    env += 0.5 * np.exp(-t * 14)
    sig = nz * env
    return fx(sig, Pedalboard([HighpassFilter(900), LowpassFilter(9000), Reverb(room_size=0.25, wet_level=0.18, dry_level=0.9)])) * 0.45

def hat(open_=False):
    n = int((0.22 if open_ else 0.06) * SR); t = np.arange(n) / SR
    sig = rng.standard_normal(n) * np.exp(-t * (14 if open_ else 70))
    return fx(sig, Pedalboard([HighpassFilter(7000)])) * (0.22 if open_ else 0.2)

def supersaw(notes, n, voices=5, spread=0.18):
    out = np.zeros(n)
    for m in notes:
        f = midi(m)
        for v in range(voices):
            det = (v - (voices - 1) / 2) / ((voices - 1) / 2) * spread
            out += saw(f * 2 ** (det / 12), n, rng.random())
    return out / (len(notes) * voices)

def pluck(m, dur=0.22):
    n = int(dur * SR); t = np.arange(n) / SR
    x = 0.6 * saw(midi(m), n) + 0.4 * saw(midi(m) * 2.005, n)
    cut = 600 + 5200 * np.exp(-t * 26)
    return onepole_lp(x, cut) * np.exp(-t * 9)

def bass_note(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = 0.55 * np.sin(2 * np.pi * midi(m) * t) + 0.45 * saw(midi(m), n)
    x = onepole_lp(x, 300 + 900 * np.exp(-t * 12))
    return x * adsr(n, 0.004, 0.08, 0.75, 0.03)

def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR; p = t / dur
    nz = rng.standard_normal(n)
    sweep = onepole_lp(nz, 300 + 9000 * p ** 2) - onepole_lp(nz, 120 + 3000 * p ** 2) * 0.6
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * p ** 2) / SR) * 0.25
    return (sweep * 0.5 + tone) * p ** 2.2 * 0.32

def whoosh(dur=0.55):
    n = int(dur * SR); t = np.arange(n) / SR; p = t / dur
    nz = rng.standard_normal(n)
    sig = onepole_lp(nz, 400 + 7000 * np.sin(np.pi * p) ** 2) * np.sin(np.pi * p) ** 2
    return fx(sig, Pedalboard([HighpassFilter(250), Reverb(room_size=0.5, wet_level=0.3)])) * 0.5

def impact():
    n = int(2.2 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t * 12)) / SR) * np.exp(-t * 2.4)
    crash = fx(rng.standard_normal(n) * np.exp(-t * 3.2), Pedalboard([HighpassFilter(2500)])) * 0.25
    return fx(np.tanh(boom * 1.4) * 0.8 + crash, Pedalboard([Reverb(room_size=0.8, wet_level=0.25, dry_level=0.9)]))

# ---------------- arrangement ----------------
def render(path, n_scenes=4, cuts=None, end_start=None, total_len=None):
    total = HOOK_S + SCENE_S * n_scenes + END_S
    if cuts is not None: total = total_len
    n = int((total + 0.3) * SR)
    drums = np.zeros(n); chords = np.zeros(n); bass = np.zeros(n); arp = np.zeros(n); sfx = np.zeros(n)
    drop = HOOK_S; end0 = HOOK_S + SCENE_S * n_scenes
    if cuts is not None: end0 = end_start
    K, C, H, HO = kick(), clap(), hat(), hat(True)
    nbeats = int(total / BEAT) + 1
    # drums (only between drop and end card)
    for b in range(nbeats):
        t = b * BEAT
        if drop <= t < end0:
            place(drums, K, t)
            if b % 2 == 1: place(drums, C, t)
            place(drums, HO, t + BEAT / 2)
            for s in (0.25, 0.75):
                place(drums, H * (0.6 if s == 0.25 else 0.8), t + BEAT * s + (0.012 if s == 0.75 else 0))
        elif t < drop and t >= BAR:           # second hook bar: 8th-note kick build
            pass
    # build: snare roll accelerating into the drop
    for i in range(16):
        t = drop - BAR + i * BAR / 16
        place(drums, C * (0.15 + 0.4 * i / 15), t)
    # sidechain envelope (duck on every kick after drop)
    duck = np.ones(n)
    for b in range(nbeats):
        t = b * BEAT
        if drop <= t < end0:
            s = int(t * SR); L = int(BEAT * SR)
            e = min(n, s + L); tt = np.arange(e - s) / SR
            duck[s:e] = np.minimum(duck[s:e], 1 - 0.75 * np.exp(-tt * 14))
    # chords + bass + arp per bar
    nbars = int(total / BAR) + 1
    for bi in range(nbars):
        t0 = bi * BAR; ch = PROG[bi % 4]; L = int(BAR * SR)
        pad = supersaw(ch, L) * adsr(L, 0.02, 0.2, 0.85, 0.06)
        place(chords, pad, t0)
        if drop <= t0 < end0:
            for q in range(8):                                    # offbeat-driven bass
                m = ROOTS[bi % 4] + (12 if q % 4 == 3 else 0)
                place(bass, bass_note(m, BEAT / 2 * 0.92), t0 + q * BEAT / 2)
        if t0 >= drop - 0.01:                                     # arp from drop to end
            pat = [0, 2, 1, 3, 2, 1, 3, 2]
            for s in range(16):
                m = ch[pat[s % 8]] + 12
                place(arp, pluck(m) * (1.0 if s % 4 == 0 else 0.7), t0 + s * BEAT / 4)
    # filter automation on chords: closed during hook, opens on drop; softer in outro
    tt = np.arange(n) / SR
    cut = np.where(tt < drop, 350 + 1800 * (tt / drop) ** 2, 5200)
    cut = np.where(tt >= end0, 2600, cut)
    chords = onepole_lp(chords, cut)
    chords *= duck; bass *= duck
    # fx
    place(sfx, riser(HOOK_S - 0.2), 0.2)
    place(sfx, impact(), drop)
    for c in (cuts if cuts is not None else [drop + k * SCENE_S for k in range(1, n_scenes)]):
        place(sfx, whoosh(), c - 0.42)
    place(sfx, whoosh(), end0 - 0.42); place(sfx, impact() * 0.8, end0)
    # bus processing
    chords_st = fx_st(np.stack([chords, chords]), Pedalboard([Chorus(rate_hz=0.6, depth=0.3, mix=0.5), HighpassFilter(180), Reverb(room_size=0.6, wet_level=0.22, dry_level=0.8, width=1.0)]))
    arp_st = fx_st(np.stack([arp, arp]), Pedalboard([HighpassFilter(400), Delay(delay_seconds=BEAT * 0.75, feedback=0.35, mix=0.28), Reverb(room_size=0.45, wet_level=0.2, width=1.0)]))
    # widen arp a bit (haas)
    d = int(0.011 * SR); arp_st[1] = np.concatenate([np.zeros(d), arp_st[1][:-d]])
    mix = (np.stack([drums, drums]) * 0.9 + chords_st * 0.62 + np.stack([bass, bass]) * 0.42
           + arp_st * 0.45 + np.stack([sfx, sfx]) * 0.6)
    # fade the tail
    tail = int(1.6 * SR); mix[:, -tail:] *= np.linspace(1, 0, tail)
    mix = fx_st(mix, Pedalboard([HighpassFilter(28), Compressor(threshold_db=-14, ratio=2.5, attack_ms=10, release_ms=120),
                                 Gain(1), Limiter(threshold_db=-2.0, release_ms=80)]))
    mix = np.clip(mix, -0.89, 0.89)
    mix = mix[:, :int(total * SR)]
    from pedalboard.io import AudioFile
    with AudioFile(path, "w", SR, 2) as f: f.write(mix.astype(np.float32))
    return total

if __name__ == "__main__":
    print(render(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4))
