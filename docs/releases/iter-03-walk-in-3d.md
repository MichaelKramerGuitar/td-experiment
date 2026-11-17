# iter-03 — Walk in 3D

*"8 Little Prayers"* · Oak · 3D Walk · World Role: **Stress** · YouTube 16:9 and Instagram 9:16 · 2:37

## What it is

The same metabolism as iter-02 — the song is the energy, 68 years of Mauna Loa CO₂ is the world, the oak
lives on the breath — but now the oak stands in space and you walk to it. It is born as the song begins
(the late 1950s), reaches full bloom around the 1970s, and you approach. You circle it while the decades
pass and the same music sustains it less and less: behind it in the second chorus, under the canopy as it
thins, and back to the front for what's left.

## How it's made

- **The tree:** ~126,000 particles, lifted from a single photograph of a New Orleans live oak. The branch
  structure is traced from the photo; each main limb is given a compass direction around the trunk, so
  from the front you see the photograph and from every other angle a plausible oak
  (`tools/photo_to_3d_tree.py`).
- **Growth and decay:** every particle knows its distance from the roots along the branches. The
  metabolism's vitality decides how far from the roots the tree is assembled; beyond that, particles
  loosen into drifting dust. Breath lights the tree; the snare shakes it; the kick swells the trunk.
- **The walk:** a table of moments in the song (`modules/visuals/oak3d/camera_path.tsv`): where the walker
  stands, how close, how high, where they look. Smoothly interpolated around the tree.
- **The world:** NOAA Global Monitoring Laboratory, Mauna Loa monthly CO₂ (March 1958 – September 2026),
  laid linearly across the song (≈ 2.3 s per year). Rising CO₂ read as *stress* is an artistic
  interpretation, not a model of real trees.

## Presenting it

Everything in `iter-02` notes applies. New angles for this one:
- *"You find a tree. You stay with it for sixty-eight years."*
- The walk is a choice of attention: the camera lingers where the loss is happening.
- For Instagram: the first frame should already say "tree + music": consider a cover still from full
  bloom (≈ 0:48).

## Technical

- Offline render (every frame), 60 fps; H.264 + stereo AAC (the song's stereo mix, verified sample-aligned
  with the render's own audio).
- YouTube: rendered 1280×720 (Non-Commercial license cap), uploaded as 1920×1080 (high-quality upscale;
  YouTube serves higher-bitrate streams for 1080p+ uploads).
- Instagram Reel: rendered 720×1280, uploaded as 1080×1920 (Instagram's recommended Reel size). The camera
  keeps the same vertical view in both formats and steps back 35% in portrait (`Portraitpull`) so the
  canopy's width fits; lyrics scale with the short side of the frame.
- Code state: tag `iter-03-walk-in-3d`.

## Credits

Music: Michael Kramer. CO₂ data: NOAA GML / Scripps Institution of Oceanography (Keeling).
Image: New Orleans live oak photograph.
