# 07 — EXAM MODE (khud ko test kar)

> **✅ STATUS (27 Sep 2026, rev 13):** questions aur 1-pager ab **rev-13 truth** pe update
> hain — v1, rev-5, rev-9 **aur rev-12** numbers sab historical hain. Rev 12 ka
> **"+₹9,574/cycle-day"** headline nikla ki woh sirf **baseline ke pull-on-float rule** se
> aata tha, set-points se nahi (ek technical re-score, 58/100, ka top finding). **Rev 13
> (physics wave 5)**: float ka response ab khud ek **policy control** hai — `pull` /
> **`vfd_hold`** / `vfd_then_pull` / `none` — aur baseline, recommendation, cold well
> **teeno** pe wahi ek policy lagti hai. VFD-hold (recommended) pe: baseline SOR 3.29,
> recommendation SOR **2.83**, 263/2xfail tests. **Fair gain (same policy): +₹3,332/d**
> (baseline pulle toh +₹12,917, kuch na kare toh **−₹3,865** — teeno bolo, kabhi ek nahi).
> Kuch bhi takraye toh file 06 ka **"Stage pe kya bolna hai"** block jeetega.

Bhai, yeh aakhri file hai. Do hisse:

1. **15 questions** — mixed difficulty, physics se strategy tak. Answers **file ke bilkul
   end me** hain. Jhaank mat, pehle likh ke ya bol ke attempt kar.
2. **"Raat ko revision"** — ek page, sirf woh cheezein jo presentation se **10 minute
   pehle** dohrani hain.

Scoring: **12+ sahi = ready.** 9-11 = file 03 aur 06 dobara. 8 se kam = poora pack dobara,
aaram se.

---

## PART 1 — 15 QUESTIONS

**Physics (5)**

1. Andrade law likh, aur bata hamare do calibration anchors me se **kaunsa asli field data
   hai aur kaunsa assumption**.
2. v1 ka `DRAINAGE_RADIUS_M = 8 m` asli drainage radius kyun **nahi** tha, v1 ka "SOR
   optimum" usse kaise aata tha, aur v2 me uski jagah kya hai?
3. v1 me oil rate ki saari harkat `μ_ref/μ` se aati thi. Yeh **~25× optimistic** kyun tha,
   aur v2 ka composite-radial uplift isko kaise theek karta hai?
4. Floating index ka formula bol, aur samjha ki **same viscosity pe zyada SPM floating
   zyada likely kyun** banata hai.
5. Produce phase me oil rate **girti** hai par rod load **badhta** hai — dono ka common
   cause ek hi hai. Kya?

**Cycle (2)**

6. Input 1,500 tonnes tha, par injection **20.27 din** chali. Kyun?
7. v1 ke produce phase me oil rate ~11 din tak **74.96 m³/d pe flat** thi. Kaun limit kar
   raha tha — reservoir ya pump? Aur isi baat ne v1 ke "10 SPM = −30%" ko kaise paida kiya?

**ML (4)**

8. Latin-hypercube sampling kyun, 3,000 uniform random draws kyun nahi?
9. **R² = 0.72** ka matlab exactly kya hai — aur exactly kya **nahi** hai?
10. Floating constraint `gp_minimize` ke andar (rev 13 se) kaise enforce hota hai, aur
    purana soft-penalty method kyun replace hua?
11. Grid search yahan galat tool kyun hai? Number ke saath argument de.

**Field / honesty (2)**

12. Baghewala ka actual measured SOR kya hai, aur poochne pe tu kya bolega?
13. Tumhare training data me kitne **real** CSS cycles hain, aur strongest honest defence
    kya hai?

**Strategy (2)**

14. Kaunsi deck **submit** karni hai (poora path), baaki kahan hain, aur slide 5 ka −41.3%
    judge pakde toh kya bolega?
15. Demo kis mode aur kis page pe chalana hai, MOCK flag kahan hai, aur live API current
    branch se kyun nahi chalana?

