# Winning-deck analysis — SIH 2025 Idea Presentation (PS 25049)

Source: `C:\Users\Gaurav Agrawal\Downloads\SIH2025-IDEA-Presentation-Format.pptx.pdf`
(friend's *selected* SIH 2025 idea deck: "AI-Driven Public Health Chatbot for Disease
Awareness", MedTech/BioTech/HealthTech, PS Category Software).

Analysed by extracting per-page text, text positions, font sizes and every embedded
raster image from the PDF (`pypdf`). 6 pages, 960x540 pt (= 13.333in x 7.5in, 16:9),
i.e. **1 pt in the PDF == 1 pt on the slide**, so the reported font sizes below are the
real slide font sizes.

---

## Global observations

- **Exactly 6 slides. No more, no less** — Title + 5 content slides. This matches the
  official template's instruction slide ("keep the maximum slides limit up to six (6),
  including the title slide"). The instruction slide itself was deleted.
- **The official template was left completely untouched structurally**: same master,
  same SIH banner logo top-right (181x92 px image repeated on every slide), same
  bottom bar, same "Your Team Name" oval top-left (they did *not* even rename it),
  same slide-number placeholder, same 48pt bold section titles, same title casing
  (`TECHNICAL APPROACH`, `FEASIBILITY AND VIABILITY`, `IMPACT AND BENEFITS`,
  `RESEARCH AND REFERENCES` — including the template's double space in
  "RESEARCH  AND REFERENCES").
- **The template's instruction pointers were kept, but repurposed as section
  headings** with the team's own content underneath. They were *not* deleted and *not*
  reworded. This is the single most important structural move in the deck.
- **No paragraphs anywhere except one line of the problem statement.** Everything else
  is 3-6 word bullets. Longest bullet in the whole deck: 7 words.
- **Bullet glyphs**: `●` (filled circle) for normal bullets, `➡` for the
  "How it addresses the problem" block. Consistent per block.
- **Text density per slide is LOW.** Slide 2 (the densest) carries ~19 bullets across
  4 blocks but each is 3-5 words; slides 3-6 carry 0-12 bullets.
- **Font sizes**: 48pt titles, 30.7pt block headings (slides 4-5), 22-27pt block
  headings (slide 2), 28pt body (slides 4-6), 20pt body (slide 2), 24pt for the
  problem-statement sentence, 16pt slide numbers.
- **Colour/graphic language**: they added zero decoration of their own — no custom
  shapes, no gradient boxes, no icon sets. All visual weight comes from **real
  diagrams and one real chart**, dropped in as pictures.

---

## Slide-by-slide

### Slide 1 — Title page (template's Title Slide layout, unchanged)
- Kept `SMART INDIA HACKATHON 2025` heading and the template's 6-line bullet block
  verbatim, just filling the values after each dash:
  - `Problem Statement ID- 25049`
  - `Problem Statement Title- AI-Driven Public Health Chatbot for Disease Awareness`
  - `Theme- MedTech / BioTech / HealthTech`
  - `PS Category- Software`
  - `Team ID-`  ← **left blank**
  - `Team Name -` ← **left blank**
- Bullets at ~22pt (template default is 24pt; shrunk one step so the long PS title fits
  the narrow left column without reflowing the layout).
- **One added element only**: a short tagline in quotes at the bottom —
  `"Empowering Preventive Healthcare Through AI"` (~16pt). That is the whole
  "creativity budget" on the title slide.
- 2 images: the template's SIH banner + one wide 2048x878 hero graphic in the
  template's right-hand picture area.

### Slide 2 — Idea title / Proposed Solution (densest slide, text-only)
- Title placeholder = **their idea title**, not the literal word "IDEA TITLE"
  (`AI-Driven Public Health Chatbot for Disease Awareness`, 28pt).
- Content area split into **4 headed blocks** whose headings are the template's own
  pointers:
  1. `Problem Statement -` (24pt) — one 2-line sentence spanning the full width, with
     the key phrases bolded (`real-time alerts`, `WhatsApp`, `SMS fallback`,
     `lightweight web/app support`).
  2. `Proposed Solution` (26.7pt heading) — 1 lead-in line + 6 bullets @ 20pt.
  3. `How It Addresses the Problem` (22.7pt) — 4 bullets @ 20pt with `➡` glyph.
  4. `Innovation & Uniqueness` (22.7pt) — 4 bullets @ 20pt.
- Blocks 2-4 sit as **three columns** below the full-width problem statement.
- **Zero images** on this slide (besides the template banner). No product screenshot.

### Slide 3 — TECHNICAL APPROACH (**pure graphics — the key lesson**)
- **The slide contains NO bullet text at all.** Extracted text is only: the title
  `TECHNICAL APPROACH` (48pt), the slide number, the team-name oval, and one orphan
  bullet glyph. The template's two pointer lines were removed here.
- The entire content area is **two flowchart images side by side**:
  - **Left/main: a polished architecture flowchart** (1280x853 px, ~2.3x oversampled) —
    "Healthcare Chatbot Architecture". Rounded/square **labelled blocks** connected by
    **black elbow arrows**, left-to-right dataflow (actors → channel gateways → AI/NLP
    engine → knowledge base → outputs), **colour-coded blocks** (blue SMS, green
    WhatsApp, orange IVR, purple web, dark-grey engine blocks, cream output panel),
    **real product/tech logos** (WhatsApp, SMS, Node.js icons) and small people/device
    icons for the actors. Bulleted sub-items live *inside* the blocks.
  - **Right/secondary: a rough hand-drawn-style tech-stack flow** (510x538 px) —
    rounded rectangles naming the actual stack (`chatbot-NLP pipeline (Rasa)+google
    translator`, `database-mongodb`, `backend-Node.js`, `frontend-Next.js+tailwind`,
    `userlogin-next-auth`, `vapi and twilio`) wired with thin arrows.
- So the technical approach answers both template pointers **graphically**: the big
  diagram = methodology/process; the small diagram = technologies used.
- **No step numbering, no swimlanes, no Gantt.** Just blocks + arrows + tech names.
- **No product screenshots anywhere in the deck.**

### Slide 4 — FEASIBILITY AND VIABILITY (text-only, 3 columns)
- **Three equal columns**, each headed with the template's exact pointer, lightly
  reworded to a noun phrase:
  | `Feasibility Analysis` | `Challenges & Risks` | `Strategies to Overcome` |
- 3-4 bullets per column @ 28pt (`●` glyph), each 3-6 words. Wraps to 2 lines max.
- Notice the 1:1 pairing — every risk in column 2 has a matching mitigation in
  column 3, read across.
- **No images, no icons, no tables** — plain text columns.

### Slide 5 — IMPACT AND BENEFITS (4 text blocks + 1 chart)
- Left ~60%: **four small headed blocks in a 2x2 / 4-across grid**, headings @ 30.7pt:
  `Target Audience` | `Social` | `Economic` | `Public Health`
  Each with a single 2-3 line sentence @ 28pt (not bulleted — sentence fragments).
  The headings map straight onto the template pointer
  "Benefits of the solution (social, economic, environmental, etc.)".
- Right: **one matplotlib-looking chart image** (759x572 px) — a plain pie chart,
  "Deaths due to Diseases (2015-2024), Total: 29920", default matplotlib-ish palette,
  no chartjunk, title + percentage labels only.
- So Impact = **quantitative evidence picture + qualitative benefit blocks**, never
  a wall of claims.

### Slide 6 — RESEARCH AND REFERENCES (text-only)
- Template pointer line removed; just **3 bullets @ 28pt**, each an
  author/organisation + title + `Retrieved from <full URL>`.
- URLs shown in full, wrapping across lines. Nothing else on the slide.
- Sparse — roughly a third of the slide is empty. They did not pad it.

---

## The 5 lessons to copy

1. **Six slides, template untouched.** Same master, banner, footer, ovals, title
   casing and 48pt title sizing. The only structural edit is deleting the instructions
   slide.
2. **Keep the template's instruction pointers — turn them into your section
   headings.** Never delete them, never reword them beyond a noun-phrase trim. The
   screener is checking that each mandated pointer is answered.
3. **Technical Approach is a picture, not a list.** A real architecture flowchart
   (labelled blocks + arrows + tech logos + colour coding) filling the content area,
   optionally with a second, smaller stack diagram beside it. Text on that slide is
   near-zero.
4. **Bullets are 3-6 words at 20-28pt.** No paragraphs, no clause-heavy sentences, no
   parenthetical caveats inside bullets. Columns for anything that has 3 parallel
   parts (feasibility/risks/mitigations; social/economic/environmental).
5. **One real chart carries the Impact slide**, plus short benefit blocks. Evidence
   picture beats adjectives; empty space is acceptable (slide 6) and padding is not.
