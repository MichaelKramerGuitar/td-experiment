# Every frame: find the line being sung, show the words sung so far, fade in/out.
def onFrameStart(frame):
    L = me.parent()
    C = op.Show
    fade = L.op('fade')
    o = fade.par.opacity.eval()
    if not C.par.Lyrics.eval():
        fade.par.opacity = 0
        return
    t = op.Show.op('clock')['songtime'].eval() + L.par.Offset.eval()
    lines = L.op('lines')
    words = L.op('words')
    hold = L.par.Hold.eval()
    cur = None
    for r in range(1, lines.numRows):
        if float(lines[r, 'start']) - 0.2 <= t <= float(lines[r, 'end']) + hold:
            cur = r
    if cur is None:
        fade.par.opacity = max(0.0, o - 0.06)
        return
    li = lines[cur, 'line'].val
    lead = L.par.Lead.eval()
    sung = [words[r, 'word'].val for r in range(1, words.numRows)
            if words[r, 'line'].val == li and float(words[r, 'start']) <= t + lead]
    L.op('text').par.text = ' '.join(sung)
    target = 1.0 if t <= float(lines[cur, 'end']) + hold - 0.6 else 0.0
    fade.par.opacity = o + (target - o) * 0.15
    return
