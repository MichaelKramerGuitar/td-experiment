# METABOLISM — design notes for `explore/metabolism`

Status: **design draft (session 3)**. Living document: update as the exploration teaches us things.

## 1. Intent

Move from *mapping* (a stem's loudness → brightness of a region) to *metabolism*: sound energy is taken in,
stored, and transformed by a stateful process whose rules are shaped by a world (a historical dataset).
The product of that process is a **breath** that sustains a downstream **life-force inhabitor**. The
audience watches the inhabitor live, starve, thrive, change.

Photosynthesis is the illustrative example, not a literal requirement. The engine knows nothing about
ecology; datasets plug in as *environments*.

## 2. Principles (agreed with Michael, 2026-11-17)

1. **Historical snapshots before live feeds.** A finished dataset has boundaries and a narrative arc. We
   analyse it *before* rendering and compress its timeline onto the length of the song. Live feeds remain a
   future adapter (big potential for live performance).
2. **Pre-recorded audio first**, live audio later (the `live_in` adapter).
3. **Process over mapping.** No direct 1:1 amplitude→pixel links in this layer. Everything visible is a
   consequence of state.
4. **Symmetry.** The world side mirrors the audio side: adapter → analysis → contract.
5. **Honesty.** The piece states which dataset, which years, and how time was compressed (credits/legend).

## 3. Architecture

```
AUDIO   sources/stems_in → analysis → op.Bus      (energy: fast, moment to moment)
WORLD   world/<dataset>_in → world_analysis → op.World   (environment: slow, the arc of the song)
                     │                         │
                     └──────────►  METABOLISM  ◄┘     op.Metabolism  (state, reactions, breath)
                                       │
                                       ▼
                            INHABITOR(S)  (visual life that consumes breath)
                                       │
                                       ▼
                               output (scenes, overlays, recorder)
```

### 3.1 World contract `op.World.op('out')` (all 0..1 unless noted)

| channel | meaning |
|---|---|
| `data_time` | position in the dataset's own timeline (0 = first sample, 1 = last) |
| `level` | the main variable, normalised over the whole snapshot |
| `trend` | slow component (the arc) |
| `cycle` | periodic component (e.g. seasons), −1..1 |
| `anomaly` | deviation from expected, −1..1 |
| `event` | pulse when the analysis flagged a turning point / record / regime change |
| `capacity`, `substrate`, `stress` | the environment as the metabolism reads it: derived from the above by a per-dataset mapping table |

Song time → data time is a **table** (`config/world_timeline.tsv`), so the arc can be linear, eased, or aligned
to song sections ("chorus 2 lands on the record year").

### 3.2 Metabolism v0 (a few reservoirs, readable Python, stepped every frame)

```
intake   = absorb · audio_power · (1 − E/Emax)                 # fills, but saturates
rate     = Vmax · capacity · E/(Ke+E) · substrate/(Ks+substrate)  # limited by the scarcest input
E'       = intake − rate − leak·E                               # stored energy
P'       = rate − exhale·P                                      # product pressure
breath   = exhale·P                                             # the outflow
V'       = feed·breath − decay·V − harm·stress                  # inhabitor vitality
```
Behaviour we want from this: memory (state carries over), saturation (loud ≠ always more), limitation (the
world can starve the process even when the music is loud), delay (energy now, breath later).
Outputs to `op.Metabolism.op('out')`: `energy`, `rate`, `breath`, `vitality`, plus `breath_pulse` events.

### 3.3 Spatial body and inhabitors (rendering)

- **Body:** a reaction-diffusion field (Gray-Scott, GLSL feedback). Feed/kill come from the metabolism + world,
  so the texture of the body is the visible chemistry.
- **Breath:** GPU particles emitted where the reaction is active, flowing outward; emission rate = `breath`.
- **Inhabitor:** something that lives on breath: growth (the oak's growth field), a swarm, a creature,
  light. First version: re-use the oak particles, but their assembly is driven by `vitality`, not `growth`.

## 4. Plan

1. ✅ Branch + this document.
2. **World adapter** for the first snapshot (Michael builds by hand, Claude reviews: LEARNING.md ex. 5).
3. `tools/world_analyze.py`: decompose the snapshot (trend / cycle / anomaly / events), write a TSV the adapter loads.
4. Metabolism v0 module (Claude builds, explained step by step) + a debug view (live plots of reservoirs).
5. Reaction-diffusion body + breath particles.
6. Inhabitor v0, first render, tag `iter-02-…` when it says something.

## 5. Decisions (2026-11-17)

- **First world:** NOAA Mauna Loa monthly CO₂, 1958 → today (`Assets/world/co2_mm_mlo.csv`, frozen snapshot).
  The rising trend is the arc; the yearly sawtooth is a breath.
- **Intake:** **stems as nutrients**, each instrument feeding the metabolism differently (to design: e.g.
  drums = fast, spiky energy; bass/sub = slow base load; voice = sustaining; guitars = trace elements that
  unlock reactions).
- **World adapter:** Michael builds it by hand (`docs/exercises/05_world_adapter.md`), Claude reviews.

## 6. Open questions

- The nutrient roles above: which stem enables which reaction?
- Does the inhabitor have a lifespan / generations across the song?
- How does a rising CO₂ arc feel inside the metabolism: abundance (more substrate) or stress, or both,
  crossing over at some point in the song? (This is the narrative choice, not a technical one.)
