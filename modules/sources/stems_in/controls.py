def onPulse(par):
    comp = me.parent()
    if par.name == 'Rebuild':
        comp.op('build').run()
    elif par.name == 'Restart':
        for o in comp.ops('af_*'):
            o.par.cuepulse.pulse()
        # project-level coupling: restarting the song also resets the growth accumulator
        a = op.Analysis
        if a is not None:
            a.par.Resetgrowth.pulse()
    return
