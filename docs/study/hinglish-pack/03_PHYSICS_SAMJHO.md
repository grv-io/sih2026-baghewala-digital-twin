# 03 — PHYSICS SAMJHO (zero se, apni bhasha me)

> **✅ STATUS (27 Sep 2026, rev 13 — physics wave 5 live):** is file me **chaar** engine-eras
> ki baat hai. **v1** = hamara first-cut engine (SOR 1.29, 244 °C, 74.96 m³/d) — iske saare
> numbers hamare apne review me **~25× optimistic** nikle; ab **historical**. **rev 9**
> (physics v3 + economics v2) — reference SOR 4.03, uplift 5.66×, cutoff hi 83–96% gain drive
> karta tha, water cut ek **constant** 85% tha — ab **historical/superseded**. **Rev 12**
> (physics wave 4) — water cut ek **state** (§5b neeche), Pal–Rhodes emulsion + 10× cap,
> float-onset produce-end rule, AOF field peak band pe retuned — SOR 4.50 gross reference pe,
> **par rev-12 ka apna +₹9,574/d headline nikla ek pull-rule artifact** (§5c neeche) — ab bhi
> **historical/superseded**, mechanism samjho par numbers quote mat karo.
> **Rev 13** (physics wave 5, 27 Sep) — float pe operator kya karta hai (slow ya pull) ab
> khud ek **policy control** hai (§5c), same policy baseline/recommendation/cold-counterfactual
> teeno pe apply hoti hai, smooth inversion band, injectivity gate, net-of-levies deck. Reference
> set-point (1,500 t / 7 d / 1.2 m³/d / 5 spm / 86 in / 91 kgf/cm², shipped default `pull`,
> rev-13 me bhi unchanged) pe SOR **4.50 gross**. Recommendation (VFD-hold): SOR **2.83**
> vs baseline (b) VFD-hold **3.29**. **263 tests pass, 2 honest gaps xfailed** (soak: no
> interior optimum; mid-range diesel price pe steam optimum BGW-8 se neeche). Mechanism sab
> se samjho; jahan table ke upar **[v1]**, **[rev 9]** ya **[rev 12]** likha hai, woh number
> historical hai, quote nahi karna. Rev-13 numbers ab safe hain — see §5c, §7.

Bhai, yeh file tera **core** hai. Tu ChemE ka banda hai, tu team lead hai — judge jab bhi
"yeh temperature kahan se aaya", "viscosity itni kaise gir gayi", "rod tootegi kyun"
poochega, sab tera muh dekhenge. Isliye yeh file ratta maarne ke liye nahi, **samajhne**
ke liye hai. Ek baar samajh liya toh number bhool bhi gaya toh derive kar lega.

---

## 0. Poori kahani ek line me — chain yaad rakh

Hamare twin me **chaar module** hain aur woh ek zanjeer (chain) me jude hain:

```
Steam daalo  →  Reservoir garam  →  Oil patla  →  Oil zyada nikla  →  Pump pe kam load
  (thermal.py)   (thermal.py)      (viscosity.py)    (ipr.py)          (srp.py)
```

Ek hi cheez — **viscosity (μ)** — poori chain ka bicholiya hai. Temperature usko girati
hai, aur woh do jagah asar dikhati hai: **IPR me rate badhata hai**, aur **SRP me rod ka
drag ghatata hai**. Yahi "coupling" hai jispe humara poora project khada hai.

> **Yaad rakhne wali baat:** agar koi ek hi cheez yaad rakhni ho toh yeh — *"μ ek hai, par
> uske do customer hain: reservoir (rate) aur pump (load). Isiliye steam aur pump ko alag-alag
> optimise nahi kar sakte."*

> **📏 Units box — ek baar dekh le, confusion khatam:**
> - **Viscosity:** 1 **cP** (centipoise) = 0.001 **Pa·s**. Paani ≈ 1 cP. Formulas (jaise rod
>   drag) me Pa·s daalte hain: 2,203 cP = 2.203 Pa·s.
> - **Volume:** 1 **m³** = **6.29 bbl** (barrel). Field log bbl/d bolte hain, hamara code
>   m³/d. 2.83 m³/d ≈ 17.8 bbl/d; 3.1 m³/d ≈ 19 bbl/d.
> - **SOR** = **tonnes steam ÷ m³ oil** (t/m³). Kam = behtar. Literature band 3–8.
>   (Kuch papers bbl/bbl me dete hain — 1 t paani ≈ 1 m³, toh number lagbhag same rehta hai.)
> - **Pressure:** 100 kPa ≈ 1 bar ≈ 1 kgf/cm². 11,400 kPa ≈ 114 bar.

---

## 1. Heat transfer hota kya hai — bilkul basic

Garmi teen tarike se travel karti hai: **conduction** (atom se atom — chammach ka doosra
sira garam ho jata hai), **convection** (bahte fluid ke saath), aur **radiation** (dhoop).
Reservoir me jo sabse zyada matter karti hai woh **conduction** hai: humne jo garmi paise
dekar neeche bheji, woh upar-neeche ki thandi chattan (cap rock, base rock) me lagataar
**chori** ho rahi hai.

Ek aur zaroori idea: **latent heat**. Steam sirf "garam paani" nahi hai — jab bhaap paani
me condense hoti hai to woh ek badi energy (latent heat, humare params me **1.40 MJ/kg**
— v1 me 1.3 tha, 290 °C pe steam tables ~1.48 dete hain, 1.40 us ke paas ka rounded
value hai) chhod deti hai bina temperature girae. CSS isi latent heat ko bechti hai.
Humare code me hum **sirf latent heat count karte hain** (`quality` se multiply karke).

**Ek honest correction:** v1 me hum wellbore heat loss ignore karte the aur isko
"conservative" bolte the. **Yeh galat tha — ignore karna OPTIMISTIC hai**, kyunki iska
matlab tha ki surface pe khareedi hui poori garmi reservoir tak pahunch gayi. Asli me
1,150 m ki pipe me garmi raste me hi nikal jati hai. **v2 isko model karta hai:** depth ke
hisaab se ~11% heat loss, aur sandface (reservoir face) pe quality = **0.55 × wellhead
quality** (0.65 → ~0.36). Isliye v2 me reservoir tak jo effective garmi pahunchti hai woh
v1 ki **~52%** hai.

**Baghewala ka setup:** ~1,150 m gehra, pay zone sirf **12 m mota**, reservoir temperature
**50 °C**, pressure **11,400 kPa**, porosity 9%. Steam **290 °C** pe, **74 t/din** ki rate
se ja rahi hai (yeh BGW-8 ka OIL ka apna confirmed number hai — 3,100 kg/hr).

---

## 2. Marx-Langenheim — "garmi kitni door tak phaili?"

### Tawa wali analogy

Soch, gas stove pe **ek patla tawa** rakha hai, beech me flame. Shuru me beech ka hissa
turant garam — garam area chhota hai, leak hone ki jagah kam hai. Par jaise-jaise garam
patch bada hota hai, uska **surface bada ho jata hai**, aur har extra second ki flame ka
bada hissa hawa me chala jata hai. Isliye patch pehle tezi se badta hai, phir dheere.

