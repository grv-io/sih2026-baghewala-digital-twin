# 00 — START HERE (Gaurav ka apna study pack)

> ## ✅ STATUS — 27 Sep 2026 (rev 13 — physics wave 5, "float pe operator kya karta hai, yeh khud ek control hai" — pehle yeh padh)
>
> - **rev 12 ab historical hai — v1 aur rev-9 ki tarah.** rev 12 ka headline
>   (+₹9,574/cycle-day) asal me ek **pull rule ka artifact** nikla: baseline (b) ko
>   float alarm pe turant pull kar diya jaata tha jab woh abhi bhi achha oil de raha
>   tha. Jaise hi twin ke apne VFD-slow mode se compare kiya, yeh gain **+₹3,332 pe
>   gir gaya**. Kabhi bhi 1,000/85/3-spm, SOR 3.19, +₹9,574, 62% SPM, ya "236 tests"
>   quote mat karo — sab superseded rev 12 hai.
> - **Rev 13 ki ek-line kahani: rods float karein toh operator SLOW karta hai ya PULL
>   karta hai — yeh choice khud ek CONTROL hai, aur kisi bhi set-point se zyada paisa
>   yehi move karta hai.** Chaar policies (`css.float_policy`): `pull` (rev-12 wala —
>   SPM keep-up limit pe chalao, 3 alarm din ke baad well pull karo), **`vfd_hold`**
>   (**RECOMMENDED** — VFD pump ko slow karke floating index ko 0.6 pe hold karta hai,
>   floor 2 spm, sirf floor pe 3 alarm din persist karne ke baad pull), `vfd_then_pull`
>   (floor thoda upar), aur `none` (float ignore, sirf rate cutoff pe cycle khatam).
>   Yeh SAME policy baseline, recommendation, **aur** cold counterfactual — teeno pe
>   equally apply hoti hai (pehle sirf recommendation pull karta tha, baseline nahi).
> - **Recommendation, dono VFD-hold policy pe** (yeh table quote kar sakte ho):
>
>   | | steam t | soak d | pressure kgf/cm² | stroke in | start spm | cutoff | SOR | ended by | net cash ₹/cycle-day (FY25/$65/net-of-levies) |
>   |---|---|---|---|---|---|---|---|---|---|
>   | Baseline (b), VFD-hold | 1,300 | 10 | 91 | 86 | 5 | 1.3 | 3.29 | float pull @ 2-spm floor | +12,064 / −582 / −14,193 |
>   | **Recommended, VFD-hold** | 1,000 | 10 | 89 | 64 | 4.5 | 0.60 backstop | **2.83** | float pull @ 2-spm floor | **+15,396 / +3,738 / −8,811** |
>
> - **Gain KABHI ek akela number me mat bolo — hamesha bolo baseline ki apni
>   float-policy ke naam ke saath, teeno number ek saath:**
>   - Baseline bhi VFD-hold kare (FAIR, same-policy comparison): **+₹3,332 / +4,319 /
>     +5,382** (FY25/$65/net-of-levies) — stroke 57%, cutoff 30%, steam 11% se aata
>   - Baseline pehle hi alarm pe pull kar de (rev-12 wala operation): +₹12,917 /
>     +14,694 / +16,606 — **68% yeh sirf policy switch hai**, set-point nahi — yehi
>     purana "+₹9,574" headline asal me tha
>   - Baseline float ko bilkul ignore kare, kuch na kare: **−₹3,865 / −2,513 /
>     −1,057** — float-safe recommendation yahan **paisa kho deta hai**, kyunki model
>     rod-failure/workover cost ko price hi nahi karta
> - **Naye honest gaps:** ab cold well har float-policy ke under **shut in** hai
>   (pumpable nahi — rev-12 wala "idealised pumpable" reading ek doosri, niche wali
>   reading ban gaya hai, ~₹11.4k/d kam); net-of-royalty-cess deck pe (~₹3,600/bbl,
>   ~35% levies, OIL ki apni FY25 Annual Report se cross-checked) **har feasible
>   point negative hai**; 0.15 diesel-discount pe best slug size (~750 t) BGW-8 se
>   (1,040–1,560 t) kam hai — naya strict xfail. VFD-hold rods ko ~55–60 din alarm
>   line (FI 0.6) pe hold karta hai — **rod-string failure cost model me kahin
>   price nahi hota**, isiliye "float ignore karo" baseline ke against loss dikhta hai.
> - Objective ab **net cash per cycle-day** hai (counterfactual-free) — incremental
>   margin nahi, kyunki woh khud policy switch ke saath badal jaata (cold well ka
>   counterfactual bhi policy-dependent hai).
> - Stage pe exactly kya bolna hai → file 06 ka stage block, jab woh rev-13 pe
>   update ho — is file ke edit ke time file 06 ka apna status alag se check kar lena.
> - Tests aaj: **263 passed, 2 xfailed** (soak — no interior optimum; mid-range
>   diesel discount pe steam optimum BGW-8 range se neeche — dono documented,
>   expected gaps, not a failure).

