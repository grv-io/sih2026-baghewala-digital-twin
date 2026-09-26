# 04 — ML AUR OPTIMIZER SAMJHO (honestly)

> **✅ STATUS (27 Sep 2026, rev 13 — physics wave 5):** ML ka role ab bhi wahi hai —
> **the physics grid is the decision engine, the ML surrogate is not** — par ab
> operator ka float-response bhi ek **policy control** ban gaya hai (`pull` /
> **`vfd_hold`** / `vfd_then_pull` / `none`), aur grid isi ke upar bhi search karta
> hai. `ml/recommend_physics.py::best_settings_physics_5d` ka exhaustive 6-lever ×
> 4-policy grid (40,194 feasible points **per policy** ek nayi **injectivity-gate**
> feasibility check ke baad, ~172 s) hi canonical recommendation deta hai: **1,000 t /
> 10 d soak / 89 kgf/cm² / 64-in stroke / start 4.5 spm / cutoff 0.60 m³/d backstop /
> VFD-hold policy → net cash +₹15,396/cycle-day FY25** (+₹3,738 $65 floor, −₹8,811
> net-of-levies). **Gain kabhi ek number nahi — baseline ka apna float-policy naam
> lena zaroori hai:** same policy (baseline bhi VFD-hold) **+₹3,332/+4,319/+5,382**;
> baseline pull kare toh +₹12,917/+14,694/+16,606 (68% sirf policy-switch hai, set-point
> nahi — yehi purana "+₹9,574" number tha); baseline kuch na kare toh **−₹3,865/−2,513/
> −1,057** (rod-failure cost model me priced hi nahi hai). `ml/optimize.py` ka Bayesian
> surrogate-optimiser ab **physics-grid optimum se ~24% neeche** land karta hai
> (+₹11,635/d surrogate-verified vs +₹15,396/d physics-grid, FY25 net cash) — float
> classifier `float_premature_pull` ab 41% positive / AUC 0.999 hai par woh sirf
> **informational** hai, search constraint nahi (rev 12 ka soft float-risk penalty
> **hard injectivity-gate constraint** se replace ho gaya — float-response ab khud ek
> chosen policy hai, toh usko penalise karna physics se hi ladna tha, real cost price
> karna nahi). Tests **263 passed, 2 xfailed**. Rev 12 (jisme baseline hamesha `pull`
> karta tha aur "+₹9,574" ek hi number tha), rev-9 aur usse pehle sab ab historical hain.

Bhai, physics ho gayi. Ab yeh wali layer. Ek baat pehle: **ML yahan hero nahi hai, physics
hero hai.** Aur ek myth pehle hi tod deta hoon: *"ML isliye hai kyunki physics slow hai"* —
**yeh galat hai.** Humne time naapa: ek poora physics cycle **0.55 ms**, surrogate ki ek
prediction **1.13 ms**. Physics hi tez hai! Toh surrogate kyun hai — iska honest jawab §2
me hai. Judge yeh zaroor poochega.

---

## 1. Synthetic data — hai kya, aur legit kyun hai

**Sach yeh hai: humare training data me ZERO real cycles hain.** Sab 3,000 rows humare apne
physics engine se nikle hain. Yeh line **bina hakle** bolni hai — hakalna khud fact se zyada
bura lagta hai.

Ab defence, aur yeh genuine hai. Yeh **banaya hua data nahi hai** — yeh **solve kiya hua**
data hai. Aaj ki CSV (rev-5, calibrated physics) ki har row in published models (aur unke
v2 corrections) ka output hai:

- **Marx-Langenheim (1959)** — heat kitni ruki (ab sensible heat + sahi wellbore-loss ke saath)
- **Boberg–Lantz (1966)** cooldown + composite-radial uplift — Andrade ki jagah
- **Walther / ASTM D341** — viscosity vs temperature, 1 cP floor ke saath
- **Vogel (1968)** — inflow performance, ab live P_res(t) ke saath
- **API RP 11L-style** rod mechanics — load aur floating, ab liquid-basis pump capacity ke saath

Matlab har row **energy balance** maanti hai aur ek published viscosity-temperature law
follow karti hai. Toh model jo seekh raha hai woh **physics ka structure** hai, random
noise nahi. **Par honest caveat:** "published models se solve kiya" ka matlab "sahi"
nahi — v1 ke models published the phir bhi combination 25× optimistic nikla. Isliye
**plausible ≠ validated.** Jab field data commercially sensitive ho, digital-twin
prototype ke liye yeh **standard practice** hai.

### LHS — Latin Hypercube Sampling

3,000 points chahiye 4-D space me (steam_t, soak_days, cutoff, spm). Random dart phenko to
kahin **clumps** ban jayenge aur kahin **poore gaps** reh jayenge. LHS guarantee karta hai ki
**har dimension evenly stratified ho** — har steam bucket, har soak bucket bhar jaye.

