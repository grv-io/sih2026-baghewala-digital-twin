# 02 — Humne Kaise Socha (PS Selection Ki Poori Soch)

Yeh file kyun padhni hai? Kyunki internal round me ek sawaal **pakka** aata hai:
*"Aapne yehi problem statement kyun choose kiya?"* Agar iska jawab *"sir interesting laga"*
hai, toh tu ek generic team lagta hai. Agar jawab **ek strategy** hai, toh tu ek serious
team lagta hai. Yeh file wahi strategy hai.

---

## 1. Situation: 233 problem statements, choose one

SIH ke portal pe **233 problem statements** the. Sabhi alag-alag ministries aur PSUs ke.
Ek team maximum **2 PS** pe apply kar sakti hai — toh ek primary chahiye tha aur ek backup.

Ab yahan zyada tar teams jo galti karti hain woh yeh hai: woh PS **"kaunsa sabse cool
lagta hai"** ke hisaab se chunti hain. Nateeja — sab log same 10 glamorous PS pe tut padte
hain (AI chatbot, drone, blockchain wale), aur 400+ ideas ek hi PS pe aa jaate hain.

Humne ulta socha. Humne **filters** lagaye.

---

## 2. Char filters jo humne lagaye

### Filter 1 — Low crowd (kam bheed)

Portal pe har PS ke saath **live idea count** dikhta hai, aur ek hard rule hai: ek PS pe
**500 ideas** aane ke baad woh PS **freeze** ho jaata hai, aur usme koi entry nahi jaati.

Toh pehla filter simple tha: **kis PS pe abhi bheed nahi hai?**

Early September 2026 me portal scrapers ne dikhaya ki **SIH26120 pe sirf 1–2 ideas** submit
hue the. Compare kar — glamorous PS pe 500 tak (freeze cap) already pahunch jaate hain.

**Iska matlab kya nikla?** Yeh ki hamara asli competitor doosri student teams nahi hain.
Hamara asli competitor **Oil India ka apna bar** hai. Kyunki rule ye hai — sponsoring
organisation *chahe toh winner declare hi na kare*. SIH 2025 me 3 PS pe exactly yeh hua
tha, zero winners.

Toh strategy shift ho gayi: **"doosron se better banao" nahi, balki "OIL ke engineers ko
convince karo"**. Yeh ek bilkul alag game hai — aur yeh game domain depth se jeeti jaati
hai, flashy UI se nahi.

### Filter 2 — Hard for others (doosron ke liye mushkil)

Yeh filter thoda counterintuitive hai. Humne aisa PS dhoonda jo **doosri teams ke liye
mushkil ho**, aur specifically **CS-only teams ke liye mushkil ho**.

SIH me 90% teams pure computer science / IT ki hoti hain. Woh log ek chatbot, ek CRUD app,
ek dashboard — ye sab hum se tez bana lenge. Us game me hum unse nahi jeet sakte.

Lekin **SIH26120** me pehle ye samajhna padta hai:
- Marx-Langenheim heat transfer model kya kehta hai
- Andrade viscosity law kya hai
- Vogel IPR curve kya hai
- Rod string mechanics aur floating kya cheez hai
- SOR ka matlab kya hai aur woh economics se kaise juda hai

Ek CS team ye sab **seekh** sakti hai, par **36 ghante me nahi**, aur **confidently defend
nahi kar sakti** jab OIL ka apna reservoir engineer cross-question kare.

Yahi wo cheez hai jo is PS ko hamare liye **easy** aur unke liye **hard** banati hai. Yeh
ek **moat** hai — competitive advantage jise copy karna mushkil hai.

### Filter 3 — ChemE edge (mera apna domain)

Main 3rd-year **Chemical Engineering** ka student hoon at MNIT. Is PS ka poora core mera
syllabus hai:

| PS me kya chahiye | Mera kaunsa subject |
|---|---|
| Steam se reservoir garam hona, heat loss | **Heat Transfer** |
| Viscosity vs temperature, Andrade law | **Fluid Mechanics / Transport Phenomena** |
| Energy balance of a CSS cycle | **Thermodynamics** |
| SOR, cost per barrel, diesel intensity | **Process Economics** |
| Pump ko chalana, set-point control | **Process Control** |