---

## PART 2 — RAAT KO REVISION (1 page, 10 minute)

**Kahani — 30 second me**
- Baghewala, Bikaner-Nagaur basin, Rajasthan · Oil India · Jaipur se **550-600 km**
- Crude **11,500 cP @ 50 °C** (lit 8,000-15,000) · **14-17° API** lit / **17-19°** PS
- **India ka pehla CSS**: BGW-8, **Dec 2018** · pehle cycle pe **5-6x uplift**
- Problem: SOR high, rod failures, sab kuch **manual guesswork**
- Solution ek line: *"ek physics twin jo CSS aur pump ko **saath me** optimise karta hai"*

**Field facts (unchanged, confirmed)**
- Depth **1,150 m** · steam **290 °C**, quality **0.65** · **74 t/d** · **52 wells** ·
  **218 t → 43,773 t** (FY17 → FY26) · field **655–1,202 bbl/d** (~19 bbl/d/well)
- Crude ~90–100× zyada gaadha apni API ke hisaab se (18° API crude ~123 cP hota)

**Kahani ka twist — 30 second me (yeh lead karo)**
- *"Our first-cut engine gave SOR 1.29 → 0.91. Our own review found it about 25 times
  optimistic on rate, not 25 percent. We replaced the physics with published models, fixed
  three of our own bugs, then two independent external reviews on 27 September scored our
  next revision 61 and 52 out of 100 and found more real gaps."*
- *"The biggest finding since: water cut is a state, not a constant — high early from
  condensate flowback, falling late toward the formation's own cut. When the produced
  stream turns oil-continuous late in the cycle, the rods float at practice speed. So we
  changed how a cycle ends: stop on the rate cutoff or three consecutive days of a float
  alarm, whichever comes first — the same thing an operator actually watches."*
- *"It's now calibrated — gross reference SOR 4.50, inside the literature bands and a real
  9,692-cycle California field-SOR band. 263 of 265 tests pass, with three honest gaps we
  mark and explain."*
- *"Our biggest recent finding: the operator's response to a floating rod is itself a
  choice — pull it, or slow the pump with a VFD and hold it at the float line. We apply
  the SAME choice to our baseline and our recommendation. Against a baseline that also
  slows down first, our recommendation gains three thousand three hundred rupees a
  cycle-day — mostly from a shorter stroke. Against one that just pulls, it looks like
  twelve thousand nine hundred, but two-thirds of that is the policy switch, not our
  set-points. And against one that does nothing about floating rods, we actually lose
  money, because we don't yet price rod damage."*

**v1 numbers — [historical prototype, audited and replaced — samjho, quote mat karo]**
- Reference 1,500 / 7 / 3.0 / 8 → SOR 1.29, 61.3 din · "optimised" 1,600 / 3 / 8.0 / 10 →
  0.91 · deck slide 5: 1.50 → 0.88 (−41.3%, optimiser midpoint baseline)
- Kyun galat: 471 bbl/d/well vs field ~19 · uplift 135× vs published 5–6× · μ(290) 0.63 cP ·
  optimum = 8 m fudge · poora gain = 10 SPM se

**rev-9 numbers — [historical, superseded — samjho, quote mat karo]**
- Reference (1,500/7/1.2/5): gross SOR 4.03, uplift 5.66× — water cut **constant** 85% tha,
  cycle sirf rate cutoff pe khatam hoti thi
- Recommendation 1,600/10/0.70/4 → incremental ₹/cycle-day −724 → +4,423 — **83–96% gain
  cutoff se** aata tha. Rev 12 me cutoff ka share **0%** hai — mat quote karna.

