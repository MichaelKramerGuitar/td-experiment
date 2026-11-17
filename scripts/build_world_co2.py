# build_world_co2.py
# Builds /project1/world (op.World) and the adapter /project1/world/co2_in, following
# docs/exercises/05_world_adapter.md step by step (same operator names), so the result can be
# read side by side with the exercise.
# Run inside TouchDesigner:
#   exec(open(project.folder + '/scripts/build_world_co2.py', encoding='utf-8').read())

root = op('/project1')


def X(par, e):
    par.expr = e
    par.mode = ParMode.EXPRESSION


def mk(parent, typ, name, x, y, inp=None):
    o = parent.create(typ, name)
    o.nodeX, o.nodeY = x, y
    if inp is not None:
        o.inputConnectors[0].connect(inp)
    return o


# ---- Step 1: the layer and the module ----
W = root.op('world')
if W is None:
    W = root.create(baseCOMP, 'world')
W.nodeX, W.nodeY = 200, -250
W.par.opshortcut = 'World'
W.comment = 'WORLD layer: historical snapshots -> analysis -> op.World contract (the environment of the metabolism).'
for c in list(W.children):
    c.destroy()
A = W.create(baseCOMP, 'co2_in')
A.nodeX, A.nodeY = 0, 0
A.comment = ('Adapter: NOAA Mauna Loa monthly CO2 (frozen snapshot in Assets/world). '
             'Whole 1958->today history laid across the song via a Lookup CHOP indexed by the song playhead.')
pg = A.appendCustomPage('World')
pg.appendFile('Snapshot')
A.par.Snapshot = 'Assets/world/co2_mm_mlo.csv'

# ---- Step 2: load the file ----
raw = mk(A, fileinDAT, 'raw', -800, 0)
X(raw.par.file, 'parent().par.Snapshot')

# ---- Step 3: clean it with a Script DAT ----
clean = mk(A, scriptDAT, 'clean', -600, 0, raw)
cb = clean.par.callbacks.eval()
cb.text = '''# clean: NOAA CSV (comment lines + header + rows) -> 3-column table.
# The File In DAT delivers the file as ONE cell of text, so we split it into lines ourselves.
def onCook(scriptOp):
    scriptOp.clear()
    src = scriptOp.inputs[0]
    text = '\\n'.join(c.val for c in src.col(0)) if src.numCols == 1 else None
    lines = text.splitlines() if text is not None else [','.join(c.val for c in src.row(r)) for r in range(src.numRows)]
    header = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue                      # skip comments / blanks
        cells = [c.strip() for c in line.split(',')]
        if header is None:
            header = cells                # year,month,decimal date,average,deseasonalized,...
            scriptOp.appendRow(['decimal_date', 'average', 'deseasonalized'])
            continue
        row = dict(zip(header, cells))
        try:
            avg = float(row['average'])
        except (KeyError, ValueError):
            continue
        if avg < 0:                       # NOAA marks missing values with negative numbers
            continue
        scriptOp.appendRow([row['decimal date'], row['average'], row['deseasonalized']])
    return
'''
clean.cook(force=True)

# ---- Step 4: table -> timeline ----
tl = mk(A, dattoCHOP, 'timeline', -400, 0)
tl.par.dat = 'clean'
tl.par.output = 'chanpercol'
tl.par.firstrow = 'names'
tl.par.firstcolumn = 'values'

# ---- Step 5: normalise (0..1 over the whole history) ----
s_avg = mk(A, selectCHOP, 'sel_average', -200, 100, tl); s_avg.par.channames = 'average'
s_des = mk(A, selectCHOP, 'sel_deseason', -200, 0, tl); s_des.par.channames = 'deseasonalized'
s_dd = mk(A, selectCHOP, 'sel_date', -200, -200, tl); s_dd.par.channames = 'decimal_date'
rmin = mk(A, analyzeCHOP, 'range_min', 0, 250, s_avg); rmin.par.function = 'minimum'
rmax = mk(A, analyzeCHOP, 'range_max', 0, 350, s_avg); rmax.par.function = 'maximum'

