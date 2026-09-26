# 05 — HUMNE KYA BANAYA (poore system ka tour)

> **✅ STATUS (27 Sep 2026, rev 13 — physics wave 5):** `twin/` ab **rev 13** hai —
> operator ka **float-response ab khud ek policy control** hai
> (`css.float_policy` ∈ `pull` / **`vfd_hold`** / `vfd_then_pull` / `none`), baseline
> aur cold counterfactual pe bhi same policy apply hoti hai (cold well ab policy ke
> under **shut in**, pumpable nahi), smooth inversion band, injectivity gate (≥400 kPa),
> naya net-of-levies price deck. **Koi calibration knob nahi hilaya** — sirf diesel
> discount base (0.30→0.15). **The physics grid (`ml/recommend_physics.py`), not the
> ML surrogate, is the decision engine** — surrogate ab ~24% neeche land karta hai
> (rev 12 me 51% tha). `twin/dyno.py` (computed Gibbs cards), `ml/dyno_classifier.py`
> (measured-card classifier, 94.8% hold-out), `twin/calibrate.py` (calibration loop) aur
> `ml/schedule.py` (multi-well field scheduler, ab har well VFD-hold pe) sab modules
> hain. Demo default MOCK mode me. Tests **263 passed, 2 xfailed** (soak; mid-range
> diesel price pe steam optimum BGW-8 range se neeche — dono documented gap, failure
> nahi; rev-12 ka cold-well xfail ab un-xfailed hai).

Bhai, ab tak tune problem aur physics samajh li. Ab dekhte hain ki **humne actually
banaya kya hai** — kaunsi folder me kya hai, wo karta kya hai, aur demo ke time
kaunsa command kis order me maarna hai.

Ek line me: **ek physics engine, uske upar do ML models, uske upar ek optimizer, uske
upar ek API, aur uske upar ek dashboard.** Neeche se upar — har layer neeche wali pe
khadi hai.

```
field params  →  twin/ (physics)  →  3,000 synthetic cycles  →  ml/ (2 models + optimizer)
                                                                        ↓
                        dashboard (browser)  ←  api/ (FastAPI, port 8000)
```

---

## 1. `twin/` — paanch physics modules

Yeh dil hai project ka. Poora deterministic, **koi network call nahi, seed 42**, matlab
same input pe hamesha same output. Judge chahe toh saamne re-run karke dikha sakta hai.

