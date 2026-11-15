# td-experiment

Audio-reactive visuals for acoustic, audio-recorded music: **Ableton Live (stems) → TouchDesigner**.
First piece: *"8 Little Prayers"* — an oak tree that grows, is painted in, or assembles from light as the
song unfolds; a prism bloom; lyrics that appear as they're sung.

- **CONTEXT.md** — concepts, the song→image mapping, decisions, current state, backlog. Start here.
- **ARCHITECTURE.md** — how the TouchDesigner project is built, patterns, performance, recipes.

## Quick start

1. Install TouchDesigner (2025.x). Open `TDExperiement.toe`.
2. Put the song's stems in `Stems/` (not in git) and check `config/stem_map.tsv` matches the file names.
3. If `Assets/oak/oak_photo.png` is missing (not in git), generate assets from your photo:
   `python tools/make_image_masks.py <photo> --seed X,Y --out Assets/oak --name oak`
4. In TouchDesigner: `/project1/show_control` → **Open Panel**. Restart, pick a Scene, toggle Lyrics,
   **Render Full Song (offline)** for a final video (lands in `Recordings/`).
5. Change output shape in `/project1/config` → Format Preset (16:9, 1:1, 4:5, 9:16, …).

## Layout

```
TDExperiement.toe   composition root          modules/   externalised .tox + .frag/.py
config/             presets, stem map, scenes  Assets/    masks, growth field, lyrics
tools/              offline Python (masks, lyric timing)
scripts/            generators for oak scenes + lyrics overlay
```

## Working with Claude

The project includes `mcp_webserver_base` (from [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp)),
expected at `../td-tools/touchdesigner-mcp-td`. It lets an AI assistant inspect and edit the running project
over `http://127.0.0.1:9981` — only while TouchDesigner is open, local machine only.
