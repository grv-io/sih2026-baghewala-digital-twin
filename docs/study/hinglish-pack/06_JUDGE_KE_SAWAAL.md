# 06 — JUDGE KE SAWAAL (stage block + top 15 + naye tough sawaal + traps + cheat sheet)

> **✅ STATUS (27 Sep 2026, rev 13, physics wave 5):** is file ka **"Stage pe kya bolna
> hai"** block poore pack ka single source of truth hai. v1, rev-5, rev-9 **aur ab
> rev-12 numbers bhi** (gross SOR 3.19, "+₹9,574/cycle-day", "SPM 62% + stroke 32%,
> cutoff 0%") sab **historical** hain — rev 12 me operator "float hote hi pull karega"
> maan liya gaya tha; usi assumption ne poora gain banaya tha. **Ek technical re-score
> (58/100) ne yehi pakda: operator ka float-response khud ek CONTROL hai** — woh pull bhi
> kar sakta hai, VFD se **slow** bhi kar sakta hai. Rev 13 (**wave 5**) is control ko
> `css.float_policy` bana deta hai (`pull` / **`vfd_hold`** / `vfd_then_pull` / `none`) aur
> **SAME policy baseline, recommendation, aur cold counterfactual teeno pe lagata hai** —
> fair comparison ke liye. Recommended policy: **VFD-hold** (float index ko 0.6 pe hold
> karo, floor 2 spm, sirf floor pe 3 alarm din ke baad pull karo). **263 passed / 2
> xfail** tests. Canonical: baseline (b) SOR 3.29 → recommendation SOR **2.83** (dono
> VFD-hold). **Gain ALWAYS baseline ki apni policy naam leke bolo:** same-policy
> (VFD-hold vs VFD-hold) **+₹3,332/d** (FY25) / +4,319 ($65) / +5,382 (net-of-levies);
> agar baseline pull karta hai, +₹12,917/+14,694/+16,606 (68% sirf policy switch hai,
> set-point nahi — purani "+₹9,574" line **yehi** thi); agar baseline kuch nahi karta,
> humara canonical recommendation phir bhi **+₹2,622/+3,484/+4,413 gain karta hai**
> (TIER1 §12.6 "mixed" row) — purani **−₹3,865/−2,513/−1,057** line ek alag,
> non-canonical plan ka number tha, humari recommendation ka nahi, ab retired. Dono
> case me: **rod-failure cost model me hai hi nahi**.

Bhai, yeh file **stage pe kaam aane wali** hai. Har sawaal ke do hisse hain:
**(a)** Hinglish me poora samajh — *kyun* wala part, taaki tu follow-up jhel sake;
**(b)** English me do-line ka polished version — **yehi bolna hai** judge ke saamne.

Ratta mat maar. **(a)** samajh, **(b)** bol.

---

## ★ Stage pe kya bolna hai (27 Sep, rev 13 version)

**★★ SAFE-TO-SAY (≤120 words, ise bolo, result pehle):**

> *"Our operating rule: slow the pump with a VFD as it nears the float limit, and
> only pull if it stays there — the same rule on both sides of every comparison.
> Under that rule, steam per cubic metre of oil falls from 3.29 to 2.83, a 14%
> cut, and we beat our own assumed baseline in 84–96% of simulated runs. The
> rupee gain is real but modest and uncertain: roughly ₹0 to ₹5,000 a cycle-day,
> because it's set by two numbers we don't have — OIL's actual VFD minimum speed
> and their real pull/produce cutoff — both now on our data request. Everything
> here is physics-simulated, not field-validated; 263 of 265 tests pass."*

Neeche **poora/full version** hai — follow-up sawaalon ke liye, opening line ke liye nahi.

**(a) Samajh (full version):** v1 → rev 5 → rev 9 → rev 12 se hote hue, ab **rev 13 (wave 5) aa gayi hai —
humari paanchvi audit**. rev 12 tak har cheez sahi thi — water cut state, float-onset rule,
sab — **par ek chhupi assumption thi: operator float hote hi well PULL karega.** Ek
**technical re-score (58/100)** ne exactly yehi pakda: rev-12 ka poora "+₹9,574/d" headline
is ek assumption ka artefact tha, physics ka nahi — jab humne apne hi twin ko VFD-slow mode
me chalaya (operator pull nahi karta, bas pump slow kar deta hai), **wahi gain gayab ho
gaya.** Iska matlab yeh nahi ki humara model galat tha — matlab yeh hai ki **operator ka
float-response khud ek choice/control hai**, humne usko fix maan liya tha. **Rev 13 isi ko
fix karta hai:** `css.float_policy` ab ek parameter hai — `pull` (rev-12 wali), **`vfd_hold`**
(VFD pump ko slow karke float index ko 0.6 pe **hold** karta hai, floor 2 spm, sirf floor pe
3 alarm din baad hi pull), `vfd_then_pull`, ya `none`. Yeh **SAME policy** baseline, humari
recommendation, AUR cold counterfactual (thanda kuan) — teeno pe lagayi gayi hai, taaki
comparison fair rahe. **Koi calibration knob nahi hila** — sirf diesel discount base
0.30→0.15 (ek economics input hai, physics fit nahi). Isi pass me inversion cliff smooth ki
gayi, ek injectivity gate add hui (≥400 kPa margin), aur ek royalty+cess-ke-baad price deck
add hui.

**(b) Yeh lines bolni hain (order me, zaroorat ke hisaab se — full version, follow-ups ke liye):**

1. *"We've been through five rounds of self- and external audit. Our biggest recent finding
   came from a technical re-score on 27 September: our previous headline gain assumed the
   baseline operator always pulls the well the instant rods float. Once we let the twin's
   own VFD-slowing mode run instead, that gain disappeared — which told us the operator's
   response to float is itself a choice we needed to model, not assume."*
2. *"So in this pass we made that response a real control: the operator can pull the well,
   or slow it with a VFD to hold the floating index at a safe limit, or do nothing. We apply
   the SAME choice to the baseline, our recommendation, and the cold, unstimulated well —
   so no comparison secretly credits itself for a fairer operating rule the other side isn't
   given."*
3. *"Under the recommended policy — VFD-hold — our recommendation runs at 1,000 tonnes of
   steam, a 64-inch stroke, starting at 4.5 strokes a minute, against a baseline of 1,300
   tonnes and 86 inches at 5 strokes — both operated the same way. Steam-oil ratio moves
   3.29 to 2.83."*
4. *"And here's the honest part: the rupee gain depends entirely on what the baseline
   operator actually does. If the baseline also slows down on float — the fair comparison —
   we gain about three thousand three hundred rupees a cycle-day. If the baseline instead
   pulls the well the moment it floats, the gain looks like twelve thousand nine hundred —
   but two-thirds of that number is just the policy difference, not our set-points. And even
   if the baseline does nothing about float at all, our recommendation still gains a little
   — about twenty-six hundred rupees — though we don't yet price the cost of running rods
   floating, so none of these three numbers reflect rod damage."*
5. *"We always name which baseline behaviour a number is against now — a single gain number
   without that label is exactly the mistake the earlier review round caught us in."*
6. *"One more honest cost we don't price: holding the floating index at its limit for
   55 to 60 days a cycle wears the rod string roughly five times harder than pulling early
   would. We don't have a rod-failure or workover cost model yet, so we recommend VFD-hold
   as the economically better policy while saying plainly that its real cost isn't in our
   rupee figure."*
7. *"All training data is still physics-generated — physically plausible, not field-
   validated. Our first ask of Oil India is now whether their operators actually slow the
   unit or pull it when rods float — that single fact changes which of our three gain
   numbers is the real one."*

**KABHI mat bolna:** −30% · −41.3% · ₹0.61 cr/yr · 6.8 cycles/yr · ₹1,300/t · 24/24 ·
116/127/197/236 tests · rev-9's **"cutoff drives 83–96% of the gain"** · rev-12's
**"SPM 62% / stroke 32%, cutoff 0%"** decomposition (ab stroke 57% / cutoff 30% / steam
11% hai, VFD-hold ke under) · **"+₹9,574/d" ya koi bhi single gain number baseline ki
apni float-policy naam liye bina** (yehi is wave ka poora point hai) · a lone
**"−₹3,865/cycle-day"** for the recommendation vs. a do-nothing baseline (yeh number
ek alag, non-canonical plan ka hai, retired — canonical plan wahan bhi **+₹2,622**
gain karta hai) · **"our engine was 25% optimistic"** (sahi **25×**, na ki 25%) ·
471 bbl/d · μ 0.63 cP · Baghewala ke apne SOR ka koi number · **measured-card
classifier ko "field-validated" bolna** · ek **soak-day recommendation** · koi
**absolute CO₂ reduction** per cycle bina "same policy" label ke, ya "makes more oil"
(same-policy comparison me yeh actually **11% less oil** hai) · "cross-validation" ·
**gross margin ko profit bolna** · **"verified improvement"** bina caveat ke ·
**"a petroleum engineer plus a data scientist ne review kiya"** ya **"two independent
external reviews"** (sahi: **do rounds of independent adversarial review — AI-assisted,
persona-based: production engineer + data scientist; judge panel — koi named human
expert nahi**).

### Rev-13 ka ek-block summary (yeh compact block bhi ratta maar)

- **Physics story:** operator ka float-response ab ek **policy control** hai (`pull` /
  **`vfd_hold`** / `vfd_then_pull` / `none`) — SAME policy baseline, recommendation, aur
  cold counterfactual teeno pe. Recommended: **VFD-hold** (float index ko 0.6 pe hold,
  floor 2 spm, floor pe 3 alarm din ke baad pull).
- **Gain ka source: baseline ki apni policy naam lo.** Same-policy (VFD-hold):
  **+₹3,332/+4,319/+5,382** (FY25/$65/net-of-levies), decompose: stroke 57% / cutoff 30% /
  steam 11%. Baseline pulls: +₹12,917/+14,694/+16,606 (68% sirf policy switch). Baseline
  kuch nahi karta: canonical plan phir bhi **+₹2,622/+3,484/+4,413** gain karta hai
  (rod-failure cost dono case me unpriced hi hai — purana **−₹3,865/−2,513/−1,057** ek
  alag, non-canonical plan tha, retired).
- **SOR:** baseline (b) 3.29 → recommendation **2.83** (dono VFD-hold, −14%); 4.35 → 2.83
  agar baseline pull karta hai.
- **Naya honest gap (unpriced):** VFD-hold rods ko float-alarm limit pe ~55–60 din/cycle
  rakhta hai — damage index `pull` policy se ~5× zyada — is rod-wear ka koi ₹ cost nahi
  model me.
