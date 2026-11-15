"""
lyric_timing.py — rough lyric timing from an ISOLATED vocal stem + the known lyrics.

How it works (no speech model needed):
  1. Find sung phrases: RMS loudness of the vocal stem, gate at (90th percentile - --gate dB),
     merge gaps shorter than --merge seconds, drop blips shorter than 0.15 s.
  2. Match phrases to lyric lines in order (the lyrics file has one line per sung phrase).
  3. Inside each phrase, place words on detected syllable onsets, weighted by syllable count.

Lyrics file format (UTF-8 text): one sung phrase per line; a line starting with '#' sets the section.
    # verse1
    The circular haunts the future, primordial song unfolds
    ...
    # chorus1
    Persistence

Outputs lyrics_lines.tsv and lyrics_words.tsv (what overlays/lyrics reads). Always eyeball the result:
the phrase count printed must equal the number of lyric lines; if not, adjust --gate / --merge.
For word-perfect sync, a forced aligner (e.g. WhisperX, Montreal Forced Aligner) can replace step 3
and write the same TSV columns.

Usage:
  pip install librosa numpy
  python tools/lyric_timing.py "Stems/Source-Audio lead vox.mp3" lyrics.txt --out Assets/lyrics
"""
import argparse
import csv
import os
import re

import librosa
import numpy as np


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith('e') and not w.endswith(('le', 'ee')) and n > 1:
        n -= 1
    return max(1, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('vocal')
    ap.add_argument('lyrics')
    ap.add_argument('--out', default='.')
    ap.add_argument('--gate', type=float, default=22.0, help='dB below the loud level that still counts as singing')
    ap.add_argument('--merge', type=float, default=0.35, help='merge phrases separated by less than this (s)')
    a = ap.parse_args()

    lines, sections, sec = [], [], 'intro'
    for raw in open(a.lyrics, encoding='utf-8'):
        raw = raw.strip()
        if not raw:
            continue
        if raw.startswith('#'):
            sec = raw.lstrip('#').strip()
            continue
        lines.append(raw)
        sections.append(sec)

    y, sr = librosa.load(a.vocal, sr=22050, mono=True)
    hop = 256
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=hop)[0]
    db = 20 * np.log10(rms + 1e-7)
    t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    act = db > np.percentile(db, 90) - a.gate
    segs, on = [], None
    for i, v in enumerate(act):
        if v and on is None:
            on = i
        if not v and on is not None:
            segs.append([t[on], t[i]])
            on = None
    merged = []
    for s, e in segs:
        if merged and s - merged[-1][1] < a.merge:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    phrases = [(s, e) for s, e in merged if e - s > 0.15]
    print('phrases found: %d   lyric lines: %d' % (len(phrases), len(lines)))
    for s, e in phrases:
        print('  %7.2f - %7.2f  (%.1fs)' % (s, e, e - s))
    if len(phrases) != len(lines):
        print('!! counts differ: adjust --gate/--merge (or edit the TSVs by hand). Pairing in order anyway.')

    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onsets = librosa.onset.onset_detect(onset_envelope=oenv, sr=sr, hop_length=hop, units='time', backtrack=True)

    words_rows, line_rows = [], []
    for li, ((s, e), text, sec) in enumerate(zip(phrases, lines, sections)):
        words = text.split()
        sy = [syllables(w) for w in words]
        tot = sum(sy)
        o = [x for x in onsets if s - 0.05 <= x < e - 0.1]
        if not o or o[0] - s > 0.15:
            o = [s] + o
        cum = np.cumsum([0] + sy[:-1])
        starts = []
        for c in cum:
            if len(o) >= tot * 0.6:
                starts.append(o[min(int(round(c * len(o) / tot)), len(o) - 1)])
            else:
                starts.append(s + (e - s) * c / tot)
        for i in range(1, len(starts)):
            if starts[i] <= starts[i - 1]:
                starts[i] = starts[i - 1] + 0.08
        for wi, (w, st) in enumerate(zip(words, starts)):
            en = starts[wi + 1] if wi + 1 < len(starts) else e
            words_rows.append([li, sec, wi, round(st, 3), round(en, 3), w])
        line_rows.append([li, sec, round(s, 3), round(e, 3), text])

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'lyrics_words.tsv'), 'w', newline='', encoding='utf-8') as f:
        wr = csv.writer(f, delimiter='\t')
        wr.writerow(['line', 'section', 'word_index', 'start', 'end', 'word'])
        wr.writerows(words_rows)
    with open(os.path.join(a.out, 'lyrics_lines.tsv'), 'w', newline='', encoding='utf-8') as f:
        wr = csv.writer(f, delimiter='\t')
        wr.writerow(['line', 'section', 'start', 'end', 'text'])
        wr.writerows(line_rows)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
