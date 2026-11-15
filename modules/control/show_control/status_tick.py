# Show clock = true audio playback position. Also finishes offline renders and updates Status.
def onFrameStart(frame):
    C = me.parent()
    clk = C.op('clock')
    ph = op.Source.op('playhead')
    if ph is not None and ph.numChans:
        clk.par.value0 = ph['sample'].eval() / max(1.0, ph['sample_rate'].eval())
        done = ph['fraction'].eval() >= 0.9995
    else:
        done = False
    if C.fetch('rendering', False) and done:
        C.par.Record = False
        project.realTime = True
        C.store('rendering', False)
    if frame % 10:
        return
    secs = clk.par.value0.eval()
    g = op.Bus.op('out')['growth']
    rec = '   ● REC' if C.par.Record.eval() else ''
    if C.fetch('rendering', False):
        rec = '   ● RENDERING %d%%' % int(ph['fraction'].eval() * 100)
    state = 'PAUSED' if C.par.Pause.eval() else 'PLAYING'
    scene = C.par.Scene.menuLabels[C.par.Scene.menuIndex] if C.par.Scene.menuLabels else '-'
    lyr = '  |  lyrics on' if C.par.Lyrics.eval() else ''
    pf = C.op('perf')
    perf = '%d fps %.0f ms' % (pf['fps'].eval(), pf['msec'].eval()) if pf is not None and pf.numChans > 1 else ''
    C.par.Status = '%s  %d:%02d  |  %s  |  %s  |  growth %d%%%s  |  %s%s' % (state, int(secs // 60), int(secs % 60), scene, op.Config.par.Preset.eval(), int((g.eval() if g is not None else 0) * 100), lyr, perf, rec)
    return