Reservoir bilkul yehi hai — bas tawa **12 m mota pancake** hai jo upar-neeche thandi
chattan ke beech sandwich hai, aur woh chattan constantly garmi chura rahi hai.

**Marx-Langenheim (1959)** exactly yehi batata hai: *tune jitni garmi bheji, uska kitna
fraction andar ruka?*

```
t_D  = 4 · α · t / h²                                (dimensionless time)
F(t_D) = exp(t_D) · erfc(√t_D) + 2·√(t_D/π) − 1
E_h  = F(t_D) / t_D                                  (thermal efficiency, 0 se 1)
```

- **α** = thermal diffusivity = k/(ρcp) = 2.5 / 2.3×10⁶ = **1.087×10⁻⁶ m²/s**
- **h** = 12 m thickness. Dekho `h²` **neeche** hai — matlab **patla reservoir bahut zyada
  leak karta hai**. Aadha mota karo to t_D chaar guna, matlab efficiency curve pe bahut
  neeche. Patla reservoir = **leaky kadhai.**
- **E_h → 1** shuru me (kuch nahi khoya), aur waqt ke saath girta hai.

Humare reference cycle pe: injection 20.27 din, t_D ≈ 0.053, **E_h ≈ 0.85** — yaani 85%
latent heat andar ruki. **[v1]** Heated radius **7.20 m**, peak temperature **244 °C**.
(v2 me wellbore loss ki wajah se kam garmi pahunchti hai → 1,500 t pe heated radius
~**5.2 m**.)

### Drainage radius kya hota hai — aur v1 ka "optimum" kahan se aaya tha

**Drainage radius (r_e)** = ek well apne chaaron taraf kitne door tak ke rock se oil
kheench raha hai. Soch ek khet me kai handpump lage hain — har pump apne aas-paas ka paani
kheenchta hai, aur do pumps ke beech kahin ek "border" banti hai. Wahi border drainage
radius hai. Yeh **well spacing** se aata hai — asli heavy-oil wells me typically
**50–150 m**. v2 me hum **100 m** use karte hain.

**v1 ki kahani (honestly):** v1 me ek `DRAINAGE_RADIUS_M = 8 m` tha. Naam drainage radius
tha, par woh asli drainage radius **tha hi nahi** — woh ek **saturation knob** tha. Heated
disc (~7 m) ko us 8 m ke disc ke against tola jata tha; ~1,750–2,000 t pe disc "bhar"
jata tha, uske baad extra steam se oil nahi badhta tha, isliye SOR wapas upar mudh jata tha
aur ek "interior optimum" dikhta tha. Pehle yeh 10 m tha; 10 m pe optimum range ke andar
aata hi nahi tha, toh ise **8 m pe retune kiya gaya** — yaani **optimum physics se nahi,
ek fudge se aaya tha.** Hamare internal review ne yahi pakda. **v2 me yeh constant delete
ho chuka hai.**

**v2 me kya hai:** **composite-radial uplift** (Boberg–Lantz ka hissa, neeche §2b me).
Seedhi baat: sirf well ke paas ka ek chhota ring (r_h ≈ 3–7 m) garam hota hai; uske bahar
100 m tak oil abhi bhi **thanda shahad** hai, aur wahi thanda hissa flow ko rokta hai.
Isliye v2 me "zyada steam = zyada oil" ka jo diminishing return dikhta hai woh **asli
geometry** se aata hai, kisi knob se nahi.

> **Yaad rakhne wali baat:** *"Zyada steam hamesha behtar hota, toh yeh project hi nahi
> hota."* — yeh idea sahi hai. Par v1 ka specific optimum ek tuned 8 m disc se aata tha,
> isliye **"hamare model me optimum 1,750 t pe hai" mat bolna.** Honest optimum SOR ka
> nahi, **₹ margin per cycle-day** ka hai — aur ab (rev 5, calibrated) woh nikal chuka hai:
> ₹/cycle-day 1,000–2,000 t steam ke plateau me sabse zyada hai (SOR khud steam ke saath
> monotone badhta rehta hai, kabhi neeche nahi mudta). Rev 13 (float-onset rule + policy
> control ke saath) ki recommendation is plateau ke **niche wale kinare, 1,000 t** pe
> baithti hai — kyunki ab gain policy (VFD-hold) aur stroke slow karne se aata hai, na ki
> zyada steam se (§5c, §7).

---

## 2b. Physics v2 (Tier-1) — kya badla aur kyun

13 Sep ko humne engine ke chhe hisse published models se badle. Har ek ka ek line me
"pehle kya tha → ab kya hai → kyun". (Andrade/Vogel ka basic neeche §3–§4 me hai; yahan
sirf badlav.)

| # | Kya badla | Beginner wali samajh | Kyun zaroori tha |
|---|---|---|---|
| 1 | **Cooldown: exponential (τ = 20 d) → Boberg–Lantz (1966)** | Garam zone thanda kaise hota hai — upar-neeche ki chattan garmi churati hai **aur** jo oil/paani hum bahar nikaalte hain woh bhi garmi saath le jata hai. Zyada tez pump karo → zone tez thanda. | τ = 20 d ek **invented** number tha. Boberg–Lantz published hai aur production ko cooling se jodta hai. Iski khud ki uncertainty ~42% hai, woh bhi hum likhte hain. |
| 2 | **Viscosity: Andrade → Walther / ASTM D341, 1 cP floor** | Same do anchor points (11,500 cP @ 50 °C, 50 cP @ 150 °C), par curve ka shape woh jo petroleum industry crude ke liye use karti hai. Aur viscosity **1 cP (paani) se neeche nahi ja sakti.** | Andrade ko 290 °C tak kheencha toh **0.63 cP** aata tha — **paani se bhi patla** heavy crude! Physically bakwaas. Walther se μ(290 °C) = **4.13 cP**, μ(244 °C) = **7.2 cP**. |
| 3 | **Rate multiplier: `μ_ref/μ` → composite-radial uplift (max 10×)** | v1 poore reservoir ko garam maan leta tha → rate **5,000×** badh jata tha. v2 kehta hai: sirf chhota ring garam, bahar sab thanda → uplift **~4×**. | v1 ki single-well peak **471 bbl/d** aati thi, jabki **poora field** (34 wells) 655–1,202 bbl/d karta hai. ~25× zyada. Published uplift 5–6× hai; v1 135× deta tha. |
| 4 | **Reservoir pressure: constant → P_res(t)** | Steam daalne se well ke paas pressure thoda **charge** hota hai (2 kPa per tonne), phir produce karte waqt **bleed** hota hai (τ ≈ 25 d). Aur P_wf ab ek **absolute** number hai (~1,144 kPa, pump ke upar 100 m liquid). | v1 me `Pwf = 0.4 × Pr` tha, toh Pr formula se **cancel** ho jata tha — reservoir pressure dashboard pe dikhta tha par kuch badalta nahi tha. |
| 5 | **Wellbore heat loss + sandface quality** | 1,150 m pipe me garmi nikalti hai; neeche quality = 0.55 × upar wali. | v1 isko ignore karta tha — jo optimistic tha (upar §1). |
| 6 | **SPM: fixed → declining schedule** | Oil thanda/gaadha hota jaye toh pump **dheere** karo taaki rod float na kare. Pump set-point se shuru hota hai, viscosity badhne pe khud 2 SPM ke floor tak ghatta hai. Saath me fillage 0.85 max, float hone pe fillage girti hai (float = barrels ka nuksaan). | Field me heavy-oil pumps **3–6 SPM** pe chalte hain. v1 ka poora −30% **10 SPM** chalane se aaya tha — jo koi operator nahi chalata. |