| File | Ek line me kya karta hai |
|---|---|
| `thermal.py` | **Wellbore heat loss** (sandface quality = 0.55 × wellhead) → **Marx-Langenheim (1959)** heated zone growth → injection band hone ke baad **Boberg–Lantz (1966)** cooldown. `BL_DELTA_FACTOR = 0.5` ab **sourced/computed hai** (Boberg-Lantz ke apne δ ka exact half, PEH Eq. 15.70–15.74), har produce-day δ simulated oil/water streams se compute hoti hai. *(v1: τ = 20 d exponential, ab deleted.)* |
| `viscosity.py` | **Walther / ASTM D341** — temperature badhne pe oil kitna patla hota hai; do anchors (11,500 cP @ 50 °C asli, 50 cP @ 150 °C assumption) pe runtime fit, **1 cP floor**. *(v1: Andrade — 290 °C pe 0.63 cP deta tha, paani se patla.)* |
| `ipr.py` | **Vogel IPR × Boberg–Lantz composite-radial uplift** — sirf garam ring (r_h) patla, bahar 100 m tak thanda; uplift max 10×, asli me ~5×. `AOF_REF_M3D` rev 12 me 0.46→**0.56** retuned taaki reference peak field ke 15–40 bbl/d band me aaye. Cold rate ab viscosity-dependent hai (Darcy mobility se scale). *(v1: global `μ_ref/μ` factor — ~5,000×, 25× optimism ki jad.)* |
| `srp.py` | **Sucker-rod pump** — rod load, energy, **floating index** = `F_viscous / W_buoyant` = `v_stroke / v_fall`; 0.6 se upar risk. Drag emulsion viscosity se aata hai (Pal–Rhodes law, 10× capped, smooth 0.075 water-cut inversion band) na ki reservoir oil ki apni viscosity se. Stroke length (64–144 in) ek lever hai, PRL cap ke saath. |
| `dyno.py` | **[rev 6/9]** Gibbs (1963) rod wave-equation FD solve — surface + pump dynamometer cards **computed**, RP-11L chart-lookup nahi. Rod-float carrier-bar separation onset SPEC ke ≈0.6 FI alarm line se independently match karta hai. |
| `dyno_classifier.py` (`ml/`) | **[rev 12 cascade]** `RandomForestClassifier` — ek **measured** surface dyno card se fault-type predict karta hai (5 classes), 3,200 synthetic cards pe trained, 94.8% hold-out accuracy. Har call pe ek domain-shift caveat repeat hota hai: kabhi real Baghewala card nahi dekha — first read hai, field-validated diagnosis nahi. |
| `calibrate.py` | **[rev 9, updated rev 12, re-run rev 13]** Observed CSS cycles (CSV) se `formation_water_cut`, `thickness_m`, `AOF_REF_M3D` fit karta hai (`bl_delta_factor` sourced hai, fit nahi hota); `ml/recommend_physics.py` recalibrated physics pe hi re-recommend karta hai (stale surrogate use nahi karta). |
| `schedule.py` (`ml/`) | **[rev 12 cascade, rev-13 numbers]** Field-level scheduler — ~33 wells, **ek** shared steam generator, sab wells **VFD-hold** policy pe. Per-well physics-optimal jobs banata hai, phir bitmask-exact search se decide karta hai kaunsa well pehle steam paaye. 12-well demo: naive fixed-job policy field-wide **+₹72,320/d** (rev 12, pull policy pe, isi setup me −₹13.3k/d **loss** thi), greedy **+₹104,403/d**, exact **+₹109,799/d**, 10/12 wells serve karke. |
| `cycle.py` | **Conductor** — inject → soak → produce, din-din. **Rev 13:** operator ka float-response ab khud ek **policy control** hai — `css.float_policy` ∈ `pull`/**`vfd_hold`**/`vfd_then_pull`/`none`; baseline, recommendation aur cold counterfactual sab pe same policy apply hoti hai (cold well policy ke under **shut in**). Injection pressure lever, injectivity gate (≥400 kPa). `summary()` me net cash per cycle-day (counterfactual-free), CO₂, injectivity margin. |

Har physical assumption code me `# ASSUMPTION:` comment ke saath likhi hui hai. Judge
puche "yeh number kahan se aaya" — file khol ke dikha dena.

**`twin/generate_data.py`** — yeh physics modules ko **3,000 baar** chalata hai. Latin-hypercube
sampling (`scipy.stats.qmc`, seed 42) se knobs — steam_t, soak_days, cutoff_m3d, spm, aur
**rev 13 me ek 7vaan, categorical column `float_policy`** ({pull, vfd_hold, vfd_then_pull},
equal strata) — ke 3,000 alag combinations banate hain, har ek pe poora cycle simulate
hota hai, aur `data/synthetic_cycles.csv` me 3,000 rows likhi jaati hain. Gross SOR
literature band (3–8, avg ~6, CalGEM real 3.47–8.24) ke andar/paas, calibration ki sanity
confirm karta hai. Command **ab safe hai chalane ke liye** — bas ~24 seconds lagte hain
3,000 rows ke liye, aur current CSV **overwrite** ho jayegi (`ml/train.py` bhi phir se
chalana padega).

*Kyun LHS aur simple random nahi?* Random draws 4-D me guch-much ho jaate hain, kuch
region bilkul unexplored reh jaate hain. LHS **har dimension ko alag-alag stratify** karta
hai — same compute, kaafi better coverage.

---

## 2. `ml/` — do models + ek optimizer

