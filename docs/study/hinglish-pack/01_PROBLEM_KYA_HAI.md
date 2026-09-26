# 01 — Problem Kya Hai? (Bilkul Zero Se)

## 1. Pehle SIH kya cheez hai — 60 second me

**Smart India Hackathon (SIH)** ek national-level competition hai jahan ministries aur
PSUs (government companies) apni **real problems** publish karte hain, aur student teams
un problems ka solution banati hain.

Process kuch aisa hai:
1. **Internal hackathon** — pehle apne college me. MNIT apni top teams choose karta hai.
   Max **50 teams per institute** national portal pe bhej sakte hain.
2. **Idea submission** — 6-slide PDF deck portal pe upload. Bas deck. No interview, no demo.
3. **Screening** — online, sirf deck dekh ke.
4. **Grand Finale** — offline, December 2026, 36 ghante continuous.

Do baatein jo strategy badalti hain:
- Ek PS pe maximum **500 ideas** hi submit ho sakte hain, uske baad woh PS freeze.
- Har PS ke liye **4–5 teams** finale me jaati hain, prize **₹1,50,000** — **lekin**
  sponsoring organisation ye keh sakta hai ki *"koi bhi team hamare standard tak nahi
  pahunchi"* aur winner declare hi na kare. SIH 2025 me exactly yeh 3 PS ke saath hua tha.

> **Yaad rakhne wali baat:** hamara asli competitor doosri teams nahi hai — **Oil India ka
> apna bar** hai. Unko impress karna hai, doosron ko harana nahi.

---

## 2. PS SIH26120 exactly kya maang raha hai — plain words me

**Problem Statement ID:** SIH26120
**Organisation:** Oil India Limited (OIL) — ek Government of India PSU
**Title:** *Digital Twin for Well-to-Surface Optimization of Cyclic Steam Stimulation and
Sucker Rod Pump Operations*

Ab isko tod ke samajh:

- **"Digital Twin"** = ek computer model jo asli cheez (yahan: ek oil well) ko itna
  accurately copy karta hai ki tu usme **pehle try kar sakta hai**, phir field me kar sakta
  hai. Jaise flight simulator — pilot pehle simulator me crash karta hai, asli plane me nahi.
- **"Well-to-surface"** = neeche reservoir se lekar upar pumpjack tak, **poora system ek
  saath**. Sirf reservoir nahi, sirf pump nahi — dono, joined.
- **"Cyclic Steam Stimulation (CSS)"** = steam daal ke oil ko patla karna (aage detail me).
- **"Sucker Rod Pump (SRP)"** = woh nodding-donkey pump jo oil ko upar kheenchta hai.
- **"Optimization"** = best settings **automatically** nikalna, banda ke tajurbe (experience)
  ke bharose nahi.

Toh OIL ka sawaal seedha yeh hai: *"Hamare Baghewala field me steam bhi hum hi decide karte
hain aur pump speed bhi hum hi decide karte hain — dono manually, alag-alag, engineer ke
experience se. Kya ek aisa system ban sakta hai jo dono ko ek saath, physics + AI se decide
kare?"*

---

## 3. Baghewala field ki kahani

### 3.1 Kahan hai

Rajasthan me, **Bikaner-Nagaur sub-basin** me, Thar desert ke andar (Jaisalmer district ki
taraf). Jaipur se road distance karib **550–600 km**. Yaani ekdum remote jagah — jahan har
choti si galti pe engineer bhej dena mehnga aur slow hai. **Yehi remoteness khud ek argument
hai** ki wahan ek digital twin kyun chahiye.

Operator: **Oil India Limited**. Area: ~200 sq km ka PML block.

### 3.2 1991 — discovery

1991 me well **Baghewala-1** me heavy oil mila. Rock kya hai? **Jodhpur Sandstone** —
early-Cambrian, yaani karib **540 million saal purani** chattan. Depth: **~1,100–1,150 m**.