> Random sampling = **andhere me dart phenkna**. LHS = **Sudoku ka rule** — har row aur har
> column me exactly ek point. Same compute, bahut behtar coverage, aur design space ke
> edges pe surrogate zyada trustworthy.

Code: `scipy.stats.qmc.LatinHypercube(d=4, seed=42)`, ranges seedhe `field_params.json` se
(steam 500–3000 t, soak 3–15 d, spm 4–12; cutoff v1 me **1–8 m³/d** tha, ab rev-5 params me
**0.6–2.0 m³/d** hai). Output: `data/synthetic_cycles.csv`, **3,000 rows** (0 dropped, 0 NaN):
SOR min **3.02**, median **4.33**, mean **4.74**, max 269.5 — **0.0%** rows SOR < 3, **0.57%**
> 8 (honest tail, not dropped). 12.7% rows alarm_days > 0, 58.2% margin-positive at bulk
diesel pricing. Reference-neighbourhood rows (near 1,500/7/1.2/5) land SOR 3.90–4.26 —
bracketing the calibrated reference gross SOR (4.09 at rev 5, 4.03 at rev 9 after physics
v3), confirming the generator matches the calibration physics. *(Dataset-wide min/median/
mean above are the rev-5 generation stats; physics v3 shifted the reference SOR only
~1.5%, so treat these as approximately, not exactly, current.)*

**Purani (v1) CSV ka mean SOR 2.96 tha** — literature average ~6 se neeche, "efficient"
band ke bhi neeche. **Yeh "realistic" ka saboot nahi, optimism ka warning sign tha** —
review ne exactly yahi pakda (v1 rate ~25× high). Seekh: apne data ka mean literature se
compare karna ek sasta sanity check hai — aaj ki v2 CSV ka mean (4.74) ab literature range
ke andar/paas hai, jo calibration ki sanity confirm karta hai.

> **Yaad rakhne wali baat:** *"This makes the model physically plausible. It does not make
> it field-validated. Those are two different claims and we don't mix them."* — yeh line
> word-for-word yaad. Jo judge poochne wala tha, tu pehle bol dega. **Yahi honesty points hai.**

---

## 2. XGBoost surrogate = "physics ka photocopy" — par kyun?

**Surrogate kya hai:** ek ML model jo physics engine ke input → output ko seekh leta hai,
taaki baad me physics chalaye bina andaza de sake. Physics ka **photocopy**.

**Pehle galat reason hata:** "physics slow hai" — **nahi.** Hamara physics cycle 0.55 ms
me chalta hai, surrogate 1.13 ms me. Aaj ke engine pe optimiser seedha physics bhi chala
sakta hai.