- **Cold well ab shut in hai**, "idealised pumpable" nahi, har float policy ke under —
  isliye har absolute incremental ₹ figure ek **upper bound** hai (asli field ne yeh wells
  cold produce kiya tha, toh `pumpable` counterfactual — ~₹11.4k/d kam — zyada
  field-consistent hai).
- **Net-of-levies deck (royalty+cess, naya):** ~₹3,600/bbl pe **har feasible grid point
  negative hai** — "is CSS profitable" ka jawab OIL ki apni price/levy deck decide karegi.
- **Best slug size 0.15 discount pe ~750 t hai** — BGW-8 ke 1,040–1,560 t se kam (naya
  strict xfail; revealed preference — OIL ka asli diesel/steam cost humare mid-range
  guess se sasta lagta hai).
- **ML ka honest role:** physics grid (40,194 feasible points/policy × 4 policies) decision
  engine hai; ML surrogate ~24% neeche land karta hai, sirf cross-check.
- **Field scheduler (12-well demo, sab VFD-hold):** naive policy ab **+₹72,320/d** hai
  (rev 12 me, pulling ke saath, field-wide **loss** thi — policy switch akela hi is farak
  ki wajah hai); exact scheduling +₹109,799/d, 10/12 wells serve karke.
- Tests: **263 passed, 2 xfailed**.

### Deck ab rev-13 numbers pe rebuilt hai — agar judge purani −41.3%/−30% wali line kahin dekh le

**(a)** Submit hone wali deck (`ppt/final/…STRICT`) is pass me **rebuilt hui hai** rev-13
numbers pe — fair same-policy gain, SOR 3.3→2.8, 263 tests, "slow-then-stop" rule, levies
deck, ek honest strip — slide 2 ab sirf **WHAT/WHY** hai (slide 3 se overlap nahi), slide 6
ke har reference pe ab ek **clickable URL/DOI** line hai. Agar phir bhi kahin (purani PDF
copy, browser cache, ya archive) v1 ka "−41.3%" ya dashboard ka purana "−30%" number dikh
jaaye, toh woh **stale artefact hai, current deck nahi** — pehle khud confirm karo ki tum
current `ppt/final/` file dekh rahe ho, phir agar zaroorat pade toh audit ki poori kahani
bata do (v1 → rev 5 → rev 9 → rev 12 → rev 13). Yaad rakhna: 1.50 kabhi bhi field baseline
nahi tha — optimiser ka apna v1 midpoint set-point tha.

**(b)** *"Our submission deck has been rebuilt on our current, rev-13 numbers — the fair,
same-policy gain of about three thousand three hundred rupees a cycle-day, steam-oil ratio
down from 3.29 to 2.83, two hundred sixty-three passing tests, and an honest strip stating
what's still unpriced. If you're seeing an older −41.3% or −30% figure anywhere, that's a
stale copy — the current deck and dashboard agree on the numbers above."*

**Agar koi "commit to 20–30%" wali line poochhe** (purane drafts me thi): *"That's the
literature benchmark for SOR reduction. Our own verified, same-policy result is a
steam-oil-ratio cut from 3.29 to 2.83 alongside a net-cash gain of about three thousand
three hundred rupees a cycle-day at OIL's own confirmed FY25 price, against a baseline
operated the same way we operate our own recommendation — we always name that baseline
policy, because the gain changes a lot if the baseline behaves differently."*

---

## A. Physics / domain (8)

### 1. Viscosity temperature ke saath itni tezi se kyun girti hai?

**(a)** Heavy crude lambi chains aur asphaltenes ka jaal hai. Andrade: `μ = A·exp(B/T)` —
**exponential**, kyunki flow *thermally activated* hai, reaction ki tarah jise energy
barrier paar karna hai. Thande end pe kam molecules ke paas woh energy hoti hai, isliye
same 10 °C ka jump thande side pe kaeen zyada viscosity girata hai. Baghewala:
**11,500 cP @ 50 °C** — normal 18° API crude se ~90-100x gaadha. v2 me same do anchors pe
**Walther / ASTM D341** fit hai (petroleum standard) aur **1 cP floor** — kyunki Andrade ko
290 °C tak kheencho toh paani se patla (0.63 cP) aata tha.

**(b)** *"Viscosity is thermally activated, so it falls exponentially with temperature — a
small rise near the cold end buys a huge drop. We fit to Baghewala's own confirmed 11,500 cP
at 50 °C, using the ASTM D341 Walther form with a 1 cP floor so it stays physical at steam
temperature."*

### 2. CSS ke "soak" phase me physically hota kya hai? Optimal soak kitna hai?

**(a)** Well **shut-in** kar dete hain. Steam condense hoti hai, latent heat rock aur oil ko
deti hai, aur garmi **conduction se andar tak failti** hai — production flow ke saath turant
bahar nahi bah jaati. Pressure bhi equalize hota hai. Chhota soak = garmi wellbore ke paas
atki; lamba soak = overburden me leak. **Honest part:** v1 optimiser ne 3 din chuna tha —
par woh v1 ki fast τ = 20 d cooldown ka artefact tha (har soak din = seedha garmi ka
nuksaan). **OIL khud 7–13 din soak karta hai.** v2 (Boberg–Lantz, calibrated) me soak ka
SOR pe asar **monotone par flat hai** (3→15 din me sirf ~1.2% girta hai — koi interior
optimum nahi, strict xfail marked). Isliye recommendation me soak ko **field practice
(10 din) pe fix rakha hai**, twin se derive nahi kiya — "the model recommends N-day soak"
kabhi mat bolna.

**(b)** *"The well is shut in so the latent heat conducts deeper instead of flowing straight
back out. Our early prototype pushed soak to 3 days, but that was an artefact of an
over-fast cooldown model. Our calibrated Boberg–Lantz model shows soak's effect on SOR is
monotone but nearly flat — under 2% from 3 to 15 days — so there's no interior optimum to
recommend. We hold soak at OIL's 10-day field practice rather than claim the model found a
number."*

### 3. Steam ka optimum volume kyun hota hai — "zyada hamesha better" kyun nahi?

**(a)** General idea sahi hai: har extra tonne thoda aur oil deta hai, par **marginal** oil
girta hai — heated zone bada hone pe surface area badhta hai, garmi leak hoti hai, aur v2 me
bahar ka thanda annulus flow ko rokta rehta hai. Steam ka cost per tonne linear hai (diesel).
**Par honest part:** v1 me SOR ka "~1,750 t optimum" ek tuned 8 m "drainage disc" se aata
tha — asli drainage radius 50–150 m hota hai; woh ek fudge tha jo humne delete kar diya.
v2 (calibrated) me SOR steam ke saath **monotone badhta rehta hai — kabhi neeche nahi
mudta**. **Asli optimum SOR ka nahi, net cash ₹ margin per cycle-day ka hai** — rev 13 me
(VFD-hold policy ke saath) woh margin **1,000 t (grid ka floor)** pe hi sabse zyada hai,
kyunki gain steam badhane se nahi, **rods VFD se slow rakhne aur short-stroke chalane se**
aata hai (decomposition: stroke 57%, cutoff 30%, steam sirf 11%). 1,000 t hi recommend kiya
hai kyunki BGW-8 ka smallest published job ~1,040 t tha — **par ek naya honest gap:** humare
mid-range (0.15) diesel-discount assumption pe grid ka apna gross-margin optimum ~750 t
nikalta hai, BGW-8 ke range se **neeche** — disclosed strict xfail. Ulta padho toh: OIL ka
asli diesel/steam cost humare mid-range guess se sasta hoga, isliye woh bade slug afford
kar paate hain.

**(b)** *"Marginal oil per tonne falls as the heated zone grows and loses heat, while steam
cost stays linear. SOR itself never turns back down under our calibrated physics — it just
rises more slowly. Under our recommended VFD-hold policy, the honest optimum sits at the
low end of our steam range, around 1,000 tonnes, because most of the gain now comes from
slowing the pump and shortening the stroke, not from more steam — steam itself is only
about 11% of the gain. One disclosed gap: at our assumed mid-range diesel discount, the
model's own gross-margin optimum is actually smaller than that, around 750 tonnes — below
what BGW-8 used, which we read as evidence OIL's real steam cost is cheaper than our
assumption."*

### 4. Dynamometer card kya hai, aur rod floating usme kaise dikhta hai?

**(a)** Dyno card = polished-rod **load vs position** ek poore stroke pe — pump ka ECG.
Healthy card smooth parallelogram-jaisa loop hota hai. **Rod floating** tab hota hai jab
downstroke pe viscous drag itna ho ki rod string utni tezi se gir hi na paaye jitni pump
chahta hai — carrier bar **separate** ho jaata hai (load zero), rod apne hi weight se girta
hai, phir **slam** karta hai jab carrier wapas pakadta hai. Card pe: flattened downstroke +
sharp load spike. Rod fatigue failure ka bada kaaran. **[Naya, rev 6/9] Ab computed hai** —
`twin/dyno.py` ek Gibbs (1963) rod wave-equation finite-difference solve karta hai (surface
+ pump card dono), RP-11L chart-lookup nahi, kyunki RP-11L me carrier-bar separation model
hi nahi hota. 12 SPM stress test pe carrier separation independently SPEC ke ≈0.6
floating-index alarm line ke saath match karta hai.

**(b)** *"A dynamometer card plots rod load against stroke position — the pump's
fingerprint. Floating shows up as the carrier bar separating — load drops to zero — then a
slam when it re-catches. Our card is computed from a Gibbs 1963 rod wave-equation
finite-difference solve, not an RP-11L chart lookup, specifically because RP-11L has no
carrier-bar-separation model. At our 12-strokes-per-minute stress test, the computed
separation onset independently matches our floating-index alarm line at about 0.6 — two
different pieces of physics agreeing."*

### 5. CSS shallow wells tak hi kyun — aur Baghewala 1,150 m pe hai, problem nahi?

**(a)** Steam neeche jaate hue heat khoti hai, toh gehre wells me bottomhole quality girti
hai. Industry rule of thumb ~1,000-1,500 m **(verify — Baghewala-specific study nahi)**.
Baghewala **~1,100-1,150 m** — window ke **edge** pe. Isi liye OIL **vacuum-insulated
tubing** use karta hai aur **downhole electric heaters** trial kar chuka hai. **Ab v2 me
wellbore heat loss model hota hai:** ~11% heat loss aur sandface quality = 0.55 × wellhead
(0.65 → ~0.36). v1 isko ignore karta tha — jo **optimistic** tha, conservative nahi.

