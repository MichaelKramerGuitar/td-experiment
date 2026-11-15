def onPulse(par):
    C = me.parent()
    n = len(C.par.Scene.menuNames)
    if par.name == 'Restart':
        op.Source.par.Restart.pulse()
    elif par.name == 'Nextscene':
        C.par.Scene.menuIndex = (C.par.Scene.menuIndex + 1) % n
    elif par.name == 'Prevscene':
        C.par.Scene.menuIndex = (C.par.Scene.menuIndex - 1) % n
    elif par.name == 'Openpreview':
        op.Output.op('preview_window').par.winopen.pulse()
    elif par.name == 'Closepreview':
        op.Output.op('preview_window').par.winclose.pulse()
    elif par.name == 'Perform':
        ui.performMode = True
    elif par.name == 'Renderfullsong':
        # Offline render: every frame is rendered and recorded, however long it takes.
        op.Output.op('preview_window').par.winclose.pulse()
        C.par.Monitor = False
        C.par.Pause = False
        project.realTime = False
        op.Source.par.Restart.pulse()
        C.store('rendering', True)
        C.par.Record = True
    return
