# build_lyrics.py
# Builds /project1/overlays/lyrics (a toggleable lyric overlay) and wires it into /project1/output.
# Run inside TouchDesigner:  exec(open(project.folder + '/scripts/build_lyrics.py', encoding='utf-8').read())
# Timing data: Assets/lyrics/lyrics_lines.tsv and lyrics_words.tsv (edit them, then pulse Reload on the component).

root = op('/project1')   # the project's composition root


def X(par, e):
    par.expr = e
    par.mode = ParMode.EXPRESSION


OV = root.op('overlays') or root.create(baseCOMP, 'overlays')
OV.nodeX, OV.nodeY = 800, -250
OV.comment = 'Overlays composited on top of whatever scene is live (lyrics, titles, ...).'

old = OV.op('lyrics')
if old:
    old.destroy()
L = OV.create(baseCOMP, 'lyrics')
L.comment = ('Shows each lyric line, word by word, as it is sung. Toggle with show_control > Show Lyrics. '
             'Offset nudges sync (+ = earlier words). Edit the TSVs in Assets/lyrics and pulse Reload.')
pg = L.appendCustomPage('Lyrics')
pg.appendFolder('Folder')
pg.appendFloat('Offset', label='Sync Offset (s)')
pg.appendFloat('Lead', label='Word Lead (s)')
pg.appendFloat('Hold', label='Hold After Line (s)')
pg.appendFloat('Fontsize', label='Font Size (px)')
pg.appendFloat('Bottom', label='Distance From Bottom (px)')
pg.appendPulse('Reload')
for p, v in (('Offset', 0.0), ('Lead', 0.08), ('Hold', 1.6),
             ('Fontsize', 46.0), ('Bottom', 64.0)):
    L.par[p] = v
    L.par[p].default = v

X(L.par.Folder, "project.folder + '/' + op.Config.par.Lyricsfolder")
L.par.opshortcut = 'Lyrics'
lines = L.create(tableDAT, 'lines')
lines.nodeX, lines.nodeY = -600, 200
words = L.create(tableDAT, 'words')
words.nodeX, words.nodeY = -600, 50

loader = L.create(textDAT, 'loader')
loader.nodeX, loader.nodeY = -600, -100
loader.text = '''# Loads the timing tables from the Folder parameter.
L = me.parent()
folder = L.par.Folder.eval()
L.op('lines').text = open(folder + '/lyrics_lines.tsv', encoding='utf-8').read()
L.op('words').text = open(folder + '/lyrics_words.tsv', encoding='utf-8').read()
'''
loader.run()

txt = L.create(textTOP, 'text')
txt.nodeX, txt.nodeY = -300, 0
txt.par.outputresolution = 'custom'
X(txt.par.resolutionw, 'op.Config.par.Width')
X(txt.par.resolutionh, 'op.Config.par.Height')
txt.par.bgalpha = 0
txt.par.font = 'Sitka Display'
txt.par.typeface = 'Italic'
X(txt.par.fontsizex, 'parent().par.Fontsize * min(op.Config.par.Width, op.Config.par.Height) / 720')   # scales with the short side (works in 9:16)
txt.par.fontcolorr, txt.par.fontcolorg, txt.par.fontcolorb = 1.0, 0.97, 0.90
txt.par.alignx = 'center'
txt.par.aligny = 'bottom'
txt.par.positionunit = 'pixels'
X(txt.par.positiony, 'parent().par.Bottom * min(op.Config.par.Width, op.Config.par.Height) / 720')
txt.par.wordwrap = True
txt.par.text = ''

blur = L.create(blurTOP, 'shadow_blur')
blur.nodeX, blur.nodeY = -150, -150
blur.inputConnectors[0].connect(txt)
blur.par.size = 10
shadow = L.create(levelTOP, 'shadow')
shadow.nodeX, shadow.nodeY = 0, -150
shadow.inputConnectors[0].connect(blur)
shadow.par.brightness1 = 0
shadow.par.opacity = 0.85
stack = L.create(overTOP, 'stack')
stack.nodeX, stack.nodeY = 150, 0
stack.inputConnectors[0].connect(txt)
stack.inputConnectors[1].connect(shadow)
fade = L.create(levelTOP, 'fade')
fade.nodeX, fade.nodeY = 300, 0
fade.inputConnectors[0].connect(stack)
fade.par.opacity = 0
out = L.create(outTOP, 'out1')
out.nodeX = 450
out.inputConnectors[0].connect(fade)

tick = L.create(executeDAT, 'tick')
tick.nodeX, tick.nodeY = -600, -250
tick.par.framestart = True
tick.text = '''# Every frame: find the line being sung, show the words sung so far, fade in/out.
def onFrameStart(frame):
    L = me.parent()
    C = op.Show
    fade = L.op('fade')
    o = fade.par.opacity.eval()
    if not C.par.Lyrics.eval():
        fade.par.opacity = 0
        return
    t = op.Show.op('clock')['songtime'].eval() + L.par.Offset.eval()
    lines = L.op('lines')
    words = L.op('words')
    hold = L.par.Hold.eval()
    cur = None
    for r in range(1, lines.numRows):
        if float(lines[r, 'start']) - 0.2 <= t <= float(lines[r, 'end']) + hold:
            cur = r
    if cur is None:
        fade.par.opacity = max(0.0, o - 0.06)
        return
    li = lines[cur, 'line'].val
    lead = L.par.Lead.eval()
    sung = [words[r, 'word'].val for r in range(1, words.numRows)
            if words[r, 'line'].val == li and float(words[r, 'start']) <= t + lead]
    L.op('text').par.text = ' '.join(sung)
    target = 1.0 if t <= float(lines[cur, 'end']) + hold - 0.6 else 0.0
    fade.par.opacity = o + (target - o) * 0.15
    return
'''

ctl = L.create(parameterexecuteDAT, 'controls')
ctl.nodeX, ctl.nodeY = -600, -400
ctl.par.op = '..'
ctl.par.pars = 'Reload'
ctl.par.onpulse = True
ctl.par.valuechange = False
ctl.text = 'def onPulse(par):\n    me.parent().op("loader").run()\n    return\n'

# ---- wire into output: lyrics over the live scene ----
OUT = op.Output
sel = OUT.op('from_lyrics') or OUT.create(selectTOP, 'from_lyrics')
sel.nodeX, sel.nodeY = 0, 200
X(sel.par.top, "op.Lyrics.op('out1')")
ov = OUT.op('lyrics_over') or OUT.create(overTOP, 'lyrics_over')
ov.nodeX, ov.nodeY = 150, 100
ov.inputConnectors[0].connect(sel)
ov.inputConnectors[1].connect(OUT.op('scene_switch'))
OUT.op('final').inputConnectors[0].connect(ov)
OUT.op('final').nodeX = 300

lyrics_report = {'lines': lines.numRows - 1, 'words': words.numRows - 1,
                 'errors': {o.path: o.errors() for o in L.findChildren() if o.errors()} }
