# LEARNING — building TouchDesigner skills alongside Claude

The deal: Claude builds some things, Michael builds some things by hand, and Claude reviews Michael's
networks through the MCP bridge (it can read every node and parameter). Each exercise is a real piece of
this project, small enough for one sitting.

## How to read what Claude built
1. Open the module, press **P** for its parameters: the custom page is its API.
2. Middle-click a node for its info; turn on viewers (lower-right button on a node) to watch signals move.
3. Text DATs hold the code; the synced files under `modules/` are the same code in VS Code.
4. ARCHITECTURE.md names the pattern each module uses.

## Exercises (in order)

1. **Read a signal.** In `/project1`, add a Select CHOP pointing at `op.Bus.op('out')` and pick `vox`.
   Add a Trail CHOP after it and watch the vocal envelope over time. *Learns: CHOPs, selecting by name.*
2. **Map a signal to a parameter by hand.** In `visuals/pulse`, make the circle's Y position follow `snare`
   using a CHOP reference (drag the channel onto the parameter → "CHOP Reference"). Then do it again as a
   typed expression. *Learns: exports vs expressions, the two ways TD connects data.*
3. **Edit a shader.** In `modules/visuals/oak_particles/pixel.frag` (VS Code), change the sunlit point colour
   `vec3(1.0, 0.93, 0.78)` and watch TD hot-reload. Then make particle size respond to `vox` (it's in `uC.w`).
   *Learns: uniforms, GLSL TOP, file sync.*
4. **Add a scene.** Copy `prism_bloom`, rename, change one thing, add a row to `config/scenes.tsv`.
   *Learns: modules, table-driven builders.*
5. **Build the first data adapter yourself** (Vector 2): fetch NOAA Mauna Loa CO₂ (CSV) with a Web Client
   DAT or a File In DAT → clean it in a Table → DAT to CHOP → normalise to 0..1 → Null `out`. Claude reviews.
   *Learns: DATs, DAT→CHOP, the adapter pattern from the other side.*
6. **Metabolism v0, together:** a Feedback-TOP reaction-diffusion where audio energy sets the feed rate and
   CO₂ sets the kill rate. Claude writes the shader, Michael wires and tunes it.

Keep notes here on what clicked and what didn't; that tells Claude what to explain differently.