**v3 (26 Sep raat):** Boberg–Lantz ka δ ab constant nahi, produced fluids ki heat se **computed** hai (SPE PEH eq. 15.70–15.74); BL factor = 0.5 exactly, sourced.

**rev 9 se rev 12 tak (superseded, samjho par quote mat karo):** rev 9 me Boberg–Lantz δ
sourced tha, `P_res` xfail closed thi, par water cut ek **constant 85%** tha aur cycle
sirf ek **rate cutoff** pe khatam hota tha. Reference tab SOR **4.03** deta tha, aur
recommendation (**1,600 t / 0.70 m³/d / 4 spm**) ka **83–96% gain sirf cutoff se** aata
tha — humare hi assumed baseline cutoff (1.3 m³/d) ke movement se, real physics se nahi.

**Rev 12 (physics wave 4, historical/superseded):** water cut ek **state** ban gaya (§5b),
Pal–Rhodes emulsion + 10× cap, **float-onset produce-end rule** (rate cutoff **ya** 3
din float alarm, jo pehle aaye), `AOF_REF_M3D` field peak band pe retuned (0.46→0.56).
Reference set-point pe SOR **4.50 gross**, uplift **5.41×**. Par rev-12 ka recommendation
(1,000 t / 85 kgf/cm² / 3 spm, SOR 3.19, **+₹9,574/cycle-day**) baseline ko **hamesha
pull-on-float** maan ke chalta tha — jab OIL ka operator float pe **slow** karta hai (VFD),
yeh poora +₹9,574 gain gayab ho jata hai. Yehi rev-13 ka top finding hai (§5c). **Kabhi mat
bolo** +₹9,574, SOR 3.19, ya "236 tests" as current.

**Rev 13 (physics wave 5, CALIBRATED, current):** float pe operator ka response —
slow karna ya pull karna — ab khud ek **policy control** hai, aur baseline, recommendation,
cold counterfactual teeno pe SAME policy apply hoti hai (poori mechanism §5c me). Reference
set-point (1,500 t / 7 d / 1.2 m³/d / 5 spm / 86 in / 91 kgf/cm², shipped default `pull`,
unchanged) pe **SOR 4.50** gross. **263 tests pass, 2 xfail** (soak — no physics optimum;
mid-range diesel discount pe steam optimum BGW-8 range se neeche). Literature band: SOR 3–8,
uplift 5–6×, peak 15–40 bbl/d, produce months-long.

**Honest gaps rahte hain (strict xfail, failure nahi):**
- **Soak ka koi interior optimum nahi** — SOR soak 3→15 din me sirf ~1.2% girta hai
  (monotone, flat). Isliye soak ko **field practice pe fix (10 din)** rakha hai, twin se
  derive nahi kiya.
- **Mid-range (0.15) diesel discount pe best slug size BGW-8 se neeche** — gross-margin
  optimum ~750 t hai, BGW-8 ka 1,040–1,560 t se kam. Revealed preference se padhein toh
  OIL ka steam humari mid-range assumption se sasta hoga.
- **Cold well har float-policy ke under shut in hai** (rev-12 me yeh "2-spm pe pump nahi
  hota" ek xfail thi — ab woh xfail **un-xfail** ho chuki hai, kyunki counterfactual ab
  policy follow karta hai: `pull`/`vfd_hold`/`vfd_then_pull` ke under shut in, sirf `none`
  ke under floating pumped). Field ne yeh wells cold produce kiya tha, toh model ka shut-in
  reading ek **upper bound** hai, exact nahi (§5c).

**Recommendation (physics-grid, VFD-hold policy) vs baseline (b), SAME policy:**

| | steam t | soak d | pressure kgf/cm² | stroke in | start spm | cutoff | SOR | ended by | net cash ₹/cycle-day (FY25/$65/net-of-levies) |
|---|---|---|---|---|---|---|---|---|---|
| Baseline (b), VFD-hold | 1,300 | 10 | 91 | 86 | 5 | 1.3 | 3.29 | float pull @ 2-spm floor | +12,064 / −582 / −14,193 |
| **Recommended, VFD-hold** | 1,000 | 10 | 89 | 64 | 4.5 | 0.60 backstop | **2.83** | float pull @ 2-spm floor | **+15,396 / +3,738 / −8,811** |

**Gain KABHI ek akela number me mat bolo — hamesha teeno baseline-policy naam ke saath:**
- Baseline bhi VFD-hold kare (fair, same policy): **+3,332 / +4,319 / +5,382**
  (FY25/$65/net-of-levies) — stroke 57%, cutoff 30%, steam 11% se aata
- Baseline pehle alarm pe hi pull kare (rev-12 wala operation): +12,917 / +14,694 /
  +16,606 — **68% yeh sirf policy switch hai**, set-point nahi (yehi purana +₹9,574 tha)
- Baseline float ko ignore kare, kuch na kare: **−3,865 / −2,513 / −1,057** —
  float-safe recommendation yahan paisa **kho deta hai**, kyunki model rod-failure/
  workover cost price hi nahi karta

**Objective ab hai: net cash per cycle-day (counterfactual-free), incremental margin
nahi** — kyunki incremental margin ka cold-baseline khud policy ke saath badal jaata,
jo policy switch ko recommendation ka apna gain bana deta. Kabhi ek single gain number
bina baseline ki apni float-policy bataye mat bolo.

> **Yaad rakhne wali baat:** *"Humne apne hi model ko audit kiya, 25× optimistic paaya,
> physics ko published models se replace kiya, external review ke baad hardening ki, phir
> paaya ki water cut cycle ke andar badalta hai jo rod float ko late-cycle phenomenon
> banata hai — aur phir ek doosre re-score ne dikhaya ki humara apna gain number sirf ek
> baseline-operating-assumption ka artifact tha. Ab hum float-response ko khud ek policy
> banate hain aur teeno number saath bolte hain."* Yeh weakness nahi, engineering maturity hai.

---

## 3. Andrade relation — "shahad ko garam karo"

Shahad fridge se nikaal — chalta hi nahi. 10 second microwave me daal — paani jaisa beh
jata hai. Heavy crude wahi hai: lambi hydrocarbon chains aur asphaltenes ek doosre pe slide
karte hain, aur yeh slide karna **thermally activated** hai — jaise reaction ko energy
barrier paar karna padta hai. Isliye viscosity **exponentially** girti hai, linearly nahi.

