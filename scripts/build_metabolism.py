# build_metabolism.py
# Builds /project1/metabolism (op.Metabolism): the stateful engine that turns song energy (op.Bus)
# inside an environment (op.World) into breath and the vitality of a life-force inhabitor.
# The engine itself is plain Python in modules/metabolism/metabolism_core.py (shared with
# tools/simulate_metabolism.py), loaded here into a Text DAT `core` that syncs with that file.
# Also adds a "World Role" menu to the control panel and the "Oak · Metabolism" scene.
# Run inside TouchDesigner:
#   exec(open(project.folder + '/scripts/build_metabolism.py', encoding='utf-8').read())

root = op('/project1')


def X(par, e):
    par.expr = e
    par.mode = ParMode.EXPRESSION


old = root.op('metabolism')
if old:
    old.destroy()
M = root.create(baseCOMP, 'metabolism')
M.nodeX, M.nodeY = 400, -250
M.par.opshortcut = 'Metabolism'
M.comment = ('METABOLISM: song energy (op.Bus) + environment (op.World) -> stored energy -> reactions -> breath '
             '-> vitality of the inhabitor. Engine = core (modules/metabolism/metabolism_core.py), stepped by tick.')

pg = M.appendCustomPage('Metabolism')
pg.appendMenu('Role', label='World Role')
pg.appendFloat('Tip', label='Tipping Point (world level)')
pg.appendFloat('Feed', label='Feed (breath -> vitality)')
pg.appendFloat('Harm', label='Harm (stress -> vitality)')
pg.appendFloat('Decay', label='Natural Decay')
pg.appendPulse('Reset', label='Reset Engine')
M.par.Role.menuNames = ['abundance', 'stress', 'tipping']
M.par.Role.menuLabels = ['Abundance', 'Stress', 'Tipping (abundance -> stress)']
for p_, v in (('Tip', 0.55), ('Feed', 0.24), ('Harm', 0.32), ('Decay', 0.035)):
    M.par[p_] = v
    M.par[p_].default = v

core = M.create(textDAT, 'core')
core.nodeX, core.nodeY = -400, 200
core.par.file = 'modules/metabolism/metabolism_core.py'
core.par.syncfile = True
if not core.text.strip():
    core.text = open(project.folder + '/modules/metabolism/metabolism_core.py', encoding='utf-8').read()

state = M.create(constantCHOP, 'state')
state.nodeX, state.nodeY = 0, 0
OUTS = ['energy', 'rate', 'breath', 'vitality', 'substrate', 'capacity', 'stress', 'catalyst']
for i, n in enumerate(OUTS):
    state.par['name%d' % i] = n
state.comment = 'Written every frame by tick. The metabolism contract: ' + ' '.join(OUTS)
null = M.create(nullCHOP, 'out')
null.nodeX, null.nodeY = 200, 0
null.inputConnectors[0].connect(state)
o1 = M.create(outCHOP, 'out1')
o1.nodeX, o1.nodeY = 400, 0
o1.inputConnectors[0].connect(null)

hist = M.create(trailCHOP, 'history')
hist.nodeX, hist.nodeY = 200, -200
hist.inputConnectors[0].connect(null)
try:
    hist.par.wlength = 30
    hist.par.wlengthunit = 'seconds'
except Exception:
    pass
hist.comment = 'DEBUG: last 30 s of the metabolism. Turn on this node\'s viewer to watch the reservoirs live.'

tick = M.create(executeDAT, 'tick')
tick.nodeX, tick.nodeY = -400, 0
tick.par.framestart = True
tick.text = '''# Steps the metabolism engine once per frame.
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
'''

ctl = M.create(parameterexecuteDAT, 'controls')
ctl.nodeX, ctl.nodeY = -400, -200
ctl.par.op = '..'
ctl.par.pars = 'Reset'
ctl.par.onpulse = True
ctl.par.valuechange = False
ctl.text = 'def onPulse(par):\n    me.parent().store("engine", None)\n    return\n'

# ---- control panel: World Role menu (drives op.Metabolism.par.Role) ----
C = op.Show
pgS = [p for p in C.customPages if p.name == 'Show'][0]
if not hasattr(C.par, 'Worldrole'):
    pgS.appendMenu('Worldrole', label='World Role')
C.par.Worldrole.menuNames = ['abundance', 'stress', 'tipping']
C.par.Worldrole.menuLabels = ['Abundance', 'Stress', 'Tipping']
C.par.Worldrole = 'tipping'
try:
    pgS.sort('Pause', 'Restart', 'Scene', 'Prevscene', 'Nextscene', 'Worldrole', 'Lyrics', 'Record',
             'Renderfullsong', 'Openpreview', 'Closepreview', 'Perform', 'Monitor', 'Volume', 'Status')
except Exception:
    pass
X(M.par.Role, 'op.Show.par.Worldrole.eval()')

# ---- inhabitor v0: "Oak · Metabolism" = oak particles, assembled by vitality, lit by breath ----
V = op.Visuals
src = V.op('oak_particles')
old = V.op('oak_metabolism')
if old:
    old.destroy()
S = V.copy(src, name='oak_metabolism')
S.nodeX, S.nodeY = 600, -400
S.par.externaltox = ''
S.comment = ('INHABITOR v0: the oak assembles from points of light as VITALITY rises and dissolves back into '
             'drifting dust as it falls; sunlit points glow with BREATH. Shader shared with oak_particles.')
pgM = S.appendCustomPage('Metabolism')
pgM.appendFloat('Vitalitygain', label='Vitality Gain')
S.par.Vitalitygain = 1.45
S.par.Vitalitygain.default = 1.45
g = S.op('render')
X(g.par.vec0valuey, "parent().par.Previewgrowth if parent().par.Previewgrowth >= 0 "
                    "else min(1.0, op.Metabolism.op('out')['vitality'] * parent().par.Vitalitygain)")
X(g.par.vec1valuez, "op.Metabolism.op('out')['breath']")     # 'hats' slot -> sunlit glow = breath
X(g.par.vec1valuew, "op.Metabolism.op('out')['breath'] * 0.6")  # 'ride' slot

OUT = op.Output
sc = OUT.op('scenes')
if 'oak_metabolism' not in ' '.join(sc[r, 'top'].val for r in range(1, sc.numRows)):
    sc.appendRow(['Oak · Metabolism', '/project1/visuals/oak_metabolism/out1'])
OUT.op('scene_build').run()
C.par.Scene.menuIndex = len(C.par.Scene.menuNames) - 1

M.cook(force=True)
metab_report = {
    'core_loaded': 'class Metabolism' in core.text,
    'scenes': list(C.par.Scene.menuLabels),
    'errors': {o.path: o.errors() for o in list(M.findChildren()) + list(S.findChildren()) if o.errors()},
}
