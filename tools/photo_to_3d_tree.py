"""
photo_to_3d_tree.py — PROTOTYPE: lift the tree in a photo into a 3D point cloud.

Idea: from the front, the 3D tree should look exactly like the photo; from any other angle it should be a
plausible tree (invented, but consistent). Steps:
  1. tree mask (same method as make_image_masks.py) -> skeleton (centre lines of trunk + branches)
  2. skeleton -> graph, walked outward from the trunk base: each pixel knows its parent, its distance
     along the tree from the roots (= growth order), and its branch
  3. depth: the trunk is planar; at every fork each child branch gets its own out-of-photo slope, so
     branches fan forward/backward in 3D while keeping their exact x/y from the photo
  4. volume: points scattered inside each branch's radius (from the distance transform)
  5. canopy: foliage pixels from the photo become points placed in depth around the nearest branch
  6. every point keeps its photo colour and its growth distance

Output: an .npz with xyz, rgb, growth (0..1), kind (0 trunk/branch, 1 canopy) + preview renders.
Usage: python tools/photo_to_3d_tree.py photo.png --seed 478,455 --out _snapshots/tree3d
"""
import argparse
import os
from collections import deque

import cv2
import numpy as np
from skimage.morphology import skeletonize


def tree_mask(im, dark_thr=0.03):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
    H, S = hsv[..., 0], hsv[..., 1] / 255
    L = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32) / 255
    greenish = (H > 28) & (H < 95) & (S > 0.30)
    dark = L < cv2.GaussianBlur(L, (0, 0), 18) - dark_thr
    m = (dark & ~greenish).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    foliage = ((H > 28) & (H < 95) & (S > 0.28))
    return lab == big, foliage


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('--seed', required=True)
    ap.add_argument('--out', default='tree3d')
    ap.add_argument('--depth', type=float, default=60, help='max limb angle (degrees) away from the photo plane')
    ap.add_argument('--rng', type=int, default=7)
    a = ap.parse_args()
    rng = np.random.default_rng(a.rng)

    im = cv2.imread(a.image)
    h, w = im.shape[:2]
    tree, foliage = tree_mask(im)
    radius = cv2.distanceTransform(tree.astype(np.uint8), cv2.DIST_L2, 5)
    skel = skeletonize(tree)

    # --- skeleton graph, BFS from the trunk base ---
    sx, sy = [int(v) for v in a.seed.split(',')]
    ys, xs = np.nonzero(skel)
    i0 = int(np.argmin((xs - sx) ** 2 + (ys - sy) ** 2))
    root = (int(ys[i0]), int(xs[i0]))
    dist = np.full((h, w), -1.0, np.float32)
    ang = np.zeros((h, w), np.float32)          # compass direction of the limb this pixel belongs to
    dist[root] = 0
    q = deque([root])
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    order = []
    lim = np.radians(a.depth)                   # max limb angle away from the photo plane
    while q:
        y, x = q.popleft()
        order.append((y, x))
        kids = []
        for dy, dx in nb:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and skel[yy, xx] and dist[yy, xx] < 0:
                dist[yy, xx] = dist[y, x] + (1.414 if dy and dx else 1.0)
                kids.append((yy, xx))
        fork = len(kids) > 1
        for (yy, xx) in kids:
            if fork and dist[y, x] > 40:
                # a new limb: main limbs (near the trunk) get any direction, later forks stay close to the parent
                spread = lim if dist[y, x] < 260 else np.radians(18)
                ang[yy, xx] = np.clip(ang[y, x] + rng.uniform(-spread, spread), -lim, lim)
            else:
                ang[yy, xx] = ang[y, x]
            q.append((yy, xx))
    # Keep x exactly as in the photo (= r cos(theta)); depth z = x_offset * tan(theta).
    # Upright branches (small x reach) also lean a little in depth.
    yy_, xx_ = np.mgrid[0:h, 0:w]
    zmap = (xx_ - root[1]) * np.tan(ang) + (root[0] - yy_) * 0.35 * np.sin(ang)
    reached = dist >= 0
    dmax = dist[reached].max()

    # --- branch volume points ---
    pts, cols, grow, kind = [], [], [], []
    for (y, x) in order:
        r = max(1.0, radius[y, x])
        n = int(min(40, 1 + r * r * 0.35))
        off = rng.normal(0, 1, (n, 3))
        off /= np.linalg.norm(off, axis=1, keepdims=True) + 1e-9
        off *= rng.uniform(0, 1, (n, 1)) ** 0.5 * r
        p = np.array([x, y, zmap[y, x]]) + off
        pts.append(p)
        px = np.clip(p[:, 0].astype(int), 0, w - 1)
        py = np.clip(p[:, 1].astype(int), 0, h - 1)
        cols.append(im[py, px][:, ::-1] / 255.0)
        grow.append(np.full(n, dist[y, x] / dmax))
        kind.append(np.zeros(n))

    # --- canopy: foliage pixels placed in depth around their nearest branch ---
    near_d, near_lbl = cv2.distanceTransformWithLabels((~skel).astype(np.uint8), cv2.DIST_L2, 5,
                                                       labelType=cv2.DIST_LABEL_PIXEL)
    lab_z = np.zeros(near_lbl.max() + 1, np.float32)
    lab_g = np.zeros(near_lbl.max() + 1, np.float32)
    sk_lbl = near_lbl[skel]
    lab_z[sk_lbl] = zmap[skel]
    lab_g[sk_lbl] = np.where(reached[skel], dist[skel] / dmax, 1.0)
    fy, fx = np.nonzero(foliage & ~tree & (near_d < 90))
    keep = rng.random(len(fy)) < 0.35
    fy, fx = fy[keep], fx[keep]
    dd = near_d[fy, fx]
    fz = lab_z[near_lbl[fy, fx]] + rng.normal(0, 1, len(fy)) * (8 + dd * 0.8)
    pts.append(np.stack([fx + rng.uniform(-.5, .5, len(fx)), fy + rng.uniform(-.5, .5, len(fy)), fz], 1))
    cols.append(im[fy, fx][:, ::-1] / 255.0)
    grow.append(np.clip(lab_g[near_lbl[fy, fx]] + dd / dmax * 0.6, 0, 1))
    kind.append(np.ones(len(fy)))

    xyz = np.concatenate(pts).astype(np.float32)
    rgb = np.concatenate(cols).astype(np.float32)
    growth = np.concatenate(grow).astype(np.float32)
    kinds = np.concatenate(kind).astype(np.uint8)
    # centre on trunk base, y up, unit scale = image height
    xyz[:, 0] -= root[1]
    xyz[:, 1] = root[0] - xyz[:, 1]
    xyz /= h
    os.makedirs(a.out, exist_ok=True)
    np.savez_compressed(os.path.join(a.out, 'tree3d.npz'), xyz=xyz, rgb=rgb, growth=growth, kind=kinds)
    print('points', len(xyz), 'branch', int((kinds == 0).sum()), 'canopy', int((kinds == 1).sum()),
          'depth range', float(xyz[:, 2].min()), float(xyz[:, 2].max()))

    # --- previews: orbit around the tree ---
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 4, figsize=(20, 5.4), facecolor='#0b0c10')
    for ax, ang, title in zip(axs, (0, 30, 60, 90), ('front (= the photo)', 'walking around: 30°', '60°', 'side: 90°')):
        t = np.radians(ang)
        X = xyz[:, 0] * np.cos(t) + xyz[:, 2] * np.sin(t)
        Z = -xyz[:, 0] * np.sin(t) + xyz[:, 2] * np.cos(t)
        o = np.argsort(Z)                                # painter's order: far first
        ax.scatter(X[o], xyz[o, 1], c=np.clip(rgb[o] * 1.3, 0, 1), s=0.35, linewidths=0)
        ax.set_facecolor('#0b0c10'); ax.set_aspect('equal'); ax.axis('off')
        ax.set_title(title, color='w')
        ax.set_xlim(np.percentile(X, 0.5) - 0.05, np.percentile(X, 99.5) + 0.05); ax.set_ylim(-0.05, 0.75)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, 'tree3d_orbit.png'), dpi=110, facecolor='#0b0c10')


if __name__ == '__main__':
    main()
