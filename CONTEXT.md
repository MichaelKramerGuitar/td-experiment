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

## 6. Open threads / backlog

- [ ] `live_in` adapter (Focusrite 18i16, Audio Device In) — same output contract as `stems_in`.
- [ ] Section/scene automation from song structure (verse/chorus timeline; e.g. full bloom on "Elegance unfolding now").
- [ ] Record the director's cuts as data → re-render offline with the same cuts.
- [ ] Virtual plants: L-system / growth-field driven geometry ("the circular haunts the future").
- [ ] Real 3D GPU particles (instancing) as an upgrade path for Oak · Particles.
- [ ] Word-perfect lyric alignment (WhisperX/MFA run locally) writing the same TSV format.
- [ ] Shared `td-modules` library repo once modules stabilise across 2+ songs.
- [ ] Projector/multi-display output profile (Window COMP per display).

## 7. Session log

- **2026-11-15 — session 1.** Built everything above. Key learnings recorded in ARCHITECTURE.md §10 (TD gotchas).
  Performance measured: see ARCHITECTURE.md §9. Note: an early test recording overwrote Michael's first
  `take.mov` (unique-suffix setting did not protect it) → takes are now timestamped.
  First full offline render: `Recordings/8_little_prayers_oak_painted_720p60.mp4` (Oak · Painted + lyrics).
  Observation for next session: late in the song the branch highlights run hot/pale (snare flash + pastel
  grade stacking) — candidate for tuning.

## 8. How to resume with Claude

1. Open `TDExperiement.toe` (it contains `mcp_webserver_base`, the bridge Claude uses).
2. Start a Claude session with the TouchDesigner MCP (or the desktop app with this folder connected).
3. Say: *"Read CONTEXT.md and ARCHITECTURE.md in C:\Users\micha\code\TDExperiement, then …"*.
4. After the session: Claude updates §5–§7 here; commit.
