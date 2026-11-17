# build_oak3d.py
# Builds /project1/visuals/oak3d: the oak as ~126k GPU-instanced 3D particles, grown and decayed by the
# metabolism's vitality, filmed by a camera that walks a path through the song (camera_path table).
# Run inside TouchDesigner:
#   exec(open(project.folder + '/scripts/build_oak3d.py', encoding='utf-8').read())
#
# Data flow (all on the GPU except the one-time load):
#   tree3d.npz --(Script TOP, numpy)--> home   (x, y, z, growth-order) per pixel = per particle
#                                   --> colors (r, g, b, kind)
#   home --(GLSL TOP 'animate', uniforms: vitality, time, breath, hits)--> particle (x, y, z, scale)
#   Geometry COMP 'tree': one tiny sphere instanced once per pixel of 'animate', coloured by 'colors'
#   Camera COMP 'cam' + Null COMP 'target', placed every frame from camera_path by 'camera_tick'
#   Render TOP 'render' -> out1

root = op('/project1')


def X(par, e):
    par.expr = e
    par.mode = ParMode.EXPRESSION


V = op.Visuals
old = V.op('oak3d')
if old:
    old.destroy()
M = V.create(baseCOMP, 'oak3d')
M.nodeX, M.nodeY = 800, -400
M.comment = ('INHABITOR v1 (3D): the oak as instanced particles in space. Vitality (op.Metabolism) assembles it '
             'from the roots outward and dissolves it back; breath lights it; the camera walks camera_path.')

pg = M.appendCustomPage('Oak 3D')
pg.appendFile('Data')
pg.appendFloat('Vitalitygain', label='Vitality Gain')
pg.appendFloat('Previewgrowth', label='Preview Growth (-1 = live)')
pg.appendFloat('Pointsize', label='Particle Size')
pg.appendFloat('Drift', label='Drift (unassembled)')
pg.appendToggle('Freecam', label='Free Camera (ignore path)')
pg2 = M.appendCustomPage('Camera')
for n_, lbl in (('Centerx', 'Orbit Center X'), ('Centery', 'Orbit Center Y'), ('Centerz', 'Orbit Center Z')):
    pg2.appendFloat(n_, label=lbl)
pg2.appendFloat('Portraitpull', label='Portrait Step-back')   # 1 = none; 1.35 = 35% farther in 9:16
for p_, v in (('Data', 'Assets/oak3d/tree3d.npz'), ('Vitalitygain', 1.45), ('Previewgrowth', -1.0),
              ('Pointsize', 0.0032), ('Drift', 0.08), ('Freecam', False),
              ('Centerx', -0.27), ('Centery', 0.41), ('Centerz', -0.18), ('Portraitpull', 1.35)):
    M.par[p_] = v
    M.par[p_].default = v


def mk(typ, name, x, y):
    o = M.create(typ, name)
    o.nodeX, o.nodeY = x, y
    return o


bus = mk(selectCHOP, 'bus', -900, 300)
X(bus.par.chops, "op.Bus.op('out')")
met = mk(selectCHOP, 'metabolism', -900, 150)
X(met.par.chops, "op.Metabolism.op('out')")

# ---- one-time load: npz -> two float textures ----
loader = mk(textDAT, 'loader', -900, 0)
loader.text = '''# Script TOP callbacks shared by 'home' and 'colors'.
# Loads the point cloud once (cached in a module-level dict, NOT COMP storage: storage is saved into the
# .toe and would add ~4 MB to every save) and hands it to the GPU as float textures:
#   home   = (x, y, z, growth order)      colors = (r, g, b, kind)
# One pixel = one particle. Unused pixels get growth 2.0 so they never appear.
import numpy as np

_CACHE = {}   # COMP path -> (data file, home, colors, count); rebuilt after a restart, never saved

def onSetupParameters(scriptOp):
    return

def onCook(scriptOp):
    M = scriptOp.parent()
    key = M.par.Data.eval()
    cache = _CACHE.get(M.path)
    if cache is None or cache[0] != key:
        d = np.load(project.folder + '/' + key)
        xyz, rgb, g, k = d['xyz'], d['rgb'], d['growth'], d['kind']
        n = len(xyz)
        W = 512
        H = (n + W - 1) // W
        home = np.zeros((H * W, 4), np.float32)
        home[:n, :3] = xyz
        home[:n, 3] = g
        home[n:, 3] = 2.0
        col = np.zeros((H * W, 4), np.float32)
        col[:n, :3] = rgb
        col[:n, 3] = k
        cache = (key, home.reshape(H, W, 4), col.reshape(H, W, 4), n)
        _CACHE[M.path] = cache
        M.store('count', n)
    scriptOp.copyNumpyArray(cache[1] if scriptOp.name == 'home' else cache[2])
    return
'''
for nm, y in (('home', -150), ('colors', -300)):
    st = mk(scriptTOP, nm, -700, y)
    for d in list(st.docked):
        d.destroy()
    st.par.callbacks = 'loader'
    st.par.format = 'rgba32float'