**rev-12 numbers — [historical, superseded by rev 13 — samjho, quote mat karo]**
- Reference SOR 4.50 gross unchanged. Baseline/recommendation gross SOR 4.35→3.19,
  incremental ₹/cycle-day −1,601 → **+7,973 (Δ +9,574)**, decomposition SPM 62%/stroke 32%/
  cutoff 0% — **yeh poora gain baseline ke pull-on-float rule se aata tha**, set-points se
  nahi (technical re-score, 58/100, ka top finding). Rev-13 me isi ko fair-baseline-policy
  se theek kiya gaya — neeche dekho.

**rev-13 numbers — [safe to quote]**
- Reference (1,500/7/1.2/5/86 in/91 kgf, policy `pull`, unchanged): gross **SOR 4.50**
- Baseline (b) aur recommendation dono **VFD-hold** policy pe compare: baseline
  1,300/10/91/86-in/5 spm → **SOR 3.29**, net cash +₹12,064 (FY25) — recommendation
  **1,000/10/89 kgf/64-in/start 4.5 spm/cutoff 0.60 backstop/VFD-hold → SOR 2.83**, net
  cash **+₹15,396** (FY25) / +₹3,738 ($65) / −₹8,811 (net-of-levies)
- **Gain, baseline ki apni policy naam leke:** same policy (VFD-hold) **+3,332/+4,319/
  +5,382** (decompose: stroke 57%, cutoff 30%, steam 11%); baseline pulle toh
  **+12,917/+14,694/+16,606** (68% sirf policy switch hai); baseline kuch na kare toh
  recommendation **−3,865/−2,513/−1,057 haarta hai** (rod damage unpriced hai)
- Teen honest xfail gaps: no interior soak optimum; mid-diesel-price pe steam optimum
  BGW-8 ke slug range se neeche (naya); rev-12 ka cold-well xfail ab **un-xfailed** hai
  (counterfactual policy follow karta hai, sahi se shut in hota hai)

**Numbers jo bol sakta hai**
- **263 passed, 2 xfailed** (documented gaps, not a failure)
- **ML ka honest role:** 6-lever × policy physics grid (40,194 points/policy) decision
  engine hai; surrogate ~24% neeche land karta hai — sirf ek cross-check. Float classifier
  ab sirf informational hai, constraint nahi — uski jagah ek **hard injectivity gate**
  (≥400 kPa) hai
- **FI threshold 0.6.** VFD-hold: FI ko 0.6 pe **hold** karta hai 2-spm floor tak, phir 3
  alarm din baad pull. Rods ~55–60 din tak alarm line pe rehte hain (damage index ~5× pull
  policy se) — **yeh cost model me unpriced hai**
- **Per-cycle economics:** 71 kg HSD/t steam, discount base ab **0.15** (0.30 se) →
  **~₹7,111/t bulk / ₹8,366/t retail**; **net-of-levies deck** (~₹3,600/bbl, ~35% levies)
  pe har feasible point negative hai
- **UQ (1,500 draws, 3 decks):** P(injectable)=1.000 sab jagah; same-policy P(rec>baseline)
  VFD-hold **0.965/0.992/0.999** (FY25/$65/levies); baseline pulle toh 0.99+; baseline
  kuch na kare toh sirf 0.16–0.25
- **Calibration demo:** formation_water_cut/aof/thickness recover within
  **−5.2/−0.9/−10.9%** (BL fixed, rev-13 pe re-run, kahani same)
- **Naye modules:** measured dyno-card classifier (94.8% hold-out, kabhi field-validated
  nahi), field scheduler (har well ab VFD-hold: naive **+₹72,320/d**, exact **+₹109,799/d**,
  10/12 wells serve)

**Honesty lines — word for word**
- *"Baghewala's own SOR isn't published — we benchmark against the literature 3-8 range."*
- *"Zero real cycles in our training data. All physics-generated."*
- *"Physically plausible, not field-validated — two different claims."*
- *"Bayesian optimisation doesn't guarantee a global optimum."*
- *"That's an assumption, and here's why we made it."*
- *"First ask of OIL: cycle records and dyno cards."*
- *"We never claim an absolute CO₂ reduction — only SOR and CO₂-per-m³-oil fall."*
- *"Soak is fixed at field practice, not a twin-derived recommendation."*