**Honest reasons (yeh bolna):**
1. **Contract-first design.** Optimiser, API aur dashboard ek fixed interface ("4 knobs in
   → SOR + P(float) out") se baat karte hain. Kal ko physics ki jagah kuch bhi aaye, upar
   ki layers nahi badalti.
2. **Jab physics mehngi hogi tab ready.** Agla step CMG STARS jaisa full reservoir
   simulator ya multi-well model hai — wahan ek run **minutes se ghante** leta hai. Tab
   surrogate hi optimiser ko practical banata hai. Architecture us din ke liye bani hai.
3. **Batching.** Ek call me hazaaron candidates ka score — sensitivity maps, uncertainty
   bands sasti ho jaati hain.
4. **Smooth P(float).** Physics ka floating result haan/naa (0.6 cross hua ya nahi) hota
   hai; classifier ek **smooth probability** deta hai, jo constraint ke liye (penalty,
   GP) bahut behtar hai.

*Aur uska ulta sawaal — "apni hi physics pe train karna circular nahi?"* — Haan, surrogate
physics se **zyada sahi kabhi nahi** ho sakta; woh sirf use copy karta hai. Isliye hum
R² ko "physics kitni achhi copy hui" bolte hain, "field accuracy" nahi. Asli sudhaar field
data se aayega (§6).

> **📘 Chhote definitions (judge ya CS dost pooche toh):**
> - **Decision tree** — "agar steam > 1,700 aur spm < 6 toh…" jaise if-else sawaalon ki
>   seedhi; har patte (leaf) pe ek prediction.
> - **Boosting (XGBoost)** — trees ek-ek karke banate hain; har naya tree **pichhle trees
>   ki galti** sudharne pe train hota hai. 300 chhote trees ka jod = ek strong model.
> - **Train/test split** — data ka 80% se seekho, 20% chhupa ke rakho aur **sirf usi pe**
>   score naapo. Warna model ne jawab ratt liye ya samjhe, pata nahi chalega.
> - **Overfitting** — model training data ratt leta hai (train pe perfect, naye data pe
>   fail). Test split isi ko pakadta hai.
> - **R²** = `1 − Σ(y − ŷ)² / Σ(y − ȳ)²` — "average guess" ke muqable model ne kitni
>   variance explain ki. 1 = perfect, 0 = average jitna hi achha.
> - **MAE** (mean absolute error) = `mean(|y − ŷ|)` — typical galti, same unit me (t/m³).
> - **ROC / AUC** — classifier ka threshold 0 se 1 tak ghumao, har threshold pe
>   true-positive vs false-positive plot karo = ROC curve. Uske neeche ka area = AUC.
>   1.0 = risky aur safe ko perfectly alag karta hai, 0.5 = sikka uchhalna.

Features sirf chaar: `[steam_t, soak_days, cutoff_m3d, spm]`. Split 80/20, seed 42
(2,400 train / 600 test), **single hold-out — koi cross-validation nahi.**

**Model 1 — `oil_model.joblib` (log(oil) predict karta hai, SOR ab derived hai).**
`XGBRegressor` (300 trees, depth 4, lr 0.05, subsample 0.9) target `log(oil_total_m3)` pe,
`.predict()` khud `exp` se inverse karta hai. `steam_t` toh humara apna decision variable
hai (jo hum hi choose karte hain), isliye sirf denominator (oil) predict karna kaafi hai —
`SOR = steam_t / oil_model.predict(X)`, seedha derive, alag se fit nahi. Held-out
**R² 0.998** (0.996 in-envelope 1,000–2,000 t steam), MAE 4.38 m³ (3.55 in-envelope).
*(Purana `sor_model.joblib`, jo direct SOR predict karta tha, retrain pe delete ho gaya.)*

**Model 2 — `margin_model.joblib` family (₹ margin per cycle-day). rev 9 se optimiser ka
objective `margin_incremental_inr_per_cycle_day` hai — incremental (stimulated minus
thanda kuan, same window), gross nahi.** Same XGBoost family, raw scale target (no
transform). Held-out **R² 0.883** overall — yeh number heavy negative tail se neeche
khinchta hai (design space ke bahar wale thin-steam/high-cutoff corners me cycle bhaari
nuksaan deta hai, jahan koi chalata nahi) — par **1,000–2,000 t plateau ke andar
R² 0.996**, MAE ₹235/cycle-day — bilkul consistent calibration log ki apni finding se
("flat 1,000–2,000 t plateau"). Gross-margin model bhi kept hai continuity ke liye
(R² 0.862 overall / 0.997 in-envelope) — par woh sirf reporting ke liye hai, objective
nahi.

**Model 3 — `float_model.joblib` (floating risk).** `XGBClassifier` binary label
`(max_floating_index > 0.6) OR (alarm_days > 0)` pe (dataset me yeh practically
`> 0.6` threshold tak reduce ho jata hai). Class balance: train 31.6%, test 29.2% positive.
**AUC 0.9994, accuracy 0.985.**

---

## 3. R² ka matlab kya hai — aur kya NAHI hai

Yeh sabse zyada misunderstand hone wala number hai. **Table yaad kar le (rev-9 retrain —
rev-13 numbers §1/§5 me hain; mechanism/interpretation same rahega):**

| Metric | Value | Iska matlab | Iska matlab **NAHI** |
|---|---|---|---|
| Oil regressor **R²** | **0.998** (0.996 in-envelope) | Surrogate **simulated** log(oil) ki ~99.8% variance explain karta hai | **99.8% accuracy nahi.** **Real-world accuracy bilkul nahi.** |
| Incremental-margin regressor **R²** | **0.883** overall / **0.996** in-envelope | Overall number heavy negative tail (bahar-ke-envelope corners) se dabaa hai; jahan koi actually chalayega wahan (1,000–2,000 t) fit almost exact hai | Ek hi "88% jaisa" flat number nahi — envelope ke andar-bahar farak bahut hai |
| Classifier **AUC** | **0.9994** | Risky vs safe settings ki ranking almost perfect | Asli rods pe kaam karta hai iska proof nahi |
| Classifier **accuracy** | **0.985** | 0.5 threshold pe | ~30% positives hain, isliye **AUC hamesha saath bolna** |

**"Classifier 0.9994 pe hai toh regressors sirf 0.88–0.998 kyun?"** — margin regressor ka
*overall* number is design space ke sparse, pathological corners (jahan koi operate nahi
karega) se neeche khinchta hai; **in-envelope** dono regressors 0.996+ pe hain. Floating
risk basically (μ, spm) me ek **smooth monotone boundary** hai — trees usko lagbhag
perfectly kaat dete hain.

**Aur yeh optimisation ke liye kaafi kyun hai?** Kyunki optimiser ko surrogate se sirf
**ranking** chahiye — "yeh setting us setting se behtar hai" — har value ko exact hit karna
nahi. Aur jo winner nikalta hai usko hum **asli physics twin pe dobara chala ke verify**
karte hain — is baar bhi surrogate-vs-physics gap chhota hai: margin −1.33%, SOR +1.13%
optimum pe.

> **Yaad rakhne wali baat:** *"R² yeh batata hai ki XGBoost ne **hamari physics** kitni
> achhi seekhi — yeh nahi batata ki hamari physics **Baghewala** se kitni milti hai."*

---

## 4. Bayesian optimisation — ek page me

**Problem:** chaar continuous knobs. Har evaluation mehnga. Kam se kam tries me best setting
chahiye.

**Grid search kyun nahi?** Cost `levels^dimensions` se badhta hai. 4 knobs × sirf 10 levels
= **10,000 runs** — aur 10 levels ka matlab steam volume me 250 t ka bhadda step. Upar se
grid **hopeless corners pe bhi utni hi mehnat** karta hai jitni promising region pe. Random
search behtar hai par **andha** hai.

**Bayesian optimisation woh hai jo search karte-karte seekhta hai.**

### Andhere kamre wali analogy

Soch, tu ek **andhere kamre** me hai aur tujhe **sabse unchi jagah** dhundhni hai. Har kadam
pe tu jhuk ke zameen ki height naap sakta hai — par naapna mehnga hai, sirf 60 baar naap
sakta hai.

Bewakoofi: 10,000 jagah naapna (grid) — budget hi nahi.
Thoda behtar: random jagah naapna.
**Smart:** har naap ke baad dimaag me ek **naksha** banate jao — "yahan uncha lag raha hai,
yahan ka andaza hai par pakka nahi." Phir agla kadam **wahin** rakho jahan ya to prediction
achhi hai (**exploitation**), ya jahan **dhundh sabse ghani** hai kyunki wahan kuch aur
behtar chhupa ho sakta hai (**exploration**).

Technically:
1. **Surrogate (Gaussian Process)** — abhi tak ke points pe fit hota hai, aur har untested
   point pe **do** cheezein deta hai: *predicted value* aur *uncertainty*. Yeh ek contour
   map hai jo yeh bhi shade karta hai ki **kahan kitni dhundh hai.**
2. **Acquisition function** — dono numbers use karke decide karta hai agla point kahan lena
   hai. Wahan evaluate karo, point add karo, GP refit karo, repeat.

*CS wale doston ke liye:* yeh epsilon-greedy bandits jaisa hai, bas fixed random exploration
rate ki jagah **uncertainty estimate batata hai ki explore karna exactly kahan worth hai.**
Ya: **gradient descent, un functions ke liye jinka gradient hi nahi hai aur jinko sample
karna paisa maangta hai.**

**Humari settings** (`ml/optimize.py`): `skopt.gp_minimize`, `n_calls = 60`,
`n_initial_points = 15` random seeds GP ke takeover se pehle, `random_state = 42`. Search
space ki ranges `field_params.json` se padhi jaati hain: steam `Real(500,3000)`, soak
`Integer(3,15)` (par recommendation-run me soak **10 pe fixed** hota hai, neeche §5b),
cutoff **`Real(0.6,2.0)`** m³/d (rev-5 range), aur **spm ab `srp.spm_practice_band`
(3–6) tak restrict** hai — poore `[4,12]` range se nahi, kyunki 3–6 hi heavy-oil field
practice hai. (Ranges params se aati hain; par poore codebase me kuch constants
hard-coded bhi hain — file 03 §6 dekh.)

**Objective ab maximise ₹ margin per cycle-day hai** (SOR minimise nahi) — SOR akela
minimise karo toh optimiser steam ko seedha minimum ki taraf le jayega, jo honest physics
hai par field ka actual goal nahi.

**Aur yeh dhyan de:** objective **physics twin ko nahi**, **trained surrogates ko** call
karta hai. Aaj ke engine pe yeh speed ke liye zaroori nahi (upar §2) — yeh **contract** ke
liye hai: kal physics ki jagah CMG-class simulator aaye toh optimiser code same rahega.
Aur surrogate ka P(float) smooth hai, jo constraint ke liye better hai.

### Floating constraint — penalty method

SPEC kehta hai floating probability **< 0.3** rehni chahiye. Humne **penalty** use ki:

```python
if float_prob >= FLOAT_PROB_LIMIT:                                    # 0.3
    penalty = PENALTY_SCALE * (float_prob - FLOAT_PROB_LIMIT)   # ₹30,000/day × excess
return margin_pred - penalty
```

Objective ab **₹/cycle-day scale** pe hai (pehle SOR-scale 1000× tha), toh penalty scale
bhi **₹30,000/day per unit overage** tak rescale hui hai — feasible margin/day spread ke
comparable. Achhi margin values thousands ₹/day range me hoti hain, toh thodi si bhi
violation score ko turant buri tarah neeche le jaati hai — candidate **hopeless**. GP seekh
jata hai ki us region me jaana hi nahi hai.

Yeh **soft constraint** hai (objective continuous rehta hai, jo GP ko pasand hai) par
**behave hard constraint jaisa** karta hai. Recommended cycle pe max FI **0.545**, alarm
days **0** — limit ke paas bhi nahi.

> **Rev 13 update:** ab float-response khud ek policy hai (upar §5), toh isko *penalise*
> karna ab galat tha — operator ne khud choose kiya ki woh float pe kya karega. Is soft
> penalty ki jagah ab ek **hard injectivity gate** hai (sandface pressure ≥400 kPa margin
> reservoir pressure ke upar) — yeh ek real physical constraint hai (steam formation me
> ghus hi nahi sakta gate ke neeche), heuristic nahi.

> **Yaad rakhne wali baat:** kabhi mat bolna *"guaranteed global optimum."* Bayesian
> optimisation ek **sample-efficient heuristic** hai non-convex objective pe. Sahi phrasing:
> *"a very good, often near-optimal solution within a limited evaluation budget."* Yeh trap
> question hai, isme mat girna.

---

## 5. Results — honest framing (yeh sabse important section hai)

> **v1 (historical):** purana recommendation −30% / −41.3% tha, jiska poora fayda **10
> SPM** chalane se aaya tha (practice 3–6 SPM pe cap karo toh SOR ≈ baseline), "3 din
> soak" fast cooldown ka artefact tha, SOR optimum 8 m drainage fudge se tha. **Ab
> historical hai — quote mat karna.**

**Rev 13: the physics grid IS the recommendation, not the surrogate — aur ab float-response
bhi ek policy dimension hai.** `ml/recommend_physics.py::best_settings_physics_5d`'s
exhaustive 6-lever × 4-policy grid (steam × pressure × stroke × spm × cutoff × float-policy,
40,194 feasible points **per policy** ek nayi injectivity-gate feasibility check ke baad,
~172 s) minimax-regret point:

| | steam t | pressure kgf/cm² | stroke in | start spm | cutoff m³/d (backstop) | policy | SOR | oil m³ | produce d (window) | net cash ₹/cycle-day (FY25 / $65 / net-of-levies) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Recommended** | **1,000** | **89** | **64** | **4.5** | **0.60** | **VFD-hold** | **2.83** | 353 | 196 (220) | **+15,396 / +3,738 / −8,811** |
| Baseline (b), same policy | 1,300 | 91 | 86 | 5.0 | 1.3 | VFD-hold | 3.29 | 395 | 199 (227) | +12,064 / −582 / −14,193 |

**Gain — hamesha baseline ki apni policy naam le ke bolo (net cash ₹/cycle-day):**
- **Baseline bhi VFD-hold kare (fair comparison): +₹3,332 / +4,319 / +5,382** —
  decomposition: stroke **57%**, cutoff **30%**, steam **11%**.
- **Baseline pehle alarm pe pull kare (rev-12 operation): +₹12,917 / +14,694 /
  +16,606** — **68% sirf policy-switch hai**, set-point nahi; yehi purana retired
  "+₹9,574" headline tha.
- **Baseline float ke baare me kuch na kare: −₹3,865 / −2,513 / −1,057** — yahan
  float-safe recommendation **paisa doobta hai**, kyunki model rod-failure/workover
  cost price hi nahi karta; jo cheez float avoid karke milti hai (72→3 alarm din,
  42→0 din FI=1.0 pe) woh ₹ me hai hi nahi.
- SOR: same policy pe 3.29 → 2.83 (−14%); ek pulling baseline ke against 4.35 → 2.83.

Baseline is **derived from OIL's own BGW-8 first CSS-cycle job** (~74 t/d ×
14–21 d ≈ 1,040–1,560 t, midpoint 1,300 t used; soak "50–60% of injection length" ≈7–13 d,
10 d used) — it is **one documented first-cycle job, not OIL's current operating
practice**.

