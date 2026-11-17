# Places the camera every frame from camera_path (Catmull-Rom through the keys, in polar form, so the
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