Bhai, yeh pack tere liye hai — **Hinglish me, bilkul basic se**. English wala master
guide `docs/study/TEAM_STUDY_GUIDE.md` hai; yeh uska **friendly, samjhane wala
version** hai — dono ab v2-calibrated numbers pe hain, takraav nahi hona chahiye; agar
ho toh upar wala banner aur file 06 ka stage block follow kar.

Ek baat pehle hi clear kar leta hoon: **tu team lead hai aur ChemE wala banda hai.**
Iska matlab — judge jab bhi physics, viscosity, steam, ya "yeh number kahan se aaya"
poochega, sab tere taraf dekhenge. Toh files 01, 03 aur 06 tere liye
**non-negotiable** hain. Baaki bhi padhni hain, par woh teen tera core hai.

---

## Padhne ka order (isi sequence me padh, shortcut mat maar)

| # | File | Ek line me kya hai | Time |
|---|---|---|---|
| 01 | `01_PROBLEM_KYA_HAI.md` | SIH kya hai, PS SIH26120 kya maang raha hai, Baghewala field ki poori kahani, CSS aur sucker rod pump basics | 25 min |
| 02 | `02_HUMNE_KAISE_SOCHA.md` | 233 problem statements me se yehi kyun chuna, backup kya tha, strategy kya hai | 15 min |
| 03 | `03_PHYSICS_SAMJHO.md` | Heat transfer se lekar rod floating tak — poori physics, zero se; v1 kya tha, v2 me kya badla | **~90 min** (zero se; ChemE background ho toh ~60) |
| 04 | `04_ML_OPTIMIZER_SAMJHO.md` | Synthetic data, XGBoost surrogate, R² 0.72 ka matlab, Bayesian optimization, economics, honest claims | 45 min |
| 05 | `05_HUMNE_KYA_BANAYA.md` | Poore system ka tour — kaunsi file me kya, demo kaise (safely) chalana hai | 20 min |
| 06 | `06_JUDGE_KE_SAWAAL.md` | **Stage block (26 Sep)**, top sawaal + jawab, naye tough sawaal, traps, cheat sheet | 60 min |
| 07 | `07_EXAM_MODE.md` | Khud ko test kar — 15 questions + raat wala 1-page revision | 25 min |

**Total: ~4.5–5 ghante — do baithak me kar.** Pehli baithak 01 → 03, doosri 04 → 07.
Agar time kam hai toh minimum: **06 ka stage block → 01 → 03 → 06 baaki.**

---

## Internal round se pehle kya-kya ratta maarna hai — checklist

Yeh cheezein **bina notes ke, bina sochne ke** aani chahiye. Tick karta ja:

### Kahani (30 second me bolni aani chahiye)
- [ ] Baghewala kahan hai, kiska hai, oil kitna gaadha hai — **8,000–15,000 cP @ 50 °C**
- [ ] CSS ka matlab — inject / soak / produce, aur yeh India ka **pehla CSS** field hai (BGW-8, Dec 2018)
- [ ] Problem exactly kya hai — SOR high, rod failures, sab kuch **manual guesswork**
- [ ] Hamara solution ek line me — "ek physics twin jo CSS aur pump ko **saath me** optimise karta hai"

