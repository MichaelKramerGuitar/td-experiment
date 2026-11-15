# Growth accumulator: growth += Growthrate * master_loudness * seconds  (clamped 0..1)
def onFrameStart(frame):
    A = me.parent()
    c = A.op('growth')
    m = A.op('env')['master']
    if m is None:
        return
    v = c.par.value0.eval() + A.par.Growthrate.eval() * m.eval() * absTime.stepSeconds
    c.par.value0 = max(0.0, min(1.0, v))
    return