**Honesty notes (yeh bhi bolna hai):**
- **Gross vs incremental SOR.** Headline SOR **stays gross** (steam ÷ all oil) — yehi
  literature/CalGEM convention hai. ₹ decisions ab **net cash per cycle-day**
  (counterfactual-free) basis pe hain. Cold well ab **policy ke under shut in** hai
  (idealised pumpable reading ~₹11.4k/d neeche, alag se bhi report hoti hai).
- **Price deck matters — teen ab.** FY25 deck pe recommendation **+₹15,396/cycle-day**
  kamata hai; **$65/bbl floor** pe **+₹3,738** — clearly weaker; **net-of-royalty-cess
  deck** (~₹3,600/bbl) pe **−₹8,811** — negative hi rehta hai, baseline se bhi neeche
  nahi (recommendation ka edge is deck pe **badhta** hai, kyunki woh steam bachata
  hai). Teeno deck dikhao, kabhi ek chhupa ke nahi.
- **Operator ka float-response ab khud ek control hai.** `pull` (rev-12 style,
  default params me kept — calibration anchor isi pe bana tha), **`vfd_hold`**
  (recommended — VFD floating index ko 0.6 pe hold karta hai, floor 2 spm, sirf
  floor pe 3 alarm din baad pull), `vfd_then_pull`, ya `none`. **Ek hi number kabhi
  mat bolo bina yeh bataye ki baseline ka policy kya hai.**