**Kabhi mat bolna**
- −30% · −41.3% (bina "v1 prototype, audited and replaced") · rev-5 ka "+188% margin" ·
  rev-9 ka "+4,423/cycle-day" ya "cutoff drives 83–96%" bina label ke · rev-12 ka
  **"+₹9,574/cycle-day"** bina yeh bataye ki woh ek **pulling baseline** assume karta tha ·
  "62% SPM / 32% stroke" (purana decomposition — ab stroke 57%/cutoff 30%/steam 11% hai) ·
  **"236 tests"** (ab **263** hai) · ₹0.61 cr/yr · 6.8 cycles/yr · ₹1,300/t · 24/24 ·
  116/127 tests · 471 bbl/d · μ 0.63 cP · Baghewala ka koi SOR · "validated on real data" ·
  "verified improvement" · R² ko accuracy · "our engine was 25% optimistic" (25× hai) ·
  **250 km** (550-600 hai) · OIL ka koi SIH track record · absolute CO₂ reduction per
  cycle · soak-day recommendation · "cross-validation" · **gross margin ko profit bolna** ·
  **"BL factor unverified hai"** · measured-card classifier ko **"field-validated"** bolna ·
  ek **single gain number bina baseline ki apni float policy bataye**

**Demo — muscle memory**
- Default **MOCK mode, `dashboard/console.html`**. Flag: **`dashboard/src/core.js:9`**,
  badla toh `node dashboard/build.js`
- Commands `.venv\Scripts\python.exe` se · bare `python` **broken**
- Sequence: problem numbers → **Simulate** (published-practice baseline baked) → **Replay:
  water cut girta dikhao, VFD unit ko slow karta dikhao FI ko 0.6 pe hold karte hue —
  "VFD slowing" banner** (rev-13 ka naya 15-second moment) → dyno card (*computed — Gibbs
  wave equation*; measured-card upload ek optional 30-s beat) → **Optimise** → SOR/margin
  bars (*physics-verified: same policy, VFD-hold, +₹3,332/cycle-day; Recommendation page ka
  baseline-policy toggle — teeno number dikhana — yehi honesty ka moment hai*) → field-view
  scheduler ek optional beat hai
- Submit deck = **`ppt/final/SIH26120_Idea_Presentation_STRICT.pdf`** — ab rev-13 numbers pe
  rebuild ho chuki hai. Baaki `ppt/archive/`.

**Pehla kaam**
- Idea-submission deadline **30 Sep 2026** — portal pe time se pehle upload
- Deck pe `TEAM ________` aur Team ID `TBD` bharna (agar abhi bhi khaali hai)

---

## PART 3 — ANSWERS

**1.** `μ = A·exp(B/T_K)`; A = 1.164×10⁻⁶, B = 7,436 K. **11,500 cP @ 50 °C = asli**
(CONFIRMED, OIL internal PPT ka midpoint). **50 cP @ 150 °C = ASSUMPTION** — Baghewala ka
koi high-temperature viscosity measurement kahin nahi mila. Bonus point: Andrade ko 290 °C
tak kheencho toh 0.63 cP (paani se patla) — isliye v2 me **Walther / ASTM D341 + 1 cP
floor**, same anchors, 290 °C pe 4.13 cP. OIL ka lab point milte hi 150 °C anchor replace.

**2.** Asli drainage radius = well kitne door tak ke rock se oil kheenchta hai, well spacing
se aata hai, typical **50–150 m**. v1 ka 8 m ek **saturation knob** tha: heated disc (~7 m)
ko 8 m disc ke against tolte the; ~1,750–2,000 t pe disc "bhar" jata tha, extra steam se oil
nahi badhta, SOR wapas mudta — "optimum". 10 m pe optimum range me nahi aata tha, isliye 8 m
pe **retune** kiya — yaani optimum ek **fudge** tha. v2 me yeh delete; ab **drainage radius
100 m** hai aur **composite-radial (Boberg–Lantz) uplift** ke andar use hota hai.