**(b)** *"Steam loses quality down the wellbore, so CSS gets harder past roughly 1,000–1,500 m,
and Baghewala sits at that edge — which is why OIL uses vacuum-insulated tubing. Our
corrected model now includes wellbore heat loss: sand-face quality is about 55% of wellhead."*

### 6. SOR kya hai, aur yehi economic metric kyun?

**(a)** SOR = tonnes steam ÷ m³ oil, ek cycle pe. Ek number me heating efficiency, viscosity
reduction aur pump performance baandh deta hai, kyunki **steam banana thermal recovery ka
sabse bada recurring opex hai** (Baghewala me diesel se). Literature: **3-8, average ~6, 3 se
neeche efficient**; CalGEM ka real 2021 field-level band **3.47–8.24** bhi isi ke andar hai
(reference SOR band rev 12 me **3.0–4.6** re-specify hui, kyunki AOF field peak band ke liye
retune hui — rev 13 ne yeh band nahi hilaya). Price-independent hai, toh literature se
compare ho sakta hai — isliye **headline SOR gross rehta hai** (steam ÷ saara oil).
**Rev 13 se ek simplification bhi aayi hai:** ab (float policy ke under) model ka cold,
unstimulated well **shut in** maana jaata hai (0 oil), toh incremental oil = gross oil, aur
SOR_incremental = SOR_gross exactly — alag se do number report karne ki zaroorat nahi (jaise
rev 12 me thi, jab cold well ek "idealised pumpable" well maana jaata tha aur incremental
SOR gross se alag aata tha). Recommendation ka SOR (VFD-hold, baseline ke against) **2.83**
hai; reference cycle (shipped `pull` default) **4.50** hai, unchanged.

**(b)** *"SOR is tonnes of steam per cubic metre of oil — it collapses heating efficiency and
pump performance into the number that drives fuel cost, and it's comparable to the
literature's 3-to-8 range and a real 2021 California field band of 3.47 to 8.24. We keep SOR
gross for that comparison; the rupee decision now runs on net cash per cycle-day, and since
our model shuts the cold well in under every float policy, incremental oil equals gross oil
here — one number, not two."*

### 7. Thermal recovery hi kyun — thanda pump kyun nahi kar sakte?

**(a)** PS: 17-19° API @ 46-48 °C; literature (SPE-23APOG + OIL): **14-17° API @ ~50 °C,
8,000-15,000 cP**. Dono agree — heavy-oil regime. Calibrated v2 model me cold rate is now
below the cutoff floor → bina steam ke uneconomic. Field proof: BGW-8 ke pehle CSS cycle ne
**5-6x uplift** diya. **Dhyan:** 5–6× ko **apne model ka proof** mat banana — v1 **135×**
deta tha, toh woh match hi nahi karta tha. Calibrated reference cycle (shipped `pull`
default, rev 13 me bhi unchanged) **5.41×** deta hai — band ke andar (uplift AOF-invariant
hai, isliye retune se bhi nahi hilta), par yeh **sanity check hai, validation nahi.**
Recommendation (VFD-hold) ka apna uplift is se thoda alag hai kyunki ab woh 196 din tak,
2-spm floor pe, float-index limit pe pump karta hai — cold rate ke against uplift 2.3–4.5×
ke beech har case me aata hai; yeh recommendation ki honest property hai, calibration ka
gap nahi.

**(b)** *"Cold, this crude barely flows — well below any economic cutoff in our model.
Baghewala proved the fix itself: BGW-8's first CSS cycle gave 5-6× uplift. Our calibrated
model's reference cycle gives 5.41×, inside that band — a sanity check, not a validation.
Our recommendation runs a different operating policy — it holds the rods at their float
limit for most of the cycle — so its own uplift moves in a 2.3-to-4.5× range depending on
how the baseline is operated; that's an honest property of the policy, not a calibration
gap."*

### 8. "Steam quality" ka matlab, aur yahan kyun matter karta hai?

**(a)** Quality = injected steam ka woh mass fraction jo actually **vapour** hai. Vapour hi
latent heat leke jaati hai, toh quality batati hai kitni asli heat pahunch rahi hai. BGW-8 pe
wellhead quality **60-70% confirmed** (OIL data) → params me **0.65**. Aur 1,150 m neeche
sandface pe aur kam — v2 me 0.55 × wellhead ≈ 0.36.

**(b)** *"Quality is the vapour mass fraction, and vapour carries the latent heat. BGW-8's
reported wellhead quality is 60-70%, so we use 0.65 — and we derate it to roughly 0.36 at
the sand face for wellbore losses."*

---

## B. ML / software (4)

### 9. Physics-based synthetic data "fake data" kyun nahi hai?

**(a)** Har row published physics models ko ek Latin-hypercube sampled operating point pe
solve karke bani hai — energy balance aur ek published viscosity law obey karti hai. ML
physics ka structure seekh raha hai, noise nahi. **Par:** published models ka combination
bhi galat ho sakta hai — hamara v1 25× optimistic nikla. Isliye *physically plausible* ≠
*field-validated*. Aur aaj ki CSV v1 physics ki hai; v2 pe regenerate hogi.

**(b)** *"Every row is published physics solved at a sampled operating point, so the ML learns
physical structure. That makes it plausible — not field-validated — and our own audit of the
first engine is exactly why we keep those two claims apart."*

### 10. XGBoost hi kyun, deep learning kyun nahi?

**(a)** Data **tabular** hai aur rows thousands me — yahan gradient-boosted trees
consistently deep nets ko beat karte hain; deep net overfit karega. Plus XGBoost **feature
importance** deta hai, jo reservoir engineer ko "kyun" samjhane ke liye chahiye, aur chhote
real + synthetic mixed data ko achha handle karta hai.

**(b)** *"It's tabular data with thousands of rows, which is exactly where gradient-boosted
trees beat deep learning. XGBoost also gives feature importances, which matters when an
engineer asks why a set-point was recommended."*

### 11. Bayesian optimization ek paragraph me samjhao — aur ML/BO laga kyun?

**(a)** BO ek **surrogate** (Gaussian Process) banata hai jo har point pe SOR ka
*prediction + uncertainty* deta hai; **acquisition function** agla point chunti hai —
exploitation (best ke paas) vs exploration (jahan uncertainty zyada). 60 evaluations; 4 knobs
× 10 levels ka grid 10,000 maangta. **Honest part:** aaj ka physics cycle **0.55 ms** me
chalta hai — "physics slow hai isliye ML" **galat** hai. BO aur surrogate isliye hain ki
(1) optimiser ek fixed contract se baat karta hai, (2) jab physics CMG-class simulator banegi
(ek run = minutes/ghante) tab yahi setup kaam aayega, (3) batching, (4) dashboard ke live
what-if sliders. **P(float) ab constraint nahi hai** (rev 13 me hataya gaya, N7 dekho).
Poora jawab Q N7 me.

**(b)** *"Bayesian optimisation fits a probabilistic surrogate and balances exploring and
exploiting, so it needs tens of evaluations, not thousands. Today our physics is fast enough
to call directly — the surrogate is there for a stable interface and for when the physics
becomes a full thermal simulator."*

### 12. Real ground-truth ke bina validate kaise kiya?

**(a)** Jo honestly validate ho sakta hai: **physics-consistency tests** (T badhe toh μ gire,
zyada steam se heated radius bade), monotonicity aur bounds, aur **literature-benchmark
tests** (SOR band 3.0–4.6 at reference, uplift 5–6× at reference, peak 15–40 bbl/d) — aaj
`pytest tests -q` pe **263 passed, 2 xfailed**. Do xfail = documented, expected gaps (no
interior soak optimum; steam optimum at the mid-range diesel price sits below BGW-8's slug
range) — strict xfail, failure nahi, dono `docs/model-improvement/TIER1_PROGRESS_LOG.md`
§12 me explain kiye gaye hain. Plus field-plausibility sanity checks (reference peak
15.1 bbl/d vs field ~19 bbl/d/well). Yeh **internal consistency + literature benchmarks**
hain, field validation nahi.

**(b)** *"We validate what can honestly be validated: physics-consistency, bounds, and
literature-benchmark tests — 263 of 265 pass, with 2 strict xfails for gaps we've
characterised and documented rather than hidden — no interior soak optimum, and a cold
well our model can't rod-pump at practice speed under any published emulsion law. Plus
field-plausibility checks against Baghewala's per-well production. That's internal
consistency and benchmark agreement, not field validation, and we say so."*

---

## C. Business / strategy (3)

### 13. Digital twin aur SCADA me farak kya?

**(a)** SCADA **monitoring aur control signals** ka system hai — data collect karta hai,
commands bhejta hai. Par woh nahi samajhta ki well aisa behave *kyun* kar raha hai. Twin ek
physics + ML model hai jo andar ka behaviour mirror karta hai, isliye change ka result
**pehle se predict** kar sakta hai aur set-point recommend kar sakta hai. SCADA hamara input
source bhi hai, output channel bhi. **Twin dimaag, SCADA nervous system.**

**(b)** *"SCADA collects and transmits; it doesn't model why the well behaves as it does.
The twin predicts the outcome of a change before you make it and recommends set-points —
the twin is the brain, SCADA is the nervous system."*

### 14. Weatherford / Lufkin / ChampionX toh yeh bechte hi hain — tumhara alag kya?

**(a)** Pehle honesty: **woh mature, asli products hain** — "exist nahi karte" kabhi mat
kehna. Differentiation **integration** hai: woh SRP ko **akele** optimise karte hain, hum CSS
decisions (steam volume, soak) aur SRP settings ko **ek hi loop me** — kyunki thermal well me
dono physically jude hain (steam → viscosity → rod load → floating risk). Plus cost aur
**data sovereignty** — PSU ka data in-house.

**(b)** *"Those are mature products, and they optimise the rod pump in isolation. Our
contribution is coupling the CSS steam cycle and the pump in one loop, because steam
decisions change viscosity, which changes rod loading — plus keeping model and data
in-house."*

### 15. Abhi model ki realistic limitations kya hain?

