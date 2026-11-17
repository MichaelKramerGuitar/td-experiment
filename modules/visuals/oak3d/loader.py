# Script TOP callbacks shared by 'home' and 'colors'.
# Loads the point cloud once (cached in the COMP's storage) and hands it to the GPU as float textures:
#   home   = (x, y, z, growth order)      colors = (r, g, b, kind)
# One pixel = one particle. Unused pixels get growth 2.0 so they never appear.
import numpy as np

def onSetupParameters(scriptOp):
    return

def onCook(scriptOp):
    M = scriptOp.parent()
    key = M.par.Data.eval()
    cache = M.fetch('cache', None)
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
        M.store('cache', cache)
        M.store('count', n)
    scriptOp.copyNumpyArray(cache[1] if scriptOp.name == 'home' else cache[2])
    return