### Numbers jo bol sakte ho (bina calculator ke)
- [ ] Field facts: depth **~1,150 m**, steam **290 °C**, quality **0.65**, **74 t/d** injection, **52 wells**, production **218 t → 43,773 t** (FY17 → FY26)
- [ ] Steam ki keemat: **71 kg diesel (HSD) per tonne steam** → **₹5,856/t bulk / ₹8,366/t retail**, **~224 kg CO₂/t**
- [ ] Reference engine (1,500/7/1.2/5/86 in/91 kgf, shipped default `pull` policy, rev-13 me bhi unchanged): SOR **4.50 gross**
- [ ] Recommendation, VFD-hold policy: **1,000 t / 10 d / 89 kgf/cm² / 64-in / start 4.5 spm, cutoff 0.60 m³/d backstop, SOR 2.83** vs baseline (b), VFD-hold: **1,300 t / 10 d / 91 kgf/cm² / 86-in / 5 spm, SOR 3.29** — net cash ₹/cycle-day **same policy: +3,332 / +4,319 / +5,382** (FY25/$65/net-of-levies); **agar baseline pull kare: +12,917/+14,694/+16,606** (68% policy switch); **agar baseline kuch na kare: −3,865/−2,513/−1,057** — teeno bolna hai ek saath, **kabhi ek akela number baseline-policy naam liye bina mat bolo**. Gain decomposition (same policy): stroke 57%, cutoff 30%, steam 11%
- [ ] Literature benchmark: gross SOR **3–8 t/m³** (avg ~6, CalGEM real 2021 field band 3.47–8.24, Kern River ek steamflood field hai cyclic-steam subset ke saath — field-level SOR band hi, koi cycle-level nahi) — hamara gross SOR isi band ke andar hai; ₹ ki baat ab **net cash per cycle-day** (counterfactual-free) ki karo, na ki incremental margin
- [ ] UQ (1,500 draws, 3 decks): P(injectable) **1.000** har jagah; same-policy P(rec > baseline), VFD-hold: **0.965 (FY25) / 0.992 ($65) / 0.999 (net-of-levies)**; agar baseline pull kare 0.99+; agar kuch na kare sirf 0.16–0.25; gain p10/p50/p90 (FY25) **+2,175 / +12,101 / +161,014** (right-skewed) — dono/teeno deck bolna hai, ek nahi; top drivers: μ_ref, cold-well skin, oil price, formation water cut
- [ ] Tests: **263 passed, 2 xfailed** (soak — no interior optimum; mid-range diesel discount pe steam optimum BGW-8 range se neeche — dono documented gap, failure nahi)
- [ ] ML ka honest role: 6-lever × policy physics grid (40,194 points/policy, ~172s, 4 policies) hi decision engine hai; ML surrogate ~24% neeche land karta hai — surrogate sirf ek fast emulator/cross-check hai, kabhi doosra optimiser nahi. Float classifier ab informational hai, search constraint nahi (injectivity gate ne yeh role liya)
- [ ] Measured dyno-card classifier: 94.8% hold-out accuracy, 5 fault classes — par kabhi field-validated mat bolo, yeh ek synthetic-trained first-read hai
- [ ] Field scheduler demo (12 wells, ek generator, sab VFD-hold): naive policy **+₹72,320/d** (rev-12 pulling policy me yeh −₹13.3k/d LOSS thi — policy switch akela farak hai), exact scheduling **+₹109,799/d** (10/12 wells serve karke)

### v1, rev-9 aur rev-12 numbers — [historical, samjho, quote mat karo]
- [ ] v1: Reference 1,500 t / 7 d / 3.0 / 8 spm → SOR 1.29, 1,159 m³, 61.3 din · optimised 1,600 / 3 / 8.0 / 10 → 0.91 (−30%). Deck slide 5 ka 1.50 → 0.88 (−41.3%) — agar judge slide pe ungli rakhe: *"that's our v1 prototype simulation, since audited and replaced"* (file 06 dekh)
- [ ] rev 9: **1,600 t / 0.70 m³/d / 4 spm → +₹4,423/cycle-day**, "cutoff drives 87%/91% of the gain", "116 passed, 1 xfailed" — yeh sab ek **constant 85% water cut** aur **fixed rate-cutoff rule** pe the, jo ab replace ho chuke hain.
- [ ] rev 12: **1,000 t / 85 kgf/cm² / 3 spm, SOR 3.19 → +₹9,574/cycle-day**, "62% SPM / 32% stroke / 0% cutoff", "236 passed" — yeh sab **`pull` policy ko baseline pe bhi force** karke nikla tha (baseline float pe turant pull hota tha). Rev 13 me jab baseline ko bhi VFD-hold diya gaya, gain **+₹9,574 se +₹3,332** pe aa gaya. **Kabhi mat bolo** +₹9,574, 62% SPM, ya 236 tests as current.
- [ ] **Kabhi nahi:** −30%, ₹0.61 cr/yr, 6.8 cycles/yr, ₹1,300/t, 24/24, 116/127/197/236 tests, 471 bbl/d, μ 0.63 cP, "25% optimistic" (sahi hai **25×**, na ki 25%), Baghewala ka apna koi SOR, koi **absolute CO₂ reduction** per cycle (ek same-policy comparison hai, physics ka law nahi), "cross-validation" (single 80/20 hold-out hai), **gross margin ko profit bol dena**, measured-card classifier ko **"field-validated"** bolna (yeh kabhi field data nahi dekha), aur — rev-13 se — **"+₹9,574"**, **"62% SPM"**, "verified improvement", ya koi bhi **single gain number jisme baseline ki float-policy naam na li ho**

