# build_oak_scenes.py
# Builds /project1/visuals/oak_assets, oak_paint and oak_particles, and registers them as scenes.
# Run inside TouchDesigner (Textport):
#   exec(open(project.folder + '/scripts/build_oak_scenes.py', encoding='utf-8').read())
# Safe to re-run: it destroys and rebuilds these three components.

V = op.Visuals
log = []


def X(par, e):
    par.expr = e
    par.mode = ParMode.EXPRESSION


# ---------- shared assets ----------
old = V.op('oak_assets')
if old:
    old.destroy()
AS = V.create(baseCOMP, 'oak_assets')
AS.nodeX, AS.nodeY = 0, -400
AS.comment = ('Image + instrument masks. masks_a: R=trunk G=branches B=light. '
              'masks_b: R=shadow G=foliage B=detail. growth: distance along tree from trunk base (0..1).')
pg = AS.appendCustomPage('Assets')
pg.appendFolder('Folder')
X(AS.par.Folder, "project.folder + '/' + op.Config.par.Imagefolder")
for i, (nm, fn) in enumerate((('photo', 'oak_photo.png'), ('masks_a', 'oak_masks_a.png'),
                              ('masks_b', 'oak_masks_b.png'), ('growth', 'oak_growth16.png'))):
    m = AS.create(moviefileinTOP, nm)
    m.nodeX, m.nodeY = 0, -i * 150
    X(m.par.file, "parent().par.Folder + '/" + fn + "'")
    if nm == 'growth':
        for fmt in ('r16fixed', 'rgba16fixed'):
            try:
                m.par.format = fmt
                break
            except Exception as e:
                log.append('fmt ' + str(e))
    o = AS.create(outTOP, 'out_' + nm)
    o.nodeX, o.nodeY = 200, -i * 150
    o.inputConnectors[0].connect(m)

COMMON = '''
uniform vec4 uA;  // songtime, growth, kick, kick_hit
uniform vec4 uB;  // snare, snare_hit, hats, ride
uniform vec4 uC;  // sub, gtr_rhythm, gtr_lead, vox
uniform vec4 uD;  // low, mid, high, master
uniform vec4 uP;  // module params (see component)
out vec4 fragColor;
// inputs: 0 photo, 1 masks_a (trunk, branches, light), 2 masks_b (shadow, foliage, detail), 3 growth field
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; } return v; }
// Aspect "cover" fit: maps output UV -> image UV so the image fills any output shape (crops, never stretches).
// uP.x = horizontal focus (0..1) = where to centre the crop when the output is narrower than the image.
vec2 coverUV(vec2 uv) {
    vec2 o = uTDOutputInfo.res.zw;
    vec2 i = uTD2DInfos[0].res.zw;
    float ro = o.x / o.y, ri = i.x / i.y;
    vec2 s = (ro > ri) ? vec2(1.0, ri / ro) : vec2(ro / ri, 1.0);
    vec2 c = vec2(clamp(uP.x, s.x * 0.5, 1.0 - s.x * 0.5), 0.5);
    return (uv - 0.5) * s + c;
}
'''