**(a)** Sabse badi pehle bolo: **(1) Rod-string damage/failure cost pura unpriced hai** —
humari recommended VFD-hold policy rods ko float-alarm limit pe ~55–60 din/cycle rakhti
hai (damage index ~5× `pull` policy se), aur is wear ka koi ₹ cost model me nahi hai; isi
liye ek float-safe baseline ke against humara own recommendation ₹ me **haar** jaata hai.
**(2) Model ka cold, unstimulated well har float policy ke under SHUT IN hai** (pump nahi,
0 oil) — asli field ne yeh wells cold produce kiya tha, toh har absolute incremental ₹
figure isi wajah se ek **upper bound** hai (field-consistent `pumpable` counterfactual
~₹11.4k/d kam deta hai). **(3) Net-of-levies deck pe har feasible point negative hai** —
"is CSS profitable" sawaal ka jawab OIL ki apni price/levy deck decide karegi. **(4) Best
slug size (0.15 discount pe ~750 t) BGW-8 ke 1,040–1,560 t se neeche hai** — disclosed
xfail. **(5) Soak ka koi interior optimum nahi** (Boberg–Lantz me conduction-only cooling
ka koi soak benefit nahi hai). **(6) Zero field data** — sab physics-generated hai, real
cycles se calibrated nahi (par ab CalGEM ke 9,692 real cycles se ek band-check hai).
**(7) Single-well physics, demo-only multi-well scheduling** — real per-well data nahi.
**(8) Analytical, 1D radial** (Marx-Langenheim + Boberg–Lantz), full 3D simulator nahi —
layering/fractures miss. **(9) Koi geomechanics nahi.** **(10) Kuch judgement calls abhi
bhi unsourced hain** — diesel discount base 0.15, daily opex ₹5,000/d, `fi_alarm_days`=3,
`vfd_turndown_frac`=0.5, royalty/cess rates 20%/20% — sab `[ASSUMPTION]`.

**(b)** *"The two biggest honest limitations now: we don't price rod-string damage, even
though our own recommended policy holds the rods at their float limit for 55 to 60 days a
cycle — about five times the wear of pulling early — so what looks like the better
economic choice has a real, unpriced cost. And our model's cold, unstimulated well is shut
in, not pumped, under every float policy, even though the field did produce these wells
cold — so every absolute rupee figure here is an upper bound, and we report the
field-consistent reading alongside it. Beyond that: on OIL's own royalty-and-cess basis
every setting we tried is net-cash negative; our own best steam-slug size drops below what
BGW-8 actually used at our assumed diesel discount (a disclosed test failure); soak has no
interior optimum; we have zero real field cycles (though a real 9,692-cycle California
band-check exists); and a handful of assumptions — the diesel discount, daily opex, the
operator's float-response window, the exact royalty/cess rates — are still unsourced. We'd
rather state those than have them found."*

---

## D. Naye tough sawaal (26–27 Sep, N1–N29) — yeh pakka aa sakte hain

### N1. "Tumhara ek well 471 bbl/d deta hai, jabki poora Baghewala field 655 bbl/d karta hai?"

**(a)** Yeh v1 ka number tha — aur exactly isi comparison se hamare review ne bug pakda. v1
viscosity ratio (~5,000×) ko **poore reservoir** pe laga deta tha. Asli me sirf ek chhota
ring garam hota hai; bahar ka thanda annulus flow rokta hai. Calibrated v2 me composite-radial
(Boberg–Lantz) uplift → reference peak **15.1 bbl/d**, band **15–40 bbl/d** across settings.
Field: 655–1,202 bbl/d across ~34 producers ≈ **~19 bbl/d/well**. Same ballpark — within
literature band, not an exact match (that would be over-claiming validation).

**(b)** *"That was our first engine, and that exact comparison is how we caught it — it
applied the hot-zone viscosity to the whole drainage area. Our calibrated composite-radial
model now gives a reference peak of 15.1 barrels a day, in a 15-to-40 range across settings —
in the same ballpark as roughly 19 barrels a day per well field-wide, which is a sanity
check, not a validation."*

### N2. "Optimum 10 SPM pe hai? Heavy-oil wells toh 3–6 SPM pe chalte hain."

**(a)** Bilkul sahi pakda — v1 me. v1 me pump capacity hi plateau ka ceiling tha, toh tez pump
= zyada oil — poora −30% isi se aaya. **Rev 13 me recommendation practice band (3–6) ke andar
4.5 SPM se START hoti hai** — par ab SPM khud koi lever nahi hai: recommended **VFD-hold**
policy khud hi pump ko slow karke floating index ko 0.6 pe hold karti hai, 2-spm floor tak,
chahe start SPM kuch bhi ho. Real lever ab **stroke length** hai (64-in vs baseline ka
86-in): chhota stroke 2-spm floor pe rod velocity kam rakhta hai, isliye VFD zyada der tak
float-limit pe hold kar paata hai bina pull hue. Decomposition: stroke **57%**, cutoff 30%,
steam 11% (VFD-hold ke under, same-policy comparison).

**(b)** *"You're right, and our own review found the same in the first engine. Our current
recommendation starts inside the practice band, at 4.5 strokes a minute, but start speed
barely matters now — our recommended VFD-hold policy itself slows the pump down to a
2-spm floor to hold the floating index at a safe limit. The real lever is stroke length: a
shorter, 64-inch stroke keeps rod velocity lower at that floor, so the VFD can hold the
float line longer before it has to pull. That's why our decomposition now attributes 57%
of the gain to stroke, not to SPM."*

### N3. "10-day soak field practice hai — tumhara model kya bolta hai?"

**(a)** Calibrated v2 (Boberg–Lantz) me soak ka SOR pe asar **monotone par flat hai** —
3→15 din me sirf ~1.2% girta hai, koi interior optimum nahi (strict xfail, documented).
Isliye recommendation me soak ko optimiser se search hi nahi karwaya — **field practice
(10 din) pe fix rakha hai.** "Model recommends N-day soak" kabhi mat bolna.

**(b)** *"Our calibrated model shows soak's effect on SOR is monotone but nearly flat —
under 2% from 3 to 15 days — so there's no interior optimum. We deliberately hold soak at
OIL's 10-day field practice rather than let the optimiser search it and land on a
meaningless bound."*

### N4. "Tumhara cycle kitne din ka hai — field me CSS cycles 6–18 mahine chalte hain?"

**(a)** v1 me cycle high cutoff (3 m³/d) aur fast cooldown ki wajah se jaldi (61 din) khatam
hota tha. Rev 12 me reference cycle (poora inject+soak+produce) **~178 din** hai;
recommendation cycle **~202 din**, baseline cycle **~167 din** — teeno ab **float-onset**
se khatam hote hain, rate cutoff se nahi. Yeh sab literature ke "months-long produce phase"
band ke andar hain, aur CalGEM ke apne real gap-proxy band ke andar bhi. Field ke 6–18
mahine (poore CSS cycle + downtime) se abhi bhi chhota hai, par cycle duration ke liye sahi
ballpark me hai.

**(b)** *"Our first engine's cycles ended after 61 days from a high cutoff and fast cooling.
Our current model's reference cycle runs about 178 days and our recommendation about 202 —
both now ending on a float-alarm rule rather than a fixed rate, and both comfortably inside
the literature's months-long produce-phase band."*

### N5. "Tumhara model 290 °C pe viscosity paani se kam deta hai?"

**(a)** v1 Andrade extrapolation ne 0.63 cP diya tha — physically impossible. v2 (calibrated):
Walther / ASTM D341 + 1 cP floor → **4.13 cP @ 290 °C**, 7.2 cP @ 244 °C. High-T lab point
OIL se milte hi anchor replace.

**(b)** *"The prototype's Andrade extrapolation did — 0.63 cP, which is impossible. We moved
to the ASTM D341 Walther form with a 1 cP floor; it now gives about 4 cP at 290 °C, which
held up through our full calibration pass. A measured high-temperature point from OIL would
replace our 150 °C anchor."*

### N6. "Floating threshold 0.6 kahan se aaya?"

**(a)** Design choice hai, measured nahi — **par ab do alag jagah se cross-check hua hai.**
Hamara FI = viscous drag / buoyant rod weight (= rod stroke speed / free-fall speed) — yeh
wahi quantity hai jo published work me **scaled load ratio** hai (SPE 233386 me learned
boundary se ~14 din pehle failure prediction). 0.6 us learned boundary ka role play karta
hai. Hamara **computed dynamometer card** (`twin/dyno.py`, Gibbs wave equation)
**independently** carrier-bar separation ka onset dikhata hai jo ≈0.6 FI ke around hi hai —
do alag mechanisms (ek design threshold, ek poori tarah computed rod dynamics) same jagah
converge kar rahe hain. Rev 12 se drag ab **Pal–Rhodes emulsion viscosity** se aata hai
(water cut ke against, 10× capped) — reservoir oil ki apni viscosity se nahi — isliye FI ab
**water-cut-dependent** hai, aur late-cycle me hi 0.6 cross karta hai. `K_VISC` isi ke
around tune hai. OIL ke dyno cards + failure log se abhi bhi re-fit hoga.

**(b)** *"It's a design threshold, not a measured one — but it's now cross-checked two
ways. Our index is the same physical quantity as the scaled load ratio used in published
rod-failure prediction, and our separately computed dynamometer card — a full rod
wave-equation solve — independently shows carrier-bar separation starting right around that
same 0.6 line. Two different pieces of physics agreeing is reassuring, but we'd still
refit it on OIL's real dyno cards and failure records."*

### N7. "Physics 0.55 ms me chalti hai, toh ML kyun? Aur apni hi physics pe train karna circular nahi?"

**(a)** Seedha maan lo: speed reason **nahi** hai (surrogate 1.13 ms, physics se slow). Honest
reasons: **contract-first** (optimiser/API/dashboard ek stable interface se baat karte hain),
**future-proof** (CMG STARS-class simulator ya multi-well model aaye toh ek run minutes/ghante
— tab surrogate zaroori), **batching**, aur dashboard ke live what-if sliders ke liye. ML ab
optimisation **constraint nahi** hai — rev 13 me soft P(float) ≤ 0.3 penalty hata di gayi;
uski jagah do real physical limits hain: **injectivity gate** (≥400 kPa sandface margin) aur
FI ≤ 0.6 float-policy rule khud. Circular?
Haan — surrogate physics se behtar kabhi nahi hoga, woh copy hai. Isliye R² ko "copy quality"
bolte hain, accuracy nahi. Sudhaar field data se aayega (real cycles mix karke).

**(b)** *"Fair — speed isn't the reason; our physics runs in half a millisecond. The surrogate
gives the optimiser a stable contract, it's ready for when the physics becomes a full thermal
simulator, and it drives the dashboard's live what-if sliders. As of rev 13 it isn't an
optimisation constraint any more — the search is limited by two real physical limits instead:
a hard injectivity gate and the FI ≤ 0.6 float-policy rule. And yes, the surrogate can't be
better than the physics it copies — accuracy only improves when OIL's cycle data goes in."*