- **Rod damage unpriced hai.** VFD-hold floating index ko 0.6 ki limit pe ~55–60 din
  hold karta hai (damage index ~5× `pull` policy ka) — extra oil ka price hai, ₹ me
  nahi hai.
- **Soak fixed hai, twin-derived nahi.** Twin me soak ka koi defensible interior mechanism
  nahi (Boberg-Lantz sirf conduction-timing se asar dikhata hai) — isliye field practice
  (10 d) pe hold, "the model recommends N-day soak" kabhi mat bolna.
- **Ek naya honest gap:** mid-range (0.15) diesel discount pe best slug (~750 t) BGW-8's
  1,040–1,560 t se **neeche** aata hai (naya disclosed xfail) — revealed preference se
  padhein toh OIL ka steam is mid-range se sasta hoga.

### "Surrogate ko physics pe re-check karo" ab "physics grid hi asli optimiser hai"

*"The physics grid — not the surrogate — is the decision engine. Running the Bayesian
optimiser over the surrogate lands ~24% below the physics-grid optimum (+₹11,635/d vs
+₹15,396/d, both FY25 net cash) — a 60-call search under-resolves the steam/pressure
dimensions, the grid's own weakest economic levers. Every number you see is the physics
twin's own output at the recommended set-points — the surrogate result is a reported
cross-check, never the recommendation. The float classifier (41% positive, AUC 0.999) is
informational only as of rev 13 — a hard injectivity gate, a real physical constraint,
replaced the old soft float-risk penalty."*

