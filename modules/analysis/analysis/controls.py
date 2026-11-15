def onPulse(par):
    if par.name == 'Resetgrowth':
        me.parent().op('growth').par.value0 = 0
    return
