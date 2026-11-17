# Steps the metabolism engine once per frame.
# - engine object lives in this COMP's storage (survives between frames)
# - pauses with the show; resets on Reset or when the song jumps backwards (Restart)
def _engine(M, fresh=False):
    eng = M.fetch('engine', None)
    if eng is None or fresh:
        core = mod(M.op('core').path)       # import the Text DAT as a Python module
        eng = core.Metabolism()
        M.store('engine', eng)
    return eng

def onFrameStart(frame):
    M = me.parent()
    ph = op.Source.op('playhead')
    pos = ph['fraction'].eval() if ph is not None and ph.numChans else 0.0
    if pos + 0.01 < M.fetch('lastpos', 0.0):
        _engine(M, fresh=True)                       # song restarted -> new life
    M.store('lastpos', pos)
    eng = _engine(M)
    if op.Show.par.Pause.eval():
        return
    eng.p.update(tip=M.par.Tip.eval(), feed=M.par.Feed.eval(), harm=M.par.Harm.eval(), decay=M.par.Decay.eval())
    bus = {c.name: c.eval() for c in op.Bus.op('out').chans()}
    world = {c.name: c.eval() for c in op.World.op('out').chans()}
    out = eng.step(absTime.stepSeconds, bus, world, M.par.Role.eval())
    st = M.op('state')
    for i in range(8):
        n = st.par['name%d' % i].eval()
        st.par['value%d' % i] = out.get(n, 0.0)
    return