# ---- per-frame particle animation on the GPU ----
anim_src = mk(textDAT, 'animate_pixel', -700, -500)
anim_src.text = '''// animate: one pixel = one particle.  in: home (xyz, growth order)  out: (xyz, scale)
uniform vec4 uA;   // time, front (vitality*gain), drift amount, particle size
uniform vec4 uB;   // breath, kick_hit, snare_hit, hats
out vec4 fragColor;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void main() {
    ivec2 ij = ivec2(gl_FragCoord.xy);
    vec4 h = texelFetch(sTD2DInputs[0], ij, 0);
    vec3 home = h.xyz;
    float g = h.w;                                  // growth order: 0 at the roots -> 1 at the tips
    float t = uA.x;
    float front = uA.y * 1.1 - 0.05;
    float a = smoothstep(g - 0.02, g + 0.05, front);   // assembled 0..1

    vec2 id = vec2(ij);
    float h1 = hash(id), h2 = hash(id + 17.31), h3 = hash(id + 41.7);
    vec3 drift = vec3(sin(t * 0.6 + h1 * 6.283 + h3 * 9.0),
                      cos(t * 0.5 + h2 * 6.283),
                      sin(t * 0.45 + h3 * 6.283 + h1 * 3.0)) * uA.z;
    vec3 jolt = normalize(vec3(h1 - 0.5, h2 - 0.5, h3 - 0.5) + 1e-3) * 0.012 * uB.z;   // snare shakes
    vec3 pos = home + drift * (1.0 - a)        // unassembled particles drift as dust
             + drift * 0.06 * uB.w            // cymbals shimmer
             + jolt * a;

    float trunk = 1.0 - smoothstep(0.12, 0.25, g);    // near the roots
    float sc = uA.w * mix(0.3, 1.0, a) * (1.0 + 0.7 * uB.y * trunk) * (0.75 + 0.5 * h3);
    if (g > 1.5) sc = 0.0;                            // padding pixels
    fragColor = vec4(pos, sc);
}
'''
anim = mk(glslTOP, 'animate', -450, -150)
for d in list(anim.docked):
    if d.name.endswith(('_pixel', '_compute')):
        d.destroy()
anim.par.pixeldat = 'animate_pixel'
anim.par.tops = 'home'
anim.par.outputresolution = 'custom'          # inputs given by name (TOPs par) don't set the size: match 'home'
X(anim.par.resolutionw, "op('home').width")
X(anim.par.resolutionh, "op('home').height")
anim.par.format = 'rgba32float'
anim.seq.vec.numBlocks = 2
G = "op('metabolism')"
B = "op('bus')"
uni = [('uA', ["op.Show.op('clock')['songtime']",
               "parent().par.Previewgrowth if parent().par.Previewgrowth >= 0 else min(1.0, " + G
               + "['vitality'] * parent().par.Vitalitygain)",
               'parent().par.Drift', 'parent().par.Pointsize']),
       ('uB', [G + "['breath']", B + "['kick_hit']", B + "['snare_hit']", B + "['hats']"])]
for i, (nm, exprs) in enumerate(uni):
    anim.par['vec%dname' % i] = nm
    for c, e in zip('xyzw', exprs):
        X(anim.par['vec%dvalue%s' % (i, c)], e)

# ---- the instanced geometry ----
geo = mk(geometryCOMP, 'tree', -150, -150)
for c in list(geo.children):
    c.destroy()
sph = geo.create(sphereSOP, 'particle')
sph.par.type = 'poly'
sph.par.rows = 4
sph.par.cols = 6
sph.par.radx = sph.par.rady = sph.par.radz = 1.0
sph.render = True
sph.display = True
geo.par.instancing = True
X(geo.par.instanceop, "op('animate')")      # a COMP's own parameters resolve from its parent's network
geo.par.instancecountmode = 'oplength'
geo.par.instancetx, geo.par.instancety, geo.par.instancetz = 'r', 'g', 'b'
geo.par.instancesx = geo.par.instancesy = geo.par.instancesz = 'a'
X(geo.par.instancecolorop, "op('colors')")
geo.par.instancecolormode = 'replace'
geo.par.instancer, geo.par.instanceg, geo.par.instanceb = 'r', 'g', 'b'

mat = mk(constantMAT, 'mat', -150, -350)
for c_ in ('colorr', 'colorg', 'colorb'):
    try:
        X(mat.par[c_], "0.85 + 0.9 * op('metabolism')['breath']")      # breath lights the tree
    except Exception:
        pass
X(geo.par.material, "op('mat')")

# ---- camera, target, light-free render ----
target = mk(nullCOMP, 'target', -150, 150)
cam = mk(cameraCOMP, 'cam', 50, 150)
X(cam.par.lookat, "op('target')")
render = mk(renderTOP, 'render', 250, -150)
render.par.camera = 'cam'
render.par.geometry = 'tree'
render.par.outputresolution = 'custom'
X(render.par.resolutionw, 'op.Config.par.Width')
X(render.par.resolutionh, 'op.Config.par.Height')
render.par.bgcolorr, render.par.bgcolorg, render.par.bgcolorb, render.par.bgcolora = 0.025, 0.03, 0.045, 1
try:
    render.par.antialias = 'aa4'