**`ml/train.py`** CSV padhta hai, 2400/600 split karta hai (single hold-out, no CV), aur
rev 13 me paanch models banata hai (7 features, `float_policy` bhi ek — one-hot encoded):

1. **Oil regressor** (`oil_model.joblib`) — `log(oil_total_m3)` target, `.predict()` khud
   inverse karta hai. **R² = 0.995** overall. SOR ab isse derive hota hai.
2. **Margin regressor** (gross, continuity ke liye kept) aur **incremental-margin
   regressor** — reporting ke liye, objective nahi.
3. **Net-cash regressor** (`margin_net_cash_model.joblib`, `margin_with_opex_inr_
   per_cycle_day`) — **yahi rev-13 optimiser ka objective hai**, counterfactual-free.
4. **Float-premature-pull classifier** (`float_model.joblib`) — naya label: "rods,
   economics nahi, ne ek productive cycle khatam kiya" (**41% positive**, AUC **0.999**)
   — rev-12 ke ~95%-positive label ko supersede karta hai; **informational only, search
   constraint nahi.**

Sab `ml/models/*.joblib` me save hote hain, metrics `ml/models/metrics.json` me
(`physics_rev` provenance ke saath). *(Purana `sor_model.joblib` retrain pe delete ho
gaya — SOR ab derived hai, alag fit nahi.)*

**`ml/optimize.py`** — `skopt.gp_minimize` (Bayesian optimization) over the surrogate,
**60 evaluations**, ab `float_policy` bhi ek search dimension (categorical). Rev 13
finding: is optimiser ka result **physics-grid optimum se ~24% neeche** hai (+₹11,635/d
surrogate-verified vs +₹15,396/d physics-grid, FY25 net cash — 60-call budget steam/
pressure dimensions ko under-resolve karta hai, jo grid ke apne weakest levers hain) —
yeh sirf ek **cross-check** hai, recommendation nahi. Constraint ab ek **hard injectivity
gate** hai (rev 12 ka soft float-risk penalty replace kiya — float-response khud ek
policy hai, usko penalise karna physics se ladna tha).

