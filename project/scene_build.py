# One Select TOP per row of "scenes" -> scene_switch. Re-run after editing the table.
comp = me.parent()
tbl = comp.op('scenes'); sw = comp.op('scene_switch')
for o in list(comp.children):
    if 'scenegen' in o.tags:
        o.destroy()
for r in range(1, tbl.numRows):
    s = comp.create(selectTOP, 'scene_%d' % r)
    s.par.top = tbl[r, 'top'].val
    s.tags.add('scenegen'); s.nodeX = -200; s.nodeY = 100 - (r - 1) * 120
    s.outputConnectors[0].connect(sw)
sc_ = op.Show
if sc_ is not None:
    names = [tbl[r, 'name'].val for r in range(1, tbl.numRows)]
    sc_.par.Scene.menuNames = [str(i) for i in range(len(names))]
    sc_.par.Scene.menuLabels = names
