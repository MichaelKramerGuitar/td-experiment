# Regenerates one chain per row of stem_map:  audio file -> rename -> merge -> out1 (audio rate)
# Safe to re-run (pulse Rebuild). Generated ops are tagged "stemgen".
comp = me.parent()
tbl = comp.op('stem_map')
merge = comp.op('merge')
for o in list(comp.children):
    if 'stemgen' in o.tags:
        o.destroy()
for r in range(1, tbl.numRows):
    ch = tbl[r, 'channel'].val
    f = tbl[r, 'file'].val
    af = comp.create(audiofileinCHOP, 'af_' + ch)
    af.par.file.expr = "parent().par.Stemsfolder + '/' + " + repr(f)
    af.par.playmode = 'sequential'
    af.par.mono = True
    af.par.repeat = 'off'
    af.par.play.expr = 'parent().par.Play'
    rn = comp.create(renameCHOP, 'name_' + ch)
    rn.par.renamefrom = '*'
    rn.par.renameto = ch
    rn.inputConnectors[0].connect(af)
    rn.outputConnectors[0].connect(merge)
    for i, o in enumerate((af, rn)):
        o.tags.add('stemgen')
        o.nodeX = -450 + i * 150
        o.nodeY = 150 - (r - 1) * 110