**3.** `μ_ref/μ` poore reservoir ko garam-oil mobility de deta tha — 244 °C pe ~5,000×. Asli me
sirf well ke paas ek chhota ring (r_h ~3–7 m) garam hota hai; bahar 100 m tak thanda shahad
flow ko rokta hai. Nateeja: v1 single-well peak **471 bbl/d** vs poora field ~655 bbl/d (~19
bbl/d/well). v2: `uplift = R_cold / R_hot` (garam ring + thanda annulus ka resistance) → **~4×**
(cap 10×), peak **13–23 bbl/d**. Saath me P_wf ab absolute (~1,144 kPa) aur P_res(t) live, toh
pressure bhi rate hilata hai.

**4.** `FI = min(F_v / W_b, 1)`, jahan `F_v = K_VISC·μ·v_avg·L` aur
`v_avg = 2·stroke·spm/60`. Drag **rod velocity me linear** hai aur velocity SPM me linear —
toh SPM double karo, drag double; denominator (buoyant weight) bilkul nahi badalta.
Concretely: 8 spm pe 0.6 ~2,450 cP pe cross hota hai, 12 spm pe ~1,635 cP pe.

**5.** **Cooling — matlab badhti viscosity.** Wahi ek μ dono jagah baithi hai: IPR ka
mobility term `μ_ref/μ` girta hai (rate down) aur rod drag `K_VISC·μ·v·L` badhta hai (load
up). **Yahi coupling poore project ka point hai** — isi liye steam schedule aur pump ko
alag-alag optimise nahi kar sakte.

**6.** Steam volume ek **amount** hai, duration nahi. Injection time = 1,500 ÷ **74 t/d** =
**20.27 din**. 74 t/d OIL ke apne BGW-8 first-cycle rate (~3,100 kg/hr) se aaya hai —
CONFIRMED — aur reported 14-21 din wale window ke andar baithta hai.

**7.** **Pump**, reservoir nahi. `A_plunger × stroke × (spm × 1440) × 0.85`
= 2.552×10⁻³ × 3.0 × 11,520 × 0.85 = **74.96 m³/d**. `srp.pump_state` `min(IPR rate, pump
capacity)` leta hai; v1 ka (25× phoola hua) IPR rate isse upar tha, toh **pump hi ceiling
tha**. Pump capacity SPM ke saath linear — toh 10 SPM = zyada ceiling = zyada oil = kam SOR.
Isiliye v1 ka poora −30% **10 SPM** se aaya; practice band 3–6 pe cap karo toh SOR ≈
baseline. v2 me well reservoir-limited hai (peak ~2.8 m³/d), toh SPM ka oil pe asar ~zero.

**8.** Uniform random 4-D me **guch-much** ho jaata hai — 3,000 samples kharch karke bhi
poore region khaali reh sakte hain. LHS **har dimension ko independently stratify** karta
hai: har input range ke 3,000 slices me se har slice ko exactly ek sample. Same compute,
bahut better coverage, edges pe zyada bharosemand surrogate.

**9.** Matlab: surrogate held-out 600-row synthetic split pe **simulated** SOR ki ~72%
variance explain karta hai. **Nahi matlab:** 72% accuracy, aur **bilkul nahi** matlab
real-world accuracy. Yeh naapta hai ki XGBoost ne *hamare physics engine* ko kitna achha
seekha — na ki hamara engine Baghewala se kitna match karta hai. Do alag claims.