### N8. "SOR kyun optimise kar rahe ho, ₹ ya NPV kyun nahi?"

**(a)** Hamara optimiser SOR optimise **karta hi nahi** — SOR price-independent aur
literature-comparable hai isliye hum ise **report** karte hain (gross basis pe, headline ke
liye), par ratio hai (chhote cycles ko favour kar sakta hai, oil ki value ignore karta hai,
aur thande kuan ka apna tel bhi credit kar deta hai). **Rev 9–12 me objective incremental ₹
margin per cycle-day tha; rev 13 se objective net cash per cycle-day hai**
(counterfactual-free — kyunki cold well ab float policy ke against alag-alag behave karta
hai, toh incremental metric policies ke beech compare karne pe khud policy-switch ko gain
bata deta) — sahi reason: SOR akela minimise karo toh optimiser steam ko seedha minimum ki
taraf le jayega, jo honest physics hai par field ka goal nahi. **Canonical set-points khud
minimax-regret se choose hote hain FY25 + $65 price decks par** (levies deck report hoti hai
par minimax me nahi), taaki recommendation price ke against robust rahe, sirf FY25 number
maximise na kare. NPV ke liye multi-cycle, field-level schedule chahiye — `ml/schedule.py`
isi disha me ek pehla kadam hai.

**(b)** *"We don't optimise SOR — we report it gross because it's price-independent and
comparable to literature. Our optimiser maximises net cash per cycle-day, counterfactual-
free — we moved off the incremental metric at rev 13 because the cold well's own baseline
behaviour now changes with the operator's float policy, so comparing incremental figures
across policies would silently book the policy switch itself as if it were the
recommendation's gain. The canonical set-points are chosen by minimax regret across the
FY25 and $65 price decks, so the recommendation is picked to be robust to price, not tuned
to maximise one deck. Minimising SOR alone would just push steam to the minimum,
which is honest physics but not the field's actual goal. Full NPV needs a multi-cycle field
schedule, which is on our roadmap."*

### N9. "CSS hi kyun — SAGD ya downhole heater kyun nahi? OIL ne dono try kiye hain."

**(a)** Recovery method hum choose nahi karte — PS specifically CSS + SRP optimise karne ko
kehta hai, aur Baghewala ka running operation CSS hai. SAGD ko aam taur pe mota, continuous pay
aur well pairs chahiye; Baghewala ka pay ~12 m aur tight hai (industry rule-of-thumb — verify,
Baghewala-specific study nahi). Downhole electric heater competitor nahi, **complement** hai —
twin me ek aur heat source term ban sakta hai. OIL ke trials ka detail hamare paas nahi, toh
uspe claim mat karna.

**(b)** *"We didn't choose the recovery method — the problem statement is CSS and rod-pump
optimisation, and that's what Baghewala runs. A downhole heater is complementary; our thermal
layer could take it as an extra heat source. We'd defer to OIL's own trial results on SAGD."*

### N10. "Poore field me steam generator limited hai — kaunse well ko kitna steam do?"

**(a)** Multi-well steam allocation real sawaal hai — aur humne iska ek pehla version bana
diya hai: `ml/schedule.py` har well ka apna job physics-grid se optimise karta hai, phir
decide karta hai kaun se wells ko agla steam milega, ek shared generator ke against
(bitmask-exact search over well subsets, ERD order within a subset). 12-synthetic-well demo
pe, har well VFD-hold pe, naive fixed-job policy hi **+₹72,320/d** field-wide kama rahi hai;
exact scheduling **+₹109,799/d** tak jaata hai, 10/12 wells serve karke. Yeh abhi bhi
synthetic-wells demo hai, real multi-well interference ya generator ke physical limits
handle nahi karta — par "we're single-well" ab sahi nahi hai.

**(b)** *"We've built a first version of this: our scheduler physics-optimises each well's
own job, then decides which wells get steam next off one shared generator. On a 12-
synthetic-well demo, every well run VFD-hold, a naive fixed-job policy already earns about
seventy-two thousand rupees a day field-wide, and exact scheduling reaches about a hundred
and ten thousand, serving ten of twelve wells. It's still a synthetic-wells demo, not
deployed against real field interference — but 'we're single-well' is no longer accurate."*

### N11. "Doosra well ho toh kya badlega?"

**(a)** Params JSON per well: depth, pay thickness, viscosity anchor, PI/AOF, drainage radius,
rod string, steam quality. Caveat: kuch constants (AOF_REF, S_COLD, K_VISC, 150 °C anchor)
abhi code me hain — params me move karna planned hai. Cold-well AOF har well ke pre-CSS rate
se calibrate hoga.

**(b)** *"A new well is mostly a new parameter file — depth, pay, viscosity, productivity, rod
string. A few calibrated constants still live in code, and moving them into per-well
parameters is on our list."*

### N12. "Yeh digital twin hai ya bas ek simulator?"

**(a)** Imaandari se: aaj yeh **twin-ready simulator + optimiser, aur calibration loop ab ban
chuki hai.** Twin banne ke teen pieces chahiye: (1) **live data link** (SCADA rates, dyno
cards) — abhi nahi; (2) **calibration / re-recommendation loop** — `twin/calibrate.py` +
`ml/recommend_physics.py` ab CSV se `water_cut`/`thickness_m`/`AOF_REF_M3D` fit karte hain
aur recalibrated physics pe hi re-recommend karte hain (pseudo-real demo: 0.2/1.6/0.9%
error) — **yeh ab ban chuka hai**, bas real OIL data se abhi nahi chala; (3) decision loop
wapas operator tak — UI ban chuki hai (Stage → Confirm). Bacha hua gap: (1), aur (2) ko
**real** field CSV se chalana.

**(b)** *"Today it's a twin-ready simulator and optimiser, and we've now built the
calibration loop itself: give it a CSV of observed cycles, it refits our most uncertain
constants and re-recommends against the recalibrated physics — demonstrated on a synthetic
dataset with recovery within about 1%. What's still missing is a live data link and running
that same loop on OIL's real cycles."*

### N13. "XSPOC, Lufkin SAM, SLB ke tools, CMG STARS — yeh sab kyun nahi use kiye?"

**(a)** Rod-lift tools (XSPOC, Lufkin SAM well manager, SLB ka lift surveillance) mature hain
par **pump-side** hain — steam cycle model nahi karte. CMG STARS thermal reservoir simulation
ka gold standard hai, par license, full geomodel aur ek run ke ghante chahiye, aur pump
optimise nahi karta. Hamara layer lightweight **coupling** hai; aur surrogate contract ki wajah
se kal STARS ko hi physics engine bana sakte hain.

**(b)** *"The rod-lift tools are excellent but pump-only; STARS is the thermal gold standard but
heavy and doesn't touch the pump. We're the lightweight layer that couples the two — and our
surrogate interface means STARS could sit behind it as the physics engine later."*

### N14. "Team me ChemE wala kya contribute karta hai?"

**(a)** Tu. Heat transfer (Marx-Langenheim, Boberg–Lantz), viscosity-temperature (Walther),
steam quality + latent heat + wellbore loss, energy balance, aur steam ka fuel/CO₂ economics.
Aur audit me sabse pehle physics red flags — μ paani se kam, 471 bbl/d vs field.

**(b)** *"I own the thermal and fluid side — heat transfer, viscosity-temperature behaviour,
steam quality and wellbore loss, and the fuel and CO₂ economics. The physical red flags in our
audit — viscosity below water, rate above the whole field — came from that side."*

### N15. "Slide 4 pe 'Monte-Carlo sensitivity' likha hai — kya hai woh exactly?"

**(a)** Yeh slide 4 ke waqt loose wording thi (tab sirf deterministic sweeps the) — **par ab
sach me ek proper Monte-Carlo hai**: `ml/uq.py`, true physics pe (surrogate pe nahi), 1,500
paired draws, seed 42, 21 uncertain inputs, teeno price deck ke liye bake hui. Result
(same-policy, VFD-hold vs VFD-hold): recommendation baseline se **96% (FY25)** behtar
hai — **lekin** woh 1.3 m³/d cutoff hamara khud ka chuna hua hai; dono ko same 0.6
backstop do toh **84%** (median gain ₹2.5k/day); aur agar VFD 2 spm se neeche chal
sake — jaisa hamara khud ka cold well allowed hai — toh set-point gain **≈ ₹0** ho
jaata hai. **OIL ka VFD minimum speed hi woh ek datum hai jo gain decide karta hai.**
(raw draws: 96.5% FY25 / 99.2% $65 / 99.9% net-of-levies); agar baseline pull karta hai
toh 99.1%+; agar baseline kuch nahi karta toh sirf **16–25%**. **P(injectable) = 100%**
har jagah. Same-policy gain p10/p50/p90 (FY25): **+2,175 / +12,101 / +161,014** —
right-skewed (point estimate low side pe baithta hai; p90 tail baseline ki apni
fragility hai). Top drivers: μ_ref, cold-well skin, oil price, formation water cut.

**(b)** *"That was loose wording at the time — today we actually run a proper paired Monte
Carlo through the true physics, not the surrogate, across 21 uncertain inputs and all
three price decks. Under the fair, same-policy comparison, our recommendation beats the
baseline in 96 percent of draws at OIL's FY25 price — but that's against a baseline whose
1.3 m³/d cutoff we chose. Give both sides the same 0.6 backstop and it's 84 percent,
median gain ₹2,500 a day; if the VFD can run below 2 spm, as our own cold well does, the
set-point gain goes to about zero. OIL's actual VFD minimum speed is the one datum that
decides this. Every draw clears our injectivity gate. The gain distribution is
right-skewed — our point estimate sits toward its low, conservative side."*

### N16. "Aap 20–30% SOR cut commit karte ho?"

**(a)** Nahi, aur ab hamare paas apna verified number hai jo alag hai. 20–30% literature
benchmark hai. Hamara result (same policy, VFD-hold): **gross SOR −14%** (3.29 → 2.83,
baseline (b) ke against, physics-verified) — par objective SOR nahi tha, **net cash per
cycle-day +₹3,332 (FY25 deck)** tha. Dono number saath bolna, alag-alag mat bolna,
price-deck AUR baseline-policy label kabhi mat chhodna, aur yeh bhi na bhoolna ki gain
stroke/cutoff se aata hai (57%/30%), steam sirf 11%.

