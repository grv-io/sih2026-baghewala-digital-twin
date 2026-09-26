"""twin -- physics engine for the Baghewala CSS + sucker-rod-pump digital twin.

Sub-modules (see docs/SPEC.md "Module contracts" for the exact, load-bearing
function signatures other agents build against):

- thermal:   wellbore delivery, Marx-Langenheim heated-zone growth during
             injection, Boberg-Lantz cooldown (slab f_VD, cylinder f_HD, delta).
- viscosity: Walther / ASTM D341 mu(T) fitted through field points, floored.
- ipr:       Vogel IPR with a Boberg-Lantz composite-radial productivity uplift.
- srp:       Sucker-rod-pump load, energy, float velocity ratio, fillage and
             liquid-basis pump capacity.
- cycle:     Day-by-day CSS cycle simulator that orchestrates the above.

All functions are pure and deterministic given `params` (the parsed
contents of params/field_params.json, optionally extended by cycle.py with
per-cycle keys such as "steam_t"). No network calls, no hidden global state.
"""
