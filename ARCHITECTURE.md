# ARCHITECTURE — how this TouchDesigner project is built (and why)

Written for Michael: a software developer learning TouchDesigner. Every pattern here has a software-engineering
equivalent; I name it so you can map TouchDesigner onto what you already know.

---

## 1. The big picture: a pipeline with one contract in the middle

```
 ┌──────────── LISTEN ────────────┐        ┌──────────────── SEE ─────────────────┐
 sources/        analysis/        bus/           visuals/          output/           (screen / file)
 stems_in ──►  envelopes  ──►  ┌────────┐   ──► prism_bloom ─┐
 (live_in)     hits            │  out   │   ──► oak_paint ───┼─► scene_switch ─► lyrics_over ─► final ─► recorder
 mock_in       bands           │15 named│   ──► oak_particles┘        ▲               ▲            └──► preview_window
               growth          │signals │                             │               │
                               └────────┘                      show_control    overlays/lyrics
                                                               (Scene menu)
 config  ──► formats, fps, paths (read by everyone)      show_control ──► transport, record, status
```

Software analogy: **ports and adapters (hexagonal architecture).** The bus is the *port* (an interface).
Sources are *adapters* on the input side; visuals are *consumers*. Anything that honours the contract can be
swapped in without touching the other side.

Network folders in `/project1` are the layers. Each layer contains **modules** (Base COMPs), each module
is self-contained with its own parameters, and modules talk only through the contract, shortcuts and config.

## 2. Operator families in one paragraph

- **CHOPs** = channels of numbers over time (audio, control signals). *Streams.*
- **TOPs** = images/textures on the GPU. *Framebuffers.*
- **DATs** = text and tables (scripts, shaders, CSV/TSV). *Files / config / code.*
- **COMPs** = containers with custom parameters. *Classes / modules.*
- **SOPs** = geometry (not used yet; future plants/particles).

Data flows along wires *within* a family; you cross families with specific ops (e.g. CHOP values into a TOP via
parameter expressions or GLSL uniforms).

## 3. The contract: `op.Bus.op('out')`

15 channels, all 0..1:

| group | channels | produced by |
|---|---|---|
| envelopes | `kick snare hats ride vox gtr_lead gtr_rhythm sub master` | analysis/env |
| hits | `kick_hit snare_hit` | analysis/h_* |
| bands | `low mid high` | analysis/bands |
| growth | `growth` | analysis/growth (+ growth_tick) |

Rules: names never change meaning; values stay 0..1; new signals are *added*, never repurposed.
`bus/adapter_switch` chooses `mock_in` (fake noise, index 0) or `analysis` (index 1) — the mock is your
**test double**: build visuals with no audio running.

## 4. Module anatomy (the pattern every module follows)

```
my_module (Base COMP)          ← custom parameter page(s) = the module's public API
 ├─ bus      (Select CHOP)     ← INPUT: reads the contract via a parameter (Bus = op.Bus.op('out'))
 ├─ ... internal ops ...       ← private implementation
 ├─ pixel / build (Text DAT)   ← code (shader / generator), synced to a file in modules/
 └─ out1     (Out TOP/CHOP)    ← OUTPUT: what the outside world consumes
```

- **Custom parameters are the API.** (`appendFloat`, `appendToggle`, `appendPulse`, menus...). Internal ops read
  them with `parent().par.Name`. Anything a user might tweak is a parameter — not a value buried in a node.
- **In/Out operators are the ports.** Consumers use `module/out1`; never reach inside a module.
- **Pulses + Parameter Execute DATs = methods.** e.g. `stems_in.Restart` → `controls` DAT runs the callback.
- **Execute DAT (frame start) = the game loop.** Used for accumulators (growth), the show clock and lyrics.

## 5. Wiring without absolute paths: Global OP Shortcuts

Each key module sets **Common → Global OP Shortcut**, so anywhere in the project you can write:

| Shortcut | Module |
|---|---|
| `op.Config` | config (formats, fps, paths) |
| `op.Show` | show_control (transport, scene, clock at `op.Show.op('clock')`) |
| `op.Bus` | bus (`op.Bus.op('out')` = the contract) |
| `op.Source` | the active audio adapter (stems_in) |
| `op.Analysis`, `op.Visuals`, `op.Output`, `op.Overlays`, `op.Lyrics` | the respective layers/modules |

