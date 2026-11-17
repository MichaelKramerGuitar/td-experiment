"""
simulate_metabolism.py — run modules/metabolism/metabolism_core.py offline on the real stems + world data.

Approximates the TouchDesigner analysis (dB-normalised envelopes with attack/release, fast-vs-slow hits),
steps the metabolism at 60 fps for every world role, and plots the result, so the engine can be tuned
before touching the TouchDesigner network.

Usage:
  pip install librosa numpy matplotlib
  python tools/simulate_metabolism.py --stems Stems --co2 Assets/world/co2_mm_mlo.csv --out _snapshots/metabolism_sim.png
"""
import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules', 'metabolism'))
import metabolism_core as mc  # noqa: E402

STEMS = {'kick': 'Source-Audio bass drum.mp3', 'snare': 'Source-Audio snair.mp3',
         'hats': 'Source-Audio oh 1 hat side.mp3', 'ride': 'Source-Audio oh 2 ride side.mp3',
         'vox': 'Source-Audio lead vox.mp3', 'gtr_lead': 'Source-Audio lead gtr.mp3',
         'gtr_rhythm': 'Source-Audio rhythm gtr.mp3', 'sub': 'Source-Audio 4-Basic Sub Sine.mp3',
         'master': 'Source-Audio.mp3'}
FPS = 60


def envelopes(folder, floor_db=-48.0, attack=0.01, release=0.18):
    import librosa
    env = {}
    for ch, fn in STEMS.items():
        y, sr = librosa.load(os.path.join(folder, fn), sr=22050, mono=True)
        hop = sr // FPS
        rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop, center=True)[0]
        db = 20 * np.log10(rms + 1e-7)
        x = np.clip((db - floor_db) / -floor_db, 0, 1)
        out = np.zeros_like(x)
        a, r = 1 - np.exp(-1 / (FPS * attack)), 1 - np.exp(-1 / (FPS * release))
        for i in range(1, len(x)):
            k = a if x[i] > out[i - 1] else r
            out[i] = out[i - 1] + k * (x[i] - out[i - 1])
        env[ch] = out
        if ch in ('kick', 'snare'):
            fast, slow, hit = np.zeros_like(x), np.zeros_like(x), np.zeros_like(x)
            kf, ks = 1 - np.exp(-1 / (FPS * 0.02)), 1 - np.exp(-1 / (FPS * 0.25))
            armed = True
            for i in range(1, len(x)):
                fast[i] = x[i] if x[i] > fast[i - 1] else fast[i - 1] + kf * (x[i] - fast[i - 1])
                slow[i] = slow[i - 1] + ks * (x[i] - slow[i - 1])
                flux = fast[i] - slow[i]
                if armed and flux > 0.12:
                    hit[i] = 1.0
                    armed = False
                else:
                    hit[i] = max(0.0, hit[i - 1] - 1 / (FPS * 0.35))
                    if flux < 0.06:
                        armed = True
            env[ch + '_hit'] = hit
    n = min(len(v) for v in env.values())
    return {k: v[:n] for k, v in env.items()}, n


def world(co2_path, n):
    dd, avg, des = [], [], []
    with open(co2_path, encoding='utf-8') as f:
        rows = [l for l in f if not l.startswith('#')]
    for r in csv.DictReader(rows):
        a = float(r['average'])
        if a < 0:
            continue
        dd.append(float(r['decimal date'])); avg.append(a); des.append(float(r['deseasonalized']))
    avg, des, dd = np.array(avg), np.array(des), np.array(dd)
    level = (avg - avg.min()) / (avg.max() - avg.min())
    cyc = avg - des
    cycle = (cyc - cyc.min()) / (cyc.max() - cyc.min()) * 2 - 1
    f = np.linspace(0, 1, n)
    idx = np.linspace(0, 1, len(avg))
    return {'level': np.interp(f, idx, level), 'cycle': np.interp(f, idx, cycle), 'year': np.interp(f, idx, dd)}


def simulate(env, w, n, role, params=None):
    m = mc.Metabolism(params)
    keys = None
    rec = {}
    for i in range(n):
        b = {k: v[i] for k, v in env.items()}
        o = m.step(1.0 / FPS, b, {'level': w['level'][i], 'cycle': w['cycle'][i]}, role)
        if keys is None:
            keys = list(o)
            rec = {k: np.zeros(n) for k in keys}
        for k in keys:
            rec[k][i] = o[k]
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stems', default='Stems')
    ap.add_argument('--co2', default='Assets/world/co2_mm_mlo.csv')
    ap.add_argument('--out', default='_snapshots/metabolism_sim.png')
    a = ap.parse_args()
    env, n = envelopes(a.stems)
    w = world(a.co2, n)
    t = np.arange(n) / FPS
    runs = {role: simulate(env, w, n, role) for role in mc.ROLES}

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(4, 1, figsize=(13, 10), sharex=True)
    axs[0].plot(t, env['master'], color='#888', lw=0.6, label='song (master envelope)')
    axs[0].plot(t, w['level'], color='#c0392b', lw=2, label='CO₂ level (1958→2026, normalised)')
    axs[0].plot(t, 0.5 + 0.15 * w['cycle'], color='#e67e22', lw=0.8, label='seasonal cycle')
    axs[0].legend(loc='upper left', fontsize=8); axs[0].set_title('Inputs')
    colors = {'abundance': '#27ae60', 'stress': '#8e44ad', 'tipping': '#2980b9'}
    for role, r in runs.items():
        axs[1].plot(t, r['vitality'], color=colors[role], lw=1.6, label=role)
        axs[2].plot(t, r['breath'], color=colors[role], lw=0.7, alpha=0.85, label=role)
        axs[3].plot(t, r['energy'], color=colors[role], lw=0.7, alpha=0.85, label=role)
    axs[1].set_title('Vitality of the inhabitor'); axs[1].legend(loc='upper left', fontsize=8)
    axs[2].set_title('Breath (outflow)'); axs[3].set_title('Stored energy')
    axs[3].set_xlabel('song time (s)')
    for ax in axs:
        ax.grid(alpha=0.25)
    yr = w['year']
    sec = axs[0].secondary_xaxis('top', functions=(lambda s: np.interp(s, t, yr), lambda y: np.interp(y, yr, t)))
    sec.set_xlabel('data year')
    fig.tight_layout()
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    fig.savefig(a.out, dpi=110)
    for role, r in runs.items():
        v = r['vitality']
        q = [v[int(n * f) - 1] for f in (0.25, 0.5, 0.75, 1.0)]
        print('%-9s vitality at 25/50/75/100%%: %s   max %.2f   breath mean %.2f' %
              (role, ' '.join('%.2f' % x for x in q), v.max(), r['breath'].mean()))
    print('wrote', a.out)


if __name__ == '__main__':
    main()
