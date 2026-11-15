# externalize_modules.py
# Saves each module as its own .tox (Common > External .tox) and syncs shaders / scripts / tables to files,
# so the project is diffable in git and modules can be reused in other projects.
# Run inside TouchDesigner:
#   exec(open(project.folder + '/scripts/externalize_modules.py', encoding='utf-8').read())
# Safe to re-run: it just re-saves everything. Afterwards save the project (Ctrl+S).
import os

F = project.folder


def write_and_sync(dat, rel):
    """Write the DAT's current content to rel, then make the DAT sync with that file."""
    path = os.path.join(F, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(dat.text if dat.text.endswith('\n') else dat.text + '\n')
    dat.par.file = rel
    dat.par.syncfile = True


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
    (op.Config.op('apply'), 'project/config_apply.py'),
]
synced = []
for dat, rel in SYNC:
    if dat is not None:
        write_and_sync(dat, rel)
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