PAINT = COMMON + '''
// oak_paint: a pencil sketch on paper that is painted in as the song grows the tree.
// trunk=kick  branches=snare  light=overheads  shadow=bass(sub)  foliage=rhythm gtr  colour detail=lead gtr
void main() {
    vec2 uv = coverUV(vUV.st);
    float t = uA.x, growth = uA.y, kick = uA.z, kickHit = uA.w;
    float snare = uB.x, snareHit = uB.y, hats = uB.z, ride = uB.w;
    float sub = uC.x, gtrR = uC.y, gtrL = uC.z;
    float pastel = uP.y, sway = uP.z;

    // foliage sways with the rhythm guitar
    float fol0 = texture(sTD2DInputs[2], uv).g;
    vec2 disp = vec2(fbm(uv * 6.0 + t * 0.35) - 0.5, fbm(uv * 6.0 + 13.0 + t * 0.35) - 0.5);
    vec2 suv = uv + disp * 0.008 * sway * (0.25 + 1.6 * gtrR) * fol0;

    vec3 photo = texture(sTD2DInputs[0], suv).rgb;
    vec4 mA = texture(sTD2DInputs[1], suv);
    vec4 mB = texture(sTD2DInputs[2], suv);
    float trunk = mA.r, branch = mA.g, light = mA.b;
    float shadow = mB.r, foliage = mB.g, detail = mB.b;
    float field = texture(sTD2DInputs[3], uv).r;

    // growth front with an organic, noisy edge
    float front = growth * 1.1 - 0.05;
    float edgeN = fbm(uv * 9.0) * 0.07;
    float reveal = smoothstep(field + edgeN - 0.03, field + edgeN + 0.03, front);   // 1 once the front has passed
    float band = smoothstep(0.04, 0.0, abs(front - (field + edgeN)));

    vec3 col = photo;
    float lum = dot(col, vec3(0.299, 0.587, 0.114));
    col *= 1.0 + trunk * (0.25 * kick + 0.7 * kickHit);                        // trunk breathes with kick
    col += branch * vec3(1.0, 0.82, 0.62) * (0.08 * snare + 0.38 * snareHit);   // branches flash with snare
    col = mix(col, col * (0.45 + 0.55 * (1.0 - sub)), shadow * 0.85);          // bass deepens shadow (relief)
    col = mix(vec3(lum), col, 1.0 + detail * gtrL * 1.3);                      // lead gtr = colour detail
    col = mix(col, col * vec3(0.94, 1.08, 0.92), foliage * gtrR * 0.7);        // rhythm gtr = living foliage

    // overheads = sunlight: glow in light gaps + soft rays from the canopy
    float sun = clamp(hats * 0.7 + ride * 0.7, 0.0, 1.5);
    vec3 sunc = vec3(1.0, 0.93, 0.78);
    col += sunc * light * sun * 0.55;
    vec2 sunPos = vec2(0.32, 1.1);
    vec2 dir = (sunPos - uv) / 18.0; vec2 q = uv; float rays = 0.0;
    for (int i = 0; i < 18; i++) { q += dir; rays += texture(sTD2DInputs[1], q).b; }
    col += sunc * (rays / 18.0) * sun * 0.5;

    // pastel grade: lifted blacks, softened contrast, slight lilac in the shadows
    vec3 past = pow(clamp(col, 0.0, 2.0), vec3(0.78)) * 0.82 + vec3(0.11, 0.10, 0.13);
    col = mix(col, past, pastel);

    // unrevealed: graphite sketch on warm paper
    vec3 paper = vec3(0.96, 0.94, 0.89) - fbm(uv * 55.0) * 0.05;
    float g = length(vec2(dFdx(lum), dFdy(lum))) * 7.0;
    float ink = clamp(g * 0.9 + (trunk + branch) * 0.18, 0.0, 1.0);
    vec3 sketch = paper - vec3(0.42, 0.40, 0.37) * ink * (0.35 + 0.65 * growth);
    col = mix(sketch, col, reveal);
    col += vec3(1.0, 0.86, 0.62) * band * (0.25 + 0.35 * kick);               // living edge of growth

    float vig = smoothstep(1.15, 0.35, length((vUV.st - 0.5) * vec2(1.4, 1.0)));
    col *= mix(0.82, 1.0, vig);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
'''