**(b)** *"20-to-30 is the literature benchmark for SOR reduction alone. Our own
physics-verified result, same operating policy both sides, is a 14% gross-SOR cut
alongside net cash per cycle-day of plus three thousand three hundred thirty-two rupees at
OIL's own confirmed FY25 price — SOR was never the objective; net cash was, and most of
that gain comes from a shorter stroke and the rate cutoff, not the steam volume."*

### N17. "Tumhara baseline paise kyun kho raha hai (agar woh pull karta hai)?"

**(a)** Ab yeh sawaal sirf **ek specific policy ke case me** sach hai: agar baseline
**pull** karta hai (rods float hote hi well nikaal leta hai), toh humara float-onset-pull
rule usse **jaldi** khatam kar deta hai — usi rate pe jo abhi bhi cutoff se zyada hai. Yaani
baseline apna poora late, cheap oil kho deta hai. **Par agar baseline VFD-hold karta hai**
(rods ko slow karke float index 0.6 pe hold karta hai, hamari recommendation jaisa), toh
baseline khud **paisa kamata hai** — +₹12,064/d (FY25). Isliye ab hum kabhi nahi kehte
"baseline paisa khota hai" bina yeh bataye ki **kaunsi policy**: pull ke under haan, VFD-hold
ke under nahi.

**(b)** *"That's only true under one specific policy: if the baseline pulls the well the
moment rods float, our rule ends its cycle early, at a rate still above the cutoff, so it
loses all the cheap late oil it would otherwise make. But if the baseline instead slows
down with a VFD — the same policy our own recommendation uses — it actually earns positive
cash, about twelve thousand rupees a day at OIL's FY25 price. So we never say 'the baseline
loses money' without naming which float policy it's running."*

### N18. "Gross vs incremental (net cash) — kaunsa quote karte ho?"

**(a)** **Gross** SOR quote karte hain headline ke roop me — steam ÷ saara oil, literature
aur CalGEM convention yehi hai, isliye comparison ke liye sahi metric hai. ₹ decision **net
cash per cycle-day** (counterfactual-free, rev 13 ka objective) pe drive hoti hai — aur
kyunki model ka cold well har float policy ke under shut in hai (0 oil), SOR_incremental ab
SOR_gross ke barabar hi aata hai, alag se report karne ki zaroorat nahi. Dono baat (gross
headline + net-cash decision) ek saath dikhana hai, kabhi ek ko doosre ke jagah nahi.

**(b)** *"Gross — that's the literature and CalGEM convention, so it's the number that's
actually comparable. The rupee decision runs on net cash per cycle-day; since our model
shuts the cold well in under every float policy, incremental and gross SOR are now the
same number, so we don't need to report them separately anymore."*

### N19. "Yeh dyno card asli hai?"

**(a)** Physically measured card nahi hai (koi asli Baghewala rod pe sensor nahi laga),
**par ab computed hai** — `twin/dyno.py`, Gibbs (1963) rod wave-equation finite-difference
solve, typical heavy-oil rod string ke saath (Baghewala-specific nahi, ek data ask hai).
Pehle yeh ek illustrative JS shape thi (`buildDynoLoop`); ab nahi. **Alag se**, ek
**measured-card classifier** bhi bana hai (`ml/dyno_classifier.py`) jo field se aayi hui ek
real card ko 5 fault types me classify karta hai — 94.8% hold-out accuracy, par yeh bhi
sirf synthetic cards pe trained hai, **kabhi field-validated mat bolna**. Ek measured card
OIL se mile toh dono (physics card aur classifier) calibrate ho sakte hain.

**(b)** *"It's not a measured card — no sensor has ever been on a real Baghewala rod — but
it is computed: a Gibbs 1963 rod wave-equation solve over a typical heavy-oil rod string,
not an illustrative shape. We've separately built a classifier that would read a real,
measured card and flag a fault type — 94.8% accuracy on synthetic cards — but it too has
never seen a real card, so we call it a first read, not a validated diagnosis, until OIL
shares one."*

### N20. "Agar hum tumhe 10 cycles ka data de dein toh?"

**(a)** Exactly yehi demo hamare paas hai. `twin/calibrate.py` CSV leta hai (well_id,
steam_t, soak_days, spm, oil_m3, produce_days), teen constants fit karta hai
(`formation_water_cut`, `thickness_m`, `AOF_REF_M3D` — `bl_delta_factor` sourced hai, fit
nahi hota), aur `ml/recommend_physics.py` us recalibrated physics pe hi re-recommend karta
hai. Pseudo-real demo (synthetic hidden-truth dataset) pe recovery: formation_water_cut
−5.2%, aof −0.9%, thickness −10.9% — sab noise floor ke andar. 10 real cycles diye toh hum
yehi pipeline turant chalayenge — **par sabse zyada value ab ek water-cut-vs-time log aur
ek late-cycle/cold-well dyno card se aayegi**, kyunki wahi humari poori float-onset thesis
ko directly test karte hain.

**(b)** *"That's exactly the loop we've already built and demonstrated. Feed us a CSV of
observed cycles, and our calibration step fits the model's most uncertain constants —
recovering them within about 1 to 10% on a synthetic test — and then re-recommends
set-points directly against that recalibrated physics. But the single most valuable thing
OIL could give us now is a water-cut-versus-time log and one late-cycle dynamometer card —
those directly test the mechanism our whole recommendation rests on."*

### N21. "Gain kabhi se aata hai sabse zyada?"

**(a)** Rev 9 me sabse bada hissa cutoff se aata tha. Rev 12 me SPM (62%) + stroke (32%) se
aata tha, cutoff 0%. **Rev 13 me (same-policy, VFD-hold, canonical vs baseline b) decompose
hota hai: stroke 57%, cutoff 30%, steam 11%, spm 1%, pressure 1%.** SPM ab lever nahi rahi
kyunki VFD khud hi speed ko float-limit tak slow kar deta hai — jo bacha hua lever hai woh
stroke length hai (chhota stroke = 2-spm floor pe kam rod velocity = FI zyada der tak ≤0.6
rehta hai). OIL ka actual float-response (slow karta hai ya pull karta hai) ab hamara pehla
data question hai.

**(b)** *"That's moved twice. At rev 12 it was SPM plus stroke, cutoff zero. Under our
current same-policy comparison it's stroke 57%, cutoff 30%, steam 11% — SPM stops being a
lever once the VFD itself does the slowing down to the float limit; stroke length is what's
left, because a shorter stroke means lower rod velocity at the floor speed. Whether OIL's
operators actually slow down or pull on float is now our first data question."*

### N22 / K33. "Why 4.5 SPM and a 64-inch stroke — isn't that just pumping less?"

**(a)** Bilkul lagta hai aise, par mechanism alag hai. Chhota stroke rod velocity ko 2-spm
VFD floor pe kam rakhta hai, isliye VFD floating index ko 0.6 pe **zyada der tak** hold kar
paata hai bina pull hue. Yeh "kam pump karo" nahi hai, yeh "VFD ko zyada der tak float-limit
pe hold karne do, taaki poora cycle zyada oil de" hai — decomposition isi ko number deta
hai: stroke 57%, cutoff 30% (interaction — chhote stroke ke saath baseline ka 1.3 m³/d
cutoff float-pull se pehle hi bind kar jaata).

**(b)** *"It looks like just pumping less, but the mechanism is different: a shorter stroke
means lower rod velocity at the VFD's 2-spm floor, so the VFD can hold the floating index
at its safe limit for longer without triggering a pull. It's about letting the policy hold
the float line longer, not about pumping less for its own sake — that's why our
decomposition attributes 57% of the gain to stroke and 30% to the cutoff."*

### N23 / K34. "Why does your baseline lose money (under the pull policy)?"

**(a)** Sirf **pull policy ke under** — VFD-hold ke under baseline khud **+₹12,064/d**
kamata hai. Pull ke under: humara float-onset-pull rule baseline (5 spm, 86-in) ko usi rate
pe khatam kar deta hai jo cutoff se abhi bhi zyada hai — baseline apna poora cheap late oil
kho deta hai. Yeh price assumption ka artefact nahi hai. Asli root cause: **OIL ka real
SPM/stroke/float-response unknown hai** — humne 5 spm/86-in/pull ko "field practice" maan
liya hai, jo shayad OIL ki asli practice na ho.

**(b)** *"Only under the pull policy — under VFD-hold the same baseline earns positive
cash, about twelve thousand rupees a day. Under pull, our float-onset rule ends its cycle
at a rate still above the cutoff, so it loses the cheap late oil it would otherwise make.
That's not a pricing artefact; the real root cause is that we don't know OIL's actual SPM,
stroke, or whether operators slow down or pull on float — we assumed 5 spm/86-in/pull as
'field practice', and that's exactly what should be checked against OIL's real
operation."*

### N24 / K35. "Is stimulation even worth it, given the cold well counterfactual?"

**(a)** Rev 13 me model ka cold, unstimulated well **har float policy ke under SHUT IN
hai** (FI 1.0, 189 kN, 0 oil) — yeh "idealised pumpable" nahi raha. Ek doosra, zyada
field-consistent counterfactual bhi hai: **`pumpable`** — VFD ko cold well pe bhi 0.25-spm
floor tak slow karo jab tak FI ≤ 0.6 na ho jaaye; usi pe well **0.53 spm** pe **0.445 m³/d**
deta hai. Rec ka net cash `pumpable` counterfactual ke against **+₹4,013/d** (FY25) hai, shut
in ke against **+₹15,396/d**. Doosra number bada isliye hai kyunki shut-in cold well ka apna
cash hi nahi hai. **Yehi wo pehla sawaal hai jo ek cold-well dyno card jawab dega** — field
ne yeh wells cold produce kiya tha, toh `pumpable` reading zyada field-consistent hai.

**(b)** *"Our model's cold, unstimulated well is now shut in under every float policy — not
an idealised pumpable well. We also report a more field-consistent counterfactual, where
the VFD slows the cold well down to a 0.25-spm floor until its own floating index is safe —
it then makes a small amount of oil. Our recommendation's net cash against that reading is
plus four thousand and thirteen rupees a day; against the shut-in reading it's plus fifteen
thousand — the difference is entirely the cold well's own credited cash. Since the field
did produce these wells cold, the `pumpable` reading is the one closer to what actually
happened in the field. A single cold-well dynamometer card is the first thing that would
confirm it."*

### N25 / K36. "What is real-time here — is this actually live?"