**Andrade (1930):**

```
μ(T) = A · exp(B / T_K)        T_K = T_°C + 273.15
```

- **B > 0** hone ki wajah se μ hamesha **strictly** girti hai T ke saath — yeh
  analytically guaranteed hai, isliye humara monotonicity test kabhi flake nahi karta.
- Do unknowns (A, B) ke liye do points chahiye. Log lo to yeh 1/T me linear ban jata hai:
  `B = ln(μ₁/μ₂)/(1/T₁ − 1/T₂)`, `A = μ₁/exp(B/T₁)`.

**Humare do anchor points:**
1. **11,500 cP @ 50 °C** — ✅ CONFIRMED, OIL ke apne 10,000–13,000 cP range ka midpoint.
2. **50 cP @ 150 °C** — ⚠️ **ASSUMPTION.** Baghewala crude ka koi high-temperature lab
   measurement kahin nahi mila.

Result: **A = 1.164×10⁻⁶ cP, B = 7,436.6 K.**

**[v1]** Aur ab magic number: **50 °C pe 11,500 cP → 244 °C pe 2.18 cP.** Yeh **~5,000
guna** patla hona hai. Shahad se paani. **Yahi CSS ka poora business case hai.**

**Par dhyan de — yahi Andrade ki kamzori bhi hai.** Isi formula ko 290 °C tak kheencho toh
**0.63 cP** aata hai — paani (1 cP) se bhi patla. Heavy crude kabhi paani se patla nahi
hota. Isliye **v2 me Walther / ASTM D341** (petroleum industry ka standard
viscosity-temperature chart) use hota hai, **same do anchors** pe fit, aur **1 cP ka
floor**. v2 values: μ(244 °C) = **7.2 cP**, μ(290 °C) = **4.13 cP** — ab bhi 11,500 se
**~1,600–2,800 guna** patla, toh business case zinda hai, bas physically sensible hai.
(Andrade 1930 ka naam aur 1/T wali intuition phir bhi sahi hai — thermally activated flow.)

*(Code ki ek chhoti detail jo tujhe smart dikhayegi: `field_params.json` me `andrade_A` aur
`andrade_B_K` jaan-boojh kar **null** rakhe hain. Rounded values likhne se μ(50 °C) 11,489.6
aata tha, exactly 11,500 nahi, aur test fail hota tha. Null rakhne se `viscosity.py` runtime
pe full precision me khud fit kar leta hai. Yeh laziness nahi, **higher-precision path** hai.)*

> **Yaad rakhne wali baat:** viscosity is chain ka **hinge** hai. Isko hata do to thermal
> model ka temperature bekaar ho jata hai aur IPR/SRP dono andhe ho jate hain.

---

## 4. Vogel IPR — "straw se gaadhi lassi peena"

Ek motti straw se **gaadhi lassi** pee ke dekh. Jitna zor se kheechega utni zyada aayegi —
par **do guna zor lagane se do guna lassi nahi aati**, curve jhuk jata hai. IPR reservoir ki
wahi **supply curve** hai, aur **Vogel (1968)** us jhukav ka industry-standard shape hai:

### Pehle shabd — yeh sab judge bolega, toh matlab pata hona chahiye

| Shabd | Matlab (lassi wali language me) |
|---|---|
| **Pr** (reservoir pressure) | Reservoir ke andar ka pressure — glass me lassi kitne zor se "dhakel" rahi hai. Baghewala: **11,400 kPa** (~116 kgf/cm²). |
| **Pwf** (flowing bottomhole pressure) | Well ke bottom pe, bahte waqt ka pressure — straw ke andar ka pressure jab tu kheench raha hai. Pump isko kam rakhta hai. |
| **Drawdown** | `Pr − Pwf` — kitna zor se kheench rahe ho. Drawdown zyada = rate zyada (ek limit tak). |
| **AOF** (absolute open flow) | Agar Pwf ko **zero** kar do (poora zor) toh maximum kitna aayega — theoretical ceiling, q_max. |
| **PI / J** (productivity index) | Har 1 kPa drawdown pe kitna oil — `q / (Pr − Pwf)`. Well ki "kheenchne layak-ness". Viscosity girne pe PI badhta hai. |
| **IPR** (inflow performance relationship) | Poora curve: har Pwf pe reservoir kitna dega. Reservoir ki **supply curve**. Pump ki demand isse jahan milti hai, wahi rate. |

### Formula

```
q/q_max = 1 − 0.2·(Pwf/Pr) − 0.8·(Pwf/Pr)²
v1:  q = AOF_REF · vogel_shape · (μ_ref / μ)
v2:  q = AOF_REF · vogel_shape · uplift(r_h, μ_hot) · (P_res / 11,400)
```

**[v1 — ab code me nahi]:**
- Pr = 11,400 kPa poore cycle constant; **Pwf = 0.4 × Pr** → shape hamesha 0.792 — aur
  Pr formula se cancel ho jata tha (dashboard pe dikhta tha, badalta kuch nahi tha).
- Rate ki saari harkat mobility factor `μ_ref/μ` se — 244 °C pe ≈ **5,270×**. Yahi 25×
  optimism ki jad thi.
- `AOF_REF_M3D = 0.7` → cold rate 0.55 m³/d; cutoff range 1–8 m³/d.

**v2 — aaj ke (rev-5 calibrated) values:**
- **Pwf absolute ~1,144 kPa** (casing head 200 kPa + pump ke upar 100 m liquid column).
- **P_res(t) live:** 11,400 se start, steam se charge (**1 kPa/t**, calibration me 2 se
  halve kiya), production me bleed (τ ≈ 25 d). Ab pressure sach me rate ko hilata hai —
  itna ki P_res sweep +61% SOR deta hai (honest xfail, upar §2b).