Software analogy: **dependency injection by name / a service locator.** Move a module anywhere in the network
(or into another project that defines the same shortcuts) and its expressions still resolve.
*Gotcha:* expressions on a COMP's **own** custom parameters are evaluated from the parent's context
(`parent()`/`me` don't point where you expect) — use `op.<Shortcut>` there.

## 6. The configuration layer: `op.Config`

| Page | Parameters |
|---|---|
| Output | **Format Preset** (from `config/resolution_presets.tsv`), Custom W/H, Width/Height (read-only, derived), Info, **Project / Record FPS**, Record Codec, Preview Window Scale |
| Paths | Stems Folder, Image Assets Folder, Lyrics Folder, Recordings Folder (relative to the project) |

Every renderer binds its resolution to `op.Config.par.Width/Height`. Image scenes use an aspect **"cover" fit**
in the shader (`coverUV()` — fill the frame, crop, never stretch) with a **Crop Focus X** parameter so a 9:16 crop
stays on the trunk. Text scales with output height. Add a format = add a row to the TSV.

## 7. Table-driven builders (data, not code, decides structure)

- `config/stem_map.tsv` (inside `stems_in`): which file feeds which bus channel → pulse **Rebuild**.
- `config/scenes.tsv` (inside `output`): scene names + which module output → re-runs `scene_build`, which also
  refreshes the Scene menu.
- `Assets/lyrics/*.tsv`: lyric line/word timing → pulse **Reload** on `overlays/lyrics`.

Software analogy: **declarative config + a generator.** Change a table, re-run the generator; no wiring by hand.
Generated ops are tagged (`stemgen`, `scenegen`) so the generator can safely delete and recreate them.

## 8. Patterns inside the modules

### 8.1 Audio → signal (analysis)
```
audio ─► Analyze (RMS) ─► Expression (to dB, normalise floor..0 → 0..1) ─► Lag (attack/release) ─► envelope
audio ─► Audio Filter ─► RMS ─► dB ─┬► fast Lag ─┐
                                    └► slow Lag ─┴► Math (fast − slow) ─► Trigger ─► hit
master ─► 3× Audio Filter (LP 200 / BP 1k / HP 4k) ─► RMS ─► dB ─► Lag ─► low/mid/high
growth += Growthrate × master × dt            (Execute DAT, every frame, clamped 0..1)
```
Why dB: loudness perception is logarithmic; linear RMS makes quiet instruments invisible.
Why fast−slow: an onset is "louder than it has recently been" — robust to overall level.

### 8.2 GLSL scenes (one fragment shader per look)
- All signals arrive as packed `vec4` uniforms (`uA..uD`), module params in `uP`. Cheap and readable.
- Images arrive by name via the GLSL TOP **TOPs** parameter (`in_photo in_masks_a ...` → `sTD2DInputs[0..3]`)
  rather than wires (scripted multi-input wiring is unreliable).
- Shaders live in DATs synced to `modules/visuals/*.frag` — edit in VS Code, TouchDesigner hot-reloads.

### 8.3 Growth field (the "unfolding")
Offline tool `tools/make_image_masks.py` finds the tree structure and computes **geodesic distance from the trunk
base** along it. In the shader: `reveal = smoothstep(field-ε, field+ε, growth)` — a pixel appears when the song's
accumulated energy reaches it. Same idea will drive plants.

### 8.4 Feedback (echoes / trails)
`Feedback TOP → Transform (expand/rotate) → Level (fade) → Composite (max) with the fresh frame`.
The loop carries last frame forward. *Gotcha:* a feedback loop keeps its resolution; bind the composite's
resolution to config and pulse the Feedback TOP's reset when the format changes.

### 8.5 Overlay (lyrics)
Text TOP (words sung so far) over a blurred black copy (shadow) → Level (fade) → `Over TOP` onto the live scene.
Driven by the show clock, so it follows Pause and Restart.

## 9. Performance, recording and formats

**Measured on your laptop (2026-11-15), Oak · Painted, 1280×720, Motion-JPEG:**

| Situation | fps avg / min | ms per frame (avg) |
|---|---|---|
| Playing | 60 / 57 | 8.7 |
| Recording @60 | 60 / 58 | 14.9 |
| Playing + preview window | 59.5 / 53 | 11.1 |
| **Recording @60 + preview window** | **45 / 31** | **28** |
| Recording @30 + preview window | 29 / steady | 11 |
| Render Full Song (offline) | — | ~5× slower than real time, every frame perfect |

At 60 fps you have **16.7 ms** per frame (at 30 fps, 33 ms). Recording alone already uses ~15 ms; adding the
second window pushes past the budget, so TouchDesigner (realtime mode) drops frames and the preview stutters.
That's what you saw. Anything else running on the machine (e.g. a video conversion) eats the same budget — we
measured recording dropping to ~19 fps while ffmpeg was busy. MJPEG@60 writes ~25 MB/s to disk.
The Status line on the control panel now shows live `fps` and `ms`.

**Practice:**
1. **Final renders → `Render Full Song (offline)`.** Turns realtime off: every frame is rendered and recorded no
   matter how long it takes, audio stays in sync, then it stops itself and restores realtime. Perfect output,
   independent of machine speed.
2. **Live/rehearsal → one window.** Use Perform mode (F1) or the preview window, close node viewers.
3. **Halve the work:** set *Project / Record FPS* to 30 for recordings (Movie File Out writes one frame per
   cook, so record fps = project fps).
4. Watch the `Status` line / a Perform CHOP: if ms/frame > 1000/fps you're over budget.

**Formats:** pick a preset in `op.Config` (16:9, 1:1, 4:5, 9:16, 4:3, 2.39:1, custom). Non-Commercial caps each
side at 1280 px, so social formats are scaled versions (e.g. 9:16 at 720×1280 — upscale in your editor or get a
Commercial license for 1080×1920). For projectors: set Custom to the projector's native resolution, open the
output with a Window COMP on that display (Perform mode), and measure ms/frame at that size — cost scales with
pixel count (1920×1080 ≈ 2.25× the pixels of 1280×720; the particle shader scales roughly linearly).

**Codecs:** MJPEG .mov (default, edits fine in Premiere), ProRes .mov (best for editing, bigger), Hap (fastest
playback in VJ software; Premiere needs a plugin). GPU H.264/H.265 need a Commercial license — so for posting,
convert the .mov afterwards (Premiere/Media Encoder, HandBrake, or
`ffmpeg -i take.mov -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a aac -b:a 256k out.mp4`).

## 10. TouchDesigner gotchas we hit (so you don't)

1. **Audio Filter CHOP** ignores the Hz field you set from Python; it uses `cutofflog` (Hz = 10**value).
2. **Speed CHOP** integrates poorly over short analysis slices → use a frame-start Execute DAT accumulator.
3. **Scripted multi-input wiring** on GLSL TOP is unreliable → use the **TOPs** parameter.
4. **COMP own-parameter expressions** evaluate in the parent's context → use `op.Shortcut`.
5. **Relative OP paths in COMP parameters** resolve from inside the COMP → prefer shortcuts/expressions.
6. **Feedback loops** remember their resolution → set it explicitly, reset on change.
7. **Movie File Out** "unique suffix" did not stop an overwrite → we generate timestamped filenames.
8. **Encoding on Windows:** read files in Python with `encoding='utf-8'` (otherwise `·` becomes `Â·`).
9. **GLSL `smoothstep(a, b, x)`** with a > b is a reversed ramp — easy to get backwards.
10. **Menu parameters in expressions:** `int(op.Config.par.Fps)` gives the menu *index*, not the value, and
    `op.Config.par.Recordcodec` passes the index too. Always use `.eval()` → `int(op.Config.par.Fps.eval())`.
    (This made one render 1 fps and another uncompressed 24 GB before we caught it.)
11. **Movie File Out opens its file the instant Record turns on** → set the file name first, start recording
    a frame later (`run(..., delayFrames=1)`).

## 11. Files and source control

```
TDExperiement.toe            composition root: layers, wiring, config values (small)
config/                      resolution_presets.tsv, stem_map.tsv, scenes.tsv   (synced from DATs)
modules/<layer>/<name>.tox   each module, externalised (Common → External .tox)
modules/<layer>/<name>/*.frag|*.py   shaders & callbacks synced from DATs (diffable!)
Assets/oak/                  masks + growth field (photo: see .gitignore note)
Assets/lyrics/               lyrics.txt + timing TSVs
tools/                       offline Python: make_image_masks.py, lyric_timing.py
scripts/                     generators that built oak scenes + lyrics (reference / rebuild from scratch)
Stems/, Recordings/          NOT in git (large / private)
```

**Saving rule:** externalised modules are **not** stored inside the .toe. After editing a module, right-click it →
*Save External .tox* (or `op('...').saveExternalTox()`), then Ctrl+S the project. DATs with *Sync to File* write
their file automatically.

## 12. Recipes

**Add a visual module:** copy `visuals/prism_bloom` → rename → change `pixel` shader → add a row to
`config/scenes.tsv` → it appears in the Scene menu. Read only from `op('bus')` (the module's Select of the contract).

**New song, same system:** export stems to `Stems/` → edit `config/stem_map.tsv` (map files to channels; keep
channel names) → pulse Rebuild → tune `analysis` (Floor dB, Hit Threshold, Growth Rate ≈ 1/(song seconds × 0.6)).
Songs with different instrumentation: map the closest stem to each channel or add channels (contract grows).

**New photo:** `python tools/make_image_masks.py new.jpg --seed X,Y --out Assets/<name> --name <name>` → point
`op.Config` Image Assets Folder at it (and file names in `oak_assets`) → set Crop Focus X.
Works best for images with a clear connected structure (trees, rivers, veins, architecture).

**New lyrics:** write `Assets/lyrics/lyrics.txt` (one sung phrase per line, `# section` headers) →
`python tools/lyric_timing.py <vocal stem> Assets/lyrics/lyrics.txt --out Assets/lyrics` → Reload.

**What generalises vs. what's per-song:** the pipeline, contract, analysis, control panel, config, overlay and
render tooling are generic. The *meaning* — which instrument is which element, which image, which words — is
per-song by design: it lives in tables, assets and the mapping section of CONTEXT.md, not in code.

## 13. Versioning: freezing states while moving forward

**Tags freeze, branches explore.**

- A **tag** is a permanent name for one exact commit. Annotated tags (`git tag -a`) carry a message, date and
  author. Use them for milestones: `iter-01-hello-world`, `iter-02-…`. They never move, unlike a branch.
- A **branch** is a moving line of work. Use short-lived branches for experiments
  (`explore/metabolism`, `explore/reaction-diffusion`) and merge to `main` when they're good. No need for a
  branch per stable state; that's what tags are for.
- A **GitHub Release** on a tag is where the *artwork* of that state lives: attach the rendered MP4 plus notes.
  Renders stay out of git; the release links code state and output together.

**Milestone ritual**
```
git add -A && git commit -m "…"                       # everything committed
git tag -a iter-02-<words> -m "what this state says"  # freeze it
git push && git push origin iter-02-<words>           # publish
# GitHub → Releases → Draft new release → choose the tag → attach the render
```
Then add a row to CONTEXT.md §5b.

**Revisiting a frozen state without disturbing current work** (`git worktree`): a second folder checked out
at the tag, so you can open the old `.toe` in TouchDesigner side by side:
```
git worktree add ../TDExperiement-iter01 iter-01-hello-world
# copy the git-ignored media in: Stems\  and  Assets\oak\oak_photo.png
# open ..\TDExperiement-iter01\TDExperiement.toe   (when done: git worktree remove ../TDExperiement-iter01)
```

**TouchDesigner-specific:** the `.toe` and `.tox` files are binary, so git can't merge them. Avoid editing the
same module on two branches at once. Because modules are externalised, a branch usually touches a few `.tox`
files plus readable `.frag`/`.py`/`.tsv` files, and those diffs tell the story.
