# Record toggle -> name the take FIRST, then start the recorder (never overwrites).
import datetime
def onValueChange(par, prev):
    rec = op.Output.op('recorder')
    if par.eval():
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        name = '%s/%s_%s.mov' % (op.Config.par.Recordingsfolder.eval(), op.Config.par.Preset.eval(), stamp)
        rec.par.file = name
        me.parent().store('lasttake', name)
        run("op.Output.op('recorder').par.record = True", delayFrames=1)
    else:
        rec.par.record = False
    return