**(a)** Do parts: (1) **Batch mode** — twin ek cycle **~8 ms** me chalata hai, isliye
1,500-draw UQ bake ya 40,194-point-per-policy exhaustive grid seconds/minutes me ho jaate
hain; yeh "real-time" interactive optimisation ke liye hai, live field telemetry ke liye
nahi. (2) **Live API** — `api/main.py` FastAPI se `/simulate`, `/optimize`, `/api/schedule`,
`/api/dyno/classify` sab live serve hote hain, dashboard bhi live mode detect karta hai.
**SCADA se live data hook abhi planned hai, built nahi** — jab tak OIL live tags/values
nahi deta, twin ek on-demand batch/API service hai, continuously streaming digital twin
nahi.

**(b)** *"Two things, and we keep them separate. The twin itself is fast — about 8
milliseconds a cycle — so a 1,500-draw uncertainty sweep or a 40,000-point-per-policy
exhaustive grid runs in seconds to minutes; that's what lets us optimise interactively.
Separately, we have a live FastAPI service the dashboard talks to. What we don't have yet
is a SCADA hook pulling live field telemetry — that's planned, not built, and we say so
rather than imply this is already streaming real field data."*

### N26. "Your gain depends on what the baseline operator does — so what is it?"

**(a)** Sabse honest jawab teeno number ek saath dena hai, kabhi ek akela nahi: **same
policy** (baseline bhi VFD-hold): **+₹3,332/d** (FY25) / +4,319 ($65) / +5,382
(net-of-levies). **Agar baseline pull karta hai** (rods float hote hi well nikaal leta hai
— rev-12 ki assumption): **+₹12,917/+14,694/+16,606** — par isme se **68% sirf policy
switch hai** (slow karna vs pull karna), hamare set-points ka nahi. **Agar baseline kuch
nahi karta** (rods ko float hone dete hain rate cutoff tak): humara canonical recommendation
phir bhi **+₹2,622/+3,484/+4,413 gain karta hai** (TIER1 §12.6 "mixed" row) — ek purani
version me yahan **−₹3,865/−2,513/−1,057** likha tha, par woh number ek alag,
non-canonical, do-nothing-ke-liye-optimised plan ka tha, humari asli recommendation ka
nahi, ab retired. Teeno case me ek cheez same rehti hai: rod-damage ka koi ₹ cost model
me hai hi nahi. Toh: "your gain" ka koi ek jawab nahi hai — jawab hai "OIL ka operator
abhi float pe kya karta hai?"

**(b)** *"Honestly, all three numbers, never just one: if the baseline is operated the same
way as our recommendation — VFD-hold — we gain about three thousand three hundred rupees a
cycle-day at FY25 prices. If the baseline operator pulls the well the instant rods float,
the gain looks like twelve thousand nine hundred — but two-thirds of that is just the
policy difference, not our set-points. And even if the baseline does nothing about float,
our recommendation still gains a little — about twenty-six hundred rupees — though we
still don't put a price on the rod damage that holding at the float limit causes, so none
of these three numbers reflect that cost. So the honest answer to 'what's your gain' is
another question: what does OIL's operator actually do today?"*

### N27. "Why VFD-hold and not just pull?"

**(a)** VFD-hold zyada oil deta hai (SOR 2.83 vs pull ke under 3.60, same set-points pe) aur
well ko **0 din** FI=1.0 (poora float) pe rakhta hai — pull ke under aur `none` ke under
yeh 42–86 din tak hota hai. Par rods **0.6 ke alarm limit pe hi ~55–60 din/cycle** baithe
rehte hain (graded damage index Σ FI³ ~5× `pull` policy se) — aur is rod-wear ka koi ₹ cost
model me nahi hai (koi rod-failure/workover term nahi). Toh VFD-hold **economically**
recommended policy hai, ek honest, unpriced cost ke saath.

**(b)** *"VFD-hold makes more oil — steam-oil ratio 2.83 versus 3.60 under pull at the same
settings — and it keeps the well at zero days fully floating, versus 42 to 86 days under
the other policies. But the rods sit right at the 0.6 floating-index alarm limit for 55 to
60 days a cycle — a graded damage index about five times the pull policy's — and we have no
rod-failure or workover cost term to price that wear. So VFD-hold is the economically
recommended policy, honestly stated alongside a real cost we don't yet put a rupee figure
on."*

### N28. "Is CSS even profitable net of royalty and cess?"

**(a)** **Nahi, humare numbers pe nahi** — OIL ki apni royalty+cess levy structure (~35%
total, OIL ke FY25 Annual Report se) pe, har feasible steam/soak/pressure/stroke/SPM
combination **net-cash-negative** aata hai, ek shut-in (non-producing) cold well ke against
bhi. Yehi wajah hai ki hum OIL se unki apni net-of-levies price/P&L basis maang rahe hain
(`docs/research/OIL_DATA_REQUEST.md`), ek assume karne ke bajaye.

**(b)** *"No, not on our numbers — at OIL's own royalty-and-cess levy structure, about 35%
total from their FY25 Annual Report, every feasible combination we tried comes out net-cash
negative, even against a shut-in, non-producing cold well. That's exactly why we're asking
OIL for their own net-of-levies price and P&L basis, rather than assuming one ourselves."*

### N29. "Why does your slug size drop below what BGW-8 used?"

**(a)** Humare assumed mid-range diesel bulk-discount (**0.15**, yaani full retail aur ek
generous 30% bulk discount ke beech ka aadha) pe, model ka apna gross-margin-optimal steam
slug sirf **~750 tonnes** aata hai — BGW-8 ke asli pehle-cycle range **1,040–1,560 tonnes**
se kam. Hum ise ek disclosed test failure (**xfail**) ke roop me flag karte hain, aur
**revealed preference** se padhte hain: kyunki OIL ne asal me bade slugs use kiye, unka
real diesel/steam cost humare mid-range assumption se **sasta** hoga — ek aur concrete data
ask.

**(b)** *"At our assumed mid-range diesel bulk-discount — halfway between full retail and a
generous 30% bulk discount — the model's own gross-margin-optimal steam slug is only about
750 tonnes, below BGW-8's actual first-cycle range of 1,040 to 1,560 tonnes. We flag this
honestly as a disclosed test failure, and we read it as revealed preference: since OIL
actually used bigger slugs, their real diesel and steam cost is probably cheaper than our
mid-range assumption — another concrete data ask for OIL."*

### N30. "Aapka VFD floor dono wells ke liye same rakh doon toh aapka gain gayab ho jaata hai — toh aapka gain hai kya?"

**(a)** Robust cheez set-point ₹ number nahi hai — **operating rule** hai: pull karne se
pehle slow karo, aur SOR drop (3.29 → 2.83) real hai. ₹ gain **₹0 se ₹5k/cycle-day** ke
beech hai, aur yeh do cheezon se decide hota hai jo humare paas nahi hai: **OIL ka VFD ka
actual minimum speed**, aur **unka real pull/produce cutoff**. Dono ab humari data request
me hain (`docs/research/OIL_DATA_REQUEST.md`, items 16–17).

**(b)** *"Honestly — yes, if we give both wells the same VFD floor, the set-point ₹ gain
goes to about zero. What survives is the operating rule, not a rupee figure: slow the pump
before you pull it, and the SOR drop from 3.29 to 2.83 is real regardless. The actual ₹
number is somewhere between zero and about five thousand a cycle-day, and it's decided by
one thing we don't have: OIL's own VFD minimum speed and their real pull or produce
cutoff. Both are now on our data request."*

### N31 / K42. "Tum baar-baar bolte ho 'kam steam, kam oil' — 11% kam oil kaise achi baat hai?"

**(a)** Apne aap me nahi — yeh ek trade hai, aur hum usse zor se bolte hain. Same VFD-hold
policy dono side, recommended cycle **23% kam steam** jalata hai (1,000 vs 1,300 t) aur
**11% kam oil** banata hai (353 vs 395 m³), isliye SOR girta hai 3.29 → 2.83: hum fuel aur
CO₂ per barrel me bada cut le rahe hain, oil ke chhote se sacrifice ke against. "Zyada oil"
sirf tab sahi hai jab baseline **pull** karta ho (~299 m³) — ek alag, unfair comparison jo
hum ab nahi karte. Yeh trade commercially worth hai ya nahi, wahi net-cash numbers (K37)
answer karte hain, SOR akela nahi.

**(b)** *"Not on its own — it's a trade, and we say the trade out loud. Under the same
VFD-hold policy on both sides, the recommended cycle burns 23% less steam and makes 11%
less oil, so SOR falls 3.29 to 2.83: we're trading a small oil loss for a bigger fuel and
CO₂ cut. 'More oil' is only true against a baseline that pulls instead of slowing down — a
different, unfair comparison we don't make any more."*

### N32 / K43. "Kya pump sach me safer hai, ya sirf dikhta hai?"

**(a)** Sirf ek specific baseline ke against, aur hum bataate hain kaunsa. Same policy
(VFD-hold) baseline ke against, floating index aur graded damage index dono side almost
same hain (FI 0.62 vs 0.62; damage index 15.99 vs 15.91 — thoda worse) — **same-policy
baseline se zyada safe nahi hai**. Woh sirf tab safer dikhta hai jab baseline rods ko
**unmanaged float** karne deta hai (72 alarm days vs 3, 42 din FI=1.0 pe vs 0) — real farak
hai, par yeh humari poori policy choice (VFD-hold vs none) ko baseline ki "kuch nahi"
approach se compare karta hai, set-points ko set-points se nahi. Aur dono comparison me,
rods ko 0.6 alarm line pe ~55–60 din/cycle **hold** karne ka damage priced nahi hai —
"safer" ka matlab hai "kuch na karne se safer", "sasta chalane layak" nahi.

**(b)** *"Only relative to a specific baseline. Against a baseline run the same way —
VFD-hold — the recommendation's own floating index and damage index are essentially
unchanged, so it isn't demonstrably safer than a same-policy baseline. It only looks safer
against a baseline that lets rods float unmanaged. And either way, the damage done while
the rods are held at the 0.6 alarm line for 55 to 60 days a cycle isn't priced — 'safer'
here means safer than doing nothing, not cheap to run."*

---

## TRAPS — yeh KABHI mat bolna