> **Yaad rakhne wali baat:** teen sentence jo tujhe har baar bachayenge —
> *"That's from our simulation, not a field measurement."* /
> *"Zero real cycles, all physics-generated."* /
> *"Physically plausible, not field-validated."*

---

## 5b. Economics — ₹ aur CO₂ ka mini section

**Naya (rev 13) — stage pe bolne wali baat:**
- **Gross vs incremental SOR** — CSS ka sahi ₹ metric ab **net cash per cycle-day**
  hai (counterfactual-free); cold well policy ke under **shut in** hai — gross SOR sirf
  literature/CalGEM comparison ke liye headline hai.
- **Teen price deck hain ab:** FY25 (+₹15,396/d recommendation), $65 floor (+₹3,738/d),
  aur naya **net-of-royalty-cess** deck (−₹8,811/d — is deck pe har feasible point
  negative hai, "kya CSS profitable hai" ka jawab OIL ke apne P&L pe depend karta hai).
- **Gain ab baseline ki apni policy pe depend karta hai** (§5 upar) — same-policy
  +₹3,332/d, baseline-pulls +₹12,917/d, baseline-kuch-na-kare −₹3,865/d. Decomposition
  (same policy): stroke 57%, cutoff 30%, steam 11%.
- **Dyno cards:** computed (Gibbs wave equation) surface+pump cards ke saath-saath ek
  **measured-card classifier** bhi hai (`ml/dyno_classifier.py`, 94.8% hold-out accuracy,
  5 fault classes) — par kabhi field-validated mat bolna, yeh sirf synthetic cards pe
  train hai.
- **Calibration loop:** real cycle CSV do → 3 constants (`formation_water_cut`,
  `thickness_m`, `AOF_REF_M3D`) fit ho jaate hain → twin re-recommend karta hai (demo:
  −5.2/−10.9/−0.9% ke andar recover hota hai; rev-13 physics pe re-run, story same).
- **Field scheduler:** ek generator, kai wells, sab **VFD-hold** pe — naive fixed-job
  policy field-wide **+₹72,320/d** hai (rev 12, pull policy pe, isi setup me −₹13.3k/d
  **loss** thi — policy switch akela farak hai), greedy per-well tuning **+₹104,403/d**,
  exact scheduling **+₹109,799/d**, serving 10 of 12 wells.

