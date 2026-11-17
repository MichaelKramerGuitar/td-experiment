# iter-02 — Metabolism: Stress

*"8 Little Prayers"* · Oak · Metabolism · World Role: **Stress** · 720p60 · 2:37

## What it is

A song that is also a metabolism. The music is the energy source; 68 years of atmospheric CO₂ measured at
Mauna Loa (1958 → 2026) is the world it lives in. The oak is an organism that takes in the song's energy,
converts it into breath, and lives on that breath. Early in the song (the 1960s) it is born from a seed and
fills out in points of light. As the decades pass and CO₂ climbs, the same music sustains it less and less.
By the 2020s it has withdrawn to its roots.

## How it works (plain version)

1. **The song is split into nutrients.** Drums give fast, spiky energy; the sub bass a steady base load;
   the voice acts as a catalyst that helps conversion (and lingers a moment after each phrase); the guitars
   are trace elements that make conversion efficient.
2. **The organism stores and converts.** Energy fills a store that saturates. A reaction turns stored
   energy into breath, limited by the scarcest input. Breath sustains the inhabitor's vitality.
3. **The world sets the conditions.** NOAA's monthly CO₂ record is laid across the song, about 2.3 seconds
   per year. In the *Stress* role, rising CO₂ is harm: it erodes the organism's capacity and damages its
   vitality. The yearly rise and fall of CO₂ (the Northern Hemisphere's growing season) is felt as a
   seasonal breathing.
4. **Vitality draws the tree.** The oak's points assemble from the trunk outward as vitality rises and
   withdraw the same way as it falls; its sunlit points glow with the breath.

Nothing on screen is mapped directly from loudness. Everything you see is a consequence of the state of the
process: the same drum hit lands differently in 1965 than in 2015.

## Data and credits

- **CO₂:** NOAA Global Monitoring Laboratory, Mauna Loa Observatory monthly means (`co2_mm_mlo.csv`,
  file created 2026-10-09; data March 1958 – September 2026). March 1958 – April 1974 obtained by
  C. David Keeling, Scripps Institution of Oceanography. December 2022 – July 2023 measured at Maunakea
  after the Mauna Loa eruption. https://gml.noaa.gov/ccgg/trends/
- **Time:** 68.5 years compressed into 2:37 (≈ 2.3 s per year, ≈ 7 beats at 200 BPM). Linear.
- **Music:** Michael Kramer. **Image:** New Orleans live oak photograph (masks derived by
  `tools/make_image_masks.py`).

## Presenting the data-driven nature to an audience

Pick by context; they combine well.

1. **One line (title card, caption, intro):**
   *"A tree that lives on this song, in the air we've measured since 1958."*
2. **Program note (~60 words):**
   *"The music is sunlight. Since 1958, scientists on Mauna Loa have measured the CO₂ in our air every
   month; that record is this tree's world, one year every two seconds. The tree takes in the song's
   energy and breathes it out. The music never weakens — but the world it lives in changes, and the same
   song sustains it less."*
3. **Make the time visible.** A small on-screen counter (`1958 · 315 ppm` → `2026 · 428 ppm`), or the
   Keeling curve drawing itself along the bottom edge with a playhead. Once people see the year move, they
   read everything else as time passing. (Both are small overlays; `op.World` already has `year` and `level`.)
4. **Name the breath.** The flicker in the tree's light is real: the yearly sawtooth in the CO₂ record is
   the planet's growing season — Earth breathing. Pointing it out turns a texture into a fact.
5. **Show the counterfactual.** Play the *Abundance* or *Tipping* render beside or after *Stress*. Same
   song, same tree, same data; only the meaning given to the data differs. That makes the data-driven
   nature undeniable — and shows the interpretation is a choice.
6. **Show the machine.** For curious audiences (talks, posts, a gallery wall): the simulation chart
   (`docs/img/metabolism_sim_roles.png`) — the music, the CO₂ curve and the tree's vitality on one timeline.
7. **Spoken intro for live (≈30 s):**
   *"Before we play: this tree is alive in a simple way. It eats this song — drums, bass, voice, guitars —
   and breathes it out. Its world is real: the carbon dioxide measured at Mauna Loa from 1958 until this
   autumn, compressed so one year passes every couple of seconds. Watch what the same song can and
   can't do as that world changes."*
8. **Social post:**
   *"8 Little Prayers — a tree that lives on a song, inside 68 years of real CO₂ data (NOAA Mauna Loa,
   1958–2026). Same music the whole way through. Different air."* Alt text: *"A tree made of thousands of
   points of light grows to full bloom, then slowly thins and withdraws to its roots while a song plays and
   lyrics appear."*

**Be clear about what's literal.** The CO₂ values and their timing are real. The tree, its metabolism and
the idea that rising CO₂ is "stress" are artistic interpretation — not a scientific model of how trees
respond to CO₂. The time compression is linear and stated. Saying this out loud strengthens trust.

## Technical

- Render: offline (every frame), 1280×720, 60 fps, H.264 MP4 (converted from Motion-JPEG), audio 256 kbps AAC.
- Code state: tag `iter-02-metabolism-stress` on `main` (merged from `explore/metabolism`).
- Reproduce: open the tagged project, control panel → Scene *Oak · Metabolism*, World Role *Stress*,
  Lyrics on → *Render Full Song (offline)*.