PART = COMMON + '''
// oak_particles: the scene assembles from drifting points of light as the song grows it.
void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 px = vUV.st * res;
    float t = uA.x, growth = uA.y, kick = uA.z, kickHit = uA.w;
    float snare = uB.x, snareHit = uB.y, hats = uB.z, ride = uB.w;
    float sub = uC.x, gtrR = uC.y, gtrL = uC.z;
    float cs = max(uP.y, 3.0);            // cell size in pixels
    float spread = uP.z;                  // drift amount (cells)
    float front = growth * 1.1 - 0.05;

    vec2 cell = floor(px / cs);
    vec3 acc = vec3(0.0);
    for (int j = -2; j <= 2; j++) {
        for (int i = -2; i <= 2; i++) {
            vec2 c = cell + vec2(i, j);
            float h1 = hash(c), h2 = hash(c + 17.31), h3 = hash(c + 41.7);
            vec2 home = (c + vec2(h1, h2)) * cs;
            vec2 huv = coverUV(home / res);
            vec3 pc = texture(sTD2DInputs[0], huv).rgb;
            vec4 mA = texture(sTD2DInputs[1], huv);
            vec4 mB = texture(sTD2DInputs[2], huv);
            float field = texture(sTD2DInputs[3], huv).r;
            float a = smoothstep(field - 0.02, field + 0.05, front);          // assembled 0..1

            vec2 drift = vec2(sin(t * 0.7 + h3 * 6.283 + h1 * 9.0), cos(t * 0.55 + h2 * 6.283)) * cs * spread;
            vec2 kickDir = normalize(vec2(h1 - 0.5, h2 - 0.5) + 1e-3);
            vec2 pos = home + drift * (1.0 - a)
                     + kickDir * cs * 0.9 * snareHit * mA.g                    // snare shakes the branches
                     + drift * 0.12 * hats;                                    // cymbals shimmer
            float lum = dot(pc, vec3(0.3, 0.59, 0.11));
            float treeness = clamp(mA.r + mA.g, 0.0, 1.0);
            float rad = cs * (0.28 + 0.22 * lum + 0.16 * treeness)
                      * (1.0 + mA.r * (0.6 * kickHit + 0.25 * kick))           // trunk swells with kick
                      * mix(0.5, 1.0, a)
                      * (1.0 - 0.35 * mB.r * sub);                             // bass pulls shadow points in
            float d = length(px - pos);
            float dotv = smoothstep(rad, rad * 0.35, d);

            vec3 col = pow(pc, vec3(0.8)) * 1.25 + 0.04;
            col = mix(col, col * vec3(1.18, 1.0, 0.82) + vec3(0.10, 0.07, 0.03), treeness * 0.7);  // warm bark points
            col = mix(vec3(dot(col, vec3(0.3, 0.59, 0.11))), col, 0.65 + mB.b * gtrL * 1.1 + mB.g * gtrR * 0.6);
            col += vec3(1.0, 0.93, 0.78) * mA.b * (hats + ride) * 0.7;          // sunlit points
            float alpha = mix(0.32, 1.0, a) * (0.8 + 0.2 * h3);
            acc = max(acc, col * dotv * alpha);
        }
    }
    vec3 bg = vec3(0.025, 0.03, 0.045) + texture(sTD2DInputs[0], coverUV(vUV.st)).rgb * 0.05 * growth;
    vec3 col = max(acc, bg);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
'''