**10.** Rev 12 tak: additive penalty — `if float_prob >= 0.3: penalty = 30,000 ×
(float_prob − 0.3)`, return `margin_pred − penalty`. **Rev 13 me yeh hata diya** — ab
float response khud ek policy (`pull`/`vfd_hold`/`vfd_then_pull`) hai, toh "float risk"
ko penalise karna matlab operating rule ko hi penalise karna (ek re-score finding). Uski
jagah ek **hard injectivity gate**: candidate ka sandface pressure reservoir pressure se
kam se kam 400 kPa upar hona chahiye — yeh ek real physical constraint hai (steam physically
formation me ja hi nahi sakta uske neeche), koi soft threshold nahi.

**11.** Grid cost = `levels^dimensions`. Char knobs, sirf 10 levels each = **10,000
evaluations** — aur 10 levels matlab bhaddi 250 t resolution. Bayesian optimisation ne
**60** me answer nikala, kyunki GP surrogate *kahan dekhna hai* woh sikha deta hai aur
proven-hopeless regions pe mehnat waste nahi karta.

**12.** **Kahin publish nahi hua** — aur yehi answer hai. *"Baghewala's own SOR isn't in any
public source, so we deliberately don't quote one. We benchmark against the industry
literature range of 3-8 t/m³, average ~6, with under 3 considered thermally efficient."*
Koi number bolna room haarne ka sabse aasan tareeka hai.

**13.** **Zero real cycles** (par ek real 9,692-cycle California band-check hai). Saare 3,000
training cycles physics-generated hain. Defence: yeh fabricated nahi hain — har row published
models (Marx-Langenheim, Boberg–Lantz, Walther, Vogel, rod mechanics) ka Latin-hypercube
sampled operating point pe solution hai, toh har row energy conservation aur sahi
viscosity-temperature law obey karti hai. Phir **khud close kar de, judge se pehle:** *"That
makes it physically plausible, not field-validated — our own three rounds of auditing this
engine are exactly why. Oil India's cycle records and dyno cards are the first thing we'd
run through our calibration loop against."* (**"1 ghante me recalibrate"** mat bolna — kuch
constants abhi bhi code me hain, jaise pump geometry aur net-pay thickness; `BL_DELTA_FACTOR`
ab **sourced** hai, iski list me nahi hai.)

**14.** **`ppt/final/SIH26120_Idea_Presentation_STRICT.pdf`** (aur `.pptx`) submit karni hai —
official SIH template, 6 slides, pointers unchanged; screeners format deviate karne wali decks
drop kar dete hain. VISUAL / VISUAL_EDITABLE ab **`ppt/archive/`** me superseded hain — sirf
practice. Deck ab **rev-13 numbers pe rebuild ho chuki hai** (slide 2 WHAT/WHY, slide 6 har
reference ke saath clickable URL/DOI). Slide 5/Impact ka −41.3%: *"That's our v1 prototype
simulation, labelled as such, against the optimiser's own midpoint baseline. We've since
been through several more audits, including a technical re-score — and our current,
same-policy recommendation gains three thousand three hundred rupees a cycle-day against a
baseline that also slows down first, at OIL's own confirmed FY25 price."*

**15.** **MOCK mode (default), `dashboard/console.html`** pe. Flag **`dashboard/src/core.js:9`**
(`const MOCK = true;`); badla toh `node dashboard/build.js` aur refresh. MOCK me baked
scenarios abhi purani physics ke hain (rev-13 re-bake pending — stage pe rev-13 numbers hi
bolne hain, dashboard nahi), aur **dynamometer card computed hai** (Gibbs wave equation);
baaki set-points ke oil/margin numbers in-browser approximation hain — waise hi bolna.
Dashboard API fail hone pe khud mock pe nahi girta — "Data source error" dikhata hai.
**20 second se zyada live debug nahi**, ek se zyada baar sorry nahi.

---

**Yaad rakhne wali baat:** score jo bhi aaye, ghabrana mat. Jo galat hue, unke liye file
number note kar (physics → 03, ML → 04, system → 05, Q&A → 06) aur sirf **wahi** dobara
padh. Aur presentation wale din — sirf **Part 2 wala 1-pager** padhna hai, poora pack nahi.
Chal, best of luck bhai. 🔥