**`ml/recommend_physics.py::best_settings_physics_5d`** — exhaustive **6-lever × 4-policy
grid** directly on the true physics (steam × wellhead-pressure × stroke × spm × cutoff ×
float_policy, 40,194 feasible points **per policy** injectivity-gate ke baad, ~172 s) —
**yehi asli decision engine hai.** Objective = **net cash per cycle-day**
(counterfactual-free), hard injectivity gate ke under. Soak **10 d field practice pe
fixed** — twin me soak ka koi interior optimum nahi hai. Canonical recommendation
(minimax-regret teeno price deck pe): **1,000 t / 10 d / 89 kgf/cm² / 64-in / start
4.5 spm, cutoff 0.60 m³/d backstop, VFD-hold policy → SOR 2.83** vs baseline (b), same
policy (1,300 / 10 / 91 kgf/cm² / 86-in / 5.0, VFD-hold → SOR 3.29) — net cash
₹/cycle-day **+12,064 → +15,396** (FY25) / **−582 → +3,738** ($65) / **−14,193 → −8,811**
(net-of-levies). **Gain hamesha baseline ki policy naam le ke bolo:** same policy
+3,332/+4,319/+5,382; baseline pulls +12,917/+14,694/+16,606 (68% policy switch);
baseline kuch na kare −3,865/−2,513/−1,057. Decomposition (same policy): **stroke 57%,
cutoff 30%, steam 11%**. *(v1's −41.3% deck-slide number, rev-5's gross "+188%", rev-9's
1,600/0.70/4, aur rev-12's single "+₹9,574" — sab ab historical.)*

---

## 3. `api/main.py` — teen endpoints

FastAPI, port 8000, CORS open. Bas teen:

| Endpoint | Kya deta hai |
|---|---|
| `GET /params` | `params/field_params.json` ka poora content (har call pe reload hota hai) |
| `GET /simulate?steam_t=&soak_days=&cutoff=&spm=` | `{summary: {...}, series: [har din ki row]}` |
| `GET /optimize` | optimizer ka poora result JSON |

Teeno **200 verify ho chuke** hain (rev-13 params se reference SOR ab **4.50 gross** hai,
shipped default `pull` policy pe, cutoff ke bajaye float onset se khatam hoti hai):
`/params` full JSON, `/simulate?steam_t=1500&soak_days=7&cutoff=1.2&spm=5` reference
reproduce karta hai, `/optimize` poora result deta hai. Naye `/api/*` endpoints bhi hain:
`/api/dyno/classify` (measured-card classifier), `/api/schedule` (field scheduler, ab
VFD-hold policy pe), `/api/recommend/physics` (6-lever × policy grid — asli decision
engine).

---

## 4. `dashboard/` — jo judge ko dikhega

Browser me chalta hai, Plotly cdnjs se. **4 pages:** `index.html` (overview),
**`console.html` (demo yahi page hai)**, `optimizer.html`, `methodology.html`. Source
`dashboard/src/*` me hai — generated `.html` mat edit karna, `node dashboard/build.js`
chalana. Console panels:

- **Cycle time-series** — temperature, viscosity (log axis), oil rate, din-b-din
- **Well cross-section** — pumpjack + heated zone ka animated cutaway, HUD ke saath
- **Dynamometer card** — rod load vs stroke position. **[Naya, rev 6/9] Ab computed hai**
  (`twin/dyno.py`, Gibbs 1963 rod wave-equation FD solve, RP-11L chart nahi) — cycle ke
  har din ke liye asli surface + pump card follow karta hai; 12 SPM stress test pe rod
  float **clamp separation** dikhta hai. (Purani illustrative `buildDynoLoop` lens
  replace ho chuki hai.)
- **Floating-risk meter + alarm banner** — 0.6 cross hote hi red, ACK button ke saath
- **Optimiser panel** — ab **net cash/cycle-day** led hai, teen price-deck preset (FY25
  realisation / $65 floor / net-of-levies) ke saath, aur ab ek **float-policy toggle**
  bhi (baseline VFD-hold / pulls / does-nothing) — yehi honesty ka moment hai, kyunki
  gain toggle se badalta hai: **published-practice baseline** (VFD-hold: +₹12,064/
  cycle-day FY25, SOR 3.29) vs **recommendation** (VFD-hold: +₹15,396/cycle-day FY25,
  SOR 2.83) — panel ka rev-13 re-bake pending hai, abhi is doc me superseded flag ke
  saath already updated numbers hain
- **Calibrate-from-field-data section** — CSV upload (MOCK preview / live `/calibrate`),
  calibrated recommendation staging
- **Replay** — poora cycle scrub se dekh sakte ho; water cut girta dikhega aur FI
  late-cycle me badhega, **rev 13 me ab VFD unit ko slow karte dikhayega** (float alarm
  pe pull ki jagah) — replay ka "15-second moment" yehi VFD-slowing banner hai (file
  `guides/DEMO_SCRIPT.md` dekh)
- **Stage → Confirm** — set-points apply karne ka do-step audited action
- **EN | हिं toggle** — Tier-1 text dono languages me stacked, Tier-2 toggle se swap,
  Tier-3 (units, numerals, `BGW-07`, `SIH26120`) kabhi translate nahi hota

**MOCK vs live:** flag **`dashboard/src/core.js:9`** — `const MOCK = true;` (default,
ships aise hi). Badlo toh `node dashboard/build.js` se rebuild, phir `console.html`
refresh. (Emergency me built `console.html` me bhi yahi line hai, ≈ line 1206 — par
source hi edit karna sahi hai.)

**MOCK me asli kya hai, approximation kya — honestly:**
- **Do baked scenarios** — **reference/baseline** (published-practice, 1,300/10/1.3/5.0)
  aur **recommendation**. Stage pe rev-13 numbers bolne hain (1,000/10/89/64/start
  4.5, VFD-hold, +₹15,396/d FY25 — same-policy baseline gain +₹3,332/d, alag naam liye
  bina mat bolna) — dashboard ka apna baked panel abhi retrain ka wait kar raha hai, yeh
  honestly bolna hai agar judge dashboard aur stage-number me farak dekhe.
- **Dynamometer cards ab computed hain** — `twin.dyno.compute_cards()` se baked
  (`dashboard/src/dyno-data.js`), din-din follow karte hain; kuch baked-nahi din pe ek
  interpolation-approx note dikhta hai, par card khud ek illustrative JS shape nahi hai.
- **Baaki har set-point** (dyno card ke alawa) ek in-browser JS heuristic (`mockSimulate`,
  `dashboard/src/page-console.js:37`) se aata hai. Panel ka meta khud "in-browser
  approximation" likhta hai. Toh set-point ka oil/margin dikhate waqt: *"this illustrates
  the mechanism"* bolna, "the twin computed this" nahi — par dyno card ke liye "computed"
  bolna sahi hai.
- API band hone pe dashboard **khud mock pe nahi girta** — "Data source error" chip dikhata
  hai. Demo MOCK = true (default) pe hi shuru karna, par live API ab current branch se bhi
  chalayi ja sakti hai agar chahiye.

---

## 5. PPT ke teen versions — kaunsi kab

| Deck | Kab use karni hai |
|---|---|
| **`ppt/final/SIH26120_Idea_Presentation_STRICT.pptx` / `.pdf`** | **Yehi submit karni hai.** Official SIH template pe bani, 6 slides, template ke pointers word-for-word intact. SIH screeners format deviate karne wali decks drop kar dete hain. Slide 5 ka −41.3% = **v1 prototype simulation** (label ke saath) — defend kaise karna hai, file 06 me. |
| **`ppt/archive/..._VISUAL.pptx` / `.pdf`** | Superseded. Sirf **practice** ke liye — sundar hai par template deviate karti hai, aur v1 numbers hain. Portal pe **mat** chadhana. |
| **`ppt/archive/..._VISUAL_EDITABLE.pptx`** | Superseded. Purana text-edit wala version. Ab edits `ppt/build_strict_deck.py` me karke STRICT rebuild. |

Rebuild command: `.venv\Scripts\python.exe ppt\build_strict_deck.py`

**Abhi bhi pending:** title slide pe `TEAM ________` aur Team ID `TBD` — registration ke
baad bharna hai.

---

## 6. `ppt/assets/svg/` — SVG library

Sab hand-made, dark aur light dono variants me — deck, dashboard, poster kahin bhi
drop-in:

- **`diagrams/`** — closed_loop, data_journey, sor_waterfall, stack_layers, system_flow
- **`illustrations/`** — css_cycle_phases, dyno_cards, india_field_map, pumpjack_scene,
  well_cutaway
- **`icons/`** — 28 icons (pumpjack, steam, viscosity, oil-drop, alert-triangle,
  rupee-saving, …) plus ek `sprite.svg`

SVG → PNG chahiye toh headless Edge use karna (`cairosvg` install nahi hai) —
command `ppt/notes/BUILD_NOTES.md` me hai.

---

## 7. "Kaunsi file me kya hai" — chhota map

| Judge puche… | Kholna hai |
|---|---|
| Reservoir heating kaise model kiya? | `twin/thermal.py` |
| Viscosity ka formula? A aur B kahan se? | `twin/viscosity.py` |
| Oil inflow model? | `twin/ipr.py` |
| Rod load / floating index exactly kya hai? | `twin/srp.py` |
| Phases kaise jude hain, cycle kab rukta hai? | `twin/cycle.py` |
| 3,000 cycles kaise sample kiye? | `twin/generate_data.py` |
| Kaunse ML models, kya metrics? | `ml/train.py`, `ml/models/metrics.json` |
| Optimizer aur safety constraint? | `ml/optimize.py` |
| Endpoints? | `api/main.py` |
| Dashboard fake toh nahi? | `dashboard/README.md` (MOCK / BAKED section) |
| Test kya kiye? | `tests/` — **263 passed, 2 xfailed**; xfail = documented, expected gaps (no interior soak optimum; mid-range diesel price pe steam optimum BGW-8 band se neeche) — not a failure. `docs/model-improvement/TIER1_PROGRESS_LOG.md` §12 |
| Physics wave 4/5 me kya badla, status kya hai? | `docs/model-improvement/TIER1_PROGRESS_LOG.md` §11–§12, `params/CHANGELOG.md` rev 12–13 |
| Field numbers ka source? | `docs/research/baghewala_facts.md` |
| Kya-kya badla aur kyun? | `params/CHANGELOG.md`, `docs/reviews/integration_report.md` |
| Koi term define karo | `docs/guides/GLOSSARY.md` |

---

## 8. Demo — step by step

**Bare `python` mat chalana.** Is machine pe PATH wala `python` ek broken MSYS2 build hai.
Hamesha `.venv\Scripts\python.exe`.

> ℹ️ **`twin\generate_data.py` aur `ml\train.py` ab SAFE hain current branch (physics-v2 /
> main) pe chalane ke liye** — physics calibrated hai, ab koi galat overwrite nahi hoga.
> Bas dhyan rakh: (1) data-gen **~24 seconds** leta hai 3,000 rows ke liye, retrain thoda
> zyada; (2) chalane se **current baked `data/synthetic_cycles.csv` aur `ml/models/*`
> overwrite ho jayenge** — agar demo se pehle chala raha hai toh time-buffer rakh.

**Default demo = MOCK mode, koi server nahi (sabse safe):**

```bat
cd "<repo>"
.venv\Scripts\python.exe -m pytest tests -q
node dashboard\build.js
start dashboard\console.html
```

(pytest ka expected result: **263 passed, 2 xfailed** — xfail = documented gap, ghabrana
nahi. `node dashboard\build.js` sirf tab zaroori hai jab `src/` me kuch badla ho.)

**Live API — ab current branch se bhi theek hai (v2 calibrated):**

```bat
cd "<repo>"
.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Doosre shell me check:

```bat
curl "http://localhost:8000/params"
curl "http://localhost:8000/simulate?steam_t=1500&soak_days=7&cutoff=1.2&spm=5"
```

Phir `dashboard\src\core.js:9` pe `MOCK = false`, `node dashboard\build.js`, aur
`dashboard\console.html` refresh. *(Purana `6bb604d` worktree instruction ab zaroori nahi
hai — woh sirf v1 ke OLD numbers reproduce karne ke liye tha. Honestly: **MOCK hi
demo ke liye kaafi hai**, live optional hai agar time ho.)*

**Demo ka sequence (3 min), `console.html` pe:** problem numbers → Simulate (published-
practice baseline baked) → **Replay: water cut girta dikhao, FI late-cycle me badhta**
— *"VFD slows the pump instead of pulling" banner* (rev-13 ka 15-second moment) →
dynamometer card (*"illustrative shape"* bolna; measured-card upload ek optional 30-s
beat hai) → Optimise → SOR/net-cash bars, **float-policy toggle** dikhao (yehi honesty
moment hai) — *"our recommendation vs OIL's own published-practice baseline, both
running the SAME VFD-hold policy, physics-verified: net cash +₹12,064 → +₹15,396/
cycle-day — a gain that depends on what the baseline operator does, and here's the
number for all three."* Field-view scheduler ek optional beat hai agar time ho.

---

**Yaad rakhne wali baat:** teen cheezein rat le — (1) pipeline ka order *physics → 3,000
cycles → 3 models + optimizer → API → dashboard*, (2) demo default **MOCK me,
`console.html` pe**, venv path ke saath — `generate_data`/`train` ab safe hain par time
lagta hai, (3) MOCK flag **`dashboard/src/core.js:9`**. Baaki sab file khol ke dikhaya ja
sakta hai. Aur haan — submit **`ppt/final/` wali STRICT** deck hi karni hai (woh abhi v1
numbers pe hai, team lead ka decision pending kal).