Yaani main is PS ke saamne **student** ki tarah nahi, **domain guy** ki tarah khada ho
sakta hoon. Aur SIH ke judging me ek documented pattern hai: **sponsor ke apne engineers hi
sabse hard domain questions poochte hain**, aur unki scepticism ko todna hi asli test hai.

Ek aur cheez — 90% teams apna technical depth **ML me** dikhati hain. Hum **physics me**
dikhayenge. Judge ke liye yeh refreshing hai, aur PSU engineers pure-ML claims pe
**bharosa nahi karte** reservoirs ke baare me. Physics-first framing hamari taraf hai.

### Filter 4 — Rajasthan angle (local story)

Baghewala **Rajasthan** me hai. Hum **MNIT Jaipur** ke hain. Jaipur se Baghewala road
distance ~**550–600 km** — same state.

Yeh sirf ek emotional line nahi hai, iske do practical faayde hain:
1. **Story me weight aata hai.** "Hum Rajasthan ke students hain, Rajasthan ke Thar desert
   me India ka pehla CSS field hai, aur hum uske liye ye bana rahe hain" — yeh ek judge ko
   yaad reh jaata hai.
2. **Pilot credible lagta hai.** Agar OIL kal ek pilot karna chahe, toh ek local team ka
   physically wahan pahunchna realistic hai. PSU evaluators explicitly **pilot scoping**
   poochte hain — *"ek field, kitne wells, kitne weeks"* — aur wahan local hona madad karta
   hai.

> **Yaad rakhne wali baat:** char filters ek line me — **kam bheed** (Filter 1), **doosron
> ke liye mushkil** (Filter 2), **mere liye asaan** (Filter 3), **ghar ke paas** (Filter 4).
> Chaaron ek saath sirf **SIH26120** pe fit hue.

---

## 3. Backup: 26165 kyun tha

Rule hai — ek team **max 2 PS** pe apply kar sakti hai. Toh ek hedge chahiye tha.

Backup **PS 26165** tha. Logic simple: agar SIH26120 pe kuch ulta ho jaaye — jaise woh PS
500 ideas pe freeze ho jaaye, ya OIL ka scope kisi wajah se change ho jaaye — toh ek doosra
rasta khula rahe. Backup ka kaam **jeetna nahi** hota, backup ka kaam **zero pe na aana**
hota hai.

Par ek honest baat: backup pe humne **effort divide nahi kiya**. Kyunki SIH ka scoring
sponsor ke bar ko clear karne pe hai, aur do PS pe aadha-aadha kaam karke dono me weak
rehna sabse bada trap hai. **Primary pe 95% effort, backup sirf insurance.**

*(Note: repo ke `docs/research/deep-dives/sih_winning_playbook.md` me ek aur natural hedge suggest
kiya gaya hai — **SIH26121**, kyunki woh bhi Oil India ka hi PS hai, adjacent domain,
offset-well decision support. Same sponsor hone ki wajah se hamari domain research reuse
ho jaati. Final call SPOC ke saath confirm karna.)*

---

## 4. 26119 — solver trap kyun tha

**PS 26119 ko humne deliberately reject kiya**, aur yeh reject karna hi ek achha decision
tha. Wajah: woh ek **solver trap** tha.

Solver trap kya hota hai? Aisa problem statement jo dikhne me domain-heavy lagta hai, par
usko solve karne me asli kaam **ek pure algorithm / solver likhna** hai. Yaani:

- Domain knowledge ki value **kam** ho jaati hai — bas problem samajhne bhar ki chahiye
- Poora game **algorithm ki quality** pe aa jaata hai — constraint solving, scheduling,
  routing, jo bhi ho
- Aur us game me **hardcore CS teams** hum se behtar hain. Unke paas competitive programming
  ka background hai, DSA ka grind hai, solver libraries ka experience hai

Yaani 26119 pe hamara **ChemE differentiator zero ho jaata**, aur hum apni weakest ground
pe ladh rahe hote. Aur judges bhi wahan hamari physics ki baat nahi sunte — woh sirf
**"aapka solver kitna fast hai, kitna optimal hai"** poochte.

