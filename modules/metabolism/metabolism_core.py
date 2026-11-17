"""
metabolism_core.py — the metabolism engine, in plain Python (no TouchDesigner imports).

Used by:
  • TouchDesigner: /project1/metabolism/core (Text DAT synced to this file), stepped every frame by `tick`
  • tools/simulate_metabolism.py: runs the same engine offline on the stems + world data, for tuning/plots

Concepts (docs/METABOLISM.md):
  NUTRIENTS   the song, split by role:
              fast     drums: spiky energy (envelopes + hits)
              base     sub/bass: steady base load
              catalyst voice: enables conversion (slow memory: a sung phrase keeps working after it ends)
              trace    guitars: trace elements that make conversion efficient
  ENVIRONMENT the world (op.World), read through a ROLE:
              abundance  rising CO2 = more substrate to work with
              stress     rising CO2 = accumulating harm + failing capacity
              tipping    abundance at first, crossing into stress past a tipping point
  STATE       E   stored energy (saturates: a full store absorbs less)
              P   product pressure
              V   vitality of the life-force inhabitor (0..1)
  OUTPUTS     energy, rate, breath, vitality, substrate, capacity, stress, catalyst
"""

DEFAULTS = {
    'absorb': 1.6,    # how strongly nutrients are taken in
    'emax': 1.0,      # energy store capacity
    'vmax': 1.1,      # max conversion rate (scaled by capacity + catalyst)
    'ke': 0.25,       # energy half-saturation (lower = converts more at low energy)
    'ks': 0.35,       # substrate half-saturation
    'leak': 0.12,     # stored energy lost per second
    'exhale': 0.9,    # how fast product is breathed out
    'feed': 0.24,     # how strongly breath sustains the inhabitor (slow: vitality is a long arc)
    'decay': 0.035,   # inhabitor's natural decline per second
    'harm': 0.32,     # how strongly stress damages the inhabitor
    'tip': 0.55,      # tipping role: world level where abundance turns to stress
    'breathscale': 1.6,  # breath -> 0..1 for display
}

ROLES = ('abundance', 'stress', 'tipping')


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def smoothstep(a, b, x):
    t = clamp((x - a) / (b - a))
    return t * t * (3 - 2 * t)


def environment(role, level, cycle, p):
    """World -> (substrate, capacity, stress). level 0..1 over the snapshot, cycle -1..1 (seasons)."""
    season = 0.5 + 0.5 * cycle
    if role == 'abundance':
        substrate = 0.25 + 0.75 * level
        capacity = 0.75 + 0.25 * season
        stress = 0.0
    elif role == 'stress':
        substrate = 0.6
        stress = level ** 1.5
        capacity = (1.0 - 0.75 * level) * (0.8 + 0.2 * season)
    else:  # tipping
        substrate = 0.25 + 0.75 * level
        stress = smoothstep(p['tip'] - 0.10, p['tip'] + 0.10, level) * level
        capacity = (1.0 - 0.7 * stress) * (0.8 + 0.2 * season)
    return substrate, capacity, stress


def nutrients(b):
    """Bus channels (0..1) -> (fast, base, catalyst, trace)."""
    g = b.get
    fast = 0.30 * (g('kick', 0) + g('snare', 0)) + 0.12 * (g('hats', 0) + g('ride', 0)) \
        + 0.7 * (g('kick_hit', 0) + g('snare_hit', 0))
    base = 0.5 * g('sub', 0)
    catalyst = g('vox', 0)
    trace = 0.5 * (g('gtr_lead', 0) + g('gtr_rhythm', 0))
    return fast, base, catalyst, trace


class Metabolism:
    def __init__(self, params=None):
        self.p = dict(DEFAULTS)
        if params:
            self.p.update(params)
        self.reset()

    def reset(self):
        self.E = 0.0
        self.P = 0.0
        self.V = 0.02                     # the inhabitor starts as a seed
        self.cat = 0.0

    def step(self, dt, bus, world, role='tipping'):
        p = self.p
        fast, base, cat, trace = nutrients(bus)
        self.cat += (cat - self.cat) * min(1.0, dt / 0.8)           # voice lingers ~1 s
        S, C, stress = environment(role, world.get('level', 0), world.get('cycle', 0), p)

        intake = p['absorb'] * (fast + base) * (1.0 - self.E / p['emax'])
        ke = p['ke'] * (1.0 - 0.5 * min(1.0, trace))
        vmax = p['vmax'] * C * (0.55 + 0.45 * self.cat)        # voice boosts, but isn't required
        rate = vmax * self.E / (ke + self.E + 1e-9) * S / (p['ks'] + S)

        self.E = clamp(self.E + (intake - rate - p['leak'] * self.E) * dt, 0.0, p['emax'])
        self.P = max(0.0, self.P + (rate - p['exhale'] * self.P) * dt)
        breath = p['exhale'] * self.P
        self.V = clamp(self.V + (p['feed'] * breath * (1.0 - self.V)
                                 - p['decay'] * self.V
                                 - p['harm'] * stress * self.V) * dt)
        return {
            'energy': self.E / p['emax'],
            'rate': clamp(rate),
            'breath': clamp(breath * p['breathscale']),
            'vitality': self.V,
            'substrate': S,
            'capacity': C,
            'stress': stress,
            'catalyst': self.cat,
        }