### Honesty lines (yeh word-for-word yaad, kyunki inhi pe game banti-bigadti hai)
- [ ] "Baghewala ka apna SOR published nahi hai — **hum koi number nahi bolte**, literature 3–8 ke against benchmark karte hain."
- [ ] "Hamare training data me **zero real cycles** hain, sab physics-generated hai."
- [ ] "Yeh model **physically plausible** hai, **field-validated nahi** — ye do alag claims hain."
- [ ] "Bayesian optimisation **global optimum guarantee nahi** karta; physics grid hamara real decision engine hai."
- [ ] "Rev 12 me humne paaya ki water cut cycle ke andar badalta hai — shuru me water-continuous, baad me oil-continuous — aur isi wajah se rods **late cycle** me float karte hain."
- [ ] "Rev 13 me humne paaya ki jab rods float karte hain, operator **slow karta hai ya pull karta hai** — yeh choice khud ek control hai, aur set-point se zyada paisa yehi move karta hai. Isliye hum gain kabhi ek number me nahi bolte — hamesha teeno baseline-policy ke saath: same policy +₹3,332/d, agar baseline pull kare +₹12,917/d, agar kuch na kare −₹3,865/d."
- [ ] "Humara recommendation VFD-hold policy hai kyunki woh zyada oil deta hai aur rods kabhi FI=1.0 pe nahi jaate — par rods ~55–60 din FI=0.6 ki limit pe rehte hain, aur uska rod-string damage cost hum **price nahi karte**. Honestly bolna hai."
- [ ] "Hamara model kehta hai ki ek cold, unstimulated well har float-policy ke under **shut in** hai, pumpable nahi — par field ne yeh wells cold produce kiya tha, toh yeh ek upper-bound hai, exact number nahi. Honestly bolna hai, chhupana nahi."
- [ ] "Net-of-royalty-cess deck pe humara har feasible point negative hai — 'kya CSS profitable hai' ka jawab OIL ki apni price/levy sheet degi, hamari assumption nahi."

### Practical
- [ ] Demo ke commands yaad (file 05 me hain) — `.venv\Scripts\python.exe`, bare `python` mat chalana. `generate_data.py` / `train.py` **ab safe hain** current branch pe chalane ke liye — bas time lagta hai (data gen ~24s, retrain thoda zyada) aur current baked data/models **overwrite** ho jayenge
- [ ] Demo default **MOCK mode** me, page **`dashboard/console.html`**. MOCK flag: **`dashboard/src/core.js:9`** (`const MOCK = true;`) — badla toh `node dashboard/build.js` se rebuild. **Live API ab current branch se bhi theek hai** (v2 calibrated hai)
- [ ] Stress test click (12 spm → alarm) — MOCK me yeh **in-browser approximation** hai (panel khud likhta hai), physics output nahi. Dikhana hai toh "illustrative" bol ke dikhana
- [ ] 3-minute pitch **stopwatch ke saath** ek baar practice, team ke har member ko bolna hai

---

**Yaad rakhne wali baat:** yeh pack padhne ka maqsad ratta nahi hai — maqsad yeh hai ki
jab judge beech me tokhe, tu **ruk ke, aaram se, honestly** jawab de sake. Jo cheez tujhe
nahi pata, uske liye ek line hai: *"That's an assumption, and here's why we made it."*
Woh line har baar tujhe bachayegi. Chal, file 01 khol.
