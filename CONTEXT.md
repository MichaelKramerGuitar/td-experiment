# CONTEXT — working document

> Living notes for Michael + Claude. Read this first when resuming. Update it at the end of every session
> (decisions, new concepts, open threads). ARCHITECTURE.md explains *how* things are built; this file holds
> *why*, *what it means*, and *where we are*.

---

## 1. What this project is

An audio-reactive visual system for music made mostly with **acoustic instruments recorded as audio**
(not MIDI). Ableton Live is where the music lives; **TouchDesigner is where the visuals live**. The visuals
are driven by the *audio itself*: stems are analysed into signals (loudness, hits, frequency bands, accumulated
energy) and those signals drive scenes.

First song: **"8 Little Prayers"** (working title), project folder `DADGCF Song 1 Project`, Live 12 Lite,
200 BPM, ~2:37. Stems: lead vox, lead gtr, rhythm gtr, sub (sine), bass drum, snare, two overheads (hat side,
ride side), master.

## 2. Ground rules (agreed)

- **Claude does not touch the music.** Ableton is read-only (we read the `.als` file and use exported stems).
  No Ableton MCP / remote scripts that can modify the set.
- **Everything in TouchDesigner is fair game.**
- **Reusable + modular over clever.** Prefer patterns that carry to the next project. Add parts, remove parts.
- **Configuration over code edits.** Formats, paths, frame rate live in `config`; per-song data lives in tables/files.
- Verify with real renders/measurements, not assumptions.
- **Michael is learning TouchDesigner, not outsourcing it.** Claude explains the *why* in TD terms before
  building, keeps ARCHITECTURE.md teachable, and regularly hands Michael a piece to build by hand
  (see `docs/LEARNING.md`), then reviews his network over the MCP bridge. Michael: hold Claude to this.

## 3. Concepts and vocabulary (our ontology)

