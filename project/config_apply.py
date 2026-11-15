# Applies config values that are not plain expressions.
def onValueChange(par, prev):
    if par.name == 'Fps':
        project.cookRate = int(par.eval())
    return