lvl = mk(A, mathCHOP, 'norm_level', 0, 100, s_avg)
X(lvl.par.fromrange1, "op('range_min')[0]"); X(lvl.par.fromrange2, "op('range_max')[0]")
lvl.par.torange1 = 0; lvl.par.torange2 = 1
trd = mk(A, mathCHOP, 'norm_trend', 0, 0, s_des)
X(trd.par.fromrange1, "op('range_min')[0]"); X(trd.par.fromrange2, "op('range_max')[0]")
trd.par.torange1 = 0; trd.par.torange2 = 1

cyc_raw = mk(A, mathCHOP, 'cycle_raw', 0, -100)          # average - deseasonalized (ppm)
cyc_raw.inputConnectors[0].connect(s_avg); cyc_raw.inputConnectors[1].connect(s_des)
cyc_raw.par.chopop = 'sub'
cmin = mk(A, analyzeCHOP, 'cycle_min', 200, -250, cyc_raw); cmin.par.function = 'minimum'
cmax = mk(A, analyzeCHOP, 'cycle_max', 200, -350, cyc_raw); cmax.par.function = 'maximum'
cyc = mk(A, mathCHOP, 'norm_cycle', 200, -100, cyc_raw)
X(cyc.par.fromrange1, "op('cycle_min')[0]"); X(cyc.par.fromrange2, "op('cycle_max')[0]")
cyc.par.torange1 = -1; cyc.par.torange2 = 1

names = []
for src, nm, y in ((lvl, 'level', 100), (trd, 'trend', 0), (cyc, 'cycle', -100), (s_dd, 'year', -200)):
    r = mk(A, renameCHOP, 'as_' + nm, 400, y, src)
    r.par.renamefrom = '*'; r.par.renameto = nm
    names.append(r)
table = mk(A, mergeCHOP, 'history', 600, 0)
for r in names:
    r.outputConnectors[0].connect(table)
table.comment = 'The whole history as channels (one sample per month): level, trend, cycle, year.'

# ---- Step 6: compress time onto the song (Lookup CHOP) ----
pos = mk(A, selectCHOP, 'song_pos', 600, 250)
X(pos.par.chops, "op.Source.op('playhead')")
pos.par.channames = 'fraction'
look = mk(A, lookupCHOP, 'at_song_time', 800, 100)
look.inputConnectors[0].connect(pos)
look.inputConnectors[1].connect(table)
look.par.index1 = 0; look.par.index2 = 1
look.par.chanmatch = 'onetomany'
look.par.interp = True
look.comment = '"We are 40% through the song -> give me the value 40% of the way through 1958..today."'

# ---- Step 7: publish the contract ----
dt = mk(A, renameCHOP, 'as_data_time', 800, 250, pos); dt.par.renamefrom = '*'; dt.par.renameto = 'data_time'
# In "one to many" mode the Lookup CHOP prefixes outputs with the index channel's name
# (fractionlevel, fractioncycle, ...): strip it.
unpre = mk(A, renameCHOP, 'strip_prefix', 900, 100, look); unpre.par.renamefrom = 'fraction*'; unpre.par.renameto = '*'
outm = mk(A, mergeCHOP, 'contract', 1000, 100)
dt.outputConnectors[0].connect(outm)
unpre.outputConnectors[0].connect(outm)
out1 = mk(A, outCHOP, 'out1', 1200, 100, outm)

sel = mk(W, selectCHOP, 'from_co2', 300, 0); sel.par.chops = 'co2_in/out1'
wout = mk(W, nullCHOP, 'out', 500, 0, sel)
wout.comment = 'THE WORLD CONTRACT: data_time level trend cycle year (anomaly/event come from world_analyze later).'

for o in (raw, clean, tl, table, look, wout):
    o.cook(force=True)
world_report = {
    'clean_rows': clean.numRows - 1,
    'timeline': [tl.numChans, tl.numSamples, [c.name for c in tl.chans()]],
    'history_ranges': {c.name: [round(min(c.vals), 3), round(max(c.vals), 3)] for c in table.chans()},
    'world_out': {c.name: round(c.eval(), 4) for c in wout.chans()},
    'errors': {o.path: o.errors() for o in W.findChildren() if o.errors()},
    'warnings': {o.path: o.warnings() for o in W.findChildren() if o.warnings()},
}