| Term | Meaning |
|---|---|
| **Signal** | A 0..1 control value derived from audio (e.g. `kick`, `vox`, `low`). |
| **Bus / contract** | The fixed set of named signals every visual can read (`op.Bus`, see ARCHITECTURE §3). The contract is the boundary between *listening* and *seeing*. |
| **Adapter** | A source that delivers named audio into the system (`stems_in` today; `live_in` for the Focusrite later). Adapters know nothing about visuals. |
| **Envelope** | Smoothed loudness of a stem (dB-normalised, attack/release). "How present is this instrument." |
| **Hit** | A short trigger on an onset (`kick_hit`, `snare_hit`). "Something just happened." |
| **Bands / the prism** | `low / mid / high` of the master. Named from the lyric *"the prism peels back Value to Goodness, Beauty and Truth"*: Goodness=low (gold), Beauty=mid (rose), Truth=high (cyan). |
| **Growth** | Accumulated loudness of the song, 0 → 1 over its length. *"Elegance unfolding now."* Things grow, they don't just pulse. |
| **Growth field** | A per-pixel map of *when* a pixel is reached by growth (distance along a structure from a seed). Turns growth into a spatial unfolding. |
| **Instrument masks** | Regions of an image assigned to instruments (trunk, branches, light, shadow, foliage, detail). |
| **Scene** | A complete visual (one module's output). Scenes are cut live like a director. |
| **Overlay** | Something composited over any scene (lyrics). Toggleable. |
| **Show clock** | Seconds into the song, taken from the true audio playhead. All time-based visuals and lyrics use it, so Pause freezes everything. |

## 4. The song → image mapping (current)

From Michael, for the oak scene (New Orleans live oak, pond, moss, foliage):

| Instrument | Element | Behaviour |
|---|---|---|
| Bass drum | Trunk | swells / brightens (envelope + hit) |
| Snare | Branches | flash; particles shake |
| Overheads (hats + ride) | Sunlight | glow in light gaps + rays through canopy |
| Sub / bass | Shadow | deepens shadow — "relief" |
| Rhythm gtr | Foliage (background detail) | sways, more vivid |
| Lead gtr | Colour / foreground detail | saturation in detailed regions |
| Voice | Language | lyrics appear word by word — "a linguistic bridge for the audience" |
| Whole song energy | Growth | the scene is drawn → painted / assembled from the trunk outward |

Earlier scene (Prism Bloom): 8-fold radial bloom ("8 Little Prayers"), three prism petal layers = bands,
kick rings echo outward (*"the circular haunts the future"*), snare flashes 8 radiating nodes
(*"all nodes radiate through me"*), vox lights the veins.

## 5. Current state (end of session 1, 2026-11-15)

Working:
- Stems adapter, analysis (envelopes, hits, bands, growth), signal bus (15 channels).
- Scenes: Prism Bloom, Pulse (demo), Oak · Painted, Oak · Particles. Live cuts via control panel.
- Lyrics overlay (toggle), timing derived from the vocal stem (approximate, editable).
- Control panel (`show_control`): Pause, Restart, Scene, Lyrics, Record, Render Full Song (offline), Preview,
  Perform, Monitor, Status.
- Config layer: format presets (16:9, 1:1, 4:5, 9:16, 4:3, 2.39:1, custom), project FPS, record codec, paths.
- Recording: timestamped takes (never overwrite), Motion-JPEG .mov (Non-Commercial license blocks H.264).
- Modules externalised to `modules/` (.tox + synced shader/script files) for git.

Known limits / debts:
- Lyric word timing is heuristic (line timing is good). Fine-tune via `Sync Offset` or the TSV.
- Non-Commercial license: max 1280 px either side, no GPU H.264/H.265.
- `live_in` (Focusrite) adapter not built; Live may hold the ASIO driver.
- Build scripts in `scripts/` generated the oak scenes + lyrics; the externalised .tox files are now the
  source of truth. Re-running a build script rebuilds that module from scratch (and overwrites hand edits).

## 5b. Milestones (frozen states)

| Tag | Date | Statement | Reference render |
|---|---|---|---|
| `iter-01-hello-world` | 2026-11-16 | "Hello, World": mixer-style mapping — each stem's loudness animates its region of the image. Oak · Particles + Lyrics is the most complete statement. | GitHub Release `iter-01-hello-world` (Oak · Particles + Lyrics, 720p60) |
| `iter-02-metabolism-stress` | 2026-11-17 | Metabolism: the song is energy, 68 years of Mauna Loa CO₂ is the world, the oak is an organism that lives on the breath. *Stress* role, start to finish. Michael's favourite of the three roles. | GitHub Release `iter-02-metabolism-stress` (Oak · Metabolism · Stress + Lyrics, 720p60); notes in `docs/releases/` |
| `iter-03-walk-in-3d` | 2026-11-17 | Walk in 3D: the metabolism's oak as ~126k particles lifted from the photo; a camera walks to it at full bloom, circles it through the decades and stays as it decays. *Stress* role. First release for social. | GitHub Release `iter-03-walk-in-3d` (YouTube 1920×1080p60 + Instagram Reel 1080×1920p60); notes in `docs/releases/` |

Reflection (Michael): the foundation is a translation of a mixing board — each voice's amplitude "dancing"
over time — mapped onto regions of an image and rendered through TD's aesthetics. Genuine milestone; also
only the surface of what this can be.

## 5c. Vector 2 — Metabolism (from "mixer" to "photosynthesis")

Inspiration: BREAKFAST (Andrew Zolty) — real-time ecological data turned into physical, kinetic experience,
so data seeps into intuition. Goal: cultivate relationship and reciprocity with global natural processes.

The shift: from *mapping* (channel → region) to a **process with state**, where things are converted:

| Photosynthesis | In the piece | Candidate data / mechanism |
|---|---|---|
| Sunlight (energy in) | **Audio** — energy absorbed, stored, spent | analysis bus; growth = stored energy |
| The leaf / organism (where conversion happens) | **The body / stage** (image or structure) | oak structure, a leaf, the ocean surface |
| CO₂ (substrate) | what the body breathes in | NOAA Mauna Loa CO₂ (daily / monthly CSV) |
| Chlorophyll (capacity to convert) | how much of the body can photosynthesise | satellite chlorophyll-a / phytoplankton (NASA PACE, NOAA ERDDAP), land SIF/GPP |
| Light actually available | modulates conversion | PAR (photosynthetically available radiation) |
| O₂ / sugar (products) | **visible outflow** — particles/flows leaving the stage | emitted at a rate set by the process |

"Chemistry" in TD terms: rates with **saturation** (more energy stops helping once substrate runs out),
**limiting factors** (the scarcest input sets the pace), **storage and delay** (energy banked now, released
later), **feedback state** (the body changes over the piece). Rendering candidates: reaction-diffusion
(Gray-Scott — literally a chemical simulation; feed/kill rates from data, energy from audio) and GPU particles
for the outflow.

A strong first study: the **Keeling curve's seasonal sawtooth** — the yearly rise and fall of CO₂ at Mauna
Loa is the Northern Hemisphere's growing season, i.e. the planet's photosynthesis as a breath. Time-compress
decades of it across the song, or play the last year as one breath per section.

## 5d. Next vector — walking into the tree (3D)

Stay with the *Stress* role. Once the tree is in full bloom, a camera enters: an observer on a walk finds the
tree, approaches, circles it in awe, and stays with it as it grows and decays — the particle growth and
decay experienced in 3D space. Planned on branch `explore/walk-in-3d` (see session 3 notes / plan).

## 6. Open threads / backlog

- [ ] `live_in` adapter (Focusrite 18i16, Audio Device In) — same output contract as `stems_in`.
- [ ] Section/scene automation from song structure (verse/chorus timeline; e.g. full bloom on "Elegance unfolding now").
- [ ] Record the director's cuts as data → re-render offline with the same cuts.
- [ ] Virtual plants: L-system / growth-field driven geometry ("the circular haunts the future").
- [ ] Real 3D GPU particles (instancing) as an upgrade path for Oak · Particles.
- [ ] Word-perfect lyric alignment (WhisperX/MFA run locally) writing the same TSV format.
- [ ] Shared `td-modules` library repo once modules stabilise across 2+ songs.
- [ ] Projector/multi-display output profile (Window COMP per display).

- [ ] **Vector 2:** `world` layer — data adapters (CO₂ first), a second contract `op.World`, a metabolism
      module with state (energy store, rates, outflow). First study: Keeling-curve breath.

## 7. Session log

- **2026-11-15 — session 1.** Built everything above. Key learnings recorded in ARCHITECTURE.md §10 (TD gotchas).
  Performance measured: see ARCHITECTURE.md §9. Note: an early test recording overwrote Michael's first
  `take.mov` (unique-suffix setting did not protect it) → takes are now timestamped.
  First full offline render: `Recordings/8_little_prayers_oak_painted_720p60.mp4` (Oak · Painted + lyrics).
  Observation for next session: late in the song the branch highlights run hot/pale (snare flash + pastel
  grade stacking) — candidate for tuning.
- **2026-11-16 — session 2.** Michael pushed main. Tagged `iter-01-hello-world`. Rendered Oak · Particles +
  Lyrics offline (reference render). Wrote versioning workflow (ARCHITECTURE §13), Vector 2 concept (§5c),
  learning path (`docs/LEARNING.md`).
- **2026-11-17 — session 3.** Branch `explore/metabolism`: world adapter (CO₂), metabolism engine
  (plain Python core + offline simulator), World Role switch, Oak · Metabolism scene. Michael's favourite:
  Stress, start to finish → rendered, merged to main, tagged `iter-02-metabolism-stress`, release notes with
  audience-presentation ideas. Fixed: synced DATs emptied by the save script (gotcha 12); project.save via
  bridge hangs (gotcha 13). Next: 3D walk into the tree.
- **2026-11-17 — session 3b.** GitHub linked: Claude can push and manage releases (REST API). Branch
  `explore/walk-in-3d`: photo → 3D point cloud (`tools/photo_to_3d_tree.py`), `visuals/oak3d` (126k instanced
  particles grown by the metabolism's vitality, lit by breath), camera walk from `camera_path.tsv`, scene
  *Oak · 3D Walk*. Fixed: metabolism blew up to infinity after a host time jump (gotcha 16).
  Next: watch it in Stress; tune the walk (Michael's exercise: edit camera_path.tsv); canopy beyond photo
  edges; backdrop; depth/fog.
- **2026-11-17 — session 3c.** Format-aware camera (vertical fov + `Portraitpull` step-back in 9:16), lyrics
  sized by the frame's short side. Rendered Oak · 3D Walk (Stress, lyrics) offline in landscape and portrait;
  upscaled to 1920×1080 (YouTube) and 1080×1920 (Instagram Reel) with the stereo mix; tagged
  `iter-03-walk-in-3d` and released. A freeze at render start traced to a stale TD process holding the
  bridge port, and a project saved mid-render reopening with the recorder still on (gotcha 17).
  Next (iter-04): canopy beyond the photo's top edge, fading backdrop, depth fog, limb variants.

## 8. How to resume with Claude

1. Open `TDExperiement.toe` (it contains `mcp_webserver_base`, the bridge Claude uses).
2. Start a Claude session with the TouchDesigner MCP (or the desktop app with this folder connected).
3. Say: *"Read CONTEXT.md and ARCHITECTURE.md in C:\Users\micha\code\TDExperiement, then …"*.
4. After the session: Claude updates §5–§7 here; commit.
