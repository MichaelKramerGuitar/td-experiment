# externalize_modules.py
# Saves each module as its own .tox (Common > External .tox) and syncs shaders / scripts / tables to files,
# so the project is diffable in git and modules can be reused in other projects.
# Run inside TouchDesigner:
#   exec(open(project.folder + '/scripts/externalize_modules.py', encoding='utf-8').read())
# Safe to re-run: it just re-saves everything. Afterwards save the project (Ctrl+S).
import os

F = project.folder


def write_and_sync(dat, rel):
    """Make the DAT sync with file `rel`, writing the DAT's content there first if needed.

    Lesson learned (2026-11-17): a synced DAT can re-read its file when its .text is accessed. Opening the
    file for writing truncates it, so reading dat.text *after* open() returned the empty file and wiped
    the DAT. So: (1) skip DATs already synced to this file, (2) read the text BEFORE opening the file,
    (3) never write an empty DAT over a non-empty file.
    """
    path = os.path.join(F, rel)
    if dat.par.syncfile.eval() and dat.par.file.eval() == rel and os.path.exists(path):
        return False
    text = dat.text                                   # read first
    if not text.strip() and os.path.exists(path) and os.path.getsize(path) > 1:
        raise RuntimeError('refusing to overwrite %s with an empty DAT (%s)' % (rel, dat.path))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text if text.endswith('\n') else text + '\n')
    dat.par.file = rel
    dat.par.syncfile = True
    return True


V = op.Visuals
SYNC = [
    # shaders
    (V.op('prism_bloom/bloom_pixel'), 'modules/visuals/prism_bloom/bloom_pixel.frag'),
    (V.op('oak_paint/pixel'), 'modules/visuals/oak_paint/pixel.frag'),
    (V.op('oak_particles/pixel'), 'modules/visuals/oak_particles/pixel.frag'),
    # per-project data tables
    (op.Source.op('stem_map'), 'config/stem_map.tsv'),
    (op.Output.op('scenes'), 'config/scenes.tsv'),
    # python callbacks / generators
    (op.Source.op('build'), 'modules/sources/stems_in/build.py'),
    (op.Source.op('controls'), 'modules/sources/stems_in/controls.py'),
    (op.Analysis.op('growth_tick'), 'modules/analysis/analysis/growth_tick.py'),
    (op.Analysis.op('controls'), 'modules/analysis/analysis/controls.py'),
    (op.Show.op('actions'), 'modules/control/show_control/actions.py'),
    (op.Show.op('status_tick'), 'modules/control/show_control/status_tick.py'),
    (op.Show.op('record_naming'), 'modules/control/show_control/record_naming.py'),
    (op.Lyrics.op('tick'), 'modules/overlays/lyrics/tick.py'),
    (op.Lyrics.op('loader'), 'modules/overlays/lyrics/loader.py'),
    (op.Output.op('scene_build'), 'project/scene_build.py'),
    # world + metabolism (explore/metabolism)
    (op.World.op('co2_in/clean').par.callbacks.eval() if op.World and op.World.op('co2_in/clean') else None,
     'modules/world/co2_in/clean_callbacks.py'),
    (op.Metabolism.op('tick') if op.Metabolism else None, 'modules/metabolism/tick.py'),
    (op.Config.op('apply'), 'project/config_apply.py'),
]
synced = []
for dat, rel in SYNC:
    if dat is not None and write_and_sync(dat, rel):
        synced.append(rel)

MODULES = [
    (op.Source, 'modules/sources/stems_in.tox'),
    (op('/project1/sources/mock_in'), 'modules/sources/mock_in.tox'),
    (op.Analysis, 'modules/analysis/analysis.tox'),
    (V.op('prism_bloom'), 'modules/visuals/prism_bloom.tox'),
    (V.op('pulse'), 'modules/visuals/pulse.tox'),
    (V.op('oak_assets'), 'modules/visuals/oak_assets.tox'),
    (V.op('oak_paint'), 'modules/visuals/oak_paint.tox'),
    (V.op('oak_particles'), 'modules/visuals/oak_particles.tox'),
    (op.Lyrics, 'modules/overlays/lyrics.tox'),
    (op.Show, 'modules/control/show_control.tox'),
    (op.World.op('co2_in') if op.World else None, 'modules/world/co2_in.tox'),
    (op.Metabolism, 'modules/metabolism/metabolism.tox'),
    (V.op('oak_metabolism'), 'modules/visuals/oak_metabolism.tox'),
]
saved = []
for comp, rel in MODULES:
    if comp is None:
        continue
    path = os.path.join(F, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    comp.par.externaltox = rel
    comp.save(path)
    saved.append(rel)

externalize_report = {'synced': synced, 'saved': saved}
