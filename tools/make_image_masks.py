"""
make_image_masks.py — turn a photo into the "instrument masks" the image scenes use.

Outputs (all fitted/cropped to --width x --height, default 1280x720):
  <name>_photo.png     the photo
  <name>_masks_a.png   R = trunk   G = branches   B = light (bright, low-saturation gaps / sky)
  <name>_masks_b.png   R = shadow  G = foliage    B = detail (saturated colour + fine edges)
  <name>_growth16.png  16-bit growth field: 0 at the seed (trunk base) -> 1 farthest along the structure

The "structure" (trunk + branches) is found as: darker than its neighbourhood, not green, then the
largest connected component. Growth distance is geodesic: measured *along* the structure from the seed,
so the reveal travels up the trunk and out the branches instead of spreading in a circle.

Usage:
  pip install opencv-python scikit-image numpy
  python tools/make_image_masks.py photo.jpg --seed 478,455 --out Assets/oak --name oak
  (--seed is the trunk base in ORIGINAL image pixels: x,y. Open the photo in any viewer to find it.)

Re-tune for a new photo with: --dark (local darkness threshold), --trunk (trunk length in px along the
structure), and check the preview sheet written next to the outputs (<name>_preview.png).
"""
import argparse
import os

import cv2
import numpy as np
from skimage.graph import MCP_Geometric


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('--seed', required=True, help='trunk base x,y in original image pixels')
    ap.add_argument('--out', default='.')
    ap.add_argument('--name', default='scene')
    ap.add_argument('--width', type=int, default=1280)
    ap.add_argument('--height', type=int, default=720)
    ap.add_argument('--dark', type=float, default=0.03, help='how much darker than surroundings counts as structure')
    ap.add_argument('--trunk', type=float, default=150, help='trunk length along the structure (original px)')
    a = ap.parse_args()

    im = cv2.imread(a.image)
    h, w = im.shape[:2]
    sx, sy = [int(v) for v in a.seed.split(',')]
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
    H, S, V = hsv[..., 0], hsv[..., 1] / 255, hsv[..., 2] / 255
    L = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32) / 255

    # --- structure (trunk + branches) ---
    greenish = (H > 28) & (H < 95) & (S > 0.30)
    dark = L < cv2.GaussianBlur(L, (0, 0), 18) - a.dark
    m = (dark & ~greenish).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    tree = lab == big

    # seed = nearest structure pixel to the requested point
    ys, xs = np.nonzero(tree)
    i = int(np.argmin((xs - sx) ** 2 + (ys - sy) ** 2))
    seed = (int(ys[i]), int(xs[i]))

    # --- geodesic growth field ---
    geo, _ = MCP_Geometric(np.where(tree, 1.0, 1e6)).find_costs([seed])
    geo_t = np.where(tree, geo, np.nan)
    gmax = np.nanpercentile(geo_t, 99.5)
    dist, lbl = cv2.distanceTransformWithLabels((~tree).astype(np.uint8), cv2.DIST_L2, 5,
                                                labelType=cv2.DIST_LABEL_PIXEL)
    near = np.zeros(lbl.max() + 1, np.float32)
    near[lbl[tree]] = np.nan_to_num(geo_t[tree], nan=gmax)
    field = np.where(tree, np.nan_to_num(geo_t, nan=gmax), near[lbl] + dist * 0.8)
    field = np.clip(field / (gmax * 1.15), 0, 1)

    trunk = (tree & (geo < a.trunk)).astype(np.float32)
    branches = (tree & ~(trunk > 0)).astype(np.float32)

    # --- light / shadow / foliage / detail ---
    light = np.clip((V - 0.78) / 0.17, 0, 1) * np.clip((0.35 - S) / 0.25, 0, 1)
    shadow = np.clip((0.42 - L) / 0.25, 0, 1)
    foliage = ((H > 28) & (H < 95) & (S > 0.28)).astype(np.float32)
    gx, gy = cv2.Sobel(L, cv2.CV_32F, 1, 0), cv2.Sobel(L, cv2.CV_32F, 0, 1)
    edge = np.clip(np.hypot(gx, gy) * 2.0, 0, 1)
    detail = np.clip(np.maximum((S - 0.42) / 0.3, edge * 0.7) * (1 - light), 0, 1)

    def soft(x, s):
        return cv2.GaussianBlur(x.astype(np.float32), (0, 0), s)

    def fit(x):  # "cover" fit: scale to fill, centre-crop
        sc = max(a.width / w, a.height / h)
        r = cv2.resize(x, (int(round(w * sc)), int(round(h * sc))), interpolation=cv2.INTER_CUBIC)
        y0 = (r.shape[0] - a.height) // 2
        x0 = (r.shape[1] - a.width) // 2
        return r[y0:y0 + a.height, x0:x0 + a.width]

    A = np.dstack([fit(np.clip(soft(light, 3) * 1.3, 0, 1)), fit(soft(branches, 1.5)), fit(soft(trunk, 2))])  # BGR
    B = np.dstack([fit(soft(detail, 1.2)), fit(soft(foliage, 3)), fit(soft(shadow, 4))])
    os.makedirs(a.out, exist_ok=True)
    p = lambda s: os.path.join(a.out, '%s_%s' % (a.name, s))
    cv2.imwrite(p('photo.png'), fit(im))
    cv2.imwrite(p('masks_a.png'), (np.clip(A, 0, 1) * 255).astype(np.uint8))
    cv2.imwrite(p('masks_b.png'), (np.clip(B, 0, 1) * 255).astype(np.uint8))
    g16 = fit(soft(field, 2))
    cv2.imwrite(p('growth16.png'), (np.clip(g16, 0, 1) * 65535).astype(np.uint16))
    prev = np.vstack([np.hstack([fit(im), (np.clip(A, 0, 1) * 255).astype(np.uint8)]),
                      np.hstack([(np.clip(B, 0, 1) * 255).astype(np.uint8),
                                 cv2.cvtColor((g16 * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)])])
    cv2.imwrite(p('preview.png'), cv2.resize(prev, None, fx=0.5, fy=0.5))
    print('wrote', a.out, 'seed', seed, 'structure px', int(tree.sum()))


if __name__ == '__main__':
    main()