| # | Kabhi mat bolna | Iske badle bolna |
|---|---|---|
| **1** | *"Yes, we validated it on real field data."* | **"Not yet."** Physics-consistency + literature-benchmark + field-plausibility checks hue hain. OIL ka historical data agla step hai. Ek follow-up me yeh claim dhaan ho jaayega aur poori session ka trust chala jaayega. |
| **2** | *"Hamara model 99% accurate hai."* | **R² ≠ field accuracy.** "R² 0.998 means the oil surrogate explains ~99.8% of variance in **simulated** oil output on held-out synthetic data. It measures how well XGBoost copied our calibrated engine — not how well our engine matches Baghewala." |
| **3** | *"Baghewala Jaipur se ~250 km hai."* | **550-600 km.** Bikaner-Nagaur basin me. Ek galat geography number pura domain credibility hila deta hai. |
| **4** | *"Baghewala ka current SOR 4.5 hai"* (ya koi bhi number). | **Baghewala ka apna SOR kahin published nahi hai.** "We deliberately don't quote one — we benchmark against the literature range of 3-8 t/m³, average ~6." |
| **5** | OIL ka koi SIH track record gadhna. | Kuch **mat** bolna. Sirf **field** ke confirmed facts — BGW-8, 52 wells, production growth. |
| **6** | *"We cut SOR by 30%"* / *"41%"* / rev-9's *"+4,423/cycle-day"* / rev-12's *"+₹9,574/cycle-day"* bina baseline-policy label ke | Sab historical/superseded. "Our own physics-verified, same-policy result is SOR down from 3.29 to 2.83 and net cash per cycle-day up by about three thousand three hundred rupees at OIL's own confirmed FY25 price, against a baseline operated the same way (VFD-hold)." |
| **7** | *"₹0.61 crore a year"* (ya koi annual ₹), ya **gross margin ko profit bolna** | Per-cycle, net cash: "Each tonne of steam is ~71 kg diesel — ₹7,111/t at our mid-range discount. Our recommended cycle's net cash — against a baseline operated the same way — is about plus three thousand three hundred rupees a cycle-day at OIL's confirmed FY25 price." |
| **8** | *"All 24 tests pass"* / *"116/127/197/236 passed"* / *"57/57, no gaps"* | "263 of 265 pass, with 2 strict xfails for gaps we've characterised and documented (soak; the steam optimum at the mid-range diesel price sits below BGW-8's slug range) — not hidden failures." |
| **9** | *"Run at 10 SPM"* (v1 artefact) / *"the recommendation runs at 3 spm"* (rev-12 artefact) | "Practice is 3–6 SPM; the current recommendation starts at 4.5 spm under a VFD-hold policy that then slows the unit further as rods approach float, down to a 2-spm floor." |
| **10** | Claiming an **absolute CO₂ reduction** per cycle without naming the baseline's policy, that the twin **recommends a soak length**, or saying the recommendation **"makes more oil"** | "Under the same operating policy, our recommended cycle burns 23% less steam than the baseline for 11% less oil (353 vs 395 m³), so SOR falls 3.29 → 2.83 and CO₂-per-m³ falls too — but that's a same-policy comparison, not a law of the physics, and it is less oil, not more. Soak is fixed at 10-day field practice, not twin-derived." |
| **11** | *"Our models were cross-validated."* | Not true — a single 80/20 hold-out split, seed 42, no cross-validation run or claimed. |
| **12** | *"The BL delta factor is unverified."* | It's sourced: exactly the ½ inside Boberg and Lantz's own 1966 equation, forced by energy conservation — not a free or unverified constant. |
| **13** | Showing only one price deck's ₹ number | Always show all three: OIL's confirmed FY25 realisation, the $65/bbl planning-floor comparison, and the net-of-royalty-and-cess deck (every feasible point is negative on that last one). |
| **14** | **"reproduces Baghewala's benchmarks"** | Say: "calibrated to the published band; not field-validated". We match literature and CalGEM bands, not Baghewala's own cycle records, which don't exist publicly. |
| **15** | **"verified improvement"** | Say: "physics-consistent improvement on synthetic data, against a named baseline policy". Real validation waits for OIL's cycles. |
| **16** | **"OIL's own practice baseline"** | Say: "baseline derived from the one published BGW-8 job; OIL's actual cutoff/SPM/stroke AND float-response (slow vs. pull) unknown". It's a reference case, not their current operating target — and the gain now rides on exactly these unknowns, the float-response most of all. |
| **17** | **"recovers thickness within 0.9%"** | Say: "thickness recovered within about 11% on the current committed seed — weakly identified, trades off against AOF". That's a demo result, not a per-run guarantee. |
| **18** | Quoting a single gain number (e.g. "+₹9,574/d" or "+₹3,332/d") **without naming the baseline's own float policy** | Say: "the gain depends on what the baseline operator does about float — same policy (VFD-hold): +₹3,332/d; if it pulls: +₹12,917/d (68% of that is just the policy switch); if it does nothing: +₹2,622/d — either way, rod damage isn't priced." |
| **19** | **"our engine was 25% optimistic"** | It's **25×**, not 25% — the first engine's peak rate was about 25 times the field-implied average, not 25% above it. |
| **20** | Calling the measured-card classifier **"field-validated"** or **"accurate on real cards"** | Say: "94.8% hold-out accuracy on synthetic cards; it has never seen a real Baghewala card — a first read to confirm with a specialist, not a validated diagnosis." |
| **21** | Saying the model's cold well **"can't be pumped"** without naming the reading | Say: "it's shut in under every float policy in our base reading; a second, more field-consistent reading credits it with a small pumped rate once the VFD slows it further — we report both." |

**Teen line jo har musibat se bachati hain:**
- *"That's from our simulation, not a field measurement."*
- *"That's industry-typical, not Baghewala-specific."*
- *"That's an assumption, and here's why we made it."*

---

## CHEAT SHEET — 21 numbers, ek-ek line context

| # | Number | Context |
|---|---|---|
| 1 | **1,150 m** | Baghewala well depth (CONFIRMED, OIL/SPE) — CSS window ke edge pe |
| 2 | **11,500 cP @ 50 °C** | Hamare model ka μ_ref; literature range 8,000-15,000 cP (CONFIRMED); normal 18° API crude se ~90–100× gaadha |
| 3 | **14-17° API (lit) vs 17-19° (PS)** | Dono bol dena aur farak batana — PS text vs SPE-23APOG/OIL data |
| 4 | **290 °C, quality 0.65** | Steam injection (BGW-8 280-305 °C, CONFIRMED); sandface pe ~0.36 (v2 wellbore loss) |
| 5 | **Gross SOR 3–8 t/m³ (avg ~6)** | Literature band; CalGEM real 2021 field band **3.47–8.24** (9,692 real cycles) bhi isi ke andar; reference-SOR band **3.0–4.6**. Baghewala ka apna SOR **published nahi** — koi number nahi bolte. Reference cycle (shipped `pull` default): **4.50** |
| 6 | **71 kg HSD / t steam** | → **₹7,111/t at 0.15 mid-range discount** (0.30/0 presets bhi hain), **~224 kg CO₂/t** (OIL ka diesel-fired steam: 220 kg/hr HSD for 3.1 t/hr) |
| 7 | **Recommended cycle burns LESS steam now (1,000 t vs baseline's 1,300 t)**, same policy | Per-cycle framing — koi annual ₹ nahi. SOR aur CO₂-per-m³-oil neeche gire hain, same-policy comparison me |
| 8 | **3,000 cycles** | Training dataset, LHS, seed 42, **rev-13 physics** pe (7th column: `float_policy`); **real cycles = ZERO** (par CalGEM se ek real band-check hai) |
| 9 | **Physics grid = decision engine (40,194 feasible points/policy, 4 policies, ~172 s)** | ML surrogate isi optimum se **~24% neeche** land karta hai — surrogate ab sirf ek cross-check hai |
| 10 | **263 passed, 2 xfailed** | xfail = documented, expected gaps (no soak optimum; steam optimum at the mid-range diesel price below BGW-8's slug range) — not failures |
| 11 | **BGW-8, Dec 2018** | **India's first CSS well** (OGJ + OIL); 5-6x uplift |
| 12 | **218 t → 43,773 t** | Baghewala production, FY17 → FY26 |
| 13 | **52 wells; field 655–1,202 bbl/d** | ~19 bbl/d/well — isi se v1 ka 471 bbl/d pakda gaya |
| 14 | **FI 0.6, `css.float_policy`** | Operator ka float-response ab ek CONTROL hai — `pull`/**`vfd_hold`**/`vfd_then_pull`/`none` — pull/VFD-hold/none teeno baseline aur recommendation dono pe SAME lagti hai |
| 15 | **Baseline (b) SOR 3.29 → Recommendation SOR 2.83 (dono VFD-hold)** | Net cash: baseline +₹12,064/d → rec +₹15,396/d (FY25). Same-policy gain **+₹3,332/d** (+4,319 $65 / +5,382 net-of-levies) — baseline pulls: +₹12,917; baseline kuch nahi karta: canonical rec **+₹2,622** (mixed row; purana −₹3,865 ek alag plan ka tha, retired). Idea deadline **30 Sep 2026** |
| 16 | **Gain (same policy, VFD-hold): stroke 57%, cutoff 30%, steam 11%** | Rev 12 me SPM 62% + stroke 32% tha — VFD khud speed slow karta hai, toh SPM ab lever nahi rahi |
| 17 | **Calibration demo: formation_water_cut/aof/thickness within −5.2/−0.9/−10.9%** | `twin/calibrate.py` pseudo-real demo, rev-13 physics pe re-run — BL fixed, not fitted |
| 18 | **Technical re-score: 58/100 (27 Sep)** | Top finding: rev-12 ka poora gain pull-rule assumption ka artefact tha — rev 13 (wave 5) isi ka jawab hai |
| 19 | **Cold well SHUT IN under every float policy** | 0 oil, FI 1.0, 189 kN at the 2-spm floor — real field ne cold produce kiya tha, toh `pumpable` counterfactual (~₹11.4k/d kam) zyada field-consistent hai; har absolute incremental figure ek upper bound hai |
| 20 | **Measured dyno classifier: 94.8% hold-out** | 5 fault classes, RandomForest, 3,200 synthetic cards — never seen a real card, never call it field-validated |
| 21 | **Rod damage unpriced: Σ FI³ ~5× under VFD-hold vs pull** | ~55–60 din/cycle FI 0.6 pe hold — no rod-failure/workover cost model. Even against a do-nothing baseline the canonical rec **still gains +₹2,622/d** (mixed row) — the earlier −₹3,865/d was a different, non-canonical plan, not our recommendation |

---

**Yaad rakhne wali baat:** judge tera answer nahi, tera **confidence + honesty** judge kar
raha hai. Jo pata hai woh saaf bol; jo nahi pata usko "that's an assumption / that's not
published" bol ke rakh de. Sabse strong move yeh hai ki **weakness khud pehle bol de** —
"our own review found our first engine 25× optimistic, so we rebuilt the physics" — usse
pehle ki judge pakde. Woh line trust banati hai, todti nahi.