**Steam ka asli daam:** OIL ke apne ops deck ke hisaab se Baghewala ke steam generators
**diesel (HSD)** pe chalte hain — ~220 kg/hr diesel se ~3,100 kg/hr steam. Yaani:

- **71 kg HSD per tonne steam**
- Bulk industrial price pe **₹5,856/t** (base case); retail pe **₹8,366/t**.
- CO₂: **~224 kg CO₂ per tonne steam.**
- Recommended cycle **kam steam jalata hai is baar** (1,000 t vs baseline ka 1,300 t) —
  per-cycle framing, koi annual assumption nahi.

**Net cash basis + opex:** ₹ ab **net cash per cycle-day** hai (counterfactual-free) —
daily opex (₹5,000/d `[ASSUMPTION]`) aur pumping power minus. Cold-well counterfactual
ab **operator ki apni float policy obey karta hai**: `pull`/`vfd_hold`/`vfd_then_pull`
ke under **shut in** (real field fact ke zyada paas), `none` ke under pumped floating.
FY25 deck pe recommendation **+₹15,396/cycle-day** kamata hai; $65 floor pe **+₹3,738**;
net-of-levies pe **−₹8,811**. Ek naya honest gap: VFD-hold floating index ko 0.6 ki
limit pe ~55–60 din hold karta hai — is rod-damage ka koi ₹ cost model me nahi hai.

**₹0.61 cr/yr (v1, historical) kyun galat tha (do baar):**
1. **₹1,300/t** steam price — yeh **gas-fired** steam ka number tha; Baghewala me gas hai
   hi nahi, diesel hai.
2. **6.8 cycles/well/yr** — 365 ÷ v1 ka 53-din simulated cycle. Asli CSS cycles **6–18
   mahine** ke hote hain; Baghewala ne ~6.5 saal me 34 wells pe total **39 cycles** kiye.

**Isliye:** annual ₹ number **mat** bolna. Bolna: *"Each tonne of steam is ~71 kg of
diesel — ₹7,111/t at our 0.15 mid-range bulk discount — and CO₂ scales with it. Under
the same VFD-hold policy, our recommended cycle burns LESS steam (1,000 t vs baseline's
1,300 t) and makes MORE oil, so SOR and CO₂ per cubic metre of oil both fall — but
that's a same-policy comparison, not a law of the physics."* **SOR kyun, ₹/NPV kyun
nahi?** — SOR price-independent hai aur literature se compare ho sakta hai (isliye
headline gross rehta hai); **objective ab net cash per cycle-day hai** (rev 13 se,
counterfactual-free), SOR ek reported efficiency side-metric hai, primary objective nahi.

---

## 6. OIL ka real data aane par — recalibration kaise hogi

Yeh finale ka jawab hai, aur judge yeh **zaroor** poochta hai: *"kal ko real data mila to?"*
**Do levels hain, dono aane chahiye.**

**Level 1 — parameter recalibration.** Zyada tar reservoir/fluid/pump numbers
`params/field_params.json` me hain — **par sab nahi.** Kuch constants abhi code me
hard-coded hain (`AOF_REF_M3D`, `S_COLD`, `K_VISC`, 150 °C / 50 cP anchor,
`PRESSURE_BOOST_PER_T_KPA`) — har ek `# ASSUMPTION` ke saath documented, aur params me
move karna planned hai. **"Kuch bhi hard-coded nahi" / "1 ghanta" mat bolna.** Sahi line:
*"Most parameters live in one JSON file; a few calibrated constants are still in code and
documented — moving them is on our list."* Flow: measured values daalo → data regenerate
→ retrain → optimise → physics pe verify.

Aur ab yeh sirf ek wishlist nahi hai — **calibration loop ban chuka hai**
(`twin/calibrate.py` + `ml/recommend_physics.py`): CSV do (well_id, steam_t, soak_days,
spm, oil_m3, produce_days), `water_cut`, `thickness_m`, `AOF_REF_M3D` fit ho jaate hain
(`bl_delta_factor` ab sourced/fixed hai, isliye fit nahi hota), aur twin usi recalibrated
physics pe re-recommend karta hai — pseudo-real demo me 0.2/1.6/0.9% ke andar recover
hota hai. Priority order phir bhi yeh hai:
1. **CSS cycle records** (steam t, soak, daily oil, cycle length) + **dyno cards** — yeh
   OIL se pehla ask hai; inse `AOF_REF_M3D`, water cut aur 0.6 threshold teeno calibrate
   hote hain. Baaki open items: pump geometry (typical, Baghewala-specific nahi), net-pay
   thickness (12 m kept vs ek 2022 paper ka 50 m gross — irrelevant hai kyunki gross ≠
   net pay).
