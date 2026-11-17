# Exercise 5 — Build the first world adapter: `world/co2_in`

**You build, Claude reviews.** Work through the steps in TouchDesigner on the `explore/metabolism` branch.
At each **🔍 Checkpoint**, tell Claude "checkpoint N". It will inspect your network over the bridge and
give feedback. Don't worry about getting it perfect first time.

**Goal:** turn the Mauna Loa CO₂ record (1958 → today) into a few clean 0..1 signals that move through the
whole history *over the length of the song*. This is the world-side twin of `stems_in` + `analysis`.

**You'll learn:** File In / Table DATs, a Script DAT (a few lines of Python), DAT → CHOP, CHOPs as whole
timelines (not just "now"), normalising with Analyze + Math, and the **Lookup CHOP**, the time-compression trick.

---

## Step 0 — Freeze the snapshot (outside TouchDesigner)

1. In your browser, download the monthly file:
   `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv`
2. Save it as `C:\Users\micha\code\TDExperiement\Assets\world\co2_mm_mlo.csv` (create the `world` folder).
3. Open it in VS Code and look at it: the `#` comment lines at the top describe the columns, then comes a
   header row, then one row per month. Note which column is the monthly **average**, which is
   **deseasonalized**, and what a *missing* value looks like.

Why a file and not a live request: it's a snapshot. The exact data the piece was made from lives in git,
so the render can always be reproduced.

## Step 1 — The module

1. At `/project1`, create a **Base COMP** named `world` (the layer, like `sources`).
   On its **Common** page set **Global OP Shortcut** = `World`.
2. Inside `world`, create a **Base COMP** named `co2_in` (the adapter module) and go inside it.

## Step 2 — Load the file

1. Add a **File In DAT** named `raw`. Set **File** to `Assets/world/co2_mm_mlo.csv`
   (relative to the project folder).
2. Look at it in the viewer: is it a table (cells) or one long text? The comment lines are in there too.

🔍 **Checkpoint 1** — `raw` loads the file.

## Step 3 — Clean it with a Script DAT

1. Add a **Script DAT** named `clean`, wire `raw` into it. A Script DAT runs a Python `onCook` function
   every time its input changes. Its *callbacks DAT* (docked next to it) holds the code.
2. Write the callback so it:
   - skips lines starting with `#`,
   - keeps the header row,
   - keeps only the columns **decimal date**, **average**, **deseasonalized**,
   - drops rows where `average` is missing.

   Skeleton (fill in the `...`):
   ```python
   def onCook(scriptOp):
       scriptOp.clear()
       src = scriptOp.inputs[0]
       header = None
       for r in range(src.numRows):
           first = src[r, 0].val
           if first.startswith('#'):
               continue
           if header is None:
               header = [c.val.strip() for c in src.row(r)]
               scriptOp.appendRow(['decimal_date', 'average', 'deseasonalized'])
               continue
           row = {header[i]: src[r, i].val for i in range(len(header))}
           ...   # pick the three values; skip the row if average looks missing
           scriptOp.appendRow([...])
       return
   ```
   Hint: if `raw` comes in as one column of text instead of cells, split each line with `.split(',')`.

🔍 **Checkpoint 2** — `clean` is a tidy 3-column table, ~800 rows.

## Step 4 — From table to timeline (DAT → CHOP)

1. Add a **DAT to CHOP** named `timeline`, input = `clean`.
2. Set it so **each column becomes a channel** and the **first row is the channel names**. You'll get three
   channels, each ~800 samples long: one sample per month.
3. Look at the CHOP viewer: you're seeing the whole Keeling curve at once. A CHOP isn't only "the value
   now"; it can hold an entire history.

🔍 **Checkpoint 3** — you can see the curve, sawtooth and all.

## Step 5 — Normalise (0..1 over the whole history)

1. Add an **Analyze CHOP** `range_min` (Function = Minimum) and another `range_max` (Maximum) after `timeline`.
2. Add a **Math CHOP** `norm` on `timeline`. On its **Range** page set **From Range** to the min/max using
   expressions, e.g. `op('range_min')['average']` and `op('range_max')['average']`, and **To Range** 0..1.
3. Make the **cycle** (the seasonal breath): a second Math or an Expression CHOP that computes
   `average − deseasonalized`, then scale it to roughly −1..1 the same way.

## Step 6 — Compress time onto the song (Lookup CHOP)

1. You need "how far through the song are we", 0..1. It already exists: the master stem's playhead.
   Add a **Select CHOP** `song_pos` with CHOPs = `op.Source.op('playhead')` and Channel Names = `fraction`.
2. Add a **Lookup CHOP** `at_song_time`. Input 1 = `song_pos` (the index), input 2 = your normalised
   timeline (the table to look up in). Set the index range to 0..1.

   It reads: *"we're 40% through the song, so give me the value 40% of the way through 1958 → today."*
   That single operator is the time compression.
3. Play the song. The values should crawl upward over the 2:37 and wobble with the seasons.

🔍 **Checkpoint 4** — values move with the song.

## Step 7 — Publish the contract

1. Use **Rename CHOP**s and a **Merge CHOP** to produce channels named exactly:
   `data_time` (= the song fraction), `level` (normalised average), `trend` (normalised deseasonalized),
   `cycle` (−1..1), `year` (raw decimal date, not normalised, for captions).
2. End with an **Out CHOP** named `out1`, the module's output port (same convention as `stems_in` and
   `analysis`).
3. Back at `/project1/world`: a **Select CHOP** pointing at `co2_in/out1`, then a **Null CHOP** named `out`.
   Now `op.World.op('out')` is the world contract, just like `op.Bus.op('out')`.

🔍 **Checkpoint 5** — final review. Then save the module as a .tox
(`modules/world/co2_in.tox`), commit on the branch, and write what clicked / didn't in `docs/LEARNING.md`.

---

**Next (Claude):** `tools/world_analyze.py` reads the same snapshot and adds the analysis layer: `anomaly`,
`event` (records, turning points), and a smarter song→data timeline in `config/world_timeline.tsv`.
Then the metabolism engine reads `op.World` + `op.Bus`.