- **Uplift** = composite-radial (Boberg–Lantz): garam ring + thanda bahar. Max 10×,
  reference set-point pe **5.66×** aata hai (BGW-8's 5–6× ke andar). Interesting baat:
  uplift temperature se lagbhag flat hai — **garmi ka radius paisa kamata hai, garmi ka
  degree nahi.**
- **`AOF_REF_M3D = 0.46`** (calibrated, v2-uncalibrated era me 0.60 tha) → cold rate
  **~0.447 m³/d ≈ 2.8 bbl/d**. Cutoff range ab **0.6–2.0 m³/d**. Thanda well range ke
  floor se neeche — **bina steam ke uneconomic, yeh CSS ka premise hai.** (Yeh do
  constants coupled hain; ek badlo toh doosra bhi, warna
  `test_cold_rate_is_uneconomically_low` jhooth bolega.)

> **Yaad rakhne wali baat:** judge poochhe *"steam paise me kahan badalti hai?"* — jawab:
> `twin/ipr.py`, function `composite_uplift()`. v1 me yeh ek line thi
> (`mu_ref/mu`) — aur wahi line 25× optimism ka source thi.

---

## 5. Rod floating — exactly kya hota hai

**Sucker rod pump** kya hai: 1,150 m lambi steel ki rod, neeche piston (plunger), upar
pumpjack (ghode ke sar wala) usse upar-neeche jhulata hai.

- **Upstroke** me motor uthata hai: rod ka apna weight + oil ka column + fluid ka drag.
  Yeh peak load hai aur yeh bijli ka bill hai.
- **Downstroke** me motor kuch nahi karta — **rod ko apni marzi se, gravity se girna hota hai.**

Ab problem: agar oil kaafi **gaadha** hai, to girte waqt ka **viscous drag** rod ke submerged
weight ke barabar aa jata hai. Rod **dheere girti hai**, horsehead se peeche reh jati hai —
yeh **"floating"** hai. Phir jab horsehead neeche pahunch chuka hota hai aur rod baad me
girti hai, woh **thap se neeche wale hisse pe takraati hai**. Rod tension me strong hai par
**compression me kamzor** — toh neeche wala section buckle karta hai, fatigue crack aata
hai, aur ek din **rod part ho jati hai**. Workover: **$15k–$50k** + lost production.

**Formulas:**

```
Buoyant rod weight   W_b = (m'·L)·g · (1 − ρ_fluid/ρ_steel)
Fluid load           F_f = ρ_fluid · g · L · A_plunger
Viscous drag         F_v = K_VISC · μ[Pa·s] · v_avg · L,   v_avg = 2·stroke·spm/60
Peak rod load        P   = W_b + F_f + F_v
FLOATING INDEX       FI  = min(F_v / W_b, 1)      → 0.6 se upar = risk
Pump capacity        q_max = A_plunger · stroke · (spm·1440) · 0.85
```

**Ek baar numbers khud nikal le, phir yeh module tera ho jayega:**
- Rod: 3.8 kg/m × 1,150 m = 4,370 kg → hawa me 42.9 kN
- API 15.5 → SG = 141.5/147 = 0.9626 → ρ = **963 kg/m³**
- Buoyancy factor = 1 − 963/7850 = 0.877 → **W_b = 37.6 kN**
- Plunger area = π/4 × 0.057² = 2.552×10⁻³ m²
- Fluid load = 963 × 9.81 × 1150 × 2.552e-3 = **27.7 kN**
- **Base load = 65.3 kN — yeh poore cycle constant hai.** Iske upar jo bhi hai woh **pura
  viscous drag hai.**

**[v1 cycle-end ka example — algebra practice ke liye]** Cycle ke end pe: μ = 2,203 cP = 2.203 Pa·s, v_avg = 2×3×8/60 = 0.8 m/s
→ F_v = 10 × 2.203 × 0.8 × 1150 = **20.3 kN** → peak load **85.6 kN**,
**FI = 20.3/37.6 = 0.539**. Dashboard ka har number, do line ke algebra se.

Ulta bhi kar sakta hai: **8 spm pe FI 0.6 ko chhuta hai μ ≈ 2,450 cP pe; 12 spm pe sirf
1,635 cP pe.** Yaani **pump tez chalao to kam thand bardasht kar sakte ho.** Yeh poori risk
story hai.

**v2 me ek hi cheez ko doosri nazar se:** FI ab `v_stroke / v_fall` likha jata hai — pump
rod ko kitni tezi se neeche bhej raha hai, vs gaadhe oil me rod **khud** kitni tezi se gir
sakti hai. Drag velocity me linear hai, isliye yeh algebraically **wahi** F_v/W_b hai.
Aur isi se v2 ka declining-SPM schedule nikalta hai: FI ko margin ke neeche rakhne ke liye
jitna SPM chahiye, pump utna hi chalta hai (floor 2 SPM).

### Threshold 0.6 kahan se aaya? (judge yeh poochega)

Honest jawab: **0.6 ek design choice hai, measured number nahi.** Hamare SPEC me 0.6 rakha
gaya, aur `K_VISC = 10` isi tarah tune kiya gaya ki thanda heavy oil mid-to-high SPM pe 0.6
ke upar jaye aur garam oil pe drag negligible rahe. **Defence:** hamara FI wahi physical
quantity hai jo published rod-failure work me "**scaled load ratio**" kehlati hai
(SPE 233386 — us paper me learned boundary se ~14 din pehle failure predict hota hai). 0.6
wahi role play karta hai jo unka learned decision boundary karta hai. **OIL ke dyno cards
aur failure records milte hi yeh threshold unke data pe re-fit hoga** — yahi hamara pehla
data ask hai.

> **Yaad rakhne wali baat:** honesty flag saath rakhna — *"Yeh static, one-number-per-day
> approximation hai API RP 11L ka. Asli dynamometer card ke liye rod elasticity aur wave
> propagation chahiye. Yeh cycle simulator ke liye theek hai, mechanical design tool nahi hai."*

### 5b. Rev 12 ka sabse bada physics finding: water cut ek constant nahi, ek STATE hai

Rev 9 tak humne `fluid.water_cut = 0.85` ek **constant** rakha tha — poore cycle me
same. Us model me rod float **kabhi bindta hi nahi tha**, kyunki 85% water pe produced
stream **water-continuous** hai (paani jaisa mobile), aur uska drag oil ki apni viscosity
se independent hota hai.

Rev 11 me humne water cut ko ek **state** banaya: produced paani do sources se aata hai —
**condensate flowback** (jo steam inject kiya tha, wahi wapas aata hai, ek tank drain hone
jaisa exponentially decay karta hai) aur **formation water** (reservoir ka apna paani, ek
lower floor `formation_water_cut` ≈ 0.45). Result: cycle **shuru me water-continuous**
(~0.87 — condensate abhi flowback ho raha hai) aur **cycle ke aakhri hisse me
oil-continuous** ho jaata hai (<0.70 — jise hum "**inversion**" kehte hain, jahan paani se
zyada oil hai stream me).

**Yahi wo jagah hai jahan rod float wapas aata hai — par honestly, sirf late cycle me:**
- Jab stream oil-continuous ho jaata hai, uski effective viscosity **Pal–Rhodes emulsion
  law** (Brinkman jaisa hi, 60% water tak) se calculate hoti hai — jo reservoir oil ki
  apni viscosity se **20× tak zyada** ho sakti hai (capped at 10×, kyunki published data
  isi range me hai).
- Isi wajah se FI produce day ~130 ke aas-paas **achanak 0 se 0.8–1.0 tak jump** karta hai
  — early, hot, water-continuous hissa **kabhi float nahi karta** (FI < 0.05).
- **Rod float ab ek late-cycle phenomenon hai** — koi bhi cycle jo poora rate-cutoff tak
  chalta hai (constant 85% cut ki tarah), woh late me float karega.

**Isi finding ne poori recommendation badal di:**
- Purana approach (rev 9/10/11): ek **fixed low rate cutoff** dhoondo jahan FI kabhi 0.6
  nahi cross kare — par yeh fragile nikla (~40% UQ draws me peak khud us cutoff se neeche
  tha, cycle day-1 pe khatam ho jaata).
- Naya approach (rev 12): **`produce_end_rule = "either"`** — cycle khatam hota hai ya toh
  rate cutoff pe, ya **FI > 0.6 lagataar 3 din** pe, jo bhi pehle aaye. Yeh exactly wahi hai
  jo ek real operator karega: dyno card pe float dikhe, pehle SPM slow karo, phir bhi float
  ho toh **well pull karo aur re-steam karo** — mahino tak floating rods nahi chalate.
- Naya recommendation isi rule ko exploit karta hai: rods **slow aur short chalao** (3 spm,
  64-in stroke) taaki float onset **late aaye** (day 179, na ki day 149 jaisa reference pe).
  Slow rods liquid bhi slow lift karte hain, toh condensate tank slow drain hota hai, toh
  inversion late aata hai — yehi poori mechanism hai.

> **Stage pe kya bolna hai:** "Humne paaya ki water cut cycle ke andar badalta hai —
> shuru me paani-heavy, baad me oil-heavy. Jab woh oil-continuous ho jaata hai, rods
> practice speed pe float karte hain — par sirf cycle ke late hisse me, jaisa ek real
> operator anticipate karega. Isliye humari recommendation hai: rods slow-short chalao,
> aur float alarm 3 din persist kare toh well pull karo — ek fixed low cutoff chase mat
> karo."

**Yeh conditional hai teen assumptions pe** (kabhi bina bataye mat bolo): inversion point
0.70 [ASSUMPTION], Pal–Rhodes emulsion law + 10× cap [ASSUMPTION], aur `fi_alarm_days = 3`
[ASSUMPTION, koi Baghewala SOP nahi]. Ek late-cycle dyno card aur ek water-cut-vs-time
log inhe measure kar sakta hai.

**Cold-well twist (rev 12, historical):** isi emulsion law se ek naya honest gap mila — model
kehta hai ki ek **cold, unstimulated well** (45% formation water cut pe) **2 spm pe pump hi
nahi ho sakta** assumed 86-in unit pe, kisi bhi published emulsion law ke under. Field ne yeh
wells cold produce kiya tha, toh model ki koi assumption galat hai — humne yeh chhupaya nahi,
ek strict test-failure (`xfail`) ke roop me record kiya tha rev 12 me. **Rev 13 me is xfail ka
resolution: cold well ab pump-nahi-ho-sakta nahi, balki policy ke under shut in maana jaata
hai** (§5c) — same finding, honest framing thodi badal gayi.

### 5c. Rev 13 ka sabse bada finding: float pe operator "slow kare ya pull kare" khud ek CONTROL hai

Rev 12 ka pura +₹9,574/cycle-day headline external re-score me pakda gaya: baseline (b)
me hum **hamesha** float-alarm pe well **pull** kar dete the (rev-12 ka `pull` rule) — chahe
woh us waqt achha oil hi kyun na de raha ho. Jab twin ke apne **VFD-slow** mode se dobara
compare kiya, yeh gain **gayab ho gaya**.

**Chaar policies (`css.float_policy`), sab kuch simulate_css_cycle ka parameter:**
- **`pull`** (rev-12 wala) — SPM keep-up limit pe chalta hai (margin 1.0); float alarm 3
  din persist kare toh well pull.
- **`vfd_hold`** (**RECOMMENDED**) — ek VFD pump ko slow karke floating index ko **0.6 pe
  hold** karta hai, floor **2 spm** tak; sirf floor pe 3 alarm din ke baad pull.
- **`vfd_then_pull`** — same par floor thoda upar hai (max(2, 0.5×start spm)).
- **`none`** — float ko bilkul ignore, sirf rate cutoff pe cycle khatam.

**Yeh SAME policy teeno jagah apply hoti hai:** baseline, recommendation, AUR cold
counterfactual. Cold, unstimulated well bhi ab isi policy ke floor pe chalta hai — agar
wahan FI 0.6 se upar hai (jaisa base case me hai — FI 1.0, PRL 189 kN 2-spm floor pe), toh
woh **shut in** maana jaata hai, pump nahi. Sirf `none` policy ke under woh floating pumped
rehta hai (rev-12 ka reading). Isi wajah se "cold well pumpable ya nahi" ka jawab ab
"depends on the policy" hai — pehle jaisa ek fixed xfail nahi.

**Kyun matter karta hai:** counterfactual cancel ho jata hai jab tak policy switch na ho.
Agar baseline aur recommendation ka comparison ek policy switch bhi karta hai (jaise
"none" wala cold well "pumpable" hai par "pull" wala "shut in"), toh woh switch khud
₹8.3k/d ka farak bana deta hai — aur agar isko recommendation ka apna gain bol diya, toh
woh galat attribution hai. Isiliye SAME-policy comparison hi "the gain" hai.

**Teen aur additions isi wave me:**
- **Smooth inversion band** (0.075 water-cut chaudi) — pehle emulsion viscosity ek sharp
  switch pe **3,365× tak** ek hi din me jump karti thi (W/O se O/W); ab band ke andar
  linearly blend hoti hai, max jump **1.22×/din**. ₹ pe asar chota hai (<₹0.1k/d) — yeh
  numerical honesty ke liye hai, economics ke liye nahi.
- **Injectivity gate** (≥400 kPa sandface margin, reservoir pressure ke upar) — yeh
  **85 kgf/cm² ka purana floor reject** kar deta hai (sirf 53 kPa margin deta tha); naya
  floor **89 kgf/cm²** hai (498 kPa margin). Pressure lever economically bahut kam matter
  karta hai — iska role sirf feasibility hai.
- **Net-of-royalty-and-cess price deck** (~₹3,600/bbl, ~35% levies, OIL ki apni FY25
  Annual Report se cross-checked) — is deck pe **har feasible grid point negative hai**,
  cold, shut-in well ke against bhi.

**Ek aur judgement call:** diesel bulk-discount ki base **0.30 → 0.15** move hui (apne hi
U[0, 0.30] range ka mid-point) — coordinator ki instruction pe, **koi physics recalibrate
nahi hua**. Knock-on: gross-margin-optimum slug size ab ~750 t hai, BGW-8 ke 1,040–1,560 t
se kam (naya strict xfail — revealed preference se, OIL ka steam humari mid-range se sasta
lagta hai).

> **Stage pe kya bolna hai:** "Humne paaya ki jab rods float karte hain, operator **slow
> karta hai ya pull karta hai** — yeh choice khud kisi bhi set-point se zyada paisa move
> karti hai. Isliye hum yeh choice ek policy banate hain, aur usi policy ko baseline aur
> cold well pe bhi fairly apply karte hain. Fair comparison me gain modest hai
> (+₹3,332/cycle-day) — par woh honest hai."

**Yeh conditional hai un assumptions pe jo pehle se the** (§5b) — inversion point, Pal–Rhodes
law, `fi_alarm_days = 3` — plus naye: `vfd_hold_fi = 0.6`, `vfd_spm_floor = 2`,
`vfd_turndown_frac = 0.5` [ASSUMPTION, NEMA-D VFD turndown], `min_injection_margin_kPa = 400`
[ASSUMPTION 300–500].

---

## 6. Humne kya simplify kiya — aur judge ko kaise bolna hai

Yeh table tera **kavach** hai. Judge assumption pakde, usse pehle **tu khud bol de.**

*(v1 ke teen simplifications — τ = 20 d cooldown, 8 m drainage disc, constant Pr — v2 me
**hata diye gaye**. Table me unka status likha hai, taaki koi purana slide/doc dikhaye toh
tu jawab de sake.)*

| Simplification | Kya kiya | Judge ko kya bolna |
|---|---|---|
| **COOLDOWN_TAU_DAYS = 20** — *[v1, deleted]* | v1 me injection ke baad simple exponential decay thi | "Woh invented tha; humne use Boberg–Lantz (1966) se replace kiya, jo conduction loss aur produced-fluid heat removal dono count karta hai. Uska published uncertainty ~42% hai, woh bhi hum state karte hain." |
| **DRAINAGE_RADIUS_M = 8.0** — *[v1, deleted]* | v1 ka saturation knob, 10 → 8 retune kiya tha taaki optimum range me aaye | "Woh asli drainage radius nahi tha, ek fudge tha — hamare review ne pakda aur humne delete kiya. Ab asli drainage radius 100 m hai (field typical 50–150 m), composite-radial PI ke andar." |
| **AOF_REF_M3D** — *0.7 (v1) → 0.60 (Tier-1) → **0.46** (rev 5, calibrated), hard-coded `ipr.py` me* | Measured productivity index nahi hai | "Cold, unstimulated well ka assumed open-flow. 0.46 se cold rate ~0.447 m³/d (2.8 bbl/d) aur stimulated peak ~15.9 bbl/d — reference set-point pe uplift 5.66×, BGW-8 ke 5–6× ke andar. OIL ka measured PI isko replace karega." |
| **K_VISC = 10.0** — *hard-coded `srp.py` me* | Rod aur tubing ke beech ka gaadha oil rod ko kitna rokta hai, uska ek lumped number — kyunki tubing/rod ke gap ka exact geometry hamare paas nahi | "Yeh ek tuned 'drag knob' hai: itna rakha ki thanda gaadha oil tez SPM pe floating zone (>0.6) me jaye, aur garam patla oil pe drag lagbhag zero ho. Sweep chalaya — koi ajeeb jump ya saturation nahi. OIL ke dyno cards se yeh fit hoga." |
| **Constant Pr** — *[v1, replaced]* | v1 me koi depletion nahi thi | "Ab P_res(t) hai — steam se charge (1 kPa/t, rev-5 me 2 se halved), production me bleed (τ 25 d). Yeh calibrated hai, par ek disclosed gap ke saath: P_res drop karne pe SOR **+61%** badhta hai vs Liaohe field ka 20–40% literature band — strict xfail, hum over-respond karte hain aur yeh khule aam bolte hain." |
| **Hard-coded constants** (v2 me bhi) | `AOF_REF_M3D`, `S_COLD`, `K_VISC`, 150 °C / 50 cP anchor, `PRESSURE_BOOST_PER_T_KPA` code me hain, JSON me nahi | "Sab `# ASSUMPTION` ke saath code me documented hain; recalibration me inhe params file me move karna planned hai. 'Kuch bhi hard-coded nahi' **mat** bolna." |

**Universal line jo har baar bachayegi:** *"That's an assumption, here's exactly why we made
it, and here's the one measurement from OIL that would replace it."*

---

## 7. Day 0 → 61 — poora cycle, din-b-din

> **[v1 engine output — mechanism samajhne ke liye, numbers quote karne ke liye nahi]**
> Neeche ki saari tables v1 engine ki hain (yeh dashboard ke ab-superseded v1 replay ke
> numbers hain — current dashboard ab v2/rev-5 baked series dikhata hai, dekh
> `dashboard/README.md` §6). Kahani — garam → patla → plateau → decline → rod load upar —
> **samajh**; numbers (244 °C, 74.96 m³/d, 1,159 m³, SOR 1.29) **historical hain, stage pe
> mat bolna**. v2 (calibrated) me yahi set-point cutoff 3.0 pe pehle din hi band ho jata hai
> (upar §2b) — v2 ka apna reference cycle set-points 1,500 t / 7 d / **1.2 m³/d** cutoff /
> 5 spm pe chalta hai, 3.0 pe nahi.

Set-points: **1,500 t steam · 7 din soak · 3.0 m³/d cutoff · 8 spm.**
Yeh dashboard ke baked replay ka cycle hai.

### Days 0 → 20.3 — INJECT (21 rows)

74 t/d pe 1,500 t = **20.27 din**. Well **shut in** hai — oil zero, rod load zero, FI zero.

| Din | T (°C) | μ (cP) | heated radius |
|---|---|---|---|
| 0 | 50.0 | 11,500 | 0 m |
| 1 | 60.8 | 5,446 | 1.70 m |
| 5 | 101.8 | 478 | 3.72 m |
| 10 | 150.3 | 49.3 | 5.17 m |
| 15 | 196.8 | 8.7 | 6.30 m |
| **20.3** | **244.2** | **2.18** | **7.20 m** |

Dekh day 0→1: sirf **+11 °C** me viscosity **aadhi** ho gayi. Exponential ka kamaal.

*(v1 me yahan bola jata tha "7.2 m heated radius vs 8 m drainage disc — isliye optimum".
**Ab mat bolna** — woh 8 m disc fudge tha, §2 dekh.)*

### Days 20.3 → 27.3 — SOAK (7 rows)

Steam band, well abhi bhi shut in. v1 me τ = 20 din wali cooldown **usi din se** shuru
(v2 me Boberg–Lantz — thanda hona dheere, 30 din pe ~69% garmi bachi, vs v1 ki ~22%).

| Din | T (°C) | μ (cP) |
|---|---|---|
| 21 | 237.2 | 2.48 |
| 25 | 203.3 | 7.00 |
| 27.3 | 186.8 | 12.2 |

7 din ka soak humein lagbhag **57 °C** ka nuksaan deta hai. Physically soak **uniformity
khareedta hai** — garmi wellbore ke aas-paas se aage failti hai. v1 optimiser soak ko
**3 din (range ka floor)** pe le jata tha — par woh v1 ki fast τ = 20 d cooldown ka
artefact tha (har soak din = seedha garmi ka nuksaan). **OIL khud 7–13 din soak karta
hai**, aur v2 me soak ka SOR pe asar lagbhag flat hai. **"Optimal soak 3 din" kabhi mat
bolna.**

### Days 27.3 → 61.3 — PRODUCE (35 rows)

Yahan **do alag regimes** hain — yeh difference jaanna high-value detail hai.

**Regime 1 — pump-limited (din 27.3 → ~38).** Reservoir pump se **zyada** de sakta hai. Rate
flat pin ho jati hai **74.96 m³/d** pe = `2.552e-3 × 3.0 × (8×1440) × 0.85`.
Chart me jo "peak" dikhta hai woh **plateau** hai — **pump ka ceiling hai, reservoir ka nahi.**

**Regime 2 — reservoir/thermally limited (din ~39 → 61.3).** Zone itna thanda ho gaya ki IPR
rate pump capacity se neeche gir gayi. Ab har din rate girti hai kyunki μ chadh rahi hai.

| Din | phase | T (°C) | μ (cP) | oil (m³/d) | rod load (kN) | FI |
|---|---|---|---|---|---|---|
| 27.3 | produce start | 186.8 | 12.2 | 74.96 | 65.4 | 0.003 |
| 34.3 | plateau | 146.4 | 58.1 | 74.96 | 65.9 | 0.014 |
| 39.3 | decline shuru | 125.1 | 150.0 | 42.5 | 66.7 | 0.037 |
| 44.3 | declining | 108.5 | 338 | 18.9 | 68.4 | 0.083 |
| 49.3 | declining | 95.6 | 670 | 9.5 | 71.5 | 0.164 |
| 54.3 | declining | 85.5 | 1,181 | 5.4 | 76.2 | 0.289 |
| 59.3 | cutoff ke paas | 77.6 | 1,877 | 3.40 | 82.6 | 0.459 |
| **61.3** | **cutoff hit** | **75.0** | **2,203** | **2.89** | **85.6** | **0.539** |

Dekh do curves **ulti disha** me ja rahe hain: **oil neeche, rod load upar** — aur dono ka
**karan ek hi hai: μ badh rahi hai.** Yeh coupling hi humara poora project hai.

Cycle rukti kab hai: loop pehle row likhta hai, **phir** break karta hai jab
`prod_rate < cutoff`. Isliye **aakhri row hamesha cutoff se neeche hoti hai** — yahan 2.89
vs 3.0.

**Cycle totals:** oil **1,158.96 m³** · **SOR 1.2943 t/m³** · energy 20.59 kWh/m³ ·
**61.27 din** · max FI **0.539** · failures_expected **0**.

**Demo ka stress-test moment:** spm 12 kar ke re-run kar. Zyada spm = zyada rod velocity =
usi viscosity pe zyada drag — ab threshold 2,450 cP ki jagah **1,635 cP** pe aata hai, aur
**alarm baj jata hai.** Mechanism bilkul sahi hai. **Par honest note:** MOCK mode me 12-spm
run baked physics nahi, **in-browser approximation** (`mockSimulate`) hai — panel khud
likhta hai. Isliye bolna: *"this illustrates the mechanism"*, "the twin predicted it" nahi.

**[v1] Optimised cycle** (1,600 t / 3 d / 8.0 / 10 spm): oil 1,765.6 m³, SOR 0.9062,
53.6 din, max FI 0.255. Hamare review ne dikhaya ki is −30% ka **poora** fayda **10 SPM**
chalane se aaya tha (v1 me pump plateau hi rate ki ceiling tha, toh tez pump = zyada oil).
SPM ko practice band **3–6** pe cap karo toh SOR baseline ke barabar aa jata hai. **Isliye:
"10 SPM pe chalao" ya "−30%" kabhi nahi.** Idea jo bachta hai — *chaaron knobs coupled
hain* — woh sahi hai.

**Rev 12 (historical) recommendation** — 1,000 t / 85 kgf/cm² / 3.0 spm, `pull` policy →
SOR 3.19, **+₹7,973/cycle-day** (Δ +9,574 vs baseline, jo bhi `pull` karta tha). **Kabhi
mat bolo, superseded** — §5c dekh.

**Rev 13 (physics-grid, calibrated) recommendation, jo ab quote kar sakte ho:** 1,000 t /
10 d / 89 kgf/cm² / 64-in stroke / start 4.5 spm / cutoff 0.60 m³/d backstop, **VFD-hold
policy** (rods 3 din tak alarm ki 2-spm floor pe rehte hain, phir pull) → SOR **2.83**, oil
**353 m³**, produce **196 din** (window 220), net cash **+₹15,396/cycle-day** (FY25) /
**+₹3,738** ($65) / **−₹8,811** (net-of-levies). Baseline (b), **SAME VFD-hold policy**
(1,300 t / 10 d / 91 kgf/cm² / 86-in / 5 spm) → SOR **3.29**, net cash +₹12,064/−582/
−14,193. **Same-policy gain: +₹3,332/+4,319/+5,382** (stroke 57%, cutoff 30%, steam 11%
se aata hai). Agar baseline pehle hi alarm pe pull kar de (rev-12 wala operation): gain
+₹12,917/+14,694/+16,606 (68% sirf policy switch, set-point nahi). Agar baseline float
ignore kare: gain **−₹3,865/−2,513/−1,057** (rod-failure cost unpriced). Isliye is baar
improvement na sirf SPM badhane se na cutoff neeche laane se — **rods VFD se slow rakhne,
stroke short (64 in) rakhne se** aata hai, taaki float ki limit pe (FI=0.6) zyada din
tak, bina FI=1.0 pe jaaye, produce ho sake.

---

## Raat wala 1-minute recap

- **Chain:** heat → μ → rate → load. μ akela hero + villain dono hai.
- **Marx-Langenheim:** patla reservoir garmi leak karta hai; E_h ≈ 0.85 humare cycle pe;
  diminishing returns. (v1 ka "1,750 t optimum" 8 m fudge se tha — ab delete.)
- **Viscosity:** v1 Andrade (290 °C pe 0.63 cP — paani se patla, galat) → v2 **Walther +
  1 cP floor** (290 °C pe 4.13 cP). Ek anchor real (11,500 @ 50), ek assumption (50 @ 150).
- **IPR:** v2 = Vogel × **composite-radial uplift (~4×)** × P_res(t). Thanda well ~0.48 m³/d
  = **uneconomic** = CSS ka premise. Pwf, Pr, drawdown, AOF, PI ke matlab yaad.
- **SRP:** base load **65.3 kN** (37.6 buoyant + 27.7 fluid), uske upar sab drag.
  **FI = F_v/W_b = v_stroke/v_fall**, threshold 0.6 = design choice (scaled-load-ratio
  defence). v2 me SPM khud ghatta hai jaise oil gaadha hota hai.
- **Rev 13 status:** CALIBRATED (physics wave 5). Float pe operator ka response (slow ya
  pull) ab khud ek policy hai, SAME policy baseline/recommendation/cold-well teeno pe.
  Reference SOR 4.50; recommendation (VFD-hold) SOR **2.83** vs baseline (b) VFD-hold
  **3.29**. Gain **kabhi ek number me nahi** — same policy +₹3,332/d, agar baseline pull
  kare +₹12,917/d, agar kuch na kare −₹3,865/d (sab per cycle-day). Honest xfail gaps:
  soak, aur mid-range-discount steam optimum BGW-8 se neeche. **v1 (SOR 1.29, −30%), rev 9
  (+₹4,423), aur rev 12 (+₹9,574, 62% SPM) sab ab historical, stage pe nahi.**
- Aur agar ek line bolni ho: *"Steam inject karo to reservoir garam hota hai, viscosity
  girti hai — bilkul shahad garam karne jaisa. Par shahad ko itna hi garam karo jitna paisa
  vasool ho, aur pump ko itna hi tez chalao ki rod na toote. Humara twin dono ek saath
  decide karta hai."*