except Exception:
    pass
out1 = mk(outTOP, 'out1', 450, -150)
out1.inputConnectors[0].connect(render)

# ---- the walk: a table of keyframes in polar form around the tree ----
path = mk(tableDAT, 'camera_path', -900, -700)
path.clear()
rows = [
    ['t', 'angle', 'radius', 'height', 'look_y', 'fov', 'note'],
    ['0', '0', '5.2', '0.45', '0.40', '24', 'front, far: the photo as you know it; the seed appears'],
    ['28', '0', '4.9', '0.45', '0.40', '24', 'growing toward full bloom (1970s)'],
    ['48', '8', '3.0', '0.38', '0.38', '30', 'full bloom: the walker notices and approaches'],
    ['68', '50', '2.3', '0.30', '0.40', '36', 'stepping around to the left'],
    ['88', '110', '2.2', '0.22', '0.42', '40', 'side view: the limbs reach toward you'],
    ['108', '180', '2.4', '0.35', '0.40', '38', 'behind the tree (chorus 2)'],
    ['126', '250', '1.5', '0.08', '0.55', '48', 'low, under the canopy, looking up as it thins'],
    ['144', '320', '2.6', '0.30', '0.40', '36', 'coming back around'],
    ['157', '360', '4.6', '0.45', '0.40', '26', 'stepping back to the front: what is left'],
]
for r in rows:
    path.appendRow(r)
path.comment = 'THE WALK. t = song seconds; angle = degrees around the tree (0 = front); radius/height in tree units.'

tick = mk(executeDAT, 'camera_tick', -900, -500)
tick.par.framestart = True
tick.text = '''# Places the camera every frame from camera_path (Catmull-Rom through the keys, in polar form, so the
# walk curves around the tree instead of cutting across it). Driven by the show clock: follows Pause/Restart.
import math

def _keys(tbl):
    cols = [c.val for c in tbl.row(0)]
    rows = []
    for r in range(1, tbl.numRows):
        rows.append({c: float(tbl[r, c].val) for c in cols if c != 'note'})
    return rows

def _cr(p0, p1, p2, p3, u):
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u)

def onFrameStart(frame):
    M = me.parent()
    if M.par.Freecam.eval():
        return
    keys = _keys(M.op('camera_path'))
    t = op.Show.op('clock')['songtime'].eval()
    i = 0
    while i < len(keys) - 2 and t > keys[i + 1]['t']:
        i += 1
    k0, k1, k2, k3 = keys[max(i - 1, 0)], keys[i], keys[i + 1], keys[min(i + 2, len(keys) - 1)]
    u = min(1.0, max(0.0, (t - k1['t']) / max(1e-6, k2['t'] - k1['t'])))
    v = {f: _cr(k0[f], k1[f], k2[f], k3[f], u) for f in ('angle', 'radius', 'height', 'look_y', 'fov')}
    cx, cy, cz = M.par.Centerx.eval(), M.par.Centery.eval(), M.par.Centerz.eval()
    a = math.radians(v['angle'])
    cam, tgt = M.op('cam'), M.op('target')
    # Format-aware: the table's fov is a HORIZONTAL fov designed for 16:9. Keep the same VERTICAL view in
    # every format (landscape unchanged), and step back in portrait so more of the tree's width fits.
    W, H = op.Config.par.Width.eval(), op.Config.par.Height.eval()
    aspect = W / max(1.0, H)
    portrait = min(1.0, max(0.0, (16 / 9 - aspect) / (16 / 9 - 9 / 16)))
    radius = v['radius'] * (1.0 + (M.par.Portraitpull.eval() - 1.0) * portrait)
    vfov = 2 * math.degrees(math.atan(math.tan(math.radians(v['fov']) / 2) / (16 / 9)))
    cam.par.tx = cx + radius * math.sin(a)
    cam.par.tz = cz + radius * math.cos(a)
    cam.par.ty = v['height']
    tgt.par.tx, tgt.par.ty, tgt.par.tz = cx, v['look_y'], cz
    cam.par.viewanglemethod = 'vertfov'
    cam.par.fov = vfov
    return
'''

# ---- register the scene ----
OUT = op.Output
sc = OUT.op('scenes')
if 'oak3d' not in ' '.join(sc[r, 'top'].val for r in range(1, sc.numRows)):
    sc.appendRow(['Oak · 3D Walk', '/project1/visuals/oak3d/out1'])
OUT.op('scene_build').run()
op.Show.par.Scene.menuIndex = len(op.Show.par.Scene.menuNames) - 1

for o in (M.op('home'), M.op('colors'), anim, render):
    o.cook(force=True)
oak3d_report = {
    'count': M.fetch('count', None),
    'home': [M.op('home').width, M.op('home').height],
    'animate_warn': anim.warnings(),
    'errors': {o.path: o.errors() for o in M.findChildren() if o.errors()},
    'warnings': {o.path: o.warnings() for o in M.findChildren() if o.warnings()},
    'scenes': list(op.Show.par.Scene.menuLabels),
}