Iske ulta SIH26120 me solver **ek chhota component** hai (Bayesian optimizer, 60 lines
ka `ml/optimize.py`), aur asli value **physics engine** me hai — jo hamari strength hai.

> **Yaad rakhne wali baat:** PS choose karte waqt sawaal ye nahi hai *"kya main isko solve
> kar sakta hoon?"* — sawaal ye hai *"is PS pe **jeetne ke liye** jo skill chahiye, kya
> wahi meri strongest skill hai?"* 26119 pe answer NO tha. 26120 pe YES.

---

## 5. Strategy: "ChemE terms + ek number har slide" wala funda

Ab PS choose ho gaya. Ab pitch kaise banega? Hamara funda ek line me:

> **Har slide pe kam se kam ek asli ChemE term, aur kam se kam ek asli number, source ke
> saath.**

Kyun yeh kaam karta hai:

**(a) ChemE term = credibility signal.** Jab tu slide pe *"Marx-Langenheim thermal
efficiency"*, *"Andrade viscosity law"*, *"Vogel IPR"*, *"steam quality"*, *"floating
index"* likhta hai — OIL ka engineer turant samajh jaata hai ki team ne homework kiya hai.
Yeh ek **shibboleth** hai — jo log domain me hain woh ise pehchante hain, jo nahi hain woh
likh hi nahi paate.

**(b) Number = "walls of text" wali maut se bachaav.** SIH internals me teams ke marne ka
**sabse zyada cited reason** hai: *"Wikipedia ya ChatGPT se copy kiye hue paragraph."* Aisa
deck jisme ministry ka naam badal do aur phir bhi sab sach lage. Uska antidote hai ek
**specific, sourced number** — `1,150 m`, `8,000–15,000 cP @ 50 °C`, `74 t/d`,
`280–305 °C`, `BGW-8, Dec 2018`, `5–6x uplift`, `218 t → 43,773 t`. Yeh numbers ChatGPT se
nahi aa sakte, yeh sirf research se aate hain.

**(c) Har number ka ek label hota hai.** Yeh sabse important discipline hai. Har number
teen me se ek category me aata hai:
- **CONFIRMED** — kisi cited source me literally likha hai
- **LITERATURE-TYPICAL** — industry-general hai, Baghewala-specific nahi
- **OUR-SIMULATION** — hamare twin ne compute kiya, sach tabhi jab hamare assumptions sach

Jo number is table pe nahi hai, woh **stage pe nahi bolna**. Aur jab bhi typical number
bolo, saath me *"that's industry-typical, not Baghewala-specific"* bolo.

**(d) Kya-kya deliberately under-serve nahi karna.** SIH ka official rubric ye kehta hai:
*novelty, complexity, clarity in the prescribed format, feasibility, practicability,
**sustainability**, scale of impact, **user experience**, **potential for future work
progression***. Ek physics+ML deck automatically novelty aur complexity pe strong hota hai
— aur **sustainability, UX aur future work pe kamzor**. Isliye humne deliberately CO₂ angle
(SOR gira toh diesel gira toh CO₂ gira), operator-facing dashboard, aur recalibration
roadmap ko explicitly deck me daala.

**(e) Format compliance khud ek scored criterion hai.** *"Clarity and details in the
prescribed format"* — literally rubric me likha hai. Isliye humne ek achha-dikhne wala
custom-designed deck (`_VISUAL`) **reject** kar diya aur official template pe **STRICT**
deck rebuild kiya — 6 slides, template ke apne pointers as headings, PDF export. Achha
dikhna kaafi nahi, **compliant** dikhna zaroori hai.

> **Yaad rakhne wali baat:** hamari strategy competition wali nahi, **credibility** wali
> hai. Low-crowd PS + domain moat + har claim pe label. Judge ko yeh feel aana chahiye ki
> *"ye log jaante hain ki ye kya nahi jaante"* — kyunki reported pattern yeh hai ki
> **defensive answers score kam karte hain, aur "I don't know, here's why" score zyada.**