Discovery test pe API gravity ~19.5–20° aayi thi. Aaj jo crude nikal raha hai woh thoda aur
heavy hai — **14–17° API**. (Official PS text me 17–19° likha hai. **Dono bol sakte hain,
bas source batana** — "PS says 17–19, published field literature says 14–17, we calibrated
to 14–17.")

**API gravity kya hai?** Oil kitna halka ya bhaari hai, uska scale. Number **zyada = halka
oil** (petrol jaisa), **kam = bhaari oil** (tar jaisa). Light crude 30°+ hota hai. 15° ka
matlab — ye paani se bhi thoda halka hai bas, aur behta bahut mushkil se hai.

### 3.3 Crude itna gaadha kyun hai — shahad wali baat

Yeh **poore project ka sabse important number** hai:

> **Baghewala crude: 8,000–15,000 cP at 50 °C.** Hum model me midpoint **11,500 cP** use
> karte hain.

Compare kar:
- Paani = **1 cP**
- Olive oil = ~80 cP
- Shahad (honey), room temperature pe = **~10,000 cP**

Toh Baghewala ka oil reservoir me **thanda shahad** hai. Chattan ke andar shahad, aur woh
chattan bhi ghatiya quality ki — **porosity 10% se kam** (yaani rock me khali jagah bahut
kam hai). Socho ek sponge ki jagah tujhe ek almost-solid patthar mila hai jisme shahad
bhara hai.

**Ab twist — "born heavy" wali story.** Normally jo oil 18° API ka hota hai woh
karib **~123 cP** hota hai 50 °C pe. Baghewala ka **90–100 guna zyada gaadha** hai apni API
ke hisaab se. Kyun?

Kyunki ye oil purane tareeke se "heavy" nahi hua. Zyada tar heavy oils **biodegradation**
se bhaari hote hain — bacteria ne halke molecules kha liye, bacha hua bhaari maal. Lekin
Jodhpur Sandstone Cambrian-era ka hai, aur is oil me **wax aur asphaltene ka fraction
naturally bahut zyada** hai — yeh **born heavy** hai, banaya nahi gaya heavy.

**Iska practical matlab (yeh judge ko bolna):** koi bhi standard "API gravity → viscosity"
correlation is oil pe **~90–100 guna galat** answer degi. Isliye humne field ka **apna measured
viscosity point** use kiya, textbook correlation nahi.

**Asphaltene kya hai?** Crude oil me bade, chipchipe, polar molecules. Yehi oil ko gaadha
banate hain, aur pressure/temperature badalne pe **precipitate ho ke** pipe aur pump valve
me jam jaate hain. Heat inko solution me rakhta hai — CSS ka ek bonus faayda.

> **Yaad rakhne wali baat:** Baghewala = **thanda shahad, ghatiya sponge me, 1,150 m neeche.**
> Yeh ek line poori problem ko capture karti hai.

---

## 4. CSS kya hai — pressure cooker wali analogy

Jab oil itna gaadha ho, toh normal pumping se kuch nahi hota. Well se bilkul kuch nahi
nikalta ya itna kam nikalta hai ki diesel ka kharcha bhi nahi nikalta.

Toh solution simple hai: **garam karo.** Shahad ko fridge se nikaal ke garam paani me rakh
do — woh paani ki tarah behne lagta hai. Wahi principle, bas 1,150 m neeche.

**Cyclic Steam Stimulation (CSS)**, jise field me **"huff and puff"** bhi kehte hain, ka
matlab hai **ek hi well** se teen kaam, baari-baari:

### Phase 1 — INJECT (huff), ~20 din
Steam ko well me pump karte hain. Baghewala pe: **~74 tonnes per day**, **280–305 °C**,
**60–70% quality**, **14–21 din** tak. Well band hai, kuch bahar nahi aa raha. Sirf heat
andar ja rahi hai.

**Steam quality kya hai?** Steam ka kitna hissa asli vapour hai vs pehle hi paani ban chuka
hai. 65% quality = 65% vapour. **Yeh matter karta hai kyunki asli heat latent heat me hai**
— vapour condense ho ke jo energy chhodta hai wahi kaam ki cheez hai. Half quality = half
delivered heat, same tonnage pe.

### Phase 2 — SOAK, ~7 din
Well **band** rehta hai. Kuch nahi karte. Bas wait.

**Pressure cooker analogy:** cooker me seeti aane ke baad tu gas band karke 10 minute chhod
deta hai na? Andar ki heat daal me evenly phail jaati hai — bas seeti ki jagah pe nahi.
Soak wahi hai. Heat wellbore ke aas-paas se **conduction se andar tak phailti hai**, ek
wider radius ka oil patla hota hai.

**Trade-off yaad rakh:** soak **chhota** rakho toh heat sirf wellbore ke paas atki rehti
hai aur steam wapas bahar aa jaata hai. Soak **lamba** rakho toh heat upar-neeche ki cold
rock (cap rock) me leak hoti rehti hai aur well ek paisa nahi kama raha. Isliye ek
**optimum** hota hai. Baghewala aajkal injection ke 50–60% ke barabar soak karta hai
(≈ 7–13 din), jabki generic textbook 2–7 din kehta hai. **Yeh khud ek open sawaal hai jiska
jawab hamara twin numbers me de sakta hai.**

### Phase 3 — PRODUCE (puff), ~35 din
Well khol do, pump chalu. Ab oil garam hai, patla hai, behta hai. Din-ba-din zone thanda
hota jaata hai, viscosity wapas chadhti hai, rate girta jaata hai. Jab rate ek **cutoff
rate** se neeche chala jaaye — bas, cycle khatam. Wapas steam.

**Result?** Baghewala ka pehla CSS cycle (well BGW-8, **December 2018**, India ka pehla
formal CSS, Canadian partner Belgrave Oil & Gas ke saath) ne production me **5–6 guna**
jump diya. June 2025 tak 39 cycles ho chuke the.

**SOR — the one number.** **Steam-Oil Ratio** = kitne tonne steam daala ÷ kitne cubic metre
oil nikla. **Kam = achha.** Industry me CSS ka typical SOR **3–8** hai (average ~6),
aur 3 se neeche ko "thermally efficient" maana jaata hai.

SOR itna important kyun? Kyunki steam banane me **diesel jalta hai**, aur wahi CSS ka
sabse bada recurring cost hai. Baghewala ke apne numbers se: **~71 kg diesel per tonne
steam** ≈ **3.0 GJ per tonne**. Har extra tonne steam = jala hua diesel + CO₂, bina extra
oil ke. Isliye SOR ek saath **economics ka bhi** number hai aur **emissions ka bhi**.

> **Baghewala ka apna SOR kabhi publish nahi hua.** Kisi source me nahi mila. Isliye hum
> **kabhi bhi** koi number nahi bolte "Baghewala's current SOR is X" — hum literature ke
> 3–8 range ke against benchmark karte hain. Yeh ek trap hai, aur file 06 me detail me hai.

---

## 5. Sucker rod pump kya hai — handpump wali analogy

Reservoir se oil wellbore tak toh aa gaya. Ab usko **1,150 m upar** kaun laayega?

**Sucker Rod Pump (SRP)** — jise "beam pump" ya **"nodding donkey"** kehte hain, kyunki
door se dekhne pe lagta hai jaise koi gadha sar hila raha ho. Duniya ke **~90% artificially
lifted wells** yahi use karte hain.

**Gaon ka handpump socho.** Tu handle upar-neeche karta hai, neeche ek piston hai, do
valve hain, aur paani upar aata hai. SRP bilkul wahi hai — bas handle ki jagah ek motor +
walking beam hai, aur piston **1,150 m neeche** hai, ek **steel rod** se juda hua jo poore
1,150 m lambi hai.

Do parts jo samajhne hain:
- **Standing valve (SV)** — barrel ke bottom me. Reservoir se fluid andar aane deta hai.
- **Travelling valve (TV)** — plunger (piston) me. Fluid ko plunger ke upar jaane deta hai.

**Upstroke** (rod upar): TV band, SV khulta hai → reservoir ka fluid barrel me ghusta hai.
Rod ab **apna weight + upar ka poora oil column** utha raha hai. Yeh peak load hai.

**Downstroke** (rod neeche): SV band, TV khulta hai → plunger fluid ke through neeche
girta hai. **Yahan koi motor rod ko dhakka nahi de raha** — rod sirf **gravity se** girti
hai.

Aur bas yahin se hamari doosri problem shuru hoti hai.

### Rod floating — asli failure mode

Agar oil kaafi gaadha ho, toh downstroke pe **viscous drag** itna zyada ho jaata hai ki rod
**utni tezi se gir hi nahi paati** jitni tezi se upar wala horsehead neeche ja raha hai.

Rod peeche reh jaati hai — woh **"float"** karti hai — aur phir pakadne ke liye **dhadaam
se girti hai**. Consequences:
- Shock loading poore unit pe
- Neeche wale rods **compression** me chale jaate hain — aur steel **tension me strong,
  compression me kamzor** hota hai → buckling, tubing se ragadna, fatigue crack
- Har stroke ek stress cycle hai. 6 SPM pe = **saal me 3.15 million cycles.** Rod overload
  se nahi tootti, **fatigue** se tootti hai.

Jab rod tootti hai toh **workover** karna padta hai — rig laao, poori string kheencho,
badlo, wapas daalo. Industry-typical cost: **$15,000–$50,000 per event** (aur agar deferred
production bhi count karo toh $90k–$270k). Aur SRP ki **50% se zyada failures** exactly
isi metal-on-metal rod/tubing wear se hoti hain.

**Aur ab dono halves ko jodo — yahi poora project hai:**

> Steam decisions → **viscosity** badalti hai. Viscosity → **rod floating risk** decide
> karti hai. Yaani steam ka decision aur pump ka decision **physically ek doosre se jude
> hue hain.**

Sirf steam optimise karoge → pump maar doge.
Sirf pump optimise karoge → steam ka paisa barbaad karoge.

---

## 6. Toh problem exactly kya hai — teen line me

1. **SOR high hai / pata hi nahi hai.** Kitna steam optimal hai, koi nahi janta. Zyada
   steam = jala hua diesel + CO₂ bina extra oil ke. Kam steam = well thanda, oil nahi.

2. **Rod failures hote hain.** Cold, gaadhe tail-end me pump chalate raho toh floating,
   compression, aur eventually ek mehnga workover.

3. **Sab kuch manual guesswork hai.** Ek CSS cycle me sirf **4 knobs** hain jo operator
   ghuma sakta hai — kitna steam, kitne din soak, kis rate pe rok do, aur pump kitni tez
   chalao. Aaj yeh chaaron **experience se** set hote hain. Koi tool inhe **saath me**
   optimise nahi karta:
   - Commercial rod-pump optimisers (XSPOC, Lufkin, Weatherford ForeSite) — **sirf pump**
   - Reservoir simulators (CMG, Eclipse) — **sirf reservoir**, aur ghante lagte hain ek run me

**Hamara claim yeh hai:** ek chhota, tez, physics-based twin jo **chaaron knobs ko ek saath**
optimise kare, aur saath hi rod ko safe rakhne ki constraint bhi lagaye.

> **Yaad rakhne wali baat:** poora project ek hi sentence me — *"Steam decisions change
> viscosity, and viscosity is exactly what decides whether the rods break. So they cannot
> be optimised separately."* Yeh line ratta maar le. Yeh hamari **novelty** hai.