def build_scene(name, frag_text, params, comment, x):
    old = V.op(name)
    if old:
        old.destroy()
    M = V.create(baseCOMP, name)
    M.nodeX, M.nodeY = x, -400
    M.comment = comment
    pg = M.appendCustomPage('Scene')
    pg.appendCHOP('Bus')
    pg.appendCOMP('Assets')
    pg.appendFloat('Previewgrowth', label='Preview Growth (-1 = live)')
    pg.appendFloat('Focusx', label='Crop Focus X (0..1)')
    for (pn, lbl, v) in params:
        pg.appendFloat(pn, label=lbl)
    X(M.par.Bus, "op.Bus.op('out')")                 # global OP shortcuts: no absolute paths
    X(M.par.Assets, "op.Visuals.op('oak_assets')")
    M.par.Previewgrowth = -1
    M.par.Previewgrowth.default = -1
    M.par.Focusx = 0.62          # the trunk sits right of centre in the oak photo
    M.par.Focusx.default = 0.62
    for (pn, lbl, v) in params:
        M.par[pn] = v
        M.par[pn].default = v
    bus = M.create(selectCHOP, 'bus')
    bus.nodeX, bus.nodeY = -500, 250
    X(bus.par.chop, 'parent().par.Bus')
    fr = M.create(textDAT, 'pixel')
    fr.nodeX, fr.nodeY = -500, 400
    fr.text = frag_text
    g = M.create(glslTOP, 'render')
    g.nodeX, g.nodeY = 0, 0
    for d in list(g.docked):           # remove auto-created template DATs; we use 'pixel'
        if d.name.endswith(('_pixel', '_compute')):
            d.destroy()
    for i, nm in enumerate(('photo', 'masks_a', 'masks_b', 'growth')):
        sl = M.create(selectTOP, 'in_' + nm)
        sl.nodeX, sl.nodeY = -250, 150 - i * 110
        X(sl.par.top, "parent().par.Assets.eval().path + '/out_" + nm + "'")
    # inputs by name (no wires): sTD2DInputs[0..3] = photo, masks_a, masks_b, growth
    g.par.tops = 'in_photo in_masks_a in_masks_b in_growth'
    g.par.pixeldat = 'pixel'
    g.par.outputresolution = 'custom'
    X(g.par.resolutionw, 'op.Config.par.Width')      # output size comes from the config layer
    X(g.par.resolutionh, 'op.Config.par.Height')
    try:
        g.par.format = 'rgba16float'
    except Exception:
        pass
    g.seq.vec.numBlocks = 5
    B = "op('bus')"
    U = [('uA', ["op.Show.op('clock')['songtime']",
                 "parent().par.Previewgrowth if parent().par.Previewgrowth >= 0 else " + B + "['growth']",
                 B + "['kick']", B + "['kick_hit']"]),
         ('uB', [B + "['snare']", B + "['snare_hit']", B + "['hats']", B + "['ride']"]),
         ('uC', [B + "['sub']", B + "['gtr_rhythm']", B + "['gtr_lead']", B + "['vox']"]),
         ('uD', [B + "['low']", B + "['mid']", B + "['high']", B + "['master']"]),
         ('uP', ['parent().par.Focusx'] + ['parent().par.' + p[0] for p in params] + ['0'] * (3 - len(params)))]
    for i, (nm, exprs) in enumerate(U):
        g.par['vec%dname' % i] = nm
        for c, e in zip('xyzw', exprs):
            X(g.par['vec%dvalue%s' % (i, c)], e)
    o = M.create(outTOP, 'out1')
    o.nodeX = 200
    o.inputConnectors[0].connect(g)
    g.cook(force=True)
    return M, g


p1, g1 = build_scene('oak_paint', PAINT, [('Pastel', 'Pastel Amount', 0.65), ('Sway', 'Foliage Sway', 1.0)],
                     'Oak, painted: sketch on paper painted in by growth. trunk=kick branches=snare '
                     'light=overheads shadow=sub foliage=gtr_rhythm detail=gtr_lead', 200)
p2, g2 = build_scene('oak_particles', PART, [('Cellsize', 'Particle Spacing (px)', 6.0), ('Spread', 'Drift (cells)', 1.6)],
                     'Oak, particles: points of light assemble the scene as growth reaches them. '
                     'Same instrument mapping as oak_paint.', 400)

# register scenes
OUT = op.Output
sc = OUT.op('scenes')
for r in range(sc.numRows - 1, 0, -1):          # drop any previous oak rows, then re-add
    if 'oak_' in sc[r, 'top'].val:
        sc.deleteRow(r)
names = [sc[r, 'name'].val for r in range(1, sc.numRows)]
for nm, path in (('Oak · Painted', '/project1/visuals/oak_paint/out1'),
                 ('Oak · Particles', '/project1/visuals/oak_particles/out1')):
    if nm not in names:
        sc.appendRow([nm, path])
OUT.op('scene_build').run()

build_report = {'log': log,
                'paint': [g1.errors(), g1.warnings()],
                'particles': [g2.errors(), g2.warnings()],
                'assets': {o.name: [o.width, o.height, o.errors()] for o in AS.findChildren(type=moviefileinTOP)}}