2. **High-temperature viscosity point** — 150 °C / 50 cP anchor replace karne ke liye.
3. **Measured well productivity (PI)** — `AOF_REF_M3D` replace karne ke liye.
4. **Well spacing** — `reservoir.drainage_radius_m = 100` ko asli value se confirm karna.

**Level 2 — model recalibration (sim-to-real).** OIL ke real historical cycles training set
me add karo — ya to seedhe mix karke, ya synthetic rows ko **down-weight** karke chhote real
dataset ke against. **XGBoost chhote, mixed tabular datasets ko deep model se kahin behtar
handle karta hai** — yeh bhi ek reason hai ki humne XGBoost hi chuna. Bayesian optimiser ka
surrogate phir real observed SOR aur floating outcomes se update hota rahega, jaise-jaise
data aata jayega.

**Aur uske saath jo validation aayegi:** known-outcome historical cycles pe twin-predicted
SOR aur floating risk compare karo; check karo ki twin jo recommend karta hai aur jo
practically kaam kiya usme **directional agreement** hai ya nahi; phir **advisory mode** me
pilot — human in the loop — aur closed-loop control jaisi koi baat uske **bahut baad**.

---

## Raat wala 1-minute recap

- **The physics grid is the decision engine, not the ML surrogate** — the exhaustive
  6-lever × policy grid (40,194 feasible points/policy, ~172 s, every point
  true-physics-verified) is what produces the canonical recommendation; the surrogate
  lands ~24% below it and is reported only as a cross-check.
- **The operator's float response is now a policy control** — `pull` / **`vfd_hold`**
  (recommended) / `vfd_then_pull` / `none`, applied alike to baseline, recommendation
  and the cold counterfactual.
- **3,000 synthetic cycles**, LHS (Sudoku, dart nahi), seed 42, 7th column ab
  `float_policy` — gross SOR literature band (3–8, avg ~6, CalGEM real 3.47–8.24) ke
  paas/andar hai.
- **Zero real cycles** — bolna hai bina hakle, aur turant "plausible ≠ validated" add karna.
- **Surrogate kyun:** "physics slow" **nahi**. Contract-first, CMG-class physics ke liye
  ready, batching, smooth risk surface — par ab yeh explicitly ek **emulator**, doosra
  optimiser nahi; float classifier **informational only**, search constraint nahi (ab
  ek hard injectivity gate hai iski jagah).
- **Bayesian opt** = andhere kamre me sabse unchi jagah — har naap ke baad naksha update.
  60 calls, 15 random seeds, spm practice band tak restricted. **Global optimum
  guarantee nahi**, aur is doc me dikhaya recommendation **physics grid se aata hai, is
  optimiser se nahi.**
- **Objective:** **net cash per cycle-day** maximise (counterfactual-free; gross nahi,
  SOR bhi nahi, incremental-margin bhi nahi ab), subject to a hard injectivity gate.
- **Claim — hamesha teeno number saath bolo:** canonical recommendation (**1,000 t /
  10 d / 89 kgf/cm² / 64-in / start 4.5 spm / cutoff 0.60 backstop / VFD-hold**) vs
  baseline (b), **same policy (VFD-hold): +₹3,332/+4,319/+5,382**; baseline pulls:
  +₹12,917/+14,694/+16,606 (68% policy switch); baseline does nothing: −₹3,865/−2,513/
  −1,057. SOR 3.29 (baseline, VFD-hold) → 2.83 (rec). Decomposition (same policy):
  stroke 57%, cutoff 30%, steam 11%. Soak fixed at 10 d field practice (not
  twin-derived). v1's −30%/−41.3%, rev-5's gross "+188%", rev-9's "cutoff drives the
  gain", aur rev-12's single "+₹9,574" — sab ab historical.
- **Economics:** 71 kg HSD/t → ₹7,111/t at the 0.15 mid-range bulk discount, presets
  0.30 (bulk) and 0 (retail). Recommended cycle burns **less** steam under the same
  policy (1,000 t vs baseline's 1,300 t) and more oil.
  **₹0.61 cr/yr (v1) kabhi nahi; never claim absolute CO₂ down as a law; never quote
  gross margin as profit; never quote a single gain number without naming the
  baseline's own float policy; never say "+₹9,574" or "verified improvement"; never
  call the classifier field-validated.**
- **Recalibration:** pehla ask = **water-cut-vs-time log + one late-cycle/cold-well dyno
  card** (`twin/calibrate.py` ab `formation_water_cut`/thickness/AOF fit karta hai, demo
  −5.2/−10.9/−0.9% ke andar recover); phir OIL ka asli float-response practice (slow ya
  pull?), rod-failure/workover cost per event, aur SPM/stroke criteria — gain ab inhi
  pe ride karta hai, cutoff pe nahi.
